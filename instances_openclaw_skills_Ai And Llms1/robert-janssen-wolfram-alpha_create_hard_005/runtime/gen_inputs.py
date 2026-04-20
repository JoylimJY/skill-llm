from pathlib import Path
import csv

Path('data').mkdir(exist_ok=True)
rows = [
    ['id', 'value', 'label'],
    ['1', '12.5', 'alpha'],
    ['2', '15.0', 'beta'],
    ['3', '14.5', 'gamma'],
    ['4', '18.0', 'delta'],
    ['5', '20.0', 'epsilon'],
]
with open('data/measurements.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(rows)

Path('data/marker.txt').write_text('WA-AUDIT-2025\nfixed-seed: 1337\n', encoding='utf-8')
