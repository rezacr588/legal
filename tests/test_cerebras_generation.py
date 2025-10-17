#!/usr/bin/env python3
import requests
import json

print("Testing Cerebras sample generation...")

response = requests.post(
    'http://127.0.0.1:5001/api/generate',
    json={
        'practice_area': 'Contract Law',
        'topic': 'Formation of Contracts',
        'difficulty': 'basic',
        'provider': 'cerebras',
        'model': 'qwen-3-235b-a22b-thinking-2507'
    },
    timeout=120
)

print(f"\nStatus Code: {response.status_code}")
print(f"Response:")
print(json.dumps(response.json(), indent=2))
