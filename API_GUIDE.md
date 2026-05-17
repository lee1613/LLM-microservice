# Health Insurance Claim Pipeline — API Usage Guide

**Base URL (Production):** `http://139.180.136.212`  
**Base URL (Local dev):** `http://localhost:8000`  
**Interactive Swagger UI:** `{base_url}/docs`  
**OpenAPI JSON schema:** `{base_url}/openapi.json`

---

## Overview

The pipeline is a six-node chain where the **output of each node becomes the input of the next**. A claim must pass every node in sequence. Nodes 1–4 are currently deployed.

```
Node 1: Claim Intake        → /intake/process
Node 2: Policy Verification → /verification/process
Node 3: Eligibility Check   → /eligibility/process
Node 4: Medical Review      → /medical/process 
```

> [!IMPORTANT]
> Each node accepts the full JSON body from the previous node's response. You only need to add fields that the previous node did not already return (e.g., `provider_registration` before Node 4).

---

## Authentication

No authentication is required at the API gateway level for the current deployment. API keys for third-party services (Vultr Inference, Gemini) are stored securely as Kubernetes secrets and injected at the container level — they are never exposed in responses.

---

## Node 1 — Claim Intake

**Endpoint:** `POST /intake/process`  
**Purpose:** Validates the raw claim submission, assigns a draft reference number, and identifies any missing supporting documents.

### Request Body

```json
{
  "policy_no": "HIC-2024-00123",
  "policy_holder": "Tan Wei Ming",
  "claimant_name": "Tan Wei Ming",
  "claimant_relationship": "self",
  "id_document_type": "nric",
  "id_document_no": "S8812345A",
  "date_of_birth": "1988-03-21",
  "claim_date": "2025-04-14",
  "incident_date": "2025-04-10",
  "claim_type": "hospitalisation",
  "provider_name": "Singapore General Hospital",
  "provider_registration": "MOH-HOSP-00142",
  "claim_amount_requested": 18500.00,
  "supporting_documents": ["medical_bill", "discharge_summary", "pre_auth_approval"],
  "claimant_contact_email": "tanweiming@email.com",
  "claimant_contact_phone": "+6591234567",
  "document_paths": {
    "medical_bill": "/path/to/medical_bill.pdf",
    "discharge_summary": "/path/to/discharge_summary.pdf",
    "pre_auth_approval": "/path/to/pre_auth_approval.pdf"
  }
}
```

### Enum Values

| Field | Allowed Values |
|-------|---------------|
| `claimant_relationship` | `self`, `spouse`, `child`, `parent`, `sibling`, `other_dependent` |
| `id_document_type` | `nric`, `passport`, `fin`, `birth_certificate` |
| `claim_type` | `hospitalisation`, `outpatient`, `surgical`, `dental`, `vision`, `maternity`, `mental_health`, `emergency` |
| `supporting_documents` | `medical_bill`, `discharge_summary`, `referral_letter`, `prescription`, `lab_report`, `imaging_report`, `specialist_memo`, `pre_auth_approval` |

### Validation Rules

- `policy_no` must match `^HIC-\d{4}-\d{5}$`
- `id_document_no` format validated per `id_document_type` (e.g. NRIC: `^[STFG]\d{7}[A-Z]$`)
- `incident_date` must be ≤ `claim_date`
- `claim_amount_requested` must be > 0
- Required documents are enforced per `claim_type` (e.g. `hospitalisation` requires `medical_bill` + `discharge_summary`)

### Response (200 OK)

```json
{
  "claim_reference_draft": "DRAFT-20250414-01001",
  "policy_no": "HIC-2024-00123",
  "claimant_name": "Tan Wei Ming",
  "id_document_type": "nric",
  "id_document_no": "S8812345A",
  "date_of_birth": "1988-03-21",
  "claimant_relationship": "self",
  "claim_type": "hospitalisation",
  "incident_date": "2025-04-10",
  "claim_date": "2025-04-14",
  "claim_amount_requested": 18500.00,
  "intake_accepted": true,
  "rejection_reason": null,
  "missing_documents": [],
  "intake_timestamp": "2025-04-14T09:00:00+08:00",
  "supporting_documents": ["medical_bill", "discharge_summary", "pre_auth_approval"],
  "document_paths": {
    "medical_bill": "/path/to/medical_bill.pdf",
    "discharge_summary": "/path/to/discharge_summary.pdf",
    "pre_auth_approval": "/path/to/pre_auth_approval.pdf"
  }
}
```

### Possible Rejection Reasons (`intake_accepted: false`)

