from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.database.schema import Base


@lru_cache
def get_engine() -> Engine:
    s = get_settings()
    s.data_dir.mkdir(parents=True, exist_ok=True)
    kwargs = {"connect_args": {"check_same_thread": False}} if s.database_url.startswith("sqlite") else {}
    return create_engine(s.database_url, **kwargs)


@lru_cache
def _session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(get_engine())


def get_db() -> Iterator[Session]:
    db = _session_factory()()
    try:
        yield db
    finally:
        db.close()
