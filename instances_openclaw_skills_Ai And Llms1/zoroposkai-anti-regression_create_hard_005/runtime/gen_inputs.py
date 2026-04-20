from pathlib import Path
import json
import random

random.seed(1337)
base = Path('.')

(base / 'source_notes.txt').write_text(
    'MARKER_ALPHA: compliance threshold 0.87\n'
    'MARKER_BETA: include only the first three incidents\n'
    'MARKER_GAMMA: report title must mention quarterly review\n',
    encoding='utf-8'
)

records = [
    {"id": 1, "severity": "low", "status": "closed", "score": 0.91},
    {"id": 2, "severity": "high", "status": "open", "score": 0.42},
    {"id": 3, "severity": "medium", "status": "closed", "score": 0.78},
    {"id": 4, "severity": "high", "status": "open", "score": 0.35},
]
(base / 'incidents.json').write_text(json.dumps(records, indent=2), encoding='utf-8')

(base / 'README_HINT.txt').write_text(
    'Use the markers to decide what to summarize. The report should be brief and deterministic.\n',
    encoding='utf-8'
)
