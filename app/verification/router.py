from fastapi import APIRouter, HTTPException
from pydantic import ValidationError
import json

from app.verification.schemas import PolicyVerificationInput, PolicyVerificationOutput
from app.verification.agent import process_verification

router = APIRouter(prefix="/verification", tags=["policy-verification"])

@router.post("/process", response_model=PolicyVerificationOutput)
def process_claim_verification(raw_text: str):
    try:
        data = json.loads(raw_text)
        input_data = PolicyVerificationInput(**data)
        output = process_verification(input_data)
        return output
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
