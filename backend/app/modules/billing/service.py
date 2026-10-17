import math
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.modules.billing.models import Payment, Price

if TYPE_CHECKING:  # sessions imports billing, never the other way round at runtime
    from app.modules.sessions.models import ParkingSession


class AlreadyPaid(Exception):
    """The payment is already settled."""


def billable_hours(minutes: int) -> int:
    return max(1, math.ceil(minutes / 60))


def fee(minutes: int, price: Price) -> int:
    """Parking fee in VND: a flat first block, then each started hour."""
    hours = billable_hours(minutes)
    if hours <= price.first_hours:
        return price.first_price
    return price.first_price + (hours - price.first_hours) * price.per_hour


def minutes(start: datetime, end: datetime) -> int:
    """Whole minutes between two instants, truncated."""
    return int((end - start).total_seconds() // 60)


def add_price(db: Session, first_hours: int, first_price: int, per_hour: int, by: str) -> Price:
    price = Price(
        first_hours=first_hours,
        first_price=first_price,
        per_hour=per_hour,
        created_at=clock.now(),
        created_by=by,
    )
    db.add(price)
    db.flush()
    return price


def seed_price(db: Session) -> None:
    if db.scalar(select(Price.id).limit(1)) is None:
        add_price(db, 2, 20000, 10000, "system")
        db.commit()


def current_price(db: Session) -> Price:
    """The newest row is the current price."""
    return db.scalars(select(Price).order_by(Price.id.desc()).limit(1)).one()


def list_prices(db: Session) -> list[Price]:
    return list(db.scalars(select(Price).order_by(Price.id.desc())))


def open_payment(db: Session, session: "ParkingSession", gate_id: str) -> Payment:
    """The session's unsettled payment, or a new pending one for its fee."""
    existing = db.scalars(
        select(Payment).where(
            Payment.session_id == session.id, Payment.status.in_(("pending", "failed"))
        )
    ).first()
    if existing is not None:
        return existing
    price = db.get(Price, session.price_id)
    assert price is not None and session.exit_at is not None
    payment = Payment(
        session_id=session.id,
        gate_id=gate_id,
        amount=fee(minutes(session.entry_at, session.exit_at), price),
        created_at=clock.now(),
    )
    db.add(payment)
    db.flush()
    return payment
