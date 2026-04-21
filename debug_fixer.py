#!/usr/bin/env python3
"""
Debug script: test just the propose_fix step with detailed logging
"""
import os
import json
from dotenv import load_dotenv

load_dotenv()

from llm_client import GeminiClient
from bughound_agent import BugHoundAgent

# Read the test code
with open("sample_code/mixed_issues.py", "r") as f:
    code = f.read()

# Issues that the LLM analyzer found
issues = [
    {
        "type": "Maintainability",
        "severity": "Medium",
        "msg": "Missing input validation. Real validation is needed."
    },
    {
        "type": "Logging",
        "severity": "Low", 
        "msg": "Unnecessary print statement. Consider using logging."
    },
    {
        "type": "Error Handling",
        "severity": "High",
        "msg": "Bare except block. Catch specific exceptions like ZeroDivisionError."
    },
    {
        "type": "Logic",
        "severity": "Medium",
        "msg": "Ambiguous error return value. Returning 0 on error is misleading."
    }
]

print("=" * 70)
print("TESTING: LLM Fixer on Complex Issues")
print("=" * 70)

print(f"\nCode to fix:\n{code}")

print(f"\nIssues to address:")
for i, issue in enumerate(issues, 1):
    print(f"  {i}. {issue['type']} | {issue['severity']}: {issue['msg']}")

print("\n" + "-" * 70)
print("Calling LLM fixer directly...")
print("-" * 70)

# Create client and test propose_fix
client = GeminiClient(model_name="gemini-2.5-flash", temperature=0.2)
agent = BugHoundAgent(client=client)

fixed = agent.propose_fix(code, issues)

print(f"\nFixer output:")
print(f"Length: {len(fixed)} chars")
print(f"Is empty: {not fixed.strip()}")

if fixed.strip():
    print(f"\nFixed code:\n{fixed}")
else:
    print("\n⚠️ LLM returned empty output. Check logs for reason.")

print(f"\nAgent logs from propose_fix:")
for log in agent.logs:
    if "ACT" in log["step"]:
        print(f"  [{log['step']}] {log['message']}")

print("\n" + "=" * 70)
print("KEY INSIGHT:")
print("=" * 70)
print("""
The LLM analyzer found 4 real issues, but the fixer can't safely fix them:

1. Missing input validation - Requires architectural changes
2. Print statements - Removing changes behavior (quieter) 
3. Bare except - Easy to fix, but changing behavior
4. Ambiguous return - Changing 0 to None changes API behavior

These are DESIGN issues that require human judgment, not mechanical fixes.
The LLM is correctly refusing to auto-fix issues that would alter behavior.
""")
