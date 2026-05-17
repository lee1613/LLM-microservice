from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import json

from app.medical.schemas import MedicalReviewInput, MedicalReviewOutput
from app.medical.agent import process_medical_review

router = APIRouter(prefix="/medical", tags=["Medical Review"])

@router.post("/process", response_model=MedicalReviewOutput)
def process_claim_medical(input_data: Optional[MedicalReviewInput] = None, raw_text: Optional[str] = None):
    # Support both JSON body and raw_text string
    if raw_text:
        try:
            parsed = json.loads(raw_text)
            input_data = MedicalReviewInput(**parsed)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid raw_text payload: {e}")
            
    if not input_data:
        raise HTTPException(status_code=400, detail="Missing input_data")
        
    return process_medical_review(input_data)
