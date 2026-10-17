from datetime import datetime

from sqlalchemy import ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.crypto import EncryptedString
from app.core.db import AwareDateTime, Base


class ParkingSession(Base):
    __tablename__ = "parking_sessions"
    # One Active session per plate, enforced by the database.
    __table_args__ = (
        Index("uq_active_plate", "plate", unique=True, sqlite_where=text("status = 'active'")),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    plate: Mapped[str] = mapped_column(EncryptedString)
    entry_at: Mapped[datetime] = mapped_column(AwareDateTime)
    exit_at: Mapped[datetime | None] = mapped_column(AwareDateTime, default=None)
    status: Mapped[str] = mapped_column(default="active")  # "active" | "closed"
    price_id: Mapped[int] = mapped_column(ForeignKey("prices.id"))  # price at entry (TC-11)


class GateEvent(Base):
    __tablename__ = "gate_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    gate_id: Mapped[str]
    plate: Mapped[str | None] = mapped_column(EncryptedString)
    confidence: Mapped[float | None]
    source: Mapped[str]  # "lpr" | "manual" | "payment"
    received_at: Mapped[datetime] = mapped_column(AwareDateTime)
    action: Mapped[
        str
    ]  # "entered" | "exited" | "manual_required" | "payment_required" | "payment_failed"
    session_id: Mapped[int | None] = mapped_column(ForeignKey("parking_sessions.id"), default=None)
    barrier_opened_at: Mapped[datetime | None] = mapped_column(AwareDateTime, default=None)
    suggested_slot: Mapped[str | None] = mapped_column(default=None)  # set on "entered"
    payment_id: Mapped[int | None] = mapped_column(ForeignKey("payments.id"), default=None)
