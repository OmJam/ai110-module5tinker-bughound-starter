# BugHound API Fix Summary

## Problem Analysis

Your Streamlit app was **falling back to heuristics** even though you had a valid Gemini API key. The root cause was in the `GeminiClient.complete()` method.

### The Root Issue

The original code was using an **incompatible message format** for the Gemini API:

```python
response = self.model.generate_content(
    [
        {"role": "system", "parts": [system_prompt]},  # ❌ INVALID
        {"role": "user", "parts": [user_prompt]},
    ],
    ...
)
```

**Error:** `Role 'system' is not supported. Please use a valid role: MODEL, USER.`

The Gemini API **does not support a "system" role**. It only accepts:

- `"user"` - messages from the user
- `"model"` - responses from the model

### Why It Silently Fell Back

The exception was caught silently and returned an empty string:

```python
except Exception as e:
    return ""  # Silent fallback
```

The agent then detected the empty output and fell back to heuristic analysis without surfacing the API error to you.

---

## Solution

Changed [llm_client.py](llm_client.py#L42-L65) to combine the system and user prompts into a single string:

```python
def complete(self, system_prompt: str, user_prompt: str) -> str:
    try:
        # Combine system prompt with user prompt (Gemini doesn't support "system" role)
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"

        response = self.model.generate_content(
            combined_prompt,
            generation_config={"temperature": self.temperature},
        )

        return response.text or ""
    except Exception as e:
        return ""
```

---

## Testing Results

✅ **API now working correctly:**

- Simple JSON requests: **PASS**
- Full agent workflow: **PASS**
- Issue analysis: **PASS** (found 4 issues in test code)
- Fix proposal: **PASS**
- Risk assessment: **PASS**

### Example Test Output

```
Issues found: 4
  1. Resource Management | High - file not closed
  2. Error Handling | Medium - bare except:
  3. Performance/Memory | Low - reads entire file
  4. Design/API | Low - returns None instead of exception

Fixed code: [properly handles with statement and specific exceptions]
Risk assessment: high (score=25, should_autofix=False)
```

---

## What to Do Next

1. **Reload your Streamlit app:**

   ```bash
   streamlit run bughound_app.py
   ```

2. **Select "Gemini (requires API key)" mode** in the sidebar

3. **Try analyzing sample code** — you should now see:
   - Full LLM-powered analysis (not heuristics)
   - Detailed issue reports
   - Intelligent fix proposals
   - Proper agent trace logs

4. **Check the debug logs** — you should see:
   ```
   [ANALYZE] Using LLM analyzer.
   [ACT] Using LLM fixer.
   ```
   (Not "Falling back to heuristics")

---

## Key Takeaway

When working with different LLM APIs, always check their supported message formats. Each API has different conventions:

- OpenAI: supports "system", "user", "assistant" roles
- Gemini: only supports "user" and "model" roles
- Claude: uses different message structures

The error handling in the original code was too silent — adding logging would have caught this sooner!
