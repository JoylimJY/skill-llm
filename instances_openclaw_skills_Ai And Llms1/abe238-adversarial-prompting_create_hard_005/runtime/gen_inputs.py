import json
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def make_pdf(path: Path, title: str, lines: list[str]):
    c = canvas.Canvas(str(path), pagesize=letter)
    width, height = letter
    y = height - 72
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, y, title)
    y -= 28
    c.setFont("Helvetica", 10)
    for line in lines:
        if y < 72:
            c.showPage()
            y = height - 72
            c.setFont("Helvetica", 10)
        c.drawString(72, y, line)
        y -= 14
    c.save()


base = Path('.')

# Deterministic marker content for evaluation
(base / 'README_brief.txt').write_text(
    'MARKER: ATLAS-DELTA-77\n'
    'Objective: choose a deployment strategy for a latency-sensitive service.\n'
    'Constraint: the final answer must include three approaches, adversarial critique, fixes, validation, consolidation, ranked options, and a recommendation.\n',
    encoding='utf-8'
)

(base / 'decision_context.json').write_text(
    json.dumps({
        'project': 'Atlas Delta',
        'service': 'real-time anomaly scoring API',
        'traffic': '12k req/s p95 target under 120ms',
        'marker': 'ATLAS-DELTA-77',
        'must_consider': [
            'blue-green rollout',
            'canary with automated rollback',
            'shadow deployment with offline comparison'
        ]
    }, indent=2),
    encoding='utf-8'
)

make_pdf(
    base / 'ops_notes.pdf',
    'Atlas Delta Operations Notes',
    [
        'MARKER: ATLAS-DELTA-77',
        'The system currently uses a monolith with a single database primary.',
        'Recent incidents were caused by configuration drift, slow warm-up, and insufficient rollback checks.',
        'Any recommendation must explicitly address failure detection, validation, and rollout safety.'
    ]
)

(base / 'requirements.txt').write_text(
    'No external task files should be added by the solver.\n',
    encoding='utf-8'
)
