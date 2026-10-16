from collections.abc import Callable, Iterator
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core import clock
from app.core.db import Base, get_db
from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)

    def override_get_db() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    # Outside a context manager, TestClient does not run the production lifespan.
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        test_client.close()
        app.dependency_overrides.clear()
        engine.dispose()


@pytest.fixture
def frozen_clock() -> Iterator[Callable[[datetime | None], None]]:
    clock.freeze(datetime(2026, 10, 19, 8, 0, tzinfo=clock.TZ))
    try:
        yield clock.freeze
    finally:
        clock.freeze(None)
