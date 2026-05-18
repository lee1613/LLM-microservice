# 🚀 Health Insurance Claims Pipeline — API Usage Guide (v2)

This guide describes how to interact with the 6-node automated health insurance claims processing pipeline and verify execution against the pre-seeded **Synthetic Data Ecosystem** and **Reference Databases**.

---

### 🌐 Base URLs
- **Production (Vultr + nip.io):** `http://gem-squared-microservice.139.180.136.212.nip.io`
- **Production (Direct IP):** `http://139.180.136.212`
- **Local Dev:** `http://localhost:8000`
- **Interactive Swagger Documentation:** `{base_url}/docs`

---

## 🔗 The 6-Stage Pipeline Cascade

The pipeline is designed so that the **entire output of one node is passed directly as the input to the next**. Each node adds new validated fields or calculations, creating an audit-safe, deterministic chain.

```
[Node 1: Intake] ──> [Node 2: Verification] ──> [Node 3: Eligibility]
                                                               │
[Node 6: Disbursement] <── [Node 5: Adjudication] <── [Node 4: Medical Review]
```

---

## 🗄️ Database & Synthetic Data Architecture

The pipeline evaluates every claim against three distinct SQLite databases shipped pre-populated inside the container under `/app/data/`:

```
data/
├── health-insurance-claim/synthetic data/
│   ├── database.db        <-- Main policy, plan details, and deductible ledger DB
│   └── registry.db        <-- Simulated external accredited providers & physicians
└── cpt_reference.db       <-- Official CMS PFS Relative Value descriptors for CPT validation
```

### 1. Main Policy Database (`database.db`)
- `policies`: Active policy terms (product code, start/end dates, premium payment status).
- `plan_documents`: Contains the raw natural-language benefits matrix (e.g., deductible caps, co-insurance percentages) for Gold, Silver, and Bronze plans.
- `deductible_ledger`: Tracks cumulative deductible spend per policy holder per benefit year. Writes are updated atomically on final disbursement.
- `claim_utilisation`: Tracks all previous approved claims to enforce duplicate checks and annual benefit limits.

### 2. External Registries (`registry.db`)
- `accredited_providers`: Simulated MOH-accredited panel institutions (e.g., Singapore General Hospital, KK Women's and Children's Hospital).
- `physician_registry`: Lists registered doctors and their unique Medical Council Registration (`MCR`) numbers used to verify billing authority.

### 3. Procedure Reference Database (`cpt_reference.db`)
- `cpt_reference`: Official 2024 CMS Physician Fee Schedule relative value codes and descriptors (e.g., `44950` for Appendectomy). Used by Node 4 to match medical necessity.

---

## 🧪 Synthetic Test Cases & Validation Guide (B001–B005)

Use the following pre-packaged synthetic test suite to verify the pipeline's operational logic:

| Case ID | Claimant Name | Policy & Product | Case Description & Path | Expected Pipeline Outcome |
| :--- | :--- | :--- | :--- | :--- |
| **`B001`** | Tan Wei Ming | `HIC-2024-00123`<br>**GOLD** | **Panel Hospitalisation (SGH)**<br>Uses provider-direct billing. Deductible is at $0 utilized, Gold plan has $1,000 annual deductible. | **Passes to N5 Adjudication**<br>Net Payable: **SGD 0.00**<br>(Entire RPS Benchmark of $370.00 absorbed by $1,000 deductible). |
| **`B002`** | Lim Kai Xuan | `HIC-2023-00456`<br>**SILVER** | **Non-Panel Outpatient**<br>Billed by a clinic. The attending physician's licence is expired or invalid. | **Fails at Node 4 (Medical Review)**<br>Error Code: `INVALID_PHYSICIAN_LICENCE` |
| **`B003`** | Priya Subramaniam | `HIC-2025-00789`<br>**SILVER** | **Panel Maternity (KKH)**<br>Policy started 2025-03-10; incident occurred on 2025-04-10 (waiting period violated). | **Fails at Node 3 (Eligibility)**<br>Error Code: `WAITING_PERIOD_NOT_MET` |
| **`B004`** | Ahmad Zulkifli | `HIC-2022-00321`<br>**BRONZE** | **Non-Panel Surgical**<br>Claim for $11,800 at a non-panel clinic. Deductible is $0, Bronze deductible is $3,500. | **Successfully Disbursed**<br>Net Payable: **SGD 1,120.00**<br>(Base benchmark of $8,750 reduced to 60% non-panel, minus $3,500 deductible, co-pay, co-insurance). |
| **`B005`** | Chen Mei Ling | `HIC-2024-00099`<br>**GOLD** | **Emergency Outpatient**<br>Duplicate claim submission for an identical incident date and policy number. | **Fails at Node 2 (Verification)**<br>Error Code: `DUPLICATE_CLAIM` |

