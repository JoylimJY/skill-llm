from pathlib import Path

# Deterministic input generation with marker content
base = Path('.')
(base / 'skill_name.txt').write_text('pincer\n', encoding='utf-8')
(base / 'marker.txt').write_text('MARKER_PINCER_EASY_TASK_001\n', encoding='utf-8')
(base / 'scan_notes.txt').write_text(
    'pincer scans for prompt injection, malware, suspicious patterns, and bundled binaries.\n',
    encoding='utf-8'
)
