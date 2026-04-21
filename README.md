# 🐶 BugHound

BugHound is a small, agent-style debugging tool. It analyzes a Python code snippet, proposes a fix, and runs basic reliability checks before deciding whether the fix is safe to apply automatically.

---

## Summary

This activity shows how to build sade agentic systems with guardrails to verify the AI-generated output/fixes are correct or need to be changed. We also see why and how a heuristic fallback, and how a risk scorer can prevent auto fixing the code. Students may find it difficult to know what correct and best practice Python code looks, since code can be valid but not the best way to implement it. Sometimes AI may also generate code that works but is also not best practice or what we are looking for. AI helps finding the issues and describing why its wrong, but struggles when making precise correct fixes. I would guide students to first use AI to fully understand what the code does and what the function do. Then have students, or an LLM, trace from input to output to understand what the code is doing and how the AI acts.

## What BugHound Does

Given a short Python snippet, BugHound:

1. **Analyzes** the code for potential issues
   - Uses heuristics in offline mode
   - Uses Gemini when API access is enabled

2. **Proposes a fix**
   - Either heuristic-based or LLM-generated
   - Attempts minimal, behavior-preserving changes

3. **Assesses risk**
   - Scores the fix
   - Flags high-risk changes
   - Decides whether the fix should be auto-applied or reviewed by a human

4. **Shows its work**
   - Displays detected issues
   - Shows a diff between original and fixed code
   - Logs each agent step

---

## Setup

### 1. Create a virtual environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# or
.venv\Scripts\activate      # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Running in Offline (Heuristic) Mode

No API key required.

```bash
streamlit run bughound_app.py
```

In the sidebar, select:

- **Model mode:** Heuristic only (no API)

This mode uses simple pattern-based rules and is useful for testing the workflow without network access.

---

## Running with Gemini

### 1. Set up your API key

Copy the example file:

```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key:

```text
GEMINI_API_KEY=your_real_key_here
```

### 2. Run the app

```bash
streamlit run bughound_app.py
```

In the sidebar, select:

- **Model mode:** Gemini (requires API key)
- Choose a Gemini model and temperature

BugHound will now use Gemini for analysis and fix generation, while still applying local reliability checks.

---

## Running Tests

Tests focus on **reliability logic** and **agent behavior**, not the UI.

```bash
pytest
```

You should see tests covering:

- Risk scoring and guardrails
- Heuristic fallbacks when LLM output is invalid
- End-to-end agent workflow shape
