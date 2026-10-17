import re
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import clock
from app.modules.billing.service import current_price, open_payment
from app.modules.sessions.models import GateEvent, ParkingSession

PLATE_RE = re.compile(r"^\d{2}[A-Z][A-Z0-9]?-\d{3}\.?\d{2}$")
CONFIDENCE_THRESHOLD = 0.8


class PlateConflict(Exception):
    """The plate already has an Active session."""


class NoActiveSession(Exception):
    """The plate has no Active session to close."""


class InvalidExitTime(Exception):
    """The exit time is earlier than the entry time."""


class InvalidPlate(Exception):
    """The plate does not match the Vietnamese plate format."""


def normalize_plate(plate: str) -> str:
    return plate.strip().upper()


def _active_session(db: Session, plate: str) -> ParkingSession | None:
    return db.scalar(
        select(ParkingSession).where(
            ParkingSession.plate == plate, ParkingSession.status == "active"
        )
    )


def handle_plate(
    db: Session,
    gate_id: str,
    plate: str,
    at: datetime,
    source: str,
    confidence: float | None,
) -> GateEvent:
    """Enter a plate (opens the barrier) or start an exit (asks for payment) by gate prefix.

    Flushes but does not commit, so the caller can add an audit row in the same transaction.
    """
    plate = normalize_plate(plate)
    if not PLATE_RE.match(plate):
        raise InvalidPlate(plate)
    event = GateEvent(
        gate_id=gate_id,
        plate=plate,
        confidence=confidence,
        source=source,
        received_at=clock.now(),
    )
    if gate_id.startswith("IN-"):
        if _active_session(db, plate) is not None:
            raise PlateConflict(plate)
        session = ParkingSession(plate=plate, entry_at=at, price_id=current_price(db).id)
        db.add(session)
        event.action = "entered"
    else:
        session = _active_session(db, plate)
        if session is None:
            raise NoActiveSession(plate)
        if at < session.entry_at:
            raise InvalidExitTime(plate)
        if session.exit_at is None:  # a repeat exit keeps the first exit time and payment
            session.exit_at = at
        # Payment closes the session and opens the barrier (see complete_exit).
        payment = open_payment(db, session, gate_id)
        event.action = "payment_required"
        event.payment_id = payment.id
    try:
        db.flush()
    except IntegrityError as exc:  # concurrent duplicate entry hit the unique index
        db.rollback()
        raise PlateConflict(plate) from exc
    event.session_id = session.id
    if event.action == "entered":
        event.barrier_opened_at = clock.now()
    db.add(event)
    db.flush()
    return event


def handle_lpr_event(
    db: Session, gate_id: str, plate: str, at: datetime, confidence: float
) -> GateEvent:
    """IF-01/IF-02: low confidence or a malformed plate needs manual entry, no barrier."""
    normalized = normalize_plate(plate)
    if confidence < CONFIDENCE_THRESHOLD or not PLATE_RE.match(normalized):
        event = GateEvent(
            gate_id=gate_id,
            plate=normalized,
            confidence=confidence,
            source="lpr",
            received_at=clock.now(),
            action="manual_required",
        )
        db.add(event)
        db.commit()
        return event
    event = handle_plate(db, gate_id, normalized, at, "lpr", confidence)
    db.commit()
    return event


def list_events(db: Session, limit: int) -> list[GateEvent]:
    return list(db.scalars(select(GateEvent).order_by(GateEvent.id.desc()).limit(limit)))


def list_sessions(db: Session, status: str | None) -> list[ParkingSession]:
    query = select(ParkingSession).order_by(ParkingSession.id.desc())
    if status is not None:
        query = query.where(ParkingSession.status == status)
    return list(db.scalars(query))
