from sqlalchemy.orm import Mapped, mapped_column

from app.core.crypto import EncryptedString
from app.core.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(EncryptedString, unique=True)
    password_hash: Mapped[str]
    role: Mapped[str]  # "driver" | "attendant" | "admin"
    token: Mapped[str | None] = mapped_column(unique=True, default=None)
