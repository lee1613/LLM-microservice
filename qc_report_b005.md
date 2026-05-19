# QC Report — B005 Full Pipeline
**Scenario:** B005 — Emergency (Closed Radius Fracture from Fall), COMP-HEALTH-GOLD, Self, REJECTED at Node 2 (Duplicate Claim)  
**Expected Outcome:** Pipeline halts at Node 2. An existing paid claim CLM-2025-0000877 already exists for policy HIC-2024-00099 + incident_date 2025-04-21 + claim_type emergency with status=paid. Duplicate check fails → DUPLICATE_CLAIM.  
**API Target:** `http://127.0.0.1:8000`  
**Run Timestamp:** `2026-05-19T17:55:03Z`  



## Executive Summary

| Metric | Count |
|:---|:---:|
| ✅ PASS | 74 |
| ❌ FAIL | 0 |
| ⏭️ SKIP (non-deterministic) | 18 |
| ℹ️ INFO (extra keys) | 0 |

### Per-Node Results
| Result | Node | PASS | FAIL | SKIP |
|:---:|:---|:---:|:---:|:---:|
| ✅ | Node 1: Intake (upload) | 35 | 0 | 9 |
| ✅ | Node 2: Verification | 39 | 0 | 9 |

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
**Uploaded Files:** ['medical_bill.pdf']  
**Status:** ✅ Accepted  


### Actual API Response
```json
{
  "claim_reference_draft": "DRAFT-20260520-19467",
  "policy_no": "HIC-2024-00099",
  "claimant_name": "Chen Mei Ling",
  "id_document_type": "nric",
  "id_document_no": "S9145678F",
  "date_of_birth": "1991-12-07",
  "claimant_relationship": "self",
  "claim_type": "emergency",
  "incident_date": "2025-04-21",
  "claim_date": "2025-05-01",
  "claim_amount_requested": 2850.0,
  "provider_name": "Tan Tock Seng Hospital",
  "provider_registration": "MOH-HOSP-00391",
  "intake_accepted": true,
  "rejection_reason": null,
  "missing_documents": [],
  "intake_timestamp": "2026-05-20T01:55:15.202851+08:00",
  "document_summary": {
    "total_billed_amount": 2850.0,
    "itemised_charges": [
      {
        "description": "Emergency Consultation & Assessment",
        "quantity": 1,
        "unit_price": 180.0
      },
      {
        "description": "X-Ray Right Wrist (2 views)",
        "quantity": 1,
        "unit_price": 95.0
      },
      {
        "description": "Closed Reduction, Right Distal",
        "quantity": 1,
        "unit_price": 1800.0
      },
      {
        "description": "Plaster Splint Application",
        "quantity": 1,
        "unit_price": 350.0
      },
      {
        "description": "Analgesics & Medications",
        "quantity": 1,
        "unit_price": 425.0
      }
    ],
    "primary_diagnosis_icd10": "S52.501A",
    "procedure_cpt_codes": [
      "73100",
      "25600"
    ],
    "symptom_onset_date": "2025-04-21",
    "admission_date": null,
    "discharge_date": null,
    "attending_physician": "Dr. Lim Ah Kow",
    "physician_license_no": "MCR-55678E",
    "pre_authorisation_no": null,
    "provider_name_on_bill": "Tan Tock Seng Hospital",
    "extraction_warnings": [
      "admission_date",
      "discharge_date",
      "INVALID_ICD10_FORMAT"
    ],
    "summary_narrative": "Patient Chen Mei Ling visited Tan Tock Seng Hospital Emergency Department on 21 April 2025 after a fall, presenting with a right distal radius fracture (ICD‑10 S52.501A). The emergency team provided consultation, X‑ray, closed reduction, splint application, and analgesia. Total billed amount was SGD 2,850.00."
  }
}
```

