from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.db import SessionLocal, init_db
from app.modules.audit import models as audit_models  # noqa: F401  (registers tables)
from app.modules.audit.router import router as audit_router
from app.modules.auth import models as auth_models  # noqa: F401  (registers tables)
from app.modules.auth.router import router as auth_router
from app.modules.auth.service import seed_users
from app.modules.health.router import router as health_router
from app.modules.sessions import models as session_models  # noqa: F401  (registers tables)
from app.modules.sessions.router import router as sessions_router
from app.modules.slots import models as slot_models  # noqa: F401  (registers tables)
from app.modules.slots.router import router as slots_router
from app.modules.slots.service import seed_slots


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    with SessionLocal() as db:
        seed_slots(db)
        seed_users(db)
    yield


app = FastAPI(title="SPMS", lifespan=lifespan)
app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(sessions_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(slots_router, prefix="/api")
