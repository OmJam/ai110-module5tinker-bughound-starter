#!/usr/bin/env python3
"""
Test the full BugHound agent workflow with the fixed client.
"""
import os
from dotenv import load_dotenv

load_dotenv()

from llm_client import GeminiClient
from bughound_agent import BugHoundAgent

print("=" * 60)
print("TESTING: Full BugHound Agent Workflow")
print("=" * 60)

# Create a real Gemini client
try:
    client = GeminiClient(model_name="gemini-2.5-flash", temperature=0.2)
    print("\n✓ Gemini client created successfully")
except Exception as e:
    print(f"\n✗ Failed to create client: {e}")
    exit(1)

# Test code sample with issues
test_code = """def load_data(path):
    try:
        data = open(path).read()
    except:
        return None
    return data
"""

print(f"\nTest code:\n{test_code}")
print("-" * 60)

# Run the agent
agent = BugHoundAgent(client=client)
print("\nRunning BugHound agent...")

result = agent.run(test_code)

print("\n" + "=" * 60)
print("RESULTS")
print("=" * 60)

print(f"\nIssues found: {len(result['issues'])}")
for i, issue in enumerate(result["issues"], 1):
    print(f"\n  {i}. {issue.get('type')} | {issue.get('severity')}")
    print(f"     {issue.get('msg')}")

print(f"\nFixed code:\n{result['fixed_code']}")

print(f"\nRisk assessment: {result['risk']}")

print(f"\nAgent trace:")
for log in result["logs"]:
    print(f"  [{log['step']}] {log['message']}")

print("\n" + "=" * 60)
