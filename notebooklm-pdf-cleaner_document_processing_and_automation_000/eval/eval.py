#!/usr/bin/env python3
"""
Evaluation script for the NotebookLM PDF Cleaner task.

Checks:
  1. Output file exists at the exact specified path.
  2. Output file is a valid PDF (not the stale placeholder).
  3. The white mask rectangle was applied (badge area is white on every page).
  4. PDF metadata was stripped (--strip-metadata used).
  5. Source file is unchanged (safety check).
  6. Output differs from the pre-existing stale file (--force was used correctly).
"""

import json
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print(json.dumps({
        "passed": False,
        "score": 0.0,
        "checks": [{"name": "pymupdf_available", "passed": False,
                    "detail": "PyMuPDF not installed in eval env"}]
    }))
    sys.exit(0)

def color_near_white(r, g, b, threshold=0.85):
    """Return True if all channels are above threshold (near-white)."""
    return r >= threshold and g >= threshold and b >= threshold

def eval_main(workspace: str):
    ws = Path(workspace)

    input_pdf   = ws / "projects/acme-corp/raw_exports/acme_q2_strategy.pdf"
    output_pdf  = ws / "projects/acme-corp/client_ready/acme_q2_strategy_final.pdf"
    stale_bytes = b"%PDF-1.4 stale placeholder - do not send to client\n"

    checks = []

    # ── Check 1: output file exists ──────────────────────────────────────────
    out_exists = output_pdf.exists() and output_pdf.stat().st_size > 200
    checks.append({
        "name": "output_file_exists",
        "passed": out_exists,
        "detail": f"Output at {output_pdf}: {'found' if out_exists else 'MISSING or too small'}"
    })

    if not out_exists:
        checks += [
            {"name": "output_is_valid_pdf",   "passed": False, "detail": "skipped — no output"},
            {"name": "stale_file_overwritten", "passed": False, "detail": "skipped — no output"},
            {"name": "badge_masked_all_pages", "passed": False, "detail": "skipped — no output"},
            {"name": "metadata_stripped",      "passed": False, "detail": "skipped — no output"},
            {"name": "source_unchanged",       "passed": False, "detail": "skipped — no output"},
        ]
        score = 0.0
        return checks, score

    # ── Check 2: stale file was overwritten (i.e., --force was used) ─────────
    try:
        actual_bytes = output_pdf.read_bytes()
        stale_overwritten = actual_bytes != stale_bytes
        checks.append({
            "name": "stale_file_overwritten",
            "passed": stale_overwritten,
            "detail": "Output differs from the pre-existing stale placeholder" if stale_overwritten
                      else "Output still contains the stale placeholder bytes — --force not used"
        })
    except Exception as e:
        stale_overwritten = False
        checks.append({"name": "stale_file_overwritten", "passed": False, "detail": str(e)})

    # ── Check 3: output is a valid PDF ───────────────────────────────────────
    doc_out = None
    try:
        doc_out = fitz.open(str(output_pdf))
        page_count = len(doc_out)
        valid_pdf = page_count == 4
        checks.append({
            "name": "output_is_valid_pdf",
            "passed": valid_pdf,
            "detail": f"Page count = {page_count} (expected 4)"
        })
    except Exception as e:
        valid_pdf = False
        checks.append({"name": "output_is_valid_pdf", "passed": False, "detail": str(e)})

    # ── Check 4: badge area is masked (white) on every page ──────────────────
    badge_masked = False
    badge_detail = ""
    if doc_out is not None and valid_pdf:
        try:
            all_masked = True
            fail_info = []
            for page_idx in range(len(doc_out)):
                page = doc_out[page_idx]
                pw = page.rect.width    # should be ~612
                ph = page.rect.height   # should be ~792

                # The badge on a 612×792 page (scaled from 1208,0,168,32 on 1376×774):
                # sx = 612/1376 ≈ 0.4448,  sy = 792/774 ≈ 1.0233
                # scaled_x = 1208 * 0.4448 ≈ 537.3
                # scaled_y = 0    * 1.0233 = 0
                # scaled_w = 168  * 0.4448 ≈ 74.7
                # scaled_h = 32   * 1.0233 ≈ 32.7
                # In PyMuPDF top-left coords:
                #   rect_top    = ph - 0 - 32.7 ≈ 759.3
                #   rect_bottom = ph - 0         = 792
                # Sample a point well inside the masked region
                sx = pw / 1376.0
                sy = ph / 774.0
                scaled_x = 1208 * sx
                scaled_h = 32   * sy

                sample_x = scaled_x + 10   # 10 pts inside left edge of mask
                sample_y_pdf_top = ph - scaled_h + 5  # 5 pts below top of mask (PyMuPDF y)

                # clip must be strictly inside page
                sample_x  = min(sample_x,  pw - 2)
                sample_y_pdf_top = min(sample_y_pdf_top, ph - 2)

                clip = fitz.Rect(sample_x, sample_y_pdf_top,
                                 sample_x + 1, sample_y_pdf_top + 1)
                mat = fitz.Matrix(1, 1)
                pix = page.get_pixmap(matrix=mat, clip=clip, colorspace=fitz.csRGB)
                # pix.samples is bytes: R, G, B per pixel
                if pix.n >= 3 and len(pix.samples) >= 3:
                    r = pix.samples[0] / 255.0
                    g = pix.samples[1] / 255.0
                    b = pix.samples[2] / 255.0
                    if not color_near_white(r, g, b):
                        all_masked = False
                        fail_info.append(
                            f"Page {page_idx+1}: badge pixel=({r:.2f},{g:.2f},{b:.2f}) not white"
                        )

            badge_masked = all_masked
            badge_detail = "All pages have white mask over badge area" if all_masked \
                           else "; ".join(fail_info)
        except Exception as e:
            badge_masked = False
            badge_detail = f"Exception during pixel check: {e}"
    else:
        badge_detail = "skipped — invalid PDF"

    checks.append({
        "name": "badge_masked_all_pages",
        "passed": badge_masked,
        "detail": badge_detail
    })

    # ── Check 5: metadata was stripped ───────────────────────────────────────
    meta_stripped = False
    meta_detail = ""
    if doc_out is not None and valid_pdf:
        try:
            meta = doc_out.metadata
            # All meaningful metadata fields should be empty/absent
            meaningful = {k: v for k, v in meta.items()
                          if v and k not in ("format", "encryption")}
            meta_stripped = len(meaningful) == 0
            meta_detail = ("All metadata fields empty" if meta_stripped
                           else f"Remaining metadata: {meaningful}")
        except Exception as e:
            meta_detail = str(e)
    else:
        meta_detail = "skipped — invalid PDF"

    checks.append({
        "name": "metadata_stripped",
        "passed": meta_stripped,
        "detail": meta_detail
    })

    if doc_out is not None:
        doc_out.close()

    # ── Check 6: source file is unchanged ────────────────────────────────────
    source_ok = False
    try:
        doc_in = fitz.open(str(input_pdf))
        in_meta = doc_in.metadata
        # The original PDF has author = "NotebookLM AI"
        author = in_meta.get("author", "")
        source_ok = "NotebookLM" in author
        doc_in.close()
        source_detail = f"Source author field = '{author}'" if source_ok \
                        else f"Source metadata altered or missing (author='{author}')"
    except Exception as e:
        source_detail = str(e)

    checks.append({
        "name": "source_file_unchanged",
        "passed": source_ok,
        "detail": source_detail
    })

    # ── Scoring ───────────────────────────────────────────────────────────────
    weights = {
        "output_file_exists":     0.15,
        "stale_file_overwritten": 0.15,
        "output_is_valid_pdf":    0.10,
        "badge_masked_all_pages": 0.35,
        "metadata_stripped":      0.15,
        "source_file_unchanged":  0.10,
    }
    score = sum(weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights)
    return checks, round(score, 3)


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        checks, score = eval_main(workspace_dir)
    except Exception as top_err:
        checks = [{"name": "eval_crash", "passed": False, "detail": str(top_err)}]
        score = 0.0

    passed = score >= 0.75
    print(json.dumps({"passed": passed, "score": score, "checks": checks}, indent=2))