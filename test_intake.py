import json
import asyncio
import sys
sys.stdout.reconfigure(encoding='utf-8')
from app.intake.schemas import ClaimIntakeInput
from app.intake.agent import process_claim_intake

async def main():
    with open(r"c:\Users\Lee023\OneDrive - National University of Singapore\Desktop\Project\LLM-microservice\data\health-insurance-claim\synthetic data\claim_B001_full_pipeline.json", "r") as f:
        data = json.load(f)
        
    input_data = data["stage_1_intake"]["_input"]
    structured_input = ClaimIntakeInput(**input_data)
    
    result = await process_claim_intake(structured_input)
    print(result.model_dump_json(indent=2))

if __name__ == "__main__":
    asyncio.run(main())
