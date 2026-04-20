from pathlib import Path
import json
import random

random.seed(42)

notes = """MARKER:CHIEF-EDITOR-INPUT-001
Topic: Small public libraries help communities.
Facts:
- Libraries offer free books and internet access.
- They provide quiet study space for students.
- Some libraries host reading clubs and workshops.
- Local volunteers often help keep them running.
Reference URL: https://example.com/library-community
"""

Path("notes.txt").write_text(notes, encoding="utf-8")

meta = {
    "marker": "MARKER:CHIEF-EDITOR-INPUT-001",
    "expected_output": "article.md"
}
Path("input_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
