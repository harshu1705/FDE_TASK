from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# From setup_db.ps1: docker run --name fde_postgres -e POSTGRES_PASSWORD=postgres -d -p 5432:5432 postgres:15
# DB_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@127.0.0.1:5432/postgres"
)

engine = create_engine(DB_URL, pool_size=20, max_overflow=0)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
