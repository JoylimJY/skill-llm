import sys
import json
import traceback
from pathlib import Path

def rgb_close(actual_rgb, expected_hex, tolerance=2):
    """Check if an RGBColor is close to an expected hex value."""
    try:
        r = int(expected_hex[0:2], 16)
        g = int(expected_hex[2:4], 16)
        b = int(expected_hex[4:6], 16)
        return (abs(actual_rgb[0] - r) <= tolerance and
                abs(actual_rgb[1] - g) <= tolerance and
                abs(actual_rgb[2] - b) <= tolerance)
    except Exception:
        return False

def get_rgb_tuple(color_obj):
    try:
        rgb = color_obj.rgb
        return (rgb.red, rgb.green, rgb.blue)
    except Exception:
        return None

def run_eval(workspace_dir):
    checks = []

    # ---- Locate the output file ----
    workspace = Path(workspace_dir)
    
    # Look for branded output - agent should produce a new branded file
    # It could be named anything branded, search broadly but prefer specific names
    candidates = list(workspace.rglob("board_pitch_branded.pptx")) + \
                 list(workspace.rglob("*branded*.pptx")) + \
                 list(workspace.rglob("*brand*.pptx")) + \
                 list(workspace.rglob("*anthropic*.pptx"))
    
    # Also check if the draft was modified in-place (less ideal but acceptable)
    draft_path = workspace / "presentations" / "drafts" / "board_pitch_draft.pptx"
    
    pptx_path = None
    if candidates:
        pptx_path = candidates[0]
    elif draft_path.exists():
        pptx_path = draft_path
    
    if pptx_path is None:
        checks.append({"name": "output_file_exists", "passed": False,
                        "detail": "No branded .pptx file found in workspace."})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "output_file_exists", "passed": True,
                    "detail": f"Found output file: {pptx_path}"})

    try:
        from pptx import Presentation
        from pptx.util import Pt
        prs = Presentation(str(pptx_path))
    except Exception as e:
        checks.append({"name": "file_parseable", "passed": False,
                        "detail": f"Failed to parse pptx: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "file_parseable", "passed": True, "detail": "PPTX parsed successfully."})

    # Brand colors
    DARK       = "141413"
    LIGHT      = "faf9f5"
    MID_GRAY   = "b0aea5"
    LIGHT_GRAY = "e8e6dc"
    ORANGE     = "d97757"
    BLUE       = "6a9bcc"
    GREEN      = "788c5d"
    ACCENT_CYCLE = [ORANGE, BLUE, GREEN]

    # ---- CHECK 1: Heading fonts (24pt+) should be Poppins or Arial fallback ----
    heading_font_ok = True
    heading_font_details = []
    body_font_ok = True
    body_font_details = []

    for slide_idx, slide in enumerate(prs.slides):
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    if not run.text.strip():
                        continue
                    font_size_pt = run.font.size.pt if run.font.size else None
                    font_name = run.font.name or ""
                    
                    if font_size_pt is not None and font_size_pt >= 24:
                        # Heading: must be Poppins or Arial
                        valid_heading = ("Poppins" in font_name or "Arial" in font_name)
                        if not valid_heading:
                            heading_font_ok = False
                            heading_font_details.append(
                                f"Slide {slide_idx+1}: '{run.text[:30]}' at {font_size_pt}pt has font '{font_name}' (expected Poppins/Arial)"
                            )
                    elif font_size_pt is not None and font_size_pt < 24:
                        # Body: must be Lora or Georgia
                        valid_body = ("Lora" in font_name or "Georgia" in font_name)
                        if not valid_body:
                            body_font_ok = False
                            body_font_details.append(
                                f"Slide {slide_idx+1}: '{run.text[:30]}' at {font_size_pt}pt has font '{font_name}' (expected Lora/Georgia)"
                            )

    checks.append({
        "name": "heading_font_poppins_or_arial",
        "passed": heading_font_ok,
        "detail": "All 24pt+ text uses Poppins/Arial" if heading_font_ok else "; ".join(heading_font_details[:5])
    })

    checks.append({
        "name": "body_font_lora_or_georgia",
        "passed": body_font_ok,
        "detail": "All sub-24pt text uses Lora/Georgia" if body_font_ok else "; ".join(body_font_details[:5])
    })

    # ---- CHECK 2: Exactly-24pt text is treated as heading (Poppins/Arial) ----
    # Slide 3 has a 24pt heading "Key Performance Metrics"
    boundary_ok = False
    boundary_detail = "24pt boundary heading not found or wrong font"
    for slide_idx, slide in enumerate(prs.slides):
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    if run.font.size and abs(run.font.size.pt - 24) < 0.5:
                        fname = run.font.name or ""
                        if "Poppins" in fname or "Arial" in fname:
                            boundary_ok = True
                            boundary_detail = f"24pt text '{run.text[:30]}' correctly uses {fname}"
    checks.append({
        "name": "boundary_24pt_treated_as_heading",
        "passed": boundary_ok,
        "detail": boundary_detail
    })

    # ---- CHECK 3: Non-text shapes use accent colors cycling orange->blue->green ----
    non_text_shapes_colors = []
    for slide_idx, slide in enumerate(prs.slides):
        for shape in slide.shapes:
            if shape.has_text_frame:
                continue
            try:
                fill = shape.fill
                if fill.type is not None:
                    color_tuple = get_rgb_tuple(fill.fore_color)
                    if color_tuple:
                        non_text_shapes_colors.append((slide_idx+1, shape.name, color_tuple))
            except Exception:
                pass

    accent_cycle_ok = False
    accent_detail = f"Found {len(non_text_shapes_colors)} non-text shapes with fill colors."
    
    if len(non_text_shapes_colors) >= 2:
        # Check that each non-text shape's color matches an accent color (cycling)
        mismatches = []
        for i, (snum, sname, crgb) in enumerate(non_text_shapes_colors):
            expected_accent = ACCENT_CYCLE[i % 3]
            if not rgb_close(crgb, expected_accent):
                # Check if any accent color matches (some shapes may be backgrounds)
                is_any_accent = any(rgb_close(crgb, a) for a in ACCENT_CYCLE)
                is_brand_bg = rgb_close(crgb, DARK) or rgb_close(crgb, LIGHT) or \
                              rgb_close(crgb, LIGHT_GRAY) or rgb_close(crgb, MID_GRAY)
                if not is_any_accent and not is_brand_bg:
                    mismatches.append(f"Slide {snum} shape '{sname}': rgb{crgb} not a brand color")
        
        if len(mismatches) == 0:
            accent_cycle_ok = True
            accent_detail = f"All {len(non_text_shapes_colors)} non-text shapes use brand colors."
        else:
            accent_detail = "Non-brand colors found: " + "; ".join(mismatches[:4])
    elif len(non_text_shapes_colors) == 0:
        accent_detail = "No non-text shapes with fill found — shapes may have been removed or colors can't be read."
        accent_cycle_ok = False
    
    checks.append({
        "name": "non_text_shapes_use_accent_colors",
        "passed": accent_cycle_ok,
        "detail": accent_detail
    })

    # ---- CHECK 4: Text colors use brand palette (dark or light) ----
    text_color_ok = True
    text_color_details = []
    VALID_TEXT_COLORS = [DARK, LIGHT, MID_GRAY, LIGHT_GRAY, ORANGE, BLUE, GREEN]

    for slide_idx, slide in enumerate(prs.slides):
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    if not run.text.strip():
                        continue
                    try:
                        color_tuple = get_rgb_tuple(run.font.color)
                        if color_tuple is None:
                            continue
                        is_valid = any(rgb_close(color_tuple, c) for c in VALID_TEXT_COLORS)
                        if not is_valid:
                            text_color_ok = False
                            text_color_details.append(
                                f"Slide {slide_idx+1}: '{run.text[:25]}' color rgb{color_tuple} not in brand palette"
                            )
                    except Exception:
                        pass

    checks.append({
        "name": "text_uses_brand_colors",
        "passed": text_color_ok,
        "detail": "All text uses brand palette" if text_color_ok else "; ".join(text_color_details[:5])
    })

    # ---- CHECK 5: Smart color — dark background -> light text (#faf9f5) ----
    # Slide 1 has a dark background; title text should be light (#faf9f5)
    smart_color_ok = False
    smart_color_detail = "Could not verify smart color selection for dark backgrounds."
    
    slide1 = prs.slides[0]
    dark_bg_detected = False
    light_text_on_dark = False
    
    for shape in slide1.shapes:
        if not shape.has_text_frame:
            try:
                color_t = get_rgb_tuple(shape.fill.fore_color)
                if color_t and rgb_close(color_t, DARK):
                    dark_bg_detected = True
            except Exception:
                pass
    
    if dark_bg_detected:
        for shape in slide1.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    for run in para.runs:
                        if run.text.strip():
                            try:
                                c = get_rgb_tuple(run.font.color)
                                if c and rgb_close(c, LIGHT):
                                    light_text_on_dark = True
                            except Exception:
                                pass
        if light_text_on_dark:
            smart_color_ok = True
            smart_color_detail = "Dark background detected; title/body text correctly uses light color (#faf9f5)."
        else:
            smart_color_detail = "Dark background detected but text is not using light brand color (#faf9f5)."
    else:
        # If background was recolored to brand dark, check again
        for shape in slide1.shapes:
            if not shape.has_text_frame:
                try:
                    color_t = get_rgb_tuple(shape.fill.fore_color)
                    if color_t and (color_t[0] < 40 and color_t[1] < 40 and color_t[2] < 40):
                        dark_bg_detected = True
                except Exception:
                    pass
        if dark_bg_detected:
            for shape in slide1.shapes:
                if shape.has_text_frame:
                    for para in shape.text_frame.paragraphs:
                        for run in para.runs:
                            if run.text.strip():
                                try:
                                    c = get_rgb_tuple(run.font.color)
                                    if c and rgb_close(c, LIGHT):
                                        light_text_on_dark = True
                                except Exception:
                                    pass
            smart_color_ok = light_text_on_dark
            smart_color_detail = (
                "Smart color check: " + ("Light text on dark bg ✓" if light_text_on_dark else "Text not using #faf9f5 on dark bg ✗")
            )

    checks.append({
        "name": "smart_color_dark_bg_light_text",
        "passed": smart_color_ok,
        "detail": smart_color_detail
    })

    # ---- FINAL SCORE ----
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks

    # Must pass core checks to overall pass: file exists, parseable, heading font, body font, text brand colors
    core_passed = all(
        c["passed"] for c in checks
        if c["name"] in ("output_file_exists", "file_parseable", "heading_font_poppins_or_arial",
                         "body_font_lora_or_georgia", "text_uses_brand_colors")
    )

    return {
        "passed": core_passed and score >= 0.75,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        result = run_eval(workspace_dir)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crashed", "passed": False, "detail": traceback.format_exc()}]
        }
    print(json.dumps(result, indent=2))