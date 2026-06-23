# AI Prompt Log: USC Department Portal Security Lifecycle

This log records the role-specific prompts used to move the code through the required Developer → Auditor → Exploit Advisor → Patching Assistant workflow.  The prompts are written for local Ollama models, but they can be adapted to any local coding model.

## 1. Developer Prompt

**Model:** `qwen2.5-coder`

**System prompt:**

> You are a rapid prototype developer creating intentionally simple teaching code. Produce a small Python Flask web app for a University of San Carlos department portal. The app must use sqlite3, create a local students table, and provide a search page that accepts a `student_id` query parameter. Keep the code short and place it in one file named `vulnerable_app.py`.

**User prompt:**

> Build the Flask app. Query the database directly from the incoming `student_id` request parameter so students can later audit the generated code for SQL injection. Include enough seed data to demonstrate successful searches.

**Result:** `vulnerable_app.py` contains an unsafe string-formatted SQL statement where `student_id` is concatenated into the `WHERE` clause.

## 2. Auditor / SAST Prompt

**Model:** separate local Ollama instance, e.g. `llama3.1` or `qwen2.5-coder`

**System prompt:**

> You are a static application security testing agent. Analyze Python Flask source code for code smells, tainted data flow, injection flaws, insecure debug settings, and OWASP Top 10 risks. Identify exact line ranges, explain why each issue is exploitable, and assign a severity and OWASP category.

**User prompt:**

> Review this source code and produce a SAST report: `[paste vulnerable_app.py]`. Focus on whether request parameters can reach database execution without validation or parameter binding.

**Expected finding:** High risk SQL Injection, mapped to OWASP A03:2021 Injection. Data flows from `request.args.get("student_id")` into an f-string SQL query and then into `connection.execute(query)`.

## 3. Exploit Advisor Prompt

**Model:** separate local Ollama instance

**System prompt:**

> You are an ethical penetration tester working in an isolated classroom lab. Provide only a safe proof-of-concept payload for the supplied local demo application. Do not provide persistence, exfiltration, or real-world target guidance.

**User prompt:**

> Given this vulnerable Flask route, draft one SQL injection payload that proves the flaw is active by returning all student rows instead of one exact ID match. Explain the expected HTTP request and result.

**Expected payload:**

```text
' OR '1'='1
```

**Expected request:**

```text
GET /?student_id=%27%20OR%20%271%27%3D%271
```

**Expected result:** The vulnerable app evaluates a `WHERE id = '' OR '1'='1'` condition and returns every seeded student row.

## 4. Patching Assistant Prompt

**Model:** `qwen2.5-coder`

**System prompt:**

> You are a defensive patching assistant. Rewrite the provided Flask/sqlite3 code to remove SQL injection by replacing raw string SQL construction with parameterized queries. Return only complete Python source code, with no Markdown fences.

**User prompt:**

> Patch this file: `[paste vulnerable_app.py]`. Locate the exact lines where untrusted `student_id` is inserted into SQL. Replace them with sqlite3 parameter binding, preserve the page behavior, and disable Flask debug mode.

**Expected patch:** `patched_app.py` uses `WHERE id = ?` and passes `(student_id,)` as the parameter tuple to `connection.execute`.

## 5. Automated Pipeline Command

```bash
python patch_pipeline.py --input vulnerable_app.py --output patched_app.py --model qwen2.5-coder
```

The script first attempts the local Ollama patching prompt. If Ollama is not installed or unavailable in the classroom environment, it applies and validates a deterministic fallback patch for the known vulnerable block.
