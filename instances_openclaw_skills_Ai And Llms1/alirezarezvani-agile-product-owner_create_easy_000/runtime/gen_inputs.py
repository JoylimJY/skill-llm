from pathlib import Path

base = Path('.')
(base / 'skill_reference.txt').write_text(
    'MARKER: AGILE-PO-001\n'
    'Persona: marketing manager\n'
    'Feature: export campaign reports to PDF\n'
    'Benefit: share results with stakeholders\n',
    encoding='utf-8'
)

(base / 'request.txt').write_text(
    'Create a simple user story about exporting a report to PDF.\n'
    'Include 4 acceptance criteria and estimate it at 3 points.\n',
    encoding='utf-8'
)
