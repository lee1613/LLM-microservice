"""
test_adjudication.py
Integration tests for Node 5 (Adjudication).
Reads Node 4 output from synthetic fixtures and calls the live /adjudication/process endpoint.
Expected values are pre-computed from the plan_benefits fixture:

  A001 (GOLD/hospitalisation, panel):   adj=16000, ded=1000, cop=750, coi=1425, net=12825, status=approved
  A002 (GOLD/outpatient, panel):        adj=320,   ded=320,  cop=0,   coi=0,    net=0,     status=zero_benefit
  A004 (GOLD/surgical, non-panel 80%):  adj=7600,  ded=1000, cop=330, coi=627,  net=5643,  status=approved
"""
import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"

EXPECTED = {
    "claim_A001_full_pipeline.json": {
        "adjudication_status": "approved",
        "adjudication_base":  16000.0,
        "deductible_applied_this_claim": 1000.0,
        "co_pay_amount":  750.0,
        "co_insurance_amount": 1425.0,
        "net_payable": 12825.0,
        "claimant_liability": 5675.0,
    },
    "claim_A002_full_pipeline.json": {
        "adjudication_status": "zero_benefit",
        "adjudication_base":  320.0,
        "deductible_applied_this_claim": 320.0,
        "co_pay_amount": 0.0,
        "co_insurance_amount": 0.0,
        "net_payable": 0.0,
        "claimant_liability": 380.0,
    },
    "claim_A004_full_pipeline.json": {
        "adjudication_status": "approved",
        "adjudication_base":  5700.0,   # 9500 × 60% non-panel (BRONZE)
        "deductible_applied_this_claim": 3500.0,
        "co_pay_amount":  440.0,        # 20% on 2200
        "co_insurance_amount": 352.0,   # 20% on 1760, cap=2000
        "net_payable": 1408.0,
        "claimant_liability": 10092.0,
    },
}

# A002: COMP-HEALTH-GOLD has deductible_annual=1000.  A002 outpatient bill=380, adj_base=min(320,380)=320.
# deductible_remaining = 1000 - 0 = 1000 > 320 → after_ded=0 → zero_benefit. Correct.


def reset_test_tables():
    """Clear Node 5 tables so each test run starts from a clean state."""
    import sqlite3
    conn = sqlite3.connect("claims.db")
    conn.execute("DELETE FROM adjudicated_claims")
    conn.execute("DELETE FROM deductible_ledger")
    conn.commit()
    conn.close()
    print("✅ Reset: adjudicated_claims and deductible_ledger cleared.")


def call(payload: dict) -> dict:
    raw = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/adjudication/process",
        data=raw,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())


def run_tests():
    reset_test_tables()
    data_dir = "data/health-insurance-claim/synthetic data"
    all_passed = True

    for filename, expected in EXPECTED.items():
        print(f"\n{'='*60}")
        print(f"Testing Node 5: {filename}")

        with open(f"{data_dir}/{filename}") as f:
            d = json.load(f)

        # Build input from Node 4 output
        node4_out = d["stage_4_medical_review"]["_output"]

        payload = {
            "claim_reference_draft": node4_out["claim_reference_draft"],
            "policy_no":             node4_out["policy_no"],
            "claimant_name":         node4_out["claimant_name"],
            "claim_type":            node4_out["claim_type"],
            "incident_date":         node4_out["incident_date"],
            "claim_amount_requested": node4_out["claim_amount_requested"],
            "claimable_ceiling":     node4_out.get("claimable_ceiling"),
            "rps_benchmark":         node4_out.get("rps_benchmark", 0.0),
            "non_panel_flag":        node4_out.get("non_panel_flag", False),
            "supporting_documents":  node4_out.get("supporting_documents", []),
            "document_paths":        node4_out.get("document_paths", {}),
        }

        try:
            result = call(payload)
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            print(f"  ❌ HTTP {e.code}: {body}")
            all_passed = False
            continue
        except Exception as e:
            print(f"  ❌ Connection error: {e}")
            all_passed = False
            continue

        # Postcondition: conservation invariant
        conservation = round(result["net_payable"] + result["claimant_liability"], 2)
        claimed = round(result["claim_amount_requested"], 2)
        assert abs(conservation - claimed) < 0.02, (
            f"Conservation violated: {result['net_payable']} + {result['claimant_liability']} = {conservation} ≠ {claimed}"
        )

        # Assert each expected field
        errors = []
        for field, exp_val in expected.items():
            got = result.get(field)
            if isinstance(exp_val, float):
                if abs(float(got) - exp_val) > 0.02:
                    errors.append(f"  {field}: expected {exp_val}, got {got}")
            else:
                if got != exp_val:
                    errors.append(f"  {field}: expected {exp_val!r}, got {got!r}")

        if errors:
            print("  ❌ Assertion failures:")
            for e in errors:
                print(e)
            all_passed = False
        else:
            print(f"  ✅ PASSED  |  status={result['adjudication_status']}"
                  f"  net_payable=SGD {result['net_payable']:.2f}"
                  f"  claimant_liability=SGD {result['claimant_liability']:.2f}")
            print(f"  📋 {result['adjudication_notes'][:120]}...")

    print(f"\n{'='*60}")
    if all_passed:
        print("🎉 All Node 5 adjudication tests passed!")
    else:
        print("⚠️  Some tests failed. Review output above.")


if __name__ == "__main__":
    run_tests()
