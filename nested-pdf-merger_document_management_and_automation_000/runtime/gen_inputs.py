#!/usr/bin/env python3
"""
Generate a realistic nested compliance/legal document tree for the benchmark task.
Structure:
  filings/
    Q1_2024/
      Section_1/
        report_1.pdf
        report_2.pdf
        report_10.pdf        <- tests natural sort vs alpha
      Section_2/
        report_1.pdf
        report_3.pdf
      .hidden_notes/         <- hidden dir with PDFs (should be excluded via --exclude-hidden)
        secret.pdf
    Q2_2024/
      Section_1/
        report_1.pdf
        report_2.pdf
      Section_9/
        report_1.pdf
      Section_10/            <- natural sort critical: comes after Section_9 naturally, not before Section_2
        report_1.pdf
    Archive/                 <- MUST be excluded per task instructions
      old_report.pdf
      Q0_2023/
        legacy.pdf
    Draft/                   <- MUST be excluded per task instructions
      draft_1.pdf
      draft_2.pdf
    .internal/               <- hidden dir (should be excluded by --exclude-hidden)
      notes.pdf
"""

import os
import struct
import zlib
from pathlib import Path

WORKSPACE = Path("/workspace")
FILINGS_DIR = WORKSPACE / "filings"

def make_minimal_pdf(title: str) -> bytes:
    """Generate a valid minimal single-page PDF with a title annotation."""
    # We create a minimal valid PDF from scratch
    content_stream = f"BT /F1 12 Tf 50 750 Td ({title}) Tj ET".encode()
    compressed = zlib.compress(content_stream)

    objects = []

    # Object 1: Catalog
    objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")

    # Object 2: Pages
    objects.append(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")

    # Object 3: Page
    objects.append(
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R "
        b"/MediaBox [0 0 612 792] "
        b"/Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
    )

    # Object 4: Content stream (compressed)
    stream_data = compressed
    objects.append(
        f"4 0 obj\n<< /Length {len(stream_data)} /Filter /FlateDecode >>\nstream\n".encode()
        + stream_data
        + b"\nendstream\nendobj\n"
    )

    # Object 5: Font
    objects.append(
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    )

    # Build PDF
    header = b"%PDF-1.4\n"
    body = b""
    offsets = []
    pos = len(header)
    for obj in objects:
        offsets.append(pos)
        body += obj
        pos += len(obj)

    # Cross-reference table
    xref_offset = len(header) + len(body)
    n = len(objects) + 1
    xref = f"xref\n0 {n}\n0000000000 65535 f \n".encode()
    for off in offsets:
        xref += f"{off:010d} 00000 n \n".encode()

    trailer = (
        f"trailer\n<< /Size {n} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode()

    return header + body + xref + trailer


def write_pdf(path: Path, title: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(make_minimal_pdf(title))


# ── Main structure ───────────────────────────────────────────────────────────

# Q1_2024 / Section_1
write_pdf(FILINGS_DIR / "Q1_2024" / "Section_1" / "report_1.pdf",  "Q1 S1 Report 1")
write_pdf(FILINGS_DIR / "Q1_2024" / "Section_1" / "report_2.pdf",  "Q1 S1 Report 2")
write_pdf(FILINGS_DIR / "Q1_2024" / "Section_1" / "report_10.pdf", "Q1 S1 Report 10")

# Q1_2024 / Section_2
write_pdf(FILINGS_DIR / "Q1_2024" / "Section_2" / "report_1.pdf",  "Q1 S2 Report 1")
write_pdf(FILINGS_DIR / "Q1_2024" / "Section_2" / "report_3.pdf",  "Q1 S2 Report 3")

# Q1_2024 / .hidden_notes  (hidden dir)
write_pdf(FILINGS_DIR / "Q1_2024" / ".hidden_notes" / "secret.pdf", "Q1 Hidden Secret")

# Q2_2024 / Section_1
write_pdf(FILINGS_DIR / "Q2_2024" / "Section_1"  / "report_1.pdf", "Q2 S1 Report 1")
write_pdf(FILINGS_DIR / "Q2_2024" / "Section_1"  / "report_2.pdf", "Q2 S1 Report 2")

# Q2_2024 / Section_9
write_pdf(FILINGS_DIR / "Q2_2024" / "Section_9"  / "report_1.pdf", "Q2 S9 Report 1")

# Q2_2024 / Section_10  (natural sort trap)
write_pdf(FILINGS_DIR / "Q2_2024" / "Section_10" / "report_1.pdf", "Q2 S10 Report 1")

# Archive (must be excluded)
write_pdf(FILINGS_DIR / "Archive" / "old_report.pdf",          "Archive Old Report")
write_pdf(FILINGS_DIR / "Archive" / "Q0_2023" / "legacy.pdf", "Archive Legacy 2023")

# Draft (must be excluded)
write_pdf(FILINGS_DIR / "Draft" / "draft_1.pdf", "Draft 1")
write_pdf(FILINGS_DIR / "Draft" / "draft_2.pdf", "Draft 2")

# .internal hidden dir
write_pdf(FILINGS_DIR / ".internal" / "notes.pdf", "Internal Notes")

# Distractor non-PDF files scattered around (should not cause issues)
distractor_texts = [
    FILINGS_DIR / "Q1_2024" / "Section_1" / "metadata.txt",
    FILINGS_DIR / "Q1_2024" / "README.md",
    FILINGS_DIR / "Q2_2024" / "Section_9" / "index.csv",
    FILINGS_DIR / "Q2_2024" / "changelog.log",
    FILINGS_DIR / "Archive" / "ARCHIVE_NOTE.txt",
    FILINGS_DIR / "Draft"   / "DRAFT_NOTE.txt",
    FILINGS_DIR / "config.json",
]
for p in distractor_texts:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("This is a distractor file and should be ignored by the merger.\n")

print("Workspace generated successfully.")
print("Tree:")
for p in sorted(FILINGS_DIR.rglob("*")):
    print(" ", p.relative_to(WORKSPACE))