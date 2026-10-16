from datetime import UTC, datetime, timedelta

import pytest

from app.core import clock, config


def test_now_is_aware_in_utc_plus_7():
    assert clock.now().utcoffset() == timedelta(hours=7)
    assert clock.now().tzinfo == clock.TZ


def test_freeze_returns_fixed_time(frozen_clock):
    assert clock.now() == datetime(2026, 10, 19, 8, 0, tzinfo=clock.TZ)
    with pytest.raises(ValueError):
        frozen_clock(datetime(2026, 10, 19, 8, 0))
    frozen_clock(datetime(2026, 10, 19, 4, 10, tzinfo=UTC))
    assert clock.now().tzinfo == clock.TZ
    assert clock.now().utcoffset() == timedelta(hours=7)
    assert clock.now().hour == 11 and clock.now().minute == 10
    frozen_clock(datetime(2026, 10, 19, 11, 10, tzinfo=clock.TZ))
    assert clock.now().hour == 11 and clock.now().minute == 10


def test_clock_unfrozen_after_fixture():
    # Runs after the freeze test and must see real time again.
    assert abs(clock.now() - datetime.now(clock.TZ)) < timedelta(seconds=5)


def test_default_database_url_points_into_backend():
    assert config.DATABASE_URL == f"sqlite:///{(config.BACKEND_DIR / 'spms.db').as_posix()}"
    assert config.BACKEND_DIR.name == "backend"
    assert config.BACKEND_DIR.is_absolute()
