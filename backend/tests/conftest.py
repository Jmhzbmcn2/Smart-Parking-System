import base64
import os
from collections.abc import Callable, Iterator
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

# A fixed data key for tests, set before the encrypted column type first needs a key.
os.environ.setdefault("SPMS_DATA_KEY", base64.b64encode(bytes(range(64))).decode())

from app.core import clock
from app.core.db import Base, get_db
from app.main import app
from app.modules.auth.service import seed_users
from app.modules.billing.service import seed_price
from app.modules.slots.service import seed_slots


@pytest.fixture
def engine() -> Iterator[Engine]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def db(engine: Engine) -> Iterator[Session]:
    """Unseeded session on the in-memory database."""
    with Session(engine) as session:
        yield session


@pytest.fixture
def client(engine: Engine) -> Iterator[TestClient]:
    with Session(engine) as session:
        seed_slots(session)
        seed_users(session)
        seed_price(session)

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


@pytest.fixture
def frozen_clock() -> Iterator[Callable[[datetime | None], None]]:
    clock.freeze(datetime(2026, 10, 19, 8, 0, tzinfo=clock.TZ))
    try:
        yield clock.freeze
    finally:
        clock.freeze(None)


@pytest.fixture
def login() -> Callable[[TestClient, str], dict[str, str]]:
    """Return a function that logs in a demo user and gives back its auth header."""

    def _login(client: TestClient, username: str) -> dict[str, str]:
        response = client.post(
            "/api/auth/login", json={"username": username, "password": f"{username}123"}
        )
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['token']}"}

    return _login
