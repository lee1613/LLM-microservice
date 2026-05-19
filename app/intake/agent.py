import re
import uuid
import math
from datetime import datetime
from app.intake.schemas import ClaimIntakeInput, ClaimIntakeOutput, DocumentSummary, IdDocumentType, ClaimType
from app.intake.tools import (
    query_policy_existence, 
    get_server_timestamp, 
    extract_document_summary
)

async def process_claim_intake(input_data: ClaimIntakeInput) -> ClaimIntakeOutput:
    rejection_reason = None
    missing_documents = []
    
    # Pre-Authorisation Document Gate
    if input_data.claim_type in [ClaimType.hospitalisation, ClaimType.surgical, ClaimType.maternity]:
        if "pre_auth_approval" not in input_data.supporting_documents:
            rejection_reason = "MISSING_PRE_AUTH_DOCUMENT"
            
    # 1. Policy existence check
    if not rejection_reason:
        if not re.match(r"^HIC-\d{4}-\d{5}$", input_data.policy_no):
            rejection_reason = "INVALID_POLICY_FORMAT"
        elif not query_policy_existence(input_data.policy_no):
            rejection_reason = "POLICY_NOT_FOUND"

    # 2. Identity document format check
    if not rejection_reason:
        id_regexes = {
            IdDocumentType.nric: r"^[STFG]\d{7}[A-Z]$",
            IdDocumentType.fin: r"^[FG]\d{7}[A-Z]$",
            IdDocumentType.passport: r"^[A-Z]{1,2}\d{6,9}$",
            IdDocumentType.birth_certificate: r"^[A-Z]{2}\d{6}[A-Z]$"
        }
        if not re.match(id_regexes[input_data.id_document_type], input_data.id_document_no):
            rejection_reason = "INVALID_ID_FORMAT"

    # 3. Date sanity & submission window
    if not rejection_reason:
        if not (input_data.date_of_birth < input_data.incident_date <= input_data.claim_date):
            if input_data.date_of_birth >= input_data.incident_date:
                rejection_reason = "INVALID_DATE_OF_BIRTH"
            elif input_data.incident_date > input_data.claim_date:
                rejection_reason = "FUTURE_INCIDENT_DATE"
        
        if not rejection_reason:
            age = math.floor((input_data.claim_date - input_data.date_of_birth).days / 365.25)
            if age < 0 or age > 120:
                rejection_reason = "INVALID_DATE_OF_BIRTH"
            
            lag = (input_data.claim_date - input_data.incident_date).days
            if lag > 365:
                rejection_reason = "LATE_SUBMISSION"

    # 4. Required documents check
    if not rejection_reason:
        required_docs = []
        if input_data.claim_type in [ClaimType.hospitalisation, ClaimType.surgical, ClaimType.maternity]:
            required_docs = ["medical_bill", "discharge_summary", "pre_auth_approval"]
        else:
            required_docs = ["medical_bill"]
            
        for doc in required_docs:
            if doc not in input_data.supporting_documents:
                missing_documents.append(doc)
                
        if missing_documents:
            rejection_reason = "MISSING_REQUIRED_DOCUMENTS"

    doc_summary = None
    if not rejection_reason:
        # 5. Document parsing & structured summary extraction
        try:
            extracted = extract_document_summary(input_data.scanned_files, input_data.claim_type.value, input_data.claim_amount_requested)
            
            # Format checks for extracted data
            warnings = extracted.get("extraction_warnings", [])
            
            if extracted.get("total_billed_amount") is None:
                warnings.append("total_billed_amount")
            if extracted.get("primary_diagnosis_icd10") is None:
                warnings.append("primary_diagnosis_icd10")
                
            if "total_billed_amount" in warnings or "primary_diagnosis_icd10" in warnings:
                rejection_reason = "DOCUMENT_PARSE_FAILURE"
            else:
                # Check amount discrepancy
                billed = extracted.get("total_billed_amount")
                if billed and billed > 0:
                    diff = abs(billed - input_data.claim_amount_requested) / input_data.claim_amount_requested
                    if diff > 0.05:
                        warnings.append("AMOUNT_DISCREPANCY")
                        
                # Post conditions checks on extracted data to ensure they conform
                if extracted.get("primary_diagnosis_icd10") and not re.match(r"^[A-Z]\d{2}(\.\d{1,4})?$", extracted.get("primary_diagnosis_icd10")):
                     warnings.append("INVALID_ICD10_FORMAT")
                     
                doc_summary = DocumentSummary(
                    total_billed_amount=extracted.get("total_billed_amount"),
                    itemised_charges=extracted.get("itemised_charges", []),
                    primary_diagnosis_icd10=extracted.get("primary_diagnosis_icd10"),
                    procedure_cpt_codes=extracted.get("procedure_cpt_codes", []),
                    symptom_onset_date=extracted.get("symptom_onset_date"),
                    admission_date=extracted.get("admission_date"),
                    discharge_date=extracted.get("discharge_date"),
                    attending_physician=extracted.get("attending_physician"),
                    physician_license_no=extracted.get("physician_license_no"),
                    pre_authorisation_no=extracted.get("pre_authorisation_no"),
                    provider_name_on_bill=extracted.get("provider_name_on_bill"),
                    extraction_warnings=warnings,
                    summary_narrative=extracted.get("summary_narrative")
                )
        except Exception as e:
            import logging
            logging.error(f"document parse failure: {e}", exc_info=True)
            rejection_reason = "DOCUMENT_PARSE_FAILURE"
            return ClaimIntakeOutput(
                claim_reference_draft="",
                policy_no=input_data.policy_no,
                claimant_name=input_data.claimant_name,
                id_document_type=input_data.id_document_type,
                id_document_no=input_data.id_document_no,
                date_of_birth=input_data.date_of_birth,
                claimant_relationship=input_data.claimant_relationship,
                claim_type=input_data.claim_type,
                incident_date=input_data.incident_date,
                claim_date=input_data.claim_date,
                claim_amount_requested=input_data.claim_amount_requested,
                provider_name=input_data.provider_name,
                provider_registration=input_data.provider_registration,
                intake_accepted=False,
                rejection_reason=rejection_reason,
                missing_documents=missing_documents,
                intake_timestamp=get_server_timestamp(),
                document_summary=None,
                _debug_error=str(e)
            )

    # Final Draft Generation
    draft_ref = ""
    if not rejection_reason:
        today_str = get_server_timestamp().strftime("%Y%m%d")
        unique_id = str(uuid.uuid4().int)[:5].zfill(5)
        draft_ref = f"DRAFT-{today_str}-{unique_id}"

    return ClaimIntakeOutput(
        claim_reference_draft=draft_ref,
        policy_no=input_data.policy_no,
        claimant_name=input_data.claimant_name,
        id_document_type=input_data.id_document_type,
        id_document_no=input_data.id_document_no,
        date_of_birth=input_data.date_of_birth,
        claimant_relationship=input_data.claimant_relationship,
        claim_type=input_data.claim_type,
        incident_date=input_data.incident_date,
        claim_date=input_data.claim_date,
        claim_amount_requested=input_data.claim_amount_requested,
        provider_name=input_data.provider_name,
        provider_registration=input_data.provider_registration,
        intake_accepted=(rejection_reason is None),
        rejection_reason=rejection_reason,
        missing_documents=missing_documents,
        intake_timestamp=get_server_timestamp(),
        document_summary=doc_summary
    )
