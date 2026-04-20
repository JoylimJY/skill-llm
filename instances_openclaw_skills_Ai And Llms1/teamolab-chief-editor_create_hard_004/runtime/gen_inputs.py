import json
from pathlib import Path

base = Path('.')
base.mkdir(parents=True, exist_ok=True)

# Deterministic source files with embedded markers
(base / 'brief_source_1.txt').write_text(
    """EDITORIAL BRIEF SOURCE A\n\nMARKER_ALPHA: alpha-117\nMARKER_BETA: beta-204\n\nSummary notes:\n- The launch window was moved from Tuesday to Thursday.\n- The team flagged a headline consistency issue in section 3.\n- A legal review is required before publication.\n\nReference URL: https://example.com/editorial-guidelines\n""",
    encoding='utf-8'
)

(base / 'brief_source_2.txt').write_text(
    """EDITORIAL BRIEF SOURCE B\n\nMARKER_GAMMA: gamma-331\nMARKER_DELTA: delta-918\n\nNotes:\n- Reader engagement improved after simplifying subheads.\n- The style guide now prefers sentence case for all deck text.\n- A correction was issued for a mislabeled chart.\n""",
    encoding='utf-8'
)

(base / 'brief_source_3.json').write_text(
    json.dumps({
        "document": "editorial-status",
        "marker": "MARKER_EPSILON: epsilon-550",
        "items": [
            "Publication delay caused by asset validation",
            "Need final sign-off from the chief editor",
            "Archive the old draft after approval"
        ],
        "links": [
            "https://example.com/archive-policy",
            "https://example.com/style-update"
        ]
    }, indent=2),
    encoding='utf-8'
)

(base / 'expected_markers.json').write_text(
    json.dumps({
        "required_markers": [
            "alpha-117",
            "beta-204",
            "gamma-331",
            "delta-918",
            "epsilon-550"
        ]
    }, indent=2),
    encoding='utf-8'
)
