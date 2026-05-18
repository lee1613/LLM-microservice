import os
from openai import OpenAI
from dotenv import load_dotenv
import fitz  # PyMuPDF

load_dotenv()
api_key = os.environ.get('VULTR_SERVERLESS_INFERENCE_API_KEY')

client = OpenAI(
    base_url="https://api.vultrinference.com/v1",
    api_key=api_key
)

pdf_path = r"c:\Users\Lee023\OneDrive - National University of Singapore\Desktop\Project\LLM-microservice\data\health-insurance-claim\synthetic data\documents\B001\medical_bill.pdf"

import base64
with open(pdf_path, "rb") as f:
    pdf_base64 = base64.b64encode(f.read()).decode("utf-8")
doc = fitz.open(pdf_path)
text = ""
for page in doc:
    text += page.get_text()

try:
    response = client.chat.completions.create(
        model="nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Please extract the total billed amount from this medical bill."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:application/pdf;base64,{pdf_base64}"
                        }
                    }
                ]
            }
        ]
    )
    print("Response:")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Error: {e}")
