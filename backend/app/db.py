"""Postgres (Neon) access helpers via psycopg 3."""

import psycopg

from .config import DATABASE_URL


def get_connection() -> psycopg.Connection:
    """Open a new connection. Caller is responsible for closing / using `with`."""
    return psycopg.connect(DATABASE_URL)


def db_ping() -> bool:
    """Cheap health check — returns True if the DB answers SELECT 1."""
    with psycopg.connect(DATABASE_URL) as conn:
        row = conn.execute("SELECT 1").fetchone()
        return row is not None and row[0] == 1
