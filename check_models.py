
import os
from dotenv import load_dotenv
load_dotenv()
from google import genai

# Using the key from environment variables
api_key = os.environ.get("GOOGLE_API_KEY")

try:
    client = genai.Client(api_key=api_key)
    with open('models_utf8.txt', 'w', encoding='utf-8') as f:
        f.write("Listing models...\n")
        for m in client.models.list():
            f.write(f"Model: {m.name}\n")
            # f.write(f" - Supported generation methods: {m.supported_generation_methods}\n")

except Exception as e:
    with open('models_utf8.txt', 'w', encoding='utf-8') as f:
        f.write(f"Error: {e}\n")
