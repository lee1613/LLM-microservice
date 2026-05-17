import json

file_path = "data/health-insurance-claim/synthetic data/claim_A001_full_pipeline.json"
with open(file_path, "r") as f:
    data = json.load(f)

doc_paths = {
    "discharge_summary": "data/health-insurance-claim/synthetic data/documents/A001/discharge_summary.pdf",
    "medical_bill": "data/health-insurance-claim/synthetic data/documents/A001/medical_bill.pdf",
    "pre_auth_approval": "data/health-insurance-claim/synthetic data/documents/A001/pre_auth_approval.pdf"
}

# Add to intake output
data["stage_1_intake"]["_output"]["document_paths"] = doc_paths
data["stage_1_intake"]["_output"]["supporting_documents"] = ["medical_bill", "discharge_summary", "pre_auth_approval"]

# Add to verification output
data["stage_2_policy_verification"]["_output"]["document_paths"] = doc_paths
data["stage_2_policy_verification"]["_output"]["supporting_documents"] = ["medical_bill", "discharge_summary", "pre_auth_approval"]

# Add to eligibility output
data["stage_3_eligibility_check"]["_output"]["document_paths"] = doc_paths
data["stage_3_eligibility_check"]["_output"]["supporting_documents"] = ["medical_bill", "discharge_summary", "pre_auth_approval"]

with open(file_path, "w") as f:
    json.dump(data, f, indent=2)

print("Patched A001 successfully.")
