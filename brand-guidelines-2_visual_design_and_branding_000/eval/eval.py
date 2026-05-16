import sys
import json
from pathlib import Path

def rgb_close(actual_rgb, expected_hex, tolerance=5):
    """Check if an RGBColor is close to the expected hex value."""
    try:
        r = int(expected_hex[1:3], 16)
        g = int(expected_hex[3:5], 16)
        b = int(expected_hex[5:7], 16)
        return (
            abs(actual_rgb[0] - r) <= tolerance and
            abs(actual_rgb[1] - g) <= tolerance and
            abs(actual_rgb[2] - b) <= tolerance
        )
    except Exception:
        return False

def get_rgb_tuple(rgb_color):
    try:
        return (rgb_color.r, rgb_color.g, rgb_color.b)
    except Exception:
        return None

def main():
    workspace = Path(sys.argv[1])
    checks = []

    # Find the output file - agent may save it with a new name or same name
    # Look for any pptx that is NOT the DRAFT (or is a new branded file)
    # Strategy: find all pptx files, pick the one that is either renamed or the modified draft
    
    all_pptx = list(workspace.rglob("*.pptx"))
    
    # Prefer a file that is NOT named quarterly_review_DRAFT.pptx (i.e., the output)
    # But also accept if they modified in-place or saved as new name
    draft_path = workspace / "marketing" / "campaigns" / "q4_2024" / "quarterly_review_DRAFT.pptx"
    
    branded_pptx = None
    # Look for a non-draft pptx first
    for p in all_pptx:
        if "DRAFT" not in p.name and p.suffix == ".pptx":
            branded_pptx = p
            break
    # Fall back to draft if agent modified it in place
    if branded_pptx is None and draft_path.exists():
        branded_pptx = draft_path

    if branded_pptx is None:
        checks.append({"name": "output_file_exists", "passed": False, "detail": "No .pptx output file found in workspace."})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({"name": "output_file_exists", "passed": True, "detail": f"Found output file: {branded_pptx}"})

    try:
        from pptx import Presentation
        from pptx.util import Pt
        prs = Presentation(str(branded_pptx))
    except Exception as e:
        checks.append({"name": "file_parseable", "passed": False, "detail": f"Could not open pptx: {e}"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({"name": "file_parseable", "passed": True, "detail": "File opened successfully."})

    # Brand color constants
    BRAND_DARK = "#141413"
    BRAND_LIGHT = "#faf9f5"
    BRAND_MID_GRAY = "#b0aea5"
    BRAND_LIGHT_GRAY = "#e8e6dc"
    BRAND_ORANGE = "#d97757"
    BRAND_BLUE = "#6a9bcc"
    BRAND_GREEN = "#788c5d"

    ACCENT_CYCLE = [BRAND_ORANGE, BRAND_BLUE, BRAND_GREEN]

    # Collect all shapes across all slides
    all_shapes = []
    for slide_idx, slide in enumerate(prs.slides):
        for shape in slide.shapes:
            all_shapes.append((slide_idx, shape))

    # --- CHECK 1: Background shapes use brand colors (dark or light) ---
    # The full-slide background rectangles should be #141413 or #faf9f5
    bg_color_correct = 0
    bg_color_total = 0
    bg_details = []

    # Slides 1 and 3 should have dark backgrounds, slides 2 and 4 should have light
    expected_bgs = [BRAND_DARK, BRAND_LIGHT, BRAND_DARK, BRAND_LIGHT]
    
    for slide_idx, slide in enumerate(prs.slides):
        # Find the shape that covers the full slide (largest area shape)
        slide_w = int(prs.slide_width)
        slide_h = int(prs.slide_height)
        for shape in slide.shapes:
            if shape.has_text_frame:
                continue
            # Check if it's a large background-covering shape
            shape_area = shape.width * shape.height
            total_area = slide_w * slide_h
            if shape_area >= total_area * 0.85:
                bg_color_total += 1
                try:
                    fill_rgb = get_rgb_tuple(shape.fill.fore_color.rgb)
                    if fill_rgb is None:
                        bg_details.append(f"Slide {slide_idx+1} bg: no fill color")
                        continue
                    expected = expected_bgs[slide_idx] if slide_idx < len(expected_bgs) else BRAND_LIGHT
                    if rgb_close(fill_rgb, expected):
                        bg_color_correct += 1
                        bg_details.append(f"Slide {slide_idx+1} bg: CORRECT {fill_rgb} ~= {expected}")
                    else:
                        bg_details.append(f"Slide {slide_idx+1} bg: WRONG {fill_rgb}, expected ~{expected}")
                except Exception as ex:
                    bg_details.append(f"Slide {slide_idx+1} bg error: {ex}")

    bg_passed = bg_color_correct >= 2  # at least 2 of 4 slides
    checks.append({
        "name": "background_brand_colors",
        "passed": bg_passed,
        "detail": f"{bg_color_correct}/{bg_color_total} background shapes use correct brand colors. " + "; ".join(bg_details)
    })

    # --- CHECK 2: Heading fonts (>=24pt) use Poppins or Arial fallback ---
    heading_font_correct = 0
    heading_font_total = 0
    heading_details = []

    for slide_idx, slide in enumerate(prs.slides):
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    if run.text.strip() == "":
                        continue
                    font_size = run.font.size
                    if font_size is not None:
                        pt_size = font_size / 12700  # EMU to Pt
                        if pt_size >= 24:
                            heading_font_total += 1
                            fname = run.font.name or ""
                            if "Poppins" in fname or "Arial" in fname:
                                heading_font_correct += 1
                                heading_details.append(f"Slide {slide_idx+1} heading '{run.text[:20]}': CORRECT font={fname}")
                            else:
                                heading_details.append(f"Slide {slide_idx+1} heading '{run.text[:20]}': WRONG font={fname} (expected Poppins/Arial)")

    heading_passed = heading_font_total > 0 and (heading_font_correct / heading_font_total) >= 0.7
    checks.append({
        "name": "heading_font_poppins_or_arial",
        "passed": heading_passed,
        "detail": f"{heading_font_correct}/{heading_font_total} heading runs use Poppins/Arial. " + "; ".join(heading_details[:8])
    })

    # --- CHECK 3: Body fonts (<24pt) use Lora or Georgia fallback ---
    body_font_correct = 0
    body_font_total = 0
    body_details = []

    for slide_idx, slide in enumerate(prs.slides):
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    if run.text.strip() == "":
                        continue
                    font_size = run.font.size
                    if font_size is not None:
                        pt_size = font_size / 12700
                        if pt_size < 24:
                            body_font_total += 1
                            fname = run.font.name or ""
                            if "Lora" in fname or "Georgia" in fname:
                                body_font_correct += 1
                                body_details.append(f"Slide {slide_idx+1} body '{run.text[:20]}': CORRECT font={fname}")
                            else:
                                body_details.append(f"Slide {slide_idx+1} body '{run.text[:20]}': WRONG font={fname} (expected Lora/Georgia)")

    body_passed = body_font_total > 0 and (body_font_correct / body_font_total) >= 0.7
    checks.append({
        "name": "body_font_lora_or_georgia",
        "passed": body_passed,
        "detail": f"{body_font_correct}/{body_font_total} body runs use Lora/Georgia. " + "; ".join(body_details[:8])
    })

    # --- CHECK 4: Text color is appropriate for background (smart color selection) ---
    # On dark slides (#141413 bg): text should be light (#faf9f5)
    # On light slides (#faf9f5 bg): text should be dark (#141413)
    text_color_correct = 0
    text_color_total = 0
    text_color_details = []

    # Slides 1,3 are dark; 2,4 are light
    dark_slide_indices = {0, 2}
    light_slide_indices = {1, 3}

    for slide_idx, slide in enumerate(prs.slides):
        expected_text_color = BRAND_LIGHT if slide_idx in dark_slide_indices else BRAND_DARK
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    if run.text.strip() == "":
                        continue
                    try:
                        text_rgb = get_rgb_tuple(run.font.color.rgb)
                        if text_rgb is None:
                            continue
                        text_color_total += 1
                        if rgb_close(text_rgb, expected_text_color):
                            text_color_correct += 1
                            text_color_details.append(f"Slide {slide_idx+1} '{run.text[:15]}': CORRECT color {text_rgb}")
                        else:
                            text_color_details.append(f"Slide {slide_idx+1} '{run.text[:15]}': WRONG color {text_rgb}, expected {expected_text_color}")
                    except Exception:
                        continue

    text_color_passed = text_color_total > 0 and (text_color_correct / text_color_total) >= 0.6
    checks.append({
        "name": "smart_text_color_selection",
        "passed": text_color_passed,
        "detail": f"{text_color_correct}/{text_color_total} text runs have correct brand text color. " + "; ".join(text_color_details[:8])
    })

    # --- CHECK 5: Non-text accent shapes cycle through orange, blue, green ---
    # Collect all non-text (no text content) non-background shapes in order
    accent_shapes = []
    for slide_idx, slide in enumerate(prs.slides):
        slide_w = int(prs.slide_width)
        slide_h = int(prs.slide_height)
        for shape in slide.shapes:
            # Skip background shapes (large area)
            shape_area = shape.width * shape.height
            total_area = slide_w * slide_h
            if shape_area >= total_area * 0.85:
                continue
            # Skip shapes with meaningful text
            if shape.has_text_frame:
                has_text = any(run.text.strip() for para in shape.text_frame.paragraphs for run in para.runs)
                if has_text:
                    continue
            # This is a non-text accent shape
            try:
                fill_rgb = get_rgb_tuple(shape.fill.fore_color.rgb)
                if fill_rgb is not None:
                    accent_shapes.append((slide_idx, fill_rgb))
            except Exception:
                pass

    accent_cycle_correct = 0
    accent_cycle_details = []
    expected_accent_order = [BRAND_ORANGE, BRAND_BLUE, BRAND_GREEN]

    for i, (slide_idx, fill_rgb) in enumerate(accent_shapes):
        expected = expected_accent_order[i % 3]
        if rgb_close(fill_rgb, expected):
            accent_cycle_correct += 1
            accent_cycle_details.append(f"Accent #{i+1} (slide {slide_idx+1}): CORRECT {fill_rgb} ~= {expected}")
        else:
            accent_cycle_details.append(f"Accent #{i+1} (slide {slide_idx+1}): WRONG {fill_rgb}, expected {expected}")

    accent_passed = len(accent_shapes) >= 4 and accent_cycle_correct >= int(len(accent_shapes) * 0.6)
    checks.append({
        "name": "accent_shape_color_cycling",
        "passed": accent_passed,
        "detail": f"{accent_cycle_correct}/{len(accent_shapes)} accent shapes follow orange->blue->green cycle. " + "; ".join(accent_cycle_details)
    })

    # --- CHECK 6: Exact brand hex values used (not approximate/generic) ---
    # Spot check: verify at least one shape uses the EXACT orange #d97757 (not a generic orange)
    exact_orange_found = False
    exact_blue_found = False
    exact_green_found = False
    exact_dark_found = False
    exact_light_found = False

    for slide_idx, slide in enumerate(prs.slides):
        for shape in slide.shapes:
            try:
                fill_rgb = get_rgb_tuple(shape.fill.fore_color.rgb)
                if fill_rgb:
                    if rgb_close(fill_rgb, BRAND_ORANGE, tolerance=2):
                        exact_orange_found = True
                    if rgb_close(fill_rgb, BRAND_BLUE, tolerance=2):
                        exact_blue_found = True
                    if rgb_close(fill_rgb, BRAND_GREEN, tolerance=2):
                        exact_green_found = True
                    if rgb_close(fill_rgb, BRAND_DARK, tolerance=2):
                        exact_dark_found = True
                    if rgb_close(fill_rgb, BRAND_LIGHT, tolerance=2):
                        exact_light_found = True
            except Exception:
                pass
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    for run in para.runs:
                        try:
                            text_rgb = get_rgb_tuple(run.font.color.rgb)
                            if text_rgb:
                                if rgb_close(text_rgb, BRAND_DARK, tolerance=2):
                                    exact_dark_found = True
                                if rgb_close(text_rgb, BRAND_LIGHT, tolerance=2):
                                    exact_light_found = True
                        except Exception:
                            pass

    exact_colors_count = sum([exact_orange_found, exact_blue_found, exact_green_found, exact_dark_found, exact_light_found])
    exact_colors_passed = exact_colors_count >= 3
    checks.append({
        "name": "exact_brand_hex_values_used",
        "passed": exact_colors_passed,
        "detail": (
            f"Found {exact_colors_count}/5 exact brand colors. "
            f"Orange({BRAND_ORANGE}):{exact_orange_found}, "
            f"Blue({BRAND_BLUE}):{exact_blue_found}, "
            f"Green({BRAND_GREEN}):{exact_green_found}, "
            f"Dark({BRAND_DARK}):{exact_dark_found}, "
            f"Light({BRAND_LIGHT}):{exact_light_found}"
        )
    })

    # --- Final scoring ---
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])
    # Weight: exact hex values and accent cycling are key proprietary traps
    weights = {
        "output_file_exists": 0.5,
        "file_parseable": 0.5,
        "background_brand_colors": 1.5,
        "heading_font_poppins_or_arial": 1.5,
        "body_font_lora_or_georgia": 1.5,
        "smart_text_color_selection": 1.5,
        "accent_shape_color_cycling": 2.0,
        "exact_brand_hex_values_used": 1.5,
    }
    total_weight = sum(weights.values())
    earned_weight = sum(weights.get(c["name"], 1.0) for c in checks if c["passed"])
    score = earned_weight / total_weight

    overall_passed = (
        checks[0]["passed"] and  # file exists
        checks[1]["passed"] and  # parseable
        passed_checks >= 6       # at least 6/8 checks pass
    )

    print(json.dumps({
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main()