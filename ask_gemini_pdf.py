import os
import json
import urllib.request
import re

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

prompt = """
You are a Python expert. I have 3 text files in 'data/health-insurance-claim/synthetic data/documents/A001/':
- discharge_summary.txt
- medical_bill.txt
- pre_auth_approval.txt

These files contain raw text of medical documents.
Write a COMPLETE Python script using the 'fpdf2' library (import FPDF) that reads these 3 text files and generates corresponding 3 PDF files (discharge_summary.pdf, medical_bill.pdf, pre_auth_approval.pdf) in the same directory.
Make the PDFs look "highly realistic" - e.g., use Arial/Helvetica, add bolding for headers, use multi_cell for text, add a fake hospital name at the top. 
Just read the text line by line and format it nicely. For example, lines in all caps or starting with "**" should be bolded in the PDF.
Output ONLY the python code inside a ```python block, nothing else.
"""

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
payload = {
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {"temperature": 0.2}
}
data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

print("Asking Gemini to write the PDF generation script...")
with urllib.request.urlopen(req) as response:
    result = json.loads(response.read().decode())
    content = result['candidates'][0]['content']['parts'][0]['text']
    
    # Extract python code
    match = re.search(r"```python\n(.*?)\n```", content, re.DOTALL)
    if match:
        code = match.group(1)
        with open("create_realistic_pdfs.py", "w") as f:
            f.write(code)
        print("Successfully generated create_realistic_pdfs.py using Gemini!")
    else:
        print("Failed to parse python code from Gemini response:", content)
