from pathlib import Path
import csv
import random

random.seed(1337)
rows_by_file = {
    'input_a.csv': [
        ['id','team','score','status'],
        ['a01','Red',91,'open'],
        ['a02','Blue',88,'closed'],
        ['a03','Red',91,'open'],
        ['a04','Green',77,'blocked'],
    ],
    'input_b.csv': [
        ['id','team','score','status'],
        ['b01','Blue',95,'open'],
        ['b02','Green',95,'closed'],
        ['b03','Yellow',66,'open'],
        ['b04','Blue',72,'blocked'],
    ],
    'input_c.csv': [
        ['id','team','score','status'],
        ['c01','Red',64,'closed'],
        ['c02','Yellow',95,'open'],
        ['c03','Yellow',71,'closed'],
    ],
}
for name, rows in rows_by_file.items():
    with open(name, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

Path('marker.txt').write_text('BENCHMARK_MARKER_48291\n', encoding='utf-8')
