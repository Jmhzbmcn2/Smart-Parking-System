import math

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.modules.billing.models import Price


def fee(minutes: int, price: Price) -> int:
    """Parking fee in VND: a flat first block, then each started hour."""
    hours = max(1, math.ceil(minutes / 60))
    if hours <= price.first_hours:
        return price.first_price
    return price.first_price + (hours - price.first_hours) * price.per_hour


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
