#!/usr/bin/env python3
"""
Evaluation script for the weekly-report-skill task.
Usage: python3 eval_script.py /workspace
"""

import sys
import json
import re
from pathlib import Path

def find_report(workspace: Path) -> Path | None:
    """Search for weekly_report.md anywhere in the workspace."""
    candidates = list(workspace.rglob("weekly_report.md"))
    return candidates[0] if candidates else None


def run_checks(workspace: Path):
    checks = []

    # ── Check 0: file exists ─────────────────────────────────────────────
    report_path = find_report(workspace)
    file_exists = report_path is not None
    checks.append({
        "name": "weekly_report.md exists",
        "passed": file_exists,
        "detail": str(report_path) if file_exists else "File 'weekly_report.md' not found anywhere under workspace."
    })
    if not file_exists:
        return checks

    # ── Read content ─────────────────────────────────────────────────────
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file readable", "passed": False, "detail": str(e)})
        return checks

    # ── Check 1: Title line matches proprietary format ───────────────────
    # Must be: # <name> (YYYY.MM.DD-MM.DD)
    title_pattern = re.compile(
        r'^#\s+.+\s*\(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\)',
        re.MULTILINE
    )
    title_match = title_pattern.search(content)
    checks.append({
        "name": "title has correct proprietary date format YYYY.MM.DD-MM.DD",
        "passed": bool(title_match),
        "detail": f"Found: {title_match.group(0)!r}" if title_match else "No H1 title matching '# ... (YYYY.MM.DD-MM.DD)' found."
    })

    # ── Check 2: week 2025.03.31-04.06 in title ──────────────────────────
    week_pattern = re.compile(r'\(2025\.03\.31-04\.06\)')
    week_match = week_pattern.search(content)
    checks.append({
        "name": "title contains the correct reporting week (2025.03.31-04.06)",
        "passed": bool(week_match),
        "detail": "Found correct week string '(2025.03.31-04.06)' in title." if week_match else "Week '(2025.03.31-04.06)' not found in title."
    })

    # ── Check 3: Required H2 sections present ────────────────────────────
    required_sections = ["## 本周工作总结", "## 关键指标", "## 下周计划", "## 风险与问题"]
    all_sections_present = all(sec in content for sec in required_sections)
    missing = [s for s in required_sections if s not in content]
    checks.append({
        "name": "all four required H2 sections present",
        "passed": all_sections_present,
        "detail": "All sections present." if all_sections_present else f"Missing: {missing}"
    })

    # ── Check 4: v3.5 subsection with actual data values ─────────────────
    v35_section = re.search(r'### v3\.5 生产部署器(.+?)###', content, re.DOTALL)
    v35_ok = False
    v35_detail = "v3.5 subsection not found."
    if v35_section:
        v35_text = v35_section.group(1)
        # Expect: 50 runs, 35.2 avg_likes, 75% accuracy (from data/v35_stats.json)
        has_runs     = "50" in v35_text
        has_likes    = "35.2" in v35_text
        has_accuracy = "75" in v35_text
        v35_ok = has_runs and has_likes and has_accuracy
        v35_detail = (
            f"runs=50:{has_runs}, avg_likes=35.2:{has_likes}, accuracy=75:{has_accuracy}"
        )
    checks.append({
        "name": "v3.5 section contains correct data values (50 runs, 35.2 likes, 75% accuracy)",
        "passed": v35_ok,
        "detail": v35_detail
    })

    # ── Check 5: InStreet subsection with actual data values ─────────────
    instreet_section = re.search(r'### InStreet 自动回复(.+?)##', content, re.DOTALL)
    instreet_ok = False
    instreet_detail = "InStreet subsection not found."
    if instreet_section:
        it = instreet_section.group(1)
        has_total   = "156" in it
        has_success = "91" in it
        has_morning = "12" in it
        instreet_ok = has_total and has_success and has_morning
        instreet_detail = f"total=156:{has_total}, success=91%:{has_success}, morning=12:{has_morning}"
    checks.append({
        "name": "InStreet section contains correct data values (156 replies, 91%, 12 activations)",
        "passed": instreet_ok,
        "detail": instreet_detail
    })

    # ── Check 6: Metrics table is present and has pipe-table syntax ───────
    table_pattern = re.compile(r'\|.+\|.+\|.+\|.+\|', re.MULTILINE)
    table_matches = table_pattern.findall(content)
    has_table = len(table_matches) >= 3  # header + separator + at least 2 data rows
    checks.append({
        "name": "关键指标 pipe-table has at least 3 rows (header+sep+data)",
        "passed": has_table,
        "detail": f"Found {len(table_matches)} pipe-table rows." if table_matches else "No pipe-table rows found."
    })

    # ── Check 7: Next-week plan uses checkbox syntax ─────────────────────
    checkbox_pattern = re.compile(r'- \[ \]', re.MULTILINE)
    checkboxes = checkbox_pattern.findall(content)
    has_checkboxes = len(checkboxes) >= 2
    checks.append({
        "name": "下周计划 contains at least 2 checkbox items '- [ ]'",
        "passed": has_checkboxes,
        "detail": f"Found {len(checkboxes)} checkbox items."
    })

    # ── Check 8: 生成时间 timestamp footer present ────────────────────────
    timestamp_pattern = re.compile(r'生成时间:\s*\d{4}-\d{2}-\d{2}')
    ts_match = timestamp_pattern.search(content)
    checks.append({
        "name": "report footer contains '生成时间: YYYY-MM-DD' timestamp",
        "passed": bool(ts_match),
        "detail": f"Found: {ts_match.group(0)!r}" if ts_match else "'生成时间' timestamp not found."
    })

    # ── Check 9: --output flag used (not stdout redirect) ─────────────────
    # Verify the file is NOT at /tmp/report.md (agent must use custom path)
    # and the script was called with --output flag by checking a non-default path.
    # We can't directly verify HOW it was called, but we can check it's not
    # the default temp path from quick-start docs.
    is_default_tmp = (str(report_path) == "/tmp/report.md")
    checks.append({
        "name": "report saved as 'weekly_report.md' (not the generic /tmp/report.md)",
        "passed": not is_default_tmp,
        "detail": f"Report at: {report_path}"
    })

    return checks


def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = run_checks(workspace)
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 3)
    overall = passed_count == total

    result = {
        "passed": overall,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()