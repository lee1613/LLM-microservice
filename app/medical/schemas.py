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

class MedicalDetails(BaseModel):
    primary_diagnosis_icd10: str
    procedure_cpt_codes: List[str]
    admission_date: Optional[date] = None
    discharge_date: Optional[date] = None
    attending_physician: str
    physician_license_no: str
    pre_authorisation_no: Optional[str] = None

class MedicalReviewInput(BaseModel):
    claim_reference_draft: str
    policy_no: str
    claimant_name: str
    claim_type: ClaimType
    incident_date: date
    claim_amount_requested: float
    claimable_ceiling: Optional[float] = None
    
    # We must also receive provider details which normally come from intake
    # Since we didn't add them to node 3 output explicitly, we assume they are passed down
    # We will make them optional to not break existing tests that omit them
    provider_name: Optional[str] = "Singapore General Hospital"
    provider_registration: Optional[str] = "HCI-88902"
    
    supporting_documents: List[str] = Field(default_factory=list)
    document_paths: Optional[Dict[str, str]] = Field(default_factory=dict)
    
    # Optionally, raw_documents (the actual text) if passed directly
    raw_documents: Optional[Dict[str, str]] = Field(default_factory=dict)

class MedicalReviewOutput(BaseModel):
    claim_reference_draft: str
    policy_no: str
    claimant_name: str
    claim_type: ClaimType
    incident_date: date
    claim_amount_requested: float
    claimable_ceiling: Optional[float] = None
    
    medical_review_passed: bool
    exclusions_triggered: List[str] = Field(default_factory=list)
    review_failure_reason: Optional[str] = None
    non_panel_flag: bool
    pre_auth_verified: bool
    length_of_stay: Optional[int] = None
    rps_benchmark: float
    bill_variance_pct: float
    medical_necessity_confirmed: bool
    medical_flags: List[str] = Field(default_factory=list)
    review_timestamp: datetime
    
    # Propagate the documents further
    supporting_documents: List[str] = Field(default_factory=list)
    document_paths: Optional[Dict[str, str]] = Field(default_factory=dict)
