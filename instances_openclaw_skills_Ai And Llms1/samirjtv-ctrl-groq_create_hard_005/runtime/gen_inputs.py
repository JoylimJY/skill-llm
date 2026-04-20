from pathlib import Path
import json
import random

random.seed(1337)
root = Path('.')
(root / 'input').mkdir(exist_ok=True)
(root / 'data').mkdir(exist_ok=True)

workspace = {
    'template.json': {
        'model': 'llama-3.1-8b-instant',
        'temperature': 0.2,
        'max_tokens': 256,
        'messages': [
            {'role': 'system', 'content': 'You are a concise assistant.'},
            {'role': 'user', 'content': 'Summarize the job payload.'}
        ]
    },
    'jobs.jsonl': [
        {
            'job_id': 'alpha-001',
            'messages': [
                {'role': 'user', 'content': '  first request   '},
                {'role': 'assistant', 'content': 'ack'}
            ],
            'temperature': 0.15
        },
        {
            'job_id': 'beta-002',
            'messages': [
                {'role': 'user', 'content': 'second request with marker GROQ-MARKER-BETA'}
            ]
        },
        {
            'job_id': 'gamma-003',
            'messages': [
                {'role': 'system', 'content': 'use the marker GAMMA-SEED-7788'},
                {'role': 'user', 'content': 'third request'}
            ],
            'max_tokens': 128
        }
    ],
    'README.source.txt': 'Groq Completion utility\nInvoke with: Groq: process workspace and emit output.jsonl plus report.json\n'
}

Path('template.json').write_text(json.dumps(workspace['template.json'], indent=2), encoding='utf-8')
with Path('jobs.jsonl').open('w', encoding='utf-8') as f:
    for row in workspace['jobs.jsonl']:
        f.write(json.dumps(row) + '\n')
Path('README.source.txt').write_text(workspace['README.source.txt'], encoding='utf-8')

Path('marker.txt').write_text('FIXED-MARKER-2025-03-17', encoding='utf-8')
