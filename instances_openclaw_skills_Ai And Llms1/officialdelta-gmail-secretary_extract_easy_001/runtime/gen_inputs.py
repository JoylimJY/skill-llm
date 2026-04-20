from pathlib import Path
import json

base = Path('.')
(base / 'cache').mkdir(exist_ok=True)

summaries = [
    {
        'i': 0,
        'id': 'msg-001',
        'threadId': 'thr-001',
        'subj': 'AP Biology club meeting tomorrow',
        'from': 'Science Fair Coach <coach@example.com>',
        'snip': 'Reminder: the club meets tomorrow after school in room 214. Please bring your project notes.',
        'date': 'Mon, 01 Apr 2025 09:00:00 -0400'
    },
    {
        'i': 1,
        'id': 'msg-002',
        'threadId': 'thr-002',
        'subj': 'Your receipt for laptop repair',
        'from': 'Billing <billing@example.com>',
        'snip': 'Attached is your receipt for the repair service. Payment has been processed successfully.',
        'date': 'Mon, 01 Apr 2025 10:15:00 -0400'
    },
    {
        'i': 2,
        'id': 'msg-003',
        'threadId': 'thr-003',
        'subj': 'Password reset requested',
        'from': 'Security <no-reply@example.com>',
        'snip': 'We received a request to reset your password. If you did not request this, ignore this email.',
        'date': 'Mon, 01 Apr 2025 11:30:00 -0400'
    }
]

(base / 'cache' / 'gmail-inbox-summaries.json').write_text(json.dumps(summaries, indent=2), encoding='utf-8')
