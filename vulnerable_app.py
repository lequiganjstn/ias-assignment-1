"""Intentionally vulnerable Flask demo for the USC department portal assignment.

This file represents the original AI-generated application.  It keeps the SQL
query construction deliberately unsafe so it can be audited and exploited in the
assignment workflow.  Do not deploy this version.
"""

import sqlite3
from pathlib import Path

from flask import Flask, render_template_string, request

DATABASE = Path(__file__).with_name("students.db")

app = Flask(__name__)

PAGE = """
<!doctype html>
<title>University of San Carlos Department Portal</title>
<h1>Student Lookup</h1>
<form method="get">
  <label for="student_id">Student ID</label>
  <input id="student_id" name="student_id" value="{{ student_id }}">
  <button type="submit">Search</button>
</form>
{% if rows is not none %}
  <h2>Results</h2>
  <ul>
  {% for row in rows %}
    <li>{{ row[0] }} — {{ row[1] }} — {{ row[2] }}</li>
  {% else %}
    <li>No matching student found.</li>
  {% endfor %}
  </ul>
{% endif %}
"""


def init_db() -> None:
    """Create a tiny local database so the demo runs without setup."""
    with sqlite3.connect(DATABASE) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                department TEXT NOT NULL
            )
            """
        )
        connection.executemany(
            "INSERT OR IGNORE INTO students (id, name, department) VALUES (?, ?, ?)",
            [
                ("2024-0001", "Ana Reyes", "Computer Science"),
                ("2024-0002", "Miguel Santos", "Information Systems"),
                ("2024-0003", "Lea Cruz", "Cybersecurity"),
            ],
        )


@app.route("/")
def search_students():
    """Search for a student ID using intentionally unsafe SQL."""
    student_id = request.args.get("student_id", "")
    rows = None

    if student_id:
        with sqlite3.connect(DATABASE) as connection:
            query = (
                "SELECT id, name, department FROM students "
                f"WHERE id = '{student_id}'"
            )
            rows = connection.execute(query).fetchall()

    return render_template_string(PAGE, student_id=student_id, rows=rows)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
