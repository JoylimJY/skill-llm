from pathlib import Path
import json
import random

random.seed(1337)

briefing = {
    "project": "Project Lattice",
    "codename": "lattice-echo",
    "preference": "The team prefers concise memory labels and avoids storing raw secrets.",
    "decision": "All weekly review notes must be summarized in Markdown before being archived.",
    "fact": "The staging API endpoint is read-only during the current test window.",
    "causal_note": "Because the staging API is read-only, any workflow that tries to mutate it should be blocked.",
}

Path("briefing.json").write_text(json.dumps(briefing, indent=2), encoding="utf-8")

notes = [
    "Project Lattice uses the codename lattice-echo for the current sprint.",
    "The team preference is to keep memory entries concise and never store secrets.",
    "Decision: weekly review notes are archived only after being summarized in Markdown.",
    "Fact: the staging API endpoint is read-only during the test window.",
    "Operational impact: mutation attempts against the staging API should be prevented.",
]
Path("briefing_notes.txt").write_text("\n".join(notes) + "\n", encoding="utf-8")

# Marker file for deterministic evaluation support
markers = [
    "MARKER_PROJECT_LATTICE",
    "MARKER_LATTICE_ECHO",
    "MARKER_READ_ONLY_STAGING_API",
    "MARKER_MARKDOWN_ARCHIVE_DECISION",
]
Path("markers.txt").write_text("\n".join(markers) + "\n", encoding="utf-8")
