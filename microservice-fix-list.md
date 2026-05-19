# gem-squared-microservice — Fix List (hand-off to teammate)

**For:** owner of `gem-squared-microservice.139.180.136.212.nip.io`
**From:** Kritik seat, AI Agent Olympics project
**Date:** 2026-05-19
**Severity legend:** 🔴 blocker · 🟠 high · 🟡 medium · 🟢 nice-to-have
**Evidence:** `api-verification-report.md` (same folder) — full probe transcript

---

## TL;DR

Six endpoints reachable. End-to-end claim flow does not work as documented in `API_USAGE.md`. Five concrete fixes below in priority order. Items 1–3 are blocking for any external caller (TechEx, AIO crafter, the doc's own Python example).

---

## Fix 1 — 🔴 `/verification/process` rejects request bodies

### Symptom
```bash
$ curl -sS -X POST $BASE/verification/process -H 'Content-Type: application/json' -d @stage_1_output.json
{"detail":[{"type":"missing","loc":["query","raw_text"],"msg":"Field required","input":null}]}
```

OpenAPI declares **only** a `raw_text` query parameter:
```yaml
/verification/process:
  post:
    parameters:
      - name: raw_text
        in: query
        required: true
        schema: {type: string}
    # no requestBody declared
```

### Why it's a blocker
The doc says "Pass Node 1 response JSON directly as input." All other 5 endpoints accept JSON bodies. Only Node 2 deviates. A ≈2.6 KB JSON URL-encoded into a query string is fragile (proxy/CDN URL length limits) and breaks the doc's Python example at line 190.

### Proposed fix (FastAPI)

Locate the handler — looks like something like:
```python
@app.post("/verification/process")
def process_claim_verification(raw_text: str):
    ...
```

Change to a Pydantic body model that mirrors `ClaimIntakeOutput`:
```python
from pydantic import BaseModel

class PolicyVerificationInput(BaseModel):
    claim_reference_draft: str
    policy_no: str
    claimant_name: str
    id_document_type: IdDocumentType
    id_document_no: str
    date_of_birth: date
    claimant_relationship: ClaimantRelationship
    claim_type: ClaimType
    incident_date: date
    claim_date: date
    claim_amount_requested: float
    provider_name: str
    provider_registration: str
    intake_accepted: bool
    rejection_reason: Optional[str] = None
    missing_documents: List[str] = []
    intake_timestamp: datetime
    document_summary: DocumentSummary

@app.post("/verification/process", response_model=PolicyVerificationOutput)
def process_claim_verification(body: PolicyVerificationInput):
    ...
```

### Verification test
```bash
curl -sS -X POST $BASE/verification/process \
  -H 'Content-Type: application/json' \
  -d @B001_stage_1_output.json | jq '.policy_verified'
# expect: true
```

---

## Fix 2 — 🔴 `/intake/process` returns `DOCUMENT_PARSE_FAILURE` on canonical inputs

### Symptom
Every probe — empty `scanned_files`, canonical `["B001/medical_bill.pdf", ...]`, or fake paths — produces the same 577-byte response:
```json
{"intake_accepted": false, "rejection_reason": "DOCUMENT_PARSE_FAILURE",
 "missing_documents": [], "document_summary": null}
```

### Why it's a blocker
No client can produce an `intake_accepted: true` claim. The entire cascade is dead from stage 1. Downstream endpoints are only testable by skipping Node 1 entirely.

### Likely root causes (need owner to investigate)
1. **Missing PDFs in container.** Dockerfile may not COPY `data/health-insurance-claim/synthetic data/documents/B0xx/` into `/app/data/...`. `docker exec <container> ls /app/data/health-insurance-claim/synthetic\ data/documents/` would confirm.
2. **PDF parser crashed silently.** If the parser uses Vultr serverless inference and the API key is missing/expired, it may catch the exception and return `DOCUMENT_PARSE_FAILURE` without surfacing the cause.
3. **`scanned_files` path interpretation drift.** Server might expect absolute paths (`/app/data/.../B001/medical_bill.pdf`) while canonical fixture uses relative (`B001/medical_bill.pdf`). Probes show no difference, but worth checking handler code.

### Proposed fix
Add a debug branch to the parser:
```python
except Exception as e:
    logger.error(f"document parse failure: {e}", exc_info=True)
    return ClaimIntakeOutput(
        ...,
        intake_accepted=False,
        rejection_reason="DOCUMENT_PARSE_FAILURE",
        _debug_error=str(e)  # surface to caller in dev only
    )
```

Then re-deploy and re-probe with B001 — the `_debug_error` field will reveal whether it's missing files, missing API key, or a parser bug.

### Verification test
```bash
# canonical B001 input
curl -sS -X POST $BASE/intake/process -H 'Content-Type: application/json' \
  -d @B001_stage_1_input.json | jq '.intake_accepted'
# expect: true
```

---

## Fix 3 — 🟠 `/adjudication/process` returns wrong math

### Symptom (B001 hospitalisation, GOLD plan, adjudication_base 16 000)

| Field | Server | Canonical (from `_arithmetic_verify`) | Δ |
|---|---|---|---|
| `deductible_applied_this_claim` | 0.00 | 1 000.00 | **−1 000** |
| `co_pay_amount` | 800.00 | 750.00 | +50 |
| `co_insurance_amount` | 1 520.00 | 1 425.00 | +95 |
| `net_payable` | **13 680.00** | **12 825.00** | **+855** |
| `claimant_liability` | 4 820.00 | 5 675.00 | −855 |

Server applies co-pay/co-insurance on the **full adjudication_base**. Canonical applies them on the **post-deductible remainder**. Both conserve `net + liability = 18 500` so the disbursement leg passes — but they're answering different math problems.

### Why it matters
- The doc's table for B001 says "Net Payable: SGD 0.00" — a **third** number, disagreeing with both server (13 680) and canonical (12 825).
- The hackathon demo will show inconsistent numbers across {doc table, server response, synthetic fixture}.

### Proposed fix
Owner picks one calculation order and propagates:

**Option A — canonical order (deductible first, then co-pay, then co-insurance on remainder):**
```python
deductible_applied = min(annual_deductible_remaining, adjudication_base)
amount_after_deductible = adjudication_base - deductible_applied
co_pay = round(amount_after_deductible * copay_rate, 2)
amount_after_copay = amount_after_deductible - co_pay
co_insurance = min(round(amount_after_copay * coins_rate, 2), coins_cap)
net_payable = round(amount_after_copay - co_insurance, 2)
```

**Option B — server's current order (co-pay/coins on full base, deductible separately):** keep current logic, but then fix the doc + synthetic fixtures to match.

Option A is closer to standard insurance arithmetic — recommend it.

### Verification test
B001 should produce:
- `deductible_applied_this_claim: 1000.0`
- `co_pay_amount: 750.0`
- `co_insurance_amount: 1425.0`
- `net_payable: 12825.0`
- `claimant_liability: 5675.0`

(Plus update `API_USAGE.md` table row from "Net Payable: SGD 0.00" → "SGD 12 825.00".)

---

## Fix 4 — 🟡 Synthetic `_output` fixtures contain placeholder strings

### Symptom
`gem-squared/tpmn-contracts@june/health-insurance-claim/synthetic data/claim_B001_full_pipeline.json` stage 2/3/4/5 outputs contain:
```json
"document_summary": "<<passthrough — identical to stage_1_intake._output.document_summary>>"
```

This is a literal string. POSTing it to `/eligibility/process` or `/medical/process` produces:
```json
{"detail":[{"type":"model_attributes_type","loc":["body","document_summary"],
  "msg":"Input should be a valid dictionary or object..."}]}
```

### Why it matters
Anyone reading the fixture as "machine-runnable test data" hits a wall. The placeholder is human-readable docs masquerading as a test fixture.

### Proposed fix
Run a script over `claim_B00N_full_pipeline.json` files in the `june` branch:
```python
for case in glob("claim_B*_full_pipeline.json"):
    data = json.load(open(case))
    ds = data["stage_1_intake"]["_output"]["document_summary"]
    for stage in ["stage_2_policy_verification", "stage_3_eligibility_check",
                  "stage_4_medical_review", "stage_5_adjudication", "stage_6_disbursement"]:
        if data[stage].get("_output", {}).get("document_summary", "").startswith("<<passthrough"):
            data[stage]["_output"]["document_summary"] = ds
    json.dump(data, open(case, "w"), indent=2)
```

Commit to the `june` branch. AI Agent Olympics + any external consumer of these fixtures can then feed them to `/eligibility/process` etc. without manual hydration.

### Verification test
```bash
jq '.. | objects | .document_summary? // empty | select(type=="string" and startswith("<<"))' \
   claim_B001_full_pipeline.json
# expect: no output (all are objects)
```

---

## Fix 5 — 🟡 `API_USAGE.md` request example contradicts the live schema

### Symptom
Doc shows on line 74–98:
```json
{
  "policy_holder": "Tan Wei Ming",
  "claimant_contact_email": "tanweiming@email.com",
  "claimant_contact_phone": "+6591234567",
  "document_paths": {
    "medical_bill": "/app/data/.../medical_bill.pdf",
    ...
  }
}
```

Live `ClaimIntakeInput` schema:
- Required: `scanned_files: array<string>` — doc says `document_paths: object`
- Not in schema: `policy_holder`, `claimant_contact_email`, `claimant_contact_phone`
- FastAPI ignores unknown fields by default, so the request body parses; but the doc presents these as canonical, which is misleading.

The doc's Python orchestrator (lines 152–223) inherits the same shape bug — it will fail at Node 2 (Fix 1 issue) even after Node 1 is fixed.

### Proposed fix
- Rename `document_paths` (object) → `scanned_files` (array of strings).
- Drop the three contact/policy_holder fields (or document them as "ignored by server").
- After Fix 1 lands: re-write the Python orchestrator to use `json=` for all 6 nodes.
- Reconcile B003 plan code with the TechEx upstream (SILVER vs GOLD — see prior Kritik report).
- Reconcile B001 "Net Payable: SGD 0.00" row with whatever value Fix 3 settles on.

### Verification test
Copy-paste the doc's Python script and run it end-to-end against the live service. It should reach `Node 6: Claim Fully Disbursed!` with no errors. Currently it fails at Node 2.

---

## Suggested order

```
Day 1:  Fix 1 (verification body)          — 1 line, unblocks every client
Day 1:  Fix 4 (hydrate synthetic fixtures) — 10-line script
Day 2:  Fix 2 (intake parse failure)       — needs container introspection
Day 2:  Fix 3 (adjudication math)          — pick order, update tests
Day 3:  Fix 5 (doc + Python example)       — straightforward after 1 & 3
```

---

## What I did NOT verify

- B002–B005 end-to-end (intake blocked all of them at stage 1).
- Whether `/intake/process` works with `document_summary` injected directly (server may not accept that field on input).
- Whether `/disbursement/process` validates bank account numbers per the doc's note about DBS/POSB 10-digit format.
- Behavior under load (single-request probes only).
- Whether `/openapi.json` matches the actual handler signatures for all 6 endpoints, or only Nodes 2 + intake schemas were checked.

Any of these are worth a follow-up Kritik pass once Fixes 1–3 land.

---

*Kritik seat, AI Agent Olympics project, 2026-05-19.*
*Evidence: `api-verification-report.md` (full probe transcript) + `endpoint-verification-report.md` (contracts repo coverage) — same folder.*
