from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.auth.router import current_user
from app.modules.slots import service
from app.modules.slots.schemas import FloorZoneSummary, SensorEvent, SensorResult

router = APIRouter(tags=["slots"])


@router.post("/sensor-events")
def sensor_event(body: SensorEvent, db: Annotated[Session, Depends(get_db)]) -> SensorResult:
    try:
        slot = service.set_occupied(db, body.slot_id, body.occupied)
    except service.UnknownSlot as exc:
        raise HTTPException(404, "Unknown slot") from exc
    return SensorResult(slot_id=slot.id, status=slot.status)


@router.get("/slots/summary", dependencies=[Depends(current_user)])
def slots_summary(db: Annotated[Session, Depends(get_db)]) -> list[FloorZoneSummary]:
    return [FloorZoneSummary(**row) for row in service.summary(db)]
