-- Glioma Copilot schema. Relationships modeled in Postgres (not Neo4j) for the MVP.

CREATE TABLE IF NOT EXISTS patients (
    id             TEXT PRIMARY KEY,
    label          TEXT,
    report         TEXT NOT NULL,
    profile        JSONB,          -- normalized marker profile (with source spans)
    classification JSONB,          -- WHO CNS5 result (diagnosis, grade, reasoning)
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS trials (
    nct_id      TEXT PRIMARY KEY,
    title       TEXT,
    status      TEXT,
    conditions  JSONB,
    eligibility TEXT,
    locations   JSONB,
    url         TEXT,
    fetched_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Per-criterion fit verdicts (Day 3 populates this).
CREATE TABLE IF NOT EXISTS eligibility_results (
    id          BIGSERIAL PRIMARY KEY,
    patient_id  TEXT REFERENCES patients(id) ON DELETE CASCADE,
    nct_id      TEXT REFERENCES trials(nct_id) ON DELETE CASCADE,
    criterion   TEXT NOT NULL,
    kind        TEXT,             -- inclusion | exclusion
    verdict     TEXT,             -- met | not_met | unknown
    citation    TEXT,             -- eligibility text line supporting the verdict
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_elig_patient ON eligibility_results (patient_id);
CREATE INDEX IF NOT EXISTS idx_elig_nct ON eligibility_results (nct_id);
