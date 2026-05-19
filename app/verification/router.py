from fastapi import APIRouter, HTTPException
from pydantic import ValidationError
import json

from app.verification.schemas import PolicyVerificationInput, PolicyVerificationOutput
from app.verification.agent import process_verification

router = APIRouter(prefix="/verification", tags=["policy-verification"])

@router.post("/process", response_model=PolicyVerificationOutput)
def process_claim_verification(input_data: PolicyVerificationInput):
    try:
        output = process_verification(input_data)
        return output
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
