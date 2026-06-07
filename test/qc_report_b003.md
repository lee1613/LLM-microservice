# QC Report — B003 Full Pipeline
**Scenario:** B003 — Maternity (Normal delivery), COMP-HEALTH-GOLD, Self, REJECTED at Node 3 (Waiting Period Not Met)  
**Expected Outcome:** Pipeline halts at Node 3. Policy inception 2025-03-10. Incident date 2025-05-14. Days elapsed = 65. Maternity waiting period = 270 days. 65 < 270 → WAITING_PERIOD_NOT_MET.  
**API Target:** `http://127.0.0.1:8000`  
**Run Timestamp:** `2026-05-19T17:45:13Z`  



## Executive Summary

| Metric | Count |
|:---|:---:|
| ✅ PASS | 107 |
| ❌ FAIL | 0 |
| ⏭️ SKIP (non-deterministic) | 25 |
| ℹ️ INFO (extra keys) | 0 |

### Per-Node Results
| Result | Node | PASS | FAIL | SKIP |
|:---:|:---|:---:|:---:|:---:|
| ✅ | Node 1: Intake (upload) | 33 | 0 | 8 |
| ✅ | Node 2: Verification | 37 | 0 | 8 |
| ✅ | Node 3: Eligibility | 37 | 0 | 9 |

---

---

# Detailed Stage Logs


## Step 0 — DB Reset

**Endpoint:** `POST /dev/reset`  
**Status:** ✅ OK  
**Response:** `{"status":"reset_complete"}`

---


## Stage 1 — Claim Intake

**Endpoint:** `POST /intake/process` (multipart: JSON metadata + PDF file uploads)  
**Uploaded Files:** ['medical_bill.pdf', 'discharge_summary.pdf', 'pre_auth_approval.pdf']  
**Status:** ✅ Accepted  


### Request Metadata (claim_data form field)
```json
{
  "policy_no": "HIC-2025-00789",
  "claimant_name": "Priya Subramaniam",
  "claimant_relationship": "self",
  "id_document_type": "nric",
  "id_document_no": "S9023456D",
  "date_of_birth": "1990-05-18",
  "incident_date": "2025-05-14",
  "claim_date": "2025-05-20",
  "claim_type": "maternity",
  "claim_amount_requested": 8200.0,
  "provider_name": "KK Women's and Children's Hospital",
  "provider_registration": "MOH-HOSP-00273",
  "supporting_documents": [
    "medical_bill",
    "discharge_summary",
    "pre_auth_approval"
  ]
}
```

### Actual API Response
```json
{
  "claim_reference_draft": "DRAFT-20260520-26596",
  "policy_no": "HIC-2025-00789",
  "claimant_name": "Priya Subramaniam",
  "id_document_type": "nric",
  "id_document_no": "S9023456D",
  "date_of_birth": "1990-05-18",
  "claimant_relationship": "self",
  "claim_type": "maternity",
  "incident_date": "2025-05-14",
  "claim_date": "2025-05-20",
  "claim_amount_requested": 8200.0,
  "provider_name": "KK Women's and Children's Hospital",
  "provider_registration": "MOH-HOSP-00273",
  "intake_accepted": true,
  "rejection_reason": null,
  "missing_documents": [],
  "intake_timestamp": "2026-05-20T01:45:30.782424+08:00",
  "document_summary": {
    "total_billed_amount": 8200.0,
    "itemised_charges": [
      {
        "description": "Delivery Suite Charges (Normal Vaginal)",
        "quantity": 1,
        "unit_price": 3500.0
      },
      {
        "description": "Post-Natal Ward (Class B1 - 3 Nights)",
        "quantity": 3,
        "unit_price": 850.0
      },
      {
        "description": "Paediatrician Assessment (Newborn)",
        "quantity": 1,
        "unit_price": 250.0
      },
      {
        "description": "Medications & Consumables",
        "quantity": 1,
        "unit_price": 1900.0
      }
    ],
    "primary_diagnosis_icd10": "Z37.0",
    "procedure_cpt_codes": [
      "59400",
      "99232"
    ],
    "symptom_onset_date": null,
    "admission_date": "2025-05-14",
    "discharge_date": "2025-05-17",
    "attending_physician": "Dr. Kavitha Rajendran",
    "physician_license_no": "MCR-31457C",
    "pre_authorisation_no": "PA-2025-550001",
    "provider_name_on_bill": "KK Women's and Children's Hospital",
    "extraction_warnings": [
      "symptom_onset_date"
    ],
    "summary_narrative": "Priya Subramaniam delivered a healthy baby on 14 May 2025 after a normal vaginal delivery (ICD‑10 Z37.0). She stayed three nights in the post‑natal ward, received a newborn assessment and medications, with a total billed amount of SGD 8,200.00."
  }
}
```

