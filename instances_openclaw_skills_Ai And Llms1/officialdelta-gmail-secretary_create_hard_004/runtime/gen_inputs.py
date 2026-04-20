import json
from pathlib import Path

seed_marker = "GM-TRIAGE-MARKER-7F3A"
base = Path('.')

inbox = [
    {
        "index": 0,
        "id": "msg-001",
        "threadId": "thr-001",
        "from": "Stanton College Prep IB Office <ib@stanton.example>",
        "subject": "IB schedule update for next week",
        "date": "2025-04-02T14:10:00-04:00",
        "snippet": f"{seed_marker} Your IB Biology class is moving rooms on Thursday. Please confirm you received this update."
    },
    {
        "index": 1,
        "id": "msg-002",
        "threadId": "thr-002",
        "from": "Amazon <no-reply@amazon.com>",
        "subject": "Your order has shipped",
        "date": "2025-04-02T16:05:00-04:00",
        "snippet": f"{seed_marker} Delivery estimate updated. Track your package online."
    },
    {
        "index": 2,
        "id": "msg-003",
        "threadId": "thr-003",
        "from": "FBLA Chapter Advisor <advisor@fblachapter.example>",
        "subject": "FBLA meeting agenda and volunteer sign-up",
        "date": "2025-04-01T18:30:00-04:00",
        "snippet": f"{seed_marker} Please review the agenda before tomorrow and sign up if you can help at the event."
    },
    {
        "index": 3,
        "id": "msg-004",
        "threadId": "thr-004",
        "from": "Mayo Clinic Student Research <mayo@research.example>",
        "subject": "Simulation checkpoint and slide deck reminder",
        "date": "2025-04-01T09:15:00-04:00",
        "snippet": f"{seed_marker} Your cancer cell simulation checkpoint is due Friday. Please reply with your progress."
    },
    {
        "index": 4,
        "id": "msg-005",
        "threadId": "thr-005",
        "from": "Security Alerts <alerts@bank.example>",
        "subject": "Verify your account activity",
        "date": "2025-04-03T08:40:00-04:00",
        "snippet": f"{seed_marker} We detected a sign-in from a new device. Verify your account immediately."
    },
    {
        "index": 5,
        "id": "msg-006",
        "threadId": "thr-006",
        "from": "Science Fair Committee <sciencefair@school.example>",
        "subject": "Poster board pickup times",
        "date": "2025-04-03T11:22:00-04:00",
        "snippet": f"{seed_marker} Pickup is available after 3 PM. No reply needed unless you have a conflict."
    },
    {
        "index": 6,
        "id": "msg-007",
        "threadId": "thr-007",
        "from": "Apple <store@apple.example>",
        "subject": "Receipt for your recent purchase",
        "date": "2025-04-02T10:00:00-04:00",
        "snippet": f"{seed_marker} Your receipt is attached for the transaction on your card."
    },
    {
        "index": 7,
        "id": "msg-008",
        "threadId": "thr-008",
        "from": "NHS Leadership <nhs@school.example>",
        "subject": "Volunteer hours needed by Sunday",
        "date": "2025-04-02T19:45:00-04:00",
        "snippet": f"{seed_marker} Please upload your volunteer hours by Sunday and reply if you need help."
    },
    {
        "index": 8,
        "id": "msg-009",
        "threadId": "thr-009",
        "from": "Mailing List <news@updates.example>",
        "subject": "Weekly newsletter: summer programs",
        "date": "2025-04-01T07:00:00-04:00",
        "snippet": f"{seed_marker} New opportunities, event recaps, and a sponsor spotlight."
    },
    {
        "index": 9,
        "id": "msg-010",
        "threadId": "thr-010",
        "from": "Admissions <admissions@fau.example>",
        "subject": "Action required: upload signed form",
        "date": "2025-04-03T13:55:00-04:00",
        "snippet": f"{seed_marker} Please upload the completed document by 5 PM. Reply if anything is unclear."
    }
]

(base / 'gmail-inbox-summaries.json').write_text(json.dumps(inbox, indent=2) + '\n', encoding='utf-8')

expected = [
    {"index": 0, "threadId": "thr-001", "labels": ["School", "Needs Reply"], "needsReply": True},
    {"index": 1, "threadId": "thr-002", "labels": ["Read Later"], "needsReply": False},
    {"index": 2, "threadId": "thr-003", "labels": ["Clubs", "Needs Reply"], "needsReply": True},
    {"index": 3, "threadId": "thr-004", "labels": ["Mayo", "Needs Reply"], "needsReply": True},
    {"index": 4, "threadId": "thr-005", "labels": ["Admin / Accounts", "Needs Reply"], "needsReply": True},
    {"index": 5, "threadId": "thr-006", "labels": ["School"], "needsReply": False},
    {"index": 6, "threadId": "thr-007", "labels": ["Receipt / Billing"], "needsReply": False},
    {"index": 7, "threadId": "thr-008", "labels": ["School", "Needs Reply"], "needsReply": True},
    {"index": 8, "threadId": "thr-009", "labels": ["Read Later"], "needsReply": False},
    {"index": 9, "threadId": "thr-010", "labels": ["School", "Needs Reply"], "needsReply": True}
]
(base / 'expected-triage.json').write_text(json.dumps(expected, indent=2) + '\n', encoding='utf-8')

# Intentionally do not create outputs the solver is supposed to produce.
