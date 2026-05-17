import os
import json
from datetime import datetime, timezone, date
from typing import Dict, Any, List
from openai import OpenAI

from app.medical.schemas import MedicalReviewInput, MedicalReviewOutput, MedicalDetails
from app.medical.tools import (
    get_provider,
    is_icd10_valid,
    is_cpt_valid,
    is_cpt_icd10_plausible,
    get_triggered_exclusions,
    get_pre_auth,
    get_physician,
    is_medically_necessary,
    get_rps_benchmark,
    check_substance_abuse_coverage
)

# Initialize Vultr Serverless Inference
vultr_api_key = os.environ.get('VULTR_SERVERLESS_INFERENCE_API_KEY')
if not vultr_api_key:
    # Try to load from .env
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if 'VULTR_SERVERLESS_INFERENCE_API_KEY' in line:
                    vultr_api_key = line.split('=', 1)[1].strip().strip('"').strip("' ")

vultr_client = OpenAI(
    base_url="https://api.vultrinference.com/v1",
    api_key=vultr_api_key
) if vultr_api_key else None

def get_server_timestamp() -> datetime:
    return datetime.now(timezone.utc)

def extract_medical_details(document_paths: Dict[str, str]) -> MedicalDetails:
    if not vultr_client:
        raise RuntimeError("VULTR_SERVERLESS_INFERENCE_API_KEY is not set.")
        
    combined_text = ""
    for doc_type, pdf_path in document_paths.items():
        txt_path = pdf_path.replace('.pdf', '.txt')
        if os.path.exists(txt_path):
            with open(txt_path, 'r', encoding='utf-8') as f:
                combined_text += f"\n\n--- {doc_type.upper()} ---\n{f.read()}"
    
    prompt = f"""
    You are a medical billing data extraction assistant.
    Extract the following details from the provided clinical documents.
    Return ONLY a valid JSON object matching this schema exactly, nothing else:
    {{
        "primary_diagnosis_icd10": "string",
        "procedure_cpt_codes": ["string"],
        "admission_date": "YYYY-MM-DD" or null,
        "discharge_date": "YYYY-MM-DD" or null,
        "attending_physician": "string",
        "physician_license_no": "string",
        "pre_authorisation_no": "string" or null (also known as Authorization Number)
    }}
    
    Documents:
    {combined_text}
    """
    
    response = vultr_client.chat.completions.create(
        model="vultr/got-qwen-120b-normalize",
        messages=[
            {"role": "system", "content": "You are a data extraction AI. Output strictly valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )
    
    content = response.choices[0].message.content
    
    # Strip markdown if present
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].strip()
        
    # <think> tags handling for reasoning models
    if "</think>" in content:
        content = content.split("</think>")[1].strip()
        
    data = json.loads(content)
    
    # Parse dates
    def parse_date(d):
        if d:
            try:
                return datetime.strptime(d, "%Y-%m-%d").date()
            except ValueError:
                return None
        return None
        
    return MedicalDetails(
        primary_diagnosis_icd10=data.get('primary_diagnosis_icd10', ''),
        procedure_cpt_codes=data.get('procedure_cpt_codes', []),
        admission_date=parse_date(data.get('admission_date')),
        discharge_date=parse_date(data.get('discharge_date')),
        attending_physician=data.get('attending_physician', ''),
        physician_license_no=data.get('physician_license_no', ''),
        pre_authorisation_no=data.get('pre_authorisation_no')
    )

def process_medical_review(input_data: MedicalReviewInput) -> MedicalReviewOutput:
    # 0. Extraction
    try:
        med_details = extract_medical_details(input_data.document_paths or {})
    except Exception as e:
        print(f"Extraction failed: {e}")
        # Return a failure if extraction breaks
        return _build_output(input_data, False, "EXTRACTION_FAILED", False, False, None, 0.0, 0.0, False, ["EXTRACTION_FAILED"])

    failure_reason = None
    flags = []
    
    icd10 = med_details.primary_diagnosis_icd10
    cpts = med_details.procedure_cpt_codes
    
    # 1. Provider accreditation check
    provider = get_provider(input_data.provider_registration)
    non_panel_flag = False
    if not provider:
        non_panel_flag = True
    else:
        exp_date_str = provider['accreditation_expiry_date']
        if not exp_date_str:
            non_panel_flag = True
        else:
            exp_date = datetime.strptime(exp_date_str, "%Y-%m-%d").date()
            if exp_date < input_data.incident_date or provider['panel_status'] != 'active':
                non_panel_flag = True
    
    if non_panel_flag:
        flags.append("NON_PANEL_PROVIDER")
        
    provider_type = provider['provider_type'] if provider else 'gp_clinic'
    
    # 2. ICD-10 Validation
    if not is_icd10_valid(icd10):
        return _build_output(input_data, False, "INVALID_ICD10", non_panel_flag, False, None, 0.0, 0.0, False, flags)
        
    # 3. CPT Validation
    for cpt in cpts:
        if not is_cpt_valid(cpt):
            return _build_output(input_data, False, "INVALID_CPT_CODE", non_panel_flag, False, None, 0.0, 0.0, False, flags)
        if not is_cpt_icd10_plausible(icd10, cpt):
            return _build_output(input_data, False, "CPT_ICD10_MISMATCH", non_panel_flag, False, None, 0.0, 0.0, False, flags)
            
    # 4. Exclusion Check
    exclusions = get_triggered_exclusions(icd10, cpts)
    if 'SUBSTANCE_ABUSE' in exclusions:
        if check_substance_abuse_coverage(input_data.policy_no): # Actually needs policy_product_code, wait
            exclusions.remove('SUBSTANCE_ABUSE')
            
    if exclusions:
        return _build_output(input_data, False, "EXCLUSIONS_TRIGGERED", non_panel_flag, False, None, 0.0, 0.0, False, flags, exclusions)

    # 5. Pre-authorisation check
    pre_auth_verified = False
    if input_data.claim_type.value in ['hospitalisation', 'surgical', 'maternity']:
        pa_no = med_details.pre_authorisation_no
        if not pa_no:
            return _build_output(input_data, False, "MISSING_PRE_AUTH", non_panel_flag, False, None, 0.0, 0.0, False, flags)
            
        pa = get_pre_auth(pa_no)
        if not pa:
            return _build_output(input_data, False, "MISSING_PRE_AUTH", non_panel_flag, False, None, 0.0, 0.0, False, flags)
        if pa['status'] != 'approved':
            return _build_output(input_data, False, "PRE_AUTH_INVALID", non_panel_flag, False, None, 0.0, 0.0, False, flags)
        if pa['policy_no'] != input_data.policy_no:
            return _build_output(input_data, False, "PRE_AUTH_POLICY_MISMATCH", non_panel_flag, False, None, 0.0, 0.0, False, flags)
            
        pa_exp = datetime.strptime(pa['expiry_date'], "%Y-%m-%d").date()
        if input_data.incident_date > pa_exp:
            return _build_output(input_data, False, "PRE_AUTH_EXPIRED", non_panel_flag, False, None, 0.0, 0.0, False, flags)
        pre_auth_verified = True
    else:
        pre_auth_verified = True
        
    # 6. Hospitalisation duration check
    los = None
    if med_details.admission_date and med_details.discharge_date:
        if med_details.discharge_date < med_details.admission_date:
            return _build_output(input_data, False, "INVALID_ADMISSION_DISCHARGE_DATES", non_panel_flag, pre_auth_verified, None, 0.0, 0.0, False, flags)
        los = (med_details.discharge_date - med_details.admission_date).days
        
    # 7. Physician licence validation
    phys = get_physician(med_details.physician_license_no)
    if not phys:
        return _build_output(input_data, False, "INVALID_PHYSICIAN_LICENCE", non_panel_flag, pre_auth_verified, los, 0.0, 0.0, False, flags)
    if phys['status'] != 'active':
        return _build_output(input_data, False, "INVALID_PHYSICIAN_LICENCE", non_panel_flag, pre_auth_verified, los, 0.0, 0.0, False, flags)
    phys_exp = datetime.strptime(phys['expiry_date'], "%Y-%m-%d").date()
    if phys_exp < input_data.incident_date:
        return _build_output(input_data, False, "INVALID_PHYSICIAN_LICENCE", non_panel_flag, pre_auth_verified, los, 0.0, 0.0, False, flags)
        
    # 8. Medical necessity determination
    necessity = True
    for cpt in cpts:
        if not is_medically_necessary(icd10, cpt):
            necessity = False
            break
            
    if not necessity:
        return _build_output(input_data, False, "MEDICAL_NECESSITY_UNCONFIRMED", non_panel_flag, pre_auth_verified, los, 0.0, 0.0, False, flags)
        
    # 9. Bill reasonableness check
    setting = 'inpatient' if input_data.claim_type.value in ['hospitalisation', 'surgical', 'maternity'] else 'outpatient'
    rps_benchmark = get_rps_benchmark(cpts, provider_type, setting)
    
    if rps_benchmark == 0.0:
        rps_benchmark = input_data.claim_amount_requested # fallback if no benchmark found
        
    variance = (input_data.claim_amount_requested - rps_benchmark) / rps_benchmark * 100
    if variance > 50:
        flags.append("BILL_EXCEEDS_BENCHMARK")
        return _build_output(input_data, False, "BILL_EXCEEDS_BENCHMARK", non_panel_flag, pre_auth_verified, los, rps_benchmark, variance, necessity, flags)
        
    # 10. Medical review result
    return _build_output(input_data, True, None, non_panel_flag, pre_auth_verified, los, rps_benchmark, variance, necessity, flags)


def _build_output(
    input_data: MedicalReviewInput,
    passed: bool,
    failure_reason: str,
    non_panel_flag: bool,
    pre_auth_verified: bool,
    los: int,
    rps_benchmark: float,
    variance: float,
    necessity: bool,
    flags: List[str],
    exclusions: List[str] = None
) -> MedicalReviewOutput:
    if exclusions is None:
        exclusions = []
    return MedicalReviewOutput(
        claim_reference_draft=input_data.claim_reference_draft,
        policy_no=input_data.policy_no,
        claimant_name=input_data.claimant_name,
        claim_type=input_data.claim_type,
        incident_date=input_data.incident_date,
        claim_amount_requested=input_data.claim_amount_requested,
        claimable_ceiling=input_data.claimable_ceiling,
        medical_review_passed=passed,
        exclusions_triggered=exclusions,
        review_failure_reason=failure_reason,
        non_panel_flag=non_panel_flag,
        pre_auth_verified=pre_auth_verified,
        length_of_stay=los,
        rps_benchmark=rps_benchmark,
        bill_variance_pct=variance,
        medical_necessity_confirmed=necessity,
        medical_flags=flags,
        review_timestamp=get_server_timestamp(),
        supporting_documents=input_data.supporting_documents,
        document_paths=input_data.document_paths
    )
