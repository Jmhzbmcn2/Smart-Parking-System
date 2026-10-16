import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
DATABASE_URL = os.getenv("SPMS_DATABASE_URL", f"sqlite:///{(BACKEND_DIR / 'spms.db').as_posix()}")