### Expected Output (from contract)
```json
{
  "claim_reference_draft": "DRAFT-20250501-01105",
  "policy_no": "HIC-2024-00099",
  "claimant_name": "Chen Mei Ling",
  "id_document_type": "nric",
  "id_document_no": "S9145678F",
  "date_of_birth": "1991-12-07",
  "claimant_relationship": "self",
  "claim_type": "emergency",
  "incident_date": "2025-04-21",
  "claim_date": "2025-05-01",
  "claim_amount_requested": 2850.0,
  "provider_name": "Tan Tock Seng Hospital",
  "provider_registration": "MOH-HOSP-00391",
  "intake_accepted": true,
  "rejection_reason": null,
  "missing_documents": [],
  "intake_timestamp": "2025-05-01T09:00:00+08:00",
  "document_summary": {
    "total_billed_amount": 2850.0,
    "itemised_charges": [
      {
        "description": "Emergency consultation and assessment",
        "quantity": 1,
        "unit_price": 180.0
      },
      {
        "description": "X-ray right wrist (2 views)",
        "quantity": 1,
        "unit_price": 95.0
      },
      {
        "description": "Closed reduction right distal radius fracture",
        "quantity": 1,
        "unit_price": 1800.0
      },
      {
        "description": "Plaster splint application",
        "quantity": 1,
        "unit_price": 350.0
      },
      {
        "description": "Analgesics and medications",
        "quantity": 1,
        "unit_price": 425.0
      }
    ],
    "primary_diagnosis_icd10": "S52.501A",
    "procedure_cpt_codes": [
      "25600",
      "73100"
    ],
    "symptom_onset_date": "2025-04-21",
    "admission_date": null,
    "discharge_date": null,
    "attending_physician": "Dr. Lim Ah Kow",
    "physician_license_no": "MCR-55678E",
    "pre_authorisation_no": null,
    "provider_name_on_bill": "Tan Tock Seng Hospital",
    "extraction_warnings": [],
    "summary_narrative": "Chen Mei Ling, 33, attended Tan Tock Seng Hospital Emergency Department on 21 Apr 2025 following a fall resulting in a closed right distal radius fracture (ICD-10 S52.501A). Procedures included emergency assessment, wrist X-ray (CPT 73100), closed reduction (CPT 25600), and splint application. No admission — outpatient emergency visit. Total billed SGD 2,850. No pre-authorisation required for emergency claims."
  }
}
```

