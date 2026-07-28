#!/usr/bin/env python3
"""Distill the 5 golden claim contracts + real source documents into
display-only demo data for the two-act console (v3).

Reads each stage's authoritative `_output` (NEVER the stale top-level
`_outcome` blurb) for status/verdict, the real `documents/{BXXX}/*.txt`
for the Act-1 doc tabs, and the stage-level / top-level trace sub-dicts
(`_validation`, `_document_extraction`, `_registry_lookups`,
`_coding_assessment`, `_arithmetic_verify`, …) for the per-node steps.
Every value traces back to the contracts — no fabrication.

Run standalone to build, self-check, and inject:
    python demo/build_demo_data.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "..", "data", "health-insurance-claim", "synthetic data")
DOCS_DIR = os.path.join(DATA_DIR, "documents")

SCENARIOS = ["B001", "B002", "B003", "B004", "B005"]

STAGE_KEYS = [
    "stage_1_intake",
    "stage_2_policy_verification",
    "stage_3_eligibility_check",
    "stage_4_medical_review",
    "stage_5_adjudication",
    "stage_6_disbursement",
]
NODE_NAMES = ["Intake", "Verify", "Eligibility", "Medical", "Adjudication", "Disbursement"]
LLM_NODES = {1, 3, 4, 5}  # 1-indexed; drives shimmer timing

# Real source documents, in the order they should appear as Act-1 tabs.
DOC_ORDER = [
    ("medical_bill.txt", "Medical Bill"),
    ("discharge_summary.txt", "Discharge Summary"),
    ("pre_auth_approval.txt", "Pre-Auth Approval"),
]

# Static per-node capability line (shared across scenarios).
CAPABILITIES = {
    1: "Nemotron agent reads the claim documents and extracts structured fields",
    2: "Deterministic policy & member validation against the ledger",
    3: "DeepSeek reads the plan document, extracts limits & waiting periods",
    4: "DeepSeek agent cross-references ICD-10/CPT codes, provider & physician registries",
    5: "DeepSeek computes deductible, co-pay & co-insurance to net payable",
    6: "Deterministic payment-channel validation & ledger commit",
}

# Curated per-scenario, per-node (verdict, keyNumbers). Only ran nodes need entries.
SCENARIO_COPY = {
    "B001": {
        1: ("Claim parsed: pneumonia hospitalisation", "GOLD plan · policy HIC-2025-…1101"),
        2: ("Policy active, member verified", "Claimant matched · no duplicates"),
        3: ("Eligible — within annual & lifetime limits", "No waiting-period breach"),
        4: ("Codes valid, provider & physician accredited", "ICD/CPT verified · panel provider"),
        5: ("Adjudicated — full cost-share applied", "Net payable SGD 14,962.50"),
        6: ("Disbursed via direct credit (DBS), T+3", "SGD 14,962.50 · ref CLM-2025-0001101"),
    },
    "B002": {
        1: ("Claim parsed: hypertension outpatient", "SILVER plan · policy HIC-2023-…456"),
        2: ("Policy active, member verified", "Claimant matched · no duplicates"),
        3: ("Eligible — within outpatient limits", "No waiting-period breach"),
        4: ("NON-PANEL provider flagged", "70% reimbursement rate applies"),
        5: ("Zero benefit — base absorbed by deductible", "Base SGD 133 vs deductible remaining SGD 1,820"),
        6: ("No disbursement — nothing payable", "Net SGD 0 · claimant liable SGD 380"),
    },
    "B003": {
        1: ("Claim parsed: normal delivery maternity", "GOLD plan · policy HIC-2025-…789"),
        2: ("Policy active, member verified", "Claimant matched · no duplicates"),
        3: ("DENIED — maternity waiting period not met", "65 days elapsed · requested SGD 8,200"),
    },
    "B004": {
        1: ("Claim parsed: appendectomy surgical", "BRONZE plan · policy HIC-…"),
        2: ("Policy active, member verified", "Claimant matched · no duplicates"),
        3: ("Eligible — within surgical limits", "No waiting-period breach"),
        4: ("NON-PANEL provider flagged", "60% reimbursement rate applies"),
        5: ("Adjudicated — deductible + co-pay applied", "SGD 3,500 deductible · 20% co-pay"),
        6: ("Disbursed — partial reimbursement", "SGD 1,120.00 · claimant liable SGD 10,680"),
    },
    "B005": {
        1: ("Claim parsed: fracture emergency", "GOLD plan · policy HIC-2024-…099"),
        2: ("DENIED — duplicate of an already-paid claim", "Existing paid claim CLM-2025-0000877"),
    },
}

# One-line curated "what the claimant asks" per scenario (Act-1 overview).
ASKS = {
    "B001": "full hospitalisation payout",
    "B002": "outpatient GP reimbursement",
    "B003": "maternity delivery payout",
    "B004": "surgical reimbursement",
    "B005": "emergency fracture payout",
}

# Known-good money-path constants. The build asserts computed values match.
EXPECTED = {
    "B001": {"status": "APPROVED", "amount": 14962.50, "halt_node": None},
    "B002": {"status": "APPROVED", "amount": 0.0,      "halt_node": None},
    "B003": {"status": "DENIED",   "amount": None,     "halt_node": 3},
    "B004": {"status": "APPROVED", "amount": 1120.00,  "halt_node": None},
    "B005": {"status": "DENIED",   "amount": None,     "halt_node": 2},
}


def _load(scenario):
    path = os.path.join(DATA_DIR, f"claim_{scenario}_full_pipeline.json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _ran(stage_dict):
    """A stage ran iff its _output is a non-empty dict."""
    out = stage_dict.get("_output")
    return isinstance(out, dict) and len(out) > 0


def _load_documents(scenario):
    """Read the real source .txt documents present for this scenario, in
    DOC_ORDER. Returns list[{type, text}]. Only files that exist are included."""
    folder = os.path.join(DOCS_DIR, scenario)
    docs = []
    for fname, label in DOC_ORDER:
        path = os.path.join(folder, fname)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                docs.append({"type": label, "text": fh.read().strip()})
    return docs


def _plan_from_title(title):
    """Extract the plan tier (GOLD/SILVER/BRONZE) from the scenario title."""
    for tier in ("GOLD", "SILVER", "BRONZE"):
        if tier in title.upper():
            return tier
    return "—"


def _meta(scenario, contract):
    """Act-1 overview summary, derived from real contract fields."""
    s1 = contract["stage_1_intake"]["_output"]
    ext = contract["stage_1_intake"].get("_document_extraction", {})
    billed = ext.get("total_billed_amount", s1.get("claim_amount_requested", 0.0))
    return {
        "plan": _plan_from_title(contract.get("_scenario", "")),
        "patient": s1.get("claimant_name", "—"),
        "relationship": s1.get("claimant_relationship", "—"),
        "claimType": str(s1.get("claim_type", "—")).replace("_", " ").title(),
        "billed": float(billed),
        "asks": ASKS.get(scenario, ""),
    }


def _step(tag, label, detail, status="pass"):
    return {"tag": tag, "label": label, "detail": str(detail), "status": status}


def _scenario_of(contract):
    """Recover the scenario id from a loaded contract (for doc lookup)."""
    t = contract.get("_scenario", "")
    for sid in SCENARIOS:
        if sid in t:
            return sid
    return SCENARIOS[0]


def _steps_intake(c):
    s1 = c["stage_1_intake"]
    ext = s1.get("_document_extraction", {})
    out = s1.get("_output", {})
    steps = []
    doc_types = [d["type"] for d in _load_documents(_scenario_of(c))]
    steps.append(_step("AI", f"Read {len(doc_types)} source document(s)",
                       ", ".join(doc_types)))
    icd = ext.get("primary_diagnosis_icd10", "—")
    cpt = ", ".join(ext.get("procedure_cpt_codes", [])) or "—"
    nfields = len(ext)
    billed = ext.get("total_billed_amount", out.get("claim_amount_requested", 0))
    steps.append(_step("AI", f"Extracted {nfields} structured fields",
                       f"ICD-10 {icd} · CPT {cpt} · billed SGD {billed:,.2f}"))
    accepted = out.get("intake_accepted", True)
    steps.append(_step("RULE", "Intake completeness check",
                       "all required documents present" if accepted
                       else out.get("rejection_reason", "incomplete"),
                       "pass" if accepted else "fail"))
    return steps


def _steps_verify(c, failed):
    out = c["stage_2_policy_verification"].get("_output", {})
    steps = [
        _step("RULE", "Policy active & in-force",
              f"{out.get('policy_product_code', '—')} · expires "
              f"{out.get('policy_expiry_date', '—')}",
              "pass" if out.get("policy_verified", True) else "fail"),
        _step("RULE", "Member / dependent match",
              "claimant matched on register"
              if out.get("dependent_verified", True) else "mismatch",
              "pass" if out.get("dependent_verified", True) else "fail"),
    ]
    fail_reason = out.get("verification_failure")
    steps.append(_step("RULE", "Duplicate-claim check",
                       fail_reason or "no prior paid claim for this incident",
                       "fail" if fail_reason else "pass"))
    return steps


def _steps_eligibility(c, failed):
    out = c["stage_3_eligibility_check"].get("_output", {})
    steps = [
        _step("AI", "Read plan document → limits & waiting periods",
              (out.get("eligibility_rationale") or "plan terms interpreted")[:160]),
    ]
    wp_ok = out.get("waiting_period_satisfied", True)
    steps.append(_step("RULE", "Waiting-period check",
                       f"{out.get('waiting_period_days', '—')} days elapsed · "
                       f"basis {out.get('waiting_period_basis', '—')}",
                       "pass" if wp_ok else "fail"))
    steps.append(_step("RULE", "Annual-limit check",
                       f"remaining SGD {out.get('annual_limit_remaining', 0):,.2f} of "
                       f"SGD {out.get('annual_limit', 0):,.2f}",
                       "pass" if out.get("annual_limit_remaining", 1) > 0 else "fail"))
    excl = out.get("exclusions_triggered", [])
    steps.append(_step("RULE", "Exclusion-range check",
                       "no exclusion codes triggered" if not excl else f"triggered: {excl}",
                       "pass" if not excl else "fail"))
    return steps


def _steps_medical(c, failed):
    st = c["stage_4_medical_review"]
    out = st.get("_output", {})
    reg = st.get("_registry_lookups", {})
    coding = st.get("_coding_assessment", []) or out.get("coding_assessment", [])
    steps = []
    prov = reg.get("provider_accreditation", {})
    if prov:
        steps.append(_step("RULE", "Tool: MOH provider registry",
                           prov.get("result", "—"),
                           "pass" if not prov.get("non_panel_flag") else "fail"))
    phys = reg.get("physician_licence", {})
    if phys:
        steps.append(_step("RULE", "Tool: SMC physician register",
                           phys.get("result", "—")))
    for item in coding:
        ok = item.get("valid") and item.get("plausible")
        steps.append(_step("AI", f"CPT {item.get('cpt_code', '—')} clinical review",
                           item.get("reasoning", "—"),
                           "pass" if ok else "fail"))
    if "pre_auth_verified" in out:
        steps.append(_step("RULE", "Pre-authorisation check",
                           "pre-auth on file & matched"
                           if out.get("pre_auth_verified") else "no valid pre-auth",
                           "pass" if out.get("pre_auth_verified") else "fail"))
    if out.get("non_panel_flag"):
        steps.append(_step("RULE", "Panel status",
                           "NON-PANEL provider — reduced reimbursement rate", "pass"))
    return steps or [_step("AI", "Medical review", out.get("medical_review_notes", "—"))]


def _steps_adjudication(c, failed):
    av = c.get("_arithmetic_verify", {})
    out = c["stage_5_adjudication"].get("_output", {})
    # Prefer the real formula strings; each line is deterministic math → RULE.
    keys = ["adjudication_base", "deductible_applied", "co_pay",
            "co_insurance_applied", "net_payable", "claimant_liability",
            "conservation_check"]
    steps = [_step("RULE", k.replace("_", " ").title(), av[k])
             for k in keys if k in av]
    if not steps:  # fallback to _output numbers
        steps = [
            _step("RULE", "Net payable", f"SGD {out.get('net_payable', 0):,.2f}"),
            _step("RULE", "Claimant liability",
                  f"SGD {out.get('claimant_liability', 0):,.2f}"),
        ]
    return steps


def _steps_disbursement(c, failed):
    out = c["stage_6_disbursement"].get("_output", {})
    net = out.get("net_payable", 0.0)
    steps = [
        _step("RULE", "Payment-channel validation",
              f"{out.get('payment_mode', '—')} → {out.get('payee_name', '—')}"),
        _step("RULE", "Disbursement status",
              out.get("remarks", out.get("disbursement_status", "—")), "pass"),
    ]
    if net == 0.0:
        steps.append(_step("RULE", "Ledger commit",
                           "no disbursement — nothing payable", "pass"))
    else:
        steps.append(_step("RULE", "Ledger commit",
                           f"SGD {net:,.2f} committed · ref "
                           f"{out.get('claim_reference_no', '—')}", "pass"))
    return steps


_DISPATCH = {
    1: lambda c, f: _steps_intake(c),
    2: _steps_verify,
    3: _steps_eligibility,
    4: _steps_medical,
    5: _steps_adjudication,
    6: _steps_disbursement,
}


def _steps_for(node, scenario, contract):
    """Distill node's real trace into tagged steps; failed flag marks the halt node."""
    failed = (EXPECTED[scenario]["halt_node"] == node)
    return _DISPATCH[node](contract, failed)


