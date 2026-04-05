import os
import logging
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

# Primary DB: PostgreSQL by default. Fallback DB: local SQLite file.
DEFAULT_POSTGRES = "postgresql://postgres:postgres@127.0.0.1:5432/postgres"
FALLBACK_SQLITE = Path(__file__).parent / "fde_fallback.db"

raw_db_url = os.environ.get("DATABASE_URL", DEFAULT_POSTGRES)
if raw_db_url.startswith("postgres://"):
    raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)


def build_engine(db_url: str):
    connect_args = {}
    engine_opts = {}

    if db_url.startswith("sqlite:"):
        connect_args = {"check_same_thread": False}
    else:
        engine_opts = {"pool_size": 20, "max_overflow": 0}

    engine = create_engine(db_url, connect_args=connect_args, **engine_opts)
    return engine


def get_fallback_engine():
    if FALLBACK_SQLITE.exists():
        fallback_url = f"sqlite:///{FALLBACK_SQLITE.as_posix()}"
        logger.warning("Using fallback SQLite database at %s", FALLBACK_SQLITE)
        return build_engine(fallback_url)
    raise RuntimeError("Fallback SQLite database not found: %s" % FALLBACK_SQLITE)


try:
    engine = build_engine(raw_db_url)
    # Try a quick connection test to fail fast if Postgres is unavailable.
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
except Exception as exc:
    logger.warning("Primary database connection failed: %s", exc)
    engine = get_fallback_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
