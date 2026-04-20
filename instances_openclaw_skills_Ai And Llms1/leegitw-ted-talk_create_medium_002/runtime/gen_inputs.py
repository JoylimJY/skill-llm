from pathlib import Path
import json
import random

random.seed(42)

marker = {
    "topic": "bootstrap observability",
    "core_insight": "greenfield systems need to learn normal before enforcing normal",
    "example_event": "3 AM debugging blind incident",
    "phases": ["bootstrap", "learn", "enforce"],
}

Path("input_context.json").write_text(json.dumps(marker, indent=2), encoding="utf-8")
Path("conversation_notes.txt").write_text(
    "Marker: TED_TALK_TASK_v1\n"
    "Key idea: bootstrap before you break.\n"
    "Audience: engineers, tech leads, and product-minded builders.\n"
    "Need: full talk with sections and Q&A.\n",
    encoding="utf-8",
)
Path("seed_info.txt").write_text(f"seed={42}\n", encoding="utf-8")
