from fastapi import APIRouter, HTTPException
from app.disbursement.schemas import DisbursementInput, DisbursementOutput
from app.disbursement.agent import process_disbursement

router = APIRouter(prefix="/disbursement", tags=["Disbursement"])


@router.post("/process", response_model=DisbursementOutput)
def process_claim_disbursement(input_data: DisbursementInput):
    try:
        return process_disbursement(input_data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
