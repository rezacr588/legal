#!/usr/bin/env python3
"""
Test script to reproduce and fix the stop batch issue.
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:5001/api"

def start_batch():
    """Start a test batch"""
    print("1. Starting a test batch...")
    response = requests.post(f"{BASE_URL}/generate/batch/start", json={
        "target_count": 7520,
        "provider": "groq",
        "model": "llama-3.3-70b-versatile"
    })
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
    return response.json().get('batch_id')

def check_status():
    """Check current batch status"""
    print("\n2. Checking batch status...")
    response = requests.get(f"{BASE_URL}/generate/batch/status")
    data = response.json()
    print(f"   Status: {response.status_code}")
    print(f"   Active batches: {data.get('count', 0)}")
    if data.get('batches'):
        for batch_id, batch in data['batches'].items():
            print(f"   - {batch_id}: running={batch.get('running')}, progress={batch.get('progress')}/{batch.get('total')}")
    return data

def stop_batch_no_body():
    """Try to stop batch WITHOUT body (incorrect)"""
    print("\n3. Testing stop WITHOUT body (might fail)...")
    try:
        response = requests.post(f"{BASE_URL}/generate/batch/stop",
                                headers={'Content-Type': 'application/json'})
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"   Error: {e}")
        return False

def stop_batch_with_body():
    """Try to stop batch WITH empty body (correct)"""
    print("\n4. Testing stop WITH empty body (should work)...")
    try:
        response = requests.post(f"{BASE_URL}/generate/batch/stop",
                                headers={'Content-Type': 'application/json'},
                                json={})
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"   Error: {e}")
        return False

def main():
    print("="*80)
    print("  STOP BATCH FUNCTIONALITY TEST")
    print("="*80)

    # Start a batch
    batch_id = start_batch()
    if not batch_id:
        print("\n❌ Failed to start batch!")
        return

    # Wait a moment for batch to initialize
    time.sleep(2)

    # Check status
    status = check_status()
    if status.get('count', 0) == 0:
        print("\n❌ No active batches found!")
        return

    # Try stopping without body
    success1 = stop_batch_no_body()

    # Check if it worked
    time.sleep(1)
    status = check_status()

    if status.get('count', 0) > 0:
        print("\n⚠️  Stop without body did NOT work")

        # Try with body
        success2 = stop_batch_with_body()

        # Check again
        time.sleep(1)
        status = check_status()

        if status.get('count', 0) == 0:
            print("\n✅ Stop WITH body worked!")
            print("\nISSUE IDENTIFIED: Frontend must send body parameter")
        else:
            print("\n❌ Stop still didn't work - backend issue?")
    else:
        print("\n✅ Stop without body worked!")

    print("\n" + "="*80)
    print("  TEST COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
