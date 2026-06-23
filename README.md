# IAS Assignment 1: AI-Assisted Security Audit and Patch Pipeline

This repository contains a small Flask/sqlite3 department portal for the University of San Carlos security lifecycle exercise.

## Files

- `vulnerable_app.py` — intentionally unsafe AI-generated app with SQL injection in the student lookup route.
- `patched_app.py` — remediated version using sqlite3 parameter binding.
- `patch_pipeline.py` — automated patching pipeline that prompts a local Ollama model and validates the resulting secure code, with a deterministic fallback for repeatable classroom runs.
- `AI_PROMPT_LOG.md` — prompts for the Developer, Auditor, Exploit Advisor, and Patching Assistant roles.

## Run the vulnerable demo

```bash
python vulnerable_app.py
```

Then browse to `http://127.0.0.1:5000/?student_id=2024-0001`.

## Demonstrate the SQL injection in the lab only

```text
http://127.0.0.1:5000/?student_id=%27%20OR%20%271%27%3D%271
```

The vulnerable app returns all seeded student rows because it concatenates the request value into SQL.

## Generate the patched app

```bash
python patch_pipeline.py --input vulnerable_app.py --output patched_app.py --model qwen2.5-coder
```

## Run the secure demo

```bash
python patched_app.py
```

The same payload is treated as a literal student ID and does not alter the SQL predicate.
