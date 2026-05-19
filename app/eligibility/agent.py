import re
import json
import os
from datetime import datetime, timezone, date
from openai import OpenAI
from dotenv import load_dotenv

from app.eligibility.schemas import (
    EligibilityCheckInput, EligibilityCheckOutput, WaitingPeriodBasis, ClaimType
)
from app.eligibility.tools import get_plan_document, get_annual_utilised, get_lifetime_utilised

load_dotenv()
client = OpenAI(
    base_url="https://api.vultrinference.com/v1",
    api_key=os.environ.get('VULTR_SERVERLESS_INFERENCE_API_KEY')
)

# Step 2: Deterministic waiting period table (days)
WAITING_PERIOD_TABLE = {
    "COMP-HEALTH-GOLD":   {"outpatient": 30, "hospitalisation": 30, "surgical": 30, "maternity": 270, "emergency": 0, "dental": 0, "vision": 0, "mental_health": 0},
    "COMP-HEALTH-SILVER": {"outpatient": 30, "hospitalisation": 60, "surgical": 60, "maternity": 365, "emergency": 0, "dental": 0, "vision": 0, "mental_health": 0},
    "COMP-HEALTH-BRONZE": {"outpatient": 60, "hospitalisation": 90, "surgical": 90, "maternity": 365, "emergency": 0, "dental": 0, "vision": 0, "mental_health": 0},
}

# Step 3: Deterministic exclusion ICD-10 ranges
def check_exclusions(icd10: str) -> list[str]:
    triggered = []
    code = icd10.upper()
    prefix2 = code[:3]
    prefix1 = code[:1]
    # Z41.x — Cosmetic
    if re.match(r'^Z41', code):
        triggered.append("COSMETIC_PROCEDURE")
    # X71–X83 — Self-inflicted
    if re.match(r'^X(7[1-9]|8[0-3])', code):
        triggered.append("SELF_INFLICTED_INJURY")
    # F10–F19 — Substance abuse
    if re.match(r'^F1[0-9]', code):
        triggered.append("SUBSTANCE_ABUSE")
    # Y36.x / Y38.x — War/terrorism
    if re.match(r'^Y3[68]', code):
        triggered.append("WAR_TERRORISM")
    return triggered


