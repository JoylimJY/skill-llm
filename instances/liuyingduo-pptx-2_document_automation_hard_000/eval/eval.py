#!/usr/bin/env python3
"""
Evaluator for the PPTX pipeline update task.
Checks that the agent produced a valid, correctly populated output.pptx
by parsing its XML content (after unpacking) and running markitdown.
"""

import sys
import json
import subprocess
import zipfile
import re
import tempfile
import shutil
from pathlib import Path

def run_check(name: str, fn) -> dict:
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {e}"}

def find_output_pptx(workspace: Path):
    """Find the output PPTX (not the template)."""
    candidates = list(workspace.rglob("q3_pipeline_update.pptx"))
    if not candidates:
        return None
    return candidates[0]

def extract_text_via_markitdown(pptx_path: Path) -> str:
    """Extract text using markitdown CLI."""
    result = subprocess.run(
        ["python3", "-m", "markitdown", str(pptx_path)],
        capture_output=True, text=True, timeout=60
    )
    return result.stdout

def unpack_pptx(pptx_path: Path, unpack_dir: Path):
    """Unpack PPTX zip into directory."""
    with zipfile.ZipFile(pptx_path, 'r') as z:
        z.extractall(unpack_dir)

def get_slide_ids(pptx_path: Path):
    """Parse presentation.xml to get ordered slide rIds."""
    import xml.etree.ElementTree as ET
    with zipfile.ZipFile(pptx_path, 'r') as z:
        prs_xml = z.read("ppt/presentation.xml").decode("utf-8")
    root = ET.fromstring(prs_xml)
    ns = {
        'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    }
    sld_id_lst = root.find('p:sldIdLst', ns)
    if sld_id_lst is None:
        return []
    return [el.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
            for el in sld_id_lst.findall('p:sldId', ns)]

def get_slide_files(pptx_path: Path):
    """Get the ordered list of slide XML filenames from presentation.rels."""
    import xml.etree.ElementTree as ET
    with zipfile.ZipFile(pptx_path, 'r') as z:
        rels_xml = z.read("ppt/_rels/presentation.xml.rels").decode("utf-8")
    root = ET.fromstring(rels_xml)
    ns = {'r': 'http://schemas.openxmlformats.org/package/2006/relationships'}
    rel_map = {}
    for el in root.findall('r:Relationship', ns):
        rid = el.get('Id')
        target = el.get('Target')
        if 'slides/slide' in target:
            rel_map[rid] = target
    return rel_map

def get_slide_text_content(pptx_path: Path, slide_filename: str) -> str:
    """Extract all text from a specific slide XML."""
    import xml.etree.ElementTree as ET
    inner_path = f"ppt/{slide_filename}" if not slide_filename.startswith("ppt/") else slide_filename
    with zipfile.ZipFile(pptx_path, 'r') as z:
        try:
            xml_bytes = z.read(inner_path)
        except KeyError:
            # Try alternate path
            xml_bytes = z.read(slide_filename)
    
    root = ET.fromstring(xml_bytes)
    ns = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
    texts = []
    for t in root.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}t'):
        if t.text:
            texts.append(t.text.strip())
    return " ".join(texts)

def check_output_exists(workspace: Path):
    pptx = find_output_pptx(workspace)
    if pptx is None:
        return False, "q3_pipeline_update.pptx not found anywhere in workspace"
    if pptx.stat().st_size < 5000:
        return False, f"Output file is suspiciously small ({pptx.stat().st_size} bytes)"
    return True, f"Found at {pptx}"

def check_is_valid_pptx(workspace: Path):
    pptx = find_output_pptx(workspace)
    if pptx is None:
        return False, "Output file not found"
    try:
        with zipfile.ZipFile(pptx, 'r') as z:
            names = z.namelist()
        required = ["ppt/presentation.xml", "[Content_Types].xml"]
        for r in required:
            if r not in names:
                return False, f"Missing required part: {r}"
        return True, "Valid PPTX structure"
    except Exception as e:
        return False, f"Not a valid ZIP/PPTX: {e}"

def check_slide_count(workspace: Path):
    """Output must have exactly 5 slides (slide 5 deleted from original 6)."""
    pptx = find_output_pptx(workspace)
    if pptx is None:
        return False, "Output not found"
    try:
        slide_ids = get_slide_ids(pptx)
        count = len(slide_ids)
        if count == 5:
            return True, f"Correct: 5 slides found (lorem/filler slide deleted)"
        elif count == 6:
            return False, f"6 slides found — the lorem ipsum filler slide was NOT deleted"
        else:
            return False, f"Expected 5 slides, found {count}"
    except Exception as e:
        return False, f"Error counting slides: {e}"

