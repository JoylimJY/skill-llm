from pathlib import Path
import json

notes = {
    "product_name": "Northstar One",
    "launch_date": "2025-04-18",
    "key_facts": [
        "Northstar One is a lightweight productivity app for small teams.",
        "It offers task tracking, shared notes, and weekly summaries.",
        "The beta included 1,240 testers across 12 countries.",
        "The public launch includes a 14-day free trial."
    ],
    "required_phrase": "Built for teams that move fast without losing clarity."
}

Path("source_notes.json").write_text(json.dumps(notes, indent=2), encoding="utf-8")
Path("brand_voice.txt").write_text(
    "Voice: clear, confident, concise, and optimistic. Avoid jargon.\n",
    encoding="utf-8"
)
