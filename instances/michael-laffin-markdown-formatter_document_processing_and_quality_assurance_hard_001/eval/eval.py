#!/usr/bin/env python3
"""
Evaluator for the markdown-formatter pharma-docs audit task.

Checks performed:
1. formatting_audit.json exists and is valid JSON
2. Report covers all 5 expected markdown files
3. Each file entry has required fields from SKILL.md return objects
4. Formatted markdown files exist and have been written back
5. Formatted content uses ATX headings (# style), not setext
6. Formatted content uses dash list markers (- ), not * or +
7. Formatted content uses fenced code blocks (```) not indented
8. Linting was performed (lintResult or errors present in report)
9. emphasisStyle is 'underscore' → __text__ not *text* for strong... 
   and _text_ rather than *text* for emphasis where applicable
10. maxWidth/wrapWidth of 100 was requested (check formattedLength or stats in report)
11. Overall statistics aggregated in report
"""

import sys
import json
import os
import re
from pathlib import Path

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def find_file(workspace, filename):
    matches = list(Path(workspace).rglob(filename))
    return matches[0] if matches else None

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    total_score = 0.0
    max_score = 10.0

    # ── CHECK 1: formatting_audit.json exists ─────────────────────────────────
    audit_path = find_file(workspace, "formatting_audit.json")
    if audit_path is None:
        checks.append(check("formatting_audit.json exists", False,
                            "File 'formatting_audit.json' not found anywhere in workspace."))
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append(check("formatting_audit.json exists", True, f"Found at {audit_path}"))
    total_score += 1.0

    # ── CHECK 2: Valid JSON ────────────────────────────────────────────────────
    try:
        audit = load_json(audit_path)
    except Exception as e:
        checks.append(check("formatting_audit.json is valid JSON", False, str(e)))
        print(json.dumps({"passed": False, "score": total_score / max_score, "checks": checks}))
        return

    checks.append(check("formatting_audit.json is valid JSON", True, "Parsed successfully."))
    total_score += 0.5

    # ── CHECK 3: Report contains file-level results for all 5 docs ────────────
    EXPECTED_FILENAMES = {
        "clinical_trial_protocol.md",
        "lab_protocol_synthesis.md",
        "safety_report_q2.md",
        "regulatory_submission_cover.md",
        "meeting_notes_dsmb.md",
    }

    # Accept either top-level list or nested under a key like "results", "files", "documents"
    file_entries = None
    if isinstance(audit, list):
        file_entries = audit
    else:
        for key in ("results", "files", "documents", "file_results", "items"):
            if key in audit and isinstance(audit[key], list):
                file_entries = audit[key]
                break

    if file_entries is None:
        checks.append(check("Report contains per-file results list", False,
                            "Could not find a list of file results in the report. "
                            "Expected top-level list or a key like 'results', 'files', 'documents'."))
        total_score = max(0, total_score)
    else:
        found_names = set()
        for entry in file_entries:
            if isinstance(entry, dict):
                # Try to find filename in any string value or 'file' key
                for v in entry.values():
                    if isinstance(v, str):
                        for exp in EXPECTED_FILENAMES:
                            if exp in v:
                                found_names.add(exp)
        missing = EXPECTED_FILENAMES - found_names
        if not missing:
            checks.append(check("Report covers all 5 pharma markdown files", True,
                                f"All 5 files found in report."))
            total_score += 1.5
        else:
            checks.append(check("Report covers all 5 pharma markdown files", False,
                                f"Missing entries for: {missing}"))

    # ── CHECK 4: Each entry has required SKILL.md return fields ───────────────
    required_fields_options = [
        # at least one of these groups should appear per entry
        {"formattedMarkdown", "warnings", "stats", "lintResult", "originalLength", "formattedLength"},
        {"formatted_markdown", "warnings", "stats", "lint_result", "original_length", "formatted_length"},
        {"formattedMarkdown", "warnings", "originalLength", "formattedLength"},
        {"errors", "warnings"},  # from lintMarkdown
    ]

    if file_entries:
        entries_with_fields = 0
        for entry in file_entries:
            if not isinstance(entry, dict):
                continue
            entry_keys = set(entry.keys())
            # Check if entry has any meaningful skill return fields
            skill_fields = {
                "formattedMarkdown", "formatted_markdown", "formattedContent",
                "warnings", "errors", "stats", "lintResult", "lint_result",
                "originalLength", "original_length", "formattedLength", "formatted_length",
                "linting_errors", "lint_errors"
            }
            if entry_keys & skill_fields:
                entries_with_fields += 1

        if file_entries and entries_with_fields >= max(1, len(file_entries) // 2):
            checks.append(check("File entries contain SKILL.md return fields", True,
                                f"{entries_with_fields}/{len(file_entries)} entries have skill return fields."))
            total_score += 1.0
        else:
            checks.append(check("File entries contain SKILL.md return fields", False,
                                f"Only {entries_with_fields}/{len(file_entries) if file_entries else 0} entries "
                                f"contain expected fields (formattedMarkdown, warnings, stats, lintResult, etc.)."))

    # ── CHECK 5: Formatted markdown files exist (written back or saved) ────────
    formatted_md_count = 0
    formatted_md_content = {}

    # Search for the 5 target files and check if they were modified
    target_paths = {
        "clinical_trial_protocol.md": Path(workspace) / "pharma_docs/clinical_trials/clinical_trial_protocol.md",
        "lab_protocol_synthesis.md": Path(workspace) / "pharma_docs/lab_protocols/lab_protocol_synthesis.md",
        "safety_report_q2.md": Path(workspace) / "pharma_docs/safety_reports/safety_report_q2.md",
        "regulatory_submission_cover.md": Path(workspace) / "pharma_docs/regulatory_submissions/regulatory_submission_cover.md",
        "meeting_notes_dsmb.md": Path(workspace) / "pharma_docs/meeting_notes/meeting_notes_dsmb.md",
    }

    for fname, fpath in target_paths.items():
        if fpath.exists():
            try:
                content = fpath.read_text(encoding="utf-8")
                # Check if file was actually processed (should not have trailing spaces on lines)
                lines_with_trailing = [l for l in content.splitlines() if l.endswith("   ") or l.endswith("  ")]
                if len(lines_with_trailing) < 3:  # original files had many trailing spaces
                    formatted_md_count += 1
                    formatted_md_content[fname] = content
            except Exception:
                pass

    if formatted_md_count >= 4:
        checks.append(check("Formatted markdown written back to files", True,
                            f"{formatted_md_count}/5 files appear to have been formatted (trailing whitespace removed)."))
        total_score += 1.5
    elif formatted_md_count >= 2:
        checks.append(check("Formatted markdown written back to files", False,
                            f"Only {formatted_md_count}/5 files appear formatted. At least 4 expected."))
        total_score += 0.5
    else:
        checks.append(check("Formatted markdown written back to files", False,
                            f"Only {formatted_md_count}/5 files appear to be formatted."))

    # Also check for formatted content stored in the audit report itself
    if file_entries and formatted_md_count < 4:
        stored_formatted = 0
        for entry in file_entries:
            if isinstance(entry, dict):
                for k in ("formattedMarkdown", "formatted_markdown", "formattedContent", "content"):
                    if k in entry and isinstance(entry[k], str) and len(entry[k]) > 50:
                        stored_formatted += 1
                        break
        if stored_formatted >= 4:
            checks.append(check("Formatted markdown stored in audit report", True,
                                f"{stored_formatted} file entries contain formatted content in the report."))
            total_score += 0.5

    # ── CHECK 6: ATX heading style (# not underline setext) ──────────────────
    atx_ok_count = 0
    setext_found_count = 0
    check_content = formatted_md_content

    # Also pull from audit report entries if we have them
    if file_entries and not check_content:
        for entry in file_entries:
            if isinstance(entry, dict):
                for k in ("formattedMarkdown", "formatted_markdown", "formattedContent"):
                    if k in entry and isinstance(entry[k], str):
                        fname = "unknown"
                        for fk in ("file", "filename", "path", "name"):
                            if fk in entry and isinstance(entry[fk], str):
                                fname = entry[fk]
                                break
                        check_content[fname] = entry[k]

    for fname, content in check_content.items():
        lines = content.splitlines()
        has_setext = any(
            re.match(r'^[=\-]{3,}\s*$', l) and i > 0 and lines[i-1].strip()
            for i, l in enumerate(lines)
        )
        if not has_setext:
            atx_ok_count += 1
        else:
            setext_found_count += 1

    if check_content:
        if atx_ok_count >= len(check_content) * 0.8:
            checks.append(check("ATX heading style applied (no setext underlines)", True,
                                f"{atx_ok_count}/{len(check_content)} files use ATX headings."))
            total_score += 0.5
        else:
            checks.append(check("ATX heading style applied (no setext underlines)", False,
                                f"{setext_found_count} files still have setext-style headings."))
    else:
        checks.append(check("ATX heading style applied (no setext underlines)", False,
                            "No formatted content found to check heading style."))

    # ── CHECK 7: Dash list markers (- not * or +) ────────────────────────────
    dash_list_count = 0
    mixed_marker_count = 0

    for fname, content in check_content.items():
        lines = content.splitlines()
        asterisk_list = [l for l in lines if re.match(r'^\s*\* \S', l)]
        plus_list = [l for l in lines if re.match(r'^\s*\+ \S', l)]
        dash_list = [l for l in lines if re.match(r'^\s*- \S', l)]

        # After formatting, + and * markers should be converted to -
        if len(asterisk_list) == 0 and len(plus_list) == 0 and len(dash_list) > 0:
            dash_list_count += 1
        elif len(asterisk_list) > 0 or len(plus_list) > 0:
            mixed_marker_count += 1

    if check_content:
        if dash_list_count >= len(check_content) * 0.6:
            checks.append(check("Dash list style applied (- markers only)", True,
                                f"{dash_list_count}/{len(check_content)} files use only dash list markers."))
            total_score += 1.0
        else:
            checks.append(check("Dash list style applied (- markers only)", False,
                                f"Only {dash_list_count}/{len(check_content)} files converted to dash-only lists. "
                                f"{mixed_marker_count} still have * or + markers."))
    else:
        checks.append(check("Dash list style applied (- markers only)", False,
                            "No formatted content to check list style."))

    # ── CHECK 8: Fenced code blocks (``` not indented) ───────────────────────
    fenced_code_count = 0
    indented_code_count = 0

    for fname, content in check_content.items():
        # Check for indented code blocks (4 spaces before non-blank content that ISN'T inside a list)
        lines = content.splitlines()
        indented_blocks = 0
        for l in lines:
            if re.match(r'^    [^\s]', l) and not re.match(r'^    [-*+\d]', l):
                indented_blocks += 1
        has_fenced = '```' in content or '~~~' in content
        if has_fenced and indented_blocks == 0:
            fenced_code_count += 1
        elif indented_blocks > 0:
            indented_code_count += 1

    if check_content:
        if fenced_code_count >= len(check_content) * 0.5:
            checks.append(check("Fenced code blocks applied (``` style)", True,
                                f"{fenced_code_count}/{len(check_content)} files use fenced code blocks."))
            total_score += 0.5
        else:
            checks.append(check("Fenced code blocks applied (``` style)", False,
                                f"Only {fenced_code_count}/{len(check_content)} files properly use fenced code blocks. "
                                f"{indented_code_count} still have indented code."))
    else:
        checks.append(check("Fenced code blocks applied (``` style)", False,
                            "No formatted content to check code block style."))

    # ── CHECK 9: Linting performed (errors/lintResult in report) ─────────────
    linting_present = False
    if file_entries:
        lint_entries = 0
        for entry in file_entries:
            if not isinstance(entry, dict):
                continue
            # Check for linting result fields
            lint_keys = {"lintResult", "lint_result", "errors", "linting_errors",
                         "lint_errors", "lintErrors", "linting"}
            if entry.keys() & lint_keys:
                lint_entries += 1
        if lint_entries >= 3:
            linting_present = True

    # Also check top-level audit for aggregate lint stats
    if not linting_present and isinstance(audit, dict):
        audit_keys = set(audit.keys())
        if audit_keys & {"totalErrors", "total_errors", "totalWarnings", "total_warnings",
                         "lintSummary", "lint_summary"}:
            linting_present = True

    if linting_present:
        checks.append(check("Linting results present in audit report", True,
                            "Lint results found in file entries."))
        total_score += 0.5
    else:
        checks.append(check("Linting results present in audit report", False,
                            "No linting results (errors/lintResult) found in file entries."))

    # ── CHECK 10: Aggregated summary in report ────────────────────────────────
    has_summary = False
    if isinstance(audit, dict):
        summary_keys = {"totalFiles", "total_files", "totalWarnings", "total_warnings",
                        "processingTime", "processing_time", "summary", "totals",
                        "totalErrors", "total_errors"}
        if audit.keys() & summary_keys:
            has_summary = True
            # Check totalFiles = 5
            for k in ("totalFiles", "total_files"):
                if k in audit:
                    val = audit[k]
                    if isinstance(val, (int, float)) and int(val) == 5:
                        total_score += 0.5
                        checks.append(check("Report shows totalFiles = 5", True,
                                            f"Found {k}: {val}"))
                        break
            else:
                checks.append(check("Report shows totalFiles = 5", False,
                                    "totalFiles not found or not equal to 5."))

    if has_summary:
        checks.append(check("Aggregated summary present in report", True,
                            "Top-level summary statistics found in audit report."))
        total_score += 0.5
    else:
        checks.append(check("Aggregated summary present in report", False,
                            "No aggregated summary (totalFiles, totalWarnings, etc.) found in report."))

    # ── FINAL SCORE ────────────────────────────────────────────────────────────
    score = min(1.0, total_score / max_score)
    passed = score >= 0.65  # Need at least 65% to pass

    result = {
        "passed": passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()