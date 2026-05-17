import json
import urllib.request
import urllib.error
import urllib.parse
import os
import time
import subprocess

def run_tests():
    # Only claims that successfully passed Node 3 reach Node 4
    claims = [
        "claim_A001_full_pipeline.json",
        "claim_A002_full_pipeline.json",
        "claim_A004_full_pipeline.json"
    ]
    
    for filename in claims:
        print(f"\n=============================================")
        print(f"Testing Medical Review Node: {filename}")
        
        json_path = f"data/health-insurance-claim/synthetic data/{filename}"
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        raw_input_dict = data["stage_3_eligibility_check"]["_output"]
        
        # We also need to add provider registration manually since we didn't add it to Node 3 output directly in previous synthetic tests
        if filename == "claim_A001_full_pipeline.json":
            raw_input_dict["provider_registration"] = "MOH-HOSP-00142"
        elif filename == "claim_A002_full_pipeline.json":
            raw_input_dict["provider_registration"] = "MOH-CLIN-00887"
        elif filename == "claim_A004_full_pipeline.json":
            raw_input_dict["provider_registration"] = "PRV-HOSP-09921"
            
        expected_output = data["stage_4_medical_review"]["_output"]
        
        raw_text_str = json.dumps(raw_input_dict)
        url = f"http://127.0.0.1:8000/medical/process"
        
        # Ensure we pass it cleanly
        req = urllib.request.Request(url, data=raw_text_str.encode('utf-8'), headers={'Content-Type': 'application/json'}, method="POST")
        
        print("Sending request... (This will trigger the Vultr Serverless LLM Extraction)")
        start_time = time.time()
        
        try:
            with urllib.request.urlopen(req) as response:
                result_body = response.read().decode('utf-8')
                result_json = json.loads(result_body)
                
                print(f"Extraction & Validation complete in {time.time() - start_time:.2f}s")
                
                # Assertions
                assert result_json["medical_review_passed"] == expected_output["medical_review_passed"], f"Expected {expected_output['medical_review_passed']} but got {result_json['medical_review_passed']}"
                
                # Optional: display the benchmark and failure reason for debugging
                if not result_json["medical_review_passed"]:
                    print(f"   Failure Reason: {result_json['review_failure_reason']}")
                if "medical_flags" in result_json:
                    print(f"   Flags: {result_json['medical_flags']}")
                    
                print(f"✅ Test Passed: {filename} Medical Review logic holds!")
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"❌ API Error {e.code}: {error_body}")
        except AssertionError as e:
            print(f"❌ Assertion Failed: {e}")
            print(f"Expected: {expected_output}")
            print(f"Result: {result_json}")
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")

if __name__ == "__main__":
    run_tests()