### Field-Level Comparison
| Status | Field | Actual | Expected | Note |
|:---:|:---|:---|:---|:---|
| ⏭️ | stage_1_intake._output.claim_reference_draft | DRAFT-20260520-19467 | DRAFT-20250501-01105 | Non-deterministic field skipped |
| ✅ | stage_1_intake._output.policy_no | HIC-2024-00099 | HIC-2024-00099 |  |
| ✅ | stage_1_intake._output.claimant_name | Chen Mei Ling | Chen Mei Ling |  |
| ✅ | stage_1_intake._output.id_document_type | nric | nric |  |
| ✅ | stage_1_intake._output.id_document_no | S9145678F | S9145678F |  |
| ✅ | stage_1_intake._output.date_of_birth | 1991-12-07 | 1991-12-07 |  |
| ✅ | stage_1_intake._output.claimant_relationship | self | self |  |
| ✅ | stage_1_intake._output.claim_type | emergency | emergency |  |
| ✅ | stage_1_intake._output.incident_date | 2025-04-21 | 2025-04-21 |  |
| ✅ | stage_1_intake._output.claim_date | 2025-05-01 | 2025-05-01 |  |
| ✅ | stage_1_intake._output.claim_amount_requested | 2850.0 | 2850.0 |  |
| ✅ | stage_1_intake._output.provider_name | Tan Tock Seng Hospital | Tan Tock Seng Hospital |  |
| ✅ | stage_1_intake._output.provider_registration | MOH-HOSP-00391 | MOH-HOSP-00391 |  |
| ✅ | stage_1_intake._output.intake_accepted | True | True |  |
| ✅ | stage_1_intake._output.rejection_reason | None | None |  |
| ⏭️ | stage_1_intake._output.intake_timestamp | 2026-05-20T01:55:15.202851+08:00 | 2025-05-01T09:00:00+08:00 | Non-deterministic field skipped |
| ✅ | stage_1_intake._output.document_summary.total_billed_amount | 2850.0 | 2850.0 |  |
| ⏭️ | stage_1_intake._output.document_summary.itemised_charges[0].description | Emergency Consultation & Assessment | Emergency consultation and assessment | Non-deterministic field skipped |
| ✅ | stage_1_intake._output.document_summary.itemised_charges[0].quantity | 1 | 1 |  |
| ✅ | stage_1_intake._output.document_summary.itemised_charges[0].unit_price | 180.0 | 180.0 |  |
| ⏭️ | stage_1_intake._output.document_summary.itemised_charges[1].description | X-Ray Right Wrist (2 views) | X-ray right wrist (2 views) | Non-deterministic field skipped |
| ✅ | stage_1_intake._output.document_summary.itemised_charges[1].quantity | 1 | 1 |  |
| ✅ | stage_1_intake._output.document_summary.itemised_charges[1].unit_price | 95.0 | 95.0 |  |
| ⏭️ | stage_1_intake._output.document_summary.itemised_charges[2].description | Closed Reduction, Right Distal | Closed reduction right distal radius fracture | Non-deterministic field skipped |
| ✅ | stage_1_intake._output.document_summary.itemised_charges[2].quantity | 1 | 1 |  |
| ✅ | stage_1_intake._output.document_summary.itemised_charges[2].unit_price | 1800.0 | 1800.0 |  |
| ⏭️ | stage_1_intake._output.document_summary.itemised_charges[3].description | Plaster Splint Application | Plaster splint application | Non-deterministic field skipped |
| ✅ | stage_1_intake._output.document_summary.itemised_charges[3].quantity | 1 | 1 |  |
| ✅ | stage_1_intake._output.document_summary.itemised_charges[3].unit_price | 350.0 | 350.0 |  |
| ⏭️ | stage_1_intake._output.document_summary.itemised_charges[4].description | Analgesics & Medications | Analgesics and medications | Non-deterministic field skipped |
| ✅ | stage_1_intake._output.document_summary.itemised_charges[4].quantity | 1 | 1 |  |
| ✅ | stage_1_intake._output.document_summary.itemised_charges[4].unit_price | 425.0 | 425.0 |  |
| ✅ | stage_1_intake._output.document_summary.primary_diagnosis_icd10 | S52.501A | S52.501A |  |
| ✅ | stage_1_intake._output.document_summary.procedure_cpt_codes[0] | 25600 | 25600 |  |
| ✅ | stage_1_intake._output.document_summary.procedure_cpt_codes[1] | 73100 | 73100 |  |
| ✅ | stage_1_intake._output.document_summary.symptom_onset_date | 2025-04-21 | 2025-04-21 |  |
| ✅ | stage_1_intake._output.document_summary.admission_date | None | None |  |
| ✅ | stage_1_intake._output.document_summary.discharge_date | None | None |  |
| ✅ | stage_1_intake._output.document_summary.attending_physician | Dr. Lim Ah Kow | Dr. Lim Ah Kow |  |
| ✅ | stage_1_intake._output.document_summary.physician_license_no | MCR-55678E | MCR-55678E |  |
| ✅ | stage_1_intake._output.document_summary.pre_authorisation_no | None | None |  |
| ✅ | stage_1_intake._output.document_summary.provider_name_on_bill | Tan Tock Seng Hospital | Tan Tock Seng Hospital |  |
| ⏭️ | stage_1_intake._output.document_summary.extraction_warnings | ['admission_date', 'discharge_date', 'INVALID_ICD10_FORMAT'] | [] | Non-deterministic field skipped |
| ⏭️ | stage_1_intake._output.document_summary.summary_narrative | Patient Chen Mei Ling visited Tan Tock Seng Hospital Emergency Department on 21 April 2025 after a fall, presenting with | Chen Mei Ling, 33, attended Tan Tock Seng Hospital Emergency Department on 21 Apr 2025 following a fall resulting in a c | Non-deterministic field skipped |

---


## Stage 2 — Policy Verification

**Endpoint:** `POST /verification/process`  
**Status:** ❌ DUPLICATE_CLAIM (EXPECTED for B005)  


