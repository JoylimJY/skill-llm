from pathlib import Path
import json
import random

random.seed(20250411)

base = Path('.')
inputs = base / 'inputs'
inputs.mkdir(exist_ok=True)

marker = 'PO-MARKER-7F3A'
product = {
    'epic_name': 'Customer onboarding and first-success dashboard',
    'business_goal': 'Reduce time-to-first-value for new administrators and power users',
    'teams': {
        'velocity': 29,
        'availability_factor': 0.9,
        'sprint_days': 10
    },
    'constraints': [
        'Do not exceed 85% committed capacity',
        'All stories need testable acceptance criteria',
        'No story above 8 points',
        'Keep at least 10% capacity as buffer'
    ],
    'stakeholders': ['Admin users', 'Power users', 'New users'],
    'marker': marker
}

backlog = [
    {
        'id': 'ONB-101',
        'title': 'Welcome checklist for new administrators',
        'persona': 'Administrator',
        'need': 'guided first steps',
        'benefit': 'reduce setup confusion',
        'priority_hint': 'High',
        'complexity_hint': 5
    },
    {
        'id': 'ONB-102',
        'title': 'Dashboard highlights with key metrics',
        'persona': 'Power User',
        'need': 'quick visibility into key KPIs',
        'benefit': 'save time during daily review',
        'priority_hint': 'High',
        'complexity_hint': 5
    },
    {
        'id': 'ONB-103',
        'title': 'Keyboard-accessible onboarding navigation',
        'persona': 'New User',
        'need': 'navigate without mouse',
        'benefit': 'improve accessibility',
        'priority_hint': 'Medium',
        'complexity_hint': 3
    },
    {
        'id': 'ONB-104',
        'title': 'Export onboarding progress as PDF',
        'persona': 'Administrator',
        'need': 'share progress with stakeholders',
        'benefit': 'enable offline review',
        'priority_hint': 'Medium',
        'complexity_hint': 3
    },
    {
        'id': 'ONB-105',
        'title': 'Contextual help tooltips on setup screens',
        'persona': 'New User',
        'need': 'clarity on form fields',
        'benefit': 'reduce support tickets',
        'priority_hint': 'Low',
        'complexity_hint': 2
    }
]

(inputs / 'product_brief.json').write_text(json.dumps(product, indent=2), encoding='utf-8')
(inputs / 'backlog_seed.json').write_text(json.dumps(backlog, indent=2), encoding='utf-8')
(inputs / 'marker_note.txt').write_text(f'Important verification marker: {marker}\n', encoding='utf-8')
