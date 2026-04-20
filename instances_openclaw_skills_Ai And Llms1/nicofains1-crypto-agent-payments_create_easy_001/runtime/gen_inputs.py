from pathlib import Path

# Deterministic input generation with embedded markers
Path('task_config.json').write_text('{"task_id":"onlyswaps-001","chain":"Base","marker":"ALPHA-7X"}\n', encoding='utf-8')
Path('notes.txt').write_text('User wants a concise setup note. Marker: ALPHA-7X. Chain: Base. Task: onlyswaps-001.\n', encoding='utf-8')
