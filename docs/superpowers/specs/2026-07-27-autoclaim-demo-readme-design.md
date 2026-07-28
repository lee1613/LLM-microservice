# AutoClaim AI — Demo UI + README Design

**Date:** 2026-07-27
**Hackathon:** AI Agent Olympics
**Author:** brainstorming session (grilled + locked 2026-07-27)

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
  drag-drops to Vercel/Netlify/GitHub Pages with zero build. Data is inlined
  into a marked `<script id="demo-data">` region — no separate `.js`, no CORS
  risk on `file://`.
- **Layout A — horizontal pipeline** (chosen from mockups).
- **All 5 scenarios** B001–B005 selectable. Default on load = **B001**.
- **Honesty:** README states the true stack (FastAPI/Python, Vultr Serverless
  LLM, vanilla-JS demo, SQLite). No fictional React/Node claims. The recorded
  demo claims **only** what the golden contracts actually produced.

## v2 redesign — inspectable playback (2026-07-28, brainstormed + approved)

v1 (Tasks 1–4, shipped: clean chips + one-line verdict + banner) only showed
*whether* each node passed — no input document, no visible agent reasoning. v2
adds two **opt-in disclosure layers** on top of the unchanged v1 auto-play, so
the headline video stays pristine while the reader can delve in.

Both layers are backed by REAL contract data (no fabrication) — verified present
in the golden JSONs:

- **Input claim document** ← `stage_1_intake._document_extraction`:
  `itemised_charges` (5 line items), `total_billed_amount`,
  `primary_diagnosis_icd10`, `procedure_cpt_codes`, admission/discharge dates,
  `attending_physician`, `physician_license_no`, `pre_authorisation_no`,
  `provider_name_on_bill`, `summary_narrative`.
- **Per-node reasoning trace** ← each stage's sub-dicts: N1 `_validation`
  (10 checks), N2 `_db_lookups`, N3 `_plan_document_lookup` + `_computation`,
  N4 `_registry_lookups` (4 tools, each `query`/`result`/`*_claim`),
  N5 `_arithmetic_verify` (line-by-line math), N6 `_payment_details`/
  `_validation`/`_ledger_writes`.

### v2 decisions (locked)

- **Q1 — Disclosure model: click-to-expand (A).** Auto-play unchanged. Each node
  chip is clickable → opens a reasoning drawer. A top-level **"View claim
  document"** button opens the document viewer. Reader drives the depth.
- **Q2 — Claim document viewer: styled document + raw-JSON toggle (C).** Renders
  a styled claim/hospital-bill document (header, itemised-charges table + total,
  diagnosis/CPT, physician, pre-auth) from real extracted fields, plus a toggle
  to the machine-read extracted JSON — which doubles as Node 1's extraction
  story. Per scenario. We do NOT have the original scanned PDF; the document is
  reconstructed from extracted fields and labelled honestly as the claim document.
- **Q3 — Reasoning drawer: uniform step model (A).** One render path: a drawer is
  a list of steps `{label, detail, status}`. The build script distills each
  node's real sub-dicts into steps — N4's 4 tools → 4 steps (query as label,
  result+claim as detail, pass/fail status); N5's arithmetic lines → steps;
  N1's checks → pass/fail steps; N2/N3/N6 similarly. Denied/halted scenarios:
  the failing node's drawer shows which check tripped; skipped nodes get no drawer.

### v2 build/data changes

- `demo/build_demo_data.py` grows to also emit, per scenario:
  `document` (itemised charges + fields + narrative), `extracted` (curated subset
  of `_document_extraction`), and `stages[i].steps[]` distilled from the real
  sub-dicts. N4 steps and N5 arithmetic come straight from structured sub-dicts
  (low curation); N1/N2/N3/N6 get light curation.
- Inline data grows (curated fields + steps for 5 scenarios) but still excludes
  the raw ~25 KB×5 contracts — only display-curated fields ship.
- Existing money-path `_self_check` stays as the regression gate; extend it to
  assert each scenario has a `document` and that ran-nodes have non-empty `steps`.
