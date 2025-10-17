#!/usr/bin/env python3
"""Test Cerebras API rate limits and performance"""

import requests
import time
import json

API_KEY = "csk-j5wrhcve3y3hrtdnrh46recfrpc4d85xwdtp4hkffyncydtd"
BASE_URL = "https://api.cerebras.ai/v1"

def test_basic_request():
    """Test a basic request and show rate limits"""
    print("=" * 60)
    print("Testing Basic Request")
    print("=" * 60)

    response = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "qwen-3-235b-a22b-thinking-2507",
            "messages": [
                {"role": "user", "content": "What is the capital of France? Answer in one word."}
            ],
            "temperature": 0.6,
            "top_p": 0.95,
            "max_tokens": 100
        }
    )

    # Print rate limit headers
    print("\nRate Limit Headers:")
    print(f"  Daily Limit:        {response.headers.get('x-ratelimit-limit-requests-day', 'N/A')} requests")
    print(f"  Tokens/Min Limit:   {response.headers.get('x-ratelimit-limit-tokens-minute', 'N/A')} tokens")
    print(f"  Remaining Today:    {response.headers.get('x-ratelimit-remaining-requests-day', 'N/A')} requests")
    print(f"  Remaining Tokens:   {response.headers.get('x-ratelimit-remaining-tokens-minute', 'N/A')} tokens/min")

    # Print response
    data = response.json()
    print(f"\nResponse:")
    print(f"  Status: {response.status_code}")
    print(f"  Model: {data.get('model')}")
    print(f"  Usage: {data.get('usage')}")

    if 'time_info' in data:
        time_info = data['time_info']
        print(f"\nPerformance:")
        print(f"  Queue time:       {time_info.get('queue_time', 0):.3f}s")
        print(f"  Prompt time:      {time_info.get('prompt_time', 0):.3f}s")
        print(f"  Completion time:  {time_info.get('completion_time', 0):.3f}s")
        print(f"  Total time:       {time_info.get('total_time', 0):.3f}s")

        # Calculate tokens/second
        completion_tokens = data['usage'].get('completion_tokens', 0)
        completion_time = time_info.get('completion_time', 1)
        tokens_per_sec = completion_tokens / completion_time if completion_time > 0 else 0
        print(f"  Speed:            {tokens_per_sec:.1f} tokens/second")

    print(f"\nGenerated Text:")
    print(f"  {data['choices'][0]['message']['content'][:200]}...")

    return data

def test_rate_limits(num_requests=10):
    """Test rate limits with multiple rapid requests"""
    print("\n" + "=" * 60)
    print(f"Testing Rate Limits with {num_requests} Rapid Requests")
    print("=" * 60)

    results = []

    for i in range(num_requests):
        start = time.time()

        try:
            response = requests.post(
                f"{BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "qwen-3-235b-a22b-thinking-2507",
                    "messages": [
                        {"role": "user", "content": f"Say 'Request {i+1}' and nothing else."}
                    ],
                    "temperature": 0.6,
                    "max_tokens": 20
                }
            )

            elapsed = time.time() - start

            data = response.json()
            remaining_requests = response.headers.get('x-ratelimit-remaining-requests-day', 'N/A')
            remaining_tokens = response.headers.get('x-ratelimit-remaining-tokens-minute', 'N/A')

            results.append({
                'request': i + 1,
                'status': response.status_code,
                'elapsed': elapsed,
                'remaining_requests': remaining_requests,
                'remaining_tokens': remaining_tokens,
                'usage': data.get('usage', {})
            })

            print(f"Request {i+1:2d}: Status={response.status_code}, "
                  f"Time={elapsed:.2f}s, "
                  f"Remaining={remaining_requests} requests, "
                  f"Tokens={remaining_tokens}/min")

        except Exception as e:
            print(f"Request {i+1:2d}: ERROR - {str(e)}")
            results.append({
                'request': i + 1,
                'error': str(e)
            })

        # Small delay to avoid overwhelming
        time.sleep(0.1)

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    successful = [r for r in results if r.get('status') == 200]
    failed = [r for r in results if 'error' in r or r.get('status') != 200]

    print(f"Successful requests: {len(successful)}/{num_requests}")
    print(f"Failed requests:     {len(failed)}/{num_requests}")

    if successful:
        avg_time = sum(r['elapsed'] for r in successful) / len(successful)
        total_tokens = sum(r.get('usage', {}).get('total_tokens', 0) for r in successful)
        print(f"Average response time: {avg_time:.3f}s")
        print(f"Total tokens used: {total_tokens}")

        if len(successful) > 0:
            first_remaining = successful[0].get('remaining_requests', 'N/A')
            last_remaining = successful[-1].get('remaining_requests', 'N/A')
            print(f"Requests consumed: {first_remaining} -> {last_remaining}")

def test_streaming():
    """Test streaming response"""
    print("\n" + "=" * 60)
    print("Testing Streaming Response")
    print("=" * 60)

    start = time.time()

    response = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "qwen-3-235b-a22b-thinking-2507",
            "messages": [
                {"role": "user", "content": "Count from 1 to 5"}
            ],
            "temperature": 0.6,
            "max_tokens": 100,
            "stream": True
        },
        stream=True
    )

    print("Streaming output:")
    token_count = 0
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                data_str = line[6:]
                if data_str.strip() == '[DONE]':
                    break
                try:
                    data = json.loads(data_str)
                    if 'choices' in data and len(data['choices']) > 0:
                        delta = data['choices'][0].get('delta', {})
                        if 'content' in delta:
                            print(delta['content'], end='', flush=True)
                            token_count += 1
                except json.JSONDecodeError:
                    pass

    elapsed = time.time() - start
    print(f"\n\nStreaming completed in {elapsed:.2f}s")
    print(f"Approximate tokens: {token_count}")

def test_different_models():
    """Test different available models"""
    print("\n" + "=" * 60)
    print("Testing Different Models")
    print("=" * 60)

    models = [
        "qwen-3-235b-a22b-thinking-2507",
        "qwen-3-235b-a22b-instruct-2507",
        "qwen-3-32b",
        "llama-3.3-70b"
    ]

    for model in models:
        print(f"\nTesting: {model}")
        start = time.time()

        try:
            response = requests.post(
                f"{BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "user", "content": "Say hello briefly"}
                    ],
                    "temperature": 0.6,
                    "max_tokens": 50
                }
            )

            elapsed = time.time() - start
            data = response.json()

            print(f"  Status: {response.status_code}")
            print(f"  Time: {elapsed:.2f}s")
            print(f"  Tokens: {data.get('usage', {}).get('total_tokens', 'N/A')}")

            if 'time_info' in data:
                completion_tokens = data['usage'].get('completion_tokens', 0)
                completion_time = data['time_info'].get('completion_time', 1)
                speed = completion_tokens / completion_time if completion_time > 0 else 0
                print(f"  Speed: {speed:.0f} tokens/second")

        except Exception as e:
            print(f"  ERROR: {str(e)}")

if __name__ == "__main__":
    # Run all tests
    test_basic_request()
    test_rate_limits(10)
    test_streaming()
    test_different_models()

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