### Request Payload (= Node 1 Output)
```json
{
  "claim_reference_draft": "DRAFT-20260520-19467",
  "policy_no": "HIC-2024-00099",
  "claimant_name": "Chen Mei Ling",
  "id_document_type": "nric",
  "id_document_no": "S9145678F",
  "date_of_birth": "1991-12-07",
  "claimant_relationship": "self",
  "claim_type": "emergency",
  "incident_date": "2025-04-21",
  "claim_date": "2025-05-01",
  "claim_amount_requested": 2850.0,
  "provider_name": "Tan Tock Seng Hospital",
  "provider_registration": "MOH-HOSP-00391",
  "intake_accepted": true,
  "rejection_reason": null,
  "missing_documents": [],
  "intake_timestamp": "2026-05-20T01:55:15.202851+08:00",
  "document_summary": {
    "total_billed_amount": 2850.0,
    "itemised_charges": [
      {
        "description": "Emergency Consultation & Assessment",
        "quantity": 1,
        "unit_price": 180.0
      },
      {
        "description": "X-Ray Right Wrist (2 views)",
        "quantity": 1,
        "unit_price": 95.0
      },
      {
        "description": "Closed Reduction, Right Distal",
        "quantity": 1,
        "unit_price": 1800.0
      },
      {
        "description": "Plaster Splint Application",
        "quantity": 1,
        "unit_price": 350.0
      },
      {
        "description": "Analgesics & Medications",
        "quantity": 1,
        "unit_price": 425.0
      }
    ],
    "primary_diagnosis_icd10": "S52.501A",
    "procedure_cpt_codes": [
      "73100",
      "25600"
    ],
    "symptom_onset_date": "2025-04-21",
    "admission_date": null,
    "discharge_date": null,
    "attending_physician": "Dr. Lim Ah Kow",
    "physician_license_no": "MCR-55678E",
    "pre_authorisation_no": null,
    "provider_name_on_bill": "Tan Tock Seng Hospital",
    "extraction_warnings": [
      "admission_date",
      "discharge_date",
      "INVALID_ICD10_FORMAT"
    ],
    "summary_narrative": "Patient Chen Mei Ling visited Tan Tock Seng Hospital Emergency Department on 21 April 2025 after a fall, presenting with a right distal radius fracture (ICD‑10 S52.501A). The emergency team provided consultation, X‑ray, closed reduction, splint application, and analgesia. Total billed amount was SGD 2,850.00."
  }
}
```

### Actual API Response
```json
{
  "claim_reference_draft": "DRAFT-20260520-19467",
  "policy_no": "HIC-2024-00099",
  "claimant_name": "Chen Mei Ling",
  "id_document_type": "nric",
  "id_document_no": "S9145678F",
  "date_of_birth": "1991-12-07",
  "claimant_relationship": "self",
  "claim_type": "emergency",
  "incident_date": "2025-04-21",
  "claim_amount_requested": 2850.0,
  "provider_name": "Tan Tock Seng Hospital",
  "provider_registration": "MOH-HOSP-00391",
  "document_summary": {
    "total_billed_amount": 2850.0,
    "itemised_charges": [
      {
        "description": "Emergency Consultation & Assessment",
        "quantity": 1,
        "unit_price": 180.0
      },
      {
        "description": "X-Ray Right Wrist (2 views)",
        "quantity": 1,
        "unit_price": 95.0
      },
      {
        "description": "Closed Reduction, Right Distal",
        "quantity": 1,
        "unit_price": 1800.0
      },
      {
        "description": "Plaster Splint Application",
        "quantity": 1,
        "unit_price": 350.0
      },
      {
        "description": "Analgesics & Medications",
        "quantity": 1,
        "unit_price": 425.0
      }
    ],
    "primary_diagnosis_icd10": "S52.501A",
    "procedure_cpt_codes": [
      "73100",
      "25600"
    ],
    "symptom_onset_date": "2025-04-21",
    "admission_date": null,
    "discharge_date": null,
    "attending_physician": "Dr. Lim Ah Kow",
    "physician_license_no": "MCR-55678E",
    "pre_authorisation_no": null,
    "provider_name_on_bill": "Tan Tock Seng Hospital",
    "extraction_warnings": [
      "admission_date",
      "discharge_date",
      "INVALID_ICD10_FORMAT"
    ],
    "summary_narrative": "Patient Chen Mei Ling visited Tan Tock Seng Hospital Emergency Department on 21 April 2025 after a fall, presenting with a right distal radius fracture (ICD‑10 S52.501A). The emergency team provided consultation, X‑ray, closed reduction, splint application, and analgesia. Total billed amount was SGD 2,850.00."
  },
  "policy_verified": false,
  "verification_failure": "DUPLICATE_CLAIM",
  "policy_start_date": "2024-04-01",
  "policy_expiry_date": "2026-03-31",
  "policy_product_code": "COMP-HEALTH-GOLD",
  "premium_payment_mode": "annual",
  "dependent_verified": true,
  "verification_timestamp": "2026-05-19T17:55:15.217750Z"
}
```