def check_no_placeholder_text(workspace: Path):
    """No XXXX, lorem, ipsum, or 'this.*page.*layout' text should remain."""
    pptx = find_output_pptx(workspace)
    if pptx is None:
        return False, "Output not found"
    try:
        text = extract_text_via_markitdown(pptx)
        patterns = [
            (r'xxxx', 'XXXX placeholder'),
            (r'lorem', 'lorem ipsum'),
            (r'ipsum', 'lorem ipsum'),
            (r'this.{0,20}(page|slide).{0,20}layout', 'slide layout placeholder'),
        ]
        found = []
        for pat, label in patterns:
            if re.search(pat, text, re.IGNORECASE):
                # Find the specific matches
                matches = re.findall(r'.{0,30}' + pat + r'.{0,30}', text, re.IGNORECASE)
                found.append(f"{label}: ...{matches[0]}...")
        if found:
            return False, f"Placeholder text still present: {'; '.join(found)}"
        return True, "No placeholder text found"
    except Exception as e:
        return False, f"Error checking text: {e}"

def check_company_name_present(workspace: Path):
    """NovaBio Therapeutics must appear in the deck."""
    pptx = find_output_pptx(workspace)
    if pptx is None:
        return False, "Output not found"
    text = extract_text_via_markitdown(pptx)
    if "NovaBio" in text:
        return True, "NovaBio Therapeutics found in deck"
    return False, "Company name 'NovaBio' not found — title slide may not be populated"

def check_pipeline_assets(workspace: Path):
    """All three pipeline assets must be mentioned."""
    pptx = find_output_pptx(workspace)
    if pptx is None:
        return False, "Output not found"
    text = extract_text_via_markitdown(pptx)
    assets = ["BIO-101", "BIO-202", "BIO-303"]
    missing = [a for a in assets if a not in text]
    if not missing:
        return True, f"All 3 pipeline assets found: {assets}"
    return False, f"Missing pipeline assets: {missing}"

def check_financial_data(workspace: Path):
    """Key financial figures must be present."""
    pptx = find_output_pptx(workspace)
    if pptx is None:
        return False, "Output not found"
    text = extract_text_via_markitdown(pptx)
    checks = {
        "142": "Cash position $142.5M",
        "48.2": "Shares outstanding 48.2M",
    }
    missing = []
    for val, label in checks.items():
        if val not in text:
            missing.append(label)
    if not missing:
        return True, "Key financial figures present"
    return False, f"Missing financial data: {missing}"

def check_management_team(workspace: Path):
    """Management team members must be named."""
    pptx = find_output_pptx(workspace)
    if pptx is None:
        return False, "Output not found"
    text = extract_text_via_markitdown(pptx)
    members = ["Hartwell", "Chen", "Santos", "Patel"]
    missing = [m for m in members if m not in text]
    if not missing:
        return True, f"All 4 management team members found"
    return False, f"Missing management team members: {missing}"

def check_multi_paragraph_structure(workspace: Path):
    """
    The pipeline slide must use separate <a:p> elements for each asset —
    not a concatenated single paragraph. This is the key proprietary constraint.
    We verify by checking that the pipeline slide XML has at least 3 separate
    <a:p> elements in the body text box (one per asset).
    """
    pptx = find_output_pptx(workspace)
    if pptx is None:
        return False, "Output not found"
    
    try:
        import xml.etree.ElementTree as ET
        
        # Find the slide with pipeline content
        rel_map = get_slide_files(pptx)
        slide_ids = get_slide_ids(pptx)
        
        pipeline_slide_xml = None
        for rid in slide_ids:
            if rid not in rel_map:
                continue
            slide_path = rel_map[rid]
            slide_text = get_slide_text_content(pptx, slide_path)
            if "BIO-101" in slide_text or "Pipeline" in slide_text or "Phase" in slide_text:
                # This is the pipeline slide
                inner = f"ppt/{slide_path}" if not slide_path.startswith("ppt/") else slide_path
                with zipfile.ZipFile(pptx, 'r') as z:
                    try:
                        pipeline_slide_xml = z.read(inner).decode("utf-8")
                    except KeyError:
                        pipeline_slide_xml = z.read(slide_path).decode("utf-8")
                break
        
        if pipeline_slide_xml is None:
            return False, "Could not identify pipeline slide"
        
        root = ET.fromstring(pipeline_slide_xml)
        a_ns = 'http://schemas.openxmlformats.org/drawingml/2006/main'
        
        # Count paragraphs in body text box (idx=1 placeholder or body sp)
        all_txbodies = root.iter(f'{{{a_ns}}}txBody')
        max_paragraphs = 0
        for txbody in all_txbodies:
            paras = txbody.findall(f'{{{a_ns}}}p')
            # Count non-empty paragraphs
            non_empty = sum(1 for p in paras if any(
                t.text and t.text.strip()
                for t in p.iter(f'{{{a_ns}}}t')
            ))
            max_paragraphs = max(max_paragraphs, non_empty)
        
        if max_paragraphs >= 3:
            return True, f"Pipeline slide has {max_paragraphs} separate paragraphs (multi-paragraph structure correct)"
        else:
            return False, f"Pipeline slide only has {max_paragraphs} non-empty paragraphs — assets may be concatenated into single paragraph"
    
    except Exception as e:
        return False, f"Error inspecting XML structure: {e}"

