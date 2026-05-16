#!/usr/bin/env python3
"""
Evaluation script for the CI/CD Pipeline Flowchart task.
Checks the agent's .excalidraw JSON and rendered PNG.
"""

import sys
import json
import os
from pathlib import Path

def find_file(workspace, pattern):
    results = list(Path(workspace).rglob(pattern))
    return results[0] if results else None

def load_excalidraw(path):
    with open(path, 'r') as f:
        return json.load(f)

def run_eval(workspace):
    checks = []
    total_score = 0.0
    max_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        nonlocal total_score, max_score
        max_score += weight
        if passed:
            total_score += weight

    # ── 1. Find the excalidraw file ──────────────────────────────────────────
    excalidraw_file = find_file(workspace, "ci_cd_pipeline.excalidraw")
    if not excalidraw_file:
        excalidraw_file = find_file(workspace, "ci-cd-pipeline.excalidraw")
    if not excalidraw_file:
        excalidraw_file = find_file(workspace, "pipeline.excalidraw")
    if not excalidraw_file:
        # Search for any .excalidraw file NOT in the old diagrams distractor
        candidates = [p for p in Path(workspace).rglob("*.excalidraw")
                      if "old" not in str(p) and "v1" not in str(p).lower()]
        excalidraw_file = candidates[0] if candidates else None

    add_check(
        "excalidraw_file_exists",
        excalidraw_file is not None,
        f"Found: {excalidraw_file}" if excalidraw_file else "No .excalidraw file found in workspace",
        weight=1.0
    )

    if excalidraw_file is None:
        # Cannot proceed
        add_check("png_file_exists", False, "Cannot check PNG without excalidraw file", weight=1.0)
        return finalize(checks, total_score, max_score)

    # ── 2. Parse the excalidraw JSON ─────────────────────────────────────────
    try:
        data = load_excalidraw(excalidraw_file)
        elements = data.get("elements", [])
        add_check(
            "valid_excalidraw_json",
            isinstance(elements, list) and len(elements) > 0,
            f"Parsed {len(elements)} elements from {excalidraw_file.name}",
            weight=1.0
        )
    except Exception as e:
        add_check("valid_excalidraw_json", False, f"JSON parse error: {e}", weight=1.0)
        return finalize(checks, total_score, max_score)

    # Build element index
    by_id = {}
    for el in elements:
        eid = el.get("id")
        if eid:
            by_id[eid] = el

    type_counts = {}
    for el in elements:
        t = el.get("type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1

    # ── 3. All elements must have unique IDs ─────────────────────────────────
    ids = [el.get("id") for el in elements if el.get("id")]
    unique_ids = set(ids)
    add_check(
        "all_elements_have_unique_ids",
        len(ids) == len(unique_ids) and len(ids) == len(elements),
        f"{len(ids)} elements have IDs, {len(unique_ids)} unique (total elements: {len(elements)})",
        weight=1.5
    )

    # ── 4. Required element types present ────────────────────────────────────
    has_rectangle = type_counts.get("rectangle", 0) >= 2
    has_diamond = type_counts.get("diamond", 0) >= 1
    has_ellipse = type_counts.get("ellipse", 0) >= 1
    has_arrow = type_counts.get("arrow", 0) >= 3
    has_text = type_counts.get("text", 0) >= 3

    add_check(
        "required_shape_types_present",
        has_rectangle and has_diamond and has_ellipse and has_arrow and has_text,
        (f"rectangle:{type_counts.get('rectangle',0)}, "
         f"ellipse:{type_counts.get('ellipse',0)}, "
         f"diamond:{type_counts.get('diamond',0)}, "
         f"arrow:{type_counts.get('arrow',0)}, "
         f"text:{type_counts.get('text',0)}"),
        weight=2.0
    )

    # ── 5. Arrows use from/to binding (not manual coordinates) ───────────────
    arrows = [el for el in elements if el.get("type") == "arrow"]
    binding_arrows = [a for a in arrows if "from" in a and "to" in a]
    non_binding_arrows = [a for a in arrows if "from" not in a or "to" not in a]
    # Multi-segment arrows with absolutePoints are allowed to be non-binding IF they have from/to too
    manual_coord_only = [a for a in non_binding_arrows if not a.get("absolutePoints")]

    add_check(
        "arrows_use_from_to_binding",
        len(binding_arrows) >= 3 and len(manual_coord_only) == 0,
        (f"{len(binding_arrows)} arrows use from/to binding, "
         f"{len(manual_coord_only)} use manual coords without binding"),
        weight=2.5
    )

    # ── 6. Arrow from/to references valid element IDs ────────────────────────
    dangling_refs = []
    for a in binding_arrows:
        src = a.get("from")
        dst = a.get("to")
        if src and src not in by_id:
            dangling_refs.append(f"arrow {a.get('id')}: from='{src}' not found")
        if dst and dst not in by_id:
            dangling_refs.append(f"arrow {a.get('id')}: to='{dst}' not found")

    add_check(
        "arrow_references_valid_ids",
        len(dangling_refs) == 0,
        "All arrow bindings reference valid element IDs" if not dangling_refs else "; ".join(dangling_refs),
        weight=2.0
    )

    # ── 7. Multi-segment (absolutePoints) loop arrow exists ──────────────────
    loop_arrows = [a for a in arrows if a.get("absolutePoints") is True and
                   isinstance(a.get("points"), list) and len(a.get("points", [])) >= 3]
    add_check(
        "multi_segment_loop_arrow_exists",
        len(loop_arrows) >= 1,
        (f"Found {len(loop_arrows)} absolutePoints arrow(s) with >=3 waypoints" 
         if loop_arrows else "No multi-segment absolutePoints arrow found — retry loop missing"),
        weight=2.0
    )

    # ── 8. Correct color palette used (SKILL.md palette, not generic CSS) ────
    VALID_FILLS = {"#a5d8ff", "#b2f2bb", "#ffec99", "#ffc9c9", "#d0bfff", "#f3d9fa", "#fff4e6"}
    VALID_STROKES = {"#1e1e1e", "#1971c2", "#2f9e44", "#e8590c", "#862e9c"}
    VALID_LABELS = {"#868e96"}
    ALL_VALID_COLORS = VALID_FILLS | VALID_STROKES | VALID_LABELS | {"transparent", "none", ""}

    shape_elements = [el for el in elements if el.get("type") not in ("arrow", "text")]
    fills_used = set()
    strokes_used = set()
    invalid_colors = []

    for el in shape_elements:
        bg = el.get("backgroundColor", "")
        sc = el.get("strokeColor", "")
        if bg:
            fills_used.add(bg)
        if sc:
            strokes_used.add(sc)

    # Check that fills are from the palette
    fills_from_palette = [f for f in fills_used if f in VALID_FILLS]
    strokes_from_palette = [s for s in strokes_used if s in VALID_STROKES]

    palette_ok = len(fills_from_palette) >= 2 and len(strokes_from_palette) >= 1
    add_check(
        "uses_skill_color_palette",
        palette_ok,
        (f"Fills from palette: {fills_from_palette}, "
         f"Strokes from palette: {strokes_from_palette}. "
         f"All fills used: {list(fills_used)}, All strokes used: {list(strokes_used)}"),
        weight=2.0
    )

    # ── 9. fillStyle values are valid SKILL.md values ────────────────────────
    VALID_FILL_STYLES = {"hachure", "cross-hatch", "solid"}
    fill_styles_used = set()
    invalid_fill_styles = []
    for el in shape_elements:
        fs = el.get("fillStyle", "")
        if fs:
            fill_styles_used.add(fs)
            if fs not in VALID_FILL_STYLES:
                invalid_fill_styles.append(f"element {el.get('id')}: fillStyle='{fs}'")

    add_check(
        "valid_fill_styles",
        len(invalid_fill_styles) == 0 and len(fill_styles_used) > 0,
        (f"fillStyles used: {fill_styles_used}. Invalid: {invalid_fill_styles}"
         if invalid_fill_styles else f"fillStyles used: {fill_styles_used}"),
        weight=1.5
    )

    # ── 10. Uses both hachure and another fillStyle (cross-hatch or solid) ───
    uses_hachure = "hachure" in fill_styles_used
    uses_alt_fill = bool(fill_styles_used - {"hachure"})
    add_check(
        "uses_multiple_fill_styles",
        uses_hachure and uses_alt_fill,
        f"fillStyles present: {fill_styles_used}",
        weight=1.5
    )

    # ── 11. fontFamily uses numeric values (1/2/3) not strings ───────────────
    text_elements = [el for el in elements if el.get("type") == "text"]
    bad_font_family = []
    for el in text_elements:
        ff = el.get("fontFamily")
        if ff is not None and not isinstance(ff, int):
            bad_font_family.append(f"id={el.get('id')}: fontFamily={repr(ff)}")

    add_check(
        "font_family_uses_numeric_values",
        len(bad_font_family) == 0 and len(text_elements) > 0,
        (f"{len(text_elements)} text elements, all using numeric fontFamily" 
         if not bad_font_family else f"Non-numeric fontFamily found: {bad_font_family[:3]}"),
        weight=1.5
    )

    # ── 12. Dashed arrow for failure path ────────────────────────────────────
    dashed_arrows = [a for a in arrows if a.get("strokeStyle") == "dashed"]
    add_check(
        "has_dashed_arrow_for_failure_path",
        len(dashed_arrows) >= 1,
        f"Found {len(dashed_arrows)} dashed arrow(s)" if dashed_arrows else "No dashed arrows found",
        weight=1.5
    )

    # ── 13. roughness values are valid (0, 1, or 2) ──────────────────────────
    invalid_roughness = []
    for el in elements:
        r = el.get("roughness")
        if r is not None and r not in (0, 1, 2):
            invalid_roughness.append(f"id={el.get('id')}: roughness={r}")

    add_check(
        "valid_roughness_values",
        len(invalid_roughness) == 0,
        f"All roughness values valid" if not invalid_roughness else f"Invalid: {invalid_roughness[:3]}",
        weight=1.0
    )

    # ── 14. excalidraw version 2 format ──────────────────────────────────────
    version = data.get("version")
    excalidraw_type = data.get("type")
    add_check(
        "correct_excalidraw_format",
        version == 2 and excalidraw_type == "excalidraw",
        f"type={excalidraw_type}, version={version}",
        weight=1.0
    )

    # ── 15. PNG file was rendered ─────────────────────────────────────────────
    png_name = excalidraw_file.stem + ".png"
    png_file = find_file(workspace, png_name)
    if not png_file:
        # Also check /tmp
        tmp_png = Path("/tmp") / png_name
        if tmp_png.exists():
            png_file = tmp_png

    png_exists = png_file is not None and png_file.stat().st_size > 1000 if png_file else False
    add_check(
        "png_rendered_successfully",
        png_exists,
        f"PNG found at {png_file} ({png_file.stat().st_size} bytes)" if png_exists else "PNG not found or too small",
        weight=2.0
    )

    # ── 16. Logical structure: rollback shape connects back (retry loop) ──────
    # The loop arrow should connect something that looks like rollback back to a health check
    # We check: there exists an arrow (possibly absolutePoints) whose 'to' target is 
    # the same as or near the health check nodes (not the end/done node)
    # Heuristic: loop arrow's 'to' endpoint must not be the same as the final terminal node
    if loop_arrows:
        loop_arrow = loop_arrows[0]
        loop_from = loop_arrow.get("from", "")
        loop_to = loop_arrow.get("to", "")
        
        # The 'to' target should exist and not be an ellipse at the very bottom (Done node)
        target_el = by_id.get(loop_to)
        if target_el:
            # Target should NOT be an ellipse named "Done" at the bottom
            target_is_terminal_ellipse = (
                target_el.get("type") == "ellipse" and
                target_el.get("backgroundColor") in ("#d0bfff", "#b2f2bb")
            )
            loop_is_valid = not target_is_terminal_ellipse
        else:
            loop_is_valid = len(loop_arrows) > 0  # At least the arrow exists
        
        add_check(
            "retry_loop_connects_back_correctly",
            loop_is_valid,
            (f"Loop arrow from='{loop_from}' to='{loop_to}', "
             f"target type={target_el.get('type') if target_el else 'unknown'}"),
            weight=2.0
        )
    else:
        add_check(
            "retry_loop_connects_back_correctly",
            False,
            "No multi-segment loop arrow found to evaluate",
            weight=2.0
        )

    # ── 17. Arrow labels (text elements near arrows) ──────────────────────────
    # Should have at least one label-style text (e.g., "Yes", "No", "retry")
    label_texts = []
    for el in text_elements:
        txt = (el.get("text") or "").strip().lower()
        if txt in ("yes", "no", "retry", "ok", "fail", "success", "failure", 
                   "both ok", "healthy", "unhealthy", "sends data"):
            label_texts.append(txt)
        elif el.get("strokeColor") == "#868e96":
            label_texts.append(f"gray-label:{txt[:20]}")

    add_check(
        "has_arrow_labels",
        len(label_texts) >= 1,
        f"Found label texts: {label_texts}" if label_texts else "No arrow labels found (Yes/No/retry/gray text)",
        weight=1.5
    )

    return finalize(checks, total_score, max_score)


def finalize(checks, total_score, max_score):
    score = round(total_score / max_score, 4) if max_score > 0 else 0.0
    passed = score >= 0.70  # Must pass at least 70% of weighted checks
    return {"passed": passed, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))