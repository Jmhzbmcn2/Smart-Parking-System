from pydantic import BaseModel


class SensorEvent(BaseModel):
    slot_id: str
    occupied: bool


class SensorResult(BaseModel):
    slot_id: str
    status: str


class FloorZoneSummary(BaseModel):
    floor: int
    zone: str
    free: int
    total: int
