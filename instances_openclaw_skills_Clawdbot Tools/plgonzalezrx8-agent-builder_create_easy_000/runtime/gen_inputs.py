from pathlib import Path

root = Path('.')
(root / 'references').mkdir(exist_ok=True)
(root / 'references' / 'marker.txt').write_text('OPENCLAW_TASK_MARKER_ALPHA_2025\n', encoding='utf-8')
(root / 'workspace_seed.txt').write_text('Agent name: Atlas\nMode: polite research assistant\nMarker: OPENCLAW_TASK_MARKER_ALPHA_2025\n', encoding='utf-8')
