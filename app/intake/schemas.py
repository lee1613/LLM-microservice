from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import List, Optional
from enum import Enum

class ClaimantRelationship(str, Enum):
    self = "self"
    spouse = "spouse"
    child = "child"
    parent = "parent"
    sibling = "sibling"
    other_dependent = "other_dependent"

class IdDocumentType(str, Enum):
    nric = "nric"
    passport = "passport"
    fin = "fin"
    birth_certificate = "birth_certificate"

class ClaimType(str, Enum):
    hospitalisation = "hospitalisation"
    outpatient = "outpatient"
    surgical = "surgical"
    dental = "dental"
    vision = "vision"
    maternity = "maternity"
    mental_health = "mental_health"
    emergency = "emergency"

class ClaimIntakeInput(BaseModel):
    """Schema A: Input"""
    policy_no: str
    claimant_name: str
    claimant_relationship: ClaimantRelationship
    id_document_type: IdDocumentType
    id_document_no: str
    date_of_birth: date
    incident_date: date
    claim_date: date
    claim_type: ClaimType
    claim_amount_requested: float
    supporting_documents: List[str]
    scanned_files: List[str]
    provider_name: str
    provider_registration: str

class ItemisedCharge(BaseModel):
    description: str
    quantity: int
    unit_price: float

class DocumentSummary(BaseModel):
    total_billed_amount: Optional[float] = None
    itemised_charges: List[ItemisedCharge] = Field(default_factory=list)
    primary_diagnosis_icd10: Optional[str] = None
    procedure_cpt_codes: List[str] = Field(default_factory=list)
    symptom_onset_date: Optional[date] = None
    admission_date: Optional[date] = None
    discharge_date: Optional[date] = None
    attending_physician: Optional[str] = None
    physician_license_no: Optional[str] = None
    pre_authorisation_no: Optional[str] = None
    provider_name_on_bill: Optional[str] = None
    extraction_warnings: List[str] = Field(default_factory=list)
    summary_narrative: Optional[str] = None

class ClaimIntakeOutput(BaseModel):
    """Schema B: Output"""
    claim_reference_draft: str
    policy_no: str
    claimant_name: str
    id_document_type: IdDocumentType
    id_document_no: str
    date_of_birth: date
    claimant_relationship: ClaimantRelationship
    claim_type: ClaimType
    incident_date: date
    claim_date: date
    claim_amount_requested: float
    provider_name: str
    provider_registration: str
    intake_accepted: bool
    rejection_reason: Optional[str] = None
    missing_documents: List[str] = Field(default_factory=list)
    intake_timestamp: datetime
    document_summary: Optional[DocumentSummary] = None
