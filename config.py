import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
IS_VERCEL = os.environ.get("VERCEL") == "1"

# Vercel serverless: only /tmp is writable; SQLite + exports go there.
if IS_VERCEL:
    DATA_DIR = Path("/tmp/safeguard-data")
    EXPORT_DIR = Path("/tmp/safeguard-exports")
else:
    DATA_DIR = BASE_DIR / "data"
    EXPORT_DIR = BASE_DIR / "exports"

SAMPLE_IMPORT_DIR = BASE_DIR / "sample_imports"
PUBLIC_STATIC_DIR = BASE_DIR / "public" / "static"
DB_PATH = DATA_DIR / "safeguard.db"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-safeguard-local-key-change-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH.as_posix()}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False


def ensure_directories():
    for folder in (DATA_DIR, EXPORT_DIR, SAMPLE_IMPORT_DIR, PUBLIC_STATIC_DIR):
        folder.mkdir(parents=True, exist_ok=True)
