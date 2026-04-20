from pathlib import Path
from PIL import Image, ImageDraw
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import json

# Deterministic marker content
marker = "TOKENGUARD_MARKER_7F3A9C"
workspace = Path('.')

# Create a small JSON input with a known marker
session = {
    "limit": 25.0,
    "spent": 19.5,
    "entries": [
        {"amount": 5.0, "description": "Claude Sonnet - planning"},
        {"amount": 14.5, "description": "Claude Sonnet - implementation"}
    ],
    "marker": marker
}
(workspace / "session_input.json").write_text(json.dumps(session, indent=2), encoding="utf-8")

# Create a simple image containing the marker text
img = Image.new("RGB", (900, 220), color="white")
draw = ImageDraw.Draw(img)
draw.text((20, 80), f"Marker: {marker}", fill="black")
img.save(workspace / "marker_image.png")

# Create a PDF containing the marker text
pdf_path = workspace / "marker_document.pdf"
c = canvas.Canvas(str(pdf_path), pagesize=letter)
c.drawString(72, 720, f"TokenGuard reference marker: {marker}")
c.drawString(72, 700, "This document is deterministic and used for evaluation.")
c.save()
