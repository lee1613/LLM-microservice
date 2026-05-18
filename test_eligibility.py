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

        print(f"\n{'='*65}")
        print(f"  {filename}")
        print(f"{'='*65}")

        # ── Node 1 ──────────────────────────────────────────────────────────
        n1 = await process_claim_intake(ClaimIntakeInput(**data["stage_1_intake"]["_input"]))
        print(f"[N1] Accepted: {n1.intake_accepted} | Reason: {n1.rejection_reason}")
        if not n1.intake_accepted:
            print("[N2][N3] Skipped")
            continue

        # ── Node 2 ──────────────────────────────────────────────────────────
        n2_in = PolicyVerificationInput(
            claim_reference_draft=n1.claim_reference_draft,
            policy_no=n1.policy_no,
            claimant_name=n1.claimant_name,
            id_document_type=n1.id_document_type,
            id_document_no=n1.id_document_no,
            date_of_birth=n1.date_of_birth,
            claimant_relationship=n1.claimant_relationship,
            claim_type=n1.claim_type,
            incident_date=n1.incident_date,
            claim_amount_requested=n1.claim_amount_requested,
            document_summary=n1.document_summary,
            provider_name=n1.provider_name,
            provider_registration=n1.provider_registration,
        )
        n2 = process_verification(n2_in)
        print(f"[N2] Verified: {n2.policy_verified} | Failure: {n2.verification_failure} | Product: {n2.policy_product_code}")
        if not n2.policy_verified:
            print("[N3] Skipped")
            continue

        # ── Node 3 ──────────────────────────────────────────────────────────
        n3_in = EligibilityCheckInput(
            claim_reference_draft=n2.claim_reference_draft,
            policy_no=n2.policy_no,
            claimant_name=n2.claimant_name,
            claim_type=n2.claim_type,
            incident_date=n2.incident_date,
            claim_amount_requested=n2.claim_amount_requested,
            policy_product_code=n2.policy_product_code,
            policy_start_date=n2.policy_start_date,
            dependent_verified=n2.dependent_verified,
            provider_name=n2.provider_name,
            provider_registration=n2.provider_registration,
            document_summary=n2.document_summary,
        )
        try:
            n3 = process_eligibility(n3_in)
            print(f"[N3] Eligible: {n3.eligible} | Failure: {n3.eligibility_failure_reason}")
            print(f"     WP: {n3.waiting_period_days}d ({n3.waiting_period_basis.value}) | Satisfied: {n3.waiting_period_satisfied}")
            print(f"     Annual Limit: {n3.annual_limit} | Utilised: {n3.annual_utilised} | Remaining: {n3.annual_limit_remaining}")
            print(f"     Per-Claim Limit: {n3.per_claim_limit} | Ceiling: {n3.claimable_ceiling}")
            print(f"     Exclusions: {n3.exclusions_triggered}")
            print(f"     Rationale: {n3.eligibility_rationale}")
        except Exception as e:
            import traceback
            print(f"[N3] ERROR: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
