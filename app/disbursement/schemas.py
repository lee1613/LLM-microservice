from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from enum import Enum
from app.intake.schemas import ClaimType


class PaymentMode(str, Enum):
    direct_credit    = 'direct_credit'
    cheque           = 'cheque'
    giro             = 'giro'
    provider_direct  = 'provider_direct'


class DisbursementStatus(str, Enum):
    disbursed             = 'disbursed'
    pending_manual_review = 'pending_manual_review'


class PaymentDetails(BaseModel):
    payment_mode:     PaymentMode
    payee_name:       str
    bank_name:        Optional[str] = None
    bank_account_no:  Optional[str] = None
    bank_branch_code: Optional[str] = None


class DisbursementInput(BaseModel):
    """Node 6 input — fed directly from Node 5 (AdjudicationOutput)."""
    claim_reference_draft:       str
    policy_no:                   str
    claimant_name:               str
    claim_type:                  ClaimType
    net_payable:                 float
    adjudication_status:         str     # must be 'approved'
    claimant_liability:          float
    adjudication_notes:          str
    deductible_applied_this_claim: float
    incident_date:               date
    provider_registration:       str
    payment_details:             PaymentDetails


class DisbursementOutput(BaseModel):
    """Node 6 output — final disbursement record."""
    claim_reference_no:   str
    policy_no:            str
    claimant_name:        str
    claim_type:           ClaimType
    disbursement_status:  DisbursementStatus
    net_payable:          float
    claimant_liability:   float
    payment_mode:         PaymentMode
    payee_name:           str           # bank account masked
    disbursement_date:    date
    incident_date:        date
    remarks:              str
    processing_timestamp: datetime
