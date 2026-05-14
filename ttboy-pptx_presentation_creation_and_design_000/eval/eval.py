import sys
import json
import zipfile
import re
import os
from pathlib import Path

def load_pptx_xml_files(pptx_path):
    """Extract all XML content from a PPTX file."""
    xml_contents = {}
    with zipfile.ZipFile(pptx_path, 'r') as z:
        for name in z.namelist():
            if name.endswith('.xml') or name.endswith('.rels'):
                try:
                    xml_contents[name] = z.read(name).decode('utf-8', errors='replace')
                except Exception:
                    xml_contents[name] = ""
    return xml_contents

def check_no_hash_colors(xml_contents):
    """Check that no hex colors use # prefix (PptxGenJS pitfall)."""
    bad_patterns = []
    color_attr_pattern = re.compile(r'(?:val|solidFill|srgbClr|schemeClr)[^>]*?#[0-9A-Fa-f]{3,8}')
    # Also check for # in color-looking attributes in the XML
    hash_color_pattern = re.compile(r'["\s]#[0-9A-Fa-f]{6}["\s<]')
    for fname, content in xml_contents.items():
        if fname.startswith('ppt/slides/slide') and fname.endswith('.xml'):
            if hash_color_pattern.search(content):
                bad_patterns.append(fname)
    return bad_patterns

def check_no_8char_hex_shadow(xml_contents):
    """Check that shadow colors are not encoded as 8-char hex (opacity trap)."""
    bad_files = []
    # 8-char hex color in shadow context (e.g., 00000020)
    eight_char_pattern = re.compile(r'<a:srgbClr val="[0-9A-Fa-f]{8}"')
    for fname, content in xml_contents.items():
        if fname.startswith('ppt/slides/') and fname.endswith('.xml'):
            if eight_char_pattern.search(content):
                bad_files.append(fname)
    return bad_files

def check_no_unicode_bullets(xml_contents):
    """Check that unicode bullet characters are not used."""
    bad_files = []
    unicode_bullet = re.compile(r'[•‣▸▪◦]')
    for fname, content in xml_contents.items():
        if fname.startswith('ppt/slides/slide') and fname.endswith('.xml'):
            if unicode_bullet.search(content):
                bad_files.append(fname)
    return bad_files

def check_slide_count(xml_contents):
    """Check that the presentation has at least 5 slides."""
    pres_xml = xml_contents.get('ppt/presentation.xml', '')
    slide_ids = re.findall(r'<p:sldId\b', pres_xml)
    return len(slide_ids)

def check_content_via_markitdown(pptx_path):
    """Use markitdown to extract text and verify key content."""
    import subprocess
    result = subprocess.run(
        ['python3', '-m', 'markitdown', str(pptx_path)],
        capture_output=True, text=True, timeout=60
    )
    return result.stdout + result.stderr

def check_has_chart(xml_contents):
    """Check that at least one chart is present."""
    for fname, content in xml_contents.items():
        if fname.startswith('ppt/charts/') and fname.endswith('.xml'):
            return True
    # Also check for chart references in slides
    for fname, content in xml_contents.items():
        if fname.startswith('ppt/slides/') and fname.endswith('.xml'):
            if 'c:chart' in content or 'chart' in content.lower() and 'c:' in content:
                return True
    return False

def check_has_shapes(xml_contents):
    """Check that shapes with fill colors are present (visual elements)."""
    shape_count = 0
    for fname, content in xml_contents.items():
        if fname.startswith('ppt/slides/slide') and fname.endswith('.xml'):
            # Count solid fill shapes (not text boxes without fill)
            fills = re.findall(r'<a:solidFill>', content)
            shape_count += len(fills)
    return shape_count