---

## 🛠️ Node Reference & Endpoint Specifications

### 1️⃣ Node 1: Claim Intake (`POST /intake/process`)
Validates document presence and NRIC format. Assigns a draft reference (`DRAFT-YYYYMMDD-XXXXX`).

#### Request Example
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
  "claim_amount_requested": 18500.0,
  "supporting_documents": ["medical_bill", "discharge_summary", "pre_auth_approval"],
  "claimant_contact_email": "tanweiming@email.com",
  "claimant_contact_phone": "+6591234567",
  "document_paths": {
    "medical_bill": "/app/data/health-insurance-claim/synthetic data/documents/B001/medical_bill.pdf",
    "discharge_summary": "/app/data/health-insurance-claim/synthetic data/documents/B001/discharge_summary.pdf",
    "pre_auth_approval": "/app/data/health-insurance-claim/synthetic data/documents/B001/pre_auth_approval.pdf"
  }
}
```

---

### 2️⃣ Node 2: Policy Verification (`POST /verification/process`)
Checks databases for active policies, premium status, claimant validity, and duplicate submissions.
- **Input:** Pass Node 1 response JSON directly.
- **Key Output fields added:** `policy_product_code`, `policy_verified: true`, `dependent_verified`.

---

### 3️⃣ Node 3: Eligibility Check (`POST /eligibility/process`)
Validates waiting periods and limits.
- **Input:** Pass Node 2 response JSON directly.
- **Key Output fields added:** `eligible: true`, `annual_limit_remaining`, `claimable_ceiling`.

---

### 4️⃣ Node 4: Medical Review (`POST /medical/process`)
Uses Vultr Serverless Inference agentic tool-calling to extract clinical parameters from the PDF paths (`document_paths`) and validates CPT/ICD-10 clinical necessity.
- **Input:** Pass Node 3 response JSON directly.
- **Key Output fields added:** `medical_review_passed: true`, `rps_benchmark`, `non_panel_flag`, `medical_flags`.

---

### 5️⃣ Node 5: Financial Adjudication (`POST /adjudication/process`)
Applies cost-sharing calculations and updates database deductible profiles.
- **Input:** Pass Node 4 response JSON directly.
- **Key Output fields added:** `adjudication_status` ("approved"), `net_payable`, `claimant_liability`, `adjudication_notes`.

---

### 6️⃣ Node 6: Disbursement (`POST /disbursement/process`)
Finalizes bank account validations and issues permanent `CLM-YYYY-NNNNNNN` tracking numbers.
- **Input:** Pass Node 5 response JSON, **plus** a `payment_details` block:
```json
{
  "payment_details": {
    "payment_mode": "direct_credit", 
    "payee_name": "Ahmad Zulkifli bin Hassan",
    "bank_name": "DBS",
    "bank_account_no": "0012345678",
    "bank_branch_code": "007"
  }
}
```
*(Note: Use bank-specific account validators e.g., DBS/POSB must be exactly 10 digits).*

---

## 🐍 Python Orchestrator Example (Verifying against B004)

Use this complete pipeline runner script to verify execution against the **BRONZE non-panel surgical path** (`B004`):

```python
import requests
import json

