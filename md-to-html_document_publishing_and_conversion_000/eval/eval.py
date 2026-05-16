import sys
import json
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []

    # ---- Check 1: Find the output HTML file named exactly 'biospark_protocol.html' ----
    target_filename = "biospark_protocol.html"
    found_files = list(workspace.rglob(target_filename))

    check_file_exists = {
        "name": "Output file 'biospark_protocol.html' exists",
        "passed": len(found_files) > 0,
        "detail": f"Found {len(found_files)} file(s) named '{target_filename}'"
    }
    checks.append(check_file_exists)

    if not found_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    html_path = found_files[0]

    try:
        html_content = html_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "HTML file readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "HTML file readable", "passed": True, "detail": f"File at {html_path}"})

    # ---- Check 2: Custom title is set correctly ----
    # The agent must use -t "BioSpark CRISPR Protocol" (or similar with BioSpark and CRISPR)
    import re

    title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE)
    title_text = title_match.group(1).strip() if title_match else ""

    # We require the title to contain "BioSpark" AND "CRISPR" (case-insensitive)
    title_has_biospark = "biospark" in title_text.lower()
    title_has_crispr = "crispr" in title_text.lower()
    title_correct = title_has_biospark and title_has_crispr

    checks.append({
        "name": "Custom title contains 'BioSpark' and 'CRISPR'",
        "passed": title_correct,
        "detail": f"Found title: '{title_text}'. Needs both 'BioSpark' and 'CRISPR'."
    })

    # ---- Check 3: TOC level restriction (only H1 and H2 in TOC, no H3/H4 items) ----
    # When -l 2 is used, only H1/H2 headings appear as toc-item divs
    # H3+ headings like "Chemical Hazards", "Criteria for sgRNA Selection" should NOT be in TOC

    # Find all toc-level classes
    toc_level_matches = re.findall(r'class="toc-item toc-level-(\d+)"', html_content)
    toc_levels = [int(x) for x in toc_level_matches]

    has_any_toc = len(toc_levels) > 0
    has_h1_or_h2_in_toc = any(l <= 2 for l in toc_levels)
    has_h3_or_deeper_in_toc = any(l >= 3 for l in toc_levels)

    toc_level_check_passed = has_any_toc and has_h1_or_h2_in_toc and not has_h3_or_deeper_in_toc

    checks.append({
        "name": "TOC restricted to H1/H2 only (level=2 flag used)",
        "passed": toc_level_check_passed,
        "detail": (
            f"TOC levels found: {sorted(set(toc_levels)) if toc_levels else 'none'}. "
            f"Expected only levels 1 and/or 2 in TOC. "
            f"H3+ present: {has_h3_or_deeper_in_toc}. Any TOC items: {has_any_toc}."
        )
    })

    # ---- Check 4: Core CRISPR content is present in HTML body ----
    # This verifies the actual markdown was converted, not an empty/stub HTML
    content_keywords = ["CRISPR", "sgRNA", "electroporation", "Cas9"]
    missing_keywords = [kw for kw in content_keywords if kw.lower() not in html_content.lower()]
    content_check_passed = len(missing_keywords) == 0

    checks.append({
        "name": "CRISPR protocol content present in HTML body",
        "passed": content_check_passed,
        "detail": (
            f"Missing keywords: {missing_keywords}" if missing_keywords
            else "All expected content keywords found in HTML."
        )
    })

    # ---- Check 5: H3+ headings appear in BODY content (not stripped from document, just from TOC) ----
    # Verify that the content itself still has h3 tags (the content is complete, only TOC is restricted)
    h3_in_body = bool(re.search(r'<h3[\s>]', html_content, re.IGNORECASE))
    checks.append({
        "name": "H3 headings present in document body (content integrity)",
        "passed": h3_in_body,
        "detail": "H3 tags should exist in the body even when TOC level is restricted to 2."
    })

    # ---- Check 6: HTML has the sidebar/TOC structure ----
    has_sidebar = 'id="sidebar"' in html_content
    has_toc_div = 'id="toc"' in html_content
    structure_ok = has_sidebar and has_toc_div

    checks.append({
        "name": "HTML has proper sidebar/TOC structure",
        "passed": structure_ok,
        "detail": f"sidebar element: {has_sidebar}, toc div: {has_toc_div}"
    })

    # ---- Scoring ----
    passed_checks = [c for c in checks if c["passed"]]
    total = len(checks)
    score = len(passed_checks) / total

    # Must pass file existence + title + toc level + content to be considered passing
    critical_checks = ["Output file 'biospark_protocol.html' exists",
                       "Custom title contains 'BioSpark' and 'CRISPR'",
                       "TOC restricted to H1/H2 only (level=2 flag used)",
                       "CRISPR protocol content present in HTML body"]
    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == name), False)
        for name in critical_checks
    )

    return {
        "passed": critical_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))