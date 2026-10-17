from datetime import datetime

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
