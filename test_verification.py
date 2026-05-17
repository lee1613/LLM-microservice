import json
import urllib.request
import urllib.error
import urllib.parse

def run_tests():
    # Loop over claims A001 to A005
    claims = [
        "claim_A001_full_pipeline.json",
        "claim_A002_full_pipeline.json",
        "claim_A003_full_pipeline.json",
        "claim_A004_full_pipeline.json",
        "claim_A005_full_pipeline.json"
    ]
    
    for filename in claims:
        print(f"\n=============================================")
        print(f"Testing Verification Node: {filename}")
        
        json_path = f"data/health-insurance-claim/synthetic data/{filename}"
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        node1_output = data["stage_1_intake"]["_output"]
        
        # Node 2 input (Schema A) is precisely Node 1 output
        raw_input_dict = node1_output
        expected_output = data["stage_2_policy_verification"]["_output"]
        
        raw_text_str = json.dumps(raw_input_dict)
        url = f"http://127.0.0.1:8000/verification/process?raw_text={urllib.parse.quote(raw_text_str)}"
        req = urllib.request.Request(url, method="POST")
        
        try:
            with urllib.request.urlopen(req) as response:
                result_body = response.read().decode('utf-8')
                result_json = json.loads(result_body)
                
                # Assertions
                assert result_json["policy_verified"] == expected_output["policy_verified"], f"Expected {expected_output['policy_verified']} but got {result_json['policy_verified']}"
                if not result_json["policy_verified"]:
                    assert result_json["verification_failure"] == expected_output["verification_failure"], f"Expected rejection {expected_output['verification_failure']} but got {result_json['verification_failure']}"
                else:
                    assert result_json["policy_no"] == expected_output["policy_no"]
                    
                assert "document_paths" in result_json, "document_paths is missing from the output!"
                assert len(result_json["document_paths"]) > 0, "document_paths is empty!"
                    
                print(f"✅ Test Passed: {filename} output matches expectations!")
                if result_json["verification_failure"]:
                    print(f"   Verification Failure: {result_json['verification_failure']}")
                
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
