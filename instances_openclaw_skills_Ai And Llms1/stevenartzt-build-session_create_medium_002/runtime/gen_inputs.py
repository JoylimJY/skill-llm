from pathlib import Path
import json

notes = {
    "title": "Weekly Build Session Notes",
    "date": "2025-04-18",
    "meeting": [
        "The sync started 10 minutes late due to a calendar overlap.",
        "Maya reported that the export script now handles empty rows correctly.",
        "Jordan asked for a short summary of progress for the product team.",
        "A regression was found in the CSV cleanup step when filenames contain spaces.",
        "The team agreed to ship a minimal fix first and revisit polish later.",
        "Next session will focus on documenting the workflow and improving test coverage."
    ],
    "actions": [
        "Fix CSV cleanup for filenames with spaces.",
        "Draft a brief progress summary for the product team.",
        "Add a regression test for empty-row handling.",
        "Document the workflow used in the build session."
    ],
    "marker": "MARKER-7F3A-BUILD-SESSION"
}
Path("notes.json").write_text(json.dumps(notes, indent=2), encoding="utf-8")
Path("reference_marker.txt").write_text(f"Important marker: {notes['marker']}\n", encoding="utf-8")
