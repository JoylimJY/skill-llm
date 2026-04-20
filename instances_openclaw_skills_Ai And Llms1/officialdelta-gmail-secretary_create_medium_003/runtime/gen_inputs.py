from pathlib import Path
import json
import random

random.seed(20250314)
base = Path('.')
(base / 'inbox').mkdir(exist_ok=True)

messages = [
    {
        'id': 'm1',
        'threadId': 't1',
        'from': 'FAU College of Medicine Admissions <admissions@fau.edu>',
        'subject': 'Admissions Offer Document Signature',
        'body': 'Hi Alan, please sign and return the admissions offer document by Friday afternoon. Thank you for your prompt attention.',
        'marker': 'MARKER_ADMISSIONS_OFFER_8Q2'
    },
    {
        'id': 'm2',
        'threadId': 't2',
        'from': 'Amazon <no-reply@amazon.com>',
        'subject': 'Your order has shipped',
        'body': 'Your package is on the way. Track your delivery using the order number below.',
        'marker': 'MARKER_SHIPPED_ORDER_4X9'
    },
    {
        'id': 'm3',
        'threadId': 't3',
        'from': 'Stanton FBLA <fbla@stanton.org>',
        'subject': 'Meeting room update for Thursday',
        'body': 'The FBLA meeting has moved to Room 214. Please let everyone know before 3 PM.',
        'marker': 'MARKER_FBBLA_ROOM_214'
    },
    {
        'id': 'm4',
        'threadId': 't4',
        'from': 'Chase Secure <alerts@chase.com>',
        'subject': 'Verify your account activity',
        'body': 'We noticed a new sign-in and need you to verify your account before continuing.',
        'marker': 'MARKER_ACCOUNT_VERIFY_C7'
    },
    {
        'id': 'm5',
        'threadId': 't5',
        'from': 'Stanton AP Biology <apbio@stanton.org>',
        'subject': 'Lab report extension request',
        'body': 'Could you please send the lab report extension form by tonight? We need it before class tomorrow.',
        'marker': 'MARKER_APBIO_EXTENSION_Z3'
    },
    {
        'id': 'm6',
        'threadId': 't6',
        'from': 'Medical Society <medsoc@stanton.org>',
        'subject': 'Volunteer schedule draft',
        'body': 'Attached is the draft schedule for the clinic volunteer event. Reply if you want a different slot.',
        'marker': 'MARKER_VOL_SCHEDULE_P1'
    }
]

for msg in messages:
    path = base / 'inbox' / f"{msg['id']}.json"
    path.write_text(json.dumps(msg, indent=2), encoding='utf-8')

(base / 'README.txt').write_text(
    'Deterministic Gmail triage task inputs.\n' +
    'Markers: ' + ', '.join(m['marker'] for m in messages) + '\n',
    encoding='utf-8'
)
