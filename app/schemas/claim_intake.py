from pydantic import BaseModel, EmailStr, Field
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

class DocumentType(str, Enum):
    medical_bill = "medical_bill"
    discharge_summary = "discharge_summary"
    referral_letter = "referral_letter"
    prescription = "prescription"
    lab_report = "lab_report"
    imaging_report = "imaging_report"
    specialist_memo = "specialist_memo"
    pre_auth_approval = "pre_auth_approval"

class ClaimIntakeInput(BaseModel):
    """Schema A: Input"""
    policy_no: str
    policy_holder: str
    claimant_name: str
    claimant_relationship: ClaimantRelationship
    id_document_type: IdDocumentType
    id_document_no: str
    date_of_birth: date
    claim_date: date
    incident_date: date
    claim_type: ClaimType
    provider_name: str
    provider_registration: str
    claim_amount_requested: float
    supporting_documents: List[str]
    claimant_contact_email: str
    claimant_contact_phone: str

class ClaimIntakeOutput(BaseModel):
    """Schema B: Output"""
    claim_reference_draft: str
    policy_no: str
    claimant_name: str
    claim_type: ClaimType
    incident_date: date
    claim_date: date
    claim_amount_requested: float
    intake_accepted: bool
    rejection_reason: Optional[str] = None
    missing_documents: List[str]
    intake_timestamp: datetime
