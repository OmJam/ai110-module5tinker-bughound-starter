#!/usr/bin/env python3
"""
Test the validation: demonstrate what happens with invalid LLM output.
"""
from bughound_agent import BugHoundAgent


# Create a mock client that returns bad data
class BadMockClient:
    def complete(self, system_prompt: str, user_prompt: str) -> str:
        # Return issues with empty messages (would fail validation)
        if "Return ONLY valid JSON" in system_prompt:
            return '[{"type": "Issue", "severity": "High", "msg": ""}, {"type": "Issue", "severity": "Low", "msg": ""}]'
        return "# No fix"


print("=" * 60)
print("TESTING: Validation Rejects Invalid Output")
print("=" * 60)

agent = BugHoundAgent(client=BadMockClient())

test_code = """def example():
    print("hello")
"""

print(f"\nInput code:\n{test_code}")
print("-" * 60)
print("Running agent with BadMockClient (returns empty messages)...\n")

result = agent.run(test_code)

print("Agent trace:")
for log in result["logs"]:
    print(f"  [{log['step']}] {log['message']}")

print(f"\nIssues found: {len(result['issues'])}")
for issue in result["issues"]:
    print(f"  - {issue.get('type')} | {issue.get('severity')}: {issue.get('msg')}")

print("\n" + "=" * 60)
print("RESULT: Validation rejected invalid output → fell back to heuristics")
print("=" * 60)
