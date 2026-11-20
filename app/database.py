import os
from collections.abc import Iterator

import psycopg
from psycopg import Connection
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.config import get_settings

_pool: ConnectionPool | None = None


def get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            get_settings().database_url,
            min_size=1,
            max_size=5,
            kwargs={"row_factory": dict_row},
            open=True,
        )
    return _pool


def get_connection() -> Iterator[Connection]:
    """Une connexion par requête. Le commit est fait si la requête réussit, le rollback sinon."""
    if os.environ.get("VERCEL"):
        # Les fonctions Vercel s'arrêtent entre deux requêtes : pas de pool, le pooler de Neon s'en charge.
        with psycopg.connect(get_settings().database_url, row_factory=dict_row) as conn:
            yield conn
    else:
        with get_pool().connection() as conn:
            yield conn


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None
