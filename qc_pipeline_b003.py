"""
QC Pipeline Validator — B003 Full Pipeline
==========================================
Reference: data/health-insurance-claim/synthetic data/claim_B003_full_pipeline.json
Output: qc_report_b003.md (detailed intermediate I/O + comparison against expected)

Scenario: Maternity claim — HALTS at Node 3 (WAITING_PERIOD_NOT_MET).
           Nodes 4–6 are skipped.

Usage:
    .venv\\Scripts\\python.exe qc_pipeline_b003.py
"""

import requests
import json
import sys
import io
from datetime import datetime, timezone
from pathlib import Path

# Force UTF-8 output on Windows to avoid cp1252 codec errors
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Config ────────────────────────────────────────────────────────────────────
BASE_URL = "http://139.180.136.212"
EXPECTED_FILE = Path(r"data\health-insurance-claim\synthetic data\claim_B003_full_pipeline.json")
DOCS_DIR = Path(r"data\health-insurance-claim\synthetic data\documents")
REPORT_FILE = Path("qc_report_b003.md")
HEADERS = {"Content-Type": "application/json"}
TIMEOUT = 90  # seconds per request

# ── Load Expected Output ───────────────────────────────────────────────────────
with open(EXPECTED_FILE, encoding="utf-8") as f:
    EXPECTED = json.load(f)

# ── Helpers ────────────────────────────────────────────────────────────────────

