from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import AwareDateTime, Base


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True)
    slot_id: Mapped[str] = mapped_column(ForeignKey("slots.id"))
    plate: Mapped[str]
    username: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(AwareDateTime)
    expires_at: Mapped[datetime] = mapped_column(AwareDateTime)
    status: Mapped[str] = mapped_column(default="active")  # "active" | "expired" | "cancelled"