- Still one self-contained `index.html`, inline data, no framework, no build tool.
- Playback animation timing unchanged.

### Grilled decisions (locked)

- **No DB-query line in the demo.** DB queries are company-specific placeholders;
  showing them overclaims and adds no value. Dropped entirely.
- **Detail card per node = `capability` + `verdict` + `keyNumbers`** (Q2).
  `capability` is static per node (6 strings, shared across scenarios);
  `verdict` and `keyNumbers` vary per scenario.
- **RAG cross-referencing = headline capability but NOT fully built.** Node 4
  currently does *deterministic* tool lookups (registry, SMC, ICD-10, CPT, RPS,
  pre-auth) — no vector retrieval. RAG is framed as **roadmap in the README
  only**, never claimed in the recorded demo (Q3).
- **Hero leads with autonomy, not a speed number** (Q4). No falsifiable
  "6 seconds" claim — the live API is down and can't be measured.
- **Banner is binary:** APPROVED (green) / DENIED (red) (Q5).
- **LLM nodes animate differently from deterministic nodes** (Q8): nodes
  1/3/4/5 show a *"reasoning…"* shimmer (~900 ms); nodes 2/6 snap fast (~300 ms).
  Visually teaches AI-vs-rules and frames deterministic guardrails as a design
  choice, not a gap.
- **Live Demo badge → GitHub Pages** (Q7): deploy the self-contained
  `index.html` to GitHub Pages so the badge is a real one-click demo.

## Deliverable 1 — `demo/index.html`

### Data pipeline

- `demo/build_demo_data.py` (one-time, regenerable): reads the 5 golden
  contracts `data/health-insurance-claim/synthetic data/claim_BXXX_full_pipeline.json`
  and distills each into **display-only** fields per stage. Writes the result
  inline into the marked `<script id="demo-data">` region of `index.html`.
- **CRITICAL build rule:** read each stage's structured **`_output`** dict —
  **never** the top-level `_outcome` narrative blurb. The blurb is stale/wrong
  in at least B002 (says "Approved… Disbursed via cheque" while `_output` shows
  `halted`, `net_payable = 0`, `zero_benefit`). `_output` is authoritative.
- Distilled shape per scenario:
  - `id`, `title` (from `_scenario`), `outcome` (derived from `_output`, not the blurb)
  - `stages[1..6]`: `{ name, status: pass|fail|skipped, capability, verdict, keyNumbers }`
  - `final`: `{ status: APPROVED|DENIED, amount, reason, note? }`
- The full ~25 KB raw JSON is NOT shipped — only the summarized display fields.

### UI (Layout A, dark theme)

- **Header:** title, scenario `<select>` (B001–B005), "Process Claim" button,
  reset. A small badge: *"Playback mode — captured pipeline output. Run live
  locally → see README."*
- **Pipeline row:** 6 node chips (Intake → Verify → Eligibility → Medical →
  Adjudication → Disbursement) with connectors. Node states:
  `pending | active | pass | fail | skipped`. Active LLM nodes show a
  *"reasoning…"* label.
- **Detail card** (below the row): updates per node as it resolves. Shows the
  node's **capability**, **verdict**, and **keyNumbers** — the agent-reasoning
  + adjudication-math showcase, visible on screen. No DB queries.
- **Result banner:** `APPROVED · SGD 14,962.50` (green) or
  `DENIED · <reason>` (red).

### Animation / behaviour

- On "Process Claim": step through nodes. Deterministic nodes (2,6) resolve
  fast (~300 ms); LLM nodes (1,3,4,5) show a *"reasoning…"* shimmer (~900 ms)
  before resolving. `active` → `pass`/`fail`; detail card swaps to that node's data.
- On a failing node (B003 halts @ Node 3 waiting-period; B005 halts @ Node 2
  duplicate claim): pipeline stops, downstream nodes render `skipped` (greyed),
  denial reason shown in the red banner.
- Reset returns all nodes to `pending`.

### Scenario outcomes (from golden contract `_output`)

