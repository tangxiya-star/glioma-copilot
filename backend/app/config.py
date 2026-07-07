"""Central config — loads secrets from the repo-root .env (gitignored)."""

import os
from pathlib import Path

from dotenv import load_dotenv

# backend/app/config.py -> parents[2] is the repo root, where .env lives.
REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Per-agent model selection. Default = Sonnet 5 (fast + cheap for high-volume,
# rule-driven calls); escalate only the calls where reasoning quality is the
# score — the verification agent catching its own overclaims — to Opus 4.8.
SONNET = "claude-sonnet-5"
OPUS = "claude-opus-4-8"

AGENT_MODELS = {
    "extract": os.getenv("EXTRACT_MODEL", SONNET),   # report -> structured markers
    "classify": os.getenv("CLASSIFY_MODEL", SONNET),  # WHO CNS5 classification
    "fit": os.getenv("FIT_MODEL", SONNET),            # per-criterion met/not-met/unknown (high volume)
    "draft": os.getenv("DRAFT_MODEL", SONNET),        # evidence brief drafting
    "verify": os.getenv("VERIFY_MODEL", OPUS),        # the money-moment: catch/rewrite overclaims
    "investigate": os.getenv("INVESTIGATE_MODEL", SONNET),
    "explain": os.getenv("EXPLAIN_MODEL", SONNET),    # plain-language rendering
    "summary": os.getenv("SUMMARY_MODEL", SONNET),    # shared-decision summary
}

# Default model for ad-hoc calls that don't name an agent.
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", SONNET)


def model_for(agent: str) -> str:
    """Return the configured model for a named agent, falling back to the default."""
    return AGENT_MODELS.get(agent, CLAUDE_MODEL)


# Reasoning depth per agent, via output_config.effort (Sonnet 5 / Opus 4.8 use
# adaptive thinking + effort; the old budget_tokens is rejected with a 400).
# Lower effort = the model thinks less and starts emitting visible output sooner
# (snappier streaming). fit is mechanical per-criterion matching -> "low" for a
# fast first token; verify is the deep-reasoning money-moment -> "high".
AGENT_EFFORT = {
    "extract": os.getenv("EXTRACT_EFFORT", "low"),
    "classify": os.getenv("CLASSIFY_EFFORT", "low"),
    "fit": os.getenv("FIT_EFFORT", "low"),
    "verify": os.getenv("VERIFY_EFFORT", "high"),
    "investigate": os.getenv("INVESTIGATE_EFFORT", "medium"),
    "explain": os.getenv("EXPLAIN_EFFORT", "low"),
    "summary": os.getenv("SUMMARY_EFFORT", "medium"),
}


def tuning_for(agent: str) -> dict:
    """Return extra Anthropic kwargs (adaptive thinking + effort) for an agent call."""
    effort = AGENT_EFFORT.get(agent, "high")
    return {
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": effort},
    }

# Comma-separated allowed origins for CORS (Next.js dev + deployed frontend).
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS", "http://localhost:3000"
).split(",")
