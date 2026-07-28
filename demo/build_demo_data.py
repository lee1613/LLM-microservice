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


def _steps_for(node, scenario, contract):
    """Distill node's real trace sub-dicts into tagged steps. Filled in Task 2."""
    return []  # stub — Task 2 replaces this


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
