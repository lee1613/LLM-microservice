from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from enum import Enum
from app.intake.schemas import ClaimType


class AdjudicationStatus(str, Enum):
    approved = 'approved'
    zero_benefit = 'zero_benefit'


class AdjudicationInput(BaseModel):
    """Node 5 input — fed directly from Node 4 (MedicalReviewOutput)."""
    claim_reference_draft: str
    policy_no: str
    claimant_name: str
    claim_type: ClaimType
    incident_date: date
    claim_amount_requested: float
    claimable_ceiling: float
    rps_benchmark: float
    non_panel_flag: bool
    policy_product_code: str
    provider_registration: str   # passthrough → Node 6
    medical_flags: List[str]
    medical_review_notes: str


class AdjudicationOutput(BaseModel):
    """Node 5 output — financial adjudication result."""
    claim_reference_draft: str
    policy_no: str
    claimant_name: str
    claim_type: ClaimType
    incident_date: date
    claim_amount_requested: float
    provider_registration: str   # passthrough → Node 6
    adjudication_base: float
    deductible_applied_this_claim: float
    co_pay_amount: float
    co_insurance_amount: float
    net_payable: float
    claimant_liability: float
    adjudication_status: AdjudicationStatus
    adjudication_notes: str      # ≤80-word LLM-generated rationale
    adjudication_timestamp: datetime
