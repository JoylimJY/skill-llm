import sys
import json
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def main():
    workspace = Path(sys.argv[1])
    checks = []
    total = 0
    passed_count = 0

    # Brand colors from SKILL.md
    DARK         = (0x14, 0x14, 0x13)
    LIGHT        = (0xfa, 0xf9, 0xf5)
    MID_GRAY     = (0xb0, 0xae, 0xa5)
    LIGHT_GRAY   = (0xe8, 0xe6, 0xdc)
    ORANGE       = (0xd9, 0x77, 0x57)
    BLUE         = (0x6a, 0x9b, 0xcc)
    GREEN        = (0x78, 0x8c, 0x5d)

    ACCENT_CYCLE = [ORANGE, BLUE, GREEN]

    HEADINGS_FONTS = {"poppins", "arial"}
    BODY_FONTS     = {"lora", "georgia"}

    def rgb_close(actual, expected, tol=5):
        return all(abs(a - e) <= tol for a, e in zip(actual, expected))

    def rgb_is_brand_color(rgb_tuple):
        brand_colors = [DARK, LIGHT, MID_GRAY, LIGHT_GRAY, ORANGE, BLUE, GREEN]
        return any(rgb_close(rgb_tuple, bc) for bc in brand_colors)

    try:
        from pptx import Presentation
        from pptx.util import Pt
        from pptx.dml.color import RGBColor
        from pptx.enum.shapes import MSO_SHAPE_TYPE
    except ImportError as e:
        print(json.dumps({"passed": False, "score": 0.0,
            "checks": [check("import_pptx", False, str(e))]}))
        return

    # ─── Find branded output file ─────────────────────────────────────────────
    # Look for any branded/output pptx that is NOT the raw drafts
    raw_names = {"investor_pitch_raw.pptx", "product_overview_raw.pptx"}
    all_pptx = list(workspace.rglob("*.pptx"))
    branded_files = [f for f in all_pptx if f.name not in raw_names]

    if not branded_files:
        checks.append(check("branded_file_exists", False,
            f"No branded .pptx found. Only raw drafts present: {[f.name for f in all_pptx]}"))
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # Use the largest branded file (most likely the main pitch deck)
    target = max(branded_files, key=lambda f: f.stat().st_size)
    checks.append(check("branded_file_exists", True, f"Found branded file: {target}"))

    try:
        prs = Presentation(str(target))
    except Exception as e:
        checks.append(check("pptx_valid", False, f"Could not open file: {e}"))
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append(check("pptx_valid", True, "Presentation opened successfully"))

    slides = prs.slides
    if len(slides) == 0:
        checks.append(check("has_slides", False, "No slides found"))
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # ─── Check 1: Background colors are brand colors ──────────────────────────
    bg_colors_ok = []
    bg_details = []
    for i, slide in enumerate(slides):
        try:
            bg = slide.background
            fill = bg.fill
            if fill.type is not None:
                rgb = fill.fore_color.rgb
                rgb_t = (rgb.red, rgb.green, rgb.blue)
                is_brand = rgb_is_brand_color(rgb_t)
                bg_colors_ok.append(is_brand)
                bg_details.append(f"Slide {i+1} bg: #{rgb.red:02x}{rgb.green:02x}{rgb.blue:02x} brand={is_brand}")
            else:
                bg_colors_ok.append(False)
                bg_details.append(f"Slide {i+1}: no fill set")
        except Exception as e:
            bg_colors_ok.append(False)
            bg_details.append(f"Slide {i+1} error: {e}")

    bg_pass = sum(bg_colors_ok) >= max(1, len(slides) * 0.75)
    checks.append(check("background_colors_brand",
        bg_pass,
        "; ".join(bg_details)))

    # ─── Check 2: Heading fonts (≥24pt) use Poppins or Arial ─────────────────
    heading_font_results = []
    heading_font_details = []
    for i, slide in enumerate(slides):
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    if run.font.size is not None:
                        pt_size = run.font.size.pt
                        font_name = (run.font.name or "").lower().strip()
                        if pt_size >= 24:
                            ok = any(hf in font_name for hf in HEADINGS_FONTS)
                            heading_font_results.append(ok)
                            heading_font_details.append(
                                f"Slide {i+1} heading run '{run.text[:20]}' "
                                f"size={pt_size}pt font='{run.font.name}' ok={ok}"
                            )

    if heading_font_results:
        hf_pass = sum(heading_font_results) / len(heading_font_results) >= 0.75
        checks.append(check("heading_font_poppins_arial",
            hf_pass,
            f"{sum(heading_font_results)}/{len(heading_font_results)} headings correct. " +
            "; ".join(heading_font_details[:6])))
    else:
        checks.append(check("heading_font_poppins_arial", False,
            "No heading runs with font size ≥24pt found"))

    # ─── Check 3: Body text (<24pt) uses Lora or Georgia ─────────────────────
    body_font_results = []
    body_font_details = []
    for i, slide in enumerate(slides):
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    if run.font.size is not None and run.text.strip():
                        pt_size = run.font.size.pt
                        font_name = (run.font.name or "").lower().strip()
                        if pt_size < 24:
                            ok = any(bf in font_name for bf in BODY_FONTS)
                            body_font_results.append(ok)
                            body_font_details.append(
                                f"Slide {i+1} body run '{run.text[:20]}' "
                                f"size={pt_size}pt font='{run.font.name}' ok={ok}"
                            )

    if body_font_results:
        bf_pass = sum(body_font_results) / len(body_font_results) >= 0.75
        checks.append(check("body_font_lora_georgia",
            bf_pass,
            f"{sum(body_font_results)}/{len(body_font_results)} body runs correct. " +
            "; ".join(body_font_details[:6])))
    else:
        checks.append(check("body_font_lora_georgia", False,
            "No body text runs with font size <24pt found"))

    # ─── Check 4: Text colors are brand colors ────────────────────────────────
    text_color_results = []
    text_color_details = []
    for i, slide in enumerate(slides):
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    if not run.text.strip():
                        continue
                    try:
                        rgb = run.font.color.rgb
                        rgb_t = (rgb.red, rgb.green, rgb.blue)
                        ok = rgb_is_brand_color(rgb_t)
                        text_color_results.append(ok)
                        text_color_details.append(
                            f"Slide {i+1} '{run.text[:20]}': "
                            f"#{rgb.red:02x}{rgb.green:02x}{rgb.blue:02x} ok={ok}"
                        )
                    except Exception:
                        pass

    if text_color_results:
        tc_pass = sum(text_color_results) / len(text_color_results) >= 0.75
        checks.append(check("text_colors_brand",
            tc_pass,
            f"{sum(text_color_results)}/{len(text_color_results)} text runs with brand colors. " +
            "; ".join(text_color_details[:6])))
    else:
        checks.append(check("text_colors_brand", False, "No text runs with color found"))

    # ─── Check 5: Non-text shapes use accent colors cycling O→B→G ────────────
    accent_colors_found = []
    accent_details = []
    shape_count = 0
    for i, slide in enumerate(slides):
        for shape in slide.shapes:
            if shape.has_text_frame:
                continue
            try:
                if shape.fill.type is not None:
                    rgb = shape.fill.fore_color.rgb
                    rgb_t = (rgb.red, rgb.green, rgb.blue)
                    accent_colors_found.append(rgb_t)
                    shape_count += 1
                    accent_details.append(
                        f"Slide {i+1} shape: #{rgb.red:02x}{rgb.green:02x}{rgb.blue:02x}"
                    )
            except Exception as e:
                accent_details.append(f"Slide {i+1} shape error: {e}")

    # Check that accent colors are drawn from the brand accent palette
    accent_brand_ok = []
    for rgb_t in accent_colors_found:
        is_accent = any(rgb_close(rgb_t, ac) for ac in ACCENT_CYCLE)
        accent_brand_ok.append(is_accent)

    # Check cycling order: the sequence found should follow O→B→G
    cycling_ok = False
    if len(accent_colors_found) >= 3:
        # Build the sequence of which accent index each shape maps to
        seq = []
        for rgb_t in accent_colors_found:
            for j, ac in enumerate(ACCENT_CYCLE):
                if rgb_close(rgb_t, ac):
                    seq.append(j)
                    break
        # Verify the sequence cycles: 0,1,2,0,1,2,...
        if seq:
            cycling_ok = all(seq[k] == k % 3 for k in range(len(seq)))

    if accent_colors_found:
        brand_acc_frac = sum(accent_brand_ok) / len(accent_brand_ok)
        a_pass = brand_acc_frac >= 0.75
        checks.append(check("accent_shapes_brand_colors",
            a_pass,
            f"{sum(accent_brand_ok)}/{len(accent_brand_ok)} shapes use brand accent colors. " +
            "; ".join(accent_details[:8])))
        checks.append(check("accent_cycling_order",
            cycling_ok,
            f"Cycling check: seq={seq if 'seq' in dir() else 'n/a'}, cycling_ok={cycling_ok}"))
    else:
        checks.append(check("accent_shapes_brand_colors", False,
            f"No non-text shapes with fills found (shape_count={shape_count}). Details: {accent_details}"))
        checks.append(check("accent_cycling_order", False, "No shapes to check cycling"))

    # ─── Check 6: Exact brand hex values used (spot-check key colors) ─────────
    # At least one occurrence of ORANGE #d97757 and DARK #141413 must be present
    orange_found = any(rgb_close(c, ORANGE) for c in accent_colors_found)
    dark_found = False
    light_found = False
    for i, slide in enumerate(slides):
        try:
            bg = slide.background
            fill = bg.fill
            if fill.type is not None:
                rgb = fill.fore_color.rgb
                rgb_t = (rgb.red, rgb.green, rgb.blue)
                if rgb_close(rgb_t, DARK):
                    dark_found = True
                if rgb_close(rgb_t, LIGHT):
                    light_found = True
        except Exception:
            pass

    checks.append(check("exact_dark_color_used", dark_found,
        f"Brand dark #141413 found in slide backgrounds: {dark_found}"))
    checks.append(check("exact_light_color_used", light_found,
        f"Brand light #faf9f5 found in slide backgrounds: {light_found}"))
    checks.append(check("exact_orange_accent_used", orange_found,
        f"Brand orange #d97757 found in shapes: {orange_found}"))

    # ─── Compute final score ──────────────────────────────────────────────────
    critical_checks = [
        "branded_file_exists",
        "pptx_valid",
        "background_colors_brand",
        "heading_font_poppins_arial",
        "body_font_lora_georgia",
        "text_colors_brand",
        "accent_shapes_brand_colors",
        "exact_dark_color_used",
        "exact_light_color_used",
        "exact_orange_accent_used",
    ]

    passed_names = {c["name"] for c in checks if c["passed"]}
    total_checks = len(checks)
    passed_total = len(passed_names)
    score = passed_total / total_checks

    overall_passed = all(
        c["name"] in passed_names
        for c in checks
        if c["name"] in [
            "branded_file_exists",
            "pptx_valid",
            "background_colors_brand",
            "heading_font_poppins_arial",
            "body_font_lora_georgia",
            "accent_shapes_brand_colors",
        ]
    )

    print(json.dumps({
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main()