from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import json

root = Path('.')
(root / 'workspace').mkdir(exist_ok=True)

# Deterministic text inputs with marker content
(root / 'workspace' / 'HEARTBEAT.md').write_text(
    '# Heartbeat\n\nUrgent messages: none\nBlockers: waiting on API review\nCurrent date/time: 2025-05-12 09:30 UTC\n\nMarker: BUILD_SESSION_MARKER_ALPHA\n',
    encoding='utf-8'
)

(root / 'workspace' / 'project_notes.txt').write_text(
    'Project list:\n- Fix flaky session log formatting\n- Update build helper for blocker detection\n- Refactor task selection\n\nMarker: BUILD_SESSION_MARKER_BETA\n',
    encoding='utf-8'
)

# Create a small PDF input the assistant may use if desired
pdf_path = root / 'workspace' / 'session_brief.pdf'
c = canvas.Canvas(str(pdf_path), pagesize=letter)
c.drawString(72, 720, 'Build Session Brief')
c.drawString(72, 700, 'Marker: BUILD_SESSION_MARKER_PDF')
c.drawString(72, 680, 'Prefer the smallest useful task if blocked.')
c.save()

# A tiny JSON manifest with deterministic content
manifest = {
    'session_type': 'build',
    'priority': ['blockers', 'urgent messages', 'smallest useful task'],
    'marker': 'BUILD_SESSION_MARKER_GAMMA'
}
(root / 'workspace' / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