def _call_llm_for_limits_and_judgment(
    plan_document: str,
    input_data: EligibilityCheckInput,
    waiting_period_days: int,
    waiting_period_basis: str,
    waiting_period_satisfied: bool,
    exclusions_triggered: list[str],
    annual_utilised: float,
    lifetime_utilised: float,
    claimable_ceiling_hint: float,
) -> dict:
    """
    Ask the LLM to:
      1. Parse the annual_limit, per_claim_limit, lifetime_limit from plan_document.
      2. Produce eligibility_rationale (≤80 words).
    The deterministic results (waiting period, exclusions, utilisation) are injected as facts.
    """
    prompt = f"""You are an expert insurance eligibility analyst. You will be given a plan coverage document and a claim context.
Your job is to:
1. Extract the numeric limits from the plan document: annual_limit (SGD), per_claim_limit (SGD), lifetime_limit (SGD).
2. Given the pre-computed deterministic facts below, decide whether this claim is ELIGIBLE.
3. Write an eligibility_rationale (≤ 80 words).

=== PLAN DOCUMENT ===
{plan_document}

=== CLAIM CONTEXT ===
Policy: {input_data.policy_no} | Product: {input_data.policy_product_code}
Claim Type: {input_data.claim_type.value}
Incident Date: {input_data.incident_date}
Claim Amount Requested: SGD {input_data.claim_amount_requested}
Primary Diagnosis (ICD-10): {input_data.document_summary.primary_diagnosis_icd10}
Summary Narrative: {input_data.document_summary.summary_narrative}

=== DETERMINISTIC FACTS (do not re-derive these) ===
- waiting_period_days: {waiting_period_days}
- waiting_period_basis: {waiting_period_basis}
- waiting_period_satisfied: {waiting_period_satisfied}
- exclusions_triggered: {exclusions_triggered}
- annual_utilised_this_year: SGD {annual_utilised}
- lifetime_utilised_all_time: SGD {lifetime_utilised}
- preliminary_claimable_ceiling: SGD {claimable_ceiling_hint} (computed before LLM limit extraction — refine if needed)

=== INSTRUCTIONS ===
Step 1: Extract from the plan document:
  - annual_limit: the numeric SGD annual benefit cap
  - per_claim_limit: the numeric SGD per-claim cap
  - lifetime_limit: the numeric SGD lifetime cap

Step 2: Compute:
  - annual_limit_remaining = annual_limit - annual_utilised
  - claimable_ceiling = min(claim_amount_requested, per_claim_limit, annual_limit_remaining)

Step 3: Determine the FINAL eligible (true/false):
  - If claim type not covered by plan → false, reason: BENEFIT_NOT_IN_PLAN
  - If waiting_period_satisfied = false → false, reason: WAITING_PERIOD_NOT_MET
  - If exclusions_triggered is non-empty → false, reason: first exclusion code
  - If annual_limit_remaining ≤ 0 → false, reason: ANNUAL_LIMIT_EXHAUSTED
  - If lifetime_utilised ≥ lifetime_limit → false, reason: LIFETIME_LIMIT_EXHAUSTED
  - If summary_narrative clearly contradicts claim_type (e.g. dental described as hospitalisation) → false, reason: BENEFIT_NOT_IN_PLAN
  - If billed amount > 2× per_claim_limit → set amount_anomaly_flag = true (do NOT set eligible = false for this)
  - Otherwise → eligible = true

Step 4: Write eligibility_rationale (≤80 words) referencing plan tier, limits applied, waiting period, and any flags. Must be grounded in plan_document figures.

Return ONLY valid JSON (no markdown, no code fences):
{{
  "annual_limit": <number>,
  "per_claim_limit": <number>,
  "lifetime_limit": <number>,
  "annual_limit_remaining": <number>,
  "claimable_ceiling": <number>,
  "eligible": <bool>,
  "eligibility_failure_reason": <string or null>,
  "amount_anomaly_flag": <bool>,
  "eligibility_rationale": "<string>"
}}
"""

    try:
        from app.core.llm_utils import call_llm_with_json_retry
        return call_llm_with_json_retry(
            client=client,
            model="nvidia/DeepSeek-V3.2-NVFP4",
            messages=[{"role": "user", "content": prompt}]
        )
    except Exception as e:
        raise RuntimeError(f"LLM eligibility judgment failed: {e}")


