import sys
import json
import re
from pathlib import Path
from datetime import date

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    # ── Locate boss_run.txt anywhere in workspace ─────────────────────────
    candidates = list(workspace.rglob("boss_run.txt"))
    
    file_found = len(candidates) > 0
    checks.append({
        "name": "boss_run.txt exists",
        "passed": file_found,
        "detail": f"Found at: {candidates[0]}" if file_found else "boss_run.txt not found anywhere in workspace"
    })
    
    if not file_found:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }
    
    try:
        content = candidates[0].read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "boss_run.txt readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({
        "name": "boss_run.txt readable",
        "passed": True,
        "detail": f"File size: {len(content)} chars"
    })
    
    # ── Check 1: --format desktop is used (keyword "卡片" → desktop) ─────
    # The user asked for "卡片" style → must use --format desktop
    has_format_desktop = bool(re.search(r'--format\s+desktop', content))
    # Also accept if 'desktop' appears as an argument value near 'format'
    has_format_desktop_alt = 'desktop' in content and ('format' in content or '--format' in content)
    desktop_passed = has_format_desktop or has_format_desktop_alt
    checks.append({
        "name": "--format desktop used (卡片 keyword → desktop format)",
        "passed": desktop_passed,
        "detail": (
            f"Found '--format desktop' in content" if has_format_desktop
            else f"Found 'desktop' with 'format' reference" if has_format_desktop_alt
            else f"Neither '--format desktop' nor 'desktop' with format context found. Content snippet: {content[:500]}"
        )
    })
    
    # ── Check 2: --report-type weekly is used ─────────────────────────────
    has_weekly = bool(re.search(r'--report-type\s+weekly', content))
    has_weekly_alt = 'weekly' in content.lower() and ('report' in content.lower() or 'report-type' in content.lower())
    weekly_passed = has_weekly or has_weekly_alt
    checks.append({
        "name": "--report-type weekly used",
        "passed": weekly_passed,
        "detail": (
            "Found '--report-type weekly'" if has_weekly
            else "Found 'weekly' with report context" if has_weekly_alt
            else f"'--report-type weekly' not found. Content snippet: {content[:500]}"
        )
    })
    
    # ── Check 3: --limit 50 is used ───────────────────────────────────────
    has_limit = bool(re.search(r'--limit\s+50', content))
    limit_passed = has_limit
    checks.append({
        "name": "--limit 50 used",
        "passed": limit_passed,
        "detail": (
            "Found '--limit 50'" if has_limit
            else f"'--limit 50' not found. Content snippet: {content[:500]}"
        )
    })
    
    # ── Check 4: Report content is present (not just the command) ─────────
    # The agent must have read the generated report and included it
    report_markers = [
        "综合评分",
        "性格特质深度分析",
        "技术能力图谱",
        "老板总结",
        "龙虾养人类",
    ]
    sections_found = [m for m in report_markers if m in content]
    report_content_passed = len(sections_found) >= 4
    checks.append({
        "name": "Report content included (at least 4 of 5 key sections present)",
        "passed": report_content_passed,
        "detail": f"Found sections: {sections_found} ({len(sections_found)}/5)"
    })
    
    # ── Check 5: Report is substantial (≥ 1500 chars of content) ──────────
    substantial = len(content) >= 1500
    checks.append({
        "name": "boss_run.txt has substantial content (≥1500 chars)",
        "passed": substantial,
        "detail": f"Content length: {len(content)} chars"
    })
    
    # ── Check 6: The generated report file exists on disk ─────────────────
    today_str = date.today().isoformat()
    expected_report = workspace / ".openclaw" / "workspace" / "reports" / f"user-profile-{today_str}.md"
    # Also check via glob in case date differs slightly
    report_files = list((workspace / ".openclaw" / "workspace" / "reports").glob("user-profile-*.md"))
    report_file_exists = expected_report.exists() or len(report_files) > 0
    checks.append({
        "name": "Generated report file exists in reports/ directory",
        "passed": report_file_exists,
        "detail": (
            f"Found: {expected_report}" if expected_report.exists()
            else f"Found via glob: {report_files[0]}" if report_files
            else f"No user-profile-*.md found in reports/ directory"
        )
    })
    
    # ── Check 7: desktop-specific ASCII art present (桌面版 indicator) ─────
    # Desktop format has the box-drawing characters ┌──...─┐
    has_ascii_box = bool(re.search(r'[┌└├│]', content))
    checks.append({
        "name": "Desktop ASCII art card present in output (box-drawing chars)",
        "passed": has_ascii_box,
        "detail": (
            "Found box-drawing characters indicating desktop ASCII card"
            if has_ascii_box
            else "No box-drawing characters found; desktop card may be missing"
        )
    })
    
    # ── Scoring ────────────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks)
    
    # Must pass core checks to be considered overall passing
    core_checks = [
        "boss_run.txt exists",
        "--format desktop used (卡片 keyword → desktop format)",
        "--report-type weekly used",
        "--limit 50 used",
        "Report content included (at least 4 of 5 key sections present)",
    ]
    core_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in core_checks
    )
    
    return {
        "passed": core_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))