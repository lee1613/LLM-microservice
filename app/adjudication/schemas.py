from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import date, datetime
from enum import Enum


class ClaimType(str, Enum):
    hospitalisation = 'hospitalisation'
    outpatient = 'outpatient'
    maternity = 'maternity'
    dental = 'dental'
    vision = 'vision'
    surgical = 'surgical'
    emergency = 'emergency'
    mental_health = 'mental_health'


class AdjudicationStatus(str, Enum):
    approved = 'approved'
    zero_benefit = 'zero_benefit'
    rejected = 'rejected'


class AdjudicationInput(BaseModel):
    """Node 5 input — direct passthrough of Node 4 (MedicalReviewOutput) output."""
    claim_reference_draft: str
    policy_no: str
    claimant_name: str
    claim_type: ClaimType
    incident_date: date
    claim_amount_requested: float
    claimable_ceiling: Optional[float] = None
    rps_benchmark: Optional[float] = 0.0
    non_panel_flag: bool = False

    # policy_product_code may not be present (Node 3 drops it in output schema).
    # The agent will re-fetch it from the policies table using policy_no.
    policy_product_code: Optional[str] = None

    # Propagated document metadata
    supporting_documents: List[str] = Field(default_factory=list)
    document_paths: Optional[Dict[str, str]] = Field(default_factory=dict)


class AdjudicationOutput(BaseModel):
    """Node 5 output — financial adjudication result."""
    claim_reference_draft: str
    policy_no: str
    claimant_name: str
    claim_type: ClaimType
    incident_date: date
    claim_amount_requested: float

    # Financial breakdown
    adjudication_base: float
    deductible_applied_this_claim: float
    co_pay_amount: float
    co_insurance_amount: float
    net_payable: float
    claimant_liability: float

    # Decision
    adjudication_status: AdjudicationStatus
    adjudication_notes: str
    adjudication_timestamp: datetime
