#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="/workspace/scripts"
mkdir -p "$SKILL_DIR"

# ── Write the clean_notebooklm_pdf.py script ─────────────────────────────────
cat > "$SKILL_DIR/clean_notebooklm_pdf.py" << 'PYEOF'
#!/usr/bin/env python3
"""
NotebookLM PDF Cleaner
Masks the bottom-right NotebookLM footer badge on each page of a
NotebookLM slide-deck PDF export.
"""

import argparse
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("ERROR: PyMuPDF (fitz) is required. Install with: pip install pymupdf", file=sys.stderr)
    sys.exit(1)

# Default mask dimensions (tuned for 16:9 NotebookLM slide decks, 1376×774 pt)
DEFAULT_MASK_X = 1208
DEFAULT_MASK_Y = 0
DEFAULT_MASK_W = 168
DEFAULT_MASK_H = 32

# Reference page size the defaults were designed for
REF_W = 1376.0
REF_H = 774.0


def parse_args():
    p = argparse.ArgumentParser(
        description="Mask the NotebookLM footer badge in a slide-deck PDF."
    )
    p.add_argument("input", help="Path to the source NotebookLM PDF")
    p.add_argument("--out", help="Explicit output path (default: input-clean.pdf)")
    p.add_argument("--inspect", action="store_true",
                   help="Print page info and exit without writing any file")
    p.add_argument("--mask-x", type=float, default=DEFAULT_MASK_X,
                   help="Mask left edge in PDF points on the reference page (default: 1208)")
    p.add_argument("--mask-y", type=float, default=DEFAULT_MASK_Y,
                   help="Mask bottom edge in PDF points on the reference page (default: 0)")
    p.add_argument("--mask-w", type=float, default=DEFAULT_MASK_W,
                   help="Mask width in PDF points on the reference page (default: 168)")
    p.add_argument("--mask-h", type=float, default=DEFAULT_MASK_H,
                   help="Mask height in PDF points on the reference page (default: 32)")
    p.add_argument("--strip-metadata", action="store_true",
                   help="Clear all PDF metadata fields")
    p.add_argument("--strip-annots", action="store_true",
                   help="Delete all annotations from each page")
    p.add_argument("--force", action="store_true",
                   help="Allow overwriting an existing output file")
    return p.parse_args()


def main():
    args = parse_args()

    input_path = Path(args.input).resolve()

    # Safety: refuse non-PDF
    if input_path.suffix.lower() != ".pdf":
        print(f"ERROR: Input must be a .pdf file, got: {input_path.suffix}", file=sys.stderr)
        sys.exit(1)

    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Determine output path
    if args.out:
        output_path = Path(args.out).resolve()
    else:
        output_path = input_path.with_name(input_path.stem + "-clean.pdf")

    # Safety: refuse to overwrite source
    if output_path == input_path:
        print("ERROR: Output path must differ from input path.", file=sys.stderr)
        sys.exit(1)

    # Open document
    doc = fitz.open(str(input_path))

    if args.inspect:
        print(f"File   : {input_path}")
        print(f"Pages  : {len(doc)}")
        for i, page in enumerate(doc):
            r = page.rect
            print(f"  Page {i+1}: width={r.width:.1f} pt, height={r.height:.1f} pt")
        meta = doc.metadata
        if any(meta.values()):
            print("Metadata:")
            for k, v in meta.items():
                if v:
                    print(f"  {k}: {v}")
        doc.close()
        return

    # Safety: refuse to overwrite existing output (unless --force)
    if output_path.exists() and not args.force:
        print(
            f"ERROR: Output file already exists: {output_path}\n"
            "Use --force to overwrite.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Strip metadata if requested
    if args.strip_metadata:
        doc.set_metadata({})

    # Process each page
    for page in doc:
        pw = page.rect.width
        ph = page.rect.height

        # Scale mask from reference dimensions to actual page dimensions
        sx = pw / REF_W
        sy = ph / REF_H

        scaled_x = args.mask_x * sx
        scaled_y = args.mask_y * sy
        scaled_w = args.mask_w * sx
        scaled_h = args.mask_h * sy

        # Convert from PDF coords (origin=bottom-left) to PyMuPDF rect (origin=top-left)
        # PDF:  x0=mask_x, y0=mask_y (bottom), width=mask_w, height=mask_h
        # MuPDF: x0=same, y1=page_height - pdf_y0, y0=y1 - mask_h
        rect_top    = ph - scaled_y - scaled_h
        rect_bottom = ph - scaled_y
        rect_left   = scaled_x
        rect_right  = scaled_x + scaled_w

        mask_rect = fitz.Rect(rect_left, rect_top, rect_right, rect_bottom)

        # Draw a white rectangle over the badge area
        page.draw_rect(mask_rect, color=(1, 1, 1), fill=(1, 1, 1))

        # Strip annotations if requested
        if args.strip_annots:
            annots = list(page.annots())
            for annot in annots:
                page.delete_annot(annot)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    doc.close()
    print(f"Saved cleaned PDF → {output_path}")


if __name__ == "__main__":
    main()
PYEOF

chmod +x "$SKILL_DIR/clean_notebooklm_pdf.py"
echo "[setup] clean_notebooklm_pdf.py installed at $SKILL_DIR"

# Verify the input PDF was created by gen_inputs
if [ -f /workspace/projects/acme-corp/raw_exports/acme_q2_strategy.pdf ]; then
    echo "[setup] Input PDF confirmed present."
else
    echo "[setup] WARNING: Input PDF not found — gen_inputs may not have run."
fi

echo "[setup] Done."