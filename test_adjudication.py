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

async def run_pipeline(data: dict, label: str):
    print(f"\n{'='*65}")
    print(f"  {label}")
    print(f"{'='*65}")

    # N1
    n1 = await process_claim_intake(ClaimIntakeInput(**data["stage_1_intake"]["_input"]))
    print(f"[N1] Accepted={n1.intake_accepted} | {n1.rejection_reason or 'OK'}")
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
    print(f"[N2] Verified={n2.policy_verified} | {n2.verification_failure or 'OK'} | {n2.policy_product_code}")
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
    print(f"[N3] Eligible={n3.eligible} | {n3.eligibility_failure_reason or 'OK'} | Ceiling={n3.claimable_ceiling}")
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
    print(f"[N4] Passed={n4.medical_review_passed} | {n4.review_failure_reason or 'OK'} | Flags={n4.medical_flags}")
    if not n4.medical_review_passed: return

    # N5
    try:
        n5 = process_adjudication(AdjudicationInput(
            claim_reference_draft=n4.claim_reference_draft,
            policy_no=n4.policy_no,
            claimant_name=n4.claimant_name,
            claim_type=n4.claim_type,
            incident_date=n4.incident_date,
            claim_amount_requested=n4.claim_amount_requested,
            claimable_ceiling=n3.claimable_ceiling,
            rps_benchmark=n4.rps_benchmark,
            non_panel_flag=n4.non_panel_flag,
            policy_product_code=n4.policy_product_code,
            provider_registration=n4.provider_registration,
            medical_flags=n4.medical_flags,
            medical_review_notes=n4.medical_review_notes,
        ))
        print(f"[N5] Status={n5.adjudication_status.value}")
        print(f"     Adjudication Base : SGD {n5.adjudication_base:.2f}")
        print(f"     Deductible Applied: SGD {n5.deductible_applied_this_claim:.2f}")
        print(f"     Co-Pay            : SGD {n5.co_pay_amount:.2f}")
        print(f"     Co-Insurance      : SGD {n5.co_insurance_amount:.2f}")
        print(f"     Net Payable       : SGD {n5.net_payable:.2f}")
        print(f"     Claimant Liability: SGD {n5.claimant_liability:.2f}")
        print(f"     Adjudication Notes: {n5.adjudication_notes}")
    except Exception as e:
        import traceback
        print(f"[N5] ERROR: {e}")
        traceback.print_exc()


async def main():
    base_dir = r"c:\Users\Lee023\OneDrive - National University of Singapore\Desktop\Project\LLM-microservice\data\health-insurance-claim\synthetic data"
    cases = [
        ("claim_B001_full_pipeline.json", "B001 — GOLD hospitalisation (panel)"),
        ("claim_B004_full_pipeline.json", "B004 — BRONZE surgical (non-panel)"),
    ]
    for fname, label in cases:
        data = json.load(open(os.path.join(base_dir, fname), encoding='utf-8'))
        await run_pipeline(data, label)

if __name__ == "__main__":
    asyncio.run(main())
