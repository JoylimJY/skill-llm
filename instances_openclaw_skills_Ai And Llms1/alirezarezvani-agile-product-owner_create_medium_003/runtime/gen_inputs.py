from pathlib import Path
import json
import random

random.seed(42)

inputs = {
    'initiative.txt': (
        'MARKER_INITIATIVE::REPORT_EXPORT\n'
        'Initiative: self-service report export for end users and administrators.\n'
        'Goal: allow users to export filtered reports to PDF and CSV.\n'
        'Constraints: 2-week sprint, average velocity 28, one developer at 50% PTO.\n'
    ),
    'stakeholders.csv': (
        'persona,need,priority\n'
        'End User,Export reports to PDF and CSV,HIGH\n'
        'Administrator,Audit export activity,HIGH\n'
        'Power User,Export with filters and date ranges,MEDIUM\n'
    ),
    'epic_notes.md': (
        '# Epic Notes\n'
        'MARKER_EPIC::EXPORT_PACKAGE\n'
        '- Feature must be independent and testable.\n'
        '- Acceptance criteria must use Given-When-Then.\n'
        '- Split large work by workflow step and persona.\n'
    )
}

for name, content in inputs.items():
    Path(name).write_text(content, encoding='utf-8')
