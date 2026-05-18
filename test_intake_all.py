import json
import asyncio
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
from app.intake.schemas import ClaimIntakeInput
from app.intake.agent import process_claim_intake

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
            
        print(f"\n--- Testing {filename} ---")
        input_data = data["stage_1_intake"]["_input"]
        structured_input = ClaimIntakeInput(**input_data)
        
        try:
            result = await process_claim_intake(structured_input)
            print(f"Accepted: {result.intake_accepted}")
            print(f"Rejection Reason: {result.rejection_reason}")
            print(f"Missing docs: {result.missing_documents}")
            if result.document_summary:
                print(f"Billed: {result.document_summary.total_billed_amount}")
                print(f"ICD10: {result.document_summary.primary_diagnosis_icd10}")
            else:
                print("No Document Summary (likely rejected before parsing)")
        except Exception as e:
            print(f"Error testing {filename}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
