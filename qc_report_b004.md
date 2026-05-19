# QC Report — B004 Full Pipeline
**Scenario:** B004 — Surgical (Appendectomy), COMP-HEALTH-BRONZE, Self, Non-Panel Hospital, APPROVED with 60% non-panel reimbursement  
**Expected Outcome:** Node 4 flags NON_PANEL_PROVIDER. Node 5 applies 60% non-panel rate + SGD 3,500 deductible (fully consumed) + 20% co-pay + 20% co-insurance. Net payable SGD 1,392. Disbursed via provider_direct T+5.  
**API Target:** `http://127.0.0.1:8000`  
**Run Timestamp:** `2026-05-19T17:51:14Z`  



## Executive Summary

| Metric | Count |
|:---|:---:|
| ✅ PASS | 171 |
| ❌ FAIL | 0 |
| ⏭️ SKIP (non-deterministic) | 45 |
| ℹ️ INFO (extra keys) | 0 |

### Per-Node Results
| Result | Node | PASS | FAIL | SKIP |
|:---:|:---|:---:|:---:|:---:|
| ✅ | Node 1: Intake (upload) | 33 | 0 | 8 |
| ✅ | Node 2: Verification | 37 | 0 | 8 |
| ✅ | Node 3: Eligibility | 37 | 0 | 9 |
| ✅ | Node 4: Medical Review | 42 | 0 | 13 |
| ✅ | Node 5: Adjudication | 13 | 0 | 3 |
| ✅ | Node 6: Disbursement | 9 | 0 | 4 |

---

---

# Detailed Stage Logs


## Step 0 — DB Reset

**Endpoint:** `POST /dev/reset`  
**Status:** ✅ OK  
**Response:** `{"status":"reset_complete"}`

---


## Stage 1 — Claim Intake

**Endpoint:** `POST /intake/process` (multipart)  
**Uploaded Files:** ['medical_bill.pdf', 'discharge_summary.pdf', 'pre_auth_approval.pdf']  
**Status:** ✅ Accepted  


### Actual API Response
```json
{
  "claim_reference_draft": "DRAFT-20260520-31231",
  "policy_no": "HIC-2022-00321",
  "claimant_name": "Ahmad Zulkifli bin Hassan",
  "id_document_type": "nric",
  "id_document_no": "S7534567E",
  "date_of_birth": "1975-09-03",
  "claimant_relationship": "self",
  "claim_type": "surgical",
  "incident_date": "2025-05-02",
  "claim_date": "2025-05-10",
  "claim_amount_requested": 11800.0,
  "provider_name": "Novena Surgical and Orthopaedic Centre",
  "provider_registration": "PRV-HOSP-09921",
  "intake_accepted": true,
  "rejection_reason": null,
  "missing_documents": [],
  "intake_timestamp": "2026-05-20T01:51:35.385577+08:00",
  "document_summary": {
    "total_billed_amount": 12000.0,
    "itemised_charges": [
      {
        "description": "Open Appendectomy (Emergency)",
        "quantity": 1,
        "unit_price": 8500.0
      },
      {
        "description": "Anaesthesia (General)",
        "quantity": 1,
        "unit_price": 1200.0
      },
      {
        "description": "Post-Surgical Ward (2 Nights)",
        "quantity": 2,
        "unit_price": 650.0
      },
      {
        "description": "Post-Operative Medications",
        "quantity": 1,
        "unit_price": 1000.0
      }
    ],
    "primary_diagnosis_icd10": "K35.80",
    "procedure_cpt_codes": [
      "44950",
      "99232"
    ],
    "symptom_onset_date": "2025-05-01",
    "admission_date": "2025-05-02",
    "discharge_date": "2025-05-04",
    "attending_physician": "Dr. Tan Boon Kiat",
    "physician_license_no": "MCR-44012D",
    "pre_authorisation_no": "PA-2025-880001",
    "provider_name_on_bill": "Novena Surgical and Orthopaedic Centre",
    "extraction_warnings": [],
    "summary_narrative": "Ahmad Zulkifli bin Hassan, a 49-year-old male, was admitted on 2 May 2025 for acute appendicitis (ICD-10 K35.80) and underwent an open appendectomy (CPT 44950) on the same day. He also received general anaesthesia, two nights of post-surgical ward care, and post-operative medications. Total billed amount was SGD 12,000, with SGD 11,800 outstanding for insurance claim."
  }
}
```

### Expected Output (from contract)
```json
{
  "claim_reference_draft": "DRAFT-20250510-01104",
  "policy_no": "HIC-2022-00321",
  "claimant_name": "Ahmad Zulkifli bin Hassan",
  "id_document_type": "nric",
  "id_document_no": "S7534567E",
  "date_of_birth": "1975-09-03",
  "claimant_relationship": "self",
  "claim_type": "surgical",
  "incident_date": "2025-05-02",
  "claim_date": "2025-05-10",
  "claim_amount_requested": 11800.0,
  "provider_name": "Novena Surgical and Orthopaedic Centre",
  "provider_registration": "PRV-HOSP-09921",
  "intake_accepted": true,
  "rejection_reason": null,
  "missing_documents": [],
  "intake_timestamp": "2025-05-10T14:00:00+08:00",
  "document_summary": {
    "total_billed_amount": 12000.0,
    "itemised_charges": [
      {
        "description": "Appendectomy (open)",
        "quantity": 1,
        "unit_price": 8500.0
      },
      {
        "description": "Anaesthesia",
        "quantity": 1,
        "unit_price": 1200.0
      },
      {
        "description": "Ward charges (2 nights)",
        "quantity": 2,
        "unit_price": 650.0
      },
      {
        "description": "Post-operative medications",
        "quantity": 1,
        "unit_price": 1000.0
      }
    ],
    "primary_diagnosis_icd10": "K35.80",
    "procedure_cpt_codes": [
      "44950",
      "99232"
    ],
    "symptom_onset_date": "2025-05-01",
    "admission_date": "2025-05-02",
    "discharge_date": "2025-05-04",
    "attending_physician": "Dr. Tan Boon Kiat",
    "physician_license_no": "MCR-44012D",
    "pre_authorisation_no": "PA-2025-880001",
    "provider_name_on_bill": "Novena Surgical and Orthopaedic Centre",
    "extraction_warnings": [],
    "summary_narrative": "Ahmad Zulkifli bin Hassan, 49, admitted to Novena Surgical and Orthopaedic Centre on 2 May 2025 for acute appendicitis (ICD-10 K35.80). Symptoms first noted 1 May 2025. Open appendectomy performed (CPT 44950) with anaesthesia and 2-night post-surgical ward stay (CPT 99232). Total billed SGD 11,800 including surgery, anaesthesia, ward, and medications. Pre-authorisation PA-2025-880001 submitted."
  }
}
```

