import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
IS_VERCEL = os.environ.get("VERCEL") == "1" or os.environ.get("VERCEL_ENV") in {
    "production",
    "preview",
    "development",
}

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


def _database_uri():
    url = os.environ.get("DATABASE_URL", "").strip()
    if url:
        return url
    return f"sqlite:///{DB_PATH.as_posix()}"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-safeguard-local-key-change-in-production")
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False


def ensure_directories():
    # On Vercel only /tmp is writable; bundled dirs already exist in the deployment.
    writable = (DATA_DIR, EXPORT_DIR)
    for folder in writable:
        folder.mkdir(parents=True, exist_ok=True)
    if not IS_VERCEL:
        for folder in (SAMPLE_IMPORT_DIR, PUBLIC_STATIC_DIR, BASE_DIR / "data"):
            folder.mkdir(parents=True, exist_ok=True)
