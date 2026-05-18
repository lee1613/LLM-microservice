import os
import sys
import traceback
sys.stdout.reconfigure(encoding='utf-8')
from app.intake.tools import extract_document_summary
from dotenv import load_dotenv

load_dotenv()

pdf_paths = ["B001/medical_bill.pdf", "B001/discharge_summary.pdf", "B001/pre_auth_approval.pdf"]
claim_type = "hospitalisation"
requested_amount = 18500.0

print("Running extract_document_summary direct test...")
try:
    res = extract_document_summary(pdf_paths, claim_type, requested_amount)
    print("Result:", res)
except Exception as e:
    print("Direct Exception:", e)
    traceback.print_exc()
