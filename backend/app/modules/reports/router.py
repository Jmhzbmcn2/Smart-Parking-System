from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.auth.router import require_role
from app.modules.reports import service
from app.modules.reports.schemas import DailyReport

router = APIRouter(tags=["reports"])


@router.get("/reports/daily", dependencies=[Depends(require_role("admin"))])
def daily(db: Annotated[Session, Depends(get_db)], date: date | None = None) -> DailyReport:
    return DailyReport(**service.daily_report(db, date or service.today()))
