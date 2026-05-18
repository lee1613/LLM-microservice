# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim AS base

# Prevents Python from writing .pyc files; enables unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8

WORKDIR /app

# ── System dependencies ───────────────────────────────────────────────────────
# sqlite3 CLI (useful for debugging), ca-certificates for HTTPS to NLM/CMS APIs
RUN apt-get update && apt-get install -y --no-install-recommends \
        sqlite3 \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ── Non-privileged runtime user ───────────────────────────────────────────────
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# ── Python dependencies ───────────────────────────────────────────────────────
COPY requirements.txt ./requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install -r requirements.txt

# ── Application source code ───────────────────────────────────────────────────
COPY app ./app
COPY data ./data
COPY setup_cpt_db.py ./setup_cpt_db.py

# ── One-time build-time setup ─────────────────────────────────────────────────
# The main SQLite databases (database.db, registry.db) are shipped pre-built
# inside data/ and copied above — no runtime seeding required.
#
# Build the CMS PFS CPT reference database (tries live CMS download first,
# falls back to embedded 2024 seed of ~120 common CPT codes).
# data/cpt_reference.db is already present from local dev, but rebuild to ensure
# it is fresh and matches the Python 3.11 environment.
RUN python setup_cpt_db.py && rm setup_cpt_db.py

# ── Runtime user ──────────────────────────────────────────────────────────────
# Make the data directory (SQLite files) owned by appuser so they are writable
# at runtime for ledger writes (deductible_ledger, claim_utilisation, claims).
RUN chown -R appuser:appuser /app/data
USER appuser

# ── Network ───────────────────────────────────────────────────────────────────
EXPOSE 8000

# ── Entrypoint ────────────────────────────────────────────────────────────────
# Single worker per container — scale horizontally via K8s replicas.
# LLM inference calls are I/O-bound so a single uvicorn worker is sufficient;
# use --workers 1 to avoid SQLite write contention across forked processes.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
