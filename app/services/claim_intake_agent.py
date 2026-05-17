from app.schemas.claim_intake import ClaimIntakeInput, ClaimIntakeOutput, IdDocumentType
from app.services.claim_intake_tools import (
    validate_regex,
    mcp_query_policy_existence,
    get_server_date,
    get_server_timestamp,
    calculate_age,
    calculate_submission_lag,
    validate_claim_amount,
    validate_documents_vocabulary,
    check_missing_documents,
    generate_draft_reference
)

async def process_claim_intake(input_data: ClaimIntakeInput) -> ClaimIntakeOutput:
    """
    Occupies the agent for following exactly how the processing logic specify.
    Produces a standard output to be processed by the other agent.
    """
    rejection_reason = None
    missing_documents = []

    # 1. Policy number format check
    if not validate_regex(r"^HIC-\d{4}-\d{5}$", input_data.policy_no):
        rejection_reason = "INVALID_POLICY_FORMAT"
    else:
        policy_exists = await mcp_query_policy_existence(input_data.policy_no)
        if not policy_exists:
            rejection_reason = "POLICY_NOT_FOUND"

    # 2. Identity document format check
    if rejection_reason is None:
        id_regexes = {
            IdDocumentType.nric: r"^[STFG]\d{7}[A-Z]$",
            IdDocumentType.fin: r"^[FG]\d{7}[A-Z]$",
            IdDocumentType.passport: r"^[A-Z]{1,2}\d{6,9}$",
            IdDocumentType.birth_certificate: r"^[A-Z]{2}\d{6}[A-Z]$"
        }
        regex = id_regexes.get(input_data.id_document_type)
        if not regex or not validate_regex(regex, input_data.id_document_no):
            rejection_reason = "INVALID_ID_FORMAT"

    # 3. Date sanity checks
    if rejection_reason is None:
        server_date = get_server_date()
        if input_data.date_of_birth >= input_data.claim_date:
            rejection_reason = "INVALID_DATE_OF_BIRTH"
        else:
            age = calculate_age(input_data.date_of_birth, input_data.claim_date)
            if age < 0 or age > 120:
                rejection_reason = "INVALID_DATE_OF_BIRTH"
            elif input_data.incident_date > input_data.claim_date:
                rejection_reason = "FUTURE_INCIDENT_DATE"
            elif input_data.claim_date != server_date:
                rejection_reason = "INVALID_CLAIM_DATE"

    # 4. Claim submission window
    if rejection_reason is None:
        lag = calculate_submission_lag(input_data.incident_date, input_data.claim_date)
        if lag > 365:
            rejection_reason = "LATE_SUBMISSION"

    # 5. Claim amount floor
    if rejection_reason is None:
        if not validate_claim_amount(input_data.claim_amount_requested):
            rejection_reason = "INVALID_CLAIM_AMOUNT"

    # 6. Supporting documents vocabulary check
    if rejection_reason is None:
        if not validate_documents_vocabulary(input_data.supporting_documents):
            rejection_reason = "UNKNOWN_DOCUMENT_TYPE"

    # 7. Supporting documents completeness
    if rejection_reason is None:
        missing_documents = check_missing_documents(
            input_data.claim_type, input_data.supporting_documents
        )
        if missing_documents:
            rejection_reason = "MISSING_REQUIRED_DOCUMENTS"

    # 8. Contact information validation
    if rejection_reason is None:
        email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        phone_regex = r"^\+?[0-9]{8,15}$"
        
        if not validate_regex(email_regex, input_data.claimant_contact_email):
            rejection_reason = "INVALID_EMAIL"
        elif not validate_regex(phone_regex, input_data.claimant_contact_phone):
            rejection_reason = "INVALID_PHONE"

    # 9 & 10. Intake status decision & Rejection reason
    intake_accepted = (rejection_reason is None)

    # Produce Output Schema B
    output = ClaimIntakeOutput(
        claim_reference_draft=generate_draft_reference(),
        policy_no=input_data.policy_no,
        claimant_name=input_data.claimant_name,
        claim_type=input_data.claim_type,
        incident_date=input_data.incident_date,
        claim_date=input_data.claim_date,
        claim_amount_requested=input_data.claim_amount_requested,
        intake_accepted=intake_accepted,
        rejection_reason=rejection_reason,
        missing_documents=missing_documents,
        intake_timestamp=get_server_timestamp()
    )

    return output
