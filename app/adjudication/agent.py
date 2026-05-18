"""
Node 5 — Claim Adjudication Agent

Architecture per contract:
  llm_scope: Step 1 (cost-sharing parameter extraction from plan_document natural language)
  Steps 2–5: fully deterministic arithmetic
  Step 5: LLM produces adjudication_notes (≤80 words)
"""
import re
import json
import os
from datetime import datetime, timezone
from openai import OpenAI
from dotenv import load_dotenv

from app.adjudication.schemas import AdjudicationInput, AdjudicationOutput, AdjudicationStatus
from app.adjudication.tools import get_plan_document, get_deductible_utilised, record_adjudicated_claim

load_dotenv()
client = OpenAI(
    base_url="https://api.vultrinference.com/v1",
    api_key=os.environ.get('VULTR_SERVERLESS_INFERENCE_API_KEY')
)


# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — LLM extracts cost-sharing parameters from plan_document text
# ─────────────────────────────────────────────────────────────────────────────

def _extract_cost_sharing_params(
    plan_document: str,
    policy_product_code: str,
    claim_type: str,
    non_panel_flag: bool,
) -> dict:
    """
    Ask the LLM to read the plan_document and extract the exact numeric cost-sharing
    parameters for this product + claim_type. Returns a dict with:
      deductible_annual, co_payment_pct, co_insurance_pct,
      co_insurance_cap, non_panel_reimbursement_pct
    """
    prompt = f"""You are an insurance policy analyst. Read the plan coverage document below and extract the EXACT numeric cost-sharing parameters for this claim.

=== PLAN DOCUMENT ===
{plan_document}

=== CLAIM CONTEXT ===
Product Code: {policy_product_code}
Claim Type: {claim_type}
Non-Panel Provider: {non_panel_flag}

=== EXTRACTION TASK ===
Extract these parameters EXACTLY as stated in the document. Do NOT estimate or infer — only use numbers explicitly stated.

1. deductible_annual: The annual deductible in SGD (the fixed amount the claimant pays first each year before insurance kicks in)
2. co_payment_pct: The co-payment percentage (fixed % the claimant pays after deductible)
3. co_insurance_pct: The co-insurance percentage (% the claimant bears after co-payment)
4. co_insurance_cap: The maximum co-insurance cap in SGD per benefit year (if stated; 0 if not applicable)
5. non_panel_reimbursement_pct: The reimbursement percentage for non-panel providers (e.g. 80 means 80% reimbursement). If not stated, use 100.

Return ONLY valid JSON (no markdown, no code fences):
{{
  "deductible_annual": <number>,
  "co_payment_pct": <number>,
  "co_insurance_pct": <number>,
  "co_insurance_cap": <number>,
  "non_panel_reimbursement_pct": <number>,
  "extraction_notes": "<brief 1-sentence confirmation of which document section each value was read from>"
}}
"""
    response = client.chat.completions.create(
        model="nvidia/DeepSeek-V3.2-NVFP4",
        messages=[{"role": "user", "content": prompt}]
    )
    content = response.choices[0].message.content
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
    content = re.sub(r'^```(?:json)?', '', content.strip(), flags=re.MULTILINE).strip()
    content = re.sub(r'```$', '', content.strip(), flags=re.MULTILINE).strip()
    return json.loads(content.strip())


# ─────────────────────────────────────────────────────────────────────────────
# Step 5 — LLM produces adjudication_notes (≤80 words)
# ─────────────────────────────────────────────────────────────────────────────

