from datetime import date

from pydantic import BaseModel


class DailyReport(BaseModel):
    date: date
    paid_count: int
    total: int  # VND
    by_method: dict[str, int]
