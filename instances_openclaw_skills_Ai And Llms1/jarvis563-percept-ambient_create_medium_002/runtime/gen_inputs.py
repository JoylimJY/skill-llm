from pathlib import Path
import json
import random

random.seed(1337)

base = Path('.')
(base / 'input').mkdir(exist_ok=True)

conversations = [
    {
        'id': 'c1',
        'speaker': 'Avery Chen',
        'text': 'Project Atlas is on track. Sam Lee will handle the dashboard prototype and Dana mentioned the privacy review is due Friday.',
        'timestamp': '2025-04-18T09:00:00Z'
    },
    {
        'id': 'c2',
        'speaker': 'Sam Lee',
        'text': 'I talked with Avery about Atlas. We agreed to keep the retrieval search local and use SQLite plus LanceDB.',
        'timestamp': '2025-04-18T09:15:00Z'
    },
    {
        'id': 'c3',
        'speaker': 'Dana Park',
        'text': 'The Atlas privacy notes should mention no audio is stored, only transcripts.',
        'timestamp': '2025-04-18T10:05:00Z'
    },
    {
        'id': 'c4',
        'speaker': 'Mina Rao',
        'text': 'Lunch was great, see you later.',
        'timestamp': '2025-04-18T12:00:00Z'
    }
]

entities = [
    {'name': 'Project Atlas', 'type': 'project', 'marker': 'KEEP'},
    {'name': 'Atlas', 'type': 'project', 'marker': 'DUPLICATE_OF:Project Atlas'},
    {'name': 'Avery Chen', 'type': 'person'},
    {'name': 'Sam Lee', 'type': 'person'},
    {'name': 'Dana Park', 'type': 'person'},
    {'name': 'LanceDB', 'type': 'technology'}
]

relationships = [
    {'source': 'Avery Chen', 'relation': 'works_on', 'target': 'Project Atlas'},
    {'source': 'Sam Lee', 'relation': 'works_on', 'target': 'Project Atlas'},
    {'source': 'Dana Park', 'relation': 'reviews', 'target': 'Project Atlas'},
    {'source': 'Project Atlas', 'relation': 'uses', 'target': 'SQLite + LanceDB'}
]

(base / 'input' / 'conversations.json').write_text(json.dumps(conversations, indent=2), encoding='utf-8')
(base / 'input' / 'entities.json').write_text(json.dumps(entities, indent=2), encoding='utf-8')
(base / 'input' / 'relationships.json').write_text(json.dumps(relationships, indent=2), encoding='utf-8')
(base / 'input' / 'markers.txt').write_text('MARKER_ENTITY=Project Atlas\nMARKER_CONVERSATION=c2\n', encoding='utf-8')
