from datetime import datetime
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints

GateId = Annotated[str, StringConstraints(pattern=r"^(IN|OUT)-\d+$")]


class LprEventRequest(BaseModel):
    plate: str
    confidence: Annotated[float, Field(ge=0, le=1)]
    gate_id: GateId
    timestamp: AwareDatetime


class ManualOpenRequest(BaseModel):
    gate_id: GateId
    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ManualEntryRequest(BaseModel):
    gate_id: GateId
    plate: str


class GateEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    gate_id: str
    plate: str | None
    confidence: float | None
    source: str
    received_at: datetime
    action: str
    session_id: int | None
    barrier_opened_at: datetime | None


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plate: str
    entry_at: datetime
    exit_at: datetime | None
    status: str
    price_id: int
