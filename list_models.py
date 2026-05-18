import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get('VULTR_SERVERLESS_INFERENCE_API_KEY')

client = OpenAI(
    base_url="https://api.vultrinference.com/v1",
    api_key=api_key
)

try:
    models = client.models.list()
    for m in models.data:
        print(m.id)
except Exception as e:
    print(f"Error: {e}")
