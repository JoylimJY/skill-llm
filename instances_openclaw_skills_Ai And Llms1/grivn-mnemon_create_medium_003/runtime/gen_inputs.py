from pathlib import Path
import json
import random

random.seed(1337)

notes = {
    "meeting_notes.txt": """
Project Aurora memory notes

Marker: AURORA-ALPHA-91

- The launch review moved from Friday to Monday because the demo environment needed extra QA time.
- Nina prefers concise status updates in bullet points.
- The team decided to keep the new API endpoint stable for one more sprint.
- A rollback playbook exists for the payments service.
- The demo failure last week was caused by a missing environment variable in staging.
""",
    "task_brief.txt": """
Memory curation task

Marker: TASK-BRIEF-44

Store the facts above with sensible categories and entities. Then create links only when the relationship is truly meaningful.
""",
}

for name, content in notes.items():
    Path(name).write_text(content.strip() + "\n", encoding="utf-8")

Path("expected_manifest.json").write_text(
    json.dumps(
        {
            "marker_note": "AURORA-ALPHA-91",
            "marker_task": "TASK-BRIEF-44",
            "expected_facts": 5,
            "expected_links_min": 2,
        },
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