BASE_URL = "http://gem-squared-microservice.139.180.136.212.nip.io"

# Payload referencing pre-loaded Docker PDFs for Ahmad Zulkifli bin Hassan (Case B004)
claim_payload = {
    "policy_no": "HIC-2022-00321",
    "policy_holder": "Ahmad Zulkifli bin Hassan",
    "claimant_name": "Ahmad Zulkifli bin Hassan",
    "claimant_relationship": "self",
    "id_document_type": "nric",
    "id_document_no": "T0112345A",
    "date_of_birth": "2001-05-14",
    "claim_date": "2025-06-01",
    "incident_date": "2025-05-25",
    "claim_type": "surgical",
    "provider_name": "Novena Surgical and Orthopaedic Centre",
    "provider_registration": "PRV-HOSP-09921",
    "claim_amount_requested": 11800.0,
    "supporting_documents": ["medical_bill", "discharge_summary"],
    "claimant_contact_email": "ahmad@email.com",
    "claimant_contact_phone": "+6598765432",
    "document_paths": {
        "medical_bill": "/app/data/health-insurance-claim/synthetic data/documents/B004/medical_bill.pdf",
        "discharge_summary": "/app/data/health-insurance-claim/synthetic data/documents/B004/discharge_summary.pdf"
    }
}

headers = {"Content-Type": "application/json"}

# 1. Intake
n1 = requests.post(f"{BASE_URL}/intake/process", headers=headers, json=claim_payload).json()
assert n1.get("intake_accepted"), f"Intake rejected: {n1.get('rejection_reason')}"
print(f"✓ Node 1: Intake Accepted | Draft ID: {n1.get('claim_reference_draft')}")

# 2. Verification
n2 = requests.post(f"{BASE_URL}/verification/process", headers=headers, json=n1).json()
assert n2.get("policy_verified"), f"Verification failed: {n2.get('verification_failure')}"
print(f"✓ Node 2: Policy Verified ({n2.get('policy_product_code')})")

# 3. Eligibility
n3 = requests.post(f"{BASE_URL}/eligibility/process", headers=headers, json=n2).json()
assert n3.get("eligible"), f"Eligibility check failed: {n3.get('eligibility_failure_reason')}"
print(f"✓ Node 3: Eligibility Verified | Remaining Limit: SGD {n3.get('annual_limit_remaining')}")

# 4. Medical Review
n4 = requests.post(f"{BASE_URL}/medical/process", headers=headers, json=n3).json()
assert n4.get("medical_review_passed"), f"Medical Review failed: {n4.get('review_failure_reason')}"
print(f"✓ Node 4: Medical Review Passed | RPS Benchmark: SGD {n4.get('rps_benchmark')}")

# 5. Adjudication
n5 = requests.post(f"{BASE_URL}/adjudication/process", headers=headers, json=n4).json()
assert n5.get("adjudication_status") == "approved", "Adjudication rejected"
print(f"✓ Node 5: Adjudication Approved | NET: SGD {n5.get('net_payable')} | Liability: SGD {n5.get('claimant_liability')}")

# 6. Disbursement
disbursement_input = {**n5}
disbursement_input["payment_details"] = {
    "payment_mode": "direct_credit",
    "payee_name": "Ahmad Zulkifli bin Hassan",
    "bank_name": "DBS",
    "bank_account_no": "0012345678",
    "bank_branch_code": "007"
}

n6 = requests.post(f"{BASE_URL}/disbursement/process", headers=headers, json=disbursement_input).json()
print(f"✓ Node 6: Claim Fully Disbursed!")
print(f"  └─ Permanent Reference ID: {n6.get('claim_reference_no')}")
print(f"  └─ Payment Schedule: {n6.get('remarks')}")
```
