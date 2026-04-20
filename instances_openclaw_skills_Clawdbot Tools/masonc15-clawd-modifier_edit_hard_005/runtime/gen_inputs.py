from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import random
import json

random.seed(1337)

# Seed workspace files with verifiable markers
Path('workspace').mkdir(exist_ok=True)
Path('assets').mkdir(exist_ok=True)
Path('references').mkdir(exist_ok=True)
Path('scripts').mkdir(exist_ok=True)

# Marker text file
Path('workspace/seed_markers.txt').write_text(
    """CLAWD_SEED_MARKER: WINTER_FESTIVAL_2025
EXPECTED_COLOR: rgb(100,149,237)
EXPECTED_THEME_KEY: clawd_body
EXPECTED_ART_HINT: tiny hat and raised arms
""",
    encoding='utf-8'
)

# Minimal JSON manifest with markers
manifest = {
    "task_id": "clawd_winter_festival_001",
    "markers": [
        "CLAWD_SEED_MARKER: WINTER_FESTIVAL_2025",
        "EXPECTED_COLOR: rgb(100,149,237)",
        "EXPECTED_ART_HINT: tiny hat and raised arms"
    ],
    "noise": [random.randint(1, 9999) for _ in range(5)]
}
Path('workspace/manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')

# Seed a PDF with an embedded marker string the eval can look for
pdf_path = Path('workspace/clawd_notes.pdf')
can = canvas.Canvas(str(pdf_path), pagesize=letter)
can.setFont('Helvetica', 12)
can.drawString(72, 720, 'Clawd Winter Festival Notes')
can.drawString(72, 700, 'Marker: WINTER_FESTIVAL_2025')
can.drawString(72, 680, 'Target color: rgb(100,149,237)')
can.drawString(72, 660, 'Artwork: raised arms + tiny hat')
can.showPage()
can.save()

# Seed a text reference to make the task self-contained
Path('references/task_brief.txt').write_text(
    "Modify the Clawd mascot to a winter festival variant, change default body color to Ocean Blue, and preserve reversibility markers.",
    encoding='utf-8'
)