### Expected Output (from contract)
```json
{
  "claim_reference_draft": "DRAFT-20250501-01105",
  "policy_no": "HIC-2024-00099",
  "claimant_name": "Chen Mei Ling",
  "id_document_type": "nric",
  "id_document_no": "S9145678F",
  "date_of_birth": "1991-12-07",
  "claimant_relationship": "self",
  "claim_type": "emergency",
  "incident_date": "2025-04-21",
  "claim_amount_requested": 2850.0,
  "provider_name": "Tan Tock Seng Hospital",
  "provider_registration": "MOH-HOSP-00391",
  "document_summary": {
    "total_billed_amount": 2850.0,
    "itemised_charges": [
      {
        "description": "Emergency consultation and assessment",
        "quantity": 1,
        "unit_price": 180.0
      },
      {
        "description": "X-ray right wrist (2 views)",
        "quantity": 1,
        "unit_price": 95.0
      },
      {
        "description": "Closed reduction right distal radius fracture",
        "quantity": 1,
        "unit_price": 1800.0
      },
      {
        "description": "Plaster splint application",
        "quantity": 1,
        "unit_price": 350.0
      },
      {
        "description": "Analgesics and medications",
        "quantity": 1,
        "unit_price": 425.0
      }
    ],
    "primary_diagnosis_icd10": "S52.501A",
    "procedure_cpt_codes": [
      "25600",
      "73100"
    ],
    "symptom_onset_date": "2025-04-21",
    "admission_date": null,
    "discharge_date": null,
    "attending_physician": "Dr. Lim Ah Kow",
    "physician_license_no": "MCR-55678E",
    "pre_authorisation_no": null,
    "provider_name_on_bill": "Tan Tock Seng Hospital",
    "extraction_warnings": [],
    "summary_narrative": "Chen Mei Ling, 33, attended Tan Tock Seng Hospital Emergency Department on 21 Apr 2025 following a fall resulting in a closed right distal radius fracture (ICD-10 S52.501A). Procedures included emergency assessment, wrist X-ray (CPT 73100), closed reduction (CPT 25600), and splint application. No admission — outpatient emergency visit. Total billed SGD 2,850. No pre-authorisation required for emergency claims."
  },
  "policy_verified": false,
  "verification_failure": "DUPLICATE_CLAIM",
  "policy_start_date": "2024-04-01",
  "policy_expiry_date": "2026-03-31",
  "policy_product_code": "COMP-HEALTH-GOLD",
  "premium_payment_mode": "annual",
  "dependent_verified": true,
  "verification_timestamp": "2025-05-01T09:01:30+08:00"
}
```