def check_forest_moss_colors(xml_contents):
    """Check that Forest & Moss palette colors are used (2C5F2D or 97BC62 or F5F5F5)."""
    palette_colors = ['2C5F2D', '2c5f2d', '97BC62', '97bc62', 'F5F5F5', 'f5f5f5']
    found = []
    all_slide_content = ""
    for fname, content in xml_contents.items():
        if fname.startswith('ppt/slides/slide') and fname.endswith('.xml'):
            all_slide_content += content
    for color in palette_colors:
        if color.lower() in all_slide_content.lower():
            found.append(color)
    return found

def check_shadow_present(xml_contents):
    """Check that shadow elements are present in the presentation."""
    for fname, content in xml_contents.items():
        if fname.startswith('ppt/slides/slide') and fname.endswith('.xml'):
            if '<a:outerShdw' in content or '<a:innerShdw' in content:
                return True
    return False

def check_revenue_data_in_chart(xml_contents):
    """Check that quarterly revenue data appears in chart XML."""
    chart_content = ""
    for fname, content in xml_contents.items():
        if fname.startswith('ppt/charts/') and fname.endswith('.xml'):
            chart_content += content
    if not chart_content:
        # Also check drawing XML for embedded chart data
        for fname, content in xml_contents.items():
            if 'chart' in fname.lower():
                chart_content += content
    
    # Check for revenue values (some should be present)
    revenue_values = ['120000', '145000', '178000', '210000', '265000', '310000',
                      '120', '145', '178', '210', '265', '310']
    found_values = [v for v in revenue_values if v in chart_content]
    
    # Also check the full content for embedded chart data
    all_content = ""
    for fname, content in xml_contents.items():
        all_content += content
    found_values_all = [v for v in revenue_values if v in all_content]
    
    return len(found_values) >= 3 or len(found_values_all) >= 3

