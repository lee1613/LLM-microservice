from fastapi import APIRouter, HTTPException
from pydantic import ValidationError
import json

from app.eligibility.schemas import EligibilityInput, EligibilityOutput
from app.eligibility.agent import process_eligibility

router = APIRouter(prefix="/eligibility", tags=["eligibility-check"])

@router.post("/process", response_model=EligibilityOutput)
def process_claim_eligibility(raw_text: str):
    try:
        data = json.loads(raw_text)
        input_data = EligibilityInput(**data)
        output = process_eligibility(input_data)
        return output
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
