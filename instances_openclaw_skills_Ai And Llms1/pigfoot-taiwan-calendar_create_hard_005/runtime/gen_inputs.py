from pathlib import Path
import json

base = Path('.')

# Deterministic marker-rich inputs
(base / 'markers.txt').write_text(
    '\n'.join([
        'ANCHOR_DATE=2025-01-06',
        'CHECK_DATE_A=2025-01-01',
        'CHECK_DATE_B=2025-01-03',
        'RANGE_START=2025-01-01',
        'RANGE_END=2025-01-31',
        'NOTE=TW-CALENDAR-MARKER-7F3A',
    ]) + '\n',
    encoding='utf-8'
)

(base / 'task_description.txt').write_text(
    'Use the Taiwan calendar skill to produce a brief for January 2025. Verify holiday and working-day status for the marker dates, and include the next working day after each marker date.\n',
    encoding='utf-8'
)

# Small auxiliary file that should remain unchanged
aux = {
    'project': 'taiwan-calendar-brief',
    'version': 1,
    'marker': 'TW-CALENDAR-MARKER-7F3A'
}
(base / 'metadata.json').write_text(json.dumps(aux, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
