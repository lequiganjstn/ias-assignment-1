"""Automated SQL-injection patch pipeline for the Flask assignment.

The script can call a local Ollama model to rewrite a vulnerable Flask source
file, then validates that the generated patch contains a parameterized query and
no longer contains the original f-string SQL sink.  If Ollama is unavailable, it
uses a deterministic local patch for this assignment's known vulnerable block.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

DEFAULT_MODEL = "qwen2.5-coder"
SYSTEM_PROMPT = """You are a defensive patching assistant. Rewrite the provided Flask/sqlite3 code to remove SQL injection by replacing raw string SQL construction with parameterized queries. Return only complete Python source code, with no Markdown fences."""


def ask_ollama(source: str, model: str) -> str | None:
    """Ask a local Ollama model to patch the source; return None if unavailable."""
    prompt = f"{SYSTEM_PROMPT}\n\nVulnerable source:\n{source}"
    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt,
            text=True,
            capture_output=True,
            check=True,
            timeout=120,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip()


def deterministic_patch(source: str) -> str:
    """Patch the known unsafe query block produced for this assignment."""
    unsafe_block = '''            query = (\n                "SELECT id, name, department FROM students "\n                f"WHERE id = '{student_id}'"\n            )\n            rows = connection.execute(query).fetchall()'''
    safe_block = '''            query = "SELECT id, name, department FROM students WHERE id = ?"\n            rows = connection.execute(query, (student_id,)).fetchall()'''
    if unsafe_block not in source:
        raise ValueError("Expected vulnerable SQL block was not found.")
    patched = source.replace(unsafe_block, safe_block).replace("app.run(debug=True)", "app.run(debug=False)")
    vulnerable_header = """Intentionally vulnerable Flask demo for the USC department portal assignment.

This file represents the original AI-generated application.  It keeps the SQL
query construction deliberately unsafe so it can be audited and exploited in the
assignment workflow.  Do not deploy this version.
"""
    secure_header = """Secure Flask demo for the USC department portal assignment.

This version keeps the same behavior as vulnerable_app.py but uses a
parameterized query so untrusted student_id input is bound as data instead of
being concatenated into SQL syntax.
"""
    patched = patched.replace(vulnerable_header, secure_header)
    return patched.replace(
        "Search for a student ID using intentionally unsafe SQL.",
        "Search for a student ID using a parameterized SQL statement.",
    )

def validate_patch(source: str) -> None:
    """Fail closed if the patched source still contains the obvious SQL sink."""
    findings = []
    if "execute(query, (student_id,))" not in source:
        findings.append("missing parameterized execute(query, (student_id,)) call")
    if "f\"WHERE id = '{student_id}'\"" in source or "execute(query).fetchall()" in source:
        findings.append("unsafe f-string SQL construction remains")
    if "app.run(debug=True)" in source:
        findings.append("debug mode remains enabled")
    if findings:
        raise ValueError("Patch validation failed: " + "; ".join(findings))


def patch_file(input_path: Path, output_path: Path, model: str) -> dict[str, str]:
    """Patch input_path and write the secure source to output_path."""
    source = input_path.read_text(encoding="utf-8")
    patched = ask_ollama(source, model)
    method = f"ollama:{model}"
    if not patched:
        patched = deterministic_patch(source)
        method = "deterministic-fallback"
    validate_patch(patched)
    output_path.write_text(patched + "\n", encoding="utf-8")
    return {"input": str(input_path), "output": str(output_path), "method": method}


def main() -> None:
    parser = argparse.ArgumentParser(description="Patch a vulnerable Flask/sqlite3 app.")
    parser.add_argument("--input", default="vulnerable_app.py", type=Path)
    parser.add_argument("--output", default="patched_app.py", type=Path)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()
    print(json.dumps(patch_file(args.input, args.output, args.model), indent=2))


if __name__ == "__main__":
    main()
