from pathlib import Path
import json
import random

random.seed(1337)

base = Path('.')
(base / 'references').mkdir(parents=True, exist_ok=True)
(base / 'cache').mkdir(parents=True, exist_ok=True)

voice = """# Alan voice reference (auto)

Generated: 2025-04-10T12:00:00.000Z
Sample size (sent snippets): 8

## High-level style (heuristics)
- Concise snippets (<=180 chars): 62%
- Greeting present: 25%
- Gratitude language: 50%

## Drafting rules
- Clear, direct, polite.
- Keep it short by default (2–6 sentences).
- If you need something: context → ask → deadline/timeframe.
- Avoid filler.

## Representative micro-snippets (snippets only)
- “Hello, thank you for your help. I can come by after school tomorrow.”
- “Dear Ms. Smith, I attached the form and wanted to confirm receipt.”
- “Hi Robin, could you please send the updated document by Friday?”
- “Thank you so much for your quick response.”
- “Hello, I am completing the onboarding steps and have one question.”
- “Warm regards, Alan”
"""
(base / 'references' / 'voice.md').write_text(voice, encoding='utf-8')

messages = [
    {
        "i": 0,
        "id": "m-001",
        "threadId": "t-001",
        "subj": "AP Calc homework extension",
        "from": "Mrs. Carter <carter@stanton.edu>",
        "snip": "I can grant a one-day extension if you email me before 6 PM today with your plan.",
        "date": "2025-04-09"
    },
    {
        "i": 1,
        "id": "m-002",
        "threadId": "t-002",
        "subj": "Science Fair judging schedule",
        "from": "Science Fair Committee <events@school.org>",
        "snip": "Please confirm your availability for the Friday showcase and arrival time.",
        "date": "2025-04-09"
    },
    {
        "i": 2,
        "id": "m-003",
        "threadId": "t-003",
        "subj": "Tuition payment reminder",
        "from": "Billing Office <billing@school.org>",
        "snip": "Your statement is due next week. A PDF invoice is attached for review.",
        "date": "2025-04-08"
    },
    {
        "i": 3,
        "id": "m-004",
        "threadId": "t-004",
        "subj": "Password reset verification code",
        "from": "Security <no-reply@accounts.example.com>",
        "snip": "Use code 482193 to finish sign-in and reset your password if requested.",
        "date": "2025-04-08"
    },
    {
        "i": 4,
        "id": "m-005",
        "threadId": "t-005",
        "subj": "FBLA meeting location changed",
        "from": "FBLA Officers <fbla@clubmail.org>",
        "snip": "We moved the meeting to Room 214 after school on Thursday.",
        "date": "2025-04-08"
    },
    {
        "i": 5,
        "id": "m-006",
        "threadId": "t-006",
        "subj": "Mayo Clinic simulation update",
        "from": "Project Lead <lead@research.net>",
        "snip": "Please review the latest cancer cell simulation notes and reply with your changes.",
        "date": "2025-04-07"
    },
    {
        "i": 6,
        "id": "m-007",
        "threadId": "t-007",
        "subj": "Weekly newsletter: tech and campus news",
        "from": "Daily Brief <newsletter@media.example>",
        "snip": "Top stories this week include product launches, campus rankings, and event highlights.",
        "date": "2025-04-07"
    },
    {
        "i": 7,
        "id": "m-008",
        "threadId": "t-008",
        "subj": "Need reply: volunteer roster",
        "from": "NHS Advisor <advisor@school.org>",
        "snip": "Please send the updated volunteer roster and confirm whether you can cover Saturday morning.",
        "date": "2025-04-07"
    }
]

(base / 'cache' / 'gmail-inbox-summaries.json').write_text(json.dumps(messages, indent=2), encoding='utf-8')

expected = [
    {"index": 0, "id": "m-001", "threadId": "t-001", "label": "School", "needsReply": True},
    {"index": 1, "id": "m-002", "threadId": "t-002", "label": "School", "needsReply": True},
    {"index": 2, "id": "m-003", "threadId": "t-003", "label": "Receipt / Billing", "needsReply": False},
    {"index": 3, "id": "m-004", "threadId": "t-004", "label": "Admin / Accounts", "needsReply": False},
    {"index": 4, "id": "m-005", "threadId": "t-005", "label": "Clubs", "needsReply": True},
    {"index": 5, "id": "m-006", "threadId": "t-006", "label": "Mayo", "needsReply": True},
    {"index": 6, "id": "m-007", "threadId": "t-007", "label": "Read Later", "needsReply": False},
    {"index": 7, "id": "m-008", "threadId": "t-008", "label": "School", "needsReply": True},
]
(base / 'cache' / 'gmail-triage-labels.json').write_text(json.dumps(expected, indent=2), encoding='utf-8')

(base / 'cache' / 'gmail-triage.md').write_text(
    "Triage complete.\n- 8 messages reviewed\n- 5 need replies\n- 1 billing\n- 1 admin/security\n- 1 newsletter\n",
    encoding='utf-8'
)

(base / 'cache' / 'gmail-drafts.md').write_text(
    "Draft queue ready.\n- AP Calc homework extension\n- Science Fair judging schedule\n- FBLA meeting location changed\n- Mayo Clinic simulation update\n- NHS volunteer roster\n",
    encoding='utf-8'
)
