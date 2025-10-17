#!/usr/bin/env python3
import requests
import json

response = requests.get(
    'https://api.cerebras.ai/v1/models',
    headers={'Authorization': 'Bearer csk-j5wrhcve3y3hrtdnrh46recfrpc4d85xwdtp4hkffyncydtd'}
)

data = response.json()

print('\nAvailable Models on Cerebras:')
print('=' * 80)
print(f"{'Model ID':<60} {'Owner':<15}")
print('-' * 80)

for model in data['data']:
    model_id = model['id']
    owner = model['owned_by']
    print(f"{model_id:<60} {owner:<15}")

print('=' * 80)
print(f'Total: {len(data["data"])} models')
print()

# Categorize models
print('Model Categories:')
print('=' * 80)

categories = {
    'Qwen Models': [m for m in data['data'] if 'qwen' in m['id'].lower()],
    'Llama Models': [m for m in data['data'] if 'llama' in m['id'].lower()],
    'GPT Models': [m for m in data['data'] if 'gpt' in m['id'].lower()],
}

for category, models in categories.items():
    print(f"\n{category} ({len(models)}):")
    for model in models:
        # Add special indicators
        indicators = []
        if 'thinking' in model['id']:
            indicators.append('💭 Thinking')
        if 'instruct' in model['id']:
            indicators.append('📚 Instruct')
        if 'coder' in model['id']:
            indicators.append('💻 Coding')

        indicator_str = ' | '.join(indicators) if indicators else ''
        print(f"  • {model['id']:<55} {indicator_str}")
