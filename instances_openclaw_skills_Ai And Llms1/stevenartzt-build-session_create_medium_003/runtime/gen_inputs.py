from pathlib import Path
import json

workspace = Path('.')
workspace.mkdir(parents=True, exist_ok=True)

# Deterministic input files with marker content
(workspace / 'HEARTBEAT.md').write_text(
    '# HEARTBEAT\n\nMarker: BUILD_SESSION_MARKER_ALPHA\nCurrent focus: reduce friction in autonomous sessions.\n',
    encoding='utf-8'
)

(workspace / 'project_notes.txt').write_text(
    'Session ideas:\n- Fix recurring logging noise\n- Improve daily build notes\n- Document one useful insight\n\nMarker: BUILD_SESSION_MARKER_BETA\n',
    encoding='utf-8'
)

(workspace / 'context.json').write_text(
    json.dumps({
        'date': '2025-05-15',
        'timezone': 'UTC',
        'marker': 'BUILD_SESSION_MARKER_GAMMA',
        'suggested_title': 'Quiet Build Session'
    }, indent=2),
    encoding='utf-8'
)
