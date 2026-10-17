from datetime import date, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import clock
from app.modules.billing.models import Payment


def today() -> date:
    return clock.now().date()


def daily_report(db: Session, day: date) -> dict:
    """Paid payments whose paid_at falls on `day` in UTC+7."""
    start = datetime.combine(day, time.min, tzinfo=clock.TZ)
    rows = db.execute(
        select(Payment.method, func.count(), func.sum(Payment.amount))
        .where(Payment.status == "paid", Payment.paid_at >= start)
        .where(Payment.paid_at < start + timedelta(days=1))
        .group_by(Payment.method)
    )
    by_method = {"qr": 0, "cash": 0}
    count = 0
    for method, n, amount in rows:
        by_method[method] = amount
        count += n
    return {
        "date": day,
        "paid_count": count,
        "total": sum(by_method.values()),
        "by_method": by_method,
    }
