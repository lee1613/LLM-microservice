# AutoClaim AI — Demo UI + README Design

**Date:** 2026-07-27
**Hackathon:** AI Agent Olympics
**Author:** brainstorming session

## Goal

Produce two recruiter-facing deliverables for the existing six-node FastAPI
health-insurance claims pipeline:

1. An **interactable static demo** (`demo/index.html`) that visually plays a real
   claim through all six nodes — for screen-recording a short video.
2. A **concise, gradual-disclosure `README.md`** with a catchy hero, plus a
   deeper `docs/ARCHITECTURE.md`.

## Constraints & Decisions

- **The live API is dead.** The demo must not call it. → static playback.
- **Static playback only.** Data captured from real pipeline runs is baked into
  the HTML and streamed to the UI on click. No local processing, no LLM calls,
  no backend needed to view. Reliable on camera, deployable anywhere.
- **The backend is real and works.** Dynamic live processing is offered as a
  local setup guide in the README, and flagged as roadmap (hosted live inference
  is the next milestone).
- **Single self-contained file.** `demo/index.html` opens via `file://` and
  drag-drops to Vercel/Netlify/GitHub Pages with zero build.
- **Layout A — horizontal pipeline** (chosen from mockups).
- **All 5 scenarios** B001–B005 selectable.
- **Honesty:** README states the true stack (FastAPI/Python, Vultr Serverless
  LLM, vanilla-JS demo, SQLite). No fictional React/Node claims.

## Deliverable 1 — `demo/index.html`

### Data pipeline

- `demo/build_demo_data.py` (one-time, regenerable): reads the 5 golden
  contracts `data/health-insurance-claim/synthetic data/claim_BXXX_full_pipeline.json`
  and distills each into **display-only** fields per stage. Writes the result
  inline into the HTML (or a `demo/demo_data.js` that is then inlined).
- Distilled shape per scenario:
  - `id`, `title` (from `_scenario`), `outcome` (from `_outcome`)
  - `stages[1..6]`: `{ name, status: pass|fail|skipped, query, params, verdict, keyNumbers }`
  - `final`: `{ status: APPROVED|DENIED, amount, reason }`
- The full 25 KB raw JSON is NOT shipped — only the summarized display fields.

### UI (Layout A, dark theme)

- **Header:** title, scenario `<select>` (B001–B005), "Process Claim" button,
  reset. A small badge: *"Playback mode — captured pipeline output. Run live
  locally → see README."*
- **Pipeline row:** 6 node chips (Intake → Verify → Eligibility → Medical →
  Adjudication → Disbursement) with connectors. Node states:
  `pending | active | pass | fail | skipped`.
- **Detail card** (below the row): updates per node as it resolves. Shows the
  node's real **DB query**, **LLM-interpreted parameters**, and **verdict** —
  this is the traceability + agent-reasoning showcase, visible on screen.
- **Result banner:** `APPROVED · SGD 14,962.50` (green) or
  `DENIED · <reason>` (red).

### Animation / behaviour

- On "Process Claim": step through nodes with ~600 ms `setTimeout` each.
  `active` → resolve to `pass`/`fail`, detail card swaps to that node's data.
- On a failing node (B003 halts @ Node 3 waiting-period; B005 halts @ Node 2
  duplicate claim): pipeline stops, downstream nodes render `skipped` (greyed),
  denial reason shown in the banner.
- Reset returns all nodes to `pending`.

### Scenario outcomes (from golden contracts)

| ID | Scenario | Outcome |
|----|----------|---------|
| B001 | Pneumonia hospitalisation, GOLD | APPROVED · SGD 14,962.50 disbursed |
| B002 | Hypertension outpatient, SILVER | Non-panel flag, partial deductible |
| B003 | Normal delivery maternity, GOLD | REJECTED @ Node 3 (waiting period) |
| B004 | Appendectomy surgical, BRONZE | APPROVED w/ 60% non-panel rate + deductible |
| B005 | Fracture emergency, GOLD | REJECTED @ Node 2 (duplicate claim) |

## Deliverable 2 — `README.md` (gradual disclosure)

### First glance (scannable in ~10s)

- **Hero headline** (catchy). Working draft:
  *"Insurance claims take days. AutoClaim AI settles them in 6 seconds."*
- One-line pitch + badges: Live Demo · Built for AI Agent Olympics · License MIT.
- Demo GIF placeholder (user records into it).
- 3-bullet "what it does".
- Mermaid flow diagram (adapted to real 6-node names).

### Gradual disclosure — collapsed `<details>` blocks

- ▸ **How the Agents Reason** — agentic tool-loops (Node 1 Nemotron reasoning
  model → `parse_pdf_file`; Node 4 DeepSeek → 6 tools); self-correcting JSON via
  `call_llm_with_json_retry` (3-retry reflection loop, strips `<think>` tags).
- ▸ **Deterministic Guardrails over LLM** — exclusion ICD ranges,
  `annual_limit_remaining <= 0`, medical failure priority force-override the model.
- ▸ **Traceability** — Pydantic field lineage carried forward node→node; DB
  queries + interpreted params logged per stage; validated field-by-field
  against golden contracts.
- ▸ **Run it Live Locally** — real setup: `.venv`, `.env` with
  `VULTR_SERVERLESS_INFERENCE_API_KEY`, `uvicorn app.main:app --reload`, then
  `/docs` or `test/qc_pipeline_b001.py` for a real end-to-end LLM run.
- ▸ **Tech stack + roadmap** — FastAPI/Python, Vultr Serverless LLM
  (Nemotron + DeepSeek), vanilla-JS demo, SQLite, K8s/VKE. Roadmap: host live
  inference (currently captured playback for reliability).

### Deepest dive — `docs/ARCHITECTURE.md`

Full six-node breakdown, model table, three-DB schema summary, guardrail logic,
deployment notes. Linked from README to keep the main page light.

## Out of scope (ponytail)

- No React, no build tooling, no bundler.
- No live-API calls, no backend required for the demo.
- No real-time local inference in the demo itself (offered as local setup +
  roadmap only).

## Files touched

- `demo/index.html` (new)
- `demo/build_demo_data.py` (new)
- `demo/demo_data.js` (new, generated; may be inlined into index.html)
- `README.md` (new)
- `docs/ARCHITECTURE.md` (new)
- `.gitignore` (add `.superpowers/`)