### Expected Output (from contract)
```json
{
  "claim_reference_draft": "DRAFT-20250520-01103",
  "policy_no": "HIC-2025-00789",
  "claimant_name": "Priya Subramaniam",
  "id_document_type": "nric",
  "id_document_no": "S9023456D",
  "date_of_birth": "1990-05-18",
  "claimant_relationship": "self",
  "claim_type": "maternity",
  "incident_date": "2025-05-14",
  "claim_date": "2025-05-20",
  "claim_amount_requested": 8200.0,
  "provider_name": "KK Women's and Children's Hospital",
  "provider_registration": "MOH-HOSP-00273",
  "intake_accepted": true,
  "rejection_reason": null,
  "missing_documents": [],
  "intake_timestamp": "2025-05-20T11:00:00+08:00",
  "document_summary": {
    "total_billed_amount": 8200.0,
    "itemised_charges": [
      {
        "description": "Delivery suite charges (normal vaginal delivery)",
        "quantity": 1,
        "unit_price": 3500.0
      },
      {
        "description": "Ward charges (Class B1, 3 days)",
        "quantity": 3,
        "unit_price": 850.0
      },
      {
        "description": "Paediatrician assessment (newborn)",
        "quantity": 1,
        "unit_price": 250.0
      },
      {
        "description": "Medications and consumables",
        "quantity": 1,
        "unit_price": 1900.0
      }
    ],
    "primary_diagnosis_icd10": "Z37.0",
    "procedure_cpt_codes": [
      "59400",
      "99232"
    ],
    "symptom_onset_date": null,
    "admission_date": "2025-05-14",
    "discharge_date": "2025-05-17",
    "attending_physician": "Dr. Kavitha Rajendran",
    "physician_license_no": "MCR-31457C",
    "pre_authorisation_no": "PA-2025-550001",
    "provider_name_on_bill": "KK Women's and Children's Hospital",
    "extraction_warnings": [],
    "summary_narrative": "Priya Subramaniam, 35, admitted to KK Women's and Children's Hospital on 14 May 2025 for normal vaginal delivery (ICD-10 Z37.0). No prior symptom onset date recorded. Procedures include delivery suite and routine post-natal inpatient management (CPT 59400, 99232). Discharged 17 May 2025. Total billed SGD 8,200 covering delivery, 3-day ward stay, paediatric assessment, and medications. Pre-authorisation PA-2025-550001 submitted."
  }
}
```

