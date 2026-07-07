"""Postgres (Neon) access helpers via psycopg 3."""

import json
from pathlib import Path
from typing import Any

import psycopg

from .config import DATABASE_URL

SCHEMA_SQL = (Path(__file__).parent / "schema.sql").read_text()


def get_connection() -> psycopg.Connection:
    """Open a new connection. Caller is responsible for closing / using `with`."""
    return psycopg.connect(DATABASE_URL)


def db_ping() -> bool:
    """Cheap health check — returns True if the DB answers SELECT 1."""
    with psycopg.connect(DATABASE_URL) as conn:
        row = conn.execute("SELECT 1").fetchone()
        return row is not None and row[0] == 1


def init_schema() -> None:
    """Create tables if they don't exist (idempotent)."""
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(SCHEMA_SQL)


def upsert_patient(patient: dict[str, Any], profile=None, classification=None) -> None:
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            """
            INSERT INTO patients (id, label, report, profile, classification, updated_at)
            VALUES (%s, %s, %s, %s, %s, now())
            ON CONFLICT (id) DO UPDATE SET
                label = EXCLUDED.label,
                report = EXCLUDED.report,
                profile = EXCLUDED.profile,
                classification = EXCLUDED.classification,
                updated_at = now()
            """,
            (
                patient["id"],
                patient.get("label"),
                patient["report"],
                json.dumps(profile) if profile is not None else None,
                json.dumps(classification) if classification is not None else None,
            ),
        )


def upsert_trials(trials: list[dict[str, Any]]) -> int:
    with psycopg.connect(DATABASE_URL) as conn:
        for t in trials:
            conn.execute(
                """
                INSERT INTO trials (nct_id, title, status, conditions, eligibility, locations, url, fetched_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, now())
                ON CONFLICT (nct_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    status = EXCLUDED.status,
                    conditions = EXCLUDED.conditions,
                    eligibility = EXCLUDED.eligibility,
                    locations = EXCLUDED.locations,
                    url = EXCLUDED.url,
                    fetched_at = now()
                """,
                (
                    t["nct_id"],
                    t.get("title"),
                    t.get("status"),
                    json.dumps(t.get("conditions")),
                    t.get("eligibility"),
                    json.dumps(t.get("locations")),
                    t.get("url"),
                ),
            )
    return len(trials)


def store_eligibility_results(patient_id: str, nct_id: str, items: list[dict[str, Any]]) -> int:
    """Replace this patient×trial's fit verdicts with a fresh set."""
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            "DELETE FROM eligibility_results WHERE patient_id = %s AND nct_id = %s",
            (patient_id, nct_id),
        )
        for it in items:
            conn.execute(
                """
                INSERT INTO eligibility_results (patient_id, nct_id, criterion, kind, verdict, citation)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    patient_id,
                    nct_id,
                    it.get("criterion"),
                    it.get("kind"),
                    it.get("verdict"),
                    it.get("citation"),
                ),
            )
    return len(items)


def db_counts() -> dict[str, int]:
    """Row counts — proves the stored data is queryable."""
    with psycopg.connect(DATABASE_URL) as conn:
        return {
            "patients": conn.execute("SELECT count(*) FROM patients").fetchone()[0],
            "trials": conn.execute("SELECT count(*) FROM trials").fetchone()[0],
            "eligibility_results": conn.execute(
                "SELECT count(*) FROM eligibility_results"
            ).fetchone()[0],
        }
