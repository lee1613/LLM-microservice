import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get('VULTR_SERVERLESS_INFERENCE_API_KEY')

client = OpenAI(
    base_url="https://api.vultrinference.com/v1",
    api_key=api_key
)

pdf_path = r"c:\Users\Lee023\OneDrive - National University of Singapore\Desktop\Project\LLM-microservice\data\health-insurance-claim\synthetic data\documents\B001\medical_bill.pdf"

try:
    with open(pdf_path, "rb") as f:
        file = client.files.create(
            file=f,
            purpose="assistants"
        )
    print("File uploaded successfully, ID:", file.id)
except Exception as e:
    print(f"Error uploading file: {e}")
