from pathlib import Path
import json
import random

random.seed(20250106)

workspace = Path('.')

# Main task manifest with marker content
manifest = {
    'project': 'taiwan-calendar-audit',
    'marker': 'MARKER-TC-2025-01-06',
    'reference_date': '2025-01-06',
    'range_start': '2025-01-01',
    'range_end': '2025-01-10',
    'dates_to_check': ['2025-01-01', '2025-01-04', '2025-01-06', '2025-01-10'],
}
(workspace / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')

# Human-readable brief with embedded marker
brief = """Taiwan Calendar Audit Brief

Marker: MARKER-TC-2025-01-06

Instructions:
- Use Taiwan working-day rules.
- Check the listed dates only.
- Ignore any decoy notes in other files.
- Produce output.txt and summary.json.
"""
(workspace / 'brief.txt').write_text(brief, encoding='utf-8')

# Decoy file with misleading content that should not be treated as authoritative
noise_lines = [
    'DEC0Y: 2025-01-01 is a working day (this is intentionally false).',
    'DEC0Y: 2025-01-04 is a holiday (also intentionally false).',
    'Random token: ' + ''.join(random.choice('abcdef0123456789') for _ in range(24)),
    'MARKER-IGNORE-THIS-FILE',
]
(workspace / 'decoy_notes.txt').write_text('\n'.join(noise_lines) + '\n', encoding='utf-8')

# Input checklist CSV
csv_content = "date,label\n2025-01-01,new_year\n2025-01-04,weekend_test\n2025-01-06,reference_day\n2025-01-10,weekend_test\n"
(workspace / 'dates.csv').write_text(csv_content, encoding='utf-8')

# Small helper file that contains a checksum-like marker string
(workspace / 'marker.txt').write_text('checksum: TC-AUDIT-9f2c1e\n', encoding='utf-8')
