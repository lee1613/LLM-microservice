# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Run locally (development):**
```powershell
.venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Run via Docker Compose:**
```powershell
docker compose up --build
```

**Run a QC end-to-end test against the live API:**
```powershell
.venv\Scripts\python.exe test\qc_pipeline_b001.py
# Reports written to test\qc_report_b001.md
```

**Reset the ledger DB between test runs:**
```powershell
# Via HTTP (requires running server)
curl -X POST http://localhost:8000/dev/reset
# Or directly
.venv\Scripts\python.exe reset_db.py
```

**Rebuild the CPT reference database:**
```powershell
.venv\Scripts\python.exe setup_cpt_db.py
```

## Architecture

A **six-node sequential health insurance claims pipeline** built with FastAPI. Each node's JSON output is passed directly as the next node's input — Pydantic schemas carry all fields forward through the entire pipeline.

```
POST /intake/process        Node 1: PDF extraction & document parsing
POST /verification/process  Node 2: Policy/member validation (deterministic)
POST /eligibility/process   Node 3: Benefit limits & waiting period check
POST /medical/process       Node 4: CPT/ICD-10 validation, provider accreditation
POST /adjudication/process  Node 5: Cost-sharing arithmetic & net payable
POST /disbursement/process  Node 6: Payment channel validation & ledger commit
```

### Module structure

Every stage under `app/` follows the same four-file pattern:
- `agent.py` — business logic (orchestrates tools and/or LLM calls)
- `router.py` — FastAPI endpoint, request parsing
- `schemas.py` — Pydantic input/output models
- `tools.py` — SQLite queries and external API calls

### LLM usage

LLM calls are concentrated in four nodes; Nodes 2 and 6 are fully deterministic:

| Node | Model | Role |
|------|-------|------|
| 1 — Intake | `nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16` | Agentic loop: calls `parse_pdf_file` tool to read PDFs, returns structured JSON |
| 3 — Eligibility | `nvidia/DeepSeek-V3.2-NVFP4` | Reads plan document text, extracts annual/per-claim/lifetime limits, renders eligibility judgment |
| 4 — Medical Review | `nvidia/DeepSeek-V3.2-NVFP4` | Agentic loop: calls 6 tools (provider registry, physician SMC registry, ICD-10 validation, CPT lookup, RPS benchmark, pre-auth check) |
| 5 — Adjudication | `nvidia/DeepSeek-V3.2-NVFP4` | Extracts deductible/co-pay/co-insurance params from plan document; generates adjudication notes |

All LLM calls use the Vultr Serverless Inference endpoint (`https://api.vultrinference.com/v1`) via an OpenAI-compatible client. The shared utility `app/core/llm_utils.py:call_llm_with_json_retry` wraps every JSON-returning call with a reflection loop (up to 3 retries) that feeds parse errors back to the model and strips `<think>` tags and markdown fences from reasoning models.

### Deterministic guardrails over LLM outputs

Eligibility and Medical Review nodes explicitly override LLM verdicts with deterministic safety checks:
- If ICD-10 codes match hard-coded exclusion ranges (cosmetic, self-inflicted, substance abuse, war), `eligible` is forced `False` regardless of the LLM.
- If `annual_limit_remaining <= 0` (computed from DB), `eligible` is forced `False`.
- Medical failure priority: invalid physician licence → pre-auth failure → invalid/implausible CPT codes.

### Databases

Three SQLite files under `data/health-insurance-claim/synthetic data/`:
- `database.db` — policies, members, claims, claim sequence counter, deductible ledger, claim utilisation, pre-authorisations
- `registry.db` — provider and physician registries
- `data/cpt_reference.db` — CMS Physician Fee Schedule CPT reference (built at Docker image build time by `setup_cpt_db.py`)

The `POST /dev/reset` endpoint (defined in `app/dev.py`) truncates ledger/claim rows written during a test run; it is called at the start of every QC script.

### Environment

Required in `.env`:
```
VULTR_SERVERLESS_INFERENCE_API_KEY=<key>
```

### QC test scripts

`test/qc_pipeline_bXXX.py` (B001–B005) run the full six-node pipeline against `http://149.28.144.51` (live Vultr deployment), chaining each node's actual response as the next node's input. Results are compared field-by-field against golden contracts in `data/health-insurance-claim/synthetic data/claim_BXXX_full_pipeline.json`. Non-deterministic fields (timestamps, LLM narrative text, sequence-dependent reference numbers) are explicitly skipped. Reports are written to `test/qc_report_bXXX.md`.

### Deployment

Deployed on Vultr Kubernetes Engine (VKE). The container runs a **single uvicorn worker** (`--workers 1`) to prevent SQLite write contention across forked processes — scale horizontally via K8s replicas instead. The `k8s/deployment.yaml` defines the Deployment and a `LoadBalancer` Service (public IP `149.28.144.51:80` → container `:8000`). Full build/push/deploy steps are in `DEPLOYMENT.md`.