def distill(scenario):
    contract = _load(scenario)
    ran = [_ran(contract.get(k, {})) for k in STAGE_KEYS]

    reached_end = ran[5]
    if reached_end:
        status, halt_node = "APPROVED", None
        amount = float(contract["stage_6_disbursement"]["_output"].get("net_payable", 0.0))
    else:
        status = "DENIED"
        halt_node = max(i for i, r in enumerate(ran) if r) + 1
        amount = None

    stages = []
    copy = SCENARIO_COPY[scenario]
    for i in range(6):
        node = i + 1
        if status == "DENIED" and node == halt_node:
            node_status = "fail"
        elif status == "DENIED" and node > halt_node:
            node_status = "skipped"
        else:
            node_status = "pass"
        entry = {
            "name": NODE_NAMES[i],
            "status": node_status,
            "llm": node in LLM_NODES,
            "capability": CAPABILITIES[node],
            "verdict": copy.get(node, ("", ""))[0],
            "keyNumbers": copy.get(node, ("", ""))[1],
            "steps": [] if node_status == "skipped" else _steps_for(node, scenario, contract),
        }
        stages.append(entry)

    final = {"status": status}
    if status == "APPROVED":
        final["amount"] = amount
        if amount == 0.0:
            final["note"] = (
                "Zero benefit: the covered base fell entirely within the "
                "member's remaining deductible, so nothing is payable."
            )
    else:
        final["reason"] = copy[halt_node][0]

    return {
        "id": scenario,
        "title": contract.get("_scenario", scenario),
        "meta": _meta(scenario, contract),
        "documents": _load_documents(scenario),
        "stages": stages,
        "final": final,
    }


