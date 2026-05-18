from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from enum import Enum
from app.intake.schemas import DocumentSummary, ClaimType
from app.verification.schemas import PremiumPaymentMode

class WaitingPeriodBasis(str, Enum):
    symptom_onset = "symptom_onset"
    incident_date = "incident_date"

class EligibilityCheckInput(BaseModel):
    claim_reference_draft: str
    policy_no: str
    claimant_name: str
    claim_type: ClaimType
    incident_date: date
    claim_amount_requested: float
    policy_product_code: str
    policy_start_date: date
    dependent_verified: bool
    provider_name: str
    provider_registration: str
    document_summary: DocumentSummary

class EligibilityCheckOutput(BaseModel):
    claim_reference_draft: str
    policy_no: str
    claimant_name: str
    claim_type: ClaimType
    incident_date: date
    claim_amount_requested: float
    policy_product_code: str
    provider_name: str
    provider_registration: str
    document_summary: DocumentSummary
    eligible: bool
    eligibility_failure_reason: Optional[str] = None
    waiting_period_satisfied: bool
    waiting_period_days: int
    waiting_period_basis: WaitingPeriodBasis
    annual_limit: float
    annual_utilised: float
    annual_limit_remaining: float
    per_claim_limit: float
    claimable_ceiling: float
    exclusions_triggered: List[str]
    eligibility_rationale: str
    eligibility_timestamp: datetime
