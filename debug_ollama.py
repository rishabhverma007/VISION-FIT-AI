
import ollama
import json

try:
    print("Listing models...")
    response = ollama.list()
    print("Type of response:", type(response))
    print("Raw response:", response)
    
    if hasattr(response, 'models'):
        print("Response has 'models' attribute (Pydantic style?)")
    
    if isinstance(response, dict):
        print("Response is a dict")
        if 'models' in response:
            print("First model sample:", response['models'][0])
            print("First model keys:", response['models'][0].keys() if isinstance(response['models'][0], dict) else dir(response['models'][0]))

except Exception as e:
    print(f"Error: {e}")