def build_all():
    return [distill(s) for s in SCENARIOS]


def _self_check(data):
    by_id = {d["id"]: d for d in data}
    for sid, exp in EXPECTED.items():
        d = by_id[sid]
        assert d["final"]["status"] == exp["status"], (
            f"{sid}: status {d['final']['status']} != {exp['status']}"
        )
        if exp["amount"] is not None:
            got = d["final"].get("amount")
            assert got == exp["amount"], f"{sid}: amount {got} != {exp['amount']}"
        if exp["halt_node"] is not None:
            fails = [i + 1 for i, s in enumerate(d["stages"]) if s["status"] == "fail"]
            assert fails == [exp["halt_node"]], f"{sid}: fail node {fails} != [{exp['halt_node']}]"
        # Act-1 documents present.
        assert len(d["documents"]) >= 1, f"{sid}: no documents loaded"
        assert d["meta"]["billed"] > 0, f"{sid}: billed amount not derived"
        # v3: ran nodes must carry tagged steps.
        for i, s in enumerate(d["stages"]):
            if s["status"] in ("pass", "fail"):
                assert len(s["steps"]) >= 1, f"{sid}: node {i+1} has no steps"
                for st in s["steps"]:
                    assert st["tag"] in ("AI", "RULE"), f"{sid} n{i+1}: bad tag {st['tag']}"
                    assert st["status"] in ("pass", "fail"), f"{sid} n{i+1}: bad step status"
            else:
                assert s["steps"] == [], f"{sid}: skipped node {i+1} has steps"
    assert by_id["B002"]["final"].get("note"), "B002 missing zero-benefit note"
    print(f"OK: {len(data)} scenarios distilled, docs + money-path asserts passed.")


INDEX_HTML = os.path.join(HERE, "index.html")
_MARK_OPEN = '<script id="demo-data" type="application/json">'
_MARK_CLOSE = "</script>"


def inject(data):
    """Rewrite the <script id="demo-data"> region of index.html in place."""
    with open(INDEX_HTML, encoding="utf-8") as fh:
        html = fh.read()
    start = html.index(_MARK_OPEN) + len(_MARK_OPEN)
    end = html.index(_MARK_CLOSE, start)
    payload = "\n" + json.dumps(data, ensure_ascii=False, indent=0) + "\n"
    new_html = html[:start] + payload + html[end:]
    with open(INDEX_HTML, "w", encoding="utf-8") as fh:
        fh.write(new_html)
    print(f"Injected {len(data)} scenarios into {INDEX_HTML}")


if __name__ == "__main__":
    data = build_all()
    _self_check(data)
    # inject(data)  # enabled in Task 4 once index.html has the marked region
