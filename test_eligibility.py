import json
import urllib.request
import urllib.error
import urllib.parse

def run_tests():
    claims = [
        "claim_A001_full_pipeline.json",
        "claim_A002_full_pipeline.json",
        "claim_A003_full_pipeline.json",
        "claim_A004_full_pipeline.json",
        "claim_A005_full_pipeline.json"
    ]
    
    for filename in claims:
        print(f"\n=============================================")
        print(f"Testing Eligibility Node: {filename}")
        
        json_path = f"data/health-insurance-claim/synthetic data/{filename}"
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        # For A005, Node 2 rejects it. In a real pipeline, Node 3 wouldn't run.
        # But we will test it anyway to ensure it behaves correctly if forced.
        # But wait, Node 3 requires Node 2's output!
        
        raw_input_dict = data["stage_2_policy_verification"]["_output"]
        
        # We also need to get expected_output from stage 3
        if "stage_3_eligibility_check" not in data or "_output" not in data["stage_3_eligibility_check"]:
            print(f"⏭️ Skipping {filename} (No Node 3 expected output)")
            continue
            
        expected_output = data["stage_3_eligibility_check"]["_output"]
        
        raw_text_str = json.dumps(raw_input_dict)
        url = f"http://127.0.0.1:8000/eligibility/process?raw_text={urllib.parse.quote(raw_text_str)}"
        req = urllib.request.Request(url, method="POST")
        
        try:
            with urllib.request.urlopen(req) as response:
                result_body = response.read().decode('utf-8')
                result_json = json.loads(result_body)
                
                # Assertions
                assert result_json["eligible"] == expected_output["eligible"], f"Expected eligible={expected_output['eligible']} but got {result_json['eligible']}"
                
                if not result_json["eligible"]:
                    assert result_json["eligibility_failure_reason"] == expected_output["eligibility_failure_reason"], f"Expected rejection {expected_output['eligibility_failure_reason']} but got {result_json['eligibility_failure_reason']}"
                else:
                    assert result_json["policy_no"] == expected_output["policy_no"]
                    assert result_json["claimable_ceiling"] == expected_output["claimable_ceiling"]
                    
                assert "document_paths" in result_json, "document_paths is missing from the output!"
                assert len(result_json["document_paths"]) > 0, "document_paths is empty!"
                    
                print(f"✅ Test Passed: {filename} output matches expectations!")
                if result_json["eligibility_failure_reason"]:
                    print(f"   Eligibility Failure: {result_json['eligibility_failure_reason']}")
                
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
