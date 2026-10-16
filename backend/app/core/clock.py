from datetime import datetime, timedelta, timezone

TZ = timezone(timedelta(hours=7))
_frozen: datetime | None = None


def now() -> datetime:
    return _frozen if _frozen is not None else datetime.now(TZ)


def freeze(at: datetime | None) -> None:
    global _frozen
    if at is not None and at.utcoffset() is None:
        raise ValueError("Frozen time must be timezone-aware")
    _frozen = at.astimezone(TZ) if at is not None else None
