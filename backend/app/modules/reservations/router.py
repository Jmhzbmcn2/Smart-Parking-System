from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.auth.models import User
from app.modules.auth.router import require_role
from app.modules.reservations import service
from app.modules.reservations.schemas import ReservationIn, ReservationOut
from app.modules.sessions.service import InvalidPlate
from app.modules.slots.service import UnknownSlot

router = APIRouter(tags=["reservations"])

driver_only = require_role("driver")

_ERRORS = {
    InvalidPlate: (422, "Invalid plate format"),
    UnknownSlot: (404, "Unknown slot"),
    service.AlreadyReserved: (409, "You already have an active reservation"),
    service.SlotNotAvailable: (409, "Slot is not available"),
    service.NoReservation: (404, "No active reservation"),
}


def http_error(exc: Exception) -> HTTPException:
    status, detail = _ERRORS[type(exc)]
    return HTTPException(status, detail)


@router.post("/reservations", status_code=201)
def create(
    body: ReservationIn,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(driver_only)],
) -> ReservationOut:
    service.expire_due(db)
    try:
        reservation = service.reserve(db, user.username, body.slot_id, body.plate)
    except tuple(_ERRORS) as exc:
        raise http_error(exc) from exc
    return ReservationOut.model_validate(reservation)


@router.get("/reservations/me")
def mine(
    db: Annotated[Session, Depends(get_db)], user: Annotated[User, Depends(driver_only)]
) -> ReservationOut | None:
    service.expire_due(db)
    reservation = service.active_for(db, user.username)
    return ReservationOut.model_validate(reservation) if reservation else None


@router.delete("/reservations/me", status_code=204)
def cancel(
    db: Annotated[Session, Depends(get_db)], user: Annotated[User, Depends(driver_only)]
) -> Response:
    service.expire_due(db)
    try:
        service.cancel(db, user.username)
    except service.NoReservation as exc:
        raise http_error(exc) from exc
    return Response(status_code=204)
