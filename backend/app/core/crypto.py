import base64
import os
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESSIV
from sqlalchemy import Text
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator

from app.core.config import BACKEND_DIR

KEY_FILE = BACKEND_DIR / ".data_key"
KEY_BYTES = 64  # AES-256-SIV uses two 256-bit keys

_key: bytes | None = None


def load_key() -> bytes:
    """The data key: env SPMS_DATA_KEY (base64), else backend/.data_key, created on first use."""
    encoded = os.getenv("SPMS_DATA_KEY")
    if encoded is None:
        path = Path(os.getenv("SPMS_DATA_KEY_FILE", KEY_FILE))
        if not path.exists():
            path.write_text(base64.b64encode(AESSIV.generate_key(KEY_BYTES * 8)).decode())
        encoded = path.read_text().strip()
    key = base64.b64decode(encoded)
    if len(key) != KEY_BYTES:
        raise ValueError(f"data key must be {KEY_BYTES} bytes, got {len(key)}")
    return key


def _siv() -> AESSIV:
    global _key
    if _key is None:
        _key = load_key()
    return AESSIV(_key)


class EncryptedString(TypeDecorator[str]):
    """NFR-04: personal data is stored as AES-256-SIV ciphertext (base64 text).

    SIV is deterministic: equal values give equal ciphertext, so equality lookups and unique
    indexes keep working. The accepted leak is equality only (same plate, same ciphertext).
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect: Dialect) -> str | None:
        if value is None:
            return None
        return base64.b64encode(_siv().encrypt(value.encode(), None)).decode()

    def process_result_value(self, value: str | None, dialect: Dialect) -> str | None:
        if value is None:
            return None
        return _siv().decrypt(base64.b64decode(value), None).decode()
