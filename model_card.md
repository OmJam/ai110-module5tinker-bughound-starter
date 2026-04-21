# BugHound Mini Model Card (Reflection)

Fill this out after you run BugHound in **both** modes (Heuristic and Gemini).

---

## 1) What is this system?

**Name:** BugHound  
**Purpose:** Analyze a Python snippet, propose a fix, and run reliability checks before suggesting whether the fix should be auto-applied.

**Intended users:** Students learning agentic workflows and AI reliability concepts.

---

## 2) How does it work?

The agent executes a five-step agentic loop:

1. **PLAN:** Log the workflow and prepare to scan the code.
2. **ANALYZE:** Detect issues by applying pattern-matching heuristics (print statements, bare except blocks, TODO comments) or by querying a LLM (Gemini) if available. Falls back to heuristics if the LLM returns invalid JSON or if no client is configured.
3. **ACT:** Propose a fix by applying heuristic transformations (e.g., replace `print()` with `logging.info()`, replace `except:` with `except Exception as e:`) or by requesting a fix from the LLM. Falls back to heuristics on LLM failure.
4. **TEST:** Run the risk assessor to score the fix from 0–100 based on: issue severity, structural changes (missing returns, code length reduction), bare exception modifications, introduced dangerous patterns (eval, exec, shell=True), and malformed logging replacements.
5. **REFLECT:** Decide whether to auto-apply the fix. Auto-fixes only if risk level is "low" (score ≥ 75). Otherwise, require human review.

**Heuristic mode** (primary, always available): Pattern-based issue detection and string replacement fixes. Fast, offline, no API costs, but limited in scope.  
**Gemini mode** (optional, if LLM client provided): More nuanced issue detection and fix generation, but introduces parsing risk and API latency/costs. Falls back to heuristics on any error.

---

## 3) Inputs and outputs

**Inputs tested:**

1. **cleanish.py**: A short 5-line module with an `add()` function using proper logging. Already clean, no issues expected.
2. **mixed_issues.py**: A `compute_ratio()` function with print statement, bare except block, and TODO comment. Multiple issues.
3. **print_spam.py**: A `greet()` function with three print statements (including multi-argument `print(“Hello”, name)`). Code Quality issue only.
4. **flaky_try_except.py**: A `load_text_file()` function with bare except and file I/O without context manager. Reliability issue.
5. **Comments-only edge case**: A file with only comments, no executable code. Edge case to test robustness.

Shape of inputs: Small functions (5–10 lines), single-function modules, no complex control flow.

**Outputs generated:**

- **Issue types detected**: Code Quality (print statements), Reliability (bare except), Maintainability (TODO comments)
- **Fixes proposed**: 
  - Add `import logging` header
  - Replace `print(` with `logging.info(`
  - Replace `except:` with `except Exception as e:` + comment
- **Risk reports**:
  - Cleanish.py: score 100, level “low”, should_autofix=True (no changes needed)
  - Mixed_issues.py: score 30, level “high”, should_autofix=False (3 issues, requires review)
  - Print_spam.py: score 65 (after guardrails), level “medium”, should_autofix=False (multi-arg print→logging detected as broken)
  - Flaky_try_except.py: score unrecorded but similar profile to mixed_issues

---

## 4) Reliability and safety rules

### Rule 1: Return Statement Removal Detection (-30 points)

**What it checks:** If the original code contains a `return` statement but the fixed code does not, deduct 30 points.

**Why it matters:** Removing a return statement is a structural regression that silently changes function behavior. A function that should return a value will now return `None`, breaking callers' expectations and potentially causing crashes downstream. This is a high-confidence signal of a broken fix.

**False positives:** A function initially returning `None` implicitly could legitimately have its explicit `return` removed (e.g., `return None` → no return statement). The rule triggers even though this is harmless. Also triggers if only some return paths are removed, not all.

**False negatives:** The rule checks only for the presence of the word "return" as a substring, not AST-level analysis. It could miss: (1) return statements moved to a different code path, (2) refactored code with return in a closure or nested function, (3) return statements hidden inside strings or comments.

