from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReservationIn(BaseModel):
    slot_id: str
    plate: str


class ReservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slot_id: str
    plate: str
    created_at: datetime
    expires_at: datetime
    status: str
