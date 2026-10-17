import hashlib
import hmac
import os
import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.auth.models import User

DEMO_USERS = (
    ("admin", "admin123", "admin"),
    ("attendant", "attendant123", "attendant"),
    ("driver", "driver123", "driver"),
)


def _scrypt(pw: str, salt: bytes) -> bytes:
    return hashlib.scrypt(pw.encode(), salt=salt, n=2**14, r=8, p=1)


def hash_password(pw: str) -> str:
    salt = os.urandom(16)
    return f"{salt.hex()}${_scrypt(pw, salt).hex()}"


def verify_password(pw: str, stored: str) -> bool:
    salt_hex, hash_hex = stored.split("$")
    return hmac.compare_digest(_scrypt(pw, bytes.fromhex(salt_hex)).hex(), hash_hex)


def seed_users(db: Session) -> None:
    for username, password, role in DEMO_USERS:
        if db.scalar(select(User).where(User.username == username)) is None:
            db.add(User(username=username, password_hash=hash_password(password), role=role))
    db.commit()


def login(db: Session, username: str, password: str) -> User | None:
    """Check the password and issue a new token, which replaces the old one."""
    user = db.scalar(select(User).where(User.username == username))
    if user is None or not verify_password(password, user.password_hash):
        return None
    user.token = secrets.token_urlsafe(32)
    db.commit()
    return user


def user_by_token(db: Session, token: str) -> User | None:
    return db.scalar(select(User).where(User.token == token))
