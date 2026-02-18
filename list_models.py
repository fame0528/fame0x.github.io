import google.genai as genai
import os

api_key = os.getenv('GEMINI_API_KEY') or "AIzaSyDKULC-j0aZdAsob2ULGnybzfh1TIPsrOQ"
client = genai.Client(api_key=api_key)

try:
    models = client.models.list()
    print("Available models:")
    for model in models:
        print(f" - {model.name}")
except Exception as e:
    print(f"Error listing models: {e}")