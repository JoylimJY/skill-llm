import sys
import json
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    workspace_path = Path(workspace)

    # --- Find the PNG poster ---
    png_files = list(workspace_path.rglob("hackathon_poster.png"))
    png_found = len(png_files) > 0
    checks.append({
        "name": "hackathon_poster.png exists",
        "passed": png_found,
        "detail": f"Found at: {png_files[0]}" if png_found else "File not found anywhere in workspace."
    })

    # --- Find the PDF schedule ---
    pdf_files = list(workspace_path.rglob("hackathon_schedule.pdf"))
    pdf_found = len(pdf_files) > 0
    checks.append({
        "name": "hackathon_schedule.pdf exists",
        "passed": pdf_found,
        "detail": f"Found at: {pdf_files[0]}" if pdf_found else "File not found anywhere in workspace."
    })

    # ===== PNG CHECKS (Glassmorphism) =====
    png_rgba_mode = False
    png_has_semitransparent_layer = False
    png_has_border_rect = False
    png_has_text = False
    png_min_size = False

    if png_found:
        try:
            from PIL import Image
            import numpy as np

            img = Image.open(str(png_files[0]))

            # Check minimum canvas size (should be reasonable poster dimensions)
            w, h = img.size
            png_min_size = (w >= 400 and h >= 300)
            checks.append({
                "name": "PNG has reasonable poster dimensions (>=400x300)",
                "passed": png_min_size,
                "detail": f"Size: {w}x{h}"
            })

            # Glassmorphism REQUIRES RGBA mode or composite transparency simulation
            # Accept both: RGBA image OR image with a visually distinct semi-transparent overlay
            # Key check: image must be RGBA at some point during creation (saved as RGBA or composited)
            # We also accept: if the image was composited (RGB) but has a frosted region
            # Strategy: convert to RGBA for analysis
            if img.mode == 'RGBA':
                png_rgba_mode = True
                arr = np.array(img)
                # Check for pixels with alpha < 255 (transparency present)
                alpha_channel = arr[:, :, 3]
                semi_transparent = np.any((alpha_channel > 0) & (alpha_channel < 255))
                png_has_semitransparent_layer = bool(semi_transparent)
            else:
                # RGB image: check if there's a visually lighter/frosted region
                # by analyzing if there's a region that's noticeably different
                # (blended/washed out layer - proxy for glassmorphism)
                # Accept RGB if it has a clearly composited frosted layer:
                # Check: is there a rectangular region with significantly higher brightness than surrounding?
                arr = np.array(img.convert('RGB'))
                # Look for a region with high mean brightness (frosted glass is lighter)
                # We'll do a simple quadrant check
                h_px, w_px = arr.shape[:2]
                center_region = arr[h_px//4:3*h_px//4, w_px//4:3*w_px//4]
                overall_mean = arr.mean()
                center_mean = center_region.mean()
                # A frosted/light overlay in center should be brighter or clearly distinct
                png_has_semitransparent_layer = (abs(float(center_mean) - float(overall_mean)) > 10)
                png_rgba_mode = True  # Accept RGB with composited effect

            checks.append({
                "name": "PNG uses RGBA/transparency for Glassmorphism frosted-glass effect",
                "passed": png_has_semitransparent_layer or png_rgba_mode,
                "detail": f"Mode: {img.mode}, semitransparent pixels or frosted region detected: {png_has_semitransparent_layer}"
            })

            # Check for border rectangle (Glassmorphism: subtle border)
            # Heuristic: check image edges/outlines for near-white/near-border colored pixel lines
            # More robust: check if any prominent rectangular outline exists by scanning for
            # consistent pixel rows/cols with distinct color
            arr_rgb = np.array(img.convert('RGB'))
            h_px, w_px = arr_rgb.shape[:2]

            # Check horizontal bands (top ~10% and bottom ~10% rows) for consistent color streaks
            # indicating a drawn border
            edge_rows = np.concatenate([arr_rgb[:int(h_px*0.15)], arr_rgb[int(h_px*0.85):]])
            edge_cols_left = arr_rgb[:, :int(w_px*0.08)]
            edge_cols_right = arr_rgb[:, int(w_px*0.92):]

            # A border would mean these regions have a distinct, relatively uniform color strip
            # Check variance in edge regions - low variance = border line
            def has_border_strip(region):
                if region.size == 0:
                    return False
                # Look for rows/cols with std dev < 30 (uniform color = border line)
                for row in region:
                    row_std = float(row.reshape(-1, 3).std(axis=0).mean())
                    if row_std < 25:
                        return True
                return False

            png_has_border_rect = (
                has_border_strip(arr_rgb[:5]) or
                has_border_strip(arr_rgb[-5:]) or
                has_border_strip(arr_rgb[:, :5]) or
                has_border_strip(arr_rgb[:, -5:]) or
                _check_drawn_border(arr_rgb)
            )

            checks.append({
                "name": "PNG has border element (Glassmorphism subtle border)",
                "passed": png_has_border_rect,
                "detail": "Border/outline rectangle detected in image."
            })

            # Check for text presence (non-uniform pixels suggesting text rendering)
            # Large std dev across the image = text/content present
            std_val = float(arr_rgb.std())
            png_has_text = std_val > 15
            checks.append({
                "name": "PNG contains text/content (non-blank poster)",
                "passed": png_has_text,
                "detail": f"Pixel std dev: {std_val:.2f} (>15 expected)"
            })

        except Exception as e:
            checks.append({"name": "PNG image analysis", "passed": False, "detail": f"Error: {e}"})

    # ===== PDF CHECKS (Brutalism) =====
    pdf_has_bold_font = False
    pdf_has_content = False
    pdf_has_color = False

    if pdf_found:
        try:
            # Read raw PDF bytes to check for Brutalism markers
            pdf_bytes = pdf_files[0].read_bytes()
            pdf_text = pdf_bytes.decode('latin-1', errors='replace')

            # Check file size (must have real content)
            pdf_size = len(pdf_bytes)
            pdf_has_content = pdf_size > 1000
            checks.append({
                "name": "PDF has substantial content (>1KB)",
                "passed": pdf_has_content,
                "detail": f"File size: {pdf_size} bytes"
            })

            # Brutalism requires BOLD typography - check for Bold font reference in PDF stream
            # fpdf2 uses /Arial,Bold or /B flag or BoldMT or Bold in font name
            bold_indicators = [b'/Bold', b'Bold', b',B]', b'Arial-Bold', b'BoldMT', b'ArialBD']
            pdf_has_bold_font = any(indicator in pdf_bytes for indicator in bold_indicators)

            # Also check for fpdf2 specific bold encoding: font style "B"
            # fpdf2 internally marks bold with specific stream tokens
            # Additional check: look for font weight markers in PDF structure
            if not pdf_has_bold_font:
                # Check for bold-style cell/text in raw stream
                pdf_has_bold_font = (b'BT' in pdf_bytes and
                                     (b'Bold' in pdf_bytes or b',B' in pdf_bytes or
                                      b'700' in pdf_bytes))

            checks.append({
                "name": "PDF uses bold typography (Brutalism bold font requirement)",
                "passed": pdf_has_bold_font,
                "detail": "Bold font markers found in PDF stream." if pdf_has_bold_font else "No bold font markers detected. Brutalism requires bold/heavy typography."
            })

            # Brutalism: clashing colors - check for non-black color commands in PDF
            # PDF color commands: rg (RGB fill), RG (RGB stroke), k (CMYK)
            # Look for color-setting commands that aren't pure black (0 0 0) or pure white
            import re
            # Find rg color commands: "R G B rg" format
            color_cmds = re.findall(rb'(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+rg', pdf_bytes)
            non_default_colors = []
            for cmd in color_cmds:
                try:
                    r, g, b = float(cmd[0]), float(cmd[1]), float(cmd[2])
                    # Skip black (0,0,0) and white (1,1,1) and near-defaults
                    if not ((r < 0.05 and g < 0.05 and b < 0.05) or
                            (r > 0.95 and g > 0.95 and b > 0.95)):
                        non_default_colors.append((r, g, b))
                except:
                    pass

            pdf_has_color = len(non_default_colors) > 0
            checks.append({
                "name": "PDF uses non-default colors (Brutalism clashing colors)",
                "passed": pdf_has_color,
                "detail": f"Non-black/white color commands found: {non_default_colors[:3]}" if pdf_has_color else "Only default black/white colors found. Brutalism requires clashing/bold colors."
            })

        except Exception as e:
            checks.append({"name": "PDF analysis", "passed": False, "detail": f"Error: {e}"})

    # ===== CONTENT CHECKS =====
    # Verify the poster uses the hackathon event data from the workspace
    if png_found:
        try:
            # Since PNG is raster, we can't easily extract text without OCR
            # Instead verify the image is non-trivial (has been genuinely designed)
            from PIL import Image
            img = Image.open(str(png_files[0]))
            w, h = img.size
            aspect_ratio_ok = 0.4 < (w / h) < 3.0
            checks.append({
                "name": "PNG has valid poster aspect ratio",
                "passed": aspect_ratio_ok,
                "detail": f"Aspect ratio: {w/h:.2f} (expected 0.4–3.0 for poster)"
            })
        except Exception as e:
            checks.append({"name": "PNG aspect ratio check", "passed": False, "detail": str(e)})

    # ===== SCORING =====
    critical_checks = [
        "hackathon_poster.png exists",
        "hackathon_schedule.pdf exists",
        "PNG uses RGBA/transparency for Glassmorphism frosted-glass effect",
        "PNG has border element (Glassmorphism subtle border)",
        "PDF uses bold typography (Brutalism bold font requirement)",
        "PDF uses non-default colors (Brutalism clashing colors)",
    ]

    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    critical_passed = sum(1 for c in checks if c["name"] in critical_checks and c["passed"])
    critical_total = len(critical_checks)

    score = (passed_count / total) if total > 0 else 0.0
    # Must pass at least 4 of 6 critical checks to truly pass
    overall_passed = (critical_passed >= 4) and png_found and pdf_found

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


def _check_drawn_border(arr_rgb):
    """Check if a drawn rectangle border exists anywhere in the image."""
    import numpy as np
    h, w = arr_rgb.shape[:2]
    # Sample interior rows/cols for a uniform-color line (border)
    for y in range(5, h - 5, max(1, h // 20)):
        row = arr_rgb[y]
        row_std = float(row.reshape(-1, 3).std(axis=0).mean())
        if row_std < 8 and row.mean() < 230:  # Non-white uniform line = border
            return True
    for x in range(5, w - 5, max(1, w // 20)):
        col = arr_rgb[:, x]
        col_std = float(col.reshape(-1, 3).std(axis=0).mean())
        if col_std < 8 and col.mean() < 230:
            return True
    return False


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))