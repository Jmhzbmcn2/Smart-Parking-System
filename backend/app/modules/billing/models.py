from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import AwareDateTime, Base


class Price(Base):
    __tablename__ = "prices"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_hours: Mapped[int]
    first_price: Mapped[int]  # VND
    per_hour: Mapped[int]  # VND
    created_at: Mapped[datetime] = mapped_column(AwareDateTime)
    created_by: Mapped[str] = mapped_column(default="system")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("parking_sessions.id"))
    gate_id: Mapped[str]
    amount: Mapped[int]  # VND
    status: Mapped[str] = mapped_column(default="pending")  # "pending" | "paid" | "failed"
    method: Mapped[str | None] = mapped_column(default=None)  # "qr" | "cash"
    created_at: Mapped[datetime] = mapped_column(AwareDateTime)
    paid_at: Mapped[datetime | None] = mapped_column(AwareDateTime, default=None)
