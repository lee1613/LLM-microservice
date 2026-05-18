"""
Node 6 — Disbursement Agent (fully deterministic, no LLM)

Steps:
  1. Payment channel validation (bank format / provider lookup)
  2. Anti-fraud payee cross-check
  3. Claim reference finalisation (atomic sequence increment)
  4. Ledger writes (deductible_ledger + claim_utilisation)
  5. Disbursement record & remarks
"""
import unicodedata
import re
from datetime import datetime, timezone, timedelta, date

from app.disbursement.schemas import (
    DisbursementInput, DisbursementOutput,
    DisbursementStatus, PaymentMode
)
from app.disbursement.tools import (
    validate_bank_account, get_provider_bank_details,
    finalise_claim_reference, write_ledger_entries,
    SETTLEMENT_DAYS
)


def _normalise(name: str) -> str:
    """Case-fold + collapse whitespace for payee name comparison."""
    n = unicodedata.normalize('NFKC', name).casefold()
    return re.sub(r'\s+', ' ', n).strip()


def _add_business_days(start: date, days: int) -> date:
    """Add calendar days (contract uses calendar days, not business days)."""
    return start + timedelta(days=days)


def _mask_account(account_no: str) -> str:
    """Mask all but last 4 digits."""
    if not account_no:
        return "****"
    return '*' * max(0, len(account_no) - 4) + account_no[-4:]


