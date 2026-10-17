from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.audit import service
from app.modules.audit.schemas import AuditLogOut
from app.modules.auth.router import require_role

router = APIRouter(tags=["audit"])


@router.get("/audit-log", dependencies=[Depends(require_role("admin"))])
def audit_log(
    db: Annotated[Session, Depends(get_db)], limit: Annotated[int, Query(ge=1, le=500)] = 50
) -> list[AuditLogOut]:
    return [AuditLogOut.model_validate(r) for r in service.list_log(db, limit)]
