from pathlib import Path
import json

chat = [
    {"role": "user", "content": "Hi, can you help me understand the new project timeline?"},
    {"role": "assistant", "content": "Sure — the timeline has three phases: planning, implementation, and review."},
    {"role": "user", "content": "Please also note that we need a weekly status update."},
    {"role": "assistant", "content": "Got it. I’ll include that requirement in the recap."}
]

Path("conversation.json").write_text(json.dumps(chat, ensure_ascii=False, indent=2), encoding="utf-8")
Path("marker.txt").write_text("SUMMARY_MARKER_7F3A\n", encoding="utf-8")