def process_eligibility(input_data: EligibilityCheckInput) -> EligibilityCheckOutput:
    now = datetime.now(timezone.utc)

    # ── Step 1: Plan document retrieval ──────────────────────────────────────
    plan_doc = get_plan_document(input_data.policy_product_code, input_data.claim_type.value)
    if not plan_doc:
        return _build_output(
            input_data,
            eligible=False, failure="BENEFIT_NOT_IN_PLAN",
            wp_days=0, wp_basis=WaitingPeriodBasis.incident_date, wp_ok=False,
            annual_limit=0, annual_utilised=0, per_claim_limit=0, lifetime_utilised=0,
            claimable_ceiling=0, exclusions=[], rationale="Claim type is not covered under this plan.",
            now=now
        )

    # ── Step 2: Waiting period (deterministic) ────────────────────────────────
    product_key = input_data.policy_product_code  # e.g. "COMP-HEALTH-GOLD"
    ct = input_data.claim_type.value
    wp_days = WAITING_PERIOD_TABLE.get(product_key, {}).get(ct, 30)

    sym_onset = input_data.document_summary.symptom_onset_date
    if sym_onset and sym_onset < input_data.incident_date:
        reference_date = sym_onset
        wp_basis = WaitingPeriodBasis.symptom_onset
    else:
        reference_date = input_data.incident_date
        wp_basis = WaitingPeriodBasis.incident_date

    effective_start = input_data.policy_start_date
    # waiting period satisfied if reference_date >= policy_start_date + wp_days
    from datetime import timedelta
    earliest_valid = effective_start + timedelta(days=wp_days)
    wp_satisfied = reference_date >= earliest_valid

    if not wp_satisfied:
        return _build_output(
            input_data,
            eligible=False, failure="WAITING_PERIOD_NOT_MET",
            wp_days=wp_days, wp_basis=wp_basis, wp_ok=False,
            annual_limit=0, annual_utilised=0, per_claim_limit=0, lifetime_utilised=0,
            claimable_ceiling=0, exclusions=[],
            rationale=f"Claim does not satisfy the {wp_days}-day waiting period for {product_key} {ct}. Reference date ({wp_basis.value}): {reference_date}; policy start: {effective_start}; earliest valid date: {earliest_valid}.",
            now=now
        )

    # ── Step 3: Exclusion check (deterministic) ───────────────────────────────
    icd10 = input_data.document_summary.primary_diagnosis_icd10 or ""
    exclusions = check_exclusions(icd10)

    # ── Step 4+5: Limits & holistic judgment (LLM) ───────────────────────────
    benefit_year = input_data.incident_date.year
    annual_utilised = get_annual_utilised(input_data.policy_no, ct, benefit_year)
    lifetime_utilised = get_lifetime_utilised(input_data.policy_no, ct)

    # Rough ceiling estimate for the prompt (LLM will refine with actual limits)
    rough_ceiling = input_data.claim_amount_requested  # will be corrected by LLM

    llm_result = _call_llm_for_limits_and_judgment(
        plan_document=plan_doc,
        input_data=input_data,
        waiting_period_days=wp_days,
        waiting_period_basis=wp_basis.value,
        waiting_period_satisfied=wp_satisfied,
        exclusions_triggered=exclusions,
        annual_utilised=annual_utilised,
        lifetime_utilised=lifetime_utilised,
        claimable_ceiling_hint=rough_ceiling,
    )

    annual_limit = float(llm_result.get("annual_limit", 0))
    per_claim_limit = float(llm_result.get("per_claim_limit", 0))
    lifetime_limit = float(llm_result.get("lifetime_limit", 0))
    annual_limit_remaining = max(0.0, annual_limit - annual_utilised)
    claimable_ceiling = min(input_data.claim_amount_requested, per_claim_limit, annual_limit_remaining) if annual_limit_remaining > 0 else 0.0

    eligible = bool(llm_result.get("eligible", False))
    failure_reason = llm_result.get("eligibility_failure_reason") or None
    rationale = llm_result.get("eligibility_rationale", "")

    # Safety: if deterministic exclusion triggered, always reject regardless of LLM
    if exclusions and eligible:
        eligible = False
        failure_reason = exclusions[0]

    # Safety: if LLM says eligible but annual_limit_remaining <= 0, reject
    if eligible and annual_limit_remaining <= 0:
        eligible = False
        failure_reason = "ANNUAL_LIMIT_EXHAUSTED"

    return _build_output(
        input_data,
        eligible=eligible, failure=failure_reason,
        wp_days=wp_days, wp_basis=wp_basis, wp_ok=wp_satisfied,
        annual_limit=annual_limit, annual_utilised=annual_utilised,
        per_claim_limit=per_claim_limit, lifetime_utilised=lifetime_utilised,
        claimable_ceiling=claimable_ceiling, exclusions=exclusions,
        rationale=rationale,
        now=now
    )


def _build_output(
    input_data: EligibilityCheckInput,
    eligible: bool,
    failure: str | None,
    wp_days: int,
    wp_basis: WaitingPeriodBasis,
    wp_ok: bool,
    annual_limit: float,
    annual_utilised: float,
    per_claim_limit: float,
    lifetime_utilised: float,
    claimable_ceiling: float,
    exclusions: list[str],
    rationale: str,
    now: datetime,
) -> EligibilityCheckOutput:
    annual_limit_remaining = max(0.0, annual_limit - annual_utilised)
    return EligibilityCheckOutput(
        claim_reference_draft=input_data.claim_reference_draft,
        policy_no=input_data.policy_no,
        claimant_name=input_data.claimant_name,
        claim_type=input_data.claim_type,
        incident_date=input_data.incident_date,
        claim_amount_requested=input_data.claim_amount_requested,
        policy_product_code=input_data.policy_product_code,
        provider_name=input_data.provider_name,
        provider_registration=input_data.provider_registration,
        document_summary=input_data.document_summary,
        eligible=eligible,
        eligibility_failure_reason=failure if not eligible else None,
        waiting_period_satisfied=wp_ok,
        waiting_period_days=wp_days,
        waiting_period_basis=wp_basis,
        annual_limit=annual_limit,
        annual_utilised=annual_utilised,
        annual_limit_remaining=annual_limit_remaining,
        per_claim_limit=per_claim_limit,
        claimable_ceiling=claimable_ceiling,
        exclusions_triggered=exclusions,
        eligibility_rationale=rationale,
        eligibility_timestamp=now,
    )
