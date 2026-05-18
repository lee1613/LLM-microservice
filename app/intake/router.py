from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from app.intake.schemas import ClaimIntakeInput, ClaimIntakeOutput
from app.intake.agent import process_claim_intake

router = APIRouter(prefix="/intake", tags=["claim-intake"])

@router.post("/process", response_model=ClaimIntakeOutput)
async def intake_claim(structured_input: ClaimIntakeInput):
    """
    Endpoint for claim intake.
    Accepts structured input (Schema A).
    Outputs standard Schema B.
    """
    if not structured_input:
        raise HTTPException(status_code=400, detail="structured_input must be provided.")
        
    output = await process_claim_intake(structured_input)
    return output
