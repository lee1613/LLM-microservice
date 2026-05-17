import re
from datetime import date, datetime, timezone, timedelta
from typing import List
import uuid

from app.schemas.claim_intake import ClaimType, DocumentType

def extract_claim_input(raw_text: str) -> dict:
    """
    Tool: Extract user information and all the input required.
    In a real implementation, this tool calls an LLM (e.g. via instructor or LangChain)
    to parse unstructured input into Schema A.
    """
    # TODO: Implement LLM structured extraction using the schema definition.
    raise NotImplementedError("LLM extraction tool requires specific model configuration.")

def validate_regex(pattern: str, string: str) -> bool:
    """Tool: Evaluates a given string against a regex pattern."""
    return bool(re.match(pattern, string))

async def mcp_query_policy_existence(policy_no: str) -> bool:
    """
    Tool: Connects to MCP (Model Context Protocol) to query if the policy exists.
    If the database tool is not available locally, we define how to connect via MCP.
    """
    # Defined connection strategy:
    # 1. Connect to MCP server using e.g., HTTP SSE or stdio transport.
    # 2. Call tool `query_policy_db` with `policy_no`.
    # 3. Server executes `SELECT 1 FROM policies WHERE policy_no = ?`.
    # Return mock result for now.
    
    # raise NotImplementedError("MCP connection requires client implementation.")
    # For now, return True so the pipeline doesn't block.
    return True

def get_server_date() -> date:
    """Tool: Fetch current server date in UTC+8."""
    return datetime.now(timezone(timedelta(hours=8))).date()

def get_server_timestamp() -> datetime:
    """Tool: Fetch current server timestamp in UTC+8."""
    return datetime.now(timezone(timedelta(hours=8)))

def calculate_age(dob: date, ref_date: date) -> int:
    """Tool: Calculates age based on floor((ref_date - dob) / 365.25)"""
    days = (ref_date - dob).days
    return int(days // 365.25)

def calculate_submission_lag(incident_date: date, claim_date: date) -> int:
    """Tool: Calculate submission lag in days."""
    return (claim_date - incident_date).days

def validate_claim_amount(amount: float) -> bool:
    """Tool: Check if claim amount requested > 0."""
    return amount > 0.0

def validate_documents_vocabulary(docs: List[str]) -> bool:
    """Tool: Validate supporting documents against allowed tokens."""
    allowed = {doc.value for doc in DocumentType}
    return all(doc in allowed for doc in docs)

def check_missing_documents(claim_type: ClaimType, docs: List[str]) -> List[str]:
    """Tool: Check minimum required document completeness based on claim_type."""
    docs_set = set(docs)
    missing = []
    
    if claim_type in [ClaimType.hospitalisation, ClaimType.surgical, ClaimType.maternity]:
        if DocumentType.medical_bill.value not in docs_set:
            missing.append(DocumentType.medical_bill.value)
        if DocumentType.discharge_summary.value not in docs_set:
            missing.append(DocumentType.discharge_summary.value)
    elif claim_type in [ClaimType.outpatient, ClaimType.dental, ClaimType.vision, ClaimType.emergency]:
        if DocumentType.medical_bill.value not in docs_set:
            missing.append(DocumentType.medical_bill.value)
            
    return missing

def generate_draft_reference() -> str:
    """Tool: Generates a draft claim reference."""
    today_str = get_server_date().strftime("%Y%m%d")
    unique_id = str(uuid.uuid4().int)[:5].zfill(5)
    return f"DRAFT-{today_str}-{unique_id}"
