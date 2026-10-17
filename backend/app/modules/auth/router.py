from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.auth import service
from app.modules.auth.models import User
from app.modules.auth.schemas import LoginRequest, LoginResponse, MeResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def current_user(
    db: Annotated[Session, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    scheme, _, token = (authorization or "").partition(" ")
    user = service.user_by_token(db, token) if scheme.lower() == "bearer" and token else None
    if user is None:
        raise HTTPException(401, "Not authenticated", headers={"WWW-Authenticate": "Bearer"})
    return user


def require_role(*roles: str) -> Callable[[User], User]:
    def dependency(user: Annotated[User, Depends(current_user)]) -> User:
        if user.role not in roles:
            raise HTTPException(403, "Forbidden")
        return user

    return dependency


@router.post("/login")
def login(body: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> LoginResponse:
    user = service.login(db, body.username, body.password)
    if user is None or user.token is None:
        raise HTTPException(401, "Invalid username or password")
    return LoginResponse(token=user.token, username=user.username, role=user.role)


@router.get("/me")
def me(user: Annotated[User, Depends(current_user)]) -> MeResponse:
    return MeResponse(username=user.username, role=user.role)