### Rule 2: Malformed Logging Replacement Detection (-30 points)

**What it checks:** If the original code has multi-argument `print()` calls (e.g., `print("Hello", name)`) AND the fixed code introduces `logging.info(` (not present in original), deduct 30 points.

**Why it matters:** The heuristic print→logging replacement is naive: it does `str.replace("print(", "logging.info(")` without understanding the API difference. `print()` accepts multiple positional arguments; `logging.info()` only takes a format string as arg #1. This produces code that raises `TypeError` at runtime.

**False positives:** If original code already uses `logging.info()` somewhere, the rule doesn't fire (checking for introduction only). Single-argument print calls (most benign) don't trigger the multi-arg pattern match, so they pass through safely. Minimal false positives by design.

**False negatives:** The rule uses regex `r'print\([^)]+,[^)]+\)'` which misses: (1) multi-arg print with nested parens like `print(func(x), y)`, (2) print with complex expressions before a comma, (3) logging.info() calls introduced by LLM (not heuristic), which may have the same issue but aren't caught here.

---

## 5) Observed failure modes

### Failure Mode 1: Broken logging.info() from Multi-Argument print() Replacement

**Snippet:**
```python
def greet(name, verbose=False):
    if verbose:
        print("Entering greet()")
    print("Hello", name)  # Multi-arg print!
    print("Welcome!")
    return True
```

**What went wrong:** The heuristic fixer naively replaced `print(` with `logging.info(`, producing:
```python
logging.info("Hello", name)  # TypeError! logging.info() doesn't accept positional args
```

**Impact:** This code appears syntactically valid but raises `TypeError: logging.info() takes exactly 1 positional argument` at runtime. Without the malformed logging replacement guardrail, the agent would score this 95 (low risk) and auto-apply a broken fix.

**Root cause:** The heuristic replacement doesn't understand the API difference between `print(*args)` (variadic) and `logging.info(msg, *args, **kwargs)` (format-based).

---

### Failure Mode 2: Over-Editing with Broad Transformations

**Context:** When the agent detects "Code Quality" issues (print statements), it applies a blanket transformation:
```python
if "import logging" not in fixed:
    fixed = "import logging\n\n" + fixed
fixed = fixed.replace("print(", "logging.info(")
```

**What went wrong:** For `mixed_issues.py`, the agent detects three separate issues (print, bare except, TODO) but applies three independent fixes in sequence. The result is a file where all print calls are replaced across the entire module, not just the ones that are actually problematic. If the module has 10 functions with print and only 2 are problematic, all 10 get modified, increasing the blast radius and risk of unintended side effects.

**Impact:** Score correctly reflects high risk (30), but the fix is too broad. A better approach would narrow the scope: only replace prints in the function(s) where the issue was actually detected.

---

**Summary:** The system catches *some* unreliability (score goes high) but only *after* producing a broken fix. Ideally, guardrails would prevent broken fixes from being generated in the first place.

---

## 6) Heuristic vs Gemini comparison

**Testing note:** The Gemini integration is optional; I tested only heuristic mode (always available, offline-first). The MockClient in tests confirms the fallback mechanism works, but I did not run full LLM integration tests.

### Heuristic Mode (Observed)

**Consistent detections:**
- Print statements (pattern: `print(`)
- Bare except blocks (pattern: `except:`)
- TODO comments (pattern: `# TODO` or `# FIXME`)

**Fix generation:**
- Always available, no latency
- Predictable transformations (string replace)
- No semantic understanding of code behavior

