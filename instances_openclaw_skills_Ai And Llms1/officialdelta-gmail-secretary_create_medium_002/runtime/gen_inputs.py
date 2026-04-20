from pathlib import Path
import json

base = Path('.')
(base / 'cache').mkdir(exist_ok=True)
(base / 'references').mkdir(exist_ok=True)

summaries = [
    {
        'i': 0,
        'id': 'msg-001',
        'threadId': 'thr-001',
        'subj': 'AP Biology lab makeup',
        'from': 'teacher@example.edu',
        'snip': 'Hi Alan, please submit the lab makeup by Friday. Thanks!',
        'date': '2025-05-01T12:00:00Z'
    },
    {
        'i': 1,
        'id': 'msg-002',
        'threadId': 'thr-002',
        'subj': 'Amazon order receipt #A-7781',
        'from': 'orders@amazon.com',
        'snip': 'Your receipt for the new monitor is attached. Total: $219.99.',
        'date': '2025-05-01T13:00:00Z'
    },
    {
        'i': 2,
        'id': 'msg-003',
        'threadId': 'thr-003',
        'subj': 'Stanton NHS meeting reminder',
        'from': 'nhs@stanton.edu',
        'snip': 'Reminder: NHS will meet in room 214 after school tomorrow.',
        'date': '2025-05-02T14:00:00Z'
    },
    {
        'i': 3,
        'id': 'msg-004',
        'threadId': 'thr-004',
        'subj': 'Password reset requested',
        'from': 'security@service.com',
        'snip': 'We detected a password reset request for your account. If this was not you, secure your account now.',
        'date': '2025-05-03T15:00:00Z'
    },
    {
        'i': 4,
        'id': 'msg-005',
        'threadId': 'thr-005',
        'subj': 'FBLA volunteer sign-up',
        'from': 'fbla@stanton.edu',
        'snip': 'Please reply if you can help at the competition this weekend.',
        'date': '2025-05-04T16:00:00Z'
    }
]

voice = """# Alan voice reference (auto)

Generated: 2025-05-05T00:00:00.000Z
Sample size (sent snippets): 3

## High-level style (heuristics)
- Concise snippets (<=180 chars): 67%
- Greeting present: 33%
- Gratitude language: 67%

## Drafting rules
- Clear, direct, polite.
- Keep it short by default (2–6 sentences).
- If you need something: context -> ask -> deadline/timeframe.
- Avoid filler.

## Representative micro-snippets (snippets only)
- “Hello, thank you for the update. I will review this tonight.”
- “Thanks so much for your help; I appreciate it.”
- “Hi Robin, I attached the form and should hear back by Friday.”
"""

labels = [
    {'index': 0, 'id': 'msg-001', 'threadId': 'thr-001', 'label': 'School', 'needsReply': True},
    {'index': 1, 'id': 'msg-002', 'threadId': 'thr-002', 'label': 'Receipt / Billing', 'needsReply': False},
    {'index': 2, 'id': 'msg-003', 'threadId': 'thr-003', 'label': 'Clubs', 'needsReply': False},
    {'index': 3, 'id': 'msg-004', 'threadId': 'thr-004', 'label': 'Admin / Accounts', 'needsReply': True},
    {'index': 4, 'id': 'msg-005', 'threadId': 'thr-005', 'label': 'Clubs', 'needsReply': True},
]

(base / 'cache' / 'gmail-inbox-summaries.json').write_text(json.dumps(summaries, indent=2) + '\n', encoding='utf-8')
(base / 'cache' / 'gmail-triage-labels.json').write_text(json.dumps(labels, indent=2) + '\n', encoding='utf-8')
(base / 'references' / 'voice.md').write_text(voice, encoding='utf-8')
