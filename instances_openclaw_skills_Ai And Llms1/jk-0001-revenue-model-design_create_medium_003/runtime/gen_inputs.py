import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def make_pdf(path: Path, lines):
    c = canvas.Canvas(str(path), pagesize=letter)
    width, height = letter
    y = height - 72
    for line in lines:
        c.drawString(72, y, line)
        y -= 16
        if y < 72:
            c.showPage()
            y = height - 72
    c.save()


def main():
    base = Path('.')
    notes = base / 'input_notes.pdf'
    lines = [
        'MARKER:REV-MODEL-2025-ALPHA',
        'Business: Solo founder building a B2B SaaS tool for invoice follow-up automation.',
        'Audience: freelance accountants and tiny agencies.',
        'Goal: predictable monthly revenue with low billing complexity.',
        'Current ideas:',
        '- subscription as the core model',
        '- one-time template pack as an add-on',
        '- occasional consulting setup fee',
        'Constraints:',
        '- prefer monthly billing',
        '- can support annual plans later',
        '- should avoid marketplace or heavy usage billing at launch',
    ]
    make_pdf(notes, lines)

    (base / 'instructions.txt').write_text(
        'Use the notes to design a revenue model. Focus on a practical solo-founder stack, payment flow, and simple projections.\n',
        encoding='utf-8'
    )


if __name__ == '__main__':
    main()
