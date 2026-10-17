from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from app.core.crypto import EncryptedString
from app.core.db import AwareDateTime, Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    at: Mapped[datetime] = mapped_column(AwareDateTime)
    username: Mapped[str] = mapped_column(EncryptedString)
    action: Mapped[str]  # "manual_open" | "manual_entry"
    gate_id: Mapped[str]
    reason: Mapped[str]
    plate: Mapped[str | None] = mapped_column(EncryptedString, default=None)
