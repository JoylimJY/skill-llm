from pathlib import Path

# Deterministic input generation with marker content
workspace = Path('.')
(workspace / 'session_notes.txt').write_text(
    'TOKEN-ALERT-MARKER\nCurrent usage estimate: 78%\nReminder threshold: 75% and 90%\n',
    encoding='utf-8'
)
