"""Central config — loads secrets from the repo-root .env (gitignored)."""

import os
from pathlib import Path

from dotenv import load_dotenv

# backend/app/config.py -> parents[2] is the repo root, where .env lives.
REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Sonnet 5 for agent calls; escalate a call to Opus 4.8 only where reasoning needs it.
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")

# Comma-separated allowed origins for CORS (Next.js dev + deployed frontend).
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS", "http://localhost:3000"
).split(",")
