from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.auth.router import require_role
from app.modules.sessions import service
from app.modules.sessions.schemas import GateEventOut, LprEventRequest, SessionOut

router = APIRouter(tags=["sessions"])

staff = Depends(require_role("attendant", "admin"))

_ERRORS = {
    service.PlateConflict: (409, "Plate already has an active session"),
    service.NoActiveSession: (404, "Plate has no active session"),
    service.InvalidPlate: (422, "Invalid plate format"),
}
GATE_ERRORS = tuple(_ERRORS)


def http_error(exc: Exception) -> HTTPException:
    status, detail = _ERRORS[type(exc)]
    return HTTPException(status, detail)


@router.post("/lpr-events", status_code=201)
def lpr_event(body: LprEventRequest, db: Annotated[Session, Depends(get_db)]) -> GateEventOut:
    try:
        event = service.handle_lpr_event(
            db, body.gate_id, body.plate, body.timestamp, body.confidence
        )
    except GATE_ERRORS as exc:
        raise http_error(exc) from exc
    return GateEventOut.model_validate(event)


@router.get("/gate-events", dependencies=[staff])
def gate_events(
    db: Annotated[Session, Depends(get_db)], limit: Annotated[int, Query(ge=1, le=200)] = 20
) -> list[GateEventOut]:
    return [GateEventOut.model_validate(e) for e in service.list_events(db, limit)]


@router.get("/sessions", dependencies=[staff])
def sessions(
    db: Annotated[Session, Depends(get_db)],
    status: Annotated[str | None, Query(pattern="^(active|closed)$")] = None,
) -> list[SessionOut]:
    return [SessionOut.model_validate(s) for s in service.list_sessions(db, status)]
