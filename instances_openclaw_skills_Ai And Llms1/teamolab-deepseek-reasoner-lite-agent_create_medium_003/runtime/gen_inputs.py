from pathlib import Path
import json

base = Path('.')
source = {
    "product_name": "Northstar Note",
    "launch_date": "2025-06-18",
    "audience": ["small teams", "independent creators", "project leads"],
    "benefits": [
        "fast note capture",
        "simple team sharing",
        "built-in task follow-up"
    ],
    "marker": "MARKER_CAMPAIGN_BRIEF_7F3A"
}
(base / 'source_notes.json').write_text(json.dumps(source, indent=2), encoding='utf-8')
(base / 'campaign_outline.txt').write_text(
    "Launch brief must mention Northstar Note, the June 2025 launch window, and the marker MARKER_CAMPAIGN_BRIEF_7F3A.\n"
    "Include 3 social post ideas and 4 milestone dates.\n",
    encoding='utf-8'
)
