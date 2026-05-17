import json
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone, timedelta, date

def run_tests():
    # Loop over claims A001 to A005
    claims = [
        "claim_A001_full_pipeline.json",
        "claim_A002_full_pipeline.json",
        "claim_A003_full_pipeline.json",
        "claim_A004_full_pipeline.json",
        "claim_A005_full_pipeline.json"
    ]
    
    server_date = datetime.now(timezone(timedelta(hours=8))).date()
    
    for filename in claims:
        print(f"\n=============================================")
        print(f"Testing: {filename}")
        
        json_path = f"data/health-insurance-claim/synthetic data/{filename}"
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        raw_input_dict = data["stage_1_intake"]["_input"]
        expected_output = data["stage_1_intake"]["_output"]
        
        # Dynamically shift dates so that claim_date matches today's server_date.
        # This allows us to pass the strict `claim_date == server_date` check 
        # without failing on incident lag or age limits.
        synthetic_claim_date = datetime.strptime(raw_input_dict["claim_date"], "%Y-%m-%d").date()
        delta_days = (server_date - synthetic_claim_date).days
        
        raw_input_dict["claim_date"] = str(server_date)
        raw_input_dict["incident_date"] = str(datetime.strptime(raw_input_dict["incident_date"], "%Y-%m-%d").date() + timedelta(days=delta_days))
        raw_input_dict["date_of_birth"] = str(datetime.strptime(raw_input_dict["date_of_birth"], "%Y-%m-%d").date() + timedelta(days=delta_days))
        
        raw_text_str = json.dumps(raw_input_dict)
        url = f"http://127.0.0.1:8000/intake/process?raw_text={urllib.parse.quote(raw_text_str)}"
        req = urllib.request.Request(url, method="POST")
        
        try:
            with urllib.request.urlopen(req) as response:
                result_body = response.read().decode('utf-8')
                result_json = json.loads(result_body)
                
                # Assertions
                assert result_json["intake_accepted"] == expected_output["intake_accepted"], f"Expected {expected_output['intake_accepted']} but got {result_json['intake_accepted']}"
                if not result_json["intake_accepted"]:
                    assert result_json["rejection_reason"] == expected_output["rejection_reason"], f"Expected rejection {expected_output['rejection_reason']} but got {result_json['rejection_reason']}"
                else:
                    assert result_json["policy_no"] == expected_output["policy_no"]
                    
                print(f"✅ Test Passed: {filename} output matches expectations!")
                if result_json["rejection_reason"]:
                    print(f"   Rejection Reason: {result_json['rejection_reason']}")
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"❌ API Error {e.code}: {error_body}")
        except AssertionError as e:
            print(f"❌ Assertion Failed: {e}")
            print(f"Result JSON: {result_json}")
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")

if __name__ == "__main__":
    run_tests()
