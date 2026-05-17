from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import date, datetime
from enum import Enum

class IdDocumentType(str, Enum):
    nric = 'nric'
    fin = 'fin'
    passport = 'passport'
    birth_cert = 'birth_cert'

class Relationship(str, Enum):
    self = 'self'
    spouse = 'spouse'
    child = 'child'
    parent = 'parent'

class ClaimType(str, Enum):
    hospitalisation = 'hospitalisation'
    outpatient = 'outpatient'
    maternity = 'maternity'
    dental = 'dental'
    vision = 'vision'
    surgical = 'surgical'
    emergency = 'emergency'

class PremiumPaymentMode(str, Enum):
    monthly = 'monthly'
    quarterly = 'quarterly'
    annual = 'annual'

class PolicyVerificationInput(BaseModel):
    claim_reference_draft: str
    policy_no: str
    claimant_name: str
    id_document_type: IdDocumentType
    id_document_no: str
    date_of_birth: date
    claimant_relationship: Relationship
    claim_type: ClaimType
    incident_date: date
    claim_amount_requested: float
    supporting_documents: List[str] = Field(default_factory=list)
    document_paths: Optional[Dict[str, str]] = Field(default_factory=dict)

class PolicyVerificationOutput(BaseModel):
    claim_reference_draft: str
    policy_no: str
    claimant_name: str
    claim_type: ClaimType
    incident_date: date
    claim_amount_requested: float
    policy_product_code: str
    premium_payment_mode: PremiumPaymentMode
    policy_start_date: date
    policy_expiry_date: date
    dependent_verified: bool
    policy_verified: bool
    verification_failure: Optional[str] = None
    verification_timestamp: datetime
    supporting_documents: List[str] = Field(default_factory=list)
    document_paths: Optional[Dict[str, str]] = Field(default_factory=dict)
