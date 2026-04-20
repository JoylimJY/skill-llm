import json
from pathlib import Path

notes = {
    "title": "Debugging insight notes",
    "marker": "TED-TALK-TASK-MARKER-9f3c1a",
    "problem": "Teams keep turning debugging lessons into shallow summaries instead of full narratives.",
    "insight": "A technical talk should explain why the lesson matters, not only what happened.",
    "examples": [
        "A deployment failed because the team lacked observability in the first week.",
        "A migration was delayed because the team had no concrete examples to explain tradeoffs to stakeholders."
    ],
    "implications": "Good technical storytelling improves adoption, debugging, and teaching.",
    "audience": "Engineers who need to present technical lessons to mixed audiences.",
    "tone": "Clear, practical, and engaging."
}
Path("notes.json").write_text(json.dumps(notes, indent=2), encoding="utf-8")
Path("brief.txt").write_text(
    "Marker: TED-TALK-TASK-MARKER-9f3c1a\n"
    "Use the notes to create a TED-style talk with all required sections.\n",
    encoding="utf-8"
)
