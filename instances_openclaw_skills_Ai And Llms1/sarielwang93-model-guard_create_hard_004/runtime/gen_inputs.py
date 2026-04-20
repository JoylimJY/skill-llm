from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

root = Path('.')

# Marker text files
(root / 'status_snapshot.txt').write_text(
    'anti-gravity usage: claude-opus-4-5-thinking 78% left, claude-sonnet-4-5 65% left, gemini-3-flash 100% left\n'
    'MARKER_STATUS_ALPHA_9b7e\n',
    encoding='utf-8'
)

(root / 'status_snapshot_alt.txt').write_text(
    'anti-gravity usage: claude-opus-4-5-thinking 12% left, claude-sonnet-4-5 18% left, gpt-oss-120b-medium 19% left\n'
    'MARKER_STATUS_BETA_2c4d\n',
    encoding='utf-8'
)

# Deterministic JSON payload
(root / 'model_targets.json').write_text(
    '{"preferred":"google-antigravity/claude-opus-4-5-thinking","fallback":"google/gemini-3-flash-preview","threshold":20,"marker":"MARKER_JSON_44aa"}\n',
    encoding='utf-8'
)

# PDF with embedded marker text
pdf_path = root / 'quota_report.pdf'
c = canvas.Canvas(str(pdf_path), pagesize=letter)
c.setFont('Helvetica', 12)
c.drawString(72, 720, 'Quarterly quota report')
c.drawString(72, 700, 'MARKER_PDF_DELTA_77ff')
c.drawString(72, 680, 'Anti-Gravity model health overview')
c.showPage()
c.drawString(72, 720, 'Appendix A')
c.drawString(72, 700, 'claude-sonnet-4-5-thinking 33% left')
c.save()
