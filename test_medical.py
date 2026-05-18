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

async def main():
    base_dir = r"c:\Users\Lee023\OneDrive - National University of Singapore\Desktop\Project\LLM-microservice\data\health-insurance-claim\synthetic data"
    # B001 is the best candidate: hospitalisation, all docs present, should pass all nodes
    test_cases = [
        "claim_B001_full_pipeline.json",
        "claim_B004_full_pipeline.json",  # surgical - BRONZE
    ]

    for filename in test_cases:
        path = os.path.join(base_dir, filename)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"\n{'='*65}")
        print(f"  {filename}")
        print(f"{'='*65}")

        # N1
        n1 = await process_claim_intake(ClaimIntakeInput(**data["stage_1_intake"]["_input"]))
        print(f"[N1] {n1.intake_accepted} | {n1.rejection_reason}")
        if not n1.intake_accepted: continue

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
        print(f"[N2] {n2.policy_verified} | {n2.verification_failure} | {n2.policy_product_code}")
        if not n2.policy_verified: continue

        # N3
        n3 = process_eligibility(EligibilityCheckInput(
            claim_reference_draft=n2.claim_reference_draft, policy_no=n2.policy_no,
            claimant_name=n2.claimant_name, claim_type=n2.claim_type,
            incident_date=n2.incident_date, claim_amount_requested=n2.claim_amount_requested,
            policy_product_code=n2.policy_product_code, policy_start_date=n2.policy_start_date,
            dependent_verified=n2.dependent_verified, provider_name=n2.provider_name,
            provider_registration=n2.provider_registration, document_summary=n2.document_summary,
        ))
        print(f"[N3] {n3.eligible} | {n3.eligibility_failure_reason} | Ceiling: {n3.claimable_ceiling}")
        if not n3.eligible: continue

        # N4
        try:
            n4 = process_medical_review(MedicalReviewInput(
                claim_reference_draft=n3.claim_reference_draft, policy_no=n3.policy_no,
                claimant_name=n3.claimant_name, claim_type=n3.claim_type,
                incident_date=n3.incident_date, claim_amount_requested=n3.claim_amount_requested,
                claimable_ceiling=n3.claimable_ceiling, policy_product_code=n3.policy_product_code,
                provider_name=n3.provider_name, provider_registration=n3.provider_registration,
                document_summary=n3.document_summary,
            ))
            print(f"[N4] Passed: {n4.medical_review_passed} | Failure: {n4.review_failure_reason}")
            print(f"     Non-Panel: {n4.non_panel_flag} | Pre-Auth: {n4.pre_auth_verified}")
            print(f"     RPS Benchmark: SGD {n4.rps_benchmark} | Billed: SGD {n4.document_summary.total_billed_amount} | Variance: {n4.bill_variance_pct:.1f}%")
            print(f"     Flags: {n4.medical_flags}")
            print(f"     LOS: {n4.length_of_stay} days")
            print(f"     Medical Necessity: {n4.medical_necessity_confirmed}")
            print(f"     Coding Assessment:")
            for ca in n4.coding_assessment:
                print(f"       CPT {ca.cpt_code}: valid={ca.valid}, plausible={ca.plausible} — {ca.reasoning}")
            print(f"     Review Notes: {n4.medical_review_notes}")
        except Exception as e:
            import traceback
            print(f"[N4] ERROR: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
