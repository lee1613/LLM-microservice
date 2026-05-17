import os
import json
import urllib.request
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def get_api_key():
    with open(".env") as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                return line.strip().split("=", 1)[1]
    return None

api_key = get_api_key()

def generate_text(prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3}
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print("API Error:", e)
        return ""

def create_pdf(txt_path, pdf_path):
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    normal_style = styles["Normal"]
    normal_style.fontName = "Courier"
    normal_style.fontSize = 9
    bold_style = ParagraphStyle('BoldStyle', parent=styles['Normal'], fontName='Courier-Bold', fontSize=10, spaceAfter=6)

    story = []
    with open(txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                story.append(Spacer(1, 10))
                continue
            if line.startswith("```"):
                continue
            if line.startswith("**"):
                story.append(Paragraph(line.replace("**", ""), bold_style))
            elif line.isupper() and len(line) > 5 and ":" not in line:
                story.append(Paragraph(line, bold_style))
            else:
                story.append(Paragraph(line, normal_style))
                
    doc.build(story)

# Load JSONs
claims = ["A002", "A003", "A004", "A005"]
for claim in claims:
    filepath = f"data/health-insurance-claim/synthetic data/claim_{claim}_full_pipeline.json"
    with open(filepath, "r") as f:
        data = json.load(f)
        
    intake = data.get("stage_1_intake", {}).get("_input", {})
    docs = intake.get("supporting_documents", [])
    
    if not docs:
        continue
        
    os.makedirs(f"data/health-insurance-claim/synthetic data/documents/{claim}", exist_ok=True)
    doc_paths = {}
    
    for doc_type in docs:
        print(f"Generating {doc_type} for {claim}...")
        prompt = f"""
        Generate a highly realistic {doc_type} for an insurance claim.
        Patient: {intake.get('claimant_name')}
        Claim Type: {intake.get('claim_type')}
        Amount: {intake.get('claim_amount_requested')} SGD
        Provider: {intake.get('provider_name')}
        Incident Date: {intake.get('incident_date')}
        Make it look like a raw text extraction of a highly structured PDF (use tables and formatting).
        """
        
        # Add specific details if medical_details exist
        if "stage_4_medical_review" in data and "_medical_details" in data["stage_4_medical_review"]:
            med = data["stage_4_medical_review"]["_medical_details"]
            prompt += f"\nICD-10: {med.get('primary_diagnosis_icd10')}\nCPT Codes: {med.get('procedure_cpt_codes')}\n"
            
        txt = generate_text(prompt)
        txt_path = f"data/health-insurance-claim/synthetic data/documents/{claim}/{doc_type}.txt"
        pdf_path = f"data/health-insurance-claim/synthetic data/documents/{claim}/{doc_type}.pdf"
        
        with open(txt_path, "w") as f:
            f.write(txt)
            
        create_pdf(txt_path, pdf_path)
        print(f"Created {pdf_path}")
        
        doc_paths[doc_type] = pdf_path
        
    # Patch the JSON
    if "_output" in data.get("stage_1_intake", {}):
        data["stage_1_intake"]["_output"]["document_paths"] = doc_paths
    if "stage_2_policy_verification" in data and "_output" in data["stage_2_policy_verification"]:
        data["stage_2_policy_verification"]["_output"]["document_paths"] = doc_paths
    if "stage_3_eligibility_check" in data and "_output" in data["stage_3_eligibility_check"]:
        data["stage_3_eligibility_check"]["_output"]["document_paths"] = doc_paths
        
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
        
print("Finished generating A002-A005 documents and patched JSONs.")
