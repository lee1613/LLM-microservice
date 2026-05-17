from datetime import datetime, timezone
from app.adjudication.schemas import AdjudicationInput, AdjudicationOutput, AdjudicationStatus
from app.adjudication.tools import (
    get_policy_product_code,
    get_full_plan_benefits,
    get_deductible_utilised,
    record_adjudicated_claim
)


def get_server_timestamp() -> datetime:
    return datetime.now(timezone.utc)


def process_adjudication(input_data: AdjudicationInput) -> AdjudicationOutput:
    """
    10-step deterministic financial adjudication cascade.
    No LLM involved — all calculations are pure arithmetic against SQL-backed data.
    """
    ts = get_server_timestamp()
    incident = input_data.incident_date
    benefit_year = incident.year

    # ── Step 1: Resolve policy_product_code ──────────────────────────────────
    policy_product_code = input_data.policy_product_code
    if not policy_product_code:
        policy_product_code = get_policy_product_code(input_data.policy_no)

    # ── Step 1b: Load benefit schedule ───────────────────────────────────────
    benefits = get_full_plan_benefits(policy_product_code, input_data.claim_type.value) if policy_product_code else None

    if not benefits:
        # Cannot adjudicate without a benefit schedule — treat as zero-benefit
        return _build_output(
            input_data=input_data,
            adjudication_base=0.0,
            deductible_applied=0.0,
            co_pay=0.0,
            co_insurance=0.0,
            net_payable=0.0,
            status=AdjudicationStatus.zero_benefit,
            notes=f"Benefit schedule not found for product '{policy_product_code}' / claim type '{input_data.claim_type.value}'. No disbursement.",
            ts=ts,
            benefit_year=benefit_year
        )

    deductible_annual       = float(benefits['deductible_annual'] or 0.0)
    co_payment_pct          = float(benefits['co_payment_pct'] or 0.0)
    co_insurance_pct        = float(benefits['co_insurance_pct'] or 0.0)
    co_insurance_cap        = float(benefits['co_insurance_cap'] or 0.0)
    non_panel_reimb_pct     = float(benefits['non_panel_reimbursement_pct'] or 100.0)

    # ── Step 2: Deductible utilised this benefit year ─────────────────────────
    deductible_utilised = get_deductible_utilised(input_data.policy_no, benefit_year)

    # ── Step 3: Adjudication base ─────────────────────────────────────────────
    # Cap at rps_benchmark (if benchmark is positive and request exceeds it)
    rps_benchmark = input_data.rps_benchmark or 0.0
    if rps_benchmark > 0 and input_data.claim_amount_requested > rps_benchmark:
        adj_base = rps_benchmark
    else:
        adj_base = input_data.claim_amount_requested

    # Apply claimable_ceiling from eligibility
    claimable_ceiling = input_data.claimable_ceiling
    if claimable_ceiling is not None and claimable_ceiling > 0:
        adj_base = min(adj_base, claimable_ceiling)

    adj_base = round(adj_base, 2)

    # ── Step 4: Non-panel adjustment ──────────────────────────────────────────
    if input_data.non_panel_flag:
        adj_base = round(adj_base * (non_panel_reimb_pct / 100.0), 2)

    # ── Step 5: Deductible application ────────────────────────────────────────
    deductible_remaining = max(0.0, deductible_annual - deductible_utilised)
    amount_after_deductible = max(0.0, adj_base - deductible_remaining)
    deductible_applied = round(adj_base - amount_after_deductible, 2)

    # ── Step 6: Co-payment application ────────────────────────────────────────
    co_pay_amount = round(amount_after_deductible * (co_payment_pct / 100.0), 2)
    amount_after_copay = round(amount_after_deductible - co_pay_amount, 2)

    # ── Step 7: Co-insurance application ──────────────────────────────────────
    co_insurance_raw = round(amount_after_copay * (co_insurance_pct / 100.0), 2)
    co_insurance_amount = min(co_insurance_raw, co_insurance_cap)
    co_insurance_amount = round(co_insurance_amount, 2)
    amount_after_coinsurance = round(amount_after_copay - co_insurance_amount, 2)

    # ── Step 8: Net payable ───────────────────────────────────────────────────
    net_payable = max(0.0, round(amount_after_coinsurance, 2))

    # ── Step 9: Claimant liability ────────────────────────────────────────────
    claimant_liability = round(input_data.claim_amount_requested - net_payable, 2)

    # Conservation invariant assertion
    conservation_check = round(net_payable + claimant_liability, 2)
    assert abs(conservation_check - round(input_data.claim_amount_requested, 2)) < 0.02, (
        f"Conservation invariant violated: {net_payable} + {claimant_liability} "
        f"= {conservation_check} ≠ {input_data.claim_amount_requested}"
    )

    # ── Step 10: Adjudication decision ────────────────────────────────────────
    if net_payable > 0:
        status = AdjudicationStatus.approved
    else:
        status = AdjudicationStatus.zero_benefit

    # Build human-readable notes
    notes_parts = [
        f"Adjudication base: SGD {adj_base:.2f}",
        f"(capped at {'RPS benchmark' if rps_benchmark > 0 and input_data.claim_amount_requested > rps_benchmark else 'claimed amount'}"
        + (f" × {non_panel_reimb_pct:.0f}% non-panel rate" if input_data.non_panel_flag else "") + ").",
    ]
    if deductible_applied > 0:
        notes_parts.append(f"Deductible applied: SGD {deductible_applied:.2f}.")
    if co_pay_amount > 0:
        notes_parts.append(f"Co-payment ({co_payment_pct:.0f}%): SGD {co_pay_amount:.2f}.")
    if co_insurance_amount > 0:
        notes_parts.append(f"Co-insurance ({co_insurance_pct:.0f}%, cap SGD {co_insurance_cap:.2f}): SGD {co_insurance_amount:.2f}.")
    notes_parts.append(f"Net payable: SGD {net_payable:.2f}. Claimant liability: SGD {claimant_liability:.2f}.")
    if status == AdjudicationStatus.zero_benefit:
        notes_parts.append("Zero disbursement: cost-sharing absorbed the entire adjudication base.")
    adjudication_notes = " ".join(notes_parts)

    return _build_output(
        input_data=input_data,
        adjudication_base=adj_base,
        deductible_applied=deductible_applied,
        co_pay=co_pay_amount,
        co_insurance=co_insurance_amount,
        net_payable=net_payable,
        status=status,
        notes=adjudication_notes,
        ts=ts,
        benefit_year=benefit_year
    )