def check_key_text_content(markitdown_output):
    """Check that key content strings appear in the extracted text."""
    checks = {
        "company_name": bool(re.search(r'greenwave', markitdown_output, re.IGNORECASE)),
        "market_tam": bool(re.search(r'\$?87', markitdown_output)),
        "mrr_or_traction": bool(re.search(r'38[,\s]?000|38K|\$38', markitdown_output, re.IGNORECASE) or 
                                re.search(r'pilot|traction|MRR', markitdown_output, re.IGNORECASE)),
        "team_ceo": bool(re.search(r'Aisha|Mensah', markitdown_output, re.IGNORECASE)),
        "team_cto": bool(re.search(r'Rajiv|Nair', markitdown_output, re.IGNORECASE)),
        "five_slides_content": len(re.findall(r'##\s*Slide\s*\d+|slide\s*\d+', markitdown_output, re.IGNORECASE)) >= 2,
    }
    return checks

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    checks = []
    total_score = 0.0
    
    # Find the output file
    pptx_candidates = list(Path(workspace).rglob('greenwave_pitch.pptx'))
    
    if not pptx_candidates:
        # Try alternate names
        pptx_candidates = list(Path(workspace).rglob('greenwave*.pptx'))
    
    if not pptx_candidates:
        pptx_candidates = list(Path(workspace).rglob('*.pptx'))
        pptx_candidates = [p for p in pptx_candidates if 'greenwave' in p.name.lower() or 'pitch' in p.name.lower()]

    file_found = len(pptx_candidates) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found: {pptx_candidates[0]}" if file_found else "No greenwave_pitch.pptx found in workspace"
    })
    
    if not file_found:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    pptx_path = pptx_candidates[0]
    
    try:
        xml_contents = load_pptx_xml_files(pptx_path)
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": f"Cannot open PPTX: {e}"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({"name": "file_readable", "passed": True, "detail": "PPTX opened and XML extracted"})

    # CHECK 1: Slide count >= 5
    try:
        slide_count = check_slide_count(xml_contents)
        passed = slide_count >= 5
        checks.append({
            "name": "slide_count_at_least_5",
            "passed": passed,
            "detail": f"Found {slide_count} slides in presentation.xml"
        })
        if passed:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "slide_count_at_least_5", "passed": False, "detail": str(e)})

    # CHECK 2: No # prefix on hex colors (critical PptxGenJS pitfall)
    try:
        bad_files = check_no_hash_colors(xml_contents)
        passed = len(bad_files) == 0
        checks.append({
            "name": "no_hash_prefix_on_colors",
            "passed": passed,
            "detail": "PASS - No # prefixes found in color attributes" if passed 
                     else f"FAIL - # prefix found in: {bad_files[:3]}"
        })
        if passed:
            total_score += 1.5
    except Exception as e:
        checks.append({"name": "no_hash_prefix_on_colors", "passed": False, "detail": str(e)})

    # CHECK 3: No 8-char hex for shadow opacity (critical pitfall)
    try:
        bad_files = check_no_8char_hex_shadow(xml_contents)
        passed = len(bad_files) == 0
        checks.append({
            "name": "no_8char_hex_shadow_color",
            "passed": passed,
            "detail": "PASS - No 8-char hex shadow colors found" if passed 
                     else f"FAIL - 8-char shadow hex found in: {bad_files[:3]}"
        })
        if passed:
            total_score += 1.5
    except Exception as e:
        checks.append({"name": "no_8char_hex_shadow_color", "passed": False, "detail": str(e)})

    # CHECK 4: No unicode bullets
    try:
        bad_files = check_no_unicode_bullets(xml_contents)
        passed = len(bad_files) == 0
        checks.append({
            "name": "no_unicode_bullet_characters",
            "passed": passed,
            "detail": "PASS - No unicode bullet chars found" if passed 
                     else f"FAIL - Unicode bullets found in: {bad_files[:3]}"
        })
        if passed:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "no_unicode_bullet_characters", "passed": False, "detail": str(e)})

    # CHECK 5: Forest & Moss palette colors used
    try:
        found_colors = check_forest_moss_colors(xml_contents)
        passed = len(found_colors) >= 1
        checks.append({
            "name": "forest_moss_palette_used",
            "passed": passed,
            "detail": f"Found palette colors: {found_colors}" if passed 
                     else "No Forest & Moss colors (2C5F2D, 97BC62, F5F5F5) found"
        })
        if passed:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "forest_moss_palette_used", "passed": False, "detail": str(e)})

    # CHECK 6: Has chart
    try:
        has_chart = check_has_chart(xml_contents)
        checks.append({
            "name": "revenue_chart_present",
            "passed": has_chart,
            "detail": "Chart found in presentation" if has_chart 
                     else "No chart found - revenue slide requires bar chart"
        })
        if has_chart:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "revenue_chart_present", "passed": False, "detail": str(e)})

    # CHECK 7: Has visual shapes (not text-only)
    try:
        shape_count = check_has_shapes(xml_contents)
        passed = shape_count >= 5
        checks.append({
            "name": "visual_shapes_present",
            "passed": passed,
            "detail": f"Found {shape_count} solid-fill shape elements" 
        })
        if passed:
            total_score += 0.5
    except Exception as e:
        checks.append({"name": "visual_shapes_present", "passed": False, "detail": str(e)})

    # CHECK 8: Shadows present
    try:
        has_shadow = check_shadow_present(xml_contents)
        checks.append({
            "name": "shadow_elements_present",
            "passed": has_shadow,
            "detail": "Shadow elements found in slides" if has_shadow 
                     else "No shadow elements found - cards should have drop shadows"
        })
        if has_shadow:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "shadow_elements_present", "passed": False, "detail": str(e)})

    # CHECK 9: Revenue data in chart
    try:
        has_revenue_data = check_revenue_data_in_chart(xml_contents)
        checks.append({
            "name": "revenue_data_in_chart",
            "passed": has_revenue_data,
            "detail": "Revenue values found in chart data" if has_revenue_data 
                     else "Revenue values (120000-310000) not found in chart"
        })
        if has_revenue_data:
            total_score += 0.5
    except Exception as e:
        checks.append({"name": "revenue_data_in_chart", "passed": False, "detail": str(e)})

    # CHECK 10: Key text content via markitdown
    try:
        md_output = check_content_via_markitdown(pptx_path)
        content_checks = check_key_text_content(md_output)
        
        passed_content = [k for k, v in content_checks.items() if v]
        failed_content = [k for k, v in content_checks.items() if not v]
        all_pass = len(failed_content) == 0
        
        checks.append({
            "name": "key_content_present_markitdown",
            "passed": len(passed_content) >= 4,
            "detail": f"Passed: {passed_content}, Failed: {failed_content}"
        })
        if len(passed_content) >= 4:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "key_content_present_markitdown", "passed": False, "detail": str(e)})

    # CHECK 11: No accent lines under titles (hallmark of AI-generated, explicitly banned)
    try:
        # Look for thin horizontal lines immediately after title elements (common pattern)
        all_content = " ".join(xml_contents.values())
        # Pattern: line shape with height ~0 (accent underline) - look for LINE shapes with h=0 near titles
        accent_line_indicators = re.findall(r'<p:sp[^>]*>.*?<a:ln[^>]*/>.*?</p:sp>', all_content[:5000], re.DOTALL)
        # This is a soft check - we look for the pattern but it's complex to detect precisely
        # Instead check for very thin rectangles used as underlines (h < 0.05")
        # EMU: 1 inch = 914400 EMU, 0.05 inch = 45720 EMU
        thin_line_pattern = re.compile(r'<a:ext cx="\d+" cy="(?:[0-9]{1,4})"')
        thin_lines = thin_line_pattern.findall(all_content)
        # A cy of < 10000 EMU is suspiciously thin (< 0.011 inches) but could be intentional icons
        very_thin = [t for t in thin_lines if int(re.search(r'cy="(\d+)"', t).group(1)) < 10000]
        
        # This check is informational - we don't hard-fail for this as detection is imperfect
        checks.append({
            "name": "no_accent_lines_under_titles_check",
            "passed": True,  # Informational only
            "detail": f"Note: {len(very_thin)} very thin elements found. Manual review recommended for accent lines."
        })
        total_score += 0.0  # No score for this - informational
    except Exception as e:
        checks.append({"name": "no_accent_lines_under_titles_check", "passed": True, "detail": "Check skipped"})

    # CHECK 12: Shared shadow object mutation check
    # If the agent shared shadow objects, the second shape will have corrupted EMU values
    # We look for unreasonably large offset values (sign of EMU mutation bug)
    try:
        shadow_corrupt = False
        shadow_pattern = re.compile(r'<a:outerShdw[^>]+dist="(\d+)"')
        for fname, content in xml_contents.items():
            if fname.startswith('ppt/slides/'):
                for match in shadow_pattern.finditer(content):
                    dist_val = int(match.group(1))
                    # Normal offset: 0-200 pt = 0-2667600 EMU
                    # Corrupted (already converted again): would be astronomically large
                    if dist_val > 3000000:
                        shadow_corrupt = True
                        break
        
        passed = not shadow_corrupt
        checks.append({
            "name": "shadow_objects_not_mutated",
            "passed": passed,
            "detail": "PASS - Shadow dist values are in normal range" if passed 
                     else "FAIL - Shadow dist values corrupted (object reuse mutation bug)"
        })
        if passed:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "shadow_objects_not_mutated", "passed": True, "detail": f"Check error (pass by default): {e}"})
        total_score += 1.0

    # Compute final score (max ~10)
    max_score = 10.0
    normalized_score = min(total_score / max_score, 1.0)
    
    critical_checks = ["output_file_exists", "no_hash_prefix_on_colors", "no_8char_hex_shadow_color", 
                       "slide_count_at_least_5", "key_content_present_markitdown"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)
    
    overall_passed = critical_passed and normalized_score >= 0.6

    print(json.dumps({
        "passed": overall_passed,
        "score": round(normalized_score, 3),
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main()