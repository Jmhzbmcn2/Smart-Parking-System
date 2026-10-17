import re
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import clock
from app.modules.sessions.models import GateEvent, ParkingSession

PLATE_RE = re.compile(r"^\d{2}[A-Z][A-Z0-9]?-\d{3}\.?\d{2}$")
CONFIDENCE_THRESHOLD = 0.8


class PlateConflict(Exception):
    """The plate already has an Active session."""


class NoActiveSession(Exception):
    """The plate has no Active session to close."""


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
    """Enter or exit a plate by gate prefix (IN-/OUT-) and open the barrier."""
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
        session = ParkingSession(plate=plate, entry_at=at)
        db.add(session)
        event.action = "entered"
    else:
        session = _active_session(db, plate)
        if session is None:
            raise NoActiveSession(plate)
        session.exit_at = at
        session.status = "closed"
        event.action = "exited"
    try:
        db.flush()
    except IntegrityError as exc:  # concurrent duplicate entry hit the unique index
        db.rollback()
        raise PlateConflict(plate) from exc
    event.session_id = session.id
    event.barrier_opened_at = clock.now()
    db.add(event)
    db.commit()
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
    return handle_plate(db, gate_id, normalized, at, "lpr", confidence)


def list_events(db: Session, limit: int) -> list[GateEvent]:
    return list(db.scalars(select(GateEvent).order_by(GateEvent.id.desc()).limit(limit)))


def list_sessions(db: Session, status: str | None) -> list[ParkingSession]:
    query = select(ParkingSession).order_by(ParkingSession.id.desc())
    if status is not None:
        query = query.where(ParkingSession.status == status)
    return list(db.scalars(query))
