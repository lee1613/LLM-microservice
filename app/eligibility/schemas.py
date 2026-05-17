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

class EligibilityInput(BaseModel):
    claim_reference_draft: str
    policy_no: str
    claimant_name: str
    claim_type: ClaimType
    incident_date: date
    claim_amount_requested: float
    policy_product_code: str
    dependent_verified: bool
    supporting_documents: List[str] = Field(default_factory=list)
    document_paths: Optional[Dict[str, str]] = Field(default_factory=dict)

class EligibilityOutput(BaseModel):
    claim_reference_draft: str
    policy_no: str
    claimant_name: str
    claim_type: ClaimType
    incident_date: date
    claim_amount_requested: float
    eligible: bool
    eligibility_failure_reason: Optional[str] = None
    claim_type_covered: bool
    waiting_period_satisfied: bool
    waiting_period_days: Optional[int] = None
    annual_limit: Optional[float] = None
    annual_utilised: Optional[float] = None
    annual_limit_remaining: Optional[float] = None
    per_claim_limit: Optional[float] = None
    claimable_ceiling: Optional[float] = None
    eligibility_timestamp: datetime
    supporting_documents: List[str] = Field(default_factory=list)
    document_paths: Optional[Dict[str, str]] = Field(default_factory=dict)
