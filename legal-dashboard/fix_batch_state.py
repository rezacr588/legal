#!/usr/bin/env python3
"""
Script to replace all batch_generation_state references with batch_state
in the batch_generate_worker function
"""

import re

# Read the file
with open('api_server.py', 'r') as f:
    content = f.read()

# Find the batch_generate_worker function (from def to the end of the function before next @app.route)
# We'll replace batch_generation_state with batch_state inside this function

# Replace pattern - we want to replace batch_generation_state with batch_state
# But we need to be smart - in some places we need locking, in others the state is already local

replacements = [
    # Direct replacements within the function
    ("current_count + batch_generation_state['samples_generated']", "current_count + batch_state['samples_generated']"),
    ("batch_generation_state.get('batch_id')", "batch_id"),  # We have batch_id as parameter now
    ("batch_generation_state['samples_generated']", "batch_state['samples_generated']"),
    ("batch_generation_state['total_tokens']", "batch_state['total_tokens']"),
    ("batch_generation_state['consecutive_failures']", "batch_state['consecutive_failures']"),
    ("batch_generation_state['circuit_breaker_summary']", "batch_state['circuit_breaker_summary']"),
    ("batch_generation_state['errors']", "batch_state['errors']"),
    ("batch_generation_state['failed_models_by_provider']", "batch_state['failed_models_by_provider']"),
    ("batch_generation_state['model_switches']", "batch_state['model_switches']"),
    ("batch_generation_state['current_provider']", "batch_state['current_provider']"),
    ("batch_generation_state['current_model']", "batch_state['current_model']"),
    ("batch_generation_state['provider_switches']", "batch_state['provider_switches']"),
    ("batch_generation_state['skipped_topics']", "batch_state['skipped_topics']"),
    ("batch_generation_state['progress']", "batch_state['progress']"),
    ("batch_generation_state['running']", "batch_state['running']"),
    ("batch_generation_state['completed_at']", "batch_state['completed_at']"),
    ("batch_generation_state[\"consecutive_failures\"]", "batch_state[\"consecutive_failures\"]"),
    ("batch_generation_state[\"samples_generated\"]", "batch_state[\"samples_generated\"]"),
]

for old, new in replacements:
    content = content.replace(old, new)

# Write back
with open('api_server.py', 'w') as f:
    f.write(content)

print("✅ Replaced all batch_generation_state references in worker function")