**Failure modes:**
- Naive API replacement (print→logging.info without adapting arguments)
- No understanding of context (doesn't know if print is for debugging vs user-facing output)
- Cannot detect subtle semantic issues (e.g., uninitialized variables, logic errors)

### Gemini Mode (Expected behavior, not tested)

**Would likely improve:**
- Semantic issue detection (logic errors, type mismatches, unreachable code)
- Context-aware fixes (adapt print to logging with correct formatting)
- Broader issue categories (complexity, testability, performance anti-patterns)

**Would likely introduce risks:**
- Parsing failures (LLM output might not be valid JSON or code)
- Hallucinations (generating plausible-sounding but incorrect fixes)
- Latency and cost (API calls, rate limits)
- Inconsistency (same code analyzed twice might yield different results)

### Risk Scorer Agreement

The risk scorer was conservative and aligned with my intuition:
- Cleanish.py (no issues) → low risk ✓
- Mixed_issues.py (3 serious issues) → high risk ✓
- Print_spam.py (broken logging replacement) → medium risk after guardrails ✓

The guardrails I added (dangerous patterns + malformed logging replacement) successfully caught cases where the heuristic fixer produced broken code.

---

## 7) Human-in-the-loop decision

### Scenario: Bare Except Modification with Error Handling

**Situation:** BugHound detects a bare `except:` block and proposes replacing it with `except Exception as e:`. While this is technically "safer," it changes exception handling semantics:

```python
# Original
try:
    load_config()
except:
    return default_config()

# Proposed fix
try:
    load_config()
except Exception as e:
    # [BugHound] log or handle the error
    return default_config()
```

**Why human review is needed:** The bare except might be intentional (catch ALL exceptions including SystemExit, KeyboardInterrupt). Changing it could allow the program to exit ungracefully on CTRL+C, hiding resource leaks. The fix is "safer" in one sense but could be *wrong* in context.

### Proposed Trigger

**Condition:** If the fix modifies an `except:` block AND the issue severity is "Reliability" AND the original code does not already have explicit exception type handling, require human confirmation before auto-applying.

**Implementation location:** `bughound_agent.py`, in the `reflect()` step after risk assessment. Add a second veto: even if risk is "low", refuse auto-fix if bare except modification is detected.

**Message to show user:**
```
⚠️  HUMAN REVIEW REQUIRED
BugHound detected a bare except: block and proposes making it more specific.
This changes exception handling semantics—what should be caught?

Original:
  except:
      # catches everything, including KeyboardInterrupt, SystemExit

Proposed:
  except Exception as e:
      # catches only regular exceptions, allows system signals through

⚠️  RECOMMENDATION: Review the original exception handling intent.
If you intentionally want to catch all exceptions, keep the original.
```

**Why this belongs in the agent workflow:** It's a behavioral policy decision about *when* to defer, not a risk score calculation. The risk assessment already penalizes it (-5), but context matters more than score here.

---

## 8) Improvement idea

### Proposed Improvement: Minimal-Diff Scoped Fixes

**Problem:** The heuristic fixer currently applies global transformations. When print statements are detected in one function, ALL print calls in the entire file are replaced, increasing blast radius and risk.

**Solution:** Make fixes minimal and localized:
- Detect which specific functions/lines have issues (during ANALYZE)
- During ACT, apply fixes only to those scopes, not the entire file
- For print→logging, only import logging if it's actually used in the modified function

**Implementation (low-complexity):**

1. Extend issue objects to include `line_number` or `function_name`
2. Modify `_heuristic_fix()` to take an optional `scope` parameter
3. Use regex with line number context: `re.sub(pattern, replacement, code, count=1)` to limit replacements to detected locations
4. Add a test: verify that fixing print in function A doesn't affect print in function B

**Example:**
```python
# Issue detected in greet() only
# OLD BEHAVIOR: import logging added, ALL print() replaced
# NEW BEHAVIOR: only print() in greet() replaced, no import unless needed

def unrelated():
    print(“debug”)  # Unchanged

def greet(name):
    print(“Hello”, name)  # Changed to logging.info (with proper formatting)
```

**Benefits:**
- Reduced diff size (easier for humans to review)
- Lower risk score (fewer unintended changes)
- More confidence in auto-apply decisions
- Aligns with principle of least privilege (“change only what's necessary”)

**Estimated complexity:** 2–3 hours. Requires parsing line numbers from heuristic patterns and scoping the regex replacements. Minimal changes to the agent loop structure.
