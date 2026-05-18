from fastapi import APIRouter, HTTPException
from pydantic import ValidationError
from app.eligibility.schemas import EligibilityCheckInput, EligibilityCheckOutput
from app.eligibility.agent import process_eligibility

router = APIRouter(prefix="/eligibility", tags=["Eligibility Check"])


@router.post("/process", response_model=EligibilityCheckOutput)
def process_claim_eligibility(input_data: EligibilityCheckInput):
    try:
        return process_eligibility(input_data)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
