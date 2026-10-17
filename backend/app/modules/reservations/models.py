from datetime import datetime

from sqlalchemy import ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import AwareDateTime, Base


class Reservation(Base):
    __tablename__ = "reservations"
    # One active hold per slot, enforced by the database (same pattern as uq_active_plate).
    __table_args__ = (
        Index("uq_active_slot", "slot_id", unique=True, sqlite_where=text("status = 'active'")),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    slot_id: Mapped[str] = mapped_column(ForeignKey("slots.id"))
    plate: Mapped[str]
    username: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(AwareDateTime)
    expires_at: Mapped[datetime] = mapped_column(AwareDateTime)
    status: Mapped[str] = mapped_column(default="active")  # "active" | "expired" | "cancelled"
