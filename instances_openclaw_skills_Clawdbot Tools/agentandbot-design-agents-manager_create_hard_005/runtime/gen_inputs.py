from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import json

base = Path('.')

# Marker-rich input data
registry = {
    'agents': [
        {'id': 'main', 'name': 'Clawdia', 'role': 'orchestrator', 'reports_to': 'Ilkerkaan', 'can_assign_to': ['research-1', 'dev-1', 'ops-1']},
        {'id': 'research-1', 'name': 'InsightFox', 'role': 'researcher', 'reports_to': 'main', 'can_assign_to': []},
        {'id': 'dev-1', 'name': 'ByteForge', 'role': 'developer', 'reports_to': 'main', 'can_assign_to': []},
        {'id': 'ops-1', 'name': 'StableHand', 'role': 'operator', 'reports_to': 'main', 'can_assign_to': []},
        {'id': 'supervisor', 'name': 'Ilkerkaan', 'role': 'human', 'reports_to': None, 'can_assign_to': ['main']},
    ],
    'marker': 'AGENT-REGISTRY-MARKER-7F3A',
}
(base / 'registry_seed.json').write_text(json.dumps(registry, indent=2), encoding='utf-8')

instructions = """
Routing challenge marker: ROUTING-RULES-DELTA-114

Required outputs:
- registry_report.md
- hierarchy.pdf
- routing_audit.json

Special constraints:
- main must report to Ilkerkaan
- research-1, dev-1, ops-1 must report to main
- main can assign to all three specialists
- specialists cannot assign to anyone
- audit must mention handshake/approval flow
""".strip()
(base / 'task_instructions.txt').write_text(instructions, encoding='utf-8')

# Create a small PDF with embedded marker text for the evaluator to verify extraction
pdf_path = base / 'reference_sheet.pdf'
c = canvas.Canvas(str(pdf_path), pagesize=letter)
width, height = letter
c.setFont('Helvetica', 12)
lines = [
    'Agent Routing Reference Sheet',
    'MARKER: PDF-ROUTE-ALPHA-5521',
    'main -> reports_to -> Ilkerkaan',
    'main -> can_assign_to -> research-1, dev-1, ops-1',
    'specialists -> report_to -> main',
]
y = height - 1 * inch
for line in lines:
    c.drawString(1 * inch, y, line)
    y -= 0.3 * inch
c.showPage()
c.save()
