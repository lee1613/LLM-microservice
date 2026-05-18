from datetime import datetime, timezone, date
from app.verification.schemas import PolicyVerificationInput, PolicyVerificationOutput
from app.verification.tools import (
    get_policy,
    get_policy_member,
    get_premium_arrears_count,
    get_dependent_coverage_end_date,
    get_duplicate_claims_count
)

def process_verification(input_data: PolicyVerificationInput) -> PolicyVerificationOutput:
    # Default outputs
    failure_reason = None
    policy_product_code = ""
    premium_payment_mode = "annual"
    policy_start_date = date.today()
    policy_expiry_date = date.today()
    dependent_verified = False

    # === Step 1: Policy existence & status ===
    policy = get_policy(input_data.policy_no)
    if not policy:
        failure_reason = "POLICY_NOT_FOUND"
        return _build_output(input_data, policy_product_code, premium_payment_mode, policy_start_date, policy_expiry_date, dependent_verified, failure_reason)

    policy_product_code = policy['policy_product_code']
    premium_payment_mode = policy['premium_payment_mode']
    policy_start_date = datetime.strptime(policy['policy_start_date'], "%Y-%m-%d").date()
    policy_expiry_date = datetime.strptime(policy['policy_expiry_date'], "%Y-%m-%d").date()

    status = policy['policy_status']
    if status == 'lapsed':
        failure_reason = "POLICY_LAPSED"
        return _build_output(input_data, policy_product_code, premium_payment_mode, policy_start_date, policy_expiry_date, dependent_verified, failure_reason)
    elif status == 'cancelled':
        failure_reason = "POLICY_CANCELLED"
        return _build_output(input_data, policy_product_code, premium_payment_mode, policy_start_date, policy_expiry_date, dependent_verified, failure_reason)
    elif status == 'pending':
        failure_reason = "POLICY_PENDING_ACTIVATION"
        return _build_output(input_data, policy_product_code, premium_payment_mode, policy_start_date, policy_expiry_date, dependent_verified, failure_reason)
    elif status != 'active':
        failure_reason = "UNKNOWN_POLICY_STATUS"
        return _build_output(input_data, policy_product_code, premium_payment_mode, policy_start_date, policy_expiry_date, dependent_verified, failure_reason)

    # === Step 2: Coverage window ===
    incident = input_data.incident_date
    if incident < policy_start_date:
        failure_reason = "INCIDENT_BEFORE_POLICY_START"
        return _build_output(input_data, policy_product_code, premium_payment_mode, policy_start_date, policy_expiry_date, dependent_verified, failure_reason)
    if incident > policy_expiry_date:
        failure_reason = "OUT_OF_COVERAGE_PERIOD"
        return _build_output(input_data, policy_product_code, premium_payment_mode, policy_start_date, policy_expiry_date, dependent_verified, failure_reason)

    # === Step 3: Identity match ===
    member = get_policy_member(
        input_data.policy_no,
        input_data.id_document_type.value,
        input_data.id_document_no
    )
    if not member:
        failure_reason = "IDENTITY_MISMATCH"
        return _build_output(input_data, policy_product_code, premium_payment_mode, policy_start_date, policy_expiry_date, dependent_verified, failure_reason)

    relationship = member['relationship']
    dependent_status = member['dependent_status']
    member_id = member['member_id']

    # === Step 4: Dependent eligibility ===
    if relationship != 'self':
        if dependent_status in ['terminated', 'suspended']:
            failure_reason = "DEPENDENT_NOT_ELIGIBLE"
            return _build_output(input_data, policy_product_code, premium_payment_mode, policy_start_date, policy_expiry_date, dependent_verified, failure_reason)

        dep_end_str = get_dependent_coverage_end_date(input_data.policy_no, member_id)
        if dep_end_str:
            dep_end = datetime.strptime(dep_end_str, "%Y-%m-%d").date()
            if dep_end < incident:
                failure_reason = "DEPENDENT_COVERAGE_EXPIRED"
                return _build_output(input_data, policy_product_code, premium_payment_mode, policy_start_date, policy_expiry_date, dependent_verified, failure_reason)
        dependent_verified = True
    else:
        dependent_verified = True

    # === Step 5: Premium arrears ===
    arrears = get_premium_arrears_count(input_data.policy_no, incident)
    if arrears > 0:
        failure_reason = "UNPAID_PREMIUMS"
        return _build_output(input_data, policy_product_code, premium_payment_mode, policy_start_date, policy_expiry_date, dependent_verified, failure_reason)

    # === Step 6: Duplicate claim check ===
    dup_count = get_duplicate_claims_count(input_data.policy_no, incident, input_data.claim_type.value)
    if dup_count > 0:
        failure_reason = "DUPLICATE_CLAIM"
        return _build_output(input_data, policy_product_code, premium_payment_mode, policy_start_date, policy_expiry_date, dependent_verified, failure_reason)

    # === All checks passed ===
    return _build_output(input_data, policy_product_code, premium_payment_mode, policy_start_date, policy_expiry_date, dependent_verified, None)


def _build_output(
    input_data: PolicyVerificationInput,
    policy_product_code: str,
    premium_payment_mode: str,
    policy_start_date: date,
    policy_expiry_date: date,
    dependent_verified: bool,
    failure_reason: str = None
) -> PolicyVerificationOutput:
    return PolicyVerificationOutput(
        claim_reference_draft=input_data.claim_reference_draft,
        policy_no=input_data.policy_no,
        claimant_name=input_data.claimant_name,
        claim_type=input_data.claim_type,
        incident_date=input_data.incident_date,
        claim_amount_requested=input_data.claim_amount_requested,
        provider_name=input_data.provider_name,
        provider_registration=input_data.provider_registration,
        document_summary=input_data.document_summary,
        policy_product_code=policy_product_code,
        premium_payment_mode=premium_payment_mode,
        policy_start_date=policy_start_date,
        policy_expiry_date=policy_expiry_date,
        dependent_verified=dependent_verified,
        policy_verified=(failure_reason is None),
        verification_failure=failure_reason,
        verification_timestamp=datetime.now(timezone.utc)
    )