def _generate_adjudication_notes(
    claim_reference_draft: str,
    policy_product_code: str,
    claim_type: str,
    claim_amount_requested: float,
    adjudication_base: float,
    rps_benchmark: float,
    claimable_ceiling: float,
    non_panel_flag: bool,
    non_panel_reimbursement_pct: float,
    deductible_annual: float,
    deductible_utilised: float,
    deductible_applied: float,
    co_payment_pct: float,
    co_pay_amount: float,
    co_insurance_pct: float,
    co_insurance_cap: float,
    co_insurance_amount: float,
    net_payable: float,
    claimant_liability: float,
    adjudication_status: str,
    medical_flags: list,
    extraction_notes: str,
) -> str:
    """Ask the LLM to produce a ≤80-word adjudication rationale grounded in the computed figures."""
    prompt = f"""You are an insurance adjudication officer writing a concise claim decision note.

=== COMPUTED ADJUDICATION FIGURES ===
Claim Reference: {claim_reference_draft}
Product: {policy_product_code} | Claim Type: {claim_type}
Amount Requested: SGD {claim_amount_requested:.2f}
Adjudication Base: SGD {adjudication_base:.2f}
  (capped at: min(requested={claim_amount_requested:.2f}, rps_benchmark={rps_benchmark:.2f}, claimable_ceiling={claimable_ceiling:.2f}){f" × {non_panel_reimbursement_pct:.0f}% non-panel rate" if non_panel_flag else ""})
Deductible Annual: SGD {deductible_annual:.2f} | Already Utilised: SGD {deductible_utilised:.2f}
Deductible Applied This Claim: SGD {deductible_applied:.2f}
Co-Payment ({co_payment_pct:.0f}%): SGD {co_pay_amount:.2f}
Co-Insurance ({co_insurance_pct:.0f}%, cap SGD {co_insurance_cap:.2f}): SGD {co_insurance_amount:.2f}
Net Payable (insurer disbursement): SGD {net_payable:.2f}
Claimant Liability: SGD {claimant_liability:.2f}
Adjudication Status: {adjudication_status}
Medical Flags: {medical_flags}
Plan Document Source Notes: {extraction_notes}

=== INSTRUCTION ===
Write adjudication_notes: a ≤80-word plain-language summary for the claimant/insurer file.
Rules:
- State the adjudication base and each non-zero cost-sharing component (deductible, co-pay, co-insurance).
- If non_panel_flag=True, state the non-panel discount rate applied.
- Cite the exact net_payable figure (SGD {net_payable:.2f}) — no rounding to a different number.
- If status=approved, do NOT use rejection/denial language.
- If status=zero_benefit, state which component consumed the base.
- Reference any medical_flags that affected the calculation.
- Return ONLY the plain text of the note (no JSON, no code blocks, no headers).
"""
    response = client.chat.completions.create(
        model="nvidia/DeepSeek-V3.2-NVFP4",
        messages=[{"role": "user", "content": prompt}]
    )
    content = response.choices[0].message.content
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
    return content.strip()


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def process_adjudication(input_data: AdjudicationInput) -> AdjudicationOutput:
    now = datetime.now(timezone.utc)
    benefit_year = input_data.incident_date.year

    # ── Step 1: Retrieve plan_document & extract cost-sharing params via LLM ──
    plan_doc = get_plan_document(input_data.policy_product_code, input_data.claim_type.value)
    if not plan_doc:
        raise RuntimeError(
            f"PLAN_DOCUMENT_NOT_FOUND: No plan document for "
            f"{input_data.policy_product_code} / {input_data.claim_type.value}"
        )

    params = _extract_cost_sharing_params(
        plan_document=plan_doc,
        policy_product_code=input_data.policy_product_code,
        claim_type=input_data.claim_type.value,
        non_panel_flag=input_data.non_panel_flag,
    )

    deductible_annual         = float(params.get("deductible_annual", 0.0))
    co_payment_pct            = float(params.get("co_payment_pct", 0.0))
    co_insurance_pct          = float(params.get("co_insurance_pct", 0.0))
    co_insurance_cap          = float(params.get("co_insurance_cap", 0.0))
    non_panel_reimbursement_pct = float(params.get("non_panel_reimbursement_pct", 100.0))
    extraction_notes          = params.get("extraction_notes", "")

    # ── Step 1b: Deductible utilised this benefit year ────────────────────────
    deductible_utilised = get_deductible_utilised(input_data.policy_no, benefit_year)

    # ── Step 2: Adjudication base — contract formula ──────────────────────────
    # adjudication_base = min(claim_amount_requested, rps_benchmark, claimable_ceiling)
    adj_base = min(
        input_data.claim_amount_requested,
        input_data.rps_benchmark,
        input_data.claimable_ceiling
    )
    adj_base = round(adj_base, 2)

    # Non-panel adjustment
    if input_data.non_panel_flag:
        adj_base = round(adj_base * (non_panel_reimbursement_pct / 100.0), 2)

    # ── Step 3: Deductible & co-payment ───────────────────────────────────────
    deductible_remaining    = max(0.0, deductible_annual - deductible_utilised)
    amount_after_deductible = max(0.0, adj_base - deductible_remaining)
    deductible_applied      = round(adj_base - amount_after_deductible, 2)
    co_pay_amount           = round(amount_after_deductible * (co_payment_pct / 100.0), 2)
    amount_after_copay      = round(amount_after_deductible - co_pay_amount, 2)

    # ── Step 4: Co-insurance & net payable ────────────────────────────────────
    co_insurance_raw    = round(amount_after_copay * (co_insurance_pct / 100.0), 2)
    co_insurance_amount = round(min(co_insurance_raw, co_insurance_cap), 2)
    net_payable         = round(max(0.0, amount_after_copay - co_insurance_amount), 2)
    claimant_liability  = round(input_data.claim_amount_requested - net_payable, 2)

    # ── Step 5: Adjudication status & LLM notes ───────────────────────────────
    status = AdjudicationStatus.approved if net_payable > 0 else AdjudicationStatus.zero_benefit

    adjudication_notes = _generate_adjudication_notes(
        claim_reference_draft=input_data.claim_reference_draft,
        policy_product_code=input_data.policy_product_code,
        claim_type=input_data.claim_type.value,
        claim_amount_requested=input_data.claim_amount_requested,
        adjudication_base=adj_base,
        rps_benchmark=input_data.rps_benchmark,
        claimable_ceiling=input_data.claimable_ceiling,
        non_panel_flag=input_data.non_panel_flag,
        non_panel_reimbursement_pct=non_panel_reimbursement_pct,
        deductible_annual=deductible_annual,
        deductible_utilised=deductible_utilised,
        deductible_applied=deductible_applied,
        co_payment_pct=co_payment_pct,
        co_pay_amount=co_pay_amount,
        co_insurance_pct=co_insurance_pct,
        co_insurance_cap=co_insurance_cap,
        co_insurance_amount=co_insurance_amount,
        net_payable=net_payable,
        claimant_liability=claimant_liability,
        adjudication_status=status.value,
        medical_flags=input_data.medical_flags,
        extraction_notes=extraction_notes,
    )

    # ── Persist ───────────────────────────────────────────────────────────────
    record_adjudicated_claim(
        claim_reference_draft=input_data.claim_reference_draft,
        policy_no=input_data.policy_no,
        claim_type=input_data.claim_type.value,
        incident_date=str(input_data.incident_date),
        benefit_year=benefit_year,
        net_payable=net_payable,
        adjudication_status=status.value,
        adjudication_timestamp=now.isoformat(),
        deductible_applied=deductible_applied,
    )

    return AdjudicationOutput(
        claim_reference_draft=input_data.claim_reference_draft,
        policy_no=input_data.policy_no,
        claimant_name=input_data.claimant_name,
        claim_type=input_data.claim_type,
        incident_date=input_data.incident_date,
        claim_amount_requested=input_data.claim_amount_requested,
        provider_registration=input_data.provider_registration,
        adjudication_base=adj_base,
        deductible_applied_this_claim=deductible_applied,
        co_pay_amount=co_pay_amount,
        co_insurance_amount=co_insurance_amount,
        net_payable=net_payable,
        claimant_liability=claimant_liability,
        adjudication_status=status,
        adjudication_notes=adjudication_notes,
        adjudication_timestamp=now,
    )
