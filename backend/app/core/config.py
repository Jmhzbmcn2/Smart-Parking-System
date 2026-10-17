import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
# Shared secret the mock devices (camera, sensor, payment gateway) send as X-Device-Key.
DEVICE_KEY = os.getenv("SPMS_DEVICE_KEY", "dev-device-key")
DATABASE_URL = os.getenv("SPMS_DATABASE_URL", f"sqlite:///{(BACKEND_DIR / 'spms.db').as_posix()}")
