from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import json
import random

random.seed(1337)

workspace = Path('.')

marker = "MARKER_TED_TALK_INPUT_9f3c2a"
text = """Technical conversation notes:
- We discovered that teams often explain what a system does, but not why it matters.
- The core insight is to turn an abstract technical lesson into a full narrative with concrete examples.
- A strong talk needs: hook, problem, discovery, real-world examples, implications, and Q&A.
- The audience asked for a 40-50 minute TED-style structure.
- Important constraint: use only the user-provided context; do not invent unsupported facts.

Marker: """ + marker + """
"""
(workspace / "conversation_notes.txt").write_text(text, encoding="utf-8")

# Create a deterministic PDF with marker content for verification
pdf_path = workspace / "reference_context.pdf"
cnv = canvas.Canvas(str(pdf_path), pagesize=letter)
width, height = letter
lines = [
    "Reference Context for TED Talk Task",
    "",
    "Key ideas:",
    "1. Explain why, not just what.",
    "2. Use concrete examples from the conversation.",
    "3. Include objections and responses in Q&A.",
    "",
    f"Marker: {marker}",
]

y = height - inch
for line in lines:
    cnv.drawString(inch, y, line)
    y -= 14
cnv.showPage()
cnv.save()

# Deterministic JSON metadata
meta = {
    "topic": "turning technical insight into a TED-style talk",
    "marker": marker,
    "required_sections": [
        "Opening",
        "Setup",
        "Problem",
        "Core Concept",
        "Real-World Examples",
        "Broader Implications",
        "Closing",
        "Q&A Preparation",
    ],
}
(workspace / "task_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
