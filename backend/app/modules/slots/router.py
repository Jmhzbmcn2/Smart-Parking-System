from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.auth.router import current_user
from app.modules.reservations.service import expire_due
from app.modules.slots import service
from app.modules.slots.schemas import FloorZoneSummary, SensorEvent, SensorResult, SlotOut

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
    expire_due(db)  # SP-2.2.2: release overdue holds before counting
    return [FloorZoneSummary(**row) for row in service.summary(db)]


@router.get("/slots", dependencies=[Depends(current_user)])
def slots(
    db: Annotated[Session, Depends(get_db)],
    floor: int | None = None,
    zone: str | None = None,
    status: str | None = None,
) -> list[SlotOut]:
    expire_due(db)
    return [SlotOut.model_validate(s) for s in service.list_slots(db, floor, zone, status)]
