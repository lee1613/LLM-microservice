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

# Payment details for each test case
PAYMENT_CONFIGS = {
    # B001 — panel hospital → provider_direct payment to SGH
    "B001": PaymentDetails(
        payment_mode=PaymentMode.provider_direct,
        payee_name="Singapore General Hospital",
    ),
    # B004 — non-panel, claimant reimburses themselves via direct credit
    "B004": PaymentDetails(
        payment_mode=PaymentMode.direct_credit,
        payee_name="Ahmad Zulkifli bin Hassan",
        bank_name="DBS",
        bank_account_no="0012345678",
        bank_branch_code="007",
    ),
}

async def run_pipeline(data: dict, label: str, payment_details: PaymentDetails):
    print(f"\n{'='*65}")
    print(f"  {label}")
    print(f"{'='*65}")

    # N1
    n1 = await process_claim_intake(ClaimIntakeInput(**data["stage_1_intake"]["_input"]))
    print(f"[N1] Accepted={n1.intake_accepted}")
    if not n1.intake_accepted: return

    # N2
    n2 = process_verification(PolicyVerificationInput(
        claim_reference_draft=n1.claim_reference_draft, policy_no=n1.policy_no,
        claimant_name=n1.claimant_name, id_document_type=n1.id_document_type,
        id_document_no=n1.id_document_no, date_of_birth=n1.date_of_birth,
        claimant_relationship=n1.claimant_relationship, claim_type=n1.claim_type,
        incident_date=n1.incident_date, claim_amount_requested=n1.claim_amount_requested,
        document_summary=n1.document_summary, provider_name=n1.provider_name,
        provider_registration=n1.provider_registration,
    ))
    print(f"[N2] Verified={n2.policy_verified} | {n2.policy_product_code}")
    if not n2.policy_verified: return

    # N3
    n3 = process_eligibility(EligibilityCheckInput(
        claim_reference_draft=n2.claim_reference_draft, policy_no=n2.policy_no,
        claimant_name=n2.claimant_name, claim_type=n2.claim_type,
        incident_date=n2.incident_date, claim_amount_requested=n2.claim_amount_requested,
        policy_product_code=n2.policy_product_code, policy_start_date=n2.policy_start_date,
        dependent_verified=n2.dependent_verified, provider_name=n2.provider_name,
        provider_registration=n2.provider_registration, document_summary=n2.document_summary,
    ))
    print(f"[N3] Eligible={n3.eligible} | Ceiling={n3.claimable_ceiling}")
    if not n3.eligible: return

    # N4
    n4 = process_medical_review(MedicalReviewInput(
        claim_reference_draft=n3.claim_reference_draft, policy_no=n3.policy_no,
        claimant_name=n3.claimant_name, claim_type=n3.claim_type,
        incident_date=n3.incident_date, claim_amount_requested=n3.claim_amount_requested,
        claimable_ceiling=n3.claimable_ceiling, policy_product_code=n3.policy_product_code,
        provider_name=n3.provider_name, provider_registration=n3.provider_registration,
        document_summary=n3.document_summary,
    ))
    print(f"[N4] Passed={n4.medical_review_passed} | Flags={n4.medical_flags}")
    if not n4.medical_review_passed: return

    # N5
    n5 = process_adjudication(AdjudicationInput(
        claim_reference_draft=n4.claim_reference_draft, policy_no=n4.policy_no,
        claimant_name=n4.claimant_name, claim_type=n4.claim_type,
        incident_date=n4.incident_date, claim_amount_requested=n4.claim_amount_requested,
        claimable_ceiling=n3.claimable_ceiling, rps_benchmark=n4.rps_benchmark,
        non_panel_flag=n4.non_panel_flag, policy_product_code=n4.policy_product_code,
        provider_registration=n4.provider_registration,
        medical_flags=n4.medical_flags, medical_review_notes=n4.medical_review_notes,
    ))
    print(f"[N5] Status={n5.adjudication_status.value} | Net={n5.net_payable} | Liability={n5.claimant_liability}")
    if n5.adjudication_status.value != 'approved':
        print("[N6] Skipped — zero_benefit")
        return

    # N6
    try:
        n6 = process_disbursement(DisbursementInput(
            claim_reference_draft=n5.claim_reference_draft,
            policy_no=n5.policy_no,
            claimant_name=n5.claimant_name,
            claim_type=n5.claim_type,
            net_payable=n5.net_payable,
            adjudication_status=n5.adjudication_status.value,
            claimant_liability=n5.claimant_liability,
            adjudication_notes=n5.adjudication_notes,
            deductible_applied_this_claim=n5.deductible_applied_this_claim,
            incident_date=n5.incident_date,
            provider_registration=n5.provider_registration,
            payment_details=payment_details,
        ))
        print(f"[N6] Status          : {n6.disbursement_status.value}")
        print(f"     Claim Ref No    : {n6.claim_reference_no}")
        print(f"     Net Payable     : SGD {n6.net_payable:.2f}")
        print(f"     Claimant Liab   : SGD {n6.claimant_liability:.2f}")
        print(f"     Payment Mode    : {n6.payment_mode.value}")
        print(f"     Payee           : {n6.payee_name}")
        print(f"     Disbursement Dt : {n6.disbursement_date}")
        print(f"     Remarks         : {n6.remarks}")
    except Exception as e:
        import traceback
        print(f"[N6] ERROR: {e}")
        traceback.print_exc()

async def main():
    base_dir = r"c:\Users\Lee023\OneDrive - National University of Singapore\Desktop\Project\LLM-microservice\data\health-insurance-claim\synthetic data"
    cases = [
        ("claim_B001_full_pipeline.json", "B001 — GOLD hospitalisation → provider_direct to SGH"),
        ("claim_B004_full_pipeline.json", "B004 — BRONZE surgical → direct_credit to claimant"),
    ]
    for fname, label in cases:
        case_id = fname.split("_")[1]  # "B001"
        data = json.load(open(os.path.join(base_dir, fname), encoding='utf-8'))
        await run_pipeline(data, label, PAYMENT_CONFIGS[case_id])

if __name__ == "__main__":
    asyncio.run(main())
