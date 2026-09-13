from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

import os
from pathlib import Path

# Default to a user-local app data directory (e.g., ~/.assetsentinel)
DEFAULT_DB_DIR = Path.home() / ".assetsentinel"
DEFAULT_DB_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "assetsentinel.db"

# Allow environment variable override
db_path_str = os.getenv("ASSETSENTINEL_DB_PATH", str(DEFAULT_DB_PATH))
db_path = Path(db_path_str)
db_path.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{db_path}")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
