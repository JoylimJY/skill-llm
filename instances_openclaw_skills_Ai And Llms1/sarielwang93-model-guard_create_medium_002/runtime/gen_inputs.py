from pathlib import Path

root = Path('.')

# Marker file used by eval to verify the generated workspace.
(root / 'marker_status.txt').write_text(
    'MARKER: MODEL_GUARD_INPUT\n'
    'Current default model: google-antigravity/claude-sonnet-4-5\n'
    'Status line: google-antigravity usage: claude-sonnet-4-5 72% left; claude-opus-4-5-thinking 18% left; gemini-3-pro-high 95% left\n',
    encoding='utf-8'
)

# A second file with structured content to make the task more realistic.
(root / 'status_snapshot.json').write_text(
    '{\n'
    '  "defaults": {"model": {"primary": "google-antigravity/claude-sonnet-4-5"}},\n'
    '  "usage": {\n'
    '    "google-antigravity/claude-opus-4-5-thinking": 18,\n'
    '    "google-antigravity/claude-sonnet-4-5": 72,\n'
    '    "google-antigravity/gemini-3-pro-high": 95\n'
    '  }\n'
    '}\n',
    encoding='utf-8'
)
