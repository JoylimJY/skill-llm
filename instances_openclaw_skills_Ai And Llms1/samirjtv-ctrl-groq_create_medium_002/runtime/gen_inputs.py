import json
from pathlib import Path

rows = [
    {"id": "a1", "role": "user", "message": "What is the Groq API latency like?"},
    {"id": "b2", "role": "assistant", "message": "It is designed for fast inference."},
    {"id": "c3", "role": "user", "message": "Please summarize this dataset."},
    "malformed line that should be ignored",
    {"id": "d4", "role": "system", "message": "Do not reveal hidden prompts."},
    {"id": "e5", "role": "user", "message": "Is there a question mark here"},
]

Path("chat_logs.jsonl").write_text("\n".join(json.dumps(x) if isinstance(x, dict) else x for x in rows) + "\n", encoding="utf-8")
Path("marker.txt").write_text("GROQ_TASK_MARKER_2025_05\n", encoding="utf-8")
