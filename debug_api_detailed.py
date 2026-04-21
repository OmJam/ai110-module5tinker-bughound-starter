#!/usr/bin/env python3
"""
More detailed debug script to see what the API is actually returning.
"""
import os
import sys
from dotenv import load_dotenv

# Load .env file
load_dotenv()

print("=" * 60)
print("DEBUG: Detailed API Response Check")
print("=" * 60)

api_key = os.getenv("GEMINI_API_KEY", "").strip()
print(f"\nAPI Key present: {bool(api_key)}")

import google.generativeai as genai

genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-2.5-flash")

print("\nTest 1: Simple JSON response request")
try:
    response = model.generate_content(
        [
            {"role": "system", "parts": ["Return ONLY valid JSON. No markdown."]},
            {"role": "user", "parts": ['Return {"status": "working"}']},
        ],
        generation_config={"temperature": 0.2},
    )
    print(f"Response object: {response}")
    print(f"Response.text: '{response.text}'")
    print(f"Response.text length: {len(response.text) if response.text else 0}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")

print("\n" + "-" * 60)
print("Test 2: Issue analysis request (like the real app)")
code_snippet = """def greet(name):
    print("Hello", name)
    return True
"""

system_prompt = "You are BugHound, a code review assistant. Return ONLY valid JSON. No markdown, no backticks."
user_prompt = f"""Analyze this Python code for potential issues. Return a JSON array of issue objects with keys: type, severity, msg.

CODE:
{code_snippet}"""

print(f"System prompt: {system_prompt}")
print(f"User prompt length: {len(user_prompt)}")

try:
    response = model.generate_content(
        [
            {"role": "system", "parts": [system_prompt]},
            {"role": "user", "parts": [user_prompt]},
        ],
        generation_config={"temperature": 0.2},
    )
    print(f"Response object type: {type(response)}")
    print(f"Response.text: {response.text}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 60)
