from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.modules.audit.models import AuditLog
from app.modules.auth.models import User


def record(
    db: Session, user: User, action: str, gate_id: str, reason: str, plate: str | None = None
) -> AuditLog:
    row = AuditLog(
        at=clock.now(),
        username=user.username,
        action=action,
        gate_id=gate_id,
        reason=reason,
        plate=plate,
    )
    db.add(row)  # The caller commits, together with the action being logged.
    return row


def list_log(db: Session, limit: int) -> list[AuditLog]:
    return list(db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)))
