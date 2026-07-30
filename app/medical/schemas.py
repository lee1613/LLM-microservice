from datetime import date, datetime

from pydantic import BaseModel

from app.intake.schemas import ClaimType, DocumentSummary


class CptCodeAssessment(BaseModel):
    cpt_code: str
    valid: bool
    plausible: bool
    reasoning: str

class MedicalReviewInput(BaseModel):
    claim_reference_draft: str
    policy_no: str
    claimant_name: str
    claim_type: ClaimType
    incident_date: date
    claim_amount_requested: float
    claimable_ceiling: float
    policy_product_code: str
    provider_name: str
    provider_registration: str
    document_summary: DocumentSummary

class MedicalReviewOutput(BaseModel):
    claim_reference_draft: str
    policy_no: str
    claimant_name: str
    claim_type: ClaimType
    incident_date: date
    claim_amount_requested: float
    claimable_ceiling: float
    policy_product_code: str
    provider_registration: str
    document_summary: DocumentSummary
    medical_review_passed: bool
    review_failure_reason: str | None = None
    non_panel_flag: bool
    accreditation_claim: str
    physician_licence_claim: str
    coding_assessment: list[CptCodeAssessment]
    pre_auth_verified: bool
    length_of_stay: int | None = None
    rps_benchmark: float
    bill_variance_pct: float
    medical_necessity_confirmed: bool
    medical_flags: list[str]
    medical_review_notes: str
    review_timestamp: datetime
