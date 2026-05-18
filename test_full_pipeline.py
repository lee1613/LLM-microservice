"""
Full end-to-end pipeline test: B001–B005 sequential.

Expected outcomes:
  B001 — GOLD hospitalisation (panel SGH)        → approved   (N1–N6 pass)
  B002 — SILVER outpatient (non-panel clinic)    → approved   (N1–N6 pass)
  B003 — SILVER maternity (panel KKH)            → FAIL at N3 (maternity waiting period)
  B004 — BRONZE surgical (non-panel Novena)      → approved   (N1–N6 pass)
  B005 — GOLD emergency (duplicate claim)        → FAIL at N2 (duplicate claim)
"""
import json
import asyncio
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

from app.intake.schemas import ClaimIntakeInput
from app.intake.agent import process_claim_intake
from app.verification.schemas import PolicyVerificationInput
from app.verification.agent import process_verification
from app.eligibility.schemas import EligibilityCheckInput
from app.eligibility.agent import process_eligibility
from app.medical.schemas import MedicalReviewInput
from app.medical.agent import process_medical_review
from app.adjudication.schemas import AdjudicationInput
from app.adjudication.agent import process_adjudication
from app.disbursement.schemas import DisbursementInput, PaymentDetails, PaymentMode
from app.disbursement.agent import process_disbursement

BASE = r"c:\Users\Lee023\OneDrive - National University of Singapore\Desktop\Project\LLM-microservice\data\health-insurance-claim\synthetic data"

# Payment details per case — provider_direct uses registered provider name as payee
PAYMENT = {
    "B001": PaymentDetails(
        payment_mode=PaymentMode.provider_direct,
        payee_name="Singapore General Hospital",       # MOH-HOSP-00142
    ),
    "B002": PaymentDetails(
        payment_mode=PaymentMode.direct_credit,
        payee_name="Lim Kai Xuan",
        bank_name="OCBC",
        bank_account_no="712345678",
        bank_branch_code="501",
    ),
    "B003": None,   # Expected to fail at N3 — no disbursement needed
    "B004": PaymentDetails(
        payment_mode=PaymentMode.direct_credit,
        payee_name="Ahmad Zulkifli bin Hassan",
        bank_name="DBS",
        bank_account_no="0012345678",
        bank_branch_code="007",
    ),
    "B005": None,   # Expected to fail at N2 — no disbursement needed
}