| Code | Meaning |
|------|---------|
| `INVALID_POLICY_FORMAT` | `policy_no` does not match the required regex |
| `INVALID_ID_FORMAT` | ID document number fails format check |
| `FUTURE_INCIDENT_DATE` | `incident_date` is after `claim_date` |
| `MISSING_REQUIRED_DOCUMENTS` | Required documents for the `claim_type` were not submitted |
| `INVALID_CLAIM_AMOUNT` | `claim_amount_requested` is zero or negative |

---

## Node 2 — Policy Verification

**Endpoint:** `POST /verification/process`  
**Purpose:** Verifies the policy is active, premium is paid, and the claimant is a covered member.

### Request Body

Pass the full output from Node 1 directly. The key fields used internally are:

```json
{
  "claim_reference_draft": "DRAFT-20250414-01001",
  "policy_no": "HIC-2024-00123",
  "claimant_name": "Tan Wei Ming",
  "id_document_type": "nric",
  "id_document_no": "S8812345A",
  "date_of_birth": "1988-03-21",
  "claimant_relationship": "self",
  "claim_type": "hospitalisation",
  "incident_date": "2025-04-10",
  "claim_amount_requested": 18500.00,
  "supporting_documents": ["medical_bill", "discharge_summary", "pre_auth_approval"],
  "document_paths": { "...": "..." }
}
```

> [!NOTE]
> Fields `intake_accepted`, `intake_timestamp`, `claim_date`, `missing_documents` from Node 1 output are safely ignored.

### Response (200 OK)

```json
{
  "claim_reference_draft": "DRAFT-20250414-01001",
  "policy_no": "HIC-2024-00123",
  "claimant_name": "Tan Wei Ming",
  "claim_type": "hospitalisation",
  "incident_date": "2025-04-10",
  "claim_amount_requested": 18500.00,
  "policy_product_code": "COMP-HEALTH-GOLD",
  "premium_payment_mode": "annual",
  "policy_start_date": "2024-01-15",
  "policy_expiry_date": "2026-01-14",
  "dependent_verified": true,
  "policy_verified": true,
  "verification_failure": null,
  "verification_timestamp": "2025-04-14T09:23:45+08:00",
  "supporting_documents": ["medical_bill", "discharge_summary", "pre_auth_approval"],
  "document_paths": { "...": "..." }
}
```

### Possible Verification Failures (`policy_verified: false`)

| Code | Meaning |
|------|---------|
| `POLICY_NOT_FOUND` | No policy exists for the given `policy_no` |
| `POLICY_EXPIRED` | Policy expiry date is before `incident_date` |
| `PREMIUM_LAPSED` | Premium payment is overdue |
| `CLAIMANT_NOT_COVERED` | Claimant ID/DOB does not match any covered member |
| `DEPENDENT_NOT_ACTIVE` | Dependent's coverage has ended |
| `DUPLICATE_CLAIM` | A claim for the same policy + incident date already exists |

---

## Node 3 — Eligibility Check

**Endpoint:** `POST /eligibility/process`  
**Purpose:** Checks that the claim type is covered under the plan, waiting periods are satisfied, and annual/per-claim limits are not exceeded.

### Request Body

Pass the full output from Node 2 directly:

```json
{
  "claim_reference_draft": "DRAFT-20250414-01001",
  "policy_no": "HIC-2024-00123",
  "claimant_name": "Tan Wei Ming",
  "claim_type": "hospitalisation",
  "incident_date": "2025-04-10",
  "claim_amount_requested": 18500.00,
  "policy_product_code": "COMP-HEALTH-GOLD",
  "dependent_verified": true,
  "supporting_documents": ["medical_bill", "discharge_summary", "pre_auth_approval"],
  "document_paths": { "...": "..." }
}
```

### Response (200 OK)

```json
{
  "claim_reference_draft": "DRAFT-20250414-01001",
  "policy_no": "HIC-2024-00123",
  "claimant_name": "Tan Wei Ming",
  "claim_type": "hospitalisation",
  "incident_date": "2025-04-10",
  "claim_amount_requested": 18500.00,
  "eligible": true,
  "eligibility_failure_reason": null,
  "claim_type_covered": true,
  "waiting_period_satisfied": true,
  "waiting_period_days": 30,
  "annual_limit": 100000.00,
  "annual_utilised": 420.00,
  "annual_limit_remaining": 99580.00,
  "per_claim_limit": 50000.00,
  "claimable_ceiling": 18500.00,
  "eligibility_timestamp": "2025-04-14T09:30:00+08:00",
  "supporting_documents": ["medical_bill", "discharge_summary", "pre_auth_approval"],
  "document_paths": { "...": "..." }
}
```

### Possible Eligibility Failures (`eligible: false`)

