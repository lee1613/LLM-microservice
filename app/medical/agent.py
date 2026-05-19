import re
import json
import os
from datetime import datetime, timezone, timedelta, date
from openai import OpenAI
from dotenv import load_dotenv

from app.medical.schemas import (
    MedicalReviewInput, MedicalReviewOutput, CptCodeAssessment, ClaimType
)
from app.medical.tools import (
    mcp_lookup_provider, mcp_lookup_physician,
    nlm_validate_icd10, lookup_cpt_code, get_rps_benchmark, get_pre_authorisation
)

load_dotenv()
client = OpenAI(
    base_url="https://api.vultrinference.com/v1",
    api_key=os.environ.get('VULTR_SERVERLESS_INFERENCE_API_KEY')
)

INPATIENT_CLAIM_TYPES = {ClaimType.hospitalisation, ClaimType.surgical, ClaimType.maternity}

# ─────────────────────────────────────────────────────────────────────────────
# Tool definitions handed to the LLM
# ─────────────────────────────────────────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "mcp_lookup_provider",
            "description": (
                "[MCP Tool] Queries the external MOH accredited provider registry using the "
                "provider's registration number. Returns accreditation metadata including panel_status, "
                "certification_body, accreditation_expiry_date, registry_source, and provider_name."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "provider_registration": {
                        "type": "string",
                        "description": "The provider registration number, e.g. 'MOH-HOSP-00142'."
                    }
                },
                "required": ["provider_registration"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mcp_lookup_physician",
            "description": (
                "[MCP Tool] Queries the external Singapore Medical Council (SMC) physician licence "
                "registry using the MCR licence number. Returns physician metadata including status, "
                "full_name, specialty, institution, expiry_date, and registry_url."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "physician_license_no": {
                        "type": "string",
                        "description": "The MCR licence number, e.g. 'MCR-10234A'."
                    }
                },
                "required": ["physician_license_no"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "nlm_validate_icd10",
            "description": (
                "Queries the NLM Clinical Tables ICD-10-CM API to validate an ICD-10 code. "
                "Returns whether the code is valid, its official description, and the API source."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The ICD-10-CM code to validate, e.g. 'J18.9'."
                    }
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_rps_benchmark",
            "description": (
                "Queries the Reference Price Schedule to get benchmark prices for CPT codes. "
                "Returns a dict of {cpt_code: unit_price, '__total__': total_benchmark_sgd}."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "cpt_codes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of CPT codes, e.g. ['99232', '71046']."
                    },
                    "provider_type": {
                        "type": "string",
                        "description": "'hospital' for inpatient claim types, 'clinic' for outpatient."
                    },
                    "setting": {
                        "type": "string",
                        "description": "'inpatient' for hospitalisation/surgical/maternity, 'outpatient' otherwise."
                    }
                },
                "required": ["cpt_codes", "provider_type", "setting"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_cpt_code",
            "description": (
                "Looks up a CPT/HCPCS code in the local CMS Physician Fee Schedule reference "
                "database (built from CMS 2024 PFS RVU data). Returns whether the code is a "
                "valid, active CPT code, its official CMS short description, and the data source. "
                "MUST be called for every CPT code before assessing plausibility."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The 5-digit CPT code to look up, e.g. '99232'."
                    }
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_pre_authorisation",
            "description": (
                "Queries the pre_authorisations database table for a given pre-auth number. "
                "Returns the PA record including status, policy_no, incident_date, expiry_date, "
                "or null if not found."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pre_auth_no": {
                        "type": "string",
                        "description": "Pre-authorisation number, e.g. 'PA-2025-110001'."
                    }
                },
                "required": ["pre_auth_no"]
            }
        }
    }
]

# Map tool names to their actual Python functions
TOOL_DISPATCH = {
    "mcp_lookup_provider":  lambda args: mcp_lookup_provider(args["provider_registration"]),
    "mcp_lookup_physician": lambda args: mcp_lookup_physician(args["physician_license_no"]),
    "nlm_validate_icd10":   lambda args: nlm_validate_icd10(args["code"]),
    "lookup_cpt_code":      lambda args: lookup_cpt_code(args["code"]),
    "get_rps_benchmark":    lambda args: get_rps_benchmark(args["cpt_codes"], args["provider_type"], args["setting"]),
    "get_pre_authorisation":lambda args: get_pre_authorisation(args["pre_auth_no"]),
}


