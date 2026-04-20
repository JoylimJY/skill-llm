from pathlib import Path
import csv

base = Path('.')
(base / 'data').mkdir(exist_ok=True)

# Deterministic measurements file with marker content
rows = [
    ['label', 'value'],
    ['alpha', '10.5'],
    ['beta', '7.25'],
    ['gamma', '12.25'],
    ['delta', '4.0'],
]
with (base / 'data' / 'measurements.csv').open('w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerows(rows)

# Notes file with embedded marker
notes = """Project notes
- item: sodium chloride
- item: lithium carbonate
- item: primary sample MARKER:PRIMARY
- item: zinc sulfate
"""
(base / 'data' / 'notes.txt').write_text(notes, encoding='utf-8')

# Extra marker file to make verification easier
(base / 'data' / 'reference.txt').write_text('REFERENCE_MARKER=WA_SKILL_TASK_001\n', encoding='utf-8')