| ID | Scenario | Real final outcome |
|----|----------|--------------------|
| B001 | Pneumonia hospitalisation, GOLD | **APPROVED** · SGD 14,962.50 disbursed (direct_credit DBS, T+3) |
| B002 | Hypertension outpatient, SILVER | **APPROVED · SGD 0 disbursed** — zero-benefit: SGD 133 base fully absorbed by remaining deductible; claimant liable SGD 380. Note shown in detail card. |
| B003 | Normal delivery maternity, GOLD | **DENIED @ Node 3** (maternity waiting period, 65 days elapsed) |
| B004 | Appendectomy surgical, BRONZE | **APPROVED** · SGD 1,120.00 disbursed (60% non-panel + SGD 3,500 deductible + 20% co-pay; claimant liable SGD 10,680) |
| B005 | Fracture emergency, GOLD | **DENIED @ Node 2** (duplicate of paid claim CLM-2025-0000877) |

**B002 special handling:** rendered as an **APPROVED (green)** scenario — all 6
nodes pass. A subsection/side-note in the detail card explains the zero-benefit
status: the (already non-panel-discounted) covered base of SGD 133 fell entirely
within the member's remaining SGD 1,820 deductible, so net payable = SGD 0 and
Node 6 halts with `ZERO_BENEFIT_NO_DISBURSEMENT`. Conservation: 0 payable +
380 liability = 380 billed. This showcases the adjudication engine's math, not a
denial.

## Deliverable 2 — `README.md` (gradual disclosure)

### First glance (scannable in ~10s)

- **Hero headline** — autonomy angle, no speed number. Working draft:
  *"Six AI agents settle an insurance claim end-to-end — no human in the loop."*
- One-line pitch + badges: **Live Demo (→ GitHub Pages)** · Built for AI Agent
  Olympics · License MIT.
- Demo GIF placeholder (user records into it).
- 3-bullet "what it does".
- Mermaid flow diagram (adapted to real 6-node names).

### Gradual disclosure — collapsed `<details>` blocks

- ▸ **How the Agents Reason** — agentic tool-loops (Node 1 Nemotron reasoning
  model → `parse_pdf_file`; Node 4 DeepSeek → 6 tools); self-correcting JSON via
  `call_llm_with_json_retry` (3-retry reflection loop, strips `<think>` tags).
- ▸ **Deterministic Guardrails over LLM** — exclusion ICD ranges,
  `annual_limit_remaining <= 0`, medical failure priority force-override the model.
  Framed as a deliberate safety design, not a limitation.
- ▸ **Traceability** — Pydantic field lineage carried forward node→node;
  interpreted params + verdicts per stage; validated field-by-field against
  golden contracts.
- ▸ **Run it Live Locally** — real setup: `.venv`, `.env` with
  `VULTR_SERVERLESS_INFERENCE_API_KEY`, `uvicorn app.main:app --reload`, then
  `/docs` or `test/qc_pipeline_b001.py` for a real end-to-end LLM run.
- ▸ **Tech stack + roadmap** — FastAPI/Python, Vultr Serverless LLM
  (Nemotron + DeepSeek), vanilla-JS demo, SQLite, K8s/VKE. Roadmap:
  (1) **RAG cross-referencing** — swap Node 4's deterministic registry/CPT
  lookups for retrieval against payer-policy corpora (the hard part, not yet
  built); (2) host live inference (currently captured playback for reliability).

### Deepest dive — `docs/ARCHITECTURE.md`

Full six-node breakdown, model table, three-DB schema summary, guardrail logic,
deployment notes. Linked from README to keep the main page light.

## Out of scope (ponytail)

- No React, no build tooling, no bundler.
- No live-API calls, no backend required for the demo.
- No real-time local inference in the demo itself (offered as local setup +
  roadmap only).
- No third banner state — B002's zero-benefit case rides the APPROVED banner
  with a note.

## Files touched

- `demo/index.html` (new — self-contained, inline data)
- `demo/build_demo_data.py` (new — reads `_output`, rewrites the inline script region)
- `README.md` (new)
- `docs/ARCHITECTURE.md` (new)
- `LICENSE` (new — MIT; README badge claims it)
- `.gitignore` (add `.superpowers/`)