def post(endpoint: str, payload: dict) -> dict:
    """POST JSON payload to an endpoint."""
    url = f"{BASE_URL}{endpoint}"
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def post_multipart(endpoint: str, claim_meta: dict, pdf_paths: list) -> dict:
    """POST claim metadata + real PDF files as multipart/form-data."""
    url = f"{BASE_URL}{endpoint}"
    data = {"claim_data": json.dumps(claim_meta, default=str)}
    file_handles = []
    files_param = []
    for p in pdf_paths:
        fh = open(p, "rb")
        file_handles.append(fh)
        files_param.append(("files", (p.name, fh, "application/pdf")))
    try:
        resp = requests.post(url, data=data, files=files_param, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    finally:
        for fh in file_handles:
            fh.close()


def _skip_fields() -> set:
    """Fields that are inherently non-deterministic and should be skipped in comparison."""
    return {
        "intake_timestamp",
        "verification_timestamp",
        "eligibility_timestamp",
        "review_timestamp",
        "adjudication_timestamp",
        "processing_timestamp",
        "claim_reference_draft",   # sequence-dependent
        "claim_reference_no",      # sequence-dependent
        "summary_narrative",       # LLM non-deterministic text
        "accreditation_claim",     # LLM non-deterministic text
        "physician_licence_claim", # LLM non-deterministic text
        "eligibility_rationale",   # LLM non-deterministic text
        "adjudication_notes",      # LLM non-deterministic text
        "remarks",                 # LLM/date-dependent non-deterministic text
        "disbursement_date",       # dynamically calculated date
        "description",             # itemised charge description text variant
        "medical_review_notes",    # LLM non-deterministic text
        "reasoning",               # LLM non-deterministic text
        "halted_reason",           # String formatting/case difference
        "extraction_warnings"      # LLM/parser warnings are non-deterministic
    }


def compare_values(path: str, actual, expected, results: list):
    """Recursively compare actual vs expected, collecting pass/fail tuples."""
    last_key = path.split(".")[-1]
    if "[" in last_key:
        last_key = last_key.split("[")[0]
    if last_key in _skip_fields():
        results.append(("SKIP", path, actual, expected, "Non-deterministic field skipped"))
        return

    # Sort CPT codes and medical flags before comparison to avoid ordering mismatches
    if last_key in ("procedure_cpt_codes", "medical_flags") and isinstance(expected, list) and isinstance(actual, list):
        actual = sorted([str(x) for x in actual])
        expected = sorted([str(x) for x in expected])

    # Sort coding_assessment objects by CPT code to avoid ordering mismatches
    if last_key == "coding_assessment" and isinstance(expected, list) and isinstance(actual, list):
        actual = sorted(actual, key=lambda x: str(x.get("cpt_code", "")) if isinstance(x, dict) else "")
        expected = sorted(expected, key=lambda x: str(x.get("cpt_code", "")) if isinstance(x, dict) else "")

    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in expected:
            compare_values(f"{path}.{key}", actual.get(key), expected[key], results)
        # flag unexpected extra keys in actual
        for key in actual:
            if key not in expected:
                results.append(("INFO", f"{path}.{key}", actual[key], None, "Extra key in actual (not in expected)"))
    elif isinstance(expected, list) and isinstance(actual, list):
        if len(actual) != len(expected):
            results.append(("FAIL", path, actual, expected, f"List length mismatch: actual={len(actual)} expected={len(expected)}"))
        else:
            for i, (a, e) in enumerate(zip(actual, expected)):
                compare_values(f"{path}[{i}]", a, e, results)
    else:
        if actual == expected:
            results.append(("PASS", path, actual, expected, ""))
        else:
            # Numeric tolerance for floats
            if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
                if abs(float(actual) - float(expected)) < 0.01:
                    results.append(("PASS", path, actual, expected, "Within float tolerance"))
                    return
            results.append(("FAIL", path, actual, expected, "Value mismatch"))


def md_table_row(*cols: str) -> str:
    return "| " + " | ".join(str(c).replace("|", "\\|").replace("\n", " ") for c in cols) + " |"


def json_block(data) -> str:
    return "```json\n" + json.dumps(data, indent=2, ensure_ascii=False) + "\n```"


def status_icon(status: str) -> str:
    return {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️", "INFO": "ℹ️"}.get(status, "❓")


# ── Main Pipeline Run ──────────────────────────────────────────────────────────

def main():
    run_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sections = []
    all_comparisons = []
    stage_results = {}

    print("=" * 60)
    print(f"  QC Pipeline B003 — {run_ts}")
    print(f"  Target: {BASE_URL}")
    print("=" * 60)

    # ── Step 0: Reset DB ───────────────────────────────────────────────────────
    print("\n[0] Resetting ledger DB…")
    try:
        reset_resp = requests.post(f"{BASE_URL}/dev/reset", timeout=TIMEOUT)
        reset_ok = reset_resp.status_code == 200
        reset_body = reset_resp.text
    except Exception as exc:
        reset_ok = False
        reset_body = str(exc)
    print(f"    → {'OK' if reset_ok else 'FAILED'}: {reset_body}")

    sections.append(f"""
## Step 0 — DB Reset

**Endpoint:** `POST /dev/reset`  
**Status:** {"✅ OK" if reset_ok else "❌ FAILED"}  
**Response:** `{reset_body}`

---
""")

    # ── Node 1: Intake (file upload) ───────────────────────────────────────────
    print("\n[1] Node 1 — Intake (uploading real PDFs via /intake/upload)...")
    n1_meta = dict(EXPECTED["stage_1_intake"]["_input"])
    n1_expected = EXPECTED["stage_1_intake"]["_output"]

    # Resolve the scanned_files to actual local PDFs
    n1_pdf_paths = []
    for rel in n1_meta.get("scanned_files", []):
        resolved = DOCS_DIR / rel
        if not resolved.exists():
            print(f"    WARNING: PDF not found locally: {resolved}")
        n1_pdf_paths.append(resolved)

    print(f"    Uploading {len(n1_pdf_paths)} file(s): {[p.name for p in n1_pdf_paths]}")

    try:
        n1_actual = post_multipart("/intake/process", n1_meta, n1_pdf_paths)
        n1_ok = n1_actual.get("intake_accepted", False)
        n1_err = None
    except Exception as exc:
        n1_actual = {}
        n1_ok = False
        n1_err = str(exc)

    n1_cmp = []
    compare_values("stage_1_intake._output", n1_actual, n1_expected, n1_cmp)
    all_comparisons.extend(n1_cmp)
    stage_results["Node 1: Intake (upload)"] = n1_cmp

    pass_c = sum(1 for r in n1_cmp if r[0] == "PASS")
    fail_c = sum(1 for r in n1_cmp if r[0] == "FAIL")
    print(f"    intake_accepted={n1_ok}  | PASS={pass_c} FAIL={fail_c}" + (f" | ERR: {n1_err}" if n1_err else ""))

    sections.append(f"""
## Stage 1 — Claim Intake

**Endpoint:** `POST /intake/process` (multipart: JSON metadata + PDF file uploads)  
**Uploaded Files:** {[p.name for p in n1_pdf_paths]}  
**Status:** {"✅ Accepted" if n1_ok else "❌ Rejected / Error"}  
{f"**Error:** `{n1_err}`" if n1_err else ""}

### Request Metadata (claim_data form field)
{json_block({k: v for k, v in n1_meta.items() if k != "scanned_files"})}

### Actual API Response
{json_block(n1_actual)}

### Expected Output (from contract)
{json_block(n1_expected)}

### Field-Level Comparison
| Status | Field | Actual | Expected | Note |
|:---:|:---|:---|:---|:---|
""" + "\n".join(md_table_row(status_icon(r[0]), r[1], str(r[2])[:120], str(r[3])[:120], r[4]) for r in n1_cmp) + "\n\n---\n")

    if n1_err:
        print("    Pipeline aborted at Node 1.")
        _write_report(sections, all_comparisons, run_ts, stage_results, aborted_at=1)
        sys.exit(1)

    # ── Node 2: Verification ──────────────────────────────────────────────────
    print("\n[2] Node 2 — Policy Verification…")
    n2_input = n1_actual
    n2_expected = EXPECTED["stage_2_policy_verification"]["_output"]

    try:
        n2_actual = post("/verification/process", n2_input)
        n2_ok = n2_actual.get("policy_verified", False)
        n2_err = None
    except Exception as exc:
        n2_actual = {}
        n2_ok = False
        n2_err = str(exc)

    n2_cmp = []
    compare_values("stage_2_verification._output", n2_actual, n2_expected, n2_cmp)
    all_comparisons.extend(n2_cmp)
    stage_results["Node 2: Verification"] = n2_cmp

    pass_c = sum(1 for r in n2_cmp if r[0] == "PASS")
    fail_c = sum(1 for r in n2_cmp if r[0] == "FAIL")
    print(f"    policy_verified={n2_ok}  | PASS={pass_c} FAIL={fail_c}" + (f" | ERR: {n2_err}" if n2_err else ""))

    sections.append(f"""
## Stage 2 — Policy Verification

**Endpoint:** `POST /verification/process`  
**Status:** {"✅ Verified" if n2_ok else "❌ Verification Failed / Error"}  
{f"**Error:** `{n2_err}`" if n2_err else ""}

### Request Payload (= Node 1 Output)
{json_block(n2_input)}

### Actual API Response
{json_block(n2_actual)}

### Expected Output (from contract)
{json_block(n2_expected)}

### Field-Level Comparison
| Status | Field | Actual | Expected | Note |
|:---:|:---|:---|:---|:---|
""" + "\n".join(md_table_row(status_icon(r[0]), r[1], str(r[2])[:120], str(r[3])[:120], r[4]) for r in n2_cmp) + "\n\n---\n")

    if n2_err:
        _write_report(sections, all_comparisons, run_ts, stage_results, aborted_at=2)
        sys.exit(1)

    # ── Node 3: Eligibility ───────────────────────────────────────────────────
    print("\n[3] Node 3 — Eligibility Check…")
    n3_input = n2_actual
    n3_expected = EXPECTED["stage_3_eligibility_check"]["_output"]

    try:
        n3_actual = post("/eligibility/process", n3_input)
        n3_ok = n3_actual.get("eligible", False)
        n3_err = None
    except Exception as exc:
        n3_actual = {}
        n3_ok = False
        n3_err = str(exc)

    n3_cmp = []
    compare_values("stage_3_eligibility._output", n3_actual, n3_expected, n3_cmp)
    all_comparisons.extend(n3_cmp)
    stage_results["Node 3: Eligibility"] = n3_cmp

    pass_c = sum(1 for r in n3_cmp if r[0] == "PASS")
    fail_c = sum(1 for r in n3_cmp if r[0] == "FAIL")
    print(f"    eligible={n3_ok}  | PASS={pass_c} FAIL={fail_c}" + (f" | ERR: {n3_err}" if n3_err else ""))

    sections.append(f"""
## Stage 3 — Eligibility Check

**Endpoint:** `POST /eligibility/process`  
**Status:** {"✅ Eligible" if n3_ok else "❌ Ineligible (EXPECTED for B003)"}  
{f"**Error:** `{n3_err}`" if n3_err else ""}

### Request Payload (= Node 2 Output)
{json_block(n3_input)}

### Actual API Response
{json_block(n3_actual)}

### Expected Output (from contract)
{json_block(n3_expected)}

### Field-Level Comparison
| Status | Field | Actual | Expected | Note |
|:---:|:---|:---|:---|:---|
""" + "\n".join(md_table_row(status_icon(r[0]), r[1], str(r[2])[:120], str(r[3])[:120], r[4]) for r in n3_cmp) + "\n\n---\n")

    # ── Pipeline halts here for B003 ──────────────────────────────────────────
    # B003 should be ineligible (WAITING_PERIOD_NOT_MET), nodes 4-6 are skipped.
    if not n3_ok:
        print("\n    ⛔ Pipeline halted at Node 3 — eligible=false (EXPECTED for B003)")
        print("    Nodes 4–6 skipped as designed.")

        sections.append("""
## Stages 4–6 — Skipped

> Pipeline halted at Node 3 — `eligible=false`, `eligibility_failure_reason=WAITING_PERIOD_NOT_MET`.  
> Nodes 4 (Medical Review), 5 (Adjudication), and 6 (Disbursement) are **not invoked** — this is the expected behaviour for B003.

---
""")

    # ── Write Final Report ────────────────────────────────────────────────────
    _write_report(sections, all_comparisons, run_ts, stage_results, aborted_at=None)

    total_pass = sum(1 for r in all_comparisons if r[0] == "PASS")
    total_fail = sum(1 for r in all_comparisons if r[0] == "FAIL")
    total_skip = sum(1 for r in all_comparisons if r[0] == "SKIP")
    print(f"\n{'='*60}")
    print(f"  QC COMPLETE  |  PASS={total_pass}  FAIL={total_fail}  SKIP={total_skip}")
    print(f"  Report saved → {REPORT_FILE}")
    print(f"{'='*60}\n")

    if total_fail > 0:
        sys.exit(2)


def _write_report(sections, all_comparisons, run_ts, stage_results, aborted_at):
    total_pass = sum(1 for r in all_comparisons if r[0] == "PASS")
    total_fail = sum(1 for r in all_comparisons if r[0] == "FAIL")
    total_skip = sum(1 for r in all_comparisons if r[0] == "SKIP")
    total_info = sum(1 for r in all_comparisons if r[0] == "INFO")

    abort_note = f"> ⛔ **Pipeline aborted at Node {aborted_at}** — subsequent stages not executed.\n" if aborted_at else ""

    # Summary table
    summary_rows = []
    for node_name, cmps in stage_results.items():
        p = sum(1 for r in cmps if r[0] == "PASS")
        f = sum(1 for r in cmps if r[0] == "FAIL")
        s = sum(1 for r in cmps if r[0] == "SKIP")
        icon = "✅" if f == 0 else "❌"
        summary_rows.append(md_table_row(icon, node_name, p, f, s))

    summary_table = (
        "| Result | Node | PASS | FAIL | SKIP |\n"
        "|:---:|:---|:---:|:---:|:---:|\n"
        + "\n".join(summary_rows)
    )

    # Critical fails list
    fails = [r for r in all_comparisons if r[0] == "FAIL"]
    fail_section = ""
    if fails:
        fail_rows = "\n".join(
            md_table_row(r[1], str(r[2])[:150], str(r[3])[:150], r[4])
            for r in fails
        )
        fail_section = f"""
## ❌ Failed Assertions Summary

| Field | Actual | Expected | Note |
|:---|:---|:---|:---|
{fail_rows}
"""

    header = f"""# QC Report — B003 Full Pipeline
**Scenario:** {EXPECTED.get('_scenario', 'B003')}  
**Expected Outcome:** {EXPECTED.get('_outcome', 'N/A')}  
**API Target:** `{BASE_URL}`  
**Run Timestamp:** `{run_ts}`  

{abort_note}

## Executive Summary

| Metric | Count |
|:---|:---:|
| ✅ PASS | {total_pass} |
| ❌ FAIL | {total_fail} |
| ⏭️ SKIP (non-deterministic) | {total_skip} |
| ℹ️ INFO (extra keys) | {total_info} |

### Per-Node Results
{summary_table}

---
"""

    content = header + fail_section + "\n---\n\n# Detailed Stage Logs\n\n" + "\n".join(sections)

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    main()
