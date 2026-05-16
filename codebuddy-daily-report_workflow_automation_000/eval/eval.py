import sys
import json
import re
from pathlib import Path
from datetime import datetime, timedelta

def main():
    workspace = Path(sys.argv[1])
    checks = []
    
    # ── Load task metadata ────────────────────────────────────────────────
    try:
        meta = json.loads((workspace / ".task_meta.json").read_text(encoding="utf-8"))
        target_date = meta["target_date"]
    except Exception as e:
        print(json.dumps({
            "passed": False, "score": 0.0,
            "checks": [{"name": "metadata_load", "passed": False, "detail": str(e)}]
        }))
        return

    expected_filename = f"daily-report-{target_date}.md"

    # ── CHECK 1: File exists with correct name ────────────────────────────
    found_files = list(workspace.rglob(expected_filename))
    # Exclude old distractor reports in reports/ dir that already existed
    # The target file should be newly created (not in reports/ which had old dates)
    file_check_passed = len(found_files) >= 1
    checks.append({
        "name": "correct_filename",
        "passed": file_check_passed,
        "detail": f"Looking for '{expected_filename}'. Found: {[str(f) for f in found_files]}"
    })
    
    if not file_check_passed:
        # Check if agent used wrong date (today or yesterday)
        today = datetime.now().date()
        wrong_files = (
            list(workspace.rglob(f"daily-report-{today.strftime('%Y-%m-%d')}.md")) +
            list(workspace.rglob(f"daily-report-{(today - timedelta(days=1)).strftime('%Y-%m-%d')}.md"))
        )
        detail_extra = ""
        if wrong_files:
            detail_extra = f" Agent created wrong-date file(s): {[str(f) for f in wrong_files]} — likely used wrong flag (not --days-ago 2)."
        print(json.dumps({
            "passed": False, "score": 0.0,
            "checks": checks + [{"name": "wrong_date_trap", "passed": False, "detail": detail_extra}]
        }))
        return

    report_path = found_files[0]
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({"name": "file_readable", "passed": True, "detail": f"Read {len(content)} chars from {report_path}"})

    # ── CHECK 2: Report date matches target_date (前天) ───────────────────
    date_in_report = target_date in content
    checks.append({
        "name": "correct_date_in_report",
        "passed": date_in_report,
        "detail": f"Expected '{target_date}' in report. {'Found.' if date_in_report else 'Not found — agent may have used wrong date flag.'}"
    })

    # ── CHECK 3: Required section headers with emojis ─────────────────────
    required_sections = [
        ("section_overview", "## 📊 今日概览"),
        ("section_projects", "## 🔧 项目详情"),
        ("section_ai", "## 🤖 AI 辅助工作"),
        ("section_summary", "## 📝 今日总结"),
    ]
    for check_name, header in required_sections:
        found = header in content
        checks.append({
            "name": check_name,
            "passed": found,
            "detail": f"Header '{header}' {'found' if found else 'MISSING'} in report."
        })

    # ── CHECK 4: Both repos mentioned ────────────────────────────────────
    for repo_name in ["payment-gateway", "risk-engine"]:
        found = repo_name in content
        checks.append({
            "name": f"repo_{repo_name.replace('-','_')}",
            "passed": found,
            "detail": f"Repo '{repo_name}' {'found' if found else 'MISSING'} in report."
        })

    # ── CHECK 5: Commit table format (HH:MM | message) ───────────────────
    # The template requires a markdown table with 时间 | 提交说明 columns
    table_header_found = bool(re.search(r'\|\s*时间\s*\|\s*提交说明\s*\|', content))
    checks.append({
        "name": "commit_table_headers",
        "passed": table_header_found,
        "detail": f"Commit table with '时间 | 提交说明' headers {'found' if table_header_found else 'MISSING'}."
    })

    # Time in HH:MM format inside a table row
    hhmm_in_table = bool(re.search(r'\|\s*\d{2}:\d{2}\s*\|', content))
    checks.append({
        "name": "commit_time_hhmm_format",
        "passed": hhmm_in_table,
        "detail": f"Time in HH:MM format inside table {'found' if hhmm_in_table else 'MISSING — agent may have used full timestamp instead of HH:MM'}."
    })

    # ── CHECK 6: Diff stats present ───────────────────────────────────────
    # Should contain additions/deletions info derived from diff_stats fields
    diff_stats_found = bool(re.search(r'\+\d+\s*-\d+', content))
    checks.append({
        "name": "diff_stats_present",
        "passed": diff_stats_found,
        "detail": f"Diff stats (+N -M) {'found' if diff_stats_found else 'MISSING'} in report."
    })

    # ── CHECK 7: 今日概览 contains active repos count and commit count ─────
    # Payment gateway has 3 commits, risk-engine has 2 → total 5 commits, 2 repos
    overview_section = ""
    overview_match = re.search(r'## 📊 今日概览(.*?)##', content, re.DOTALL)
    if overview_match:
        overview_section = overview_match.group(1)
    
    active_repos_line = bool(re.search(r'活跃仓库.*[：:]\s*2\s*个', overview_section) or
                              re.search(r'活跃仓库.*2', overview_section))
    checks.append({
        "name": "overview_active_repos_count",
        "passed": active_repos_line,
        "detail": f"Overview shows 2 active repos: {'yes' if active_repos_line else 'no/incorrect'}."
    })

    total_commits_correct = bool(re.search(r'总提交数.*[：:]\s*5\s*次', overview_section) or
                                  re.search(r'总提交.*5', overview_section))
    checks.append({
        "name": "overview_total_commits",
        "passed": total_commits_correct,
        "detail": f"Overview shows 5 total commits: {'yes' if total_commits_correct else 'no/incorrect (expected 5 = 3+2)'}."
    })

    # ── CHECK 8: AI/Agent sessions section has content ────────────────────
    ai_section = ""
    ai_match = re.search(r'## 🤖 AI 辅助工作(.*?)## 📝', content, re.DOTALL)
    if ai_match:
        ai_section = ai_match.group(1).strip()
    
    ai_has_content = len(ai_section) > 50
    checks.append({
        "name": "ai_sessions_section_content",
        "passed": ai_has_content,
        "detail": f"AI sessions section has {'sufficient' if ai_has_content else 'insufficient/empty'} content ({len(ai_section)} chars)."
    })

    # ── CHECK 9: Summary section has content ─────────────────────────────
    summary_section = ""
    summary_match = re.search(r'## 📝 今日总结(.*?)$', content, re.DOTALL)
    if summary_match:
        summary_section = summary_match.group(1).strip()
    
    summary_has_content = len(summary_section) > 30
    checks.append({
        "name": "summary_section_content",
        "passed": summary_has_content,
        "detail": f"Summary section has {'sufficient' if summary_has_content else 'insufficient/empty'} content ({len(summary_section)} chars)."
    })

    # ── CHECK 10: Language is Chinese (not English-only) ──────────────────
    chinese_char_count = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
    is_chinese = chinese_char_count > 30
    checks.append({
        "name": "report_language_chinese",
        "passed": is_chinese,
        "detail": f"Chinese character count: {chinese_char_count}. {'Passes' if is_chinese else 'Fails'} Chinese language requirement."
    })

    # ── CHECK 11: Specific commit messages present ────────────────────────
    key_commits = [
        ("commit_idempotency", "idempotency"),
        ("commit_fraud_detection", "fraud"),
    ]
    for check_name, keyword in key_commits:
        found = keyword.lower() in content.lower()
        checks.append({
            "name": check_name,
            "passed": found,
            "detail": f"Keyword '{keyword}' {'found' if found else 'MISSING'} in report."
        })

    # ── SCORE CALCULATION ─────────────────────────────────────────────────
    # Weight critical checks more heavily
    critical_checks = {
        "correct_filename": 3,
        "correct_date_in_report": 2,
        "section_overview": 2,
        "section_projects": 2,
        "section_ai": 2,
        "section_summary": 2,
        "commit_table_headers": 2,
        "commit_time_hhmm_format": 2,
        "report_language_chinese": 2,
    }
    
    total_weight = 0
    passed_weight = 0
    for check in checks:
        w = critical_checks.get(check["name"], 1)
        total_weight += w
        if check["passed"]:
            passed_weight += w

    score = round(passed_weight / total_weight, 3) if total_weight > 0 else 0.0
    all_critical_passed = all(
        c["passed"] for c in checks
        if c["name"] in critical_checks
    )
    passed = all_critical_passed and score >= 0.75

    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()