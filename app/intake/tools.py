import re
import os
import sqlite3
import fitz
import json
from datetime import datetime, timezone, timedelta, date
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'health-insurance-claim', 'synthetic data', 'database.db')

client = OpenAI(
    base_url="https://api.vultrinference.com/v1",
    api_key=os.environ.get('VULTR_SERVERLESS_INFERENCE_API_KEY')
)

def query_policy_existence(policy_no: str) -> bool:
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM policies WHERE policy_no = ?", (policy_no,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except sqlite3.Error as e:
        print(f"DB Error: {e}")
        return False

def get_server_timestamp() -> datetime:
    return datetime.now(timezone(timedelta(hours=8)))

def parse_pdf_file_tool(rel_path: str) -> str:
    """
    Tool function called by the LLM.

    Accepts either:
    - An **absolute path** (used for temp-uploaded files from /intake/upload).
    - A **relative path** such as 'B001/medical_bill.pdf' (resolved against the
      server's pre-loaded documents directory for /intake/process).
    """
    if os.path.isabs(rel_path):
        full_path = rel_path
    else:
        base_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'health-insurance-claim', 'synthetic data', 'documents')
        full_path = os.path.join(base_dir, rel_path)

    if not os.path.exists(full_path):
        return f"Error: File {rel_path} not found."
    try:
        doc = fitz.open(full_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        return f"Error reading {rel_path}: {e}"


def extract_document_summary(pdf_paths: list[str], claim_type: str, requested_amount: float) -> dict:
    # Normalize paths to use forward slashes to prevent escape character issues (like \U) on Windows
    normalized_paths = [str(p).replace("\\", "/") for p in pdf_paths]
    prompt = f"""
You are an expert medical claims extractor. You have access to a tool `parse_pdf_file` which reads the text of a PDF file.
Use the tool to read the contents of the following files: {normalized_paths}.
After reading all the required files, return structured information.
Return ONLY valid JSON format. Do not use markdown blocks like ```json ... ```, just pure JSON.

The required fields to extract:
- "total_billed_amount": float or null if UNREADABLE
- "itemised_charges": list of objects {{"description": str, "quantity": int, "unit_price": float}}
- "primary_diagnosis_icd10": string (ICD-10 format, e.g. "J18.9", or infer the most appropriate ICD-10 code from the diagnosis name or medications/treatments if the explicit diagnosis is missing, e.g., Antihypertensive Medications -> "I10") or null if UNREADABLE
- "procedure_cpt_codes": list of strings (e.g. ["99232"])
- "symptom_onset_date": string (YYYY-MM-DD) or null
- "admission_date": string (YYYY-MM-DD) or null
- "discharge_date": string (YYYY-MM-DD) or null
- "attending_physician": string or null
- "physician_license_no": string or null
- "pre_authorisation_no": string or null
- "provider_name_on_bill": string or null
- "extraction_warnings": list of strings (Any field above that was required but couldn't be read should have its name here, e.g., "primary_diagnosis_icd10")
- "summary_narrative": string (<= 150 words plain language summary of the claim event, must reference diagnosis, treatment, and total billed amount).

Claim context: Type: {claim_type}, Requested Amount: {requested_amount}
Return raw JSON ONLY after you have gathered the data.
"""
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "parse_pdf_file",
                "description": "Extracts and returns the text content from a PDF file.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filepath": {
                            "type": "string",
                            "description": "The path to the PDF file."
                        }
                    },
                    "required": ["filepath"]
                }
            }
        }
    ]

    messages = [{"role": "user", "content": prompt}]
    
    response = client.chat.completions.create(
        model="nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
    response_message = response.choices[0].message
    
    # If the model decides to call tools
    while response_message.tool_calls:
        messages.append(response_message)
        for tool_call in response_message.tool_calls:
            if tool_call.function.name == "parse_pdf_file":
                # Parse JSON arguments with a robust regex fallback if JSON decoding fails due to backslashes
                filepath = ""
                try:
                    args = json.loads(tool_call.function.arguments)
                    filepath = args.get("filepath", "")
                except Exception:
                    # Fallback to regex parsing if LLM output JSON is invalid or has bad escape characters
                    import re
                    match = re.search(r'"filepath"\s*:\s*"([^"]+)"', tool_call.function.arguments)
                    if match:
                        filepath = match.group(1)
                
                # Normalize the filepath again before reading
                filepath = filepath.replace("\\", "/")
                text_result = parse_pdf_file_tool(filepath)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": "parse_pdf_file",
                    "content": text_result
                })
        
        # Send the tool results back to the model
        from app.core.llm_utils import call_llm_with_json_retry
        response_message = call_llm_with_json_retry(
            client=client,
            model="nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        if isinstance(response_message, dict):
            return response_message # It successfully parsed json
        # Otherwise, loop continues if it called tools again

    from app.core.llm_utils import call_llm_with_json_retry
    return call_llm_with_json_retry(
        client=client,
        model="nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16",
        messages=messages
    )
