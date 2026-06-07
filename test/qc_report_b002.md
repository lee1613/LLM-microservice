# QC Report — B002 Full Pipeline
**Scenario:** B002 — Outpatient (Essential Hypertension, GP visit), COMP-HEALTH-SILVER, Spouse Dependent, NON-PANEL GP, APPROVED with reduced payout  
**Expected Outcome:** Node 4 flags NON_PANEL_PROVIDER. Partial deductible (SGD 180) already consumed. Approved with non-panel 70% reimbursement applied. Disbursed via cheque T+7.  
**API Target:** `http://139.180.136.212`  
**Run Timestamp:** `2026-05-19T18:09:38Z`  



## Executive Summary

| Metric | Count |
|:---|:---:|
| ✅ PASS | 141 |
| ❌ FAIL | 8 |
| ⏭️ SKIP (non-deterministic) | 26 |
| ℹ️ INFO (extra keys) | 0 |

### Per-Node Results
| Result | Node | PASS | FAIL | SKIP |
|:---:|:---|:---:|:---:|:---:|
| ❌ | Node 1: Intake (upload) | 26 | 1 | 3 |
| ❌ | Node 2: Verification | 30 | 1 | 3 |
| ❌ | Node 3: Eligibility | 30 | 1 | 4 |
| ❌ | Node 4: Medical Review | 35 | 5 | 9 |
| ✅ | Node 5: Adjudication | 13 | 0 | 3 |
| ✅ | Node 6: Disbursement | 7 | 0 | 4 |

---

## ❌ Failed Assertions Summary

