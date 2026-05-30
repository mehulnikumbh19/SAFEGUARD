from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
EXPORT_DIR = BASE_DIR / "exports"
SAMPLE_IMPORT_DIR = BASE_DIR / "sample_imports"
DB_PATH = DATA_DIR / "safeguard.db"


class Config:
    SECRET_KEY = "dev-safeguard-local-key"
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH.as_posix()}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False


def ensure_directories():
    for folder in (DATA_DIR, EXPORT_DIR, SAMPLE_IMPORT_DIR):
        folder.mkdir(parents=True, exist_ok=True)
