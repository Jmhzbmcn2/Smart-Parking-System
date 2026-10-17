from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class PriceIn(BaseModel):
    first_hours: Annotated[int, Field(ge=1)]
    first_price: Annotated[int, Field(ge=0)]
    per_hour: Annotated[int, Field(ge=0)]


class PriceOut(PriceIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    created_by: str


class MockResult(BaseModel):
    success: bool


class PaymentOut(BaseModel):
    id: int
    session_id: int
    plate: str
    gate_id: str
    amount: int
    status: str
    method: str | None
    qr_payload: str