### Field-Level Comparison
| Status | Field | Actual | Expected | Note |
|:---:|:---|:---|:---|:---|
| ⏭️ | stage_2_verification._output.claim_reference_draft | DRAFT-20260520-19467 | DRAFT-20250501-01105 | Non-deterministic field skipped |
| ✅ | stage_2_verification._output.policy_no | HIC-2024-00099 | HIC-2024-00099 |  |
| ✅ | stage_2_verification._output.claimant_name | Chen Mei Ling | Chen Mei Ling |  |
| ✅ | stage_2_verification._output.id_document_type | nric | nric |  |
| ✅ | stage_2_verification._output.id_document_no | S9145678F | S9145678F |  |
| ✅ | stage_2_verification._output.date_of_birth | 1991-12-07 | 1991-12-07 |  |
| ✅ | stage_2_verification._output.claimant_relationship | self | self |  |
| ✅ | stage_2_verification._output.claim_type | emergency | emergency |  |
| ✅ | stage_2_verification._output.incident_date | 2025-04-21 | 2025-04-21 |  |
| ✅ | stage_2_verification._output.claim_amount_requested | 2850.0 | 2850.0 |  |
| ✅ | stage_2_verification._output.provider_name | Tan Tock Seng Hospital | Tan Tock Seng Hospital |  |
| ✅ | stage_2_verification._output.provider_registration | MOH-HOSP-00391 | MOH-HOSP-00391 |  |
| ✅ | stage_2_verification._output.document_summary.total_billed_amount | 2850.0 | 2850.0 |  |
| ⏭️ | stage_2_verification._output.document_summary.itemised_charges[0].description | Emergency Consultation & Assessment | Emergency consultation and assessment | Non-deterministic field skipped |
| ✅ | stage_2_verification._output.document_summary.itemised_charges[0].quantity | 1 | 1 |  |
| ✅ | stage_2_verification._output.document_summary.itemised_charges[0].unit_price | 180.0 | 180.0 |  |
| ⏭️ | stage_2_verification._output.document_summary.itemised_charges[1].description | X-Ray Right Wrist (2 views) | X-ray right wrist (2 views) | Non-deterministic field skipped |
| ✅ | stage_2_verification._output.document_summary.itemised_charges[1].quantity | 1 | 1 |  |
| ✅ | stage_2_verification._output.document_summary.itemised_charges[1].unit_price | 95.0 | 95.0 |  |
| ⏭️ | stage_2_verification._output.document_summary.itemised_charges[2].description | Closed Reduction, Right Distal | Closed reduction right distal radius fracture | Non-deterministic field skipped |
| ✅ | stage_2_verification._output.document_summary.itemised_charges[2].quantity | 1 | 1 |  |
| ✅ | stage_2_verification._output.document_summary.itemised_charges[2].unit_price | 1800.0 | 1800.0 |  |
| ⏭️ | stage_2_verification._output.document_summary.itemised_charges[3].description | Plaster Splint Application | Plaster splint application | Non-deterministic field skipped |
| ✅ | stage_2_verification._output.document_summary.itemised_charges[3].quantity | 1 | 1 |  |
| ✅ | stage_2_verification._output.document_summary.itemised_charges[3].unit_price | 350.0 | 350.0 |  |
| ⏭️ | stage_2_verification._output.document_summary.itemised_charges[4].description | Analgesics & Medications | Analgesics and medications | Non-deterministic field skipped |
| ✅ | stage_2_verification._output.document_summary.itemised_charges[4].quantity | 1 | 1 |  |
| ✅ | stage_2_verification._output.document_summary.itemised_charges[4].unit_price | 425.0 | 425.0 |  |
| ✅ | stage_2_verification._output.document_summary.primary_diagnosis_icd10 | S52.501A | S52.501A |  |
| ✅ | stage_2_verification._output.document_summary.procedure_cpt_codes[0] | 25600 | 25600 |  |
| ✅ | stage_2_verification._output.document_summary.procedure_cpt_codes[1] | 73100 | 73100 |  |
| ✅ | stage_2_verification._output.document_summary.symptom_onset_date | 2025-04-21 | 2025-04-21 |  |
| ✅ | stage_2_verification._output.document_summary.admission_date | None | None |  |
| ✅ | stage_2_verification._output.document_summary.discharge_date | None | None |  |
| ✅ | stage_2_verification._output.document_summary.attending_physician | Dr. Lim Ah Kow | Dr. Lim Ah Kow |  |
| ✅ | stage_2_verification._output.document_summary.physician_license_no | MCR-55678E | MCR-55678E |  |
| ✅ | stage_2_verification._output.document_summary.pre_authorisation_no | None | None |  |
| ✅ | stage_2_verification._output.document_summary.provider_name_on_bill | Tan Tock Seng Hospital | Tan Tock Seng Hospital |  |
| ⏭️ | stage_2_verification._output.document_summary.extraction_warnings | ['admission_date', 'discharge_date', 'INVALID_ICD10_FORMAT'] | [] | Non-deterministic field skipped |
| ⏭️ | stage_2_verification._output.document_summary.summary_narrative | Patient Chen Mei Ling visited Tan Tock Seng Hospital Emergency Department on 21 April 2025 after a fall, presenting with | Chen Mei Ling, 33, attended Tan Tock Seng Hospital Emergency Department on 21 Apr 2025 following a fall resulting in a c | Non-deterministic field skipped |
| ✅ | stage_2_verification._output.policy_verified | False | False |  |
| ✅ | stage_2_verification._output.verification_failure | DUPLICATE_CLAIM | DUPLICATE_CLAIM |  |
| ✅ | stage_2_verification._output.policy_start_date | 2024-04-01 | 2024-04-01 |  |
| ✅ | stage_2_verification._output.policy_expiry_date | 2026-03-31 | 2026-03-31 |  |
| ✅ | stage_2_verification._output.policy_product_code | COMP-HEALTH-GOLD | COMP-HEALTH-GOLD |  |
| ✅ | stage_2_verification._output.premium_payment_mode | annual | annual |  |
| ✅ | stage_2_verification._output.dependent_verified | True | True |  |
| ⏭️ | stage_2_verification._output.verification_timestamp | 2026-05-19T17:55:15.217750Z | 2025-05-01T09:01:30+08:00 | Non-deterministic field skipped |

---


## Stages 3–6 — Skipped

> Pipeline halted at Node 2 — `policy_verified=false`, `verification_failure=DUPLICATE_CLAIM`.  
> Nodes 3 (Eligibility), 4 (Medical Review), 5 (Adjudication), and 6 (Disbursement) are **not invoked** — this is the expected behaviour for B005.

---
