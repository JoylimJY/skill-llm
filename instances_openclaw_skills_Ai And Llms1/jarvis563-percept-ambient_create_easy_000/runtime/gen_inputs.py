from pathlib import Path
import json

base = Path('.')
files = {
    'conversation_1.txt': 'Marker: ORBIT-17\nAlice: We should finalize the launch checklist for Project Atlas by Friday.\nBob: I will notify the client, Northwind Labs, about the updated timeline.\n',
    'conversation_2.txt': 'Marker: ORBIT-17\nAlice: The dashboard should show ambient context packets for recent meetings.\nCarol: I linked the relationship between Northwind Labs and Project Atlas in our notes.\n',
    'conversation_3.txt': 'Marker: ORBIT-17\nBob: Reminder that the privacy controls must keep transcripts local only.\nAlice: Agreed, and we should mention the entity graph in the summary.\n'
}
for name, content in files.items():
    (base / name).write_text(content, encoding='utf-8')

manifest = {
    'marker': 'ORBIT-17',
    'files': sorted(files.keys()),
    'expected_entities': ['Alice', 'Bob', 'Carol', 'Project Atlas', 'Northwind Labs'],
}
(base / 'input_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
