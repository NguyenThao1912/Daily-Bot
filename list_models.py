from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("Listing models for v1:")
try:
    for m in client.models.list(config={'api_version': 'v1'}):
        print(f"- {m.name}")
except Exception as e:
    print(f"Error v1: {e}")

print("\nListing models for v1beta:")
try:
    for m in client.models.list(config={'api_version': 'v1beta'}):
        print(f"- {m.name}")
except Exception as e:
    print(f"Error v1beta: {e}")
