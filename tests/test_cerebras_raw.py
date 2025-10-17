#!/usr/bin/env python3
import requests
import json

API_KEY = "csk-j5wrhcve3y3hrtdnrh46recfrpc4d85xwdtp4hkffyncydtd"

print("Testing Cerebras API directly...")
print("=" * 60)

# Test prompt
prompt = """You are a UK legal expert. Generate ONE realistic legal training sample.

Generate a sample with a practical legal question about Contract Law - Formation of Contracts.

Return ONLY a valid JSON object with this exact structure:
{
    "id": "contract_law_formation_001",
    "question": "question text",
    "answer": "comprehensive answer",
    "topic": "Contract Law - Formation of Contracts",
    "difficulty": "basic",
    "case_citation": "Real UK cases",
    "reasoning": "Step 1: ... Step 2: ..."
}"""

response = requests.post(
    'https://api.cerebras.ai/v1/chat/completions',
    headers={
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    },
    json={
        'model': 'qwen-3-235b-a22b-thinking-2507',
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.6,
        'top_p': 0.95,
        'max_tokens': 4000
    },
    timeout=120
)

print(f"Status Code: {response.status_code}")
print(f"Headers: {dict(response.headers)}")
print()
print("Response JSON:")
print(json.dumps(response.json(), indent=2))
print()

if response.status_code == 200:
    data = response.json()
    content = data['choices'][0]['message']['content']
    print("="* 60)
    print("Response Content:")
    print("=" * 60)
    print(content[:1000])  # Print first 1000 characters
    print()
    print(f"Content length: {len(content)} characters")
