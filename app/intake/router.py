from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from app.intake.schemas import ClaimIntakeInput, ClaimIntakeOutput
from app.intake.agent import process_claim_intake
from app.intake.tools import extract_claim_input

router = APIRouter(prefix="/intake", tags=["claim-intake"])

@router.post("/process", response_model=ClaimIntakeOutput)
async def intake_claim(raw_text: str = None, structured_input: ClaimIntakeInput = None):
    """
    Endpoint for claim intake.
    Optionally accepts raw_text to be extracted using the LLM extraction tool,
    or directly accepts structured input (Schema A).
    Outputs standard Schema B.
    """
    if raw_text and not structured_input:
        try:
            extracted_data = extract_claim_input(raw_text)
            structured_input = ClaimIntakeInput(**extracted_data)
        except NotImplementedError as e:
            raise HTTPException(status_code=501, detail=str(e))
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Extraction failed to match schema: {e}")
            
    if not structured_input:
        raise HTTPException(status_code=400, detail="Either raw_text or structured_input must be provided.")
        
    output = await process_claim_intake(structured_input)
    return output
