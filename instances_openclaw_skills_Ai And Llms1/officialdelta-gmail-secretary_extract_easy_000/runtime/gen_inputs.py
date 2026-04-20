from pathlib import Path
import json

base = Path('.')
(base / 'inbox').mkdir(exist_ok=True)

messages = [
    {
        'id': 'msg-001',
        'subject': 'Welcome to the newsletter',
        'body': 'Hello Alan, thanks for subscribing. This weekly update is just for reading later. MARKER-ALPHA'
    },
    {
        'id': 'msg-002',
        'subject': 'Receipt for your payment',
        'body': 'Hi Alan, your card was charged for the order. Attached receipt details. MARKER-BETA'
    },
    {
        'id': 'msg-003',
        'subject': 'School club meeting reminder',
        'body': 'Reminder for FBLA members: meeting on Friday after school. MARKER-GAMMA'
    }
]

with open(base / 'inbox' / 'messages.json', 'w', encoding='utf-8') as f:
    json.dump(messages, f, indent=2)

with open(base / 'inbox' / 'readme.txt', 'w', encoding='utf-8') as f:
    f.write('Input bundle for triage task.\n')
    f.write('Contains a hidden verification marker: MARKER-ALPHA.\n')