| Code | Meaning |
|------|---------|
| `CLAIM_TYPE_NOT_COVERED` | The plan does not cover this type of claim |
| `WAITING_PERIOD_NOT_MET` | Claim occurred within the waiting period since policy start |
| `ANNUAL_LIMIT_EXCEEDED` | Prior claims this year have exhausted the annual limit |
| `PER_CLAIM_LIMIT_EXCEEDED` | Requested amount exceeds the per-claim ceiling |

---

## Node 4 — Medical Review

**Endpoint:** `POST /medical/process`  
**Purpose:** Uses the **Vultr Serverless Inference LLM** (`vultr/got-qwen-120b-normalize`) to extract structured clinical data from the submitted PDF documents, then runs 10 deterministic SQL-backed validation checks.

### Request Body

Pass the full output from Node 3, plus `provider_registration` (if not already present):

```json
{
  "claim_reference_draft": "DRAFT-20250414-01001",
  "policy_no": "HIC-2024-00123",
  "claimant_name": "Tan Wei Ming",
  "claim_type": "hospitalisation",
  "incident_date": "2025-04-10",
  "claim_amount_requested": 18500.00,
  "claimable_ceiling": 18500.00,
  "provider_name": "Singapore General Hospital",
  "provider_registration": "MOH-HOSP-00142",
  "supporting_documents": ["medical_bill", "discharge_summary", "pre_auth_approval"],
  "document_paths": {
    "medical_bill": "/app/data/health-insurance-claim/synthetic data/documents/A001/medical_bill.pdf",
    "discharge_summary": "/app/data/health-insurance-claim/synthetic data/documents/A001/discharge_summary.pdf",
    "pre_auth_approval": "/app/data/health-insurance-claim/synthetic data/documents/A001/pre_auth_approval.pdf"
  }
}
```

> [!IMPORTANT]
> The `document_paths` values must be **absolute paths accessible on the server**. When running in the Docker/Kubernetes deployment, documents must be pre-loaded into the container image (as they currently are at `/app/data/...`). For production use with external uploads, documents would be stored in object storage and paths updated accordingly.

### How the 10-step validation works (internally)

| Step | Check |
|------|-------|
| 1 | Provider accreditation — panel status and expiry |
| 2 | ICD-10 code validity and active status |
| 3 | CPT code validity, format, and ICD-10 plausibility |
| 4 | Policy exclusions (cosmetic, self-harm, substance abuse, experimental) |
| 5 | Pre-authorisation existence, status, and policy match |
| 6 | Admission/discharge date logic and length-of-stay computation |
| 7 | Physician licence format (`MCR-#####X`) and registry status |
| 8 | Medical necessity confirmation per ICD-10/CPT pair |
| 9 | Reference Price Schedule benchmark and bill variance (>50% flags) |
| 10 | Final aggregation: all checks must pass |

### Response (200 OK)

```json
{
  "claim_reference_draft": "DRAFT-20250414-01001",
  "policy_no": "HIC-2024-00123",
  "claimant_name": "Tan Wei Ming",
  "claim_type": "hospitalisation",
  "incident_date": "2025-04-10",
  "claim_amount_requested": 18500.00,
  "claimable_ceiling": 18500.00,
  "medical_review_passed": true,
  "exclusions_triggered": [],
  "review_failure_reason": null,
  "non_panel_flag": false,
  "pre_auth_verified": true,
  "length_of_stay": 4,
  "rps_benchmark": 1480.00,
  "bill_variance_pct": -12.5,
  "medical_necessity_confirmed": true,
  "medical_flags": [],
  "review_timestamp": "2025-04-14T09:45:00Z",
  "supporting_documents": ["medical_bill", "discharge_summary", "pre_auth_approval"],
  "document_paths": { "...": "..." }
}
```

### Possible Review Failures (`medical_review_passed: false`)

| Code | Meaning |
|------|---------|
| `EXTRACTION_FAILED` | LLM could not parse clinical data from documents |
| `INVALID_ICD10` | Primary diagnosis code not found in ICD-10 reference table |
| `INVALID_CPT_CODE` | One or more procedure codes not in approved CPT table |
| `CPT_ICD10_MISMATCH` | CPT/ICD-10 pair is clinically implausible |
| `EXCLUSIONS_TRIGGERED` | Claim falls under a policy exclusion (see `exclusions_triggered`) |
| `MISSING_PRE_AUTH` | No pre-authorisation number found (required for surgical/hospitalisation/maternity) |
| `PRE_AUTH_INVALID` | Pre-auth status is not `approved` |
| `PRE_AUTH_POLICY_MISMATCH` | Pre-auth was issued under a different policy number |
| `PRE_AUTH_EXPIRED` | Incident date is after the pre-auth expiry |
| `INVALID_ADMISSION_DISCHARGE_DATES` | Discharge date precedes admission date |
| `INVALID_PHYSICIAN_LICENCE` | Physician not found in registry or licence expired |
| `MEDICAL_NECESSITY_UNCONFIRMED` | ICD-10/CPT pair not confirmed as medically necessary |
| `BILL_EXCEEDS_BENCHMARK` | Claimed amount is >50% above the Reference Price Schedule |

