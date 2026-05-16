import sys
import json
import re
import os
from pathlib import Path
from datetime import datetime

def evaluate(workspace: str):
    checks = []
    
    # ── 1. Find the report file ──────────────────────────────────────────────
    reports_dir = Path(workspace) / "reports"
    
    report_files = list(reports_dir.glob("accessibility-review-*.md")) if reports_dir.exists() else []
    
    if not report_files:
        # Also search globally in case agent put it elsewhere
        report_files = list(Path(workspace).rglob("accessibility-review-*.md"))
    
    file_found = len(report_files) > 0
    checks.append({
        "name": "report_file_exists",
        "passed": file_found,
        "detail": f"Found {len(report_files)} report file(s): {[str(f) for f in report_files]}"
    })
    
    if not file_found:
        return {"passed": False, "score": 0.0, "checks": checks}
    
    # Use the most recently modified report
    report_path = sorted(report_files, key=lambda f: f.stat().st_mtime, reverse=True)[0]
    
    # ── 2. Check file is inside reports/ directory ───────────────────────────
    in_reports_dir = "reports" in str(report_path.parent)
    checks.append({
        "name": "report_in_reports_directory",
        "passed": in_reports_dir,
        "detail": f"Report path: {report_path}"
    })
    
    # ── 3. Check filename pattern: accessibility-review-YYYY-MM-DD-HHmmss.md ──
    fname = report_path.name
    fname_pattern = re.compile(r'^accessibility-review-\d{4}-\d{2}-\d{2}-\d{6}\.md$')
    fname_valid = bool(fname_pattern.match(fname))
    checks.append({
        "name": "report_filename_format",
        "passed": fname_valid,
        "detail": f"Filename: '{fname}', expected pattern: accessibility-review-YYYY-MM-DD-HHmmss.md"
    })
    
    # ── 4. Read report content ───────────────────────────────────────────────
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "report_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    # ── 5. Check required header metadata fields ─────────────────────────────
    has_generation_time = bool(re.search(r'生成时间', content))
    checks.append({
        "name": "header_generation_time",
        "passed": has_generation_time,
        "detail": "Report must contain '生成时间' timestamp field"
    })
    
    has_review_tool = bool(re.search(r'frontend-craft', content))
    checks.append({
        "name": "header_review_tool_frontend_craft",
        "passed": has_review_tool,
        "detail": "Report must contain '评审工具: frontend-craft' — this is a proprietary field from the skill spec"
    })
    
    has_wcag_standard = bool(re.search(r'WCAG\s*2\.1\s*AA', content))
    checks.append({
        "name": "header_wcag_standard",
        "passed": has_wcag_standard,
        "detail": "Report must reference 'WCAG 2.1 AA' standard"
    })
    
    # ── 6. Check required section headers (Chinese + emoji) ──────────────────
    has_must_fix_section = bool(re.search(r'🔴\s*必须修复', content))
    checks.append({
        "name": "section_must_fix_red",
        "passed": has_must_fix_section,
        "detail": "Report must contain '🔴 必须修复' section"
    })
    
    has_suggest_section = bool(re.search(r'🟡\s*建议改进', content))
    checks.append({
        "name": "section_suggest_yellow",
        "passed": has_suggest_section,
        "detail": "Report must contain '🟡 建议改进' section"
    })
    
    has_passed_section = bool(re.search(r'✅\s*已通过', content))
    checks.append({
        "name": "section_passed_green",
        "passed": has_passed_section,
        "detail": "Report must contain '✅ 已通过项' section"
    })
    
    has_code_suggestion_section = bool(re.search(r'建议的代码修改', content))
    checks.append({
        "name": "section_code_suggestions",
        "passed": has_code_suggestion_section,
        "detail": "Report must contain '建议的代码修改' section"
    })
    
    # ── 7. Check [文件:行号] citation format is used ─────────────────────────
    # Pattern: [some-file.html:123] or [SomeFile.js:45]
    has_file_line_citations = bool(re.search(r'\[[\w\-./]+\.\w+:\d+\]', content))
    checks.append({
        "name": "file_line_citation_format",
        "passed": has_file_line_citations,
        "detail": "Issues must cite [文件:行号] format, e.g. [patient-registration.html:23]"
    })
    
    # ── 8. Check that key WCAG violations were identified ────────────────────
    # Must detect: missing labels on form inputs
    has_label_issue = bool(re.search(
        r'(?i)(label|标签|关联|for\s*属性|htmlFor|没有.*label|缺少.*label|label.*缺失)',
        content
    ))
    checks.append({
        "name": "identified_missing_labels",
        "passed": has_label_issue,
        "detail": "Must identify missing/unassociated <label> issues on form inputs"
    })
    
    # Must detect: modal focus trap issues
    has_modal_focus_issue = bool(re.search(
        r'(?i)(modal|对话框|模态|焦点|focus|trap|捕获|aria-modal|Esc|Escape)',
        content
    ))
    checks.append({
        "name": "identified_modal_focus_issues",
        "passed": has_modal_focus_issue,
        "detail": "Must identify modal dialog focus trap / Esc key issues"
    })
    
    # Must detect: missing alt text
    has_alt_issue = bool(re.search(
        r'(?i)(alt|图片|image|img|替代文字|替换文本)',
        content
    ))
    checks.append({
        "name": "identified_alt_text_issues",
        "passed": has_alt_issue,
        "detail": "Must identify missing/empty alt text on meaningful images"
    })
    
    # Must detect: landmark/semantic HTML issues
    has_landmark_issue = bool(re.search(
        r'(?i)(landmark|地标|main|header|footer|nav|aside|语义|semantic|<div)',
        content
    ))
    checks.append({
        "name": "identified_landmark_issues",
        "passed": has_landmark_issue,
        "detail": "Must identify missing semantic landmarks (main, header, footer, nav)"
    })
    
    # Must detect: heading hierarchy issues
    has_heading_issue = bool(re.search(
        r'(?i)(heading|标题|h1|h2|h3|h4|层级|hierarchy|skip|跳级)',
        content
    ))
    checks.append({
        "name": "identified_heading_hierarchy_issues",
        "passed": has_heading_issue,
        "detail": "Must identify heading hierarchy violations (e.g., h1→h3, h2→h4)"
    })
    
    # Must detect: aria-expanded / keyboard nav issues on menu
    has_aria_expanded_issue = bool(re.search(
        r'(?i)(aria-expanded|aria.haspopup|keyboard|键盘|下拉|submenu|菜单)',
        content
    ))
    checks.append({
        "name": "identified_aria_expanded_nav_issues",
        "passed": has_aria_expanded_issue,
        "detail": "Must identify missing aria-expanded/haspopup on dropdown navigation"
    })
    
    # Must detect: aria-live for dynamic status
    has_aria_live_issue = bool(re.search(
        r'(?i)(aria-live|动态|live.region|loading|状态|status|通知)',
        content
    ))
    checks.append({
        "name": "identified_aria_live_issues",
        "passed": has_aria_live_issue,
        "detail": "Must identify missing aria-live region for loading/error status updates"
    })
    
    # Must detect: icon-only buttons/links without accessible names
    has_icon_button_issue = bool(re.search(
        r'(?i)(icon|图标|aria-label|accessible.name|可访问.*名称|名称.*可访问|纯图标)',
        content
    ))
    checks.append({
        "name": "identified_icon_only_control_issues",
        "passed": has_icon_button_issue,
        "detail": "Must identify icon-only buttons/links lacking accessible names"
    })
    
    # ── 9. Check item counts in section headers (N项) ────────────────────────
    has_counts = bool(re.search(r'[（\(]?\d+\s*项[）\)]?', content))
    checks.append({
        "name": "section_item_counts",
        "passed": has_counts,
        "detail": "Section headers should include item counts like 'N项'"
    })
    
    # ── 10. Report covers multiple source files ───────────────────────────────
    files_mentioned = set()
    for fname_match in re.finditer(r'[\w\-]+\.(html|js|jsx|ts|tsx)', content):
        files_mentioned.add(fname_match.group(0))
    
    covers_multiple_files = len(files_mentioned) >= 3
    checks.append({
        "name": "covers_multiple_source_files",
        "passed": covers_multiple_files,
        "detail": f"Report should reference at least 3 source files. Found: {sorted(files_mentioned)}"
    })
    
    # ── Score calculation ─────────────────────────────────────────────────────
    # Weight critical checks more heavily
    critical_checks = [
        "report_file_exists",
        "report_in_reports_directory",
        "report_filename_format",
        "header_review_tool_frontend_craft",
        "section_must_fix_red",
        "section_suggest_yellow",
        "file_line_citation_format",
        "identified_missing_labels",
        "identified_modal_focus_issues",
    ]
    
    check_dict = {c["name"]: c["passed"] for c in checks}
    
    critical_passed = sum(1 for name in critical_checks if check_dict.get(name, False))
    total_passed = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    
    # Score: 60% weight on critical, 40% on total
    critical_score = (critical_passed / len(critical_checks)) * 0.6
    total_score = (total_passed / total_checks) * 0.4
    score = round(critical_score + total_score, 3)
    
    # Must pass all critical checks to be considered "passing"
    all_critical_passed = all(check_dict.get(name, False) for name in critical_checks)
    passed = all_critical_passed and (total_passed / total_checks) >= 0.75
    
    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))