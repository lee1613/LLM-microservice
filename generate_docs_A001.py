import os
import json
import urllib.request
def get_api_key():
    with open(".env") as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                return line.strip().split("=", 1)[1]
    return None

api_key = get_api_key()

if not api_key:
    print("Error: GEMINI_API_KEY not found in .env")
    exit(1)

def generate_text(prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4}
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print("API Error:", e)
        if hasattr(e, 'read'):
            print(e.read().decode())
        raise

prompt_discharge = """
Generate a highly realistic Discharge Summary for a patient named Tan Wei Ming at Singapore General Hospital.
Details:
- Admission Date: 2025-04-10
- Discharge Date: 2025-04-14
- Attending Physician: Dr. Chong Wei Liang (MCR-10234A)
- Primary Diagnosis: Pneumonia, unspecified organism (ICD-10: J18.9)
- Procedures/Interventions: Subsequent hospital inpatient visits (CPT 99232) and Chest X-ray, 2 views (CPT 71046).
- Include realistic sections like Chief Complaint, History of Present Illness, Hospital Course, Discharge Medications, and Follow-up.
Make it look like a raw text extraction of a PDF.
"""

prompt_bill = """
Generate a highly realistic Medical Bill/Invoice for a patient named Tan Wei Ming at Singapore General Hospital.
Details:
- Admission Date: 2025-04-10
- Discharge Date: 2025-04-14
- Total Amount: 18,500.00 SGD
- Include line items that would sum up to this amount, prominently including charges for:
  * Inpatient visits (corresponding to CPT 99232)
  * Chest X-ray, 2 views (corresponding to CPT 71046)
  * Room and board (4 days)
  * Medications (IV antibiotics, etc)
- Pre-authorisation Reference: PA-2025-001234
Make it look tabular or heavily formatted with invoice numbers, dates, and amounts, as if extracted from a PDF.
"""

prompt_preauth = """
Generate a highly realistic Pre-Authorisation Approval Letter from 'HealthSure Insurance'.
Details:
- Policy Holder/Patient: Tan Wei Ming
- Policy Number: HIC-2024-00123
- Pre-auth Number: PA-2025-001234
- Hospital: Singapore General Hospital
- Attending Physician: Dr. Chong Wei Liang
- Diagnosis: Pneumonia (J18.9)
- Status: Approved
- Date Issued: 2025-04-09
Make it read like a formal insurance approval letter acknowledging coverage up to policy limits for the planned admission.
"""

print("Generating Discharge Summary...")
discharge_txt = generate_text(prompt_discharge)

print("Generating Medical Bill...")
bill_txt = generate_text(prompt_bill)

print("Generating Pre-Auth Approval...")
preauth_txt = generate_text(prompt_preauth)

os.makedirs("data/health-insurance-claim/synthetic data/documents/A001", exist_ok=True)

with open("data/health-insurance-claim/synthetic data/documents/A001/discharge_summary.txt", "w") as f:
    f.write(discharge_txt)
    
with open("data/health-insurance-claim/synthetic data/documents/A001/medical_bill.txt", "w") as f:
    f.write(bill_txt)
    
with open("data/health-insurance-claim/synthetic data/documents/A001/pre_auth_approval.txt", "w") as f:
    f.write(preauth_txt)

print("Successfully generated A001 documents.")