### Field-Level Comparison
| Status | Field | Actual | Expected | Note |
|:---:|:---|:---|:---|:---|
| ⏭️ | stage_1_intake._output.claim_reference_draft | DRAFT-20260520-31231 | DRAFT-20250510-01104 | Non-deterministic field skipped |
| ✅ | stage_1_intake._output.policy_no | HIC-2022-00321 | HIC-2022-00321 |  |
| ✅ | stage_1_intake._output.claimant_name | Ahmad Zulkifli bin Hassan | Ahmad Zulkifli bin Hassan |  |
| ✅ | stage_1_intake._output.id_document_type | nric | nric |  |
| ✅ | stage_1_intake._output.id_document_no | S7534567E | S7534567E |  |
| ✅ | stage_1_intake._output.date_of_birth | 1975-09-03 | 1975-09-03 |  |
| ✅ | stage_1_intake._output.claimant_relationship | self | self |  |
| ✅ | stage_1_intake._output.claim_type | surgical | surgical |  |
| ✅ | stage_1_intake._output.incident_date | 2025-05-02 | 2025-05-02 |  |
| ✅ | stage_1_intake._output.claim_date | 2025-05-10 | 2025-05-10 |  |
| ✅ | stage_1_intake._output.claim_amount_requested | 11800.0 | 11800.0 |  |
| ✅ | stage_1_intake._output.provider_name | Novena Surgical and Orthopaedic Centre | Novena Surgical and Orthopaedic Centre |  |
| ✅ | stage_1_intake._output.provider_registration | PRV-HOSP-09921 | PRV-HOSP-09921 |  |
| ✅ | stage_1_intake._output.intake_accepted | True | True |  |
| ✅ | stage_1_intake._output.rejection_reason | None | None |  |
| ⏭️ | stage_1_intake._output.intake_timestamp | 2026-05-20T01:51:35.385577+08:00 | 2025-05-10T14:00:00+08:00 | Non-deterministic field skipped |
| ✅ | stage_1_intake._output.document_summary.total_billed_amount | 12000.0 | 12000.0 |  |
| ⏭️ | stage_1_intake._output.document_summary.itemised_charges[0].description | Open Appendectomy (Emergency) | Appendectomy (open) | Non-deterministic field skipped |
| ✅ | stage_1_intake._output.document_summary.itemised_charges[0].quantity | 1 | 1 |  |
| ✅ | stage_1_intake._output.document_summary.itemised_charges[0].unit_price | 8500.0 | 8500.0 |  |
| ⏭️ | stage_1_intake._output.document_summary.itemised_charges[1].description | Anaesthesia (General) | Anaesthesia | Non-deterministic field skipped |
| ✅ | stage_1_intake._output.document_summary.itemised_charges[1].quantity | 1 | 1 |  |
| ✅ | stage_1_intake._output.document_summary.itemised_charges[1].unit_price | 1200.0 | 1200.0 |  |
| ⏭️ | stage_1_intake._output.document_summary.itemised_charges[2].description | Post-Surgical Ward (2 Nights) | Ward charges (2 nights) | Non-deterministic field skipped |
| ✅ | stage_1_intake._output.document_summary.itemised_charges[2].quantity | 2 | 2 |  |
| ✅ | stage_1_intake._output.document_summary.itemised_charges[2].unit_price | 650.0 | 650.0 |  |
| ⏭️ | stage_1_intake._output.document_summary.itemised_charges[3].description | Post-Operative Medications | Post-operative medications | Non-deterministic field skipped |
| ✅ | stage_1_intake._output.document_summary.itemised_charges[3].quantity | 1 | 1 |  |
| ✅ | stage_1_intake._output.document_summary.itemised_charges[3].unit_price | 1000.0 | 1000.0 |  |
| ✅ | stage_1_intake._output.document_summary.primary_diagnosis_icd10 | K35.80 | K35.80 |  |
| ✅ | stage_1_intake._output.document_summary.procedure_cpt_codes[0] | 44950 | 44950 |  |
| ✅ | stage_1_intake._output.document_summary.procedure_cpt_codes[1] | 99232 | 99232 |  |
| ✅ | stage_1_intake._output.document_summary.symptom_onset_date | 2025-05-01 | 2025-05-01 |  |
| ✅ | stage_1_intake._output.document_summary.admission_date | 2025-05-02 | 2025-05-02 |  |
| ✅ | stage_1_intake._output.document_summary.discharge_date | 2025-05-04 | 2025-05-04 |  |
| ✅ | stage_1_intake._output.document_summary.attending_physician | Dr. Tan Boon Kiat | Dr. Tan Boon Kiat |  |
| ✅ | stage_1_intake._output.document_summary.physician_license_no | MCR-44012D | MCR-44012D |  |
| ✅ | stage_1_intake._output.document_summary.pre_authorisation_no | PA-2025-880001 | PA-2025-880001 |  |
| ✅ | stage_1_intake._output.document_summary.provider_name_on_bill | Novena Surgical and Orthopaedic Centre | Novena Surgical and Orthopaedic Centre |  |
| ⏭️ | stage_1_intake._output.document_summary.extraction_warnings | [] | [] | Non-deterministic field skipped |
| ⏭️ | stage_1_intake._output.document_summary.summary_narrative | Ahmad Zulkifli bin Hassan, a 49-year-old male, was admitted on 2 May 2025 for acute appendicitis (ICD-10 K35.80) and und | Ahmad Zulkifli bin Hassan, 49, admitted to Novena Surgical and Orthopaedic Centre on 2 May 2025 for acute appendicitis ( | Non-deterministic field skipped |

---


## Stage 2 — Policy Verification

**Endpoint:** `POST /verification/process`  
**Status:** ✅ Verified  


### Actual API Response
```json
{
  "claim_reference_draft": "DRAFT-20260520-31231",
  "policy_no": "HIC-2022-00321",
  "claimant_name": "Ahmad Zulkifli bin Hassan",
  "id_document_type": "nric",
  "id_document_no": "S7534567E",
  "date_of_birth": "1975-09-03",
  "claimant_relationship": "self",
  "claim_type": "surgical",
  "incident_date": "2025-05-02",
  "claim_amount_requested": 11800.0,
  "provider_name": "Novena Surgical and Orthopaedic Centre",
  "provider_registration": "PRV-HOSP-09921",
  "document_summary": {
    "total_billed_amount": 12000.0,
    "itemised_charges": [
      {
        "description": "Open Appendectomy (Emergency)",
        "quantity": 1,
        "unit_price": 8500.0
      },
      {
        "description": "Anaesthesia (General)",
        "quantity": 1,
        "unit_price": 1200.0
      },
      {
        "description": "Post-Surgical Ward (2 Nights)",
        "quantity": 2,
        "unit_price": 650.0
      },
      {
        "description": "Post-Operative Medications",
        "quantity": 1,
        "unit_price": 1000.0
      }
    ],
    "primary_diagnosis_icd10": "K35.80",
    "procedure_cpt_codes": [
      "44950",
      "99232"
    ],
    "symptom_onset_date": "2025-05-01",
    "admission_date": "2025-05-02",
    "discharge_date": "2025-05-04",
    "attending_physician": "Dr. Tan Boon Kiat",
    "physician_license_no": "MCR-44012D",
    "pre_authorisation_no": "PA-2025-880001",
    "provider_name_on_bill": "Novena Surgical and Orthopaedic Centre",
    "extraction_warnings": [],
    "summary_narrative": "Ahmad Zulkifli bin Hassan, a 49-year-old male, was admitted on 2 May 2025 for acute appendicitis (ICD-10 K35.80) and underwent an open appendectomy (CPT 44950) on the same day. He also received general anaesthesia, two nights of post-surgical ward care, and post-operative medications. Total billed amount was SGD 12,000, with SGD 11,800 outstanding for insurance claim."
  },
  "policy_verified": true,
  "verification_failure": null,
  "policy_start_date": "2022-09-01",
  "policy_expiry_date": "2025-08-31",
  "policy_product_code": "COMP-HEALTH-BRONZE",
  "premium_payment_mode": "quarterly",
  "dependent_verified": true,
  "verification_timestamp": "2026-05-19T17:51:35.400336Z"
}
```

### Expected Output (from contract)
```json
{
  "claim_reference_draft": "DRAFT-20250510-01104",
  "policy_no": "HIC-2022-00321",
  "claimant_name": "Ahmad Zulkifli bin Hassan",
  "id_document_type": "nric",
  "id_document_no": "S7534567E",
  "date_of_birth": "1975-09-03",
  "claimant_relationship": "self",
  "claim_type": "surgical",
  "incident_date": "2025-05-02",
  "claim_amount_requested": 11800.0,
  "provider_name": "Novena Surgical and Orthopaedic Centre",
  "provider_registration": "PRV-HOSP-09921",
  "document_summary": {
    "total_billed_amount": 12000.0,
    "itemised_charges": [
      {
        "description": "Appendectomy (open)",
        "quantity": 1,
        "unit_price": 8500.0
      },
      {
        "description": "Anaesthesia",
        "quantity": 1,
        "unit_price": 1200.0
      },
      {
        "description": "Ward charges (2 nights)",
        "quantity": 2,
        "unit_price": 650.0
      },
      {
        "description": "Post-operative medications",
        "quantity": 1,
        "unit_price": 1000.0
      }
    ],
    "primary_diagnosis_icd10": "K35.80",
    "procedure_cpt_codes": [
      "44950",
      "99232"
    ],
    "symptom_onset_date": "2025-05-01",
    "admission_date": "2025-05-02",
    "discharge_date": "2025-05-04",
    "attending_physician": "Dr. Tan Boon Kiat",
    "physician_license_no": "MCR-44012D",
    "pre_authorisation_no": "PA-2025-880001",
    "provider_name_on_bill": "Novena Surgical and Orthopaedic Centre",
    "extraction_warnings": [],
    "summary_narrative": "Ahmad Zulkifli bin Hassan, 49, admitted to Novena Surgical and Orthopaedic Centre on 2 May 2025 for acute appendicitis (ICD-10 K35.80). Symptoms first noted 1 May 2025. Open appendectomy performed (CPT 44950) with anaesthesia and 2-night post-surgical ward stay (CPT 99232). Total billed SGD 11,800 including surgery, anaesthesia, ward, and medications. Pre-authorisation PA-2025-880001 submitted."
  },
  "policy_verified": true,
  "verification_failure": null,
  "policy_start_date": "2022-09-01",
  "policy_expiry_date": "2025-08-31",
  "policy_product_code": "COMP-HEALTH-BRONZE",
  "premium_payment_mode": "quarterly",
  "dependent_verified": true,
  "verification_timestamp": "2025-05-10T14:01:00+08:00"
}
```

### Field-Level Comparison
| Status | Field | Actual | Expected | Note |
|:---:|:---|:---|:---|:---|
| ⏭️ | stage_2_verification._output.claim_reference_draft | DRAFT-20260520-31231 | DRAFT-20250510-01104 | Non-deterministic field skipped |
| ✅ | stage_2_verification._output.policy_no | HIC-2022-00321 | HIC-2022-00321 |  |
| ✅ | stage_2_verification._output.claimant_name | Ahmad Zulkifli bin Hassan | Ahmad Zulkifli bin Hassan |  |
| ✅ | stage_2_verification._output.id_document_type | nric | nric |  |
| ✅ | stage_2_verification._output.id_document_no | S7534567E | S7534567E |  |
| ✅ | stage_2_verification._output.date_of_birth | 1975-09-03 | 1975-09-03 |  |
| ✅ | stage_2_verification._output.claimant_relationship | self | self |  |
| ✅ | stage_2_verification._output.claim_type | surgical | surgical |  |
| ✅ | stage_2_verification._output.incident_date | 2025-05-02 | 2025-05-02 |  |
| ✅ | stage_2_verification._output.claim_amount_requested | 11800.0 | 11800.0 |  |
| ✅ | stage_2_verification._output.provider_name | Novena Surgical and Orthopaedic Centre | Novena Surgical and Orthopaedic Centre |  |
| ✅ | stage_2_verification._output.provider_registration | PRV-HOSP-09921 | PRV-HOSP-09921 |  |
| ✅ | stage_2_verification._output.document_summary.total_billed_amount | 12000.0 | 12000.0 |  |
| ⏭️ | stage_2_verification._output.document_summary.itemised_charges[0].description | Open Appendectomy (Emergency) | Appendectomy (open) | Non-deterministic field skipped |
| ✅ | stage_2_verification._output.document_summary.itemised_charges[0].quantity | 1 | 1 |  |
| ✅ | stage_2_verification._output.document_summary.itemised_charges[0].unit_price | 8500.0 | 8500.0 |  |
| ⏭️ | stage_2_verification._output.document_summary.itemised_charges[1].description | Anaesthesia (General) | Anaesthesia | Non-deterministic field skipped |
| ✅ | stage_2_verification._output.document_summary.itemised_charges[1].quantity | 1 | 1 |  |
| ✅ | stage_2_verification._output.document_summary.itemised_charges[1].unit_price | 1200.0 | 1200.0 |  |
| ⏭️ | stage_2_verification._output.document_summary.itemised_charges[2].description | Post-Surgical Ward (2 Nights) | Ward charges (2 nights) | Non-deterministic field skipped |
| ✅ | stage_2_verification._output.document_summary.itemised_charges[2].quantity | 2 | 2 |  |
| ✅ | stage_2_verification._output.document_summary.itemised_charges[2].unit_price | 650.0 | 650.0 |  |
| ⏭️ | stage_2_verification._output.document_summary.itemised_charges[3].description | Post-Operative Medications | Post-operative medications | Non-deterministic field skipped |
| ✅ | stage_2_verification._output.document_summary.itemised_charges[3].quantity | 1 | 1 |  |
| ✅ | stage_2_verification._output.document_summary.itemised_charges[3].unit_price | 1000.0 | 1000.0 |  |
| ✅ | stage_2_verification._output.document_summary.primary_diagnosis_icd10 | K35.80 | K35.80 |  |
| ✅ | stage_2_verification._output.document_summary.procedure_cpt_codes[0] | 44950 | 44950 |  |
| ✅ | stage_2_verification._output.document_summary.procedure_cpt_codes[1] | 99232 | 99232 |  |
| ✅ | stage_2_verification._output.document_summary.symptom_onset_date | 2025-05-01 | 2025-05-01 |  |
| ✅ | stage_2_verification._output.document_summary.admission_date | 2025-05-02 | 2025-05-02 |  |
| ✅ | stage_2_verification._output.document_summary.discharge_date | 2025-05-04 | 2025-05-04 |  |
| ✅ | stage_2_verification._output.document_summary.attending_physician | Dr. Tan Boon Kiat | Dr. Tan Boon Kiat |  |
| ✅ | stage_2_verification._output.document_summary.physician_license_no | MCR-44012D | MCR-44012D |  |
| ✅ | stage_2_verification._output.document_summary.pre_authorisation_no | PA-2025-880001 | PA-2025-880001 |  |
| ✅ | stage_2_verification._output.document_summary.provider_name_on_bill | Novena Surgical and Orthopaedic Centre | Novena Surgical and Orthopaedic Centre |  |
| ⏭️ | stage_2_verification._output.document_summary.extraction_warnings | [] | [] | Non-deterministic field skipped |
| ⏭️ | stage_2_verification._output.document_summary.summary_narrative | Ahmad Zulkifli bin Hassan, a 49-year-old male, was admitted on 2 May 2025 for acute appendicitis (ICD-10 K35.80) and und | Ahmad Zulkifli bin Hassan, 49, admitted to Novena Surgical and Orthopaedic Centre on 2 May 2025 for acute appendicitis ( | Non-deterministic field skipped |
| ✅ | stage_2_verification._output.policy_verified | True | True |  |
| ✅ | stage_2_verification._output.verification_failure | None | None |  |
| ✅ | stage_2_verification._output.policy_start_date | 2022-09-01 | 2022-09-01 |  |
| ✅ | stage_2_verification._output.policy_expiry_date | 2025-08-31 | 2025-08-31 |  |
| ✅ | stage_2_verification._output.policy_product_code | COMP-HEALTH-BRONZE | COMP-HEALTH-BRONZE |  |
| ✅ | stage_2_verification._output.premium_payment_mode | quarterly | quarterly |  |
| ✅ | stage_2_verification._output.dependent_verified | True | True |  |
| ⏭️ | stage_2_verification._output.verification_timestamp | 2026-05-19T17:51:35.400336Z | 2025-05-10T14:01:00+08:00 | Non-deterministic field skipped |

---


## Stage 3 — Eligibility Check

**Endpoint:** `POST /eligibility/process`  
**Status:** ✅ Eligible  


### Actual API Response
```json
{
  "claim_reference_draft": "DRAFT-20260520-31231",
  "policy_no": "HIC-2022-00321",
  "claimant_name": "Ahmad Zulkifli bin Hassan",
  "claim_type": "surgical",
  "incident_date": "2025-05-02",
  "claim_amount_requested": 11800.0,
  "policy_product_code": "COMP-HEALTH-BRONZE",
  "provider_name": "Novena Surgical and Orthopaedic Centre",
  "provider_registration": "PRV-HOSP-09921",
  "document_summary": {
    "total_billed_amount": 12000.0,
    "itemised_charges": [
      {
        "description": "Open Appendectomy (Emergency)",
        "quantity": 1,
        "unit_price": 8500.0
      },
      {
        "description": "Anaesthesia (General)",
        "quantity": 1,
        "unit_price": 1200.0
      },
      {
        "description": "Post-Surgical Ward (2 Nights)",
        "quantity": 2,
        "unit_price": 650.0
      },
      {
        "description": "Post-Operative Medications",
        "quantity": 1,
        "unit_price": 1000.0
      }
    ],
    "primary_diagnosis_icd10": "K35.80",
    "procedure_cpt_codes": [
      "44950",
      "99232"
    ],
    "symptom_onset_date": "2025-05-01",
    "admission_date": "2025-05-02",
    "discharge_date": "2025-05-04",
    "attending_physician": "Dr. Tan Boon Kiat",
    "physician_license_no": "MCR-44012D",
    "pre_authorisation_no": "PA-2025-880001",
    "provider_name_on_bill": "Novena Surgical and Orthopaedic Centre",
    "extraction_warnings": [],
    "summary_narrative": "Ahmad Zulkifli bin Hassan, a 49-year-old male, was admitted on 2 May 2025 for acute appendicitis (ICD-10 K35.80) and underwent an open appendectomy (CPT 44950) on the same day. He also received general anaesthesia, two nights of post-surgical ward care, and post-operative medications. Total billed amount was SGD 12,000, with SGD 11,800 outstanding for insurance claim."
  },
  "eligible": true,
  "eligibility_failure_reason": null,
  "waiting_period_satisfied": true,
  "waiting_period_days": 90,
  "waiting_period_basis": "symptom_onset",
  "annual_limit": 25000.0,
  "annual_utilised": 0.0,
  "annual_limit_remaining": 25000.0,
  "per_claim_limit": 12000.0,
  "claimable_ceiling": 11800.0,
  "exclusions_triggered": [],
  "eligibility_rationale": "Surgical claim eligible under COMP-HEALTH-BRONZE. Waiting period satisfied. Claim of SGD 11,800 is within per-claim (SGD 12,000) and ample annual (SGD 25,000) limits. Lifetime limit not utilised.",
  "eligibility_timestamp": "2026-05-19T17:51:35.409252Z"
}
```

### Expected Output (from contract)
```json
{
  "claim_reference_draft": "DRAFT-20250510-01104",
  "policy_no": "HIC-2022-00321",
  "claimant_name": "Ahmad Zulkifli bin Hassan",
  "claim_type": "surgical",
  "incident_date": "2025-05-02",
  "claim_amount_requested": 11800.0,
  "policy_product_code": "COMP-HEALTH-BRONZE",
  "provider_name": "Novena Surgical and Orthopaedic Centre",
  "provider_registration": "PRV-HOSP-09921",
  "document_summary": {
    "total_billed_amount": 12000.0,
    "itemised_charges": [
      {
        "description": "Appendectomy (open)",
        "quantity": 1,
        "unit_price": 8500.0
      },
      {
        "description": "Anaesthesia",
        "quantity": 1,
        "unit_price": 1200.0
      },
      {
        "description": "Ward charges (2 nights)",
        "quantity": 2,
        "unit_price": 650.0
      },
      {
        "description": "Post-operative medications",
        "quantity": 1,
        "unit_price": 1000.0
      }
    ],
    "primary_diagnosis_icd10": "K35.80",
    "procedure_cpt_codes": [
      "44950",
      "99232"
    ],
    "symptom_onset_date": "2025-05-01",
    "admission_date": "2025-05-02",
    "discharge_date": "2025-05-04",
    "attending_physician": "Dr. Tan Boon Kiat",
    "physician_license_no": "MCR-44012D",
    "pre_authorisation_no": "PA-2025-880001",
    "provider_name_on_bill": "Novena Surgical and Orthopaedic Centre",
    "extraction_warnings": [],
    "summary_narrative": "Ahmad Zulkifli bin Hassan, 49, admitted to Novena Surgical and Orthopaedic Centre on 2 May 2025 for acute appendicitis (ICD-10 K35.80). Symptoms first noted 1 May 2025. Open appendectomy performed (CPT 44950) with anaesthesia and 2-night post-surgical ward stay (CPT 99232). Total billed SGD 11,800 including surgery, anaesthesia, ward, and medications. Pre-authorisation PA-2025-880001 submitted."
  },
  "eligible": true,
  "eligibility_failure_reason": null,
  "waiting_period_satisfied": true,
  "waiting_period_days": 90,
  "waiting_period_basis": "symptom_onset",
  "annual_limit": 25000.0,
  "annual_utilised": 0.0,
  "annual_limit_remaining": 25000.0,
  "per_claim_limit": 12000.0,
  "claimable_ceiling": 11800.0,
  "exclusions_triggered": [],
  "eligibility_rationale": "Surgical is covered under COMP-HEALTH-BRONZE with 90-day waiting period. Symptom onset 1 May 2025 is 972 days after policy inception 1 Sep 2022 — waiting period satisfied. K35.80 (appendicitis) triggers no exclusion. Annual limit SGD 25,000 fully available. Per-claim limit SGD 12,000 exceeds claim SGD 11,800. Claimable ceiling SGD 11,800.",
  "eligibility_timestamp": "2025-05-10T14:02:00+08:00"
}
```

### Field-Level Comparison
| Status | Field | Actual | Expected | Note |
|:---:|:---|:---|:---|:---|
| ⏭️ | stage_3_eligibility._output.claim_reference_draft | DRAFT-20260520-31231 | DRAFT-20250510-01104 | Non-deterministic field skipped |
| ✅ | stage_3_eligibility._output.policy_no | HIC-2022-00321 | HIC-2022-00321 |  |
| ✅ | stage_3_eligibility._output.claimant_name | Ahmad Zulkifli bin Hassan | Ahmad Zulkifli bin Hassan |  |
| ✅ | stage_3_eligibility._output.claim_type | surgical | surgical |  |
| ✅ | stage_3_eligibility._output.incident_date | 2025-05-02 | 2025-05-02 |  |
| ✅ | stage_3_eligibility._output.claim_amount_requested | 11800.0 | 11800.0 |  |
| ✅ | stage_3_eligibility._output.policy_product_code | COMP-HEALTH-BRONZE | COMP-HEALTH-BRONZE |  |
| ✅ | stage_3_eligibility._output.provider_name | Novena Surgical and Orthopaedic Centre | Novena Surgical and Orthopaedic Centre |  |
| ✅ | stage_3_eligibility._output.provider_registration | PRV-HOSP-09921 | PRV-HOSP-09921 |  |
| ✅ | stage_3_eligibility._output.document_summary.total_billed_amount | 12000.0 | 12000.0 |  |
| ⏭️ | stage_3_eligibility._output.document_summary.itemised_charges[0].description | Open Appendectomy (Emergency) | Appendectomy (open) | Non-deterministic field skipped |
| ✅ | stage_3_eligibility._output.document_summary.itemised_charges[0].quantity | 1 | 1 |  |
| ✅ | stage_3_eligibility._output.document_summary.itemised_charges[0].unit_price | 8500.0 | 8500.0 |  |
| ⏭️ | stage_3_eligibility._output.document_summary.itemised_charges[1].description | Anaesthesia (General) | Anaesthesia | Non-deterministic field skipped |
| ✅ | stage_3_eligibility._output.document_summary.itemised_charges[1].quantity | 1 | 1 |  |
| ✅ | stage_3_eligibility._output.document_summary.itemised_charges[1].unit_price | 1200.0 | 1200.0 |  |
| ⏭️ | stage_3_eligibility._output.document_summary.itemised_charges[2].description | Post-Surgical Ward (2 Nights) | Ward charges (2 nights) | Non-deterministic field skipped |
| ✅ | stage_3_eligibility._output.document_summary.itemised_charges[2].quantity | 2 | 2 |  |
| ✅ | stage_3_eligibility._output.document_summary.itemised_charges[2].unit_price | 650.0 | 650.0 |  |
| ⏭️ | stage_3_eligibility._output.document_summary.itemised_charges[3].description | Post-Operative Medications | Post-operative medications | Non-deterministic field skipped |
| ✅ | stage_3_eligibility._output.document_summary.itemised_charges[3].quantity | 1 | 1 |  |
| ✅ | stage_3_eligibility._output.document_summary.itemised_charges[3].unit_price | 1000.0 | 1000.0 |  |
| ✅ | stage_3_eligibility._output.document_summary.primary_diagnosis_icd10 | K35.80 | K35.80 |  |
| ✅ | stage_3_eligibility._output.document_summary.procedure_cpt_codes[0] | 44950 | 44950 |  |
| ✅ | stage_3_eligibility._output.document_summary.procedure_cpt_codes[1] | 99232 | 99232 |  |
| ✅ | stage_3_eligibility._output.document_summary.symptom_onset_date | 2025-05-01 | 2025-05-01 |  |
| ✅ | stage_3_eligibility._output.document_summary.admission_date | 2025-05-02 | 2025-05-02 |  |
| ✅ | stage_3_eligibility._output.document_summary.discharge_date | 2025-05-04 | 2025-05-04 |  |
| ✅ | stage_3_eligibility._output.document_summary.attending_physician | Dr. Tan Boon Kiat | Dr. Tan Boon Kiat |  |
| ✅ | stage_3_eligibility._output.document_summary.physician_license_no | MCR-44012D | MCR-44012D |  |
| ✅ | stage_3_eligibility._output.document_summary.pre_authorisation_no | PA-2025-880001 | PA-2025-880001 |  |
| ✅ | stage_3_eligibility._output.document_summary.provider_name_on_bill | Novena Surgical and Orthopaedic Centre | Novena Surgical and Orthopaedic Centre |  |
| ⏭️ | stage_3_eligibility._output.document_summary.extraction_warnings | [] | [] | Non-deterministic field skipped |
| ⏭️ | stage_3_eligibility._output.document_summary.summary_narrative | Ahmad Zulkifli bin Hassan, a 49-year-old male, was admitted on 2 May 2025 for acute appendicitis (ICD-10 K35.80) and und | Ahmad Zulkifli bin Hassan, 49, admitted to Novena Surgical and Orthopaedic Centre on 2 May 2025 for acute appendicitis ( | Non-deterministic field skipped |
| ✅ | stage_3_eligibility._output.eligible | True | True |  |
| ✅ | stage_3_eligibility._output.eligibility_failure_reason | None | None |  |
| ✅ | stage_3_eligibility._output.waiting_period_satisfied | True | True |  |
| ✅ | stage_3_eligibility._output.waiting_period_days | 90 | 90 |  |
| ✅ | stage_3_eligibility._output.waiting_period_basis | symptom_onset | symptom_onset |  |
| ✅ | stage_3_eligibility._output.annual_limit | 25000.0 | 25000.0 |  |
| ✅ | stage_3_eligibility._output.annual_utilised | 0.0 | 0.0 |  |
| ✅ | stage_3_eligibility._output.annual_limit_remaining | 25000.0 | 25000.0 |  |
| ✅ | stage_3_eligibility._output.per_claim_limit | 12000.0 | 12000.0 |  |
| ✅ | stage_3_eligibility._output.claimable_ceiling | 11800.0 | 11800.0 |  |
| ⏭️ | stage_3_eligibility._output.eligibility_rationale | Surgical claim eligible under COMP-HEALTH-BRONZE. Waiting period satisfied. Claim of SGD 11,800 is within per-claim (SGD | Surgical is covered under COMP-HEALTH-BRONZE with 90-day waiting period. Symptom onset 1 May 2025 is 972 days after poli | Non-deterministic field skipped |
| ⏭️ | stage_3_eligibility._output.eligibility_timestamp | 2026-05-19T17:51:35.409252Z | 2025-05-10T14:02:00+08:00 | Non-deterministic field skipped |

---


## Stage 4 — Medical Review

**Endpoint:** `POST /medical/process`  
**Status:** ✅ Passed  


### Actual API Response
```json
{
  "claim_reference_draft": "DRAFT-20260520-31231",
  "policy_no": "HIC-2022-00321",
  "claimant_name": "Ahmad Zulkifli bin Hassan",
  "claim_type": "surgical",
  "incident_date": "2025-05-02",
  "claim_amount_requested": 11800.0,
  "claimable_ceiling": 11800.0,
  "policy_product_code": "COMP-HEALTH-BRONZE",
  "provider_registration": "PRV-HOSP-09921",
  "document_summary": {
    "total_billed_amount": 12000.0,
    "itemised_charges": [
      {
        "description": "Open Appendectomy (Emergency)",
        "quantity": 1,
        "unit_price": 8500.0
      },
      {
        "description": "Anaesthesia (General)",
        "quantity": 1,
        "unit_price": 1200.0
      },
      {
        "description": "Post-Surgical Ward (2 Nights)",
        "quantity": 2,
        "unit_price": 650.0
      },
      {
        "description": "Post-Operative Medications",
        "quantity": 1,
        "unit_price": 1000.0
      }
    ],
    "primary_diagnosis_icd10": "K35.80",
    "procedure_cpt_codes": [
      "44950",
      "99232"
    ],
    "symptom_onset_date": "2025-05-01",
    "admission_date": "2025-05-02",
    "discharge_date": "2025-05-04",
    "attending_physician": "Dr. Tan Boon Kiat",
    "physician_license_no": "MCR-44012D",
    "pre_authorisation_no": "PA-2025-880001",
    "provider_name_on_bill": "Novena Surgical and Orthopaedic Centre",
    "extraction_warnings": [],
    "summary_narrative": "Ahmad Zulkifli bin Hassan, a 49-year-old male, was admitted on 2 May 2025 for acute appendicitis (ICD-10 K35.80) and underwent an open appendectomy (CPT 44950) on the same day. He also received general anaesthesia, two nights of post-surgical ward care, and post-operative medications. Total billed amount was SGD 12,000, with SGD 11,800 outstanding for insurance claim."
  },
  "medical_review_passed": true,
  "review_failure_reason": null,
  "non_panel_flag": true,
  "accreditation_claim": "Provider PRV-HOSP-09921 (Novena Surgical and Orthopaedic Centre) is not found in MOH accredited provider list as of 2026-05-19 per registry source: https://www.moh.gov.sg/hpp/allopathic-medicine/healthcare-institutions/hospitals",
  "physician_licence_claim": "Physician MCR-44012D (Dr. Tan Boon Kiat) is active with expiry 2026-12-31 per Singapore Medical Council Full Medical Register as of 2026-05-19",
  "coding_assessment": [
    {
      "cpt_code": "44950",
      "valid": true,
      "plausible": true,
      "reasoning": "Open appendectomy (CMS short descriptor: Appendectomy open) is clinically appropriate and standard of care for acute appendicitis per CMS_PFS_2024_SEED."
    },
    {
      "cpt_code": "99232",
      "valid": true,
      "plausible": true,
      "reasoning": "Subsequent hospital care (CMS short descriptor: Subsequent hospital care mod mdm) is appropriate for post-operative monitoring during inpatient stay per CMS_PFS_2024_SEED."
    }
  ],
  "pre_auth_verified": true,
  "length_of_stay": 2,
  "rps_benchmark": 8750.0,
  "bill_variance_pct": 37.14,
  "medical_necessity_confirmed": true,
  "medical_flags": [
    "NON_PANEL_PROVIDER"
  ],
  "medical_review_notes": "Appendectomy for acute appendicitis medically necessary. Non-panel facility: reimbursement at 60% of RPS benchmark SGD 8750. Pre-authorisation PA-2025-880001 valid and covers incident date. CPT codes valid and clinically appropriate. Total bill SGD 12000 exceeds benchmark.",
  "review_timestamp": "2026-05-19T17:51:37.655114Z"
}
```

### Expected Output (from contract)
```json
{
  "claim_reference_draft": "DRAFT-20250510-01104",
  "policy_no": "HIC-2022-00321",
  "claimant_name": "Ahmad Zulkifli bin Hassan",
  "claim_type": "surgical",
  "incident_date": "2025-05-02",
  "claim_amount_requested": 11800.0,
  "claimable_ceiling": 11800.0,
  "policy_product_code": "COMP-HEALTH-BRONZE",
  "provider_registration": "PRV-HOSP-09921",
  "document_summary": {
    "total_billed_amount": 12000.0,
    "itemised_charges": [
      {
        "description": "Appendectomy (open)",
        "quantity": 1,
        "unit_price": 8500.0
      },
      {
        "description": "Anaesthesia",
        "quantity": 1,
        "unit_price": 1200.0
      },
      {
        "description": "Ward charges (2 nights)",
        "quantity": 2,
        "unit_price": 650.0
      },
      {
        "description": "Post-operative medications",
        "quantity": 1,
        "unit_price": 1000.0
      }
    ],
    "primary_diagnosis_icd10": "K35.80",
    "procedure_cpt_codes": [
      "44950",
      "99232"
    ],
    "symptom_onset_date": "2025-05-01",
    "admission_date": "2025-05-02",
    "discharge_date": "2025-05-04",
    "attending_physician": "Dr. Tan Boon Kiat",
    "physician_license_no": "MCR-44012D",
    "pre_authorisation_no": "PA-2025-880001",
    "provider_name_on_bill": "Novena Surgical and Orthopaedic Centre",
    "extraction_warnings": [],
    "summary_narrative": "Ahmad Zulkifli bin Hassan, 49, admitted to Novena Surgical and Orthopaedic Centre on 2 May 2025 for acute appendicitis (ICD-10 K35.80). Symptoms first noted 1 May 2025. Open appendectomy performed (CPT 44950) with anaesthesia and 2-night post-surgical ward stay (CPT 99232). Total billed SGD 11,800 including surgery, anaesthesia, ward, and medications. Pre-authorisation PA-2025-880001 submitted."
  },
  "medical_review_passed": true,
  "review_failure_reason": null,
  "non_panel_flag": true,
  "accreditation_claim": "Novena Surgical and Orthopaedic Centre (PRV-HOSP-09921) was not found in the MOH accredited panel provider list as of 2025-05-10. Provider is a non-panel private hospital. Source: MOH Healthcare Institution Registry.",
  "physician_licence_claim": "Dr. Tan Boon Kiat (MCR-44012D) holds a valid and active medical licence under General Surgery, verified at SMC Full Medical Register on 2025-05-10. Valid through 2026-12-31.",
  "coding_assessment": [
    {
      "cpt_code": "44950",
      "valid": true,
      "plausible": true,
      "reasoning": "Appendectomy (CPT 44950) is standard surgical treatment for acute appendicitis K35.80."
    },
    {
      "cpt_code": "99232",
      "valid": true,
      "plausible": true,
      "reasoning": "Post-surgical inpatient monitoring (CPT 99232) is expected following appendectomy."
    }
  ],
  "pre_auth_verified": true,
  "length_of_stay": 2,
  "rps_benchmark": 8750.0,
  "bill_variance_pct": 37.14,
  "medical_necessity_confirmed": true,
  "medical_flags": [
    "NON_PANEL_PROVIDER"
  ],
  "medical_review_notes": "Non-panel private hospital Novena Surgical confirmed not on MOH panel — NON_PANEL_PROVIDER flagged. Dr. Tan Boon Kiat SMC licence valid through 2026. CPT 44950 (appendectomy) and 99232 (inpatient visit) clinically plausible for K35.80 appendicitis. Pre-auth PA-2025-880001 verified. Bill SGD 11,800 is 34.9% above RPS benchmark SGD 8,750 — within 50% threshold. Medical necessity confirmed.",
  "review_timestamp": "2025-05-10T14:03:30+08:00"
}
```

### Field-Level Comparison
| Status | Field | Actual | Expected | Note |
|:---:|:---|:---|:---|:---|
| ⏭️ | stage_4_medical_review._output.claim_reference_draft | DRAFT-20260520-31231 | DRAFT-20250510-01104 | Non-deterministic field skipped |
| ✅ | stage_4_medical_review._output.policy_no | HIC-2022-00321 | HIC-2022-00321 |  |
| ✅ | stage_4_medical_review._output.claimant_name | Ahmad Zulkifli bin Hassan | Ahmad Zulkifli bin Hassan |  |
| ✅ | stage_4_medical_review._output.claim_type | surgical | surgical |  |
| ✅ | stage_4_medical_review._output.incident_date | 2025-05-02 | 2025-05-02 |  |
| ✅ | stage_4_medical_review._output.claim_amount_requested | 11800.0 | 11800.0 |  |
| ✅ | stage_4_medical_review._output.claimable_ceiling | 11800.0 | 11800.0 |  |
| ✅ | stage_4_medical_review._output.policy_product_code | COMP-HEALTH-BRONZE | COMP-HEALTH-BRONZE |  |
| ✅ | stage_4_medical_review._output.provider_registration | PRV-HOSP-09921 | PRV-HOSP-09921 |  |
| ✅ | stage_4_medical_review._output.document_summary.total_billed_amount | 12000.0 | 12000.0 |  |
| ⏭️ | stage_4_medical_review._output.document_summary.itemised_charges[0].description | Open Appendectomy (Emergency) | Appendectomy (open) | Non-deterministic field skipped |
| ✅ | stage_4_medical_review._output.document_summary.itemised_charges[0].quantity | 1 | 1 |  |
| ✅ | stage_4_medical_review._output.document_summary.itemised_charges[0].unit_price | 8500.0 | 8500.0 |  |
| ⏭️ | stage_4_medical_review._output.document_summary.itemised_charges[1].description | Anaesthesia (General) | Anaesthesia | Non-deterministic field skipped |
| ✅ | stage_4_medical_review._output.document_summary.itemised_charges[1].quantity | 1 | 1 |  |
| ✅ | stage_4_medical_review._output.document_summary.itemised_charges[1].unit_price | 1200.0 | 1200.0 |  |
| ⏭️ | stage_4_medical_review._output.document_summary.itemised_charges[2].description | Post-Surgical Ward (2 Nights) | Ward charges (2 nights) | Non-deterministic field skipped |
| ✅ | stage_4_medical_review._output.document_summary.itemised_charges[2].quantity | 2 | 2 |  |
| ✅ | stage_4_medical_review._output.document_summary.itemised_charges[2].unit_price | 650.0 | 650.0 |  |
| ⏭️ | stage_4_medical_review._output.document_summary.itemised_charges[3].description | Post-Operative Medications | Post-operative medications | Non-deterministic field skipped |
| ✅ | stage_4_medical_review._output.document_summary.itemised_charges[3].quantity | 1 | 1 |  |
| ✅ | stage_4_medical_review._output.document_summary.itemised_charges[3].unit_price | 1000.0 | 1000.0 |  |
| ✅ | stage_4_medical_review._output.document_summary.primary_diagnosis_icd10 | K35.80 | K35.80 |  |
| ✅ | stage_4_medical_review._output.document_summary.procedure_cpt_codes[0] | 44950 | 44950 |  |
| ✅ | stage_4_medical_review._output.document_summary.procedure_cpt_codes[1] | 99232 | 99232 |  |
| ✅ | stage_4_medical_review._output.document_summary.symptom_onset_date | 2025-05-01 | 2025-05-01 |  |
| ✅ | stage_4_medical_review._output.document_summary.admission_date | 2025-05-02 | 2025-05-02 |  |
| ✅ | stage_4_medical_review._output.document_summary.discharge_date | 2025-05-04 | 2025-05-04 |  |
| ✅ | stage_4_medical_review._output.document_summary.attending_physician | Dr. Tan Boon Kiat | Dr. Tan Boon Kiat |  |
| ✅ | stage_4_medical_review._output.document_summary.physician_license_no | MCR-44012D | MCR-44012D |  |
| ✅ | stage_4_medical_review._output.document_summary.pre_authorisation_no | PA-2025-880001 | PA-2025-880001 |  |
| ✅ | stage_4_medical_review._output.document_summary.provider_name_on_bill | Novena Surgical and Orthopaedic Centre | Novena Surgical and Orthopaedic Centre |  |
| ⏭️ | stage_4_medical_review._output.document_summary.extraction_warnings | [] | [] | Non-deterministic field skipped |
| ⏭️ | stage_4_medical_review._output.document_summary.summary_narrative | Ahmad Zulkifli bin Hassan, a 49-year-old male, was admitted on 2 May 2025 for acute appendicitis (ICD-10 K35.80) and und | Ahmad Zulkifli bin Hassan, 49, admitted to Novena Surgical and Orthopaedic Centre on 2 May 2025 for acute appendicitis ( | Non-deterministic field skipped |
| ✅ | stage_4_medical_review._output.medical_review_passed | True | True |  |
| ✅ | stage_4_medical_review._output.review_failure_reason | None | None |  |
| ✅ | stage_4_medical_review._output.non_panel_flag | True | True |  |
| ⏭️ | stage_4_medical_review._output.accreditation_claim | Provider PRV-HOSP-09921 (Novena Surgical and Orthopaedic Centre) is not found in MOH accredited provider list as of 2026 | Novena Surgical and Orthopaedic Centre (PRV-HOSP-09921) was not found in the MOH accredited panel provider list as of 20 | Non-deterministic field skipped |
| ⏭️ | stage_4_medical_review._output.physician_licence_claim | Physician MCR-44012D (Dr. Tan Boon Kiat) is active with expiry 2026-12-31 per Singapore Medical Council Full Medical Reg | Dr. Tan Boon Kiat (MCR-44012D) holds a valid and active medical licence under General Surgery, verified at SMC Full Medi | Non-deterministic field skipped |
| ✅ | stage_4_medical_review._output.coding_assessment[0].cpt_code | 44950 | 44950 |  |
| ✅ | stage_4_medical_review._output.coding_assessment[0].valid | True | True |  |
| ✅ | stage_4_medical_review._output.coding_assessment[0].plausible | True | True |  |
| ⏭️ | stage_4_medical_review._output.coding_assessment[0].reasoning | Open appendectomy (CMS short descriptor: Appendectomy open) is clinically appropriate and standard of care for acute app | Appendectomy (CPT 44950) is standard surgical treatment for acute appendicitis K35.80. | Non-deterministic field skipped |
| ✅ | stage_4_medical_review._output.coding_assessment[1].cpt_code | 99232 | 99232 |  |
| ✅ | stage_4_medical_review._output.coding_assessment[1].valid | True | True |  |
| ✅ | stage_4_medical_review._output.coding_assessment[1].plausible | True | True |  |
| ⏭️ | stage_4_medical_review._output.coding_assessment[1].reasoning | Subsequent hospital care (CMS short descriptor: Subsequent hospital care mod mdm) is appropriate for post-operative moni | Post-surgical inpatient monitoring (CPT 99232) is expected following appendectomy. | Non-deterministic field skipped |
| ✅ | stage_4_medical_review._output.pre_auth_verified | True | True |  |
| ✅ | stage_4_medical_review._output.length_of_stay | 2 | 2 |  |
| ✅ | stage_4_medical_review._output.rps_benchmark | 8750.0 | 8750.0 |  |
| ✅ | stage_4_medical_review._output.bill_variance_pct | 37.14 | 37.14 |  |
| ✅ | stage_4_medical_review._output.medical_necessity_confirmed | True | True |  |
| ✅ | stage_4_medical_review._output.medical_flags[0] | NON_PANEL_PROVIDER | NON_PANEL_PROVIDER |  |
| ⏭️ | stage_4_medical_review._output.medical_review_notes | Appendectomy for acute appendicitis medically necessary. Non-panel facility: reimbursement at 60% of RPS benchmark SGD 8 | Non-panel private hospital Novena Surgical confirmed not on MOH panel — NON_PANEL_PROVIDER flagged. Dr. Tan Boon Kiat SM | Non-deterministic field skipped |
| ⏭️ | stage_4_medical_review._output.review_timestamp | 2026-05-19T17:51:37.655114Z | 2025-05-10T14:03:30+08:00 | Non-deterministic field skipped |

---


## Stage 5 — Financial Adjudication

**Endpoint:** `POST /adjudication/process`  
**Status:** ✅ Approved  


### Actual API Response
```json
{
  "claim_reference_draft": "DRAFT-20260520-31231",
  "policy_no": "HIC-2022-00321",
  "claimant_name": "Ahmad Zulkifli bin Hassan",
  "claim_type": "surgical",
  "incident_date": "2025-05-02",
  "claim_amount_requested": 11800.0,
  "provider_registration": "PRV-HOSP-09921",
  "adjudication_base": 5250.0,
  "deductible_applied_this_claim": 3500.0,
  "co_pay_amount": 350.0,
  "co_insurance_amount": 280.0,
  "net_payable": 1120.0,
  "claimant_liability": 10680.0,
  "adjudication_status": "approved",
  "adjudication_notes": "Claim approved. Based on a capped adjudication base of SGD 5,250.00, cost-sharing applies. The annual deductible of SGD 3,500.00 is applied first. For this non-panel provider claim, reimbursement is at 60%. A co-payment of SGD 350.00 and co-insurance of SGD 280.00 are then applied. The final insurer disbursement is SGD 1,120.00.",
  "adjudication_timestamp": "2026-05-19T17:51:50.844524Z"
}
```

### Expected Output (from contract)
```json
{
  "claim_reference_draft": "DRAFT-20250510-01104",
  "policy_no": "HIC-2022-00321",
  "claimant_name": "Ahmad Zulkifli bin Hassan",
  "claim_type": "surgical",
  "incident_date": "2025-05-02",
  "claim_amount_requested": 11800.0,
  "provider_registration": "PRV-HOSP-09921",
  "adjudication_base": 5250.0,
  "deductible_applied_this_claim": 3500.0,
  "co_pay_amount": 350.0,
  "co_insurance_amount": 280.0,
  "net_payable": 1120.0,
  "claimant_liability": 10680.0,
  "adjudication_status": "approved",
  "adjudication_notes": "Non-panel provider: 60% Bronze reimbursement applied — base reduced from RPS SGD 8,750 to SGD 5,250. Annual deductible SGD 3,500 fully applied. Co-pay 20% = SGD 350. Co-insurance 20% = SGD 280 (below SGD 2,000 cap). Net payable SGD 1,120. Claimant liability SGD 10,680.",
  "adjudication_timestamp": "2025-05-10T14:04:00+08:00"
}
```

### Field-Level Comparison
| Status | Field | Actual | Expected | Note |
|:---:|:---|:---|:---|:---|
| ⏭️ | stage_5_adjudication._output.claim_reference_draft | DRAFT-20260520-31231 | DRAFT-20250510-01104 | Non-deterministic field skipped |
| ✅ | stage_5_adjudication._output.policy_no | HIC-2022-00321 | HIC-2022-00321 |  |
| ✅ | stage_5_adjudication._output.claimant_name | Ahmad Zulkifli bin Hassan | Ahmad Zulkifli bin Hassan |  |
| ✅ | stage_5_adjudication._output.claim_type | surgical | surgical |  |
| ✅ | stage_5_adjudication._output.incident_date | 2025-05-02 | 2025-05-02 |  |
| ✅ | stage_5_adjudication._output.claim_amount_requested | 11800.0 | 11800.0 |  |
| ✅ | stage_5_adjudication._output.provider_registration | PRV-HOSP-09921 | PRV-HOSP-09921 |  |
| ✅ | stage_5_adjudication._output.adjudication_base | 5250.0 | 5250.0 |  |
| ✅ | stage_5_adjudication._output.deductible_applied_this_claim | 3500.0 | 3500.0 |  |
| ✅ | stage_5_adjudication._output.co_pay_amount | 350.0 | 350.0 |  |
| ✅ | stage_5_adjudication._output.co_insurance_amount | 280.0 | 280.0 |  |
| ✅ | stage_5_adjudication._output.net_payable | 1120.0 | 1120.0 |  |
| ✅ | stage_5_adjudication._output.claimant_liability | 10680.0 | 10680.0 |  |
| ✅ | stage_5_adjudication._output.adjudication_status | approved | approved |  |
| ⏭️ | stage_5_adjudication._output.adjudication_notes | Claim approved. Based on a capped adjudication base of SGD 5,250.00, cost-sharing applies. The annual deductible of SGD  | Non-panel provider: 60% Bronze reimbursement applied — base reduced from RPS SGD 8,750 to SGD 5,250. Annual deductible S | Non-deterministic field skipped |
| ⏭️ | stage_5_adjudication._output.adjudication_timestamp | 2026-05-19T17:51:50.844524Z | 2025-05-10T14:04:00+08:00 | Non-deterministic field skipped |

---


## Stage 6 — Disbursement

**Endpoint:** `POST /disbursement/process`  
**Status:** ✅ Disbursed  


### Actual API Response
```json
{
  "claim_reference_no": "CLM-2025-0001102",
  "policy_no": "HIC-2022-00321",
  "claimant_name": "Ahmad Zulkifli bin Hassan",
  "claim_type": "surgical",
  "disbursement_status": "disbursed",
  "net_payable": 1120.0,
  "claimant_liability": 10680.0,
  "payment_mode": "provider_direct",
  "payee_name": "Novena Surgical and Orthopaedic Centre (UOB ******9921)",
  "disbursement_date": "2026-05-24",
  "incident_date": "2025-05-02",
  "remarks": "Claim CLM-2025-0001102 approved. SGD 1120.00 to be disbursed via provider-direct payment by 24 May 2026 (T+5). Non-panel provider discount was applied. Claimant liability: SGD 10680.00.",
  "processing_timestamp": "2026-05-19T17:51:54.075753Z"
}
```

### Expected Output (from contract)
```json
{
  "claim_reference_no": "CLM-2025-0001104",
  "policy_no": "HIC-2022-00321",
  "claimant_name": "Ahmad Zulkifli bin Hassan",
  "claim_type": "surgical",
  "disbursement_status": "disbursed",
  "net_payable": 1120.0,
  "claimant_liability": 10680.0,
  "payment_mode": "provider_direct",
  "payee_name": "Novena Surgical and Orthopaedic Centre (UOB ******9921)",
  "disbursement_date": "2025-05-15",
  "incident_date": "2025-05-02",
  "remarks": "Claim CLM-2025-0001104 approved. Non-panel 60% reimbursement and SGD 3,500 annual deductible applied. Net payable SGD 1,120 disbursed directly to Novena Surgical and Orthopaedic Centre via UOB provider_direct by 15 May 2025 (T+5).",
  "processing_timestamp": "2025-05-10T14:05:00+08:00"
}
```

### Field-Level Comparison
| Status | Field | Actual | Expected | Note |
|:---:|:---|:---|:---|:---|
| ⏭️ | stage_6_disbursement._output.claim_reference_no | CLM-2025-0001102 | CLM-2025-0001104 | Non-deterministic field skipped |
| ✅ | stage_6_disbursement._output.policy_no | HIC-2022-00321 | HIC-2022-00321 |  |
| ✅ | stage_6_disbursement._output.claimant_name | Ahmad Zulkifli bin Hassan | Ahmad Zulkifli bin Hassan |  |
| ✅ | stage_6_disbursement._output.claim_type | surgical | surgical |  |
| ✅ | stage_6_disbursement._output.disbursement_status | disbursed | disbursed |  |
| ✅ | stage_6_disbursement._output.net_payable | 1120.0 | 1120.0 |  |
| ✅ | stage_6_disbursement._output.claimant_liability | 10680.0 | 10680.0 |  |
| ✅ | stage_6_disbursement._output.payment_mode | provider_direct | provider_direct |  |
| ✅ | stage_6_disbursement._output.payee_name | Novena Surgical and Orthopaedic Centre (UOB ******9921) | Novena Surgical and Orthopaedic Centre (UOB ******9921) |  |
| ⏭️ | stage_6_disbursement._output.disbursement_date | 2026-05-24 | 2025-05-15 | Non-deterministic field skipped |
| ✅ | stage_6_disbursement._output.incident_date | 2025-05-02 | 2025-05-02 |  |
| ⏭️ | stage_6_disbursement._output.remarks | Claim CLM-2025-0001102 approved. SGD 1120.00 to be disbursed via provider-direct payment by 24 May 2026 (T+5). Non-panel | Claim CLM-2025-0001104 approved. Non-panel 60% reimbursement and SGD 3,500 annual deductible applied. Net payable SGD 1, | Non-deterministic field skipped |
| ⏭️ | stage_6_disbursement._output.processing_timestamp | 2026-05-19T17:51:54.075753Z | 2025-05-10T14:05:00+08:00 | Non-deterministic field skipped |

---
