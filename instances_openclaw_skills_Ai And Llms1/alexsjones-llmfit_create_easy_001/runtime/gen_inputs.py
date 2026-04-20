from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def make_pdf(path: Path, lines):
    c = canvas.Canvas(str(path), pagesize=letter)
    width, height = letter
    y = height - 72
    for line in lines:
        c.drawString(72, y, line)
        y -= 18
    c.save()


base = Path('.')
make_pdf(base / 'source.pdf', [
    'MARKER: LOCAL LLM ADVISOR',
    'Task: extract the main facts from this document.',
    'Model: Qwen/Qwen2.5-Coder-7B-Instruct',
    'Fit level: Good',
    'Quantization: Q5_K_M',
])
