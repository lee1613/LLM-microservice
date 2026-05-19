# Deployed API Usage Guidelines

The Health Insurance Claims pipeline is deployed at:  
👉 **`http://139.180.136.212`**

---

## 🛠️ Endpoints Overview

| Node | Route | HTTP Method | Input Description |
|---|---|---|---|
| **Reset DB** | `/dev/reset` | `POST` | Resets ledger limits for clean synthetic testing. |
| **Node 1: Intake** | `/intake/process` | `POST` | Expects raw claim metadata (`_input`). |
| **Node 2: Verification** | `/verification/process` | `POST` | Expects output from Node 1. |
| **Node 3: Eligibility** | `/eligibility/process` | `POST` | Expects output from Node 2. |
| **Node 4: Medical Review** | `/medical/process` | `POST` | Expects output from Node 3. |
| **Node 5: Adjudication** | `/adjudication/process` | `POST` | Expects output from Node 4. |
| **Node 6: Disbursement** | `/disbursement/process` | `POST` | Expects output from Node 5 + `payment_details`. |

---

## 🚀 Quick Start: Testing the Pipeline

Use python/curl to trigger the pipeline sequentially with the synthetic dataset provided in `synthetic data/`.

### 1. Reset the Ledger (Recommended before testing)
```bash
curl -X POST http://139.180.136.212/dev/reset
```

### 2. Run Intake (Node 1)
Pass the `_input` block from `claim_B001_full_pipeline.json`:
```bash
curl -X POST http://139.180.136.212/intake/process \
     -H "Content-Type: application/json" \
     -d '{
       "policy_no": "HIC-2024-00123",
       "claimant_name": "Tan Wei Ming",
       "claimant_relationship": "self",
       "id_document_type": "nric",
       "id_document_no": "S7801234A",
       "date_of_birth": "1978-03-22",
       "incident_date": "2025-04-10",
       "claim_date": "2025-04-14",
       "claim_type": "hospitalisation",
       "claim_amount_requested": 18500.0,
       "provider_name": "Singapore General Hospital",
       "provider_registration": "MOH-HOSP-00142",
       "supporting_documents": ["medical_bill", "discharge_summary", "pre_auth_approval"],
       "scanned_files": ["B001/medical_bill.pdf", "B001/discharge_summary.pdf", "B001/pre_auth_approval.pdf"]
     }'
```
Pass the resulting JSON directly into the `/verification/process` endpoint, and continue down the pipeline table sequentially.
