from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from app.intake.schemas import DocumentSummary, ClaimType, IdDocumentType, ClaimantRelationship
from enum import Enum

class PremiumPaymentMode(str, Enum):
    monthly = "monthly"
    quarterly = "quarterly"
    annual = "annual"

class PolicyVerificationInput(BaseModel):
    claim_reference_draft: str
    policy_no: str
    claimant_name: str
    id_document_type: IdDocumentType
    id_document_no: str
    date_of_birth: date
    claimant_relationship: ClaimantRelationship
    claim_type: ClaimType
    incident_date: date
    claim_amount_requested: float
    document_summary: DocumentSummary
    provider_name: str
    provider_registration: str

class PolicyVerificationOutput(BaseModel):
    claim_reference_draft: str
    policy_no: str
    claimant_name: str
    claim_type: ClaimType
    incident_date: date
    claim_amount_requested: float
    provider_name: str
    provider_registration: str
    document_summary: DocumentSummary
    policy_verified: bool
    verification_failure: Optional[str] = None
    policy_start_date: date
    policy_expiry_date: date
    policy_product_code: str
    premium_payment_mode: PremiumPaymentMode
    dependent_verified: bool
    verification_timestamp: datetime