def process_disbursement(input_data: DisbursementInput) -> DisbursementOutput:
    now = datetime.now(timezone.utc)
    processing_date = now.date()
    benefit_year = input_data.incident_date.year
    pd = input_data.payment_details
    mode = pd.payment_mode

    # ── Approval gate ─────────────────────────────────────────────────────────
    if input_data.adjudication_status != 'approved':
        raise ValueError(
            f"ZERO_BENEFIT_NO_DISBURSEMENT: adjudication_status is "
            f"'{input_data.adjudication_status}', not 'approved'. Disbursement halted."
        )

    # ── Step 1: Payment channel validation ────────────────────────────────────
    resolved_bank_account = pd.bank_account_no  # may be overridden for provider_direct
    resolved_bank_name    = pd.bank_name
    resolved_payee_name   = pd.payee_name
    provider_registered_name = None

    if mode in (PaymentMode.direct_credit, PaymentMode.giro):
        if not pd.bank_name or not pd.bank_account_no or not pd.bank_branch_code:
            raise ValueError("INVALID_BANK_DETAILS: bank_name, bank_account_no, bank_branch_code are required.")
        if not re.match(r'^\d{3}$', pd.bank_branch_code):
            raise ValueError(f"INVALID_BANK_DETAILS: bank_branch_code '{pd.bank_branch_code}' must be 3 digits.")
        if not validate_bank_account(pd.bank_name, pd.bank_account_no):
            raise ValueError(
                f"INVALID_BANK_DETAILS: account '{pd.bank_account_no}' fails format check for bank '{pd.bank_name}'."
            )

    elif mode == PaymentMode.cheque:
        if not pd.payee_name:
            raise ValueError("INVALID_BANK_DETAILS: payee_name is required for cheque payment.")

    elif mode == PaymentMode.provider_direct:
        provider_rec = get_provider_bank_details(input_data.provider_registration)
        if not provider_rec or not provider_rec.get('bank_account_no'):
            raise ValueError(
                f"PROVIDER_BANK_DETAILS_NOT_FOUND: No bank details found for provider "
                f"'{input_data.provider_registration}'."
            )
        resolved_bank_account = provider_rec['bank_account_no']
        resolved_bank_name    = provider_rec['bank_name']
        provider_registered_name = provider_rec['provider_name']

    # ── Step 2: Anti-fraud payee cross-check ──────────────────────────────────
    disbursement_status = DisbursementStatus.disbursed
    fraud_flag = False

    if mode in (PaymentMode.direct_credit, PaymentMode.giro, PaymentMode.cheque):
        if _normalise(pd.payee_name) != _normalise(input_data.claimant_name):
            disbursement_status = DisbursementStatus.pending_manual_review
            fraud_flag = True
    elif mode == PaymentMode.provider_direct and provider_registered_name:
        if _normalise(pd.payee_name) != _normalise(provider_registered_name):
            disbursement_status = DisbursementStatus.pending_manual_review
            fraud_flag = True

    if fraud_flag:
        # Halt — return pending_manual_review without ledger writes
        return DisbursementOutput(
            claim_reference_no=input_data.claim_reference_draft,  # draft retained, not finalised
            policy_no=input_data.policy_no,
            claimant_name=input_data.claimant_name,
            claim_type=input_data.claim_type,
            disbursement_status=DisbursementStatus.pending_manual_review,
            net_payable=input_data.net_payable,
            claimant_liability=input_data.claimant_liability,
            payment_mode=mode,
            payee_name=pd.payee_name,
            disbursement_date=processing_date,
            incident_date=input_data.incident_date,
            remarks=(
                f"Disbursement halted: payee name '{pd.payee_name}' does not match "
                f"expected name '{input_data.claimant_name if mode != PaymentMode.provider_direct else provider_registered_name}'. "
                f"Claim {input_data.claim_reference_draft} referred for manual review."
            ),
            processing_timestamp=now,
        )

    # ── Step 3: Claim reference finalisation ──────────────────────────────────
    claim_reference_no = finalise_claim_reference(input_data.claim_reference_draft, benefit_year)

    # ── Step 4: Ledger writes ─────────────────────────────────────────────────
    posted_at = now.isoformat()
    write_ledger_entries(
        policy_no=input_data.policy_no,
        claim_type=input_data.claim_type.value,
        benefit_year=benefit_year,
        claim_reference_no=claim_reference_no,
        net_payable=input_data.net_payable,
        deductible_applied=input_data.deductible_applied_this_claim,
        posted_at=posted_at,
    )

    # ── Step 5: Disbursement record & remarks ─────────────────────────────────
    settlement_days  = SETTLEMENT_DAYS[mode.value]
    disbursement_date = _add_business_days(processing_date, settlement_days)

    # Mask bank account for output
    masked_account = _mask_account(resolved_bank_account or "")
    payee_display = (
        f"{pd.payee_name} ({resolved_bank_name} {masked_account})"
        if resolved_bank_account and mode != PaymentMode.cheque
        else pd.payee_name
    )

    # Build remarks
    mode_label = {
        PaymentMode.direct_credit:   "direct credit",
        PaymentMode.giro:            "GIRO",
        PaymentMode.cheque:          "cheque",
        PaymentMode.provider_direct: "provider-direct payment",
    }[mode]

    adjudication_context = ""
    if "NON_PANEL" in input_data.adjudication_notes.upper() or "non-panel" in input_data.adjudication_notes.lower():
        adjudication_context = " Non-panel provider discount was applied."
    elif "CO-INSURANCE CAP" in input_data.adjudication_notes.upper():
        adjudication_context = " Co-insurance cap was applied."

    remarks = (
        f"Claim {claim_reference_no} approved. SGD {input_data.net_payable:.2f} to be disbursed via "
        f"{mode_label} by {disbursement_date.strftime('%d %b %Y')} (T+{settlement_days}).{adjudication_context} "
        f"Claimant liability: SGD {input_data.claimant_liability:.2f}."
    )

    return DisbursementOutput(
        claim_reference_no=claim_reference_no,
        policy_no=input_data.policy_no,
        claimant_name=input_data.claimant_name,
        claim_type=input_data.claim_type,
        disbursement_status=DisbursementStatus.disbursed,
        net_payable=input_data.net_payable,
        claimant_liability=input_data.claimant_liability,
        payment_mode=mode,
        payee_name=payee_display,
        disbursement_date=disbursement_date,
        incident_date=input_data.incident_date,
        remarks=remarks,
        processing_timestamp=now,
    )