def _run_agentic_medical_review(input_data: MedicalReviewInput, check_date: str) -> dict:
    """
    Runs the LLM in an agentic tool-calling loop.
    The LLM is given tools and must call them to gather evidence, then produce a structured JSON verdict.
    """
    ds = input_data.document_summary
    is_inpatient = input_data.claim_type in INPATIENT_CLAIM_TYPES
    provider_type = "hospital" if is_inpatient else "clinic"
    setting = "inpatient" if is_inpatient else "outpatient"
    requires_pre_auth = input_data.claim_type in INPATIENT_CLAIM_TYPES

    system_prompt = f"""You are a medical review agent for a health insurance company. 
You have access to tools to gather evidence. Use them to perform a complete medical review.

You MUST use the tools in this order:
1. Call mcp_lookup_provider with provider_registration="{input_data.provider_registration}"
2. Call mcp_lookup_physician with physician_license_no="{ds.physician_license_no or 'N/A'}"
3. Call nlm_validate_icd10 with code="{ds.primary_diagnosis_icd10}"
4. For EACH CPT code in {ds.procedure_cpt_codes or []}, call lookup_cpt_code to verify it exists in the CMS PFS database before assessing clinical plausibility.
5. Call get_rps_benchmark with cpt_codes={ds.procedure_cpt_codes or []}, provider_type="{provider_type}", setting="{setting}"
{"6. Call get_pre_authorisation with pre_auth_no='" + (ds.pre_authorisation_no or '') + "'" if requires_pre_auth and ds.pre_authorisation_no else ("6. Pre-auth is NOT required for this claim type." if not requires_pre_auth else "6. pre_authorisation_no is null — pre-auth document missing, this is a failure.")}

After gathering all evidence, return ONLY valid JSON (no markdown, no code fences) with this structure:
{{
  "non_panel_flag": <bool>,
  "accreditation_claim": "<sourced string citing registry source and check date {check_date}>",
  "provider_name_mismatch": <bool>,
  "physician_licence_claim": "<sourced string citing SMC registry and check date {check_date}>",
  "physician_licence_valid": <bool>,
  "icd10_valid": <bool>,
  "icd10_description": "<description from NLM>",
  "rps_benchmark": <number>,
  "rps_per_code": {{}},
  "pre_auth_verified": <bool>,
  "pre_auth_failure": <"PRE_AUTH_INVALID"|"PRE_AUTH_EXPIRED"|null>,
  "coding_assessment": [
    {{"cpt_code": "<code>", "valid": <bool>, "plausible": <bool>, "reasoning": "<1-sentence citing clinical standards>"}}
  ],
  "medical_necessity_confirmed": <bool>,
  "medical_review_notes": "<≤100 word plain-language verdict>"
}}

CPT plausibility rules:
- You MUST call lookup_cpt_code for each CPT code first. If lookup_cpt_code returns found=false, mark valid=false.
- If found=true, use the CMS short_descriptor as the authoritative description of the procedure.
- Base plausibility on established clinical standards and standard-of-care guidelines.
- A chest X-ray (CPT 71046) is clinically plausible for pneumonia (J18.9) because imaging is standard of care.
- Only mark implausible if the procedure is genuinely inappropriate or contradicted by the diagnosis.
- In reasoning, cite the CMS short_descriptor and the data source returned by lookup_cpt_code.

Accreditation/licence rules:
- accreditation_claim and physician_licence_claim MUST cite the registry source and check date {check_date}.
- If non_panel_flag=true, accreditation_claim must state the specific reason.
- If physician_licence_valid=false, physician_licence_claim must state the specific reason.
"""

    user_msg = f"""Perform a medical review for this claim:

Claim Reference: {input_data.claim_reference_draft}
Policy: {input_data.policy_no}
Claim Type: {input_data.claim_type.value}
Incident Date: {input_data.incident_date}
Provider: {input_data.provider_name} ({input_data.provider_registration})
Provider on Bill: {ds.provider_name_on_bill}
Physician: {ds.attending_physician} | Licence: {ds.physician_license_no}
ICD-10: {ds.primary_diagnosis_icd10}
CPT Codes: {ds.procedure_cpt_codes}
Pre-Auth No: {ds.pre_authorisation_no}
Total Billed: SGD {ds.total_billed_amount}
Claimable Ceiling: SGD {input_data.claimable_ceiling}
Admission: {ds.admission_date} → Discharge: {ds.discharge_date}
Clinical Narrative: {ds.summary_narrative}

Gather evidence using tools, then return the JSON verdict."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg}
    ]

    # Agentic tool-calling loop
    response = client.chat.completions.create(
        model="nvidia/DeepSeek-V3.2-NVFP4",
        messages=messages,
        tools=TOOLS,
        tool_choice="auto"
    )

    response_message = response.choices[0].message

    while response_message.tool_calls:
        messages.append(response_message)
        for tool_call in response_message.tool_calls:
            fn_name = tool_call.function.name
            raw_args = (tool_call.function.arguments or "").strip()
            fn_args = json.loads(raw_args) if raw_args else {}
            fn_result = TOOL_DISPATCH[fn_name](fn_args)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": fn_name,
                "content": json.dumps(fn_result, default=str)
            })

        from app.core.llm_utils import call_llm_with_json_retry
        response_message = call_llm_with_json_retry(
            client=client,
            model="nvidia/DeepSeek-V3.2-NVFP4",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )
        if isinstance(response_message, dict):
            return response_message # Successfully parsed JSON

    # If it didn't call tools initially or finishes tools loop
    from app.core.llm_utils import call_llm_with_json_retry
    return call_llm_with_json_retry(
        client=client,
        model="nvidia/DeepSeek-V3.2-NVFP4",
        messages=messages
    )


def process_medical_review(input_data: MedicalReviewInput) -> MedicalReviewOutput:
    now = datetime.now(timezone.utc)
    check_date = now.strftime("%Y-%m-%d")
    ds = input_data.document_summary

    # Run the agentic loop — LLM calls all tools itself
    llm = _run_agentic_medical_review(input_data, check_date)

    # ── Assemble deterministic fields from LLM tool results ───────────────
    non_panel_flag = bool(llm.get("non_panel_flag", True))
    accreditation_claim = llm.get("accreditation_claim", "")
    physician_licence_claim = llm.get("physician_licence_claim", "")
    physician_licence_valid = bool(llm.get("physician_licence_valid", False))
    pre_auth_verified = bool(llm.get("pre_auth_verified", True))
    pre_auth_failure = llm.get("pre_auth_failure")
    rps_benchmark = float(llm.get("rps_benchmark", 0.0))
    medical_necessity_confirmed = bool(llm.get("medical_necessity_confirmed", False))
    medical_review_notes = llm.get("medical_review_notes", "")
    coding_assessment = [CptCodeAssessment(**c) for c in llm.get("coding_assessment", [])]

    # ── Compute derived fields ─────────────────────────────────────────────
    total_billed = ds.total_billed_amount or 0.0
    bill_variance_pct = ((total_billed - rps_benchmark) / rps_benchmark * 100) if rps_benchmark > 0 else 0.0

    # ── Build medical flags ────────────────────────────────────────────────
    medical_flags: list[str] = []
    if non_panel_flag:
        medical_flags.append("NON_PANEL_PROVIDER")
    if llm.get("provider_name_mismatch"):
        medical_flags.append("PROVIDER_NAME_MISMATCH")
    if bill_variance_pct > 50:
        medical_flags.append("BILL_EXCEEDS_BENCHMARK")

    # ── Determine failure reason (priority order) ──────────────────────────
    failure_reason: str | None = None
    if not physician_licence_valid:
        failure_reason = "INVALID_PHYSICIAN_LICENCE"
    elif pre_auth_failure:
        failure_reason = pre_auth_failure
    elif not pre_auth_verified and input_data.claim_type in INPATIENT_CLAIM_TYPES:
        failure_reason = "MISSING_PRE_AUTH" if not ds.pre_authorisation_no else "PRE_AUTH_INVALID"
    else:
        for ca in coding_assessment:
            if not ca.valid and not failure_reason:
                failure_reason = "INVALID_CPT_CODE"
            if not ca.plausible and not failure_reason:
                failure_reason = "CPT_ICD10_MISMATCH"

    medical_review_passed = (failure_reason is None) and medical_necessity_confirmed

    # ── Length of stay ─────────────────────────────────────────────────────
    length_of_stay = None
    if ds.admission_date and ds.discharge_date:
        adm = ds.admission_date if isinstance(ds.admission_date, date) else datetime.strptime(str(ds.admission_date), "%Y-%m-%d").date()
        dis = ds.discharge_date if isinstance(ds.discharge_date, date) else datetime.strptime(str(ds.discharge_date), "%Y-%m-%d").date()
        length_of_stay = (dis - adm).days

    return MedicalReviewOutput(
        claim_reference_draft=input_data.claim_reference_draft,
        policy_no=input_data.policy_no,
        claimant_name=input_data.claimant_name,
        claim_type=input_data.claim_type,
        incident_date=input_data.incident_date,
        claim_amount_requested=input_data.claim_amount_requested,
        claimable_ceiling=input_data.claimable_ceiling,
        policy_product_code=input_data.policy_product_code,
        provider_registration=input_data.provider_registration,
        document_summary=ds,
        medical_review_passed=medical_review_passed,
        review_failure_reason=failure_reason if not medical_review_passed else None,
        non_panel_flag=non_panel_flag,
        accreditation_claim=accreditation_claim,
        physician_licence_claim=physician_licence_claim,
        coding_assessment=coding_assessment,
        pre_auth_verified=pre_auth_verified,
        length_of_stay=length_of_stay,
        rps_benchmark=rps_benchmark,
        bill_variance_pct=round(bill_variance_pct, 2),
        medical_necessity_confirmed=medical_necessity_confirmed,
        medical_flags=medical_flags,
        medical_review_notes=medical_review_notes,
        review_timestamp=now,
    )
