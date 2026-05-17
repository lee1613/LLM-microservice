from datetime import datetime, timezone
from app.eligibility.schemas import EligibilityInput, EligibilityOutput
from app.eligibility.tools import (
    get_policy_start_date,
    get_plan_benefits,
    get_annual_utilised,
    get_lifetime_utilised
)

def get_server_timestamp() -> datetime:
    return datetime.now(timezone.utc)

def process_eligibility(input_data: EligibilityInput) -> EligibilityOutput:
    # Outputs to populate
    eligible = False
    failure_reason = None
    claim_type_covered = False
    waiting_period_satisfied = False
    waiting_period_days = None
    annual_limit = None
    annual_utilised = None
    annual_limit_remaining = None
    per_claim_limit = None
    claimable_ceiling = None
    
    incident = input_data.incident_date
    benefit_year = incident.year
    
    # Step 1: Coverage type inclusion
    benefits = get_plan_benefits(input_data.policy_product_code, input_data.claim_type.value)
    if not benefits or not benefits['covered']:
        failure_reason = 'BENEFIT_NOT_IN_PLAN'
        return _build_output(input_data, False, failure_reason, False, False, None, None, None, None, None, None)
        
    claim_type_covered = True
    waiting_period_days = benefits['waiting_period_days']
    annual_limit = benefits['annual_limit']
    per_claim_limit = benefits['per_claim_limit']
    lifetime_limit = benefits['lifetime_limit']
    
    # Step 2: Waiting period check
    p_start_str = get_policy_start_date(input_data.policy_no)
    if p_start_str:
        p_start = datetime.strptime(p_start_str, "%Y-%m-%d").date()
        days_since_start = (incident - p_start).days
        if days_since_start < waiting_period_days:
            failure_reason = 'WAITING_PERIOD_NOT_MET'
            return _build_output(
                input_data, False, failure_reason, claim_type_covered, False,
                waiting_period_days, annual_limit, None, None, per_claim_limit, None
            )
            
    waiting_period_satisfied = True
    
    # Step 3: Annual benefit limit check
    annual_utilised = get_annual_utilised(input_data.policy_no, input_data.claim_type.value, benefit_year)
    annual_limit_remaining = annual_limit - annual_utilised
    if annual_limit_remaining <= 0:
        annual_limit_remaining = 0
        failure_reason = 'ANNUAL_LIMIT_EXHAUSTED'
        return _build_output(
            input_data, False, failure_reason, claim_type_covered, waiting_period_satisfied,
            waiting_period_days, annual_limit, annual_utilised, annual_limit_remaining, per_claim_limit, 0
        )
        
    # Step 4: Per-claim limit check
    claimable_ceiling = min(input_data.claim_amount_requested, per_claim_limit, annual_limit_remaining)
    
    # Step 5: Lifetime benefit limit check
    lifetime_utilised = get_lifetime_utilised(input_data.policy_no)
    if lifetime_utilised >= lifetime_limit:
        failure_reason = 'LIFETIME_LIMIT_EXHAUSTED'
        return _build_output(
            input_data, False, failure_reason, claim_type_covered, waiting_period_satisfied,
            waiting_period_days, annual_limit, annual_utilised, annual_limit_remaining, per_claim_limit, claimable_ceiling
        )
        
    # Step 6: Eligibility result (all passed)
    return _build_output(
        input_data, True, None, claim_type_covered, waiting_period_satisfied,
        waiting_period_days, annual_limit, annual_utilised, annual_limit_remaining, per_claim_limit, claimable_ceiling
    )

def _build_output(
    input_data: EligibilityInput,
    eligible: bool,
    failure_reason: str,
    claim_type_covered: bool,
    waiting_period_satisfied: bool,
    waiting_period_days: int,
    annual_limit: float,
    annual_utilised: float,
    annual_limit_remaining: float,
    per_claim_limit: float,
    claimable_ceiling: float
) -> EligibilityOutput:
    return EligibilityOutput(
        claim_reference_draft=input_data.claim_reference_draft,
        policy_no=input_data.policy_no,
        claimant_name=input_data.claimant_name,
        claim_type=input_data.claim_type,
        incident_date=input_data.incident_date,
        claim_amount_requested=input_data.claim_amount_requested,
        eligible=eligible,
        eligibility_failure_reason=failure_reason,
        claim_type_covered=claim_type_covered,
        waiting_period_satisfied=waiting_period_satisfied,
        waiting_period_days=waiting_period_days,
        annual_limit=annual_limit,
        annual_utilised=annual_utilised,
        annual_limit_remaining=annual_limit_remaining,
        per_claim_limit=per_claim_limit,
        claimable_ceiling=claimable_ceiling,
        eligibility_timestamp=get_server_timestamp(),
        supporting_documents=input_data.supporting_documents,
        document_paths=input_data.document_paths
    )
