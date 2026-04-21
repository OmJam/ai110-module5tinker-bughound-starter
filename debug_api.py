#!/usr/bin/env python3
"""
Debug script to test API key loading and client initialization.
"""
import os
import sys
from dotenv import load_dotenv

# Load .env file
load_dotenv()

print("=" * 60)
print("DEBUG: API Key Setup Check")
print("=" * 60)

# Check 1: Is API key loaded?
api_key = os.getenv("GEMINI_API_KEY", "").strip()
print(f"\n1. API Key loaded from environment: {bool(api_key)}")
if api_key:
    print(f"   First 20 chars: {api_key[:20]}...")

# Check 2: Try to import google.generativeai
print("\n2. Testing google.generativeai import...")
try:
    import google.generativeai as genai

    print("   ✓ Successfully imported google.generativeai")
except ImportError as e:
    print(f"   ✗ Failed to import: {e}")
    sys.exit(1)

# Check 3: Try to create GeminiClient
print("\n3. Testing GeminiClient initialization...")
try:
    from llm_client import GeminiClient

    client = GeminiClient(model_name="gemini-2.5-flash", temperature=0.2)
    print("   ✓ GeminiClient created successfully")
except Exception as e:
    print(f"   ✗ Failed to create GeminiClient: {type(e).__name__}: {e}")
    sys.exit(1)

# Check 4: Try a simple API call
print("\n4. Testing API call with a simple prompt...")
try:
    response = client.complete(
        system_prompt="You are a helpful assistant. Return ONLY valid JSON.",
        user_prompt='Return {"status": "working"} and nothing else.',
    )
    print(f"   ✓ API call succeeded")
    print(f"   Response (first 100 chars): {response[:100]}")
except Exception as e:
    print(f"   ✗ API call failed: {type(e).__name__}: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("All checks passed! API setup appears to be working.")
print("=" * 60)