### Possible `medical_flags` (non-blocking)

| Flag | Meaning |
|------|---------|
| `NON_PANEL_PROVIDER` | Provider is not on the insurer's approved panel (claim still processed at non-panel reimbursement rate) |
| `BILL_EXCEEDS_BENCHMARK` | Bill is over the RPS benchmark (also a failure reason when >50%) |

---

## Health & Status

**Endpoint:** `GET /health`

```json
{ "status": "healthy", "service": "llm-microservice" }
```

**Endpoint:** `GET /`

```json
{
  "message": "Welcome to the LLM Microservice",
  "docs": "/docs",
  "health": "/health"
}
```

---

## End-to-End Example (curl)

```bash
BASE="http://139.180.136.212"

# Node 1 — Intake
INTAKE=$(curl -s -X POST "$BASE/intake/process" \
  -H "Content-Type: application/json" \
  -d '{
    "policy_no": "HIC-2024-00123",
    "policy_holder": "Tan Wei Ming",
    "claimant_name": "Tan Wei Ming",
    "claimant_relationship": "self",
    "id_document_type": "nric",
    "id_document_no": "S8812345A",
    "date_of_birth": "1988-03-21",
    "claim_date": "2025-04-14",
    "incident_date": "2025-04-10",
    "claim_type": "hospitalisation",
    "provider_name": "Singapore General Hospital",
    "provider_registration": "MOH-HOSP-00142",
    "claim_amount_requested": 18500.00,
    "supporting_documents": ["medical_bill", "discharge_summary", "pre_auth_approval"],
    "claimant_contact_email": "tanweiming@email.com",
    "claimant_contact_phone": "+6591234567",
    "document_paths": {
      "medical_bill": "/app/data/health-insurance-claim/synthetic data/documents/A001/medical_bill.pdf",
      "discharge_summary": "/app/data/health-insurance-claim/synthetic data/documents/A001/discharge_summary.pdf",
      "pre_auth_approval": "/app/data/health-insurance-claim/synthetic data/documents/A001/pre_auth_approval.pdf"
    }
  }')
echo "Node 1: $INTAKE" | python3 -m json.tool

# Node 2 — Verification (pipe Node 1 output directly)
VERIFY=$(curl -s -X POST "$BASE/verification/process" \
  -H "Content-Type: application/json" \
  -d "$INTAKE")
echo "Node 2: $VERIFY" | python3 -m json.tool

# Node 3 — Eligibility (pipe Node 2 output directly)
ELIGIBILITY=$(curl -s -X POST "$BASE/eligibility/process" \
  -H "Content-Type: application/json" \
  -d "$VERIFY")
echo "Node 3: $ELIGIBILITY" | python3 -m json.tool

# Node 4 — Medical Review (add provider_registration, pipe Node 3 output)
MEDICAL=$(echo "$ELIGIBILITY" | python3 -c "
import json, sys
d = json.load(sys.stdin)
d['provider_registration'] = 'MOH-HOSP-00142'
print(json.dumps(d))
" | curl -s -X POST "$BASE/medical/process" \
  -H "Content-Type: application/json" \
  -d @-)
echo "Node 4: $MEDICAL" | python3 -m json.tool
```

---

## Deployment Reference

| Item | Value |
|------|-------|
| Docker image | `lee1613/llm-microservice:v1` |
| Platforms | `linux/amd64`, `linux/arm64` |
| Kubernetes cluster | Vultr Kubernetes Engine (VKE) |
| Replicas | 2 (one per node for HA) |
| K8s manifest | `k8s/deployment.yaml` |
| Port | `80` (LoadBalancer) → `8000` (container) |

### Redeployment

```bash
# Rebuild and push a new version
docker buildx build --platform linux/amd64,linux/arm64 --push -t lee1613/llm-microservice:v2 .

# Update the image tag in the manifest and apply
kubectl set image deployment/llm-microservice api=lee1613/llm-microservice:v2
kubectl rollout status deployment/llm-microservice
```

### Cluster management commands

```bash
# Check running pods
kubectl get pods -o wide

# View live logs from all pods
kubectl logs -l app=llm-microservice -f

# Scale up/down
kubectl scale deployment llm-microservice --replicas=3

# Get the public LoadBalancer IP
kubectl get service llm-microservice-svc
```
