from pydantic import BaseModel, ConfigDict


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


class SlotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    floor: int
    zone: str
    status: str
