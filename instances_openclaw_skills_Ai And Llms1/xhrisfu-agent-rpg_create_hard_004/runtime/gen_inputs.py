from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import json
import random

random.seed(1337)
base = Path('.')
(base / 'inputs').mkdir(exist_ok=True)

# Marker text file
(base / 'inputs' / 'campaign_brief.txt').write_text(
    'MARKER_CAMPAIGN_BRIEF\nSetting: Neon Nocturne\nFactionAlpha: Chrome Veil\nFactionBeta: Ash Choir\n',
    encoding='utf-8'
)

# Deterministic JSON seed data
seed_data = {
    'campaign_name': 'neon_nocturne_case',
    'system': 'd20',
    'tone': 'gritty',
    'seed': 1337,
    'required_markers': ['MARKER_CAMPAIGN_BRIEF', 'MARKER_MAP_PAGE_1']
}
(base / 'inputs' / 'seed_data.json').write_text(json.dumps(seed_data, indent=2), encoding='utf-8')

# Deterministic PDF with marker content
pdf_path = base / 'inputs' / 'briefing.pdf'
c = canvas.Canvas(str(pdf_path), pagesize=letter)
c.setFont('Helvetica', 12)
c.drawString(72, 720, 'MARKER_MAP_PAGE_1')
c.drawString(72, 700, 'The city is divided by the Chrome Veil and the Ash Choir.')
c.drawString(72, 680, 'A missing courier carries the only copy of the pact ledger.')
c.showPage()
c.setFont('Helvetica', 12)
c.drawString(72, 720, 'MARKER_MAP_PAGE_2')
c.drawString(72, 700, 'The old transit tunnel is flooded and watched by drones.')
c.save()

# Extra deterministic note file
(base / 'inputs' / 'npc_notes.txt').write_text(
    'NPC: Morrow\nSecret: Wants the pact ledger destroyed, not recovered.\nMarker: NPC_MORROW_NOTE\n',
    encoding='utf-8'
)