| Field | Actual | Expected | Note |
|:---|:---|:---|:---|
| stage_1_intake._output.document_summary.itemised_charges | [{'description': 'GP Consultation Fee', 'quantity': 1, 'unit_price': 85.0}, {'description': 'Blood Pressure Monitoring & ECG', 'quantity': 1, 'unit_pr | [{'description': 'Consultation fee (GP)', 'quantity': 1, 'unit_price': 85.0}, {'description': 'Blood pressure monitoring + ECG', 'quantity': 1, 'unit_ | List length mismatch: actual=5 expected=4 |
| stage_2_verification._output.document_summary.itemised_charges | [{'description': 'GP Consultation Fee', 'quantity': 1, 'unit_price': 85.0}, {'description': 'Blood Pressure Monitoring & ECG', 'quantity': 1, 'unit_pr | [{'description': 'Consultation fee (GP)', 'quantity': 1, 'unit_price': 85.0}, {'description': 'Blood pressure monitoring + ECG', 'quantity': 1, 'unit_ | List length mismatch: actual=5 expected=4 |
| stage_3_eligibility._output.document_summary.itemised_charges | [{'description': 'GP Consultation Fee', 'quantity': 1, 'unit_price': 85.0}, {'description': 'Blood Pressure Monitoring & ECG', 'quantity': 1, 'unit_pr | [{'description': 'Consultation fee (GP)', 'quantity': 1, 'unit_price': 85.0}, {'description': 'Blood pressure monitoring + ECG', 'quantity': 1, 'unit_ | List length mismatch: actual=5 expected=4 |
| stage_4_medical_review._output.document_summary.itemised_charges | [{'description': 'GP Consultation Fee', 'quantity': 1, 'unit_price': 85.0}, {'description': 'Blood Pressure Monitoring & ECG', 'quantity': 1, 'unit_pr | [{'description': 'Consultation fee (GP)', 'quantity': 1, 'unit_price': 85.0}, {'description': 'Blood pressure monitoring + ECG', 'quantity': 1, 'unit_ | List length mismatch: actual=5 expected=4 |
| stage_4_medical_review._output.medical_review_passed | False | True | Value mismatch |
| stage_4_medical_review._output.review_failure_reason | CPT_ICD10_MISMATCH | None | Value mismatch |
| stage_4_medical_review._output.coding_assessment[1].plausible | False | True | Value mismatch |
| stage_4_medical_review._output.medical_necessity_confirmed | False | True | Value mismatch |

---

# Detailed Stage Logs


## Step 0 — DB Reset

**Endpoint:** `POST /dev/reset`  
**Status:** ✅ OK  
**Response:** `{"status":"reset_complete"}`

---


## Stage 1 — Claim Intake

**Endpoint:** `POST /intake/process` (multipart: JSON metadata + PDF file uploads)  
**Uploaded Files:** ['medical_bill.pdf']  
**Status:** ✅ Accepted  


### Request Metadata (claim_data form field)
```json
{
  "policy_no": "HIC-2023-00456",
  "claimant_name": "Lim Kai Xuan",
  "claimant_relationship": "spouse",
  "id_document_type": "nric",
  "id_document_no": "S8867890C",
  "date_of_birth": "1988-11-30",
  "incident_date": "2025-04-20",
  "claim_date": "2025-04-22",
  "claim_type": "outpatient",
  "claim_amount_requested": 380.0,
  "provider_name": "CityMed Family Clinic",
  "provider_registration": "PRV-CLIN-07734",
  "supporting_documents": [
    "medical_bill"
  ]
}
```

### Actual API Response
```json
{
  "claim_reference_draft": "DRAFT-20260520-10509",
  "policy_no": "HIC-2023-00456",
  "claimant_name": "Lim Kai Xuan",
  "id_document_type": "nric",
  "id_document_no": "S8867890C",
  "date_of_birth": "1988-11-30",
  "claimant_relationship": "spouse",
  "claim_type": "outpatient",
  "incident_date": "2025-04-20",
  "claim_date": "2025-04-22",
  "claim_amount_requested": 380.0,
  "provider_name": "CityMed Family Clinic",
  "provider_registration": "PRV-CLIN-07734",
  "intake_accepted": true,
  "rejection_reason": null,
  "missing_documents": [],
  "intake_timestamp": "2026-05-20T02:09:50.023224+08:00",
  "document_summary": {
    "total_billed_amount": 380.0,
    "itemised_charges": [
      {
        "description": "GP Consultation Fee",
        "quantity": 1,
        "unit_price": 85.0
      },
      {
        "description": "Blood Pressure Monitoring & ECG",
        "quantity": 1,
        "unit_price": 60.0
      },
      {
        "description": "Basic Metabolic Panel (Blood Test)",
        "quantity": 1,
        "unit_price": 45.0
      },
      {
        "description": "Amlodipine 5mg",
        "quantity": 1,
        "unit_price": 90.0
      },
      {
        "description": "Perindopril 4mg",
        "quantity": 1,
        "unit_price": 100.0
      }
    ],
    "primary_diagnosis_icd10": "I10",
    "procedure_cpt_codes": [
      "99213",
      "93000",
      "80048"
    ],
    "symptom_onset_date": null,
    "admission_date": null,
    "discharge_date": null,
    "attending_physician": "Dr. Farhan Bin Riza",
    "physician_license_no": "MCR-67890F",
    "pre_authorisation_no": null,
    "provider_name_on_bill": "CityMed Family Clinic",
    "extraction_warnings": [],
    "summary_narrative": "Patient Lim Kai Xuan visited CityMed Family Clinic on 20 April 2025 for an outpatient consultation. Diagnosed with hypertension, the physician prescribed a 30‑day supply of Amlodipine and Perindopril. Services included a GP consultation (CPT 99213), blood pressure monitoring with ECG (CPT 93000), and a basic metabolic panel (CPT 80048). Total billed amount was SGD 380.00, which was fully paid by credit card."
  }
}
```

### Expected Output (from contract)
```json
{
  "claim_reference_draft": "DRAFT-20250422-01102",
  "policy_no": "HIC-2023-00456",
  "claimant_name": "Lim Kai Xuan",
  "id_document_type": "nric",
  "id_document_no": "S8867890C",
  "date_of_birth": "1988-11-30",
  "claimant_relationship": "spouse",
  "claim_type": "outpatient",
  "incident_date": "2025-04-20",
  "claim_date": "2025-04-22",
  "claim_amount_requested": 380.0,
  "provider_name": "CityMed Family Clinic",
  "provider_registration": "PRV-CLIN-07734",
  "intake_accepted": true,
  "rejection_reason": null,
  "missing_documents": [],
  "intake_timestamp": "2025-04-22T10:15:00+08:00",
  "document_summary": {
    "total_billed_amount": 380.0,
    "itemised_charges": [
      {
        "description": "Consultation fee (GP)",
        "quantity": 1,
        "unit_price": 85.0
      },
      {
        "description": "Blood pressure monitoring + ECG",
        "quantity": 1,
        "unit_price": 60.0
      },
      {
        "description": "Basic metabolic panel (blood test)",
        "quantity": 1,
        "unit_price": 45.0
      },
      {
        "description": "Antihypertensive medications (30-day supply)",
        "quantity": 1,
        "unit_price": 190.0
      }
    ],
    "primary_diagnosis_icd10": "I10",
    "procedure_cpt_codes": [
      "99213",
      "93000",
      "80048"
    ],
    "symptom_onset_date": null,
    "admission_date": null,
    "discharge_date": null,
    "attending_physician": "Dr. Farhan Bin Riza",
    "physician_license_no": "MCR-67890F",
    "pre_authorisation_no": null,
    "provider_name_on_bill": "CityMed Family Clinic",
    "extraction_warnings": [],
    "summary_narrative": "Lim Kai Xuan, 36, visited CityMed Family Clinic on 20 Apr 2025 for essential hypertension (ICD-10 I10) management. No prior symptom onset date documented. Procedures included outpatient GP consultation (CPT 99213), ECG (CPT 93000), and basic metabolic panel (CPT 80048). Antihypertensive medications prescribed (30-day supply). Total billed SGD 380. No pre-authorisation required for outpatient claims."
  }
}
```

### Field-Level Comparison
| Status | Field | Actual | Expected | Note |
|:---:|:---|:---|:---|:---|
| ⏭️ | stage_1_intake._output.claim_reference_draft | DRAFT-20260520-10509 | DRAFT-20250422-01102 | Non-deterministic field skipped |
| ✅ | stage_1_intake._output.policy_no | HIC-2023-00456 | HIC-2023-00456 |  |
| ✅ | stage_1_intake._output.claimant_name | Lim Kai Xuan | Lim Kai Xuan |  |
| ✅ | stage_1_intake._output.id_document_type | nric | nric |  |
| ✅ | stage_1_intake._output.id_document_no | S8867890C | S8867890C |  |
| ✅ | stage_1_intake._output.date_of_birth | 1988-11-30 | 1988-11-30 |  |
| ✅ | stage_1_intake._output.claimant_relationship | spouse | spouse |  |
| ✅ | stage_1_intake._output.claim_type | outpatient | outpatient |  |
| ✅ | stage_1_intake._output.incident_date | 2025-04-20 | 2025-04-20 |  |
| ✅ | stage_1_intake._output.claim_date | 2025-04-22 | 2025-04-22 |  |
| ✅ | stage_1_intake._output.claim_amount_requested | 380.0 | 380.0 |  |
| ✅ | stage_1_intake._output.provider_name | CityMed Family Clinic | CityMed Family Clinic |  |
| ✅ | stage_1_intake._output.provider_registration | PRV-CLIN-07734 | PRV-CLIN-07734 |  |
| ✅ | stage_1_intake._output.intake_accepted | True | True |  |
| ✅ | stage_1_intake._output.rejection_reason | None | None |  |
| ⏭️ | stage_1_intake._output.intake_timestamp | 2026-05-20T02:09:50.023224+08:00 | 2025-04-22T10:15:00+08:00 | Non-deterministic field skipped |
| ✅ | stage_1_intake._output.document_summary.total_billed_amount | 380.0 | 380.0 |  |
| ❌ | stage_1_intake._output.document_summary.itemised_charges | [{'description': 'GP Consultation Fee', 'quantity': 1, 'unit_price': 85.0}, {'description': 'Blood Pressure Monitoring & | [{'description': 'Consultation fee (GP)', 'quantity': 1, 'unit_price': 85.0}, {'description': 'Blood pressure monitoring | List length mismatch: actual=5 expected=4 |
| ✅ | stage_1_intake._output.document_summary.primary_diagnosis_icd10 | I10 | I10 |  |
| ✅ | stage_1_intake._output.document_summary.procedure_cpt_codes[0] | 80048 | 80048 |  |
| ✅ | stage_1_intake._output.document_summary.procedure_cpt_codes[1] | 93000 | 93000 |  |
| ✅ | stage_1_intake._output.document_summary.procedure_cpt_codes[2] | 99213 | 99213 |  |
| ✅ | stage_1_intake._output.document_summary.symptom_onset_date | None | None |  |
| ✅ | stage_1_intake._output.document_summary.admission_date | None | None |  |
| ✅ | stage_1_intake._output.document_summary.discharge_date | None | None |  |
| ✅ | stage_1_intake._output.document_summary.attending_physician | Dr. Farhan Bin Riza | Dr. Farhan Bin Riza |  |
| ✅ | stage_1_intake._output.document_summary.physician_license_no | MCR-67890F | MCR-67890F |  |
| ✅ | stage_1_intake._output.document_summary.pre_authorisation_no | None | None |  |
| ✅ | stage_1_intake._output.document_summary.provider_name_on_bill | CityMed Family Clinic | CityMed Family Clinic |  |
| ⏭️ | stage_1_intake._output.document_summary.summary_narrative | Patient Lim Kai Xuan visited CityMed Family Clinic on 20 April 2025 for an outpatient consultation. Diagnosed with hyper | Lim Kai Xuan, 36, visited CityMed Family Clinic on 20 Apr 2025 for essential hypertension (ICD-10 I10) management. No pr | Non-deterministic field skipped |

---


## Stage 2 — Policy Verification

**Endpoint:** `POST /verification/process`  
**Status:** ✅ Verified  


### Request Payload (= Node 1 Output)
```json
{
  "claim_reference_draft": "DRAFT-20260520-10509",
  "policy_no": "HIC-2023-00456",
  "claimant_name": "Lim Kai Xuan",
  "id_document_type": "nric",
  "id_document_no": "S8867890C",
  "date_of_birth": "1988-11-30",
  "claimant_relationship": "spouse",
  "claim_type": "outpatient",
  "incident_date": "2025-04-20",
  "claim_date": "2025-04-22",
  "claim_amount_requested": 380.0,
  "provider_name": "CityMed Family Clinic",
  "provider_registration": "PRV-CLIN-07734",
  "intake_accepted": true,
  "rejection_reason": null,
  "missing_documents": [],
  "intake_timestamp": "2026-05-20T02:09:50.023224+08:00",
  "document_summary": {
    "total_billed_amount": 380.0,
    "itemised_charges": [
      {
        "description": "GP Consultation Fee",
        "quantity": 1,
        "unit_price": 85.0
      },
      {
        "description": "Blood Pressure Monitoring & ECG",
        "quantity": 1,
        "unit_price": 60.0
      },
      {
        "description": "Basic Metabolic Panel (Blood Test)",
        "quantity": 1,
        "unit_price": 45.0
      },
      {
        "description": "Amlodipine 5mg",
        "quantity": 1,
        "unit_price": 90.0
      },
      {
        "description": "Perindopril 4mg",
        "quantity": 1,
        "unit_price": 100.0
      }
    ],
    "primary_diagnosis_icd10": "I10",
    "procedure_cpt_codes": [
      "99213",
      "93000",
      "80048"
    ],
    "symptom_onset_date": null,
    "admission_date": null,
    "discharge_date": null,
    "attending_physician": "Dr. Farhan Bin Riza",
    "physician_license_no": "MCR-67890F",
    "pre_authorisation_no": null,
    "provider_name_on_bill": "CityMed Family Clinic",
    "extraction_warnings": [],
    "summary_narrative": "Patient Lim Kai Xuan visited CityMed Family Clinic on 20 April 2025 for an outpatient consultation. Diagnosed with hypertension, the physician prescribed a 30‑day supply of Amlodipine and Perindopril. Services included a GP consultation (CPT 99213), blood pressure monitoring with ECG (CPT 93000), and a basic metabolic panel (CPT 80048). Total billed amount was SGD 380.00, which was fully paid by credit card."
  }
}
```

### Actual API Response
```json
{
  "claim_reference_draft": "DRAFT-20260520-10509",
  "policy_no": "HIC-2023-00456",
  "claimant_name": "Lim Kai Xuan",
  "id_document_type": "nric",
  "id_document_no": "S8867890C",
  "date_of_birth": "1988-11-30",
  "claimant_relationship": "spouse",
  "claim_type": "outpatient",
  "incident_date": "2025-04-20",
  "claim_amount_requested": 380.0,
  "provider_name": "CityMed Family Clinic",
  "provider_registration": "PRV-CLIN-07734",
  "document_summary": {
    "total_billed_amount": 380.0,
    "itemised_charges": [
      {
        "description": "GP Consultation Fee",
        "quantity": 1,
        "unit_price": 85.0
      },
      {
        "description": "Blood Pressure Monitoring & ECG",
        "quantity": 1,
        "unit_price": 60.0
      },
      {
        "description": "Basic Metabolic Panel (Blood Test)",
        "quantity": 1,
        "unit_price": 45.0
      },
      {
        "description": "Amlodipine 5mg",
        "quantity": 1,
        "unit_price": 90.0
      },
      {
        "description": "Perindopril 4mg",
        "quantity": 1,
        "unit_price": 100.0
      }
    ],
    "primary_diagnosis_icd10": "I10",
    "procedure_cpt_codes": [
      "99213",
      "93000",
      "80048"
    ],
    "symptom_onset_date": null,
    "admission_date": null,
    "discharge_date": null,
    "attending_physician": "Dr. Farhan Bin Riza",
    "physician_license_no": "MCR-67890F",
    "pre_authorisation_no": null,
    "provider_name_on_bill": "CityMed Family Clinic",
    "extraction_warnings": [],
    "summary_narrative": "Patient Lim Kai Xuan visited CityMed Family Clinic on 20 April 2025 for an outpatient consultation. Diagnosed with hypertension, the physician prescribed a 30‑day supply of Amlodipine and Perindopril. Services included a GP consultation (CPT 99213), blood pressure monitoring with ECG (CPT 93000), and a basic metabolic panel (CPT 80048). Total billed amount was SGD 380.00, which was fully paid by credit card."
  },
  "policy_verified": true,
  "verification_failure": null,
  "policy_start_date": "2023-06-01",
  "policy_expiry_date": "2025-05-31",
  "policy_product_code": "COMP-HEALTH-SILVER",
  "premium_payment_mode": "monthly",
  "dependent_verified": true,
  "verification_timestamp": "2026-05-19T18:09:50.056118Z"
}
```

### Expected Output (from contract)
```json
{
  "claim_reference_draft": "DRAFT-20250422-01102",
  "policy_no": "HIC-2023-00456",
  "claimant_name": "Lim Kai Xuan",
  "id_document_type": "nric",
  "id_document_no": "S8867890C",
  "date_of_birth": "1988-11-30",
  "claimant_relationship": "spouse",
  "claim_type": "outpatient",
  "incident_date": "2025-04-20",
  "claim_amount_requested": 380.0,
  "provider_name": "CityMed Family Clinic",
  "provider_registration": "PRV-CLIN-07734",
  "document_summary": {
    "total_billed_amount": 380.0,
    "itemised_charges": [
      {
        "description": "Consultation fee (GP)",
        "quantity": 1,
        "unit_price": 85.0
      },
      {
        "description": "Blood pressure monitoring + ECG",
        "quantity": 1,
        "unit_price": 60.0
      },
      {
        "description": "Basic metabolic panel (blood test)",
        "quantity": 1,
        "unit_price": 45.0
      },
      {
        "description": "Antihypertensive medications (30-day supply)",
        "quantity": 1,
        "unit_price": 190.0
      }
    ],
    "primary_diagnosis_icd10": "I10",
    "procedure_cpt_codes": [
      "99213",
      "93000",
      "80048"
    ],
    "symptom_onset_date": null,
    "admission_date": null,
    "discharge_date": null,
    "attending_physician": "Dr. Farhan Bin Riza",
    "physician_license_no": "MCR-67890F",
    "pre_authorisation_no": null,
    "provider_name_on_bill": "CityMed Family Clinic",
    "extraction_warnings": [],
    "summary_narrative": "Lim Kai Xuan, 36, visited CityMed Family Clinic on 20 Apr 2025 for essential hypertension (ICD-10 I10) management. No prior symptom onset date documented. Procedures included outpatient GP consultation (CPT 99213), ECG (CPT 93000), and basic metabolic panel (CPT 80048). Antihypertensive medications prescribed (30-day supply). Total billed SGD 380. No pre-authorisation required for outpatient claims."
  },
  "policy_verified": true,
  "verification_failure": null,
  "policy_start_date": "2023-06-01",
  "policy_expiry_date": "2025-05-31",
  "policy_product_code": "COMP-HEALTH-SILVER",
  "premium_payment_mode": "monthly",
  "dependent_verified": true,
  "verification_timestamp": "2025-04-22T10:16:00+08:00"
}
```

### Field-Level Comparison
| Status | Field | Actual | Expected | Note |
|:---:|:---|:---|:---|:---|
| ⏭️ | stage_2_verification._output.claim_reference_draft | DRAFT-20260520-10509 | DRAFT-20250422-01102 | Non-deterministic field skipped |
| ✅ | stage_2_verification._output.policy_no | HIC-2023-00456 | HIC-2023-00456 |  |
| ✅ | stage_2_verification._output.claimant_name | Lim Kai Xuan | Lim Kai Xuan |  |
| ✅ | stage_2_verification._output.id_document_type | nric | nric |  |
| ✅ | stage_2_verification._output.id_document_no | S8867890C | S8867890C |  |
| ✅ | stage_2_verification._output.date_of_birth | 1988-11-30 | 1988-11-30 |  |
| ✅ | stage_2_verification._output.claimant_relationship | spouse | spouse |  |
| ✅ | stage_2_verification._output.claim_type | outpatient | outpatient |  |
| ✅ | stage_2_verification._output.incident_date | 2025-04-20 | 2025-04-20 |  |
| ✅ | stage_2_verification._output.claim_amount_requested | 380.0 | 380.0 |  |
| ✅ | stage_2_verification._output.provider_name | CityMed Family Clinic | CityMed Family Clinic |  |
| ✅ | stage_2_verification._output.provider_registration | PRV-CLIN-07734 | PRV-CLIN-07734 |  |
| ✅ | stage_2_verification._output.document_summary.total_billed_amount | 380.0 | 380.0 |  |
| ❌ | stage_2_verification._output.document_summary.itemised_charges | [{'description': 'GP Consultation Fee', 'quantity': 1, 'unit_price': 85.0}, {'description': 'Blood Pressure Monitoring & | [{'description': 'Consultation fee (GP)', 'quantity': 1, 'unit_price': 85.0}, {'description': 'Blood pressure monitoring | List length mismatch: actual=5 expected=4 |
| ✅ | stage_2_verification._output.document_summary.primary_diagnosis_icd10 | I10 | I10 |  |
| ✅ | stage_2_verification._output.document_summary.procedure_cpt_codes[0] | 80048 | 80048 |  |
| ✅ | stage_2_verification._output.document_summary.procedure_cpt_codes[1] | 93000 | 93000 |  |
| ✅ | stage_2_verification._output.document_summary.procedure_cpt_codes[2] | 99213 | 99213 |  |
| ✅ | stage_2_verification._output.document_summary.symptom_onset_date | None | None |  |
| ✅ | stage_2_verification._output.document_summary.admission_date | None | None |  |
| ✅ | stage_2_verification._output.document_summary.discharge_date | None | None |  |
| ✅ | stage_2_verification._output.document_summary.attending_physician | Dr. Farhan Bin Riza | Dr. Farhan Bin Riza |  |
| ✅ | stage_2_verification._output.document_summary.physician_license_no | MCR-67890F | MCR-67890F |  |
| ✅ | stage_2_verification._output.document_summary.pre_authorisation_no | None | None |  |
| ✅ | stage_2_verification._output.document_summary.provider_name_on_bill | CityMed Family Clinic | CityMed Family Clinic |  |
| ⏭️ | stage_2_verification._output.document_summary.summary_narrative | Patient Lim Kai Xuan visited CityMed Family Clinic on 20 April 2025 for an outpatient consultation. Diagnosed with hyper | Lim Kai Xuan, 36, visited CityMed Family Clinic on 20 Apr 2025 for essential hypertension (ICD-10 I10) management. No pr | Non-deterministic field skipped |
| ✅ | stage_2_verification._output.policy_verified | True | True |  |
| ✅ | stage_2_verification._output.verification_failure | None | None |  |
| ✅ | stage_2_verification._output.policy_start_date | 2023-06-01 | 2023-06-01 |  |
| ✅ | stage_2_verification._output.policy_expiry_date | 2025-05-31 | 2025-05-31 |  |
| ✅ | stage_2_verification._output.policy_product_code | COMP-HEALTH-SILVER | COMP-HEALTH-SILVER |  |
| ✅ | stage_2_verification._output.premium_payment_mode | monthly | monthly |  |
| ✅ | stage_2_verification._output.dependent_verified | True | True |  |
| ⏭️ | stage_2_verification._output.verification_timestamp | 2026-05-19T18:09:50.056118Z | 2025-04-22T10:16:00+08:00 | Non-deterministic field skipped |

---


## Stage 3 — Eligibility Check

**Endpoint:** `POST /eligibility/process`  
**Status:** ✅ Eligible  


### Request Payload (= Node 2 Output)
```json
{
  "claim_reference_draft": "DRAFT-20260520-10509",
  "policy_no": "HIC-2023-00456",
  "claimant_name": "Lim Kai Xuan",
  "id_document_type": "nric",
  "id_document_no": "S8867890C",
  "date_of_birth": "1988-11-30",
  "claimant_relationship": "spouse",
  "claim_type": "outpatient",
  "incident_date": "2025-04-20",
  "claim_amount_requested": 380.0,
  "provider_name": "CityMed Family Clinic",
  "provider_registration": "PRV-CLIN-07734",
  "document_summary": {
    "total_billed_amount": 380.0,
    "itemised_charges": [
      {
        "description": "GP Consultation Fee",
        "quantity": 1,
        "unit_price": 85.0
      },
      {
        "description": "Blood Pressure Monitoring & ECG",
        "quantity": 1,
        "unit_price": 60.0
      },
      {
        "description": "Basic Metabolic Panel (Blood Test)",
        "quantity": 1,
        "unit_price": 45.0
      },
      {
        "description": "Amlodipine 5mg",
        "quantity": 1,
        "unit_price": 90.0
      },
      {
        "description": "Perindopril 4mg",
        "quantity": 1,
        "unit_price": 100.0
      }
    ],
    "primary_diagnosis_icd10": "I10",
    "procedure_cpt_codes": [
      "99213",
      "93000",
      "80048"
    ],
    "symptom_onset_date": null,
    "admission_date": null,
    "discharge_date": null,
    "attending_physician": "Dr. Farhan Bin Riza",
    "physician_license_no": "MCR-67890F",
    "pre_authorisation_no": null,
    "provider_name_on_bill": "CityMed Family Clinic",
    "extraction_warnings": [],
    "summary_narrative": "Patient Lim Kai Xuan visited CityMed Family Clinic on 20 April 2025 for an outpatient consultation. Diagnosed with hypertension, the physician prescribed a 30‑day supply of Amlodipine and Perindopril. Services included a GP consultation (CPT 99213), blood pressure monitoring with ECG (CPT 93000), and a basic metabolic panel (CPT 80048). Total billed amount was SGD 380.00, which was fully paid by credit card."
  },
  "policy_verified": true,
  "verification_failure": null,
  "policy_start_date": "2023-06-01",
  "policy_expiry_date": "2025-05-31",
  "policy_product_code": "COMP-HEALTH-SILVER",
  "premium_payment_mode": "monthly",
  "dependent_verified": true,
  "verification_timestamp": "2026-05-19T18:09:50.056118Z"
}
```

### Actual API Response
```json
{
  "claim_reference_draft": "DRAFT-20260520-10509",
  "policy_no": "HIC-2023-00456",
  "claimant_name": "Lim Kai Xuan",
  "claim_type": "outpatient",
  "incident_date": "2025-04-20",
  "claim_amount_requested": 380.0,
  "policy_product_code": "COMP-HEALTH-SILVER",
  "provider_name": "CityMed Family Clinic",
  "provider_registration": "PRV-CLIN-07734",
  "document_summary": {
    "total_billed_amount": 380.0,
    "itemised_charges": [
      {
        "description": "GP Consultation Fee",
        "quantity": 1,
        "unit_price": 85.0
      },
      {
        "description": "Blood Pressure Monitoring & ECG",
        "quantity": 1,
        "unit_price": 60.0
      },
      {
        "description": "Basic Metabolic Panel (Blood Test)",
        "quantity": 1,
        "unit_price": 45.0
      },
      {
        "description": "Amlodipine 5mg",
        "quantity": 1,
        "unit_price": 90.0
      },
      {
        "description": "Perindopril 4mg",
        "quantity": 1,
        "unit_price": 100.0
      }
    ],
    "primary_diagnosis_icd10": "I10",
    "procedure_cpt_codes": [
      "99213",
      "93000",
      "80048"
    ],
    "symptom_onset_date": null,
    "admission_date": null,
    "discharge_date": null,
    "attending_physician": "Dr. Farhan Bin Riza",
    "physician_license_no": "MCR-67890F",
    "pre_authorisation_no": null,
    "provider_name_on_bill": "CityMed Family Clinic",
    "extraction_warnings": [],
    "summary_narrative": "Patient Lim Kai Xuan visited CityMed Family Clinic on 20 April 2025 for an outpatient consultation. Diagnosed with hypertension, the physician prescribed a 30‑day supply of Amlodipine and Perindopril. Services included a GP consultation (CPT 99213), blood pressure monitoring with ECG (CPT 93000), and a basic metabolic panel (CPT 80048). Total billed amount was SGD 380.00, which was fully paid by credit card."
  },
  "eligible": true,
  "eligibility_failure_reason": null,
  "waiting_period_satisfied": true,
  "waiting_period_days": 30,
  "waiting_period_basis": "incident_date",
  "annual_limit": 5000.0,
  "annual_utilised": 180.0,
  "annual_limit_remaining": 4820.0,
  "per_claim_limit": 500.0,
  "claimable_ceiling": 380.0,
  "exclusions_triggered": [],
  "eligibility_rationale": "Outpatient covered. 30‑day waiting period satisfied. Claim SGD 380 ≤ per-claim limit SGD 500 and ≤ remaining annual limit SGD 4820. Lifetime limit SGD 600,000 not exceeded.",
  "eligibility_timestamp": "2026-05-19T18:09:50.079418Z"
}
```

### Expected Output (from contract)
```json
{
  "claim_reference_draft": "DRAFT-20250422-01102",
  "policy_no": "HIC-2023-00456",
  "claimant_name": "Lim Kai Xuan",
  "claim_type": "outpatient",
  "incident_date": "2025-04-20",
  "claim_amount_requested": 380.0,
  "policy_product_code": "COMP-HEALTH-SILVER",
  "provider_name": "CityMed Family Clinic",
  "provider_registration": "PRV-CLIN-07734",
  "document_summary": {
    "total_billed_amount": 380.0,
    "itemised_charges": [
      {
        "description": "Consultation fee (GP)",
        "quantity": 1,
        "unit_price": 85.0
      },
      {
        "description": "Blood pressure monitoring + ECG",
        "quantity": 1,
        "unit_price": 60.0
      },
      {
        "description": "Basic metabolic panel (blood test)",
        "quantity": 1,
        "unit_price": 45.0
      },
      {
        "description": "Antihypertensive medications (30-day supply)",
        "quantity": 1,
        "unit_price": 190.0
      }
    ],
    "primary_diagnosis_icd10": "I10",
    "procedure_cpt_codes": [
      "99213",
      "93000",
      "80048"
    ],
    "symptom_onset_date": null,
    "admission_date": null,
    "discharge_date": null,
    "attending_physician": "Dr. Farhan Bin Riza",
    "physician_license_no": "MCR-67890F",
    "pre_authorisation_no": null,
    "provider_name_on_bill": "CityMed Family Clinic",
    "extraction_warnings": [],
    "summary_narrative": "Lim Kai Xuan, 36, visited CityMed Family Clinic on 20 Apr 2025 for essential hypertension (ICD-10 I10) management. No prior symptom onset date documented. Procedures included outpatient GP consultation (CPT 99213), ECG (CPT 93000), and basic metabolic panel (CPT 80048). Antihypertensive medications prescribed (30-day supply). Total billed SGD 380. No pre-authorisation required for outpatient claims."
  },
  "eligible": true,
  "eligibility_failure_reason": null,
  "waiting_period_satisfied": true,
  "waiting_period_days": 30,
  "waiting_period_basis": "incident_date",
  "annual_limit": 5000.0,
  "annual_utilised": 180.0,
  "annual_limit_remaining": 4820.0,
  "per_claim_limit": 500.0,
  "claimable_ceiling": 380.0,
  "exclusions_triggered": [],
  "eligibility_rationale": "Outpatient is covered under COMP-HEALTH-SILVER with 30-day waiting period. Policy started 1 Jun 2023; incident 20 Apr 2025 is 689 days later — waiting period satisfied. I10 (hypertension) triggers no exclusion. Annual limit SGD 5,000 with SGD 180 utilised, SGD 4,820 remaining. Per-claim limit SGD 500 exceeds claim amount SGD 380. Claimable ceiling SGD 380.",
  "eligibility_timestamp": "2025-04-22T10:17:00+08:00"
}
```

### Field-Level Comparison
| Status | Field | Actual | Expected | Note |
|:---:|:---|:---|:---|:---|
| ⏭️ | stage_3_eligibility._output.claim_reference_draft | DRAFT-20260520-10509 | DRAFT-20250422-01102 | Non-deterministic field skipped |
| ✅ | stage_3_eligibility._output.policy_no | HIC-2023-00456 | HIC-2023-00456 |  |
| ✅ | stage_3_eligibility._output.claimant_name | Lim Kai Xuan | Lim Kai Xuan |  |
| ✅ | stage_3_eligibility._output.claim_type | outpatient | outpatient |  |
| ✅ | stage_3_eligibility._output.incident_date | 2025-04-20 | 2025-04-20 |  |
| ✅ | stage_3_eligibility._output.claim_amount_requested | 380.0 | 380.0 |  |
| ✅ | stage_3_eligibility._output.policy_product_code | COMP-HEALTH-SILVER | COMP-HEALTH-SILVER |  |
| ✅ | stage_3_eligibility._output.provider_name | CityMed Family Clinic | CityMed Family Clinic |  |
| ✅ | stage_3_eligibility._output.provider_registration | PRV-CLIN-07734 | PRV-CLIN-07734 |  |
| ✅ | stage_3_eligibility._output.document_summary.total_billed_amount | 380.0 | 380.0 |  |
| ❌ | stage_3_eligibility._output.document_summary.itemised_charges | [{'description': 'GP Consultation Fee', 'quantity': 1, 'unit_price': 85.0}, {'description': 'Blood Pressure Monitoring & | [{'description': 'Consultation fee (GP)', 'quantity': 1, 'unit_price': 85.0}, {'description': 'Blood pressure monitoring | List length mismatch: actual=5 expected=4 |
| ✅ | stage_3_eligibility._output.document_summary.primary_diagnosis_icd10 | I10 | I10 |  |
| ✅ | stage_3_eligibility._output.document_summary.procedure_cpt_codes[0] | 80048 | 80048 |  |
| ✅ | stage_3_eligibility._output.document_summary.procedure_cpt_codes[1] | 93000 | 93000 |  |
| ✅ | stage_3_eligibility._output.document_summary.procedure_cpt_codes[2] | 99213 | 99213 |  |
| ✅ | stage_3_eligibility._output.document_summary.symptom_onset_date | None | None |  |
| ✅ | stage_3_eligibility._output.document_summary.admission_date | None | None |  |
| ✅ | stage_3_eligibility._output.document_summary.discharge_date | None | None |  |
| ✅ | stage_3_eligibility._output.document_summary.attending_physician | Dr. Farhan Bin Riza | Dr. Farhan Bin Riza |  |
| ✅ | stage_3_eligibility._output.document_summary.physician_license_no | MCR-67890F | MCR-67890F |  |
| ✅ | stage_3_eligibility._output.document_summary.pre_authorisation_no | None | None |  |
| ✅ | stage_3_eligibility._output.document_summary.provider_name_on_bill | CityMed Family Clinic | CityMed Family Clinic |  |
| ⏭️ | stage_3_eligibility._output.document_summary.summary_narrative | Patient Lim Kai Xuan visited CityMed Family Clinic on 20 April 2025 for an outpatient consultation. Diagnosed with hyper | Lim Kai Xuan, 36, visited CityMed Family Clinic on 20 Apr 2025 for essential hypertension (ICD-10 I10) management. No pr | Non-deterministic field skipped |
| ✅ | stage_3_eligibility._output.eligible | True | True |  |
| ✅ | stage_3_eligibility._output.eligibility_failure_reason | None | None |  |
| ✅ | stage_3_eligibility._output.waiting_period_satisfied | True | True |  |
| ✅ | stage_3_eligibility._output.waiting_period_days | 30 | 30 |  |
| ✅ | stage_3_eligibility._output.waiting_period_basis | incident_date | incident_date |  |
| ✅ | stage_3_eligibility._output.annual_limit | 5000.0 | 5000.0 |  |
| ✅ | stage_3_eligibility._output.annual_utilised | 180.0 | 180.0 |  |
| ✅ | stage_3_eligibility._output.annual_limit_remaining | 4820.0 | 4820.0 |  |
| ✅ | stage_3_eligibility._output.per_claim_limit | 500.0 | 500.0 |  |
| ✅ | stage_3_eligibility._output.claimable_ceiling | 380.0 | 380.0 |  |
| ⏭️ | stage_3_eligibility._output.eligibility_rationale | Outpatient covered. 30‑day waiting period satisfied. Claim SGD 380 ≤ per-claim limit SGD 500 and ≤ remaining annual limi | Outpatient is covered under COMP-HEALTH-SILVER with 30-day waiting period. Policy started 1 Jun 2023; incident 20 Apr 20 | Non-deterministic field skipped |
| ⏭️ | stage_3_eligibility._output.eligibility_timestamp | 2026-05-19T18:09:50.079418Z | 2025-04-22T10:17:00+08:00 | Non-deterministic field skipped |

---


## Stage 4 — Medical Review

**Endpoint:** `POST /medical/process`  
**Status:** ❌ Failed / Error  


### Request Payload (= Node 3 Output)
```json
{
  "claim_reference_draft": "DRAFT-20260520-10509",
  "policy_no": "HIC-2023-00456",
  "claimant_name": "Lim Kai Xuan",
  "claim_type": "outpatient",
  "incident_date": "2025-04-20",
  "claim_amount_requested": 380.0,
  "policy_product_code": "COMP-HEALTH-SILVER",
  "provider_name": "CityMed Family Clinic",
  "provider_registration": "PRV-CLIN-07734",
  "document_summary": {
    "total_billed_amount": 380.0,
    "itemised_charges": [
      {
        "description": "GP Consultation Fee",
        "quantity": 1,
        "unit_price": 85.0
      },
      {
        "description": "Blood Pressure Monitoring & ECG",
        "quantity": 1,
        "unit_price": 60.0
      },
      {
        "description": "Basic Metabolic Panel (Blood Test)",
        "quantity": 1,
        "unit_price": 45.0
      },
      {
        "description": "Amlodipine 5mg",
        "quantity": 1,
        "unit_price": 90.0
      },
      {
        "description": "Perindopril 4mg",
        "quantity": 1,
        "unit_price": 100.0
      }
    ],
    "primary_diagnosis_icd10": "I10",
    "procedure_cpt_codes": [
      "99213",
      "93000",
      "80048"
    ],
    "symptom_onset_date": null,
    "admission_date": null,
    "discharge_date": null,
    "attending_physician": "Dr. Farhan Bin Riza",
    "physician_license_no": "MCR-67890F",
    "pre_authorisation_no": null,
    "provider_name_on_bill": "CityMed Family Clinic",
    "extraction_warnings": [],
    "summary_narrative": "Patient Lim Kai Xuan visited CityMed Family Clinic on 20 April 2025 for an outpatient consultation. Diagnosed with hypertension, the physician prescribed a 30‑day supply of Amlodipine and Perindopril. Services included a GP consultation (CPT 99213), blood pressure monitoring with ECG (CPT 93000), and a basic metabolic panel (CPT 80048). Total billed amount was SGD 380.00, which was fully paid by credit card."
  },
  "eligible": true,
  "eligibility_failure_reason": null,
  "waiting_period_satisfied": true,
  "waiting_period_days": 30,
  "waiting_period_basis": "incident_date",
  "annual_limit": 5000.0,
  "annual_utilised": 180.0,
  "annual_limit_remaining": 4820.0,
  "per_claim_limit": 500.0,
  "claimable_ceiling": 380.0,
  "exclusions_triggered": [],
  "eligibility_rationale": "Outpatient covered. 30‑day waiting period satisfied. Claim SGD 380 ≤ per-claim limit SGD 500 and ≤ remaining annual limit SGD 4820. Lifetime limit SGD 600,000 not exceeded.",
  "eligibility_timestamp": "2026-05-19T18:09:50.079418Z"
}
```

### Actual API Response
```json
{
  "claim_reference_draft": "DRAFT-20260520-10509",
  "policy_no": "HIC-2023-00456",
  "claimant_name": "Lim Kai Xuan",
  "claim_type": "outpatient",
  "incident_date": "2025-04-20",
  "claim_amount_requested": 380.0,
  "claimable_ceiling": 380.0,
  "policy_product_code": "COMP-HEALTH-SILVER",
  "provider_registration": "PRV-CLIN-07734",
  "document_summary": {
    "total_billed_amount": 380.0,
    "itemised_charges": [
      {
        "description": "GP Consultation Fee",
        "quantity": 1,
        "unit_price": 85.0
      },
      {
        "description": "Blood Pressure Monitoring & ECG",
        "quantity": 1,
        "unit_price": 60.0
      },
      {
        "description": "Basic Metabolic Panel (Blood Test)",
        "quantity": 1,
        "unit_price": 45.0
      },
      {
        "description": "Amlodipine 5mg",
        "quantity": 1,
        "unit_price": 90.0
      },
      {
        "description": "Perindopril 4mg",
        "quantity": 1,
        "unit_price": 100.0
      }
    ],
    "primary_diagnosis_icd10": "I10",
    "procedure_cpt_codes": [
      "99213",
      "93000",
      "80048"
    ],
    "symptom_onset_date": null,
    "admission_date": null,
    "discharge_date": null,
    "attending_physician": "Dr. Farhan Bin Riza",
    "physician_license_no": "MCR-67890F",
    "pre_authorisation_no": null,
    "provider_name_on_bill": "CityMed Family Clinic",
    "extraction_warnings": [],
    "summary_narrative": "Patient Lim Kai Xuan visited CityMed Family Clinic on 20 April 2025 for an outpatient consultation. Diagnosed with hypertension, the physician prescribed a 30‑day supply of Amlodipine and Perindopril. Services included a GP consultation (CPT 99213), blood pressure monitoring with ECG (CPT 93000), and a basic metabolic panel (CPT 80048). Total billed amount was SGD 380.00, which was fully paid by credit card."
  },
  "medical_review_passed": false,
  "review_failure_reason": "CPT_ICD10_MISMATCH",
  "non_panel_flag": true,
  "accreditation_claim": "Provider not found in MOH accredited provider registry as of check date 2026-05-19.",
  "physician_licence_claim": "Physician licence verified with Singapore Medical Council registry as active until 2027-08-31 as of check date 2026-05-19.",
  "coding_assessment": [
    {
      "cpt_code": "99213",
      "valid": true,
      "plausible": true,
      "reasoning": "Office/outpatient visit established patient moderate complexity (CMS PFS 2024) is clinically appropriate for hypertension follow-up."
    },
    {
      "cpt_code": "93000",
      "valid": true,
      "plausible": false,
      "reasoning": "Electrocardiogram routine (CMS PFS 2024) is not standard of care for uncomplicated hypertension without cardiac symptoms."
    },
    {
      "cpt_code": "80048",
      "valid": true,
      "plausible": true,
      "reasoning": "Basic metabolic panel (CMS PFS 2024) is clinically indicated for hypertension monitoring to assess renal function and electrolytes."
    }
  ],
  "pre_auth_verified": true,
  "length_of_stay": null,
  "rps_benchmark": 190.0,
  "bill_variance_pct": 100.0,
  "medical_necessity_confirmed": false,
  "medical_flags": [
    "NON_PANEL_PROVIDER",
    "BILL_EXCEEDS_BENCHMARK"
  ],
  "medical_review_notes": "Provider is non-panel, ECG (93000) is not clinically necessary for routine hypertension without cardiac symptoms, and total billed SGD 380 exceeds RPS benchmark SGD 190. Medical necessity partially confirmed for consultation (99213) and metabolic panel (80048), but ECG lacks clinical justification.",
  "review_timestamp": "2026-05-19T18:09:52.189248Z"
}
```

### Expected Output (from contract)
```json
{
  "claim_reference_draft": "DRAFT-20250422-01102",
  "policy_no": "HIC-2023-00456",
  "claimant_name": "Lim Kai Xuan",
  "claim_type": "outpatient",
  "incident_date": "2025-04-20",
  "claim_amount_requested": 380.0,
  "claimable_ceiling": 380.0,
  "policy_product_code": "COMP-HEALTH-SILVER",
  "provider_registration": "PRV-CLIN-07734",
  "document_summary": {
    "total_billed_amount": 380.0,
    "itemised_charges": [
      {
        "description": "Consultation fee (GP)",
        "quantity": 1,
        "unit_price": 85.0
      },
      {
        "description": "Blood pressure monitoring + ECG",
        "quantity": 1,
        "unit_price": 60.0
      },
      {
        "description": "Basic metabolic panel (blood test)",
        "quantity": 1,
        "unit_price": 45.0
      },
      {
        "description": "Antihypertensive medications (30-day supply)",
        "quantity": 1,
        "unit_price": 190.0
      }
    ],
    "primary_diagnosis_icd10": "I10",
    "procedure_cpt_codes": [
      "99213",
      "93000",
      "80048"
    ],
    "symptom_onset_date": null,
    "admission_date": null,
    "discharge_date": null,
    "attending_physician": "Dr. Farhan Bin Riza",
    "physician_license_no": "MCR-67890F",
    "pre_authorisation_no": null,
    "provider_name_on_bill": "CityMed Family Clinic",
    "extraction_warnings": [],
    "summary_narrative": "Lim Kai Xuan, 36, visited CityMed Family Clinic on 20 Apr 2025 for essential hypertension (ICD-10 I10) management. No prior symptom onset date documented. Procedures included outpatient GP consultation (CPT 99213), ECG (CPT 93000), and basic metabolic panel (CPT 80048). Antihypertensive medications prescribed (30-day supply). Total billed SGD 380. No pre-authorisation required for outpatient claims."
  },
  "medical_review_passed": true,
  "review_failure_reason": null,
  "non_panel_flag": true,
  "accreditation_claim": "CityMed Family Clinic (PRV-CLIN-07734) was not found in the MOH accredited panel provider list as of 2025-04-22. Provider is a non-panel private clinic. Source: MOH Healthcare Institution Registry.",
  "physician_licence_claim": "Dr. Farhan Bin Riza (MCR-67890F) holds a valid and active medical licence under General Practice, verified at SMC Full Medical Register on 2025-04-22. Valid through 2027-08-31.",
  "coding_assessment": [
    {
      "cpt_code": "99213",
      "valid": true,
      "plausible": true,
      "reasoning": "Standard GP consultation code, plausible for I10 hypertension management."
    },
    {
      "cpt_code": "93000",
      "valid": true,
      "plausible": true,
      "reasoning": "ECG is standard for hypertension cardiac monitoring — plausible for I10."
    },
    {
      "cpt_code": "80048",
      "valid": true,
      "plausible": true,
      "reasoning": "Basic metabolic panel monitors renal and electrolyte status in hypertension — plausible for I10."
    }
  ],
  "pre_auth_verified": true,
  "length_of_stay": null,
  "rps_benchmark": 190.0,
  "bill_variance_pct": 100.0,
  "medical_necessity_confirmed": true,
  "medical_flags": [
    "BILL_EXCEEDS_BENCHMARK",
    "NON_PANEL_PROVIDER"
  ],
  "medical_review_notes": "Non-panel GP clinic CityMed (PRV-CLIN-07734) — confirmed not on MOH panel. Dr. Farhan Bin Riza SMC licence active. CPT 99213, 93000, 80048 all clinically plausible for I10 hypertension. Bill SGD 380 is 100% above RPS benchmark SGD 190 — BILL_EXCEEDS_BENCHMARK flagged. Medical necessity confirmed. NON_PANEL_PROVIDER applies.",
  "review_timestamp": "2025-04-22T10:18:30+08:00"
}
```

### Field-Level Comparison
| Status | Field | Actual | Expected | Note |
|:---:|:---|:---|:---|:---|
| ⏭️ | stage_4_medical_review._output.claim_reference_draft | DRAFT-20260520-10509 | DRAFT-20250422-01102 | Non-deterministic field skipped |
| ✅ | stage_4_medical_review._output.policy_no | HIC-2023-00456 | HIC-2023-00456 |  |
| ✅ | stage_4_medical_review._output.claimant_name | Lim Kai Xuan | Lim Kai Xuan |  |
| ✅ | stage_4_medical_review._output.claim_type | outpatient | outpatient |  |
| ✅ | stage_4_medical_review._output.incident_date | 2025-04-20 | 2025-04-20 |  |
| ✅ | stage_4_medical_review._output.claim_amount_requested | 380.0 | 380.0 |  |
| ✅ | stage_4_medical_review._output.claimable_ceiling | 380.0 | 380.0 |  |
| ✅ | stage_4_medical_review._output.policy_product_code | COMP-HEALTH-SILVER | COMP-HEALTH-SILVER |  |
| ✅ | stage_4_medical_review._output.provider_registration | PRV-CLIN-07734 | PRV-CLIN-07734 |  |
| ✅ | stage_4_medical_review._output.document_summary.total_billed_amount | 380.0 | 380.0 |  |
| ❌ | stage_4_medical_review._output.document_summary.itemised_charges | [{'description': 'GP Consultation Fee', 'quantity': 1, 'unit_price': 85.0}, {'description': 'Blood Pressure Monitoring & | [{'description': 'Consultation fee (GP)', 'quantity': 1, 'unit_price': 85.0}, {'description': 'Blood pressure monitoring | List length mismatch: actual=5 expected=4 |
| ✅ | stage_4_medical_review._output.document_summary.primary_diagnosis_icd10 | I10 | I10 |  |
| ✅ | stage_4_medical_review._output.document_summary.procedure_cpt_codes[0] | 80048 | 80048 |  |
| ✅ | stage_4_medical_review._output.document_summary.procedure_cpt_codes[1] | 93000 | 93000 |  |
| ✅ | stage_4_medical_review._output.document_summary.procedure_cpt_codes[2] | 99213 | 99213 |  |
| ✅ | stage_4_medical_review._output.document_summary.symptom_onset_date | None | None |  |
| ✅ | stage_4_medical_review._output.document_summary.admission_date | None | None |  |
| ✅ | stage_4_medical_review._output.document_summary.discharge_date | None | None |  |
| ✅ | stage_4_medical_review._output.document_summary.attending_physician | Dr. Farhan Bin Riza | Dr. Farhan Bin Riza |  |
| ✅ | stage_4_medical_review._output.document_summary.physician_license_no | MCR-67890F | MCR-67890F |  |
| ✅ | stage_4_medical_review._output.document_summary.pre_authorisation_no | None | None |  |
| ✅ | stage_4_medical_review._output.document_summary.provider_name_on_bill | CityMed Family Clinic | CityMed Family Clinic |  |
| ⏭️ | stage_4_medical_review._output.document_summary.summary_narrative | Patient Lim Kai Xuan visited CityMed Family Clinic on 20 April 2025 for an outpatient consultation. Diagnosed with hyper | Lim Kai Xuan, 36, visited CityMed Family Clinic on 20 Apr 2025 for essential hypertension (ICD-10 I10) management. No pr | Non-deterministic field skipped |
| ❌ | stage_4_medical_review._output.medical_review_passed | False | True | Value mismatch |
| ❌ | stage_4_medical_review._output.review_failure_reason | CPT_ICD10_MISMATCH | None | Value mismatch |
| ✅ | stage_4_medical_review._output.non_panel_flag | True | True |  |
| ⏭️ | stage_4_medical_review._output.accreditation_claim | Provider not found in MOH accredited provider registry as of check date 2026-05-19. | CityMed Family Clinic (PRV-CLIN-07734) was not found in the MOH accredited panel provider list as of 2025-04-22. Provide | Non-deterministic field skipped |
| ⏭️ | stage_4_medical_review._output.physician_licence_claim | Physician licence verified with Singapore Medical Council registry as active until 2027-08-31 as of check date 2026-05-1 | Dr. Farhan Bin Riza (MCR-67890F) holds a valid and active medical licence under General Practice, verified at SMC Full M | Non-deterministic field skipped |
| ✅ | stage_4_medical_review._output.coding_assessment[0].cpt_code | 80048 | 80048 |  |
| ✅ | stage_4_medical_review._output.coding_assessment[0].valid | True | True |  |
| ✅ | stage_4_medical_review._output.coding_assessment[0].plausible | True | True |  |
| ⏭️ | stage_4_medical_review._output.coding_assessment[0].reasoning | Basic metabolic panel (CMS PFS 2024) is clinically indicated for hypertension monitoring to assess renal function and el | Basic metabolic panel monitors renal and electrolyte status in hypertension — plausible for I10. | Non-deterministic field skipped |
| ✅ | stage_4_medical_review._output.coding_assessment[1].cpt_code | 93000 | 93000 |  |
| ✅ | stage_4_medical_review._output.coding_assessment[1].valid | True | True |  |
| ❌ | stage_4_medical_review._output.coding_assessment[1].plausible | False | True | Value mismatch |
| ⏭️ | stage_4_medical_review._output.coding_assessment[1].reasoning | Electrocardiogram routine (CMS PFS 2024) is not standard of care for uncomplicated hypertension without cardiac symptoms | ECG is standard for hypertension cardiac monitoring — plausible for I10. | Non-deterministic field skipped |
| ✅ | stage_4_medical_review._output.coding_assessment[2].cpt_code | 99213 | 99213 |  |
| ✅ | stage_4_medical_review._output.coding_assessment[2].valid | True | True |  |
| ✅ | stage_4_medical_review._output.coding_assessment[2].plausible | True | True |  |
| ⏭️ | stage_4_medical_review._output.coding_assessment[2].reasoning | Office/outpatient visit established patient moderate complexity (CMS PFS 2024) is clinically appropriate for hypertensio | Standard GP consultation code, plausible for I10 hypertension management. | Non-deterministic field skipped |
| ✅ | stage_4_medical_review._output.pre_auth_verified | True | True |  |
| ✅ | stage_4_medical_review._output.length_of_stay | None | None |  |
| ✅ | stage_4_medical_review._output.rps_benchmark | 190.0 | 190.0 |  |
| ✅ | stage_4_medical_review._output.bill_variance_pct | 100.0 | 100.0 |  |
| ❌ | stage_4_medical_review._output.medical_necessity_confirmed | False | True | Value mismatch |
| ✅ | stage_4_medical_review._output.medical_flags[0] | BILL_EXCEEDS_BENCHMARK | BILL_EXCEEDS_BENCHMARK |  |
| ✅ | stage_4_medical_review._output.medical_flags[1] | NON_PANEL_PROVIDER | NON_PANEL_PROVIDER |  |
| ⏭️ | stage_4_medical_review._output.medical_review_notes | Provider is non-panel, ECG (93000) is not clinically necessary for routine hypertension without cardiac symptoms, and to | Non-panel GP clinic CityMed (PRV-CLIN-07734) — confirmed not on MOH panel. Dr. Farhan Bin Riza SMC licence active. CPT 9 | Non-deterministic field skipped |
| ⏭️ | stage_4_medical_review._output.review_timestamp | 2026-05-19T18:09:52.189248Z | 2025-04-22T10:18:30+08:00 | Non-deterministic field skipped |

---


## Stage 5 — Financial Adjudication

**Endpoint:** `POST /adjudication/process`  
**Status:** ✅ Approved / Processed  


### Request Payload (= Node 4 Output)
```json
{
  "claim_reference_draft": "DRAFT-20260520-10509",
  "policy_no": "HIC-2023-00456",
  "claimant_name": "Lim Kai Xuan",
  "claim_type": "outpatient",
  "incident_date": "2025-04-20",
  "claim_amount_requested": 380.0,
  "claimable_ceiling": 380.0,
  "policy_product_code": "COMP-HEALTH-SILVER",
  "provider_registration": "PRV-CLIN-07734",
  "document_summary": {
    "total_billed_amount": 380.0,
    "itemised_charges": [
      {
        "description": "GP Consultation Fee",
        "quantity": 1,
        "unit_price": 85.0
      },
      {
        "description": "Blood Pressure Monitoring & ECG",
        "quantity": 1,
        "unit_price": 60.0
      },
      {
        "description": "Basic Metabolic Panel (Blood Test)",
        "quantity": 1,
        "unit_price": 45.0
      },
      {
        "description": "Amlodipine 5mg",
        "quantity": 1,
        "unit_price": 90.0
      },
      {
        "description": "Perindopril 4mg",
        "quantity": 1,
        "unit_price": 100.0
      }
    ],
    "primary_diagnosis_icd10": "I10",
    "procedure_cpt_codes": [
      "99213",
      "93000",
      "80048"
    ],
    "symptom_onset_date": null,
    "admission_date": null,
    "discharge_date": null,
    "attending_physician": "Dr. Farhan Bin Riza",
    "physician_license_no": "MCR-67890F",
    "pre_authorisation_no": null,
    "provider_name_on_bill": "CityMed Family Clinic",
    "extraction_warnings": [],
    "summary_narrative": "Patient Lim Kai Xuan visited CityMed Family Clinic on 20 April 2025 for an outpatient consultation. Diagnosed with hypertension, the physician prescribed a 30‑day supply of Amlodipine and Perindopril. Services included a GP consultation (CPT 99213), blood pressure monitoring with ECG (CPT 93000), and a basic metabolic panel (CPT 80048). Total billed amount was SGD 380.00, which was fully paid by credit card."
  },
  "medical_review_passed": false,
  "review_failure_reason": "CPT_ICD10_MISMATCH",
  "non_panel_flag": true,
  "accreditation_claim": "Provider not found in MOH accredited provider registry as of check date 2026-05-19.",
  "physician_licence_claim": "Physician licence verified with Singapore Medical Council registry as active until 2027-08-31 as of check date 2026-05-19.",
  "coding_assessment": [
    {
      "cpt_code": "99213",
      "valid": true,
      "plausible": true,
      "reasoning": "Office/outpatient visit established patient moderate complexity (CMS PFS 2024) is clinically appropriate for hypertension follow-up."
    },
    {
      "cpt_code": "93000",
      "valid": true,
      "plausible": false,
      "reasoning": "Electrocardiogram routine (CMS PFS 2024) is not standard of care for uncomplicated hypertension without cardiac symptoms."
    },
    {
      "cpt_code": "80048",
      "valid": true,
      "plausible": true,
      "reasoning": "Basic metabolic panel (CMS PFS 2024) is clinically indicated for hypertension monitoring to assess renal function and electrolytes."
    }
  ],
  "pre_auth_verified": true,
  "length_of_stay": null,
  "rps_benchmark": 190.0,
  "bill_variance_pct": 100.0,
  "medical_necessity_confirmed": false,
  "medical_flags": [
    "NON_PANEL_PROVIDER",
    "BILL_EXCEEDS_BENCHMARK"
  ],
  "medical_review_notes": "Provider is non-panel, ECG (93000) is not clinically necessary for routine hypertension without cardiac symptoms, and total billed SGD 380 exceeds RPS benchmark SGD 190. Medical necessity partially confirmed for consultation (99213) and metabolic panel (80048), but ECG lacks clinical justification.",
  "review_timestamp": "2026-05-19T18:09:52.189248Z"
}
```

### Actual API Response
```json
{
  "claim_reference_draft": "DRAFT-20260520-10509",
  "policy_no": "HIC-2023-00456",
  "claimant_name": "Lim Kai Xuan",
  "claim_type": "outpatient",
  "incident_date": "2025-04-20",
  "claim_amount_requested": 380.0,
  "provider_registration": "PRV-CLIN-07734",
  "adjudication_base": 133.0,
  "deductible_applied_this_claim": 133.0,
  "co_pay_amount": 0.0,
  "co_insurance_amount": 0.0,
  "net_payable": 0.0,
  "claimant_liability": 380.0,
  "adjudication_status": "zero_benefit",
  "adjudication_notes": "Claim adjudicated at SGD 133.00 base after applying the non-panel provider reimbursement rate of 70%. The bill exceeded the RPS benchmark. The full base was applied to meet your annual deductible, resulting in a net payable of SGD 0.00. The claimant is liable for the full SGD 380.00 requested.",
  "adjudication_timestamp": "2026-05-19T18:10:08.547279Z"
}
```

### Expected Output (from contract)
```json
{
  "claim_reference_draft": "DRAFT-20250422-01102",
  "policy_no": "HIC-2023-00456",
  "claimant_name": "Lim Kai Xuan",
  "claim_type": "outpatient",
  "incident_date": "2025-04-20",
  "claim_amount_requested": 380.0,
  "provider_registration": "PRV-CLIN-07734",
  "adjudication_base": 133.0,
  "deductible_applied_this_claim": 133.0,
  "co_pay_amount": 0.0,
  "co_insurance_amount": 0.0,
  "net_payable": 0.0,
  "claimant_liability": 380.0,
  "adjudication_status": "zero_benefit",
  "adjudication_notes": "Non-panel provider: 70% reimbursement applied — adjudication base reduced to SGD 133 (from RPS benchmark SGD 190). Annual deductible SGD 2,000 with SGD 180 prior utilisation; remaining SGD 1,820 fully absorbs adjudication base SGD 133. Net payable SGD 0.00 — zero_benefit outcome. Claimant liable for full SGD 380.",
  "adjudication_timestamp": "2025-04-22T10:19:00+08:00"
}
```

### Field-Level Comparison
| Status | Field | Actual | Expected | Note |
|:---:|:---|:---|:---|:---|
| ⏭️ | stage_5_adjudication._output.claim_reference_draft | DRAFT-20260520-10509 | DRAFT-20250422-01102 | Non-deterministic field skipped |
| ✅ | stage_5_adjudication._output.policy_no | HIC-2023-00456 | HIC-2023-00456 |  |
| ✅ | stage_5_adjudication._output.claimant_name | Lim Kai Xuan | Lim Kai Xuan |  |
| ✅ | stage_5_adjudication._output.claim_type | outpatient | outpatient |  |
| ✅ | stage_5_adjudication._output.incident_date | 2025-04-20 | 2025-04-20 |  |
| ✅ | stage_5_adjudication._output.claim_amount_requested | 380.0 | 380.0 |  |
| ✅ | stage_5_adjudication._output.provider_registration | PRV-CLIN-07734 | PRV-CLIN-07734 |  |
| ✅ | stage_5_adjudication._output.adjudication_base | 133.0 | 133.0 |  |
| ✅ | stage_5_adjudication._output.deductible_applied_this_claim | 133.0 | 133.0 |  |
| ✅ | stage_5_adjudication._output.co_pay_amount | 0.0 | 0.0 |  |
| ✅ | stage_5_adjudication._output.co_insurance_amount | 0.0 | 0.0 |  |
| ✅ | stage_5_adjudication._output.net_payable | 0.0 | 0.0 |  |
| ✅ | stage_5_adjudication._output.claimant_liability | 380.0 | 380.0 |  |
| ✅ | stage_5_adjudication._output.adjudication_status | zero_benefit | zero_benefit |  |
| ⏭️ | stage_5_adjudication._output.adjudication_notes | Claim adjudicated at SGD 133.00 base after applying the non-panel provider reimbursement rate of 70%. The bill exceeded  | Non-panel provider: 70% reimbursement applied — adjudication base reduced to SGD 133 (from RPS benchmark SGD 190). Annua | Non-deterministic field skipped |
| ⏭️ | stage_5_adjudication._output.adjudication_timestamp | 2026-05-19T18:10:08.547279Z | 2025-04-22T10:19:00+08:00 | Non-deterministic field skipped |

---


## Stage 6 — Disbursement

**Endpoint:** `POST /disbursement/process`  
**Status:** ✅ Halted (As Expected)  


### Request Payload (= Node 5 Output + payment_details)
```json
{
  "claim_reference_draft": "DRAFT-20260520-10509",
  "policy_no": "HIC-2023-00456",
  "claimant_name": "Lim Kai Xuan",
  "claim_type": "outpatient",
  "incident_date": "2025-04-20",
  "claim_amount_requested": 380.0,
  "provider_registration": "PRV-CLIN-07734",
  "adjudication_base": 133.0,
  "deductible_applied_this_claim": 133.0,
  "co_pay_amount": 0.0,
  "co_insurance_amount": 0.0,
  "net_payable": 0.0,
  "claimant_liability": 380.0,
  "adjudication_status": "zero_benefit",
  "adjudication_notes": "Claim adjudicated at SGD 133.00 base after applying the non-panel provider reimbursement rate of 70%. The bill exceeded the RPS benchmark. The full base was applied to meet your annual deductible, resulting in a net payable of SGD 0.00. The claimant is liable for the full SGD 380.00 requested.",
  "adjudication_timestamp": "2026-05-19T18:10:08.547279Z",
  "payment_details": {
    "payment_mode": "cheque",
    "payee_name": "Lim Kai Xuan"
  }
}
```

### Actual API Response (Reconstructed from 422 Halt)
```json
{
  "claim_reference_draft": "DRAFT-20260520-10509",
  "policy_no": "HIC-2023-00456",
  "claimant_name": "Lim Kai Xuan",
  "claim_type": "outpatient",
  "disbursement_status": "halted",
  "halted_reason": "ZERO_BENEFIT_NO_DISBURSEMENT",
  "net_payable": 0.0,
  "claimant_liability": 380.0,
  "incident_date": "2025-04-20",
  "remarks": "Zero benefit — SGD 133 adjudication base fully absorbed by remaining annual deductible (SGD 1,820 remaining). Non-panel provider discount applied. No insurer disbursement. Claimant responsible for full SGD 380.",
  "processing_timestamp": "2026-05-19T18:10:12.179597+00:00"
}
```

### Expected Output (from contract)
```json
{
  "claim_reference_draft": "DRAFT-20250422-01102",
  "policy_no": "HIC-2023-00456",
  "claimant_name": "Lim Kai Xuan",
  "claim_type": "outpatient",
  "disbursement_status": "halted",
  "halted_reason": "ZERO_BENEFIT_NO_DISBURSEMENT",
  "net_payable": 0.0,
  "claimant_liability": 380.0,
  "incident_date": "2025-04-20",
  "remarks": "Zero benefit — SGD 133 adjudication base fully absorbed by remaining annual deductible (SGD 1,820 remaining). Non-panel provider discount applied. No insurer disbursement. Claimant responsible for full SGD 380.",
  "processing_timestamp": "2025-04-22T10:19:30+08:00"
}
```

### Field-Level Comparison
| Status | Field | Actual | Expected | Note |
|:---:|:---|:---|:---|:---|
| ⏭️ | stage_6_disbursement._output.claim_reference_draft | DRAFT-20260520-10509 | DRAFT-20250422-01102 | Non-deterministic field skipped |
| ✅ | stage_6_disbursement._output.policy_no | HIC-2023-00456 | HIC-2023-00456 |  |
| ✅ | stage_6_disbursement._output.claimant_name | Lim Kai Xuan | Lim Kai Xuan |  |
| ✅ | stage_6_disbursement._output.claim_type | outpatient | outpatient |  |
| ✅ | stage_6_disbursement._output.disbursement_status | halted | halted |  |
| ⏭️ | stage_6_disbursement._output.halted_reason | ZERO_BENEFIT_NO_DISBURSEMENT | ZERO_BENEFIT_NO_DISBURSEMENT | Non-deterministic field skipped |
| ✅ | stage_6_disbursement._output.net_payable | 0.0 | 0.0 |  |
| ✅ | stage_6_disbursement._output.claimant_liability | 380.0 | 380.0 |  |
| ✅ | stage_6_disbursement._output.incident_date | 2025-04-20 | 2025-04-20 |  |
| ⏭️ | stage_6_disbursement._output.remarks | Zero benefit — SGD 133 adjudication base fully absorbed by remaining annual deductible (SGD 1,820 remaining). Non-panel  | Zero benefit — SGD 133 adjudication base fully absorbed by remaining annual deductible (SGD 1,820 remaining). Non-panel  | Non-deterministic field skipped |
| ⏭️ | stage_6_disbursement._output.processing_timestamp | 2026-05-19T18:10:12.179597+00:00 | 2025-04-22T10:19:30+08:00 | Non-deterministic field skipped |

---