def check_bold_headers_present(workspace: Path):
    """
    At least one slide must have bold formatting on headers (b='1' in rPr).
    This verifies the agent followed the proprietary bold rule for headers.
    """
    pptx = find_output_pptx(workspace)
    if pptx is None:
        return False, "Output not found"
    
    try:
        bold_found = False
        with zipfile.ZipFile(pptx, 'r') as z:
            slide_files = [n for n in z.namelist() if re.match(r'ppt/slides/slide\d+\.xml', n)]
            for sf in slide_files:
                content = z.read(sf).decode("utf-8")
                if 'b="1"' in content or "b='1'" in content:
                    bold_found = True
                    break
        
        if bold_found:
            return True, "Bold formatting (b='1') found in slide XML — headers correctly bolded"
        return False, "No bold formatting found in any slide XML — headers not bolded per skill rules"
    except Exception as e:
        return False, f"Error checking bold: {e}"

def check_no_unicode_bullets(workspace: Path):
    """
    No raw unicode bullet character (•, U+2022) should appear in slide XML.
    The skill mandates using <a:buChar> or <a:buNone>, never raw '•'.
    """
    pptx = find_output_pptx(workspace)
    if pptx is None:
        return False, "Output not found"
    
    try:
        violations = []
        with zipfile.ZipFile(pptx, 'r') as z:
            slide_files = [n for n in z.namelist() if re.match(r'ppt/slides/slide\d+\.xml', n)]
            for sf in slide_files:
                content = z.read(sf).decode("utf-8")
                # Check for unicode bullet inside <a:t> tags
                if '\u2022' in content:
                    violations.append(sf)
        
        if not violations:
            return True, "No raw unicode bullets (•) found — correct bullet handling"
        return False, f"Raw unicode bullets found in: {violations} — use <a:buChar> or <a:buNone> instead"
    except Exception as e:
        return False, f"Error checking bullets: {e}"

def check_pack_used_correctly(workspace: Path):
    """
    The pack.py script requires --original flag. We verify the output is a
    structurally valid PPTX that has content_types and proper slide master linkage,
    which only pack.py with --original produces correctly.
    """
    pptx = find_output_pptx(workspace)
    if pptx is None:
        return False, "Output not found"
    
    try:
        with zipfile.ZipFile(pptx, 'r') as z:
            names = z.namelist()
        
        required_parts = [
            "[Content_Types].xml",
            "ppt/presentation.xml",
            "ppt/slideMasters/slideMaster1.xml",
            "ppt/slideLayouts/slideLayout1.xml",
        ]
        missing = [p for p in required_parts if p not in names]
        if missing:
            return False, f"Missing PPTX parts (improper packing): {missing}"
        
        # Check that slide layout refs exist
        slide_files = [n for n in names if re.match(r'ppt/slides/slide\d+\.xml', n)]
        if len(slide_files) == 0:
            return False, "No slide files found in output"
        
        return True, f"PPTX has proper structure with {len(slide_files)} slides and all required parts"
    except Exception as e:
        return False, f"Error verifying pack: {e}"

def check_q3_catalysts(workspace: Path):
    """At least two Q4 2024 catalysts must be mentioned."""
    pptx = find_output_pptx(workspace)
    if pptx is None:
        return False, "Output not found"
    text = extract_text_via_markitdown(pptx)
    catalyst_keywords = ["Q4 2024", "Q1 2025", "topline", "catalyst", "milestone", "Fast Track", "enrollment"]
    found = [k for k in catalyst_keywords if k in text]
    if len(found) >= 2:
        return True, f"Catalyst/milestone content found: {found[:3]}"
    return False, f"Insufficient catalyst/milestone content. Only found: {found}"

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    
    checks_fns = [
        ("output_file_exists", check_output_exists),
        ("valid_pptx_structure", check_is_valid_pptx),
        ("slide_count_is_5", check_slide_count),
        ("no_placeholder_text", check_no_placeholder_text),
        ("company_name_present", check_company_name_present),
        ("all_pipeline_assets_present", check_pipeline_assets),
        ("financial_data_present", check_financial_data),
        ("management_team_named", check_management_team),
        ("multi_paragraph_xml_structure", check_multi_paragraph_structure),
        ("bold_headers_in_xml", check_bold_headers_present),
        ("no_raw_unicode_bullets", check_no_unicode_bullets),
        ("pptx_correctly_packed", check_pack_used_correctly),
        ("q3_catalysts_present", check_q3_catalysts),
    ]
    
    results = []
    for name, fn in checks_fns:
        results.append(run_check(name, lambda f=fn: f(workspace)))
    
    passed_count = sum(1 for r in results if r["passed"])
    total = len(results)
    score = passed_count / total
    
    # Must pass critical checks to overall pass
    critical = ["output_file_exists", "valid_pptx_structure", "slide_count_is_5", 
                "no_placeholder_text", "all_pipeline_assets_present", "multi_paragraph_xml_structure"]
    critical_passed = all(r["passed"] for r in results if r["name"] in critical)
    
    output = {
        "passed": critical_passed and score >= 0.75,
        "score": round(score, 3),
        "checks": results
    }
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()