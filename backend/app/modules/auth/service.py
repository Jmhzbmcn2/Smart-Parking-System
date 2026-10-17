import hashlib
import hmac
import os

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
