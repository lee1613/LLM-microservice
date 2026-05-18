import json
import asyncio
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
from app.intake.schemas import ClaimIntakeInput
from app.intake.agent import process_claim_intake
from app.verification.schemas import PolicyVerificationInput
from app.verification.agent import process_verification

async def main():
    base_dir = r"c:\Users\Lee023\OneDrive - National University of Singapore\Desktop\Project\LLM-microservice\data\health-insurance-claim\synthetic data"
    test_cases = [
        "claim_B001_full_pipeline.json",
        "claim_B002_full_pipeline.json",
        "claim_B003_full_pipeline.json",
        "claim_B004_full_pipeline.json",
        "claim_B005_full_pipeline.json"
    ]

    for filename in test_cases:
        path = os.path.join(base_dir, filename)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"\n{'='*60}")
        print(f"Testing Node 2: {filename}")
        print(f"{'='*60}")

        # === Node 1: Claim Intake ===
        intake_input = data["stage_1_intake"]["_input"]
        n1_result = await process_claim_intake(ClaimIntakeInput(**intake_input))

        print(f"[Node 1] Accepted: {n1_result.intake_accepted} | Reason: {n1_result.rejection_reason}")

        if not n1_result.intake_accepted:
            print("[Node 2] Skipped (Node 1 rejected)")
            continue

        # === Node 2: Policy Verification — input is built from Node 1 output ===
        n2_input = PolicyVerificationInput(
            claim_reference_draft=n1_result.claim_reference_draft,
            policy_no=n1_result.policy_no,
            claimant_name=n1_result.claimant_name,
            id_document_type=n1_result.id_document_type,
            id_document_no=n1_result.id_document_no,
            date_of_birth=n1_result.date_of_birth,
            claimant_relationship=n1_result.claimant_relationship,
            claim_type=n1_result.claim_type,
            incident_date=n1_result.incident_date,
            claim_amount_requested=n1_result.claim_amount_requested,
            document_summary=n1_result.document_summary,
            provider_name=n1_result.provider_name,
            provider_registration=n1_result.provider_registration,
        )

        try:
            n2_result = process_verification(n2_input)
            print(f"[Node 2] Verified: {n2_result.policy_verified} | Failure: {n2_result.verification_failure}")
            print(f"         Product Code: {n2_result.policy_product_code}")
            print(f"         Coverage: {n2_result.policy_start_date} → {n2_result.policy_expiry_date}")
            print(f"         Dependent Verified: {n2_result.dependent_verified}")
        except Exception as e:
            import traceback
            print(f"[Node 2] ERROR: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

