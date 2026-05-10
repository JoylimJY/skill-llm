import sys
import json
import os
from pathlib import Path

def run_eval(workspace):
    checks = []
    total_score = 0.0
    max_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        nonlocal total_score, max_score
        checks.append({"name": name, "passed": passed, "detail": detail})
        max_score += weight
        if passed:
            total_score += weight

    # ---- CHECK 1: Output file exists ----
    report_files = list(Path(workspace).rglob("formatting_audit.json"))
    report_exists = len(report_files) > 0
    add_check(
        "formatting_audit.json exists",
        report_exists,
        f"Found {len(report_files)} file(s) named 'formatting_audit.json'" if report_exists else "File 'formatting_audit.json' not found anywhere in workspace",
        weight=1.0
    )

    if not report_exists:
        # All subsequent checks will fail - still report them
        add_check("Report is valid JSON", False, "Cannot check - file not found", weight=1.0)
        add_check("Report contains results array with 5 entries", False, "Cannot check - file not found", weight=2.0)
        add_check("Each result has required fields", False, "Cannot check - file not found", weight=2.0)
        add_check("All 5 legacy docs processed", False, "Cannot check - file not found", weight=2.0)
        add_check("formattedMarkdown present and non-empty for each doc", False, "Cannot check - file not found", weight=2.0)
        add_check("originalLength and formattedLength are numeric", False, "Cannot check - file not found", weight=1.0)
        add_check("warnings field present per result", False, "Cannot check - file not found", weight=1.0)
        add_check("lintErrors count present per result", False, "Cannot check - file not found", weight=1.0)
        add_check("commonmark style used (emphasisStyle underscore evidence)", False, "Cannot check - file not found", weight=3.0)
        add_check("listStyle dash applied (no asterisk or plus list markers)", False, "Cannot check - file not found", weight=2.0)
        add_check("headingStyle atx applied (no setext headings)", False, "Cannot check - file not found", weight=2.0)
        add_check("Formatted docs written back to original paths", False, "Cannot check - file not found", weight=2.0)

        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    report_path = report_files[0]

    # ---- CHECK 2: Valid JSON ----
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        add_check("Report is valid JSON", True, f"Parsed successfully from {report_path}", weight=1.0)
    except Exception as e:
        add_check("Report is valid JSON", False, f"JSON parse error: {e}", weight=1.0)
        # Can't continue
        for _ in range(10):
            add_check("(skipped)", False, "Cannot check - JSON invalid", weight=1.0)
        score = total_score / max_score if max_score > 0 else 0.0
        return {"passed": False, "score": round(score, 3), "checks": checks}

    # ---- CHECK 3: results array with 5 entries ----
    results = None
    if isinstance(report, dict) and "results" in report:
        results = report["results"]
    elif isinstance(report, list):
        results = report

    has_5_results = isinstance(results, list) and len(results) == 5
    add_check(
        "Report contains results array with 5 entries",
        has_5_results,
        f"results array has {len(results) if isinstance(results, list) else 'N/A'} entries (expected 5)",
        weight=2.0
    )

    if not has_5_results:
        for _ in range(9):
            add_check("(skipped)", False, "Cannot check - results array missing or wrong size", weight=1.0)
        score = total_score / max_score if max_score > 0 else 0.0
        return {"passed": False, "score": round(score, 3), "checks": checks}

    # ---- CHECK 4: Each result has required fields ----
    required_fields_checks = []
    for i, res in enumerate(results):
        if not isinstance(res, dict):
            required_fields_checks.append(False)
            continue
        # Must have at minimum: file/path identifier, formattedMarkdown or formatted content, originalLength, formattedLength, warnings, lintErrors or lint info
        has_file = any(k in res for k in ["file", "path", "filename", "name"])
        has_formatted = any(k in res for k in ["formattedMarkdown", "formatted", "content", "formattedContent"])
        has_orig_len = any(k in res for k in ["originalLength", "original_length", "origLen"])
        has_fmt_len = any(k in res for k in ["formattedLength", "formatted_length", "fmtLen"])
        has_warnings = "warnings" in res
        required_fields_checks.append(has_file and has_formatted and has_orig_len and has_fmt_len and has_warnings)

    all_have_fields = all(required_fields_checks)
    add_check(
        "Each result has required fields",
        all_have_fields,
        f"{sum(required_fields_checks)}/5 results have all required fields (file, formattedMarkdown, originalLength, formattedLength, warnings)",
        weight=2.0
    )

    # ---- CHECK 5: All 5 legacy docs accounted for ----
    expected_doc_patterns = [
        "device-overview",
        "installation-guide",
        "api-reference",
        "calibration-procedure",
        "release-notes"
    ]
    found_docs = []
    for res in results:
        if not isinstance(res, dict):
            continue
        file_val = ""
        for k in ["file", "path", "filename", "name"]:
            if k in res:
                file_val = str(res[k])
                break
        found_docs.append(file_val)

    docs_found_count = 0
    for pattern in expected_doc_patterns:
        if any(pattern in fd for fd in found_docs):
            docs_found_count += 1

    add_check(
        "All 5 legacy docs processed",
        docs_found_count == 5,
        f"Found {docs_found_count}/5 expected documents: {expected_doc_patterns}",
        weight=2.0
    )

    # ---- CHECK 6: formattedMarkdown present and non-empty ----
    non_empty_formatted = 0
    for res in results:
        if not isinstance(res, dict):
            continue
        for k in ["formattedMarkdown", "formatted", "content", "formattedContent"]:
            if k in res and isinstance(res[k], str) and len(res[k].strip()) > 50:
                non_empty_formatted += 1
                break

    add_check(
        "formattedMarkdown present and non-empty for each doc",
        non_empty_formatted == 5,
        f"{non_empty_formatted}/5 results have non-empty formatted markdown content",
        weight=2.0
    )

    # ---- CHECK 7: originalLength and formattedLength are numeric ----
    numeric_lengths = 0
    for res in results:
        if not isinstance(res, dict):
            continue
        orig = None
        fmt = None
        for k in ["originalLength", "original_length", "origLen"]:
            if k in res:
                orig = res[k]
                break
        for k in ["formattedLength", "formatted_length", "fmtLen"]:
            if k in res:
                fmt = res[k]
                break
        if isinstance(orig, (int, float)) and isinstance(fmt, (int, float)) and orig > 0 and fmt > 0:
            numeric_lengths += 1

    add_check(
        "originalLength and formattedLength are numeric and positive",
        numeric_lengths == 5,
        f"{numeric_lengths}/5 results have valid numeric originalLength and formattedLength",
        weight=1.0
    )

    # ---- CHECK 8: warnings field present ----
    warnings_present = 0
    for res in results:
        if not isinstance(res, dict):
            continue
        if "warnings" in res and isinstance(res["warnings"], (list, int, float)):
            warnings_present += 1

    add_check(
        "warnings field present per result",
        warnings_present == 5,
        f"{warnings_present}/5 results have warnings field",
        weight=1.0
    )

    # ---- CHECK 9: lintErrors / lint info present ----
    lint_present = 0
    for res in results:
        if not isinstance(res, dict):
            continue
        has_lint = any(k in res for k in ["lintErrors", "lint_errors", "errors", "lintResult", "lintCount", "errorCount"])
        if has_lint:
            lint_present += 1

    add_check(
        "lintErrors count or lintResult present per result",
        lint_present == 5,
        f"{lint_present}/5 results have lint error information",
        weight=1.0
    )

    # ---- CHECK 10: commonmark style + emphasisStyle underscore ----
    # Inspect formatted markdown content for underscore emphasis usage
    # The messy files have *text* and **text** - with underscore style they should become _text_ and __text__
    formatted_contents = []
    for res in results:
        if not isinstance(res, dict):
            continue
        for k in ["formattedMarkdown", "formatted", "content", "formattedContent"]:
            if k in res and isinstance(res[k], str):
                formatted_contents.append(res[k])
                break

    # Also check the on-disk written files
    legacy_paths = [
        os.path.join(workspace, "docs/legacy/v1/device-overview.md"),
        os.path.join(workspace, "docs/legacy/v1/installation-guide.md"),
        os.path.join(workspace, "docs/legacy/v2/api-reference.md"),
        os.path.join(workspace, "docs/legacy/v2/calibration-procedure.md"),
        os.path.join(workspace, "docs/current/reference/release-notes.md"),
    ]

    disk_contents = []
    for p in legacy_paths:
        try:
            with open(p, "r", encoding="utf-8") as f:
                disk_contents.append(f.read())
        except Exception:
            pass

    all_contents = formatted_contents + disk_contents

    # Check: underscore emphasis means _word_ patterns appear (not eliminated entirely)
    # and that there are no stray lone * used for emphasis (but * for lists is ok)
    # We look for _..._ usage in emphasis context in at least 3 out of the contents
    underscore_emphasis_count = 0
    for content in all_contents:
        # Check for underscore single emphasis _text_ patterns
        import re
        # Look for _word(s)_ pattern used for emphasis (not inside code blocks)
        # Remove code blocks first
        no_code = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
        no_code = re.sub(r'`[^`]+`', '', no_code)
        if re.search(r'(?<!\w)_[^_\n]+_(?!\w)', no_code):
            underscore_emphasis_count += 1

    # We check formatted_contents specifically (from the report)
    report_underscore_count = 0
    for content in formatted_contents:
        import re
        no_code = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
        no_code = re.sub(r'`[^`]+`', '', no_code)
        if re.search(r'(?<!\w)_[^_\n]+_(?!\w)', no_code):
            report_underscore_count += 1

    # style field in report
    style_commonmark = False
    if isinstance(report, dict):
        style_val = report.get("style", report.get("styleGuide", ""))
        if "commonmark" in str(style_val).lower():
            style_commonmark = True
    # Also check individual results
    for res in results:
        if isinstance(res, dict):
            style_val = res.get("style", res.get("styleGuide", ""))
            if "commonmark" in str(style_val).lower():
                style_commonmark = True

    emphasis_check_passed = report_underscore_count >= 3 or (style_commonmark and report_underscore_count >= 2)
    add_check(
        "commonmark style used with emphasisStyle underscore evidence",
        emphasis_check_passed,
        f"Found underscore emphasis in {report_underscore_count}/5 formatted contents in report. style_commonmark={style_commonmark}",
        weight=3.0
    )

    # ---- CHECK 11: listStyle dash - no asterisk or plus list markers ----
    import re
    dash_list_check_count = 0
    for content in formatted_contents:
        no_code = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
        # Check that there are no * or + list markers (lines starting with "* " or "+ ")
        has_asterisk_list = bool(re.search(r'^\* ', no_code, re.MULTILINE))
        has_plus_list = bool(re.search(r'^\+ ', no_code, re.MULTILINE))
        has_dash_list = bool(re.search(r'^- ', no_code, re.MULTILINE))
        if not has_asterisk_list and not has_plus_list and has_dash_list:
            dash_list_check_count += 1

    add_check(
        "listStyle dash applied (only dash markers, no asterisk or plus list markers)",
        dash_list_check_count >= 3,
        f"{dash_list_check_count}/5 formatted contents use only dash list markers",
        weight=2.0
    )

    # ---- CHECK 12: headingStyle atx (no setext headings) ----
    atx_check_count = 0
    for content in formatted_contents:
        # setext headings are lines followed by === or --- underlines
        has_setext = bool(re.search(r'^.+\n[=\-]{3,}', content, re.MULTILINE))
        if not has_setext:
            atx_check_count += 1

    add_check(
        "headingStyle atx applied (no setext underline-style headings in output)",
        atx_check_count >= 4,
        f"{atx_check_count}/5 formatted contents have no setext headings (ATX-only)",
        weight=2.0
    )

    # ---- CHECK 13: Formatted docs written back to original paths ----
    modified_count = 0
    for p in legacy_paths:
        try:
            with open(p, "r", encoding="utf-8") as f:
                content = f.read()
            # Check that trailing whitespace lines have been removed (original had "   " at end of lines)
            lines_with_trailing = [l for l in content.split('\n') if l != l.rstrip()]
            # Also check that setext headings are gone (files had them)
            has_setext = bool(re.search(r'^.+\n[=\-]{3,}', content, re.MULTILINE))
            # For installation-guide and calibration-procedure, setext should be gone
            if p.endswith("installation-guide.md") or p.endswith("calibration-procedure.md"):
                if not has_setext and len(lines_with_trailing) < 3:
                    modified_count += 1
            else:
                if len(lines_with_trailing) < 3:
                    modified_count += 1
        except Exception:
            pass

    add_check(
        "Formatted documents written back to original file paths",
        modified_count >= 4,
        f"{modified_count}/5 original legacy files appear to have been reformatted (reduced trailing whitespace, setext headings converted)",
        weight=2.0
    )

    # ---- Final scoring ----
    score = total_score / max_score if max_score > 0 else 0.0

    # Must pass the critical checks: file exists, valid JSON, 5 results, formatting evidence
    critical_passed = (
        report_exists and
        has_5_results and
        docs_found_count >= 4 and
        (emphasis_check_passed or dash_list_check_count >= 3 or atx_check_count >= 4)
    )

    return {
        "passed": critical_passed and score >= 0.6,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))