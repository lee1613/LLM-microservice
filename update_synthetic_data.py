import json
import os
import glob

def update_synthetic_data():
    base_dir = "data/health-insurance-claim/synthetic data"
    claim_files = glob.glob(os.path.join(base_dir, "claim_A00*.json"))
    
    for file_path in claim_files:
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        # 1. Update Node 1 Output
        if "stage_1_intake" in data:
            if "_input" in data["stage_1_intake"] and "_output" in data["stage_1_intake"]:
                n1_input = data["stage_1_intake"]["_input"]
                n1_output = data["stage_1_intake"]["_output"]
                n1_output["id_document_type"] = n1_input["id_document_type"]
                n1_output["id_document_no"] = n1_input["id_document_no"]
                n1_output["date_of_birth"] = n1_input["date_of_birth"]
                n1_output["claimant_relationship"] = n1_input["claimant_relationship"]
            
        # 2. Update Node 2 output
        if "stage_2_policy_verification" in data:
            if "_db_lookups" in data["stage_2_policy_verification"] and "_output" in data["stage_2_policy_verification"]:
                n2_lookups = data["stage_2_policy_verification"]["_db_lookups"]
                n2_output = data["stage_2_policy_verification"]["_output"]
                
                # Extract product code and dependent status from db lookups if missing
                if "policy_product_code" not in n2_output:
                    n2_output["policy_product_code"] = n2_lookups.get("policy_product_code", "UNKNOWN")
                if "dependent_verified" not in n2_output:
                    n2_output["dependent_verified"] = n2_lookups.get("dependent_verified", True)
                if "premium_payment_mode" not in n2_output:
                    n2_output["premium_payment_mode"] = n2_lookups.get("premium_payment_mode", "annual")
                if "policy_start_date" not in n2_output:
                    n2_output["policy_start_date"] = n2_lookups.get("policy_start_date", "2024-01-01")
                if "policy_expiry_date" not in n2_output:
                    n2_output["policy_expiry_date"] = n2_lookups.get("policy_expiry_date", "2026-01-01")
                if "verification_timestamp" not in n2_output:
                    n2_output["verification_timestamp"] = "2025-05-14T10:00:00+08:00"
            
        # 3. Update Node 3 Output
        if "stage_3_eligibility_check" in data:
            n3_val = data["stage_3_eligibility_check"].get("_validation", {})
            n3_output = data["stage_3_eligibility_check"].get("_output", {})
            
            # Remove exclusions
            if "specific_exclusions_triggered" in n3_val:
                del n3_val["specific_exclusions_triggered"]
            if "no_specific_exclusion" in n3_val:
                del n3_val["no_specific_exclusion"]
            if "exclusions_triggered" in n3_output:
                del n3_output["exclusions_triggered"]
                
        # Write back
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
            
    print("Successfully updated all synthetic data files.")

if __name__ == "__main__":
    update_synthetic_data()
