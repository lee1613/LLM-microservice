# Architecture

AutoClaim AI is a **six-node sequential pipeline** built with FastAPI. Each node exposes
one endpoint; its JSON `_output` is passed directly as the next node's input, and Pydantic
schemas carry every field forward through the whole pipeline. Four nodes call an LLM; two
are fully deterministic.

← Back to the [README](../README.md).

## The six nodes

| # | Endpoint | Node | Engine | Role |
|---|----------|------|--------|------|
| 1 | `POST /intake/process` | Intake | `nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16` | Agentic loop: calls `parse_pdf_file` to read the claim documents, returns structured JSON. |
| 2 | `POST /verification/process` | Verify | deterministic Python | Policy in-force + member/dependent match + duplicate-claim check against the ledger. |
| 3 | `POST /eligibility/process` | Eligibility | `nvidia/DeepSeek-V3.2-NVFP4` | Reads the plan document, extracts annual/per-claim/lifetime limits and waiting periods, renders the eligibility judgment. |
| 4 | `POST /medical/process` | Medical Review | `nvidia/DeepSeek-V3.2-NVFP4` | Agentic loop over 6 tools: provider registry, physician SMC register, ICD-10 validation, CPT lookup, RPS benchmark, pre-auth check. |
| 5 | `POST /adjudication/process` | Adjudication | `nvidia/DeepSeek-V3.2-NVFP4` | Extracts deductible/co-pay/co-insurance parameters from the plan document; computes net payable + adjudication notes. |
| 6 | `POST /disbursement/process` | Disbursement | deterministic Python | Payment-channel validation + ledger commit. |

All LLM calls hit the Vultr Serverless Inference endpoint (`https://api.vultrinference.com/v1`)
through an OpenAI-compatible client.

## Module structure

Every stage under `app/` follows the same four-file pattern:

- `agent.py` — business logic (orchestrates tools and/or LLM calls)
- `router.py` — FastAPI endpoint, request parsing
- `schemas.py` — Pydantic input/output models
- `tools.py` — SQLite queries and external API calls

## LLM reliability

The shared utility `app/core/llm_utils.py:call_llm_with_json_retry` wraps every
JSON-returning LLM call with a reflection loop (up to 3 retries) that:

1. feeds any JSON parse error back to the model as a correction prompt, and
2. strips `<think>` tags and markdown fences from reasoning-model output.

This makes the structured-output contract robust even with a reasoning model that
narrates before it answers.

## Deterministic guardrails over LLM output

The Eligibility and Medical Review nodes explicitly **override** the LLM verdict with
deterministic safety checks:

- If ICD-10 codes match hard-coded exclusion ranges (cosmetic, self-inflicted, substance
  abuse, war), `eligible` is forced `False` regardless of the model.
- If `annual_limit_remaining <= 0` (computed from the ledger), `eligible` is forced `False`.
- Medical failure priority: invalid physician licence → pre-auth failure →
  invalid/implausible CPT codes.

The demo surfaces this by tagging each trace step `AI` (Nemotron/DeepSeek) or `RULE`
(deterministic Python), and — where the contract records both — showing the model verdict
and the rule that overrode it side by side.

## Databases (three SQLite files)

| File | Contents |
|------|----------|
| `database.db` | Policies, members, claims, the claim sequence counter, the deductible ledger, claim utilisation, pre-authorisations. |
| `registry.db` | Provider registry and physician registry. |
| `data/cpt_reference.db` | CMS Physician Fee Schedule CPT reference, built at image-build time by `setup_cpt_db.py`. |

SQLite was chosen for a self-contained, reproducible demo; the single-writer model is why
the API runs one uvicorn worker (below).

## Adjudication maths (the receipt)

Node 5 produces a line-by-line arithmetic receipt (`_arithmetic_verify` in the contracts):
adjudication base → deductible applied → co-pay → co-insurance → net payable → claimant
liability, closed by a **conservation check** (`payout + liability = billed`). The demo
renders these verbatim as `RULE` trace steps, so the money path is inspectable end to end.

Worked example (B002, zero-benefit): the covered base of SGD 133 falls entirely within the
member's remaining deductible, so net payable = SGD 0 and Node 6 halts with
`ZERO_BENEFIT_NO_DISBURSEMENT`; conservation is `0 payable + 380 liability = 380 billed`.
This is the adjudication engine doing its job, not a denial — the demo shows it on the
green APPROVED banner with an explanatory note.

## Deployment

Deployed on **Vultr Kubernetes Engine (VKE)**. The container runs a **single uvicorn
worker** (`--workers 1`) to prevent SQLite write contention across forked processes — scale
horizontally with K8s replicas instead. `k8s/deployment.yaml` defines the Deployment and a
`LoadBalancer` Service. Full build/push/deploy steps live in
[`DEPLOYMENT.md`](../DEPLOYMENT.md).

> The public live API is currently down; the demo therefore ships as captured playback of
> real runs. Hosted live inference is the next roadmap milestone.

## Roadmap

1. **RAG cross-referencing** — Node 4 currently does deterministic tool lookups (registry,
   SMC, ICD-10, CPT, RPS, pre-auth) with no vector retrieval. Swapping these for retrieval
   against payer-policy corpora is the headline next step.
2. **Hosted live inference** — replace captured playback with a hosted end-to-end run.
