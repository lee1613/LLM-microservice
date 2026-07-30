from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


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
    supporting_documents: list[str]
    scanned_files: list[str]
    provider_name: str
    provider_registration: str

class ItemisedCharge(BaseModel):
    description: str
    quantity: int
    unit_price: float

class DocumentSummary(BaseModel):
    total_billed_amount: float | None = None
    itemised_charges: list[ItemisedCharge] = Field(default_factory=list)
    primary_diagnosis_icd10: str | None = None
    procedure_cpt_codes: list[str] = Field(default_factory=list)
    symptom_onset_date: date | None = None
    admission_date: date | None = None
    discharge_date: date | None = None
    attending_physician: str | None = None
    physician_license_no: str | None = None
    pre_authorisation_no: str | None = None
    provider_name_on_bill: str | None = None
    extraction_warnings: list[str] = Field(default_factory=list)
    summary_narrative: str | None = None

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
    rejection_reason: str | None = None
    missing_documents: list[str] = Field(default_factory=list)
    intake_timestamp: datetime
    document_summary: DocumentSummary | None = None
    _debug_error: str | None = None
