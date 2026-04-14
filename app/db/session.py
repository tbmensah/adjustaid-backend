from collections.abc import Generator
from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

SessionLocal = sessionmaker(autoflush=False, autocommit=False, expire_on_commit=False)

# Supabase pooler URLs often include ?pgbouncer=true; psycopg rejects it as an unknown libpq option.
_DROP_QUERY_KEYS = frozenset({"pgbouncer"})


def _strip_query_params(url: str, remove: frozenset[str]) -> str:
    parsed = urlparse(url)
    if not parsed.query:
        return url
    kept = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k.lower() not in remove]
    new_query = urlencode(kept)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))


def _normalize_database_url(url: str) -> str:
    """Use psycopg3 driver when URL is a plain postgresql:// DSN; strip params psycopg cannot use."""
    if url.startswith("postgresql://") and not url.startswith("postgresql+"):
        url = "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return _strip_query_params(url, _DROP_QUERY_KEYS)


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    if not settings.database_url:
        msg = "DATABASE_URL is not set"
        raise RuntimeError(msg)
    url = _normalize_database_url(settings.database_url)
    return create_engine(url, pool_pre_ping=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal(bind=get_engine())
    try:
        yield db
    finally:
        db.close()
