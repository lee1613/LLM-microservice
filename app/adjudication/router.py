from fastapi import APIRouter, HTTPException
from app.adjudication.schemas import AdjudicationInput, AdjudicationOutput
from app.adjudication.agent import process_adjudication

router = APIRouter(prefix="/adjudication", tags=["Adjudication"])


@router.post("/process", response_model=AdjudicationOutput)
def process_claim_adjudication(input_data: AdjudicationInput):
    try:
        return process_adjudication(input_data)
    except AssertionError as e:
        raise HTTPException(status_code=500, detail=f"Conservation invariant violated: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
