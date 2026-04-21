#!/usr/bin/env python3
"""
Test propose_fix on mixed_issues.py to analyze the LLM-generated fix.
"""
import os
from dotenv import load_dotenv

load_dotenv()

from llm_client import GeminiClient
from bughound_agent import BugHoundAgent

# Read the test code
with open("sample_code/mixed_issues.py", "r") as f:
    test_code = f.read()

print("=" * 70)
print("ANALYZING: mixed_issues.py")
print("=" * 70)

print(f"\nOriginal code:\n{test_code}")
print("\n" + "-" * 70)

# Create client and agent
client = GeminiClient(model_name="gemini-2.5-flash", temperature=0.2)
agent = BugHoundAgent(client=client)

# Run the full workflow
result = agent.run(test_code)

print("\n" + "=" * 70)
print("ANALYSIS RESULTS")
print("=" * 70)

# Display issues
print(f"\nIssues detected: {len(result['issues'])}")
for i, issue in enumerate(result['issues'], 1):
    print(f"\n{i}. {issue.get('type')} | {issue.get('severity')}")
    print(f"   {issue.get('msg')}")

# Display proposed fix
fixed_code = result['fixed_code']
print(f"\n" + "-" * 70)
print("PROPOSED FIX:")
print("-" * 70)
print(fixed_code)

# Analyze changes
print("\n" + "=" * 70)
print("ANALYSIS: What Changed?")
print("=" * 70)

original_lines = test_code.strip().split('\n')
fixed_lines = fixed_code.strip().split('\n')

print(f"\nOriginal lines: {len(original_lines)}")
print(f"Fixed lines: {len(fixed_lines)}")

# Check for control flow changes
has_try_except_change = "except:" in test_code and "except:" not in fixed_code
has_except_change = "except Exception" in fixed_code or "except OSError" in fixed_code
has_return_change = test_code.count("return") != fixed_code.count("return")
has_logic_change = test_code.count("if") != fixed_code.count("if") or test_code.count("for") != fixed_code.count("for")

print(f"\nControl flow changes:")
print(f"  Bare except: → Specific exception: {has_except_change}")
print(f"  Return statements: {test_code.count('return')} → {fixed_code.count('return')}")
print(f"  Return values changed: {has_return_change}")

# Check for behavioral changes
has_print_removal = "print(" in test_code and fixed_code.count("print(") < test_code.count("print(")
has_logging_add = "logging" in fixed_code and "logging" not in test_code

print(f"\nBehavioral changes:")
print(f"  Print → Logging conversion: {has_logging_add}")
print(f"  Print statements remaining: {fixed_code.count('print(')}")

# Check for imports
has_new_imports = "import" in fixed_code and fixed_code.split('\n')[0] != test_code.split('\n')[0]
print(f"  New imports added: {has_new_imports}")

# Risk assessment
print(f"\n" + "-" * 70)
print("RISK ASSESSMENT:")
print(f"-" * 70)
risk = result.get('risk', {})
print(f"Risk level: {risk.get('level', 'unknown').upper()}")
print(f"Risk score: {risk.get('score', '-')}")
print(f"Auto-fix recommended: {risk.get('should_autofix', False)}")

# Agent trace
print(f"\n" + "-" * 70)
print("AGENT TRACE:")
print(f"-" * 70)
for log in result['logs']:
    print(f"[{log['step']}] {log['message']}")

print("\n" + "=" * 70)
