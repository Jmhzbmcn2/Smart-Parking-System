from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    at: datetime
    username: str
    action: str
    gate_id: str
    reason: str
    plate: str | None
