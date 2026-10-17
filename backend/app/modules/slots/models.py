from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Slot(Base):
    __tablename__ = "slots"

    id: Mapped[str] = mapped_column(primary_key=True)
    floor: Mapped[int]
    zone: Mapped[str]
    status: Mapped[str] = mapped_column(
        default="available"
    )  # "available" | "occupied" | "reserved"