### Field-Level Comparison
| Status | Field | Actual | Expected | Note |
|:---:|:---|:---|:---|:---|
| ⏭️ | stage_1_intake._output.claim_reference_draft | DRAFT-20260520-26596 | DRAFT-20250520-01103 | Non-deterministic field skipped |
| ✅ | stage_1_intake._output.policy_no | HIC-2025-00789 | HIC-2025-00789 |  |
| ✅ | stage_1_intake._output.claimant_name | Priya Subramaniam | Priya Subramaniam |  |
| ✅ | stage_1_intake._output.id_document_type | nric | nric |  |
| ✅ | stage_1_intake._output.id_document_no | S9023456D | S9023456D |  |
| ✅ | stage_1_intake._output.date_of_birth | 1990-05-18 | 1990-05-18 |  |
| ✅ | stage_1_intake._output.claimant_relationship | self | self |  |
| ✅ | stage_1_intake._output.claim_type | maternity | maternity |  |
| ✅ | stage_1_intake._output.incident_date | 2025-05-14 | 2025-05-14 |  |
| ✅ | stage_1_intake._output.claim_date | 2025-05-20 | 2025-05-20 |  |
| ✅ | stage_1_intake._output.claim_amount_requested | 8200.0 | 8200.0 |  |
| ✅ | stage_1_intake._output.provider_name | KK Women's and Children's Hospital | KK Women's and Children's Hospital |  |
| ✅ | stage_1_intake._output.provider_registration | MOH-HOSP-00273 | MOH-HOSP-00273 |  |
| ✅ | stage_1_intake._output.intake_accepted | True | True |  |
| ✅ | stage_1_intake._output.rejection_reason | None | None |  |
| ⏭️ | stage_1_intake._output.intake_timestamp | 2026-05-20T01:45:30.782424+08:00 | 2025-05-20T11:00:00+08:00 | Non-deterministic field skipped |
| ✅ | stage_1_intake._output.document_summary.total_billed_amount | 8200.0 | 8200.0 |  |
| ⏭️ | stage_1_intake._output.document_summary.itemised_charges[0].description | Delivery Suite Charges (Normal Vaginal) | Delivery suite charges (normal vaginal delivery) | Non-deterministic field skipped |
| ✅ | stage_1_intake._output.document_summary.itemised_charges[0].quantity | 1 | 1 |  |
| ✅ | stage_1_intake._output.document_summary.itemised_charges[0].unit_price | 3500.0 | 3500.0 |  |
| ⏭️ | stage_1_intake._output.document_summary.itemised_charges[1].description | Post-Natal Ward (Class B1 - 3 Nights) | Ward charges (Class B1, 3 days) | Non-deterministic field skipped |
| ✅ | stage_1_intake._output.document_summary.itemised_charges[1].quantity | 3 | 3 |  |
| ✅ | stage_1_intake._output.document_summary.itemised_charges[1].unit_price | 850.0 | 850.0 |  |
| ⏭️ | stage_1_intake._output.document_summary.itemised_charges[2].description | Paediatrician Assessment (Newborn) | Paediatrician assessment (newborn) | Non-deterministic field skipped |
| ✅ | stage_1_intake._output.document_summary.itemised_charges[2].quantity | 1 | 1 |  |
| ✅ | stage_1_intake._output.document_summary.itemised_charges[2].unit_price | 250.0 | 250.0 |  |
| ⏭️ | stage_1_intake._output.document_summary.itemised_charges[3].description | Medications & Consumables | Medications and consumables | Non-deterministic field skipped |
| ✅ | stage_1_intake._output.document_summary.itemised_charges[3].quantity | 1 | 1 |  |
| ✅ | stage_1_intake._output.document_summary.itemised_charges[3].unit_price | 1900.0 | 1900.0 |  |
| ✅ | stage_1_intake._output.document_summary.primary_diagnosis_icd10 | Z37.0 | Z37.0 |  |
| ✅ | stage_1_intake._output.document_summary.procedure_cpt_codes[0] | 59400 | 59400 |  |
| ✅ | stage_1_intake._output.document_summary.procedure_cpt_codes[1] | 99232 | 99232 |  |
| ✅ | stage_1_intake._output.document_summary.symptom_onset_date | None | None |  |
| ✅ | stage_1_intake._output.document_summary.admission_date | 2025-05-14 | 2025-05-14 |  |
| ✅ | stage_1_intake._output.document_summary.discharge_date | 2025-05-17 | 2025-05-17 |  |
| ✅ | stage_1_intake._output.document_summary.attending_physician | Dr. Kavitha Rajendran | Dr. Kavitha Rajendran |  |
| ✅ | stage_1_intake._output.document_summary.physician_license_no | MCR-31457C | MCR-31457C |  |
| ✅ | stage_1_intake._output.document_summary.pre_authorisation_no | PA-2025-550001 | PA-2025-550001 |  |
| ✅ | stage_1_intake._output.document_summary.provider_name_on_bill | KK Women's and Children's Hospital | KK Women's and Children's Hospital |  |
| ⏭️ | stage_1_intake._output.document_summary.extraction_warnings | ['symptom_onset_date'] | [] | Non-deterministic field skipped |
| ⏭️ | stage_1_intake._output.document_summary.summary_narrative | Priya Subramaniam delivered a healthy baby on 14 May 2025 after a normal vaginal delivery (ICD‑10 Z37.0). She stayed thr | Priya Subramaniam, 35, admitted to KK Women's and Children's Hospital on 14 May 2025 for normal vaginal delivery (ICD-10 | Non-deterministic field skipped |

---


## Stage 2 — Policy Verification

**Endpoint:** `POST /verification/process`  
**Status:** ✅ Verified  


### Request Payload (= Node 1 Output)
```json
{
  "claim_reference_draft": "DRAFT-20260520-26596",
  "policy_no": "HIC-2025-00789",
  "claimant_name": "Priya Subramaniam",
  "id_document_type": "nric",
  "id_document_no": "S9023456D",
  "date_of_birth": "1990-05-18",
  "claimant_relationship": "self",
  "claim_type": "maternity",
  "incident_date": "2025-05-14",
  "claim_date": "2025-05-20",
  "claim_amount_requested": 8200.0,
  "provider_name": "KK Women's and Children's Hospital",
  "provider_registration": "MOH-HOSP-00273",
  "intake_accepted": true,
  "rejection_reason": null,
  "missing_documents": [],
  "intake_timestamp": "2026-05-20T01:45:30.782424+08:00",
  "document_summary": {
    "total_billed_amount": 8200.0,
    "itemised_charges": [
      {
        "description": "Delivery Suite Charges (Normal Vaginal)",
        "quantity": 1,
        "unit_price": 3500.0
      },
      {
        "description": "Post-Natal Ward (Class B1 - 3 Nights)",
        "quantity": 3,
        "unit_price": 850.0
      },
      {
        "description": "Paediatrician Assessment (Newborn)",
        "quantity": 1,
        "unit_price": 250.0
      },
      {
        "description": "Medications & Consumables",
        "quantity": 1,
        "unit_price": 1900.0
      }
    ],
    "primary_diagnosis_icd10": "Z37.0",
    "procedure_cpt_codes": [
      "59400",
      "99232"
    ],
    "symptom_onset_date": null,
    "admission_date": "2025-05-14",
    "discharge_date": "2025-05-17",
    "attending_physician": "Dr. Kavitha Rajendran",
    "physician_license_no": "MCR-31457C",
    "pre_authorisation_no": "PA-2025-550001",
    "provider_name_on_bill": "KK Women's and Children's Hospital",
    "extraction_warnings": [
      "symptom_onset_date"
    ],
    "summary_narrative": "Priya Subramaniam delivered a healthy baby on 14 May 2025 after a normal vaginal delivery (ICD‑10 Z37.0). She stayed three nights in the post‑natal ward, received a newborn assessment and medications, with a total billed amount of SGD 8,200.00."
  }
}
```

### Actual API Response
```json
{
  "claim_reference_draft": "DRAFT-20260520-26596",
  "policy_no": "HIC-2025-00789",
  "claimant_name": "Priya Subramaniam",
  "id_document_type": "nric",
  "id_document_no": "S9023456D",
  "date_of_birth": "1990-05-18",
  "claimant_relationship": "self",
  "claim_type": "maternity",
  "incident_date": "2025-05-14",
  "claim_amount_requested": 8200.0,
  "provider_name": "KK Women's and Children's Hospital",
  "provider_registration": "MOH-HOSP-00273",
  "document_summary": {
    "total_billed_amount": 8200.0,
    "itemised_charges": [
      {
        "description": "Delivery Suite Charges (Normal Vaginal)",
        "quantity": 1,
        "unit_price": 3500.0
      },
      {
        "description": "Post-Natal Ward (Class B1 - 3 Nights)",
        "quantity": 3,
        "unit_price": 850.0
      },
      {
        "description": "Paediatrician Assessment (Newborn)",
        "quantity": 1,
        "unit_price": 250.0
      },
      {
        "description": "Medications & Consumables",
        "quantity": 1,
        "unit_price": 1900.0
      }
    ],
    "primary_diagnosis_icd10": "Z37.0",
    "procedure_cpt_codes": [
      "59400",
      "99232"
    ],
    "symptom_onset_date": null,
    "admission_date": "2025-05-14",
    "discharge_date": "2025-05-17",
    "attending_physician": "Dr. Kavitha Rajendran",
    "physician_license_no": "MCR-31457C",
    "pre_authorisation_no": "PA-2025-550001",
    "provider_name_on_bill": "KK Women's and Children's Hospital",
    "extraction_warnings": [
      "symptom_onset_date"
    ],
    "summary_narrative": "Priya Subramaniam delivered a healthy baby on 14 May 2025 after a normal vaginal delivery (ICD‑10 Z37.0). She stayed three nights in the post‑natal ward, received a newborn assessment and medications, with a total billed amount of SGD 8,200.00."
  },
  "policy_verified": true,
  "verification_failure": null,
  "policy_start_date": "2025-03-10",
  "policy_expiry_date": "2027-03-09",
  "policy_product_code": "COMP-HEALTH-GOLD",
  "premium_payment_mode": "annual",
  "dependent_verified": true,
  "verification_timestamp": "2026-05-19T17:45:30.809425Z"
}
```

### Expected Output (from contract)
```json
{
  "claim_reference_draft": "DRAFT-20250520-01103",
  "policy_no": "HIC-2025-00789",
  "claimant_name": "Priya Subramaniam",
  "id_document_type": "nric",
  "id_document_no": "S9023456D",
  "date_of_birth": "1990-05-18",
  "claimant_relationship": "self",
  "claim_type": "maternity",
  "incident_date": "2025-05-14",
  "claim_amount_requested": 8200.0,
  "provider_name": "KK Women's and Children's Hospital",
  "provider_registration": "MOH-HOSP-00273",
  "document_summary": {
    "total_billed_amount": 8200.0,
    "itemised_charges": [
      {
        "description": "Delivery suite charges (normal vaginal delivery)",
        "quantity": 1,
        "unit_price": 3500.0
      },
      {
        "description": "Ward charges (Class B1, 3 days)",
        "quantity": 3,
        "unit_price": 850.0
      },
      {
        "description": "Paediatrician assessment (newborn)",
        "quantity": 1,
        "unit_price": 250.0
      },
      {
        "description": "Medications and consumables",
        "quantity": 1,
        "unit_price": 1900.0
      }
    ],
    "primary_diagnosis_icd10": "Z37.0",
    "procedure_cpt_codes": [
      "59400",
      "99232"
    ],
    "symptom_onset_date": null,
    "admission_date": "2025-05-14",
    "discharge_date": "2025-05-17",
    "attending_physician": "Dr. Kavitha Rajendran",
    "physician_license_no": "MCR-31457C",
    "pre_authorisation_no": "PA-2025-550001",
    "provider_name_on_bill": "KK Women's and Children's Hospital",
    "extraction_warnings": [],
    "summary_narrative": "Priya Subramaniam, 35, admitted to KK Women's and Children's Hospital on 14 May 2025 for normal vaginal delivery (ICD-10 Z37.0). No prior symptom onset date recorded. Procedures include delivery suite and routine post-natal inpatient management (CPT 59400, 99232). Discharged 17 May 2025. Total billed SGD 8,200 covering delivery, 3-day ward stay, paediatric assessment, and medications. Pre-authorisation PA-2025-550001 submitted."
  },
  "policy_verified": true,
  "verification_failure": null,
  "policy_start_date": "2025-03-10",
  "policy_expiry_date": "2027-03-09",
  "policy_product_code": "COMP-HEALTH-GOLD",
  "premium_payment_mode": "annual",
  "dependent_verified": true,
  "verification_timestamp": "2025-05-20T11:01:00+08:00"
}
```

### Field-Level Comparison
| Status | Field | Actual | Expected | Note |
|:---:|:---|:---|:---|:---|
| ⏭️ | stage_2_verification._output.claim_reference_draft | DRAFT-20260520-26596 | DRAFT-20250520-01103 | Non-deterministic field skipped |
| ✅ | stage_2_verification._output.policy_no | HIC-2025-00789 | HIC-2025-00789 |  |
| ✅ | stage_2_verification._output.claimant_name | Priya Subramaniam | Priya Subramaniam |  |
| ✅ | stage_2_verification._output.id_document_type | nric | nric |  |
| ✅ | stage_2_verification._output.id_document_no | S9023456D | S9023456D |  |
| ✅ | stage_2_verification._output.date_of_birth | 1990-05-18 | 1990-05-18 |  |
| ✅ | stage_2_verification._output.claimant_relationship | self | self |  |
| ✅ | stage_2_verification._output.claim_type | maternity | maternity |  |
| ✅ | stage_2_verification._output.incident_date | 2025-05-14 | 2025-05-14 |  |
| ✅ | stage_2_verification._output.claim_amount_requested | 8200.0 | 8200.0 |  |
| ✅ | stage_2_verification._output.provider_name | KK Women's and Children's Hospital | KK Women's and Children's Hospital |  |
| ✅ | stage_2_verification._output.provider_registration | MOH-HOSP-00273 | MOH-HOSP-00273 |  |
| ✅ | stage_2_verification._output.document_summary.total_billed_amount | 8200.0 | 8200.0 |  |
| ⏭️ | stage_2_verification._output.document_summary.itemised_charges[0].description | Delivery Suite Charges (Normal Vaginal) | Delivery suite charges (normal vaginal delivery) | Non-deterministic field skipped |
| ✅ | stage_2_verification._output.document_summary.itemised_charges[0].quantity | 1 | 1 |  |
| ✅ | stage_2_verification._output.document_summary.itemised_charges[0].unit_price | 3500.0 | 3500.0 |  |
| ⏭️ | stage_2_verification._output.document_summary.itemised_charges[1].description | Post-Natal Ward (Class B1 - 3 Nights) | Ward charges (Class B1, 3 days) | Non-deterministic field skipped |
| ✅ | stage_2_verification._output.document_summary.itemised_charges[1].quantity | 3 | 3 |  |
| ✅ | stage_2_verification._output.document_summary.itemised_charges[1].unit_price | 850.0 | 850.0 |  |
| ⏭️ | stage_2_verification._output.document_summary.itemised_charges[2].description | Paediatrician Assessment (Newborn) | Paediatrician assessment (newborn) | Non-deterministic field skipped |
| ✅ | stage_2_verification._output.document_summary.itemised_charges[2].quantity | 1 | 1 |  |
| ✅ | stage_2_verification._output.document_summary.itemised_charges[2].unit_price | 250.0 | 250.0 |  |
| ⏭️ | stage_2_verification._output.document_summary.itemised_charges[3].description | Medications & Consumables | Medications and consumables | Non-deterministic field skipped |
| ✅ | stage_2_verification._output.document_summary.itemised_charges[3].quantity | 1 | 1 |  |
| ✅ | stage_2_verification._output.document_summary.itemised_charges[3].unit_price | 1900.0 | 1900.0 |  |
| ✅ | stage_2_verification._output.document_summary.primary_diagnosis_icd10 | Z37.0 | Z37.0 |  |
| ✅ | stage_2_verification._output.document_summary.procedure_cpt_codes[0] | 59400 | 59400 |  |
| ✅ | stage_2_verification._output.document_summary.procedure_cpt_codes[1] | 99232 | 99232 |  |
| ✅ | stage_2_verification._output.document_summary.symptom_onset_date | None | None |  |
| ✅ | stage_2_verification._output.document_summary.admission_date | 2025-05-14 | 2025-05-14 |  |
| ✅ | stage_2_verification._output.document_summary.discharge_date | 2025-05-17 | 2025-05-17 |  |
| ✅ | stage_2_verification._output.document_summary.attending_physician | Dr. Kavitha Rajendran | Dr. Kavitha Rajendran |  |
| ✅ | stage_2_verification._output.document_summary.physician_license_no | MCR-31457C | MCR-31457C |  |
| ✅ | stage_2_verification._output.document_summary.pre_authorisation_no | PA-2025-550001 | PA-2025-550001 |  |
| ✅ | stage_2_verification._output.document_summary.provider_name_on_bill | KK Women's and Children's Hospital | KK Women's and Children's Hospital |  |
| ⏭️ | stage_2_verification._output.document_summary.extraction_warnings | ['symptom_onset_date'] | [] | Non-deterministic field skipped |
| ⏭️ | stage_2_verification._output.document_summary.summary_narrative | Priya Subramaniam delivered a healthy baby on 14 May 2025 after a normal vaginal delivery (ICD‑10 Z37.0). She stayed thr | Priya Subramaniam, 35, admitted to KK Women's and Children's Hospital on 14 May 2025 for normal vaginal delivery (ICD-10 | Non-deterministic field skipped |
| ✅ | stage_2_verification._output.policy_verified | True | True |  |
| ✅ | stage_2_verification._output.verification_failure | None | None |  |
| ✅ | stage_2_verification._output.policy_start_date | 2025-03-10 | 2025-03-10 |  |
| ✅ | stage_2_verification._output.policy_expiry_date | 2027-03-09 | 2027-03-09 |  |
| ✅ | stage_2_verification._output.policy_product_code | COMP-HEALTH-GOLD | COMP-HEALTH-GOLD |  |
| ✅ | stage_2_verification._output.premium_payment_mode | annual | annual |  |
| ✅ | stage_2_verification._output.dependent_verified | True | True |  |
| ⏭️ | stage_2_verification._output.verification_timestamp | 2026-05-19T17:45:30.809425Z | 2025-05-20T11:01:00+08:00 | Non-deterministic field skipped |

---


## Stage 3 — Eligibility Check

**Endpoint:** `POST /eligibility/process`  
**Status:** ❌ Ineligible (EXPECTED for B003)  


### Request Payload (= Node 2 Output)
```json
{
  "claim_reference_draft": "DRAFT-20260520-26596",
  "policy_no": "HIC-2025-00789",
  "claimant_name": "Priya Subramaniam",
  "id_document_type": "nric",
  "id_document_no": "S9023456D",
  "date_of_birth": "1990-05-18",
  "claimant_relationship": "self",
  "claim_type": "maternity",
  "incident_date": "2025-05-14",
  "claim_amount_requested": 8200.0,
  "provider_name": "KK Women's and Children's Hospital",
  "provider_registration": "MOH-HOSP-00273",
  "document_summary": {
    "total_billed_amount": 8200.0,
    "itemised_charges": [
      {
        "description": "Delivery Suite Charges (Normal Vaginal)",
        "quantity": 1,
        "unit_price": 3500.0
      },
      {
        "description": "Post-Natal Ward (Class B1 - 3 Nights)",
        "quantity": 3,
        "unit_price": 850.0
      },
      {
        "description": "Paediatrician Assessment (Newborn)",
        "quantity": 1,
        "unit_price": 250.0
      },
      {
        "description": "Medications & Consumables",
        "quantity": 1,
        "unit_price": 1900.0
      }
    ],
    "primary_diagnosis_icd10": "Z37.0",
    "procedure_cpt_codes": [
      "59400",
      "99232"
    ],
    "symptom_onset_date": null,
    "admission_date": "2025-05-14",
    "discharge_date": "2025-05-17",
    "attending_physician": "Dr. Kavitha Rajendran",
    "physician_license_no": "MCR-31457C",
    "pre_authorisation_no": "PA-2025-550001",
    "provider_name_on_bill": "KK Women's and Children's Hospital",
    "extraction_warnings": [
      "symptom_onset_date"
    ],
    "summary_narrative": "Priya Subramaniam delivered a healthy baby on 14 May 2025 after a normal vaginal delivery (ICD‑10 Z37.0). She stayed three nights in the post‑natal ward, received a newborn assessment and medications, with a total billed amount of SGD 8,200.00."
  },
  "policy_verified": true,
  "verification_failure": null,
  "policy_start_date": "2025-03-10",
  "policy_expiry_date": "2027-03-09",
  "policy_product_code": "COMP-HEALTH-GOLD",
  "premium_payment_mode": "annual",
  "dependent_verified": true,
  "verification_timestamp": "2026-05-19T17:45:30.809425Z"
}
```

### Actual API Response
```json
{
  "claim_reference_draft": "DRAFT-20260520-26596",
  "policy_no": "HIC-2025-00789",
  "claimant_name": "Priya Subramaniam",
  "claim_type": "maternity",
  "incident_date": "2025-05-14",
  "claim_amount_requested": 8200.0,
  "policy_product_code": "COMP-HEALTH-GOLD",
  "provider_name": "KK Women's and Children's Hospital",
  "provider_registration": "MOH-HOSP-00273",
  "document_summary": {
    "total_billed_amount": 8200.0,
    "itemised_charges": [
      {
        "description": "Delivery Suite Charges (Normal Vaginal)",
        "quantity": 1,
        "unit_price": 3500.0
      },
      {
        "description": "Post-Natal Ward (Class B1 - 3 Nights)",
        "quantity": 3,
        "unit_price": 850.0
      },
      {
        "description": "Paediatrician Assessment (Newborn)",
        "quantity": 1,
        "unit_price": 250.0
      },
      {
        "description": "Medications & Consumables",
        "quantity": 1,
        "unit_price": 1900.0
      }
    ],
    "primary_diagnosis_icd10": "Z37.0",
    "procedure_cpt_codes": [
      "59400",
      "99232"
    ],
    "symptom_onset_date": null,
    "admission_date": "2025-05-14",
    "discharge_date": "2025-05-17",
    "attending_physician": "Dr. Kavitha Rajendran",
    "physician_license_no": "MCR-31457C",
    "pre_authorisation_no": "PA-2025-550001",
    "provider_name_on_bill": "KK Women's and Children's Hospital",
    "extraction_warnings": [
      "symptom_onset_date"
    ],
    "summary_narrative": "Priya Subramaniam delivered a healthy baby on 14 May 2025 after a normal vaginal delivery (ICD‑10 Z37.0). She stayed three nights in the post‑natal ward, received a newborn assessment and medications, with a total billed amount of SGD 8,200.00."
  },
  "eligible": false,
  "eligibility_failure_reason": "WAITING_PERIOD_NOT_MET",
  "waiting_period_satisfied": false,
  "waiting_period_days": 270,
  "waiting_period_basis": "incident_date",
  "annual_limit": 0.0,
  "annual_utilised": 0.0,
  "annual_limit_remaining": 0.0,
  "per_claim_limit": 0.0,
  "claimable_ceiling": 0.0,
  "exclusions_triggered": [],
  "eligibility_rationale": "Claim does not satisfy the 270-day waiting period for COMP-HEALTH-GOLD maternity. Reference date (incident_date): 2025-05-14; policy start: 2025-03-10; earliest valid date: 2025-12-05.",
  "eligibility_timestamp": "2026-05-19T17:45:30.819704Z"
}
```

### Expected Output (from contract)
```json
{
  "claim_reference_draft": "DRAFT-20250520-01103",
  "policy_no": "HIC-2025-00789",
  "claimant_name": "Priya Subramaniam",
  "claim_type": "maternity",
  "incident_date": "2025-05-14",
  "claim_amount_requested": 8200.0,
  "policy_product_code": "COMP-HEALTH-GOLD",
  "provider_name": "KK Women's and Children's Hospital",
  "provider_registration": "MOH-HOSP-00273",
  "document_summary": {
    "total_billed_amount": 8200.0,
    "itemised_charges": [
      {
        "description": "Delivery suite charges (normal vaginal delivery)",
        "quantity": 1,
        "unit_price": 3500.0
      },
      {
        "description": "Ward charges (Class B1, 3 days)",
        "quantity": 3,
        "unit_price": 850.0
      },
      {
        "description": "Paediatrician assessment (newborn)",
        "quantity": 1,
        "unit_price": 250.0
      },
      {
        "description": "Medications and consumables",
        "quantity": 1,
        "unit_price": 1900.0
      }
    ],
    "primary_diagnosis_icd10": "Z37.0",
    "procedure_cpt_codes": [
      "59400",
      "99232"
    ],
    "symptom_onset_date": null,
    "admission_date": "2025-05-14",
    "discharge_date": "2025-05-17",
    "attending_physician": "Dr. Kavitha Rajendran",
    "physician_license_no": "MCR-31457C",
    "pre_authorisation_no": "PA-2025-550001",
    "provider_name_on_bill": "KK Women's and Children's Hospital",
    "extraction_warnings": [],
    "summary_narrative": "Priya Subramaniam, 35, admitted to KK Women's and Children's Hospital on 14 May 2025 for normal vaginal delivery (ICD-10 Z37.0). No prior symptom onset date recorded. Procedures include delivery suite and routine post-natal inpatient management (CPT 59400, 99232). Discharged 17 May 2025. Total billed SGD 8,200 covering delivery, 3-day ward stay, paediatric assessment, and medications. Pre-authorisation PA-2025-550001 submitted."
  },
  "eligible": false,
  "eligibility_failure_reason": "WAITING_PERIOD_NOT_MET",
  "waiting_period_satisfied": false,
  "waiting_period_days": 270,
  "waiting_period_basis": "incident_date",
  "annual_limit": 0.0,
  "annual_utilised": 0.0,
  "annual_limit_remaining": 0.0,
  "per_claim_limit": 0.0,
  "claimable_ceiling": 0.0,
  "exclusions_triggered": [],
  "eligibility_rationale": "Maternity benefit under COMP-HEALTH-GOLD requires a 270-day waiting period from policy inception. Policy started 10 Mar 2025; incident date 14 May 2025 is only 65 days after inception — 205 days short of the required 270. No symptom onset date available to use as alternative reference. Claim is ineligible: WAITING_PERIOD_NOT_MET.",
  "eligibility_timestamp": "2025-05-20T11:02:00+08:00"
}
```

### Field-Level Comparison
| Status | Field | Actual | Expected | Note |
|:---:|:---|:---|:---|:---|
| ⏭️ | stage_3_eligibility._output.claim_reference_draft | DRAFT-20260520-26596 | DRAFT-20250520-01103 | Non-deterministic field skipped |
| ✅ | stage_3_eligibility._output.policy_no | HIC-2025-00789 | HIC-2025-00789 |  |
| ✅ | stage_3_eligibility._output.claimant_name | Priya Subramaniam | Priya Subramaniam |  |
| ✅ | stage_3_eligibility._output.claim_type | maternity | maternity |  |
| ✅ | stage_3_eligibility._output.incident_date | 2025-05-14 | 2025-05-14 |  |
| ✅ | stage_3_eligibility._output.claim_amount_requested | 8200.0 | 8200.0 |  |
| ✅ | stage_3_eligibility._output.policy_product_code | COMP-HEALTH-GOLD | COMP-HEALTH-GOLD |  |
| ✅ | stage_3_eligibility._output.provider_name | KK Women's and Children's Hospital | KK Women's and Children's Hospital |  |
| ✅ | stage_3_eligibility._output.provider_registration | MOH-HOSP-00273 | MOH-HOSP-00273 |  |
| ✅ | stage_3_eligibility._output.document_summary.total_billed_amount | 8200.0 | 8200.0 |  |
| ⏭️ | stage_3_eligibility._output.document_summary.itemised_charges[0].description | Delivery Suite Charges (Normal Vaginal) | Delivery suite charges (normal vaginal delivery) | Non-deterministic field skipped |
| ✅ | stage_3_eligibility._output.document_summary.itemised_charges[0].quantity | 1 | 1 |  |
| ✅ | stage_3_eligibility._output.document_summary.itemised_charges[0].unit_price | 3500.0 | 3500.0 |  |
| ⏭️ | stage_3_eligibility._output.document_summary.itemised_charges[1].description | Post-Natal Ward (Class B1 - 3 Nights) | Ward charges (Class B1, 3 days) | Non-deterministic field skipped |
| ✅ | stage_3_eligibility._output.document_summary.itemised_charges[1].quantity | 3 | 3 |  |
| ✅ | stage_3_eligibility._output.document_summary.itemised_charges[1].unit_price | 850.0 | 850.0 |  |
| ⏭️ | stage_3_eligibility._output.document_summary.itemised_charges[2].description | Paediatrician Assessment (Newborn) | Paediatrician assessment (newborn) | Non-deterministic field skipped |
| ✅ | stage_3_eligibility._output.document_summary.itemised_charges[2].quantity | 1 | 1 |  |
| ✅ | stage_3_eligibility._output.document_summary.itemised_charges[2].unit_price | 250.0 | 250.0 |  |
| ⏭️ | stage_3_eligibility._output.document_summary.itemised_charges[3].description | Medications & Consumables | Medications and consumables | Non-deterministic field skipped |
| ✅ | stage_3_eligibility._output.document_summary.itemised_charges[3].quantity | 1 | 1 |  |
| ✅ | stage_3_eligibility._output.document_summary.itemised_charges[3].unit_price | 1900.0 | 1900.0 |  |
| ✅ | stage_3_eligibility._output.document_summary.primary_diagnosis_icd10 | Z37.0 | Z37.0 |  |
| ✅ | stage_3_eligibility._output.document_summary.procedure_cpt_codes[0] | 59400 | 59400 |  |
| ✅ | stage_3_eligibility._output.document_summary.procedure_cpt_codes[1] | 99232 | 99232 |  |
| ✅ | stage_3_eligibility._output.document_summary.symptom_onset_date | None | None |  |
| ✅ | stage_3_eligibility._output.document_summary.admission_date | 2025-05-14 | 2025-05-14 |  |
| ✅ | stage_3_eligibility._output.document_summary.discharge_date | 2025-05-17 | 2025-05-17 |  |
| ✅ | stage_3_eligibility._output.document_summary.attending_physician | Dr. Kavitha Rajendran | Dr. Kavitha Rajendran |  |
| ✅ | stage_3_eligibility._output.document_summary.physician_license_no | MCR-31457C | MCR-31457C |  |
| ✅ | stage_3_eligibility._output.document_summary.pre_authorisation_no | PA-2025-550001 | PA-2025-550001 |  |
| ✅ | stage_3_eligibility._output.document_summary.provider_name_on_bill | KK Women's and Children's Hospital | KK Women's and Children's Hospital |  |
| ⏭️ | stage_3_eligibility._output.document_summary.extraction_warnings | ['symptom_onset_date'] | [] | Non-deterministic field skipped |
| ⏭️ | stage_3_eligibility._output.document_summary.summary_narrative | Priya Subramaniam delivered a healthy baby on 14 May 2025 after a normal vaginal delivery (ICD‑10 Z37.0). She stayed thr | Priya Subramaniam, 35, admitted to KK Women's and Children's Hospital on 14 May 2025 for normal vaginal delivery (ICD-10 | Non-deterministic field skipped |
| ✅ | stage_3_eligibility._output.eligible | False | False |  |
| ✅ | stage_3_eligibility._output.eligibility_failure_reason | WAITING_PERIOD_NOT_MET | WAITING_PERIOD_NOT_MET |  |
| ✅ | stage_3_eligibility._output.waiting_period_satisfied | False | False |  |
| ✅ | stage_3_eligibility._output.waiting_period_days | 270 | 270 |  |
| ✅ | stage_3_eligibility._output.waiting_period_basis | incident_date | incident_date |  |
| ✅ | stage_3_eligibility._output.annual_limit | 0.0 | 0.0 |  |
| ✅ | stage_3_eligibility._output.annual_utilised | 0.0 | 0.0 |  |
| ✅ | stage_3_eligibility._output.annual_limit_remaining | 0.0 | 0.0 |  |
| ✅ | stage_3_eligibility._output.per_claim_limit | 0.0 | 0.0 |  |
| ✅ | stage_3_eligibility._output.claimable_ceiling | 0.0 | 0.0 |  |
| ⏭️ | stage_3_eligibility._output.eligibility_rationale | Claim does not satisfy the 270-day waiting period for COMP-HEALTH-GOLD maternity. Reference date (incident_date): 2025-0 | Maternity benefit under COMP-HEALTH-GOLD requires a 270-day waiting period from policy inception. Policy started 10 Mar  | Non-deterministic field skipped |
| ⏭️ | stage_3_eligibility._output.eligibility_timestamp | 2026-05-19T17:45:30.819704Z | 2025-05-20T11:02:00+08:00 | Non-deterministic field skipped |

---


## Stages 4–6 — Skipped

> Pipeline halted at Node 3 — `eligible=false`, `eligibility_failure_reason=WAITING_PERIOD_NOT_MET`.  
> Nodes 4 (Medical Review), 5 (Adjudication), and 6 (Disbursement) are **not invoked** — this is the expected behaviour for B003.

---
