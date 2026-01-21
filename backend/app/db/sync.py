"""Synchronous database connection for Alembic migrations."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

sync_engine = create_engine(
    settings.database_url_sync,
    echo=settings.debug,
)

SyncSessionLocal = sessionmaker(bind=sync_engine)