def _build_output(
    input_data: AdjudicationInput,
    adjudication_base: float,
    deductible_applied: float,
    co_pay: float,
    co_insurance: float,
    net_payable: float,
    status: AdjudicationStatus,
    notes: str,
    ts: datetime,
    benefit_year: int
) -> AdjudicationOutput:
    """Persist result and construct the output model."""
    claimant_liability = round(input_data.claim_amount_requested - net_payable, 2)

    record_adjudicated_claim(
        claim_reference_draft=input_data.claim_reference_draft,
        policy_no=input_data.policy_no,
        claim_type=input_data.claim_type.value,
        incident_date=str(input_data.incident_date),
        benefit_year=benefit_year,
        adjudication_base=adjudication_base,
        deductible_applied=deductible_applied,
        co_pay_amount=co_pay,
        co_insurance_amount=co_insurance,
        net_payable=net_payable,
        claimant_liability=claimant_liability,
        adjudication_status=status.value,
        adjudication_timestamp=ts.isoformat()
    )

    return AdjudicationOutput(
        claim_reference_draft=input_data.claim_reference_draft,
        policy_no=input_data.policy_no,
        claimant_name=input_data.claimant_name,
        claim_type=input_data.claim_type,
        incident_date=input_data.incident_date,
        claim_amount_requested=input_data.claim_amount_requested,
        adjudication_base=adjudication_base,
        deductible_applied_this_claim=deductible_applied,
        co_pay_amount=co_pay,
        co_insurance_amount=co_insurance,
        net_payable=net_payable,
        claimant_liability=claimant_liability,
        adjudication_status=status,
        adjudication_notes=notes,
        adjudication_timestamp=ts
    )
