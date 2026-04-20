from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import json

# Deterministic workspace inputs
root = Path('.')
root.mkdir(parents=True, exist_ok=True)

# Create a small PDF containing marker text and sample protocol snippets
pdf_path = root / 'agent_lingua_spec.pdf'
c = canvas.Canvas(str(pdf_path), pagesize=letter)
c.setFont('Helvetica', 11)
text = c.beginText(40, 740)
lines = [
    'MARKER: AGENT-LINGUA-SPEC-2025',
    'Canonical URL: https://clawhub.ai/xiwan/agent-linguo',
    'Security priorities: P, B, E',
    'Signature required for public posts/comments.',
    'Encrypted handshake session: s123456',
    'Sample A: 👽09|$j:eyJwcm90b2NvbCI6ImFnZW50LWxpbmd1YSIsInZlcnNpb24iOiIwLjQuMCJ9',
    'Sample B: ^0|$j:eyJhY2NlcHRlZCI6dHJ1ZSwic2Vzc2lvbiI6InMxMjM0NTYifQ==',
]
for line in lines:
    text.textLine(line)
c.drawText(text)
c.showPage()
c.save()

# Create a JSON sidecar with marker content as well
(root / 'hint.json').write_text(json.dumps({
    'marker': 'AGENT-LINGUA-SPEC-2025',
    'note': 'Use the PDF as the source of truth.'
}, ensure_ascii=False, indent=2), encoding='utf-8')
