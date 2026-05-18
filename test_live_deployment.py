"""
Test the live Vultr Kubernetes deployment of the Health Insurance Claims Pipeline.
Iterates over cases B001-B005 sequentially hitting real HTTP endpoints:
  POST http://gem-squared-microservice.139.180.136.212.nip.io/{node}/process
"""
import requests
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://gem-squared-microservice.139.180.136.212.nip.io"
DATA_DIR = r"data/health-insurance-claim/synthetic data"

PAYMENT = {
    "B001": {
        "payment_mode": "provider_direct",
        "payee_name": "Singapore General Hospital",
    },
    "B002": {
        "payment_mode": "direct_credit",
        "payee_name": "Lim Kai Xuan",
        "bank_name": "OCBC",
        "bank_account_no": "712345678",
        "bank_branch_code": "501",
    },
    "B003": None,
    "B004": {
        "payment_mode": "direct_credit",
        "payee_name": "Ahmad Zulkifli bin Hassan",
        "bank_name": "DBS",
        "bank_account_no": "0012345678",
        "bank_branch_code": "007",
    },
    "B005": None,
}

headers = {"Content-Type": "application/json"}


def run_test_case(case_id: str, desc: str):
    fname = f"claim_{case_id}_full_pipeline.json"
    fpath = os.path.join(DATA_DIR, fname)
    with open(fpath, "r", encoding="utf-8") as f:
        case_data = json.load(f)

    # 1. Intake
    intake_input = case_data["stage_1_intake"]["_input"]
    print(f"\n=======================================================")
    print(f" 🚀 Running {case_id} — {desc}")
    print(f"=======================================================")

    print(f"  [>] Node 1 (Intake) ... ", end="", flush=True)
    r1 = requests.post(
        f"{BASE_URL}/intake/process", headers=headers, json=intake_input
    )
    if r1.status_code != 200:
        print(f"FAIL [HTTP {r1.status_code}]")
        print(r1.text)
        return
    n1 = r1.json()
    if not n1.get("intake_accepted"):
        print(f"REJECTED: {n1.get('rejection_reason')}")
        return
    print(f"PASS (Draft: {n1.get('claim_reference_draft')})")

    # 2. Verification
    print(f"  [>] Node 2 (Verification) ... ", end="", flush=True)
    r2 = requests.post(f"{BASE_URL}/verification/process", headers=headers, json=n1)
    if r2.status_code != 200:
        print(f"FAIL [HTTP {r2.status_code}]")
        print(r2.text)
        return
    n2 = r2.json()
    if not n2.get("policy_verified"):
        print(f"REJECTED: {n2.get('verification_failure')}")
        return
    print(f"PASS ({n2.get('policy_product_code')})")

    # 3. Eligibility
    print(f"  [>] Node 3 (Eligibility) ... ", end="", flush=True)
    r3 = requests.post(f"{BASE_URL}/eligibility/process", headers=headers, json=n2)
    if r3.status_code != 200:
        print(f"FAIL [HTTP {r3.status_code}]")
        print(r3.text)
        return
    n3 = r3.json()
    if not n3.get("eligible"):
        print(f"REJECTED: {n3.get('eligibility_failure_reason')}")
        return
    print(f"PASS (Ceiling: SGD {n3.get('claimable_ceiling')})")

    # 4. Medical Review
    print(f"  [>] Node 4 (Medical Review) ... ", end="", flush=True)
    # Ensure provider_registration is set (passed in from Node 3 or directly)
    if "provider_registration" not in n3 or not n3["provider_registration"]:
        n3["provider_registration"] = intake_input.get("provider_registration")
    r4 = requests.post(f"{BASE_URL}/medical/process", headers=headers, json=n3)
    if r4.status_code != 200:
        print(f"FAIL [HTTP {r4.status_code}]")
        print(r4.text)
        return
    n4 = r4.json()
    if not n4.get("medical_review_passed"):
        print(f"REJECTED: {n4.get('review_failure_reason')}")
        return
    print(
        f"PASS (RPS: SGD {n4.get('rps_benchmark')} | Flags: {n4.get('medical_flags')})"
    )

    # 5. Adjudication
    print(f"  [>] Node 5 (Adjudication) ... ", end="", flush=True)
    r5 = requests.post(f"{BASE_URL}/adjudication/process", headers=headers, json=n4)
    if r5.status_code != 200:
        print(f"FAIL [HTTP {r5.status_code}]")
        print(r5.text)
        return
    n5 = r5.json()
    if n5.get("adjudication_status") != "approved":
        print(f"REJECTED: {n5.get('adjudication_status')}")
        return
    print(
        f"PASS (Net Payable: SGD {n5.get('net_payable'):.2f} | Deductible Applied: SGD {n5.get('deductible_applied_this_claim'):.2f})"
    )
    print(f"      AI Adjudication Note: {n5.get('adjudication_notes')}")

    # 6. Disbursement
    pd = PAYMENT[case_id]
    if not pd:
        print(f"  [>] Node 6 (Disbursement) ... SKIPPED (Expected validation halt)")
        return

    print(f"  [>] Node 6 (Disbursement) ... ", end="", flush=True)
    disb_input = {**n5, "payment_details": pd}
    r6 = requests.post(
        f"{BASE_URL}/disbursement/process", headers=headers, json=disb_input
    )
    if r6.status_code != 200:
        print(f"FAIL [HTTP {r6.status_code}]")
        print(r6.text)
        return
    n6 = r6.json()
    if n6.get("disbursement_status") != "disbursed":
        print(f"REJECTED: {n6.get('disbursement_status')}")
        return
    print(f"PASS (Claim ID: {n6.get('claim_reference_no')})")
    print(f"      Status : {n6.get('remarks')}")


def main():
    cases = [
        ("B001", "GOLD Panel Hospitalisation (Tan Wei Ming)"),
        ("B002", "SILVER Non-Panel Outpatient (Lim Kai Xuan - Expired Doctor License)"),
        ("B003", "SILVER Panel Maternity (Priya Subramaniam - Waiting Period)"),
        ("B004", "BRONZE Non-Panel Surgical (Ahmad Zulkifli bin Hassan)"),
        ("B005", "GOLD Emergency Outpatient Duplicate Claim (Chen Mei Ling)"),
    ]
    for cid, desc in cases:
        run_test_case(cid, desc)


if __name__ == "__main__":
    main()
