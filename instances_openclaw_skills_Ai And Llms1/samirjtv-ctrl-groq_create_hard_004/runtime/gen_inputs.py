from pathlib import Path
import json

notes = """- The summary must be exactly 3 bullet points.\n- Each bullet should be 1 sentence long.\n- Mention Groq's fast inference once.\n- Keep the tone professional.\n- Do not include a title.\n"""
Path("notes.txt").write_text(notes, encoding="utf-8")
Path("marker.json").write_text(json.dumps({"marker": "GROQ_SUMMARY_TASK_V1", "seed": 1337}, indent=2), encoding="utf-8")
