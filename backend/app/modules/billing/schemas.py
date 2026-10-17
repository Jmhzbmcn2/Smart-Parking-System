from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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
    paid_at: datetime | None
    qr_payload: str


class InvoiceRequest(BaseModel):
    email: EmailStr


class InvoiceResult(BaseModel):
    sent_at: datetime
    path: str | None  # outbox file name; null when sent through SMTP
