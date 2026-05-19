import requests
import json
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
DOCS_DIR = Path(r"data\health-insurance-claim\synthetic data\documents")
pdf_paths = [
    DOCS_DIR / "B001" / "medical_bill.pdf",
    DOCS_DIR / "B001" / "discharge_summary.pdf",
    DOCS_DIR / "B001" / "pre_auth_approval.pdf"
]

metadata_no_scanned_files = {
    "policy_no": "HIC-2024-00123",
    "policy_holder": "Tan Wei Ming",
    "claimant_name": "Tan Wei Ming",
    "claimant_relationship": "self",
    "id_document_type": "nric",
    "id_document_no": "S7801234A",
    "date_of_birth": "1978-03-22",
    "claim_date": "2025-04-14",
    "incident_date": "2025-04-10",
    "claim_type": "hospitalisation",
    "claim_amount_requested": 18500.0,
    "provider_name": "Singapore General Hospital",
    "provider_registration": "MOH-HOSP-00142",
    "supporting_documents": ["medical_bill", "discharge_summary", "pre_auth_approval"]
}

metadata_with_scanned_files = {
    **metadata_no_scanned_files,
    "scanned_files": ["B001/medical_bill.pdf"]
}

def test_upload(metadata, desc):
    print(f"\n--- Testing: {desc} ---")
    data = {"claim_data": json.dumps(metadata)}
    file_handles = []
    files_param = []
    for p in pdf_paths:
        fh = open(p, "rb")
        file_handles.append(fh)
        files_param.append(("files", (p.name, fh, "application/pdf")))
    try:
        resp = requests.post(f"{BASE_URL}/intake/process", data=data, files=files_param)
        print("Status Code:", resp.status_code)
        print("Response:", json.dumps(resp.json(), indent=2))
    except Exception as e:
        print("Request failed:", e)
    finally:
        for fh in file_handles:
            fh.close()

if __name__ == "__main__":
    test_upload(metadata_no_scanned_files, "Without scanned_files in metadata JSON")
    test_upload(metadata_with_scanned_files, "With scanned_files in metadata JSON")
