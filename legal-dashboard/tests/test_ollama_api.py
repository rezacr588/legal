import requests
import json

api_key = "09c0a66a183949a7af9a92ef386a526b.scZcSuUZwFQ8uUMt04qvKYYR"

headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}

payload = {
    'model': 'gpt-oss:20b-cloud',
    'messages': [{'role': 'user', 'content': 'Say hello in one sentence'}],
    'stream': False
}

try:
    response = requests.post(
        'https://ollama.com/api/chat',
        headers=headers,
        json=payload,
        timeout=30
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"\nResponse Body:")
    print(json.dumps(response.json(), indent=2))

except Exception as e:
    print(f"Error: {type(e).__name__}: {str(e)}")
    print(f"Response text: {response.text if 'response' in locals() else 'N/A'}")