async def run_case(case_id: str, description: str):
    fname = f"claim_{case_id}_full_pipeline.json"
    data  = json.load(open(os.path.join(BASE, fname), encoding='utf-8'))
    pd    = PAYMENT[case_id]

    print(f"\n{'='*70}")
    print(f"  {case_id} — {description}")
    print(f"{'='*70}")

    # ── Node 1: Intake ──────────────────────────────────────────────────────
    n1 = await process_claim_intake(ClaimIntakeInput(**data["stage_1_intake"]["_input"]))
    _report("N1 Intake", n1.intake_accepted, n1.rejection_reason,
            f"ref={n1.claim_reference_draft} | policy={n1.policy_no}")
    if not n1.intake_accepted:
        return

    # ── Node 2: Policy Verification ─────────────────────────────────────────
    n2 = process_verification(PolicyVerificationInput(
        claim_reference_draft=n1.claim_reference_draft, policy_no=n1.policy_no,
        claimant_name=n1.claimant_name, id_document_type=n1.id_document_type,
        id_document_no=n1.id_document_no, date_of_birth=n1.date_of_birth,
        claimant_relationship=n1.claimant_relationship, claim_type=n1.claim_type,
        incident_date=n1.incident_date, claim_amount_requested=n1.claim_amount_requested,
        document_summary=n1.document_summary, provider_name=n1.provider_name,
        provider_registration=n1.provider_registration,
    ))
    _report("N2 Verification", n2.policy_verified, n2.verification_failure,
            f"product={n2.policy_product_code} | start={n2.policy_start_date}")
    if not n2.policy_verified:
        return

    # ── Node 3: Eligibility ──────────────────────────────────────────────────
    n3 = process_eligibility(EligibilityCheckInput(
        claim_reference_draft=n2.claim_reference_draft, policy_no=n2.policy_no,
        claimant_name=n2.claimant_name, claim_type=n2.claim_type,
        incident_date=n2.incident_date, claim_amount_requested=n2.claim_amount_requested,
        policy_product_code=n2.policy_product_code, policy_start_date=n2.policy_start_date,
        dependent_verified=n2.dependent_verified, provider_name=n2.provider_name,
        provider_registration=n2.provider_registration, document_summary=n2.document_summary,
    ))
    _report("N3 Eligibility", n3.eligible, n3.eligibility_failure_reason,
            f"ceiling=SGD {n3.claimable_ceiling}")
    if not n3.eligible:
        return

    # ── Node 4: Medical Review ───────────────────────────────────────────────
    n4 = process_medical_review(MedicalReviewInput(
        claim_reference_draft=n3.claim_reference_draft, policy_no=n3.policy_no,
        claimant_name=n3.claimant_name, claim_type=n3.claim_type,
        incident_date=n3.incident_date, claim_amount_requested=n3.claim_amount_requested,
        claimable_ceiling=n3.claimable_ceiling, policy_product_code=n3.policy_product_code,
        provider_name=n3.provider_name, provider_registration=n3.provider_registration,
        document_summary=n3.document_summary,
    ))
    _report("N4 Medical Review", n4.medical_review_passed, n4.review_failure_reason,
            f"flags={n4.medical_flags} | RPS=SGD {n4.rps_benchmark} | LOS={n4.length_of_stay}d")
    if not n4.medical_review_passed:
        return

    # ── Node 5: Adjudication ────────────────────────────────────────────────
    n5 = process_adjudication(AdjudicationInput(
        claim_reference_draft=n4.claim_reference_draft, policy_no=n4.policy_no,
        claimant_name=n4.claimant_name, claim_type=n4.claim_type,
        incident_date=n4.incident_date, claim_amount_requested=n4.claim_amount_requested,
        claimable_ceiling=n3.claimable_ceiling, rps_benchmark=n4.rps_benchmark,
        non_panel_flag=n4.non_panel_flag, policy_product_code=n4.policy_product_code,
        provider_registration=n4.provider_registration,
        medical_flags=n4.medical_flags, medical_review_notes=n4.medical_review_notes,
    ))
    _report("N5 Adjudication", n5.adjudication_status.value == 'approved',
            None if n5.adjudication_status.value == 'approved' else n5.adjudication_status.value,
            f"base=SGD {n5.adjudication_base:.2f} | ded=SGD {n5.deductible_applied_this_claim:.2f} "
            f"| copay=SGD {n5.co_pay_amount:.2f} | coins=SGD {n5.co_insurance_amount:.2f} "
            f"| NET=SGD {n5.net_payable:.2f} | liability=SGD {n5.claimant_liability:.2f}")
    print(f"        Notes: {n5.adjudication_notes}")
    if n5.adjudication_status.value != 'approved':
        return

    # ── Node 6: Disbursement ────────────────────────────────────────────────
    if pd is None:
        print("  [N6] Skipped — no payment details provided")
        return

    n6 = process_disbursement(DisbursementInput(
        claim_reference_draft=n5.claim_reference_draft, policy_no=n5.policy_no,
        claimant_name=n5.claimant_name, claim_type=n5.claim_type,
        net_payable=n5.net_payable, adjudication_status=n5.adjudication_status.value,
        claimant_liability=n5.claimant_liability, adjudication_notes=n5.adjudication_notes,
        deductible_applied_this_claim=n5.deductible_applied_this_claim,
        incident_date=n5.incident_date, provider_registration=n5.provider_registration,
        payment_details=pd,
    ))
    _report("N6 Disbursement", n6.disbursement_status.value == 'disbursed',
            None if n6.disbursement_status.value == 'disbursed' else n6.disbursement_status.value,
            f"ref={n6.claim_reference_no} | mode={n6.payment_mode.value} | date={n6.disbursement_date}")
    print(f"        Payee  : {n6.payee_name}")
    print(f"        Remarks: {n6.remarks}")


def _report(node: str, passed: bool, failure: str | None, detail: str):
    icon = "✓" if passed else "✗"
    status = "PASS" if passed else f"FAIL [{failure}]"
    print(f"  [{icon}] {node:<20} {status}")
    print(f"        {detail}")


async def main():
    cases = [
        ("B001", "GOLD hospitalisation — panel SGH → provider_direct"),
        ("B002", "SILVER outpatient — non-panel clinic → direct_credit"),
        ("B003", "SILVER maternity — panel KKH → expect N3 FAIL (waiting period)"),
        ("B004", "BRONZE surgical — non-panel Novena → direct_credit"),
        ("B005", "GOLD emergency — DUPLICATE CLAIM → expect N2 FAIL"),
    ]
    for case_id, desc in cases:
        await run_case(case_id, desc)

    print(f"\n{'='*70}")
    print("  Pipeline run complete.")
    print(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(main())
