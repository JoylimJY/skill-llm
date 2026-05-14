import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    # Find the report file - look for any file named pr_assessment_report.md
    report_files = list(workspace.rglob("pr_assessment_report.md"))
    
    report_content = None
    report_path = None
    
    if report_files:
        report_path = report_files[0]
        try:
            report_content = report_path.read_text(encoding="utf-8")
        except Exception as e:
            checks.append({"name": "report_readable", "passed": False, "detail": f"Found file but could not read: {e}"})
    
    if not report_content:
        # Try alternative names
        alt_names = ["pr_report.md", "mergeability_report.md", "report.md", "assessment.md", "pr_412_report.md"]
        for alt in alt_names:
            candidates = list(workspace.rglob(alt))
            if candidates:
                try:
                    report_content = candidates[0].read_text(encoding="utf-8")
                    report_path = candidates[0]
                    break
                except Exception:
                    pass
    
    if not report_content:
        checks.append({
            "name": "report_exists",
            "passed": False,
            "detail": "Could not find pr_assessment_report.md or any alternative report file in workspace"
        })
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }
    
    checks.append({
        "name": "report_exists",
        "passed": True,
        "detail": f"Found report at {report_path}"
    })
    
    content_lower = report_content.lower()
    content = report_content
    
    # CHECK 1: Correct score tier — must be RED / LOW (<40%)
    red_score_present = bool(
        re.search(r'🔴', content) or 
        re.search(r':red_circle:', content_lower) or
        re.search(r'\bred\b', content_lower)
    )
    
    low_present = bool(re.search(r'\blow\b', content_lower))
    
    # Check for percentage below 40
    pct_matches = re.findall(r'(\d+)\s*%', content)
    score_below_40 = any(int(p) < 40 for p in pct_matches) if pct_matches else False
    
    score_correct = red_score_present and (low_present or score_below_40)
    checks.append({
        "name": "score_tier_red_low",
        "passed": score_correct,
        "detail": f"Red/Low tier detected: red_emoji={red_score_present}, low_keyword={low_present}, pct_below_40={score_below_40}. Percentages found: {pct_matches}"
    })
    
    # CHECK 2: Draft status flagged
    draft_flagged = bool(re.search(r'draft', content_lower))
    checks.append({
        "name": "draft_status_flagged",
        "passed": draft_flagged,
        "detail": "Report must mention draft status as a blocker"
    })
    
    # CHECK 3: LOC / size flagged (>1000 LOC = danger zone)
    loc_pattern = bool(
        re.search(r'1[,.]?(?:449|[5-9]\d{2}|\d{3,})\s*(?:loc|lines|additions|changed)', content_lower) or
        re.search(r'1\d{3,}\s*(?:loc|lines)', content_lower) or
        re.search(r'>?\s*1000\s*(?:loc|lines)', content_lower) or
        re.search(r'danger\s*zone', content_lower) or
        re.search(r'1,?449', content) or
        re.search(r'1754', content) or  # total add+del
        re.search(r'(?:large|huge|massive|oversized)\s+(?:pr|pull\s*request|change)', content_lower) or
        re.search(r'(?:reviewer\s*fatigue|too\s*large|too\s*many\s*lines)', content_lower)
    )
    checks.append({
        "name": "loc_size_flagged",
        "passed": loc_pattern,
        "detail": "Report must flag >1000 LOC as a risk factor (danger zone threshold from SKILL.md)"
    })
    
    # CHECK 4: Failed CI checks flagged
    ci_failed = bool(
        re.search(r'(?:ci|check|test|pipeline)\s*(?:fail|failing|failed|broken)', content_lower) or
        re.search(r'fail(?:ed|ing)\s+(?:ci|check|test)', content_lower) or
        re.search(r'unit.?test.*fail', content_lower) or
        re.search(r'integration.?test.*fail', content_lower) or
        re.search(r'security.?scan.*fail', content_lower) or
        re.search(r'3\s*(?:of|out of|\/)\s*5\s*(?:checks|ci)', content_lower) or
        re.search(r'(?:3|three)\s*failed?\s*(?:checks?|ci|tests?)', content_lower)
    )
    checks.append({
        "name": "failed_ci_flagged",
        "passed": ci_failed,
        "detail": "Report must flag failed CI checks (unit-tests, integration-tests, security-scan all failed)"
    })
    
    # CHECK 5: Changes requested / unaddressed review feedback flagged
    changes_requested = bool(
        re.search(r'changes?\s*requested', content_lower) or
        re.search(r'vasquez', content_lower) or
        re.search(r'unaddressed\s*(?:review|feedback|comment)', content_lower) or
        re.search(r'review\s*(?:feedback|comment).*(?:unaddressed|not\s*addressed|outstanding)', content_lower) or
        re.search(r'outstanding\s*(?:review|changes|feedback)', content_lower)
    )
    checks.append({
        "name": "changes_requested_flagged",
        "passed": changes_requested,
        "detail": "Report must flag unaddressed CHANGES_REQUESTED review from dr-elena-vasquez"
    })
    
    # CHECK 6: Do-not-merge label flagged
    label_flagged = bool(
        re.search(r'do.?not.?merge', content_lower) or
        re.search(r'blocking\s*label', content_lower) or
        re.search(r'label.*(?:do.not.merge|wip|block)', content_lower)
    )
    checks.append({
        "name": "blocking_label_flagged",
        "passed": label_flagged,
        "detail": "Report must flag 'do-not-merge' label as a blocker"
    })
    
    # CHECK 7: Staleness flagged (PR is from 2024-11-15, evaluate as >30 days old relative to any reasonable current date, 
    # or the agent should note it's been open a significant time)
    staleness_flagged = bool(
        re.search(r'stale|stall|abandon|inactive|old\s+pr|open\s+(?:for|since)', content_lower) or
        re.search(r'\d+\s*(?:days?|weeks?)\s*(?:old|open|since|ago)', content_lower) or
        re.search(r'(?:november|nov).{0,20}2024', content_lower) or
        re.search(r'no\s*(?:recent\s*)?activity', content_lower) or
        re.search(r'last\s*(?:updated|active|activity)', content_lower)
    )
    checks.append({
        "name": "staleness_flagged",
        "passed": staleness_flagged,
        "detail": "Report must flag staleness (PR open since Nov 2024, >30 days)"
    })
    
    # CHECK 8: First-time contributor / no merge history flagged
    author_history_flagged = bool(
        re.search(r'first.?time\s*contributor', content_lower) or
        re.search(r'no\s*(?:prior|previous)\s*(?:pr|merge|contribution)', content_lower) or
        re.search(r'(?:0|zero)\s*(?:prior|previous|merged)\s*(?:pr|merge)', content_lower) or
        re.search(r'merge\s*(?:rate|history).*0', content_lower) or
        re.search(r'0%\s*merge', content_lower) or
        re.search(r'nova.?contrib', content_lower)
    )
    checks.append({
        "name": "author_history_flagged",
        "passed": author_history_flagged,
        "detail": "Report must flag first-time contributor with 0% merge history"
    })
    
    # CHECK 9: CLA not signed flagged
    cla_flagged = bool(
        re.search(r'cla\b', content_lower) or
        re.search(r'contributor\s*licen[sc]e\s*agreement', content_lower) or
        re.search(r'dco\b', content_lower) or
        re.search(r'licen[sc]e.*(?:not\s*signed|missing|unsigned)', content_lower)
    )
    checks.append({
        "name": "cla_not_signed_flagged",
        "passed": cla_flagged,
        "detail": "Report must flag that CLA has not been signed"
    })
    
    # CHECK 10: CODEOWNERS signal flagged
    codeowners_flagged = bool(
        re.search(r'codeowner', content_lower) or
        re.search(r'code\s*owner', content_lower) or
        re.search(r'required\s*reviewer', content_lower)
    )
    checks.append({
        "name": "codeowners_flagged",
        "passed": codeowners_flagged,
        "detail": "Report must mention CODEOWNERS file and its implications"
    })
    
    # CHECK 11: Report has all 5 required sections
    has_score_section = bool(re.search(r'(?:mergeability\s*score|score)', content_lower))
    has_risk_section = bool(re.search(r'risk\s*factor', content_lower))
    has_strengths_section = bool(re.search(r'strength', content_lower))
    has_recommendations_section = bool(re.search(r'recommendation', content_lower))
    has_verdict_section = bool(re.search(r'verdict', content_lower))
    
    all_sections = has_score_section and has_risk_section and has_strengths_section and has_recommendations_section and has_verdict_section
    checks.append({
        "name": "all_5_sections_present",
        "passed": all_sections,
        "detail": f"Score={has_score_section}, Risk={has_risk_section}, Strengths={has_strengths_section}, Recommendations={has_recommendations_section}, Verdict={has_verdict_section}"
    })
    
    # CHECK 12: At least one strength identified (even bad PRs have some positives — lint passing, has contributing guide, etc.)
    strengths_present = bool(
        re.search(r'(?:✅|:white_check_mark:|\+)', content) and
        re.search(r'strength', content_lower)
    )
    # Be more lenient - just check the section exists with some content
    if not strengths_present:
        strengths_section_match = re.search(r'strength.*?\n(.*?)(?:\n#|\Z)', content_lower, re.DOTALL)
        if strengths_section_match:
            section_text = strengths_section_match.group(1).strip()
            strengths_present = len(section_text) > 20
    checks.append({
        "name": "strengths_section_has_content",
        "passed": strengths_present,
        "detail": "Report must identify at least one strength (e.g., lint passing, has contributing guide)"
    })
    
    # CHECK 13: Verdict is a single sentence summarizing the blocker situation
    verdict_match = re.search(r'verdict[:\s]*\n*(.*?)(?:\n#|\Z)', content_lower, re.DOTALL)
    verdict_has_content = False
    if verdict_match:
        verdict_text = verdict_match.group(1).strip()
        # Should have at least 20 chars but not be an essay (under ~500 chars for "one sentence" spirit)
        verdict_has_content = 20 < len(verdict_text) < 600
    checks.append({
        "name": "verdict_is_summary_sentence",
        "passed": verdict_has_content,
        "detail": f"Verdict section must contain a meaningful summary sentence"
    })
    
    # CHECK 14: PR reference (paycore-oss/payment-sdk#412 or similar)
    pr_referenced = bool(
        re.search(r'payment.?sdk', content_lower) or
        re.search(r'paycore', content_lower) or
        re.search(r'#412\b', content) or
        re.search(r'pull/412', content_lower)
    )
    checks.append({
        "name": "pr_correctly_identified",
        "passed": pr_referenced,
        "detail": "Report must reference the correct PR (paycore-oss/payment-sdk#412)"
    })
    
    # Scoring
    passed_checks = [c for c in checks if c["passed"]]
    total_checks = len(checks)
    score = len(passed_checks) / total_checks
    
    # Must pass the critical checks to pass overall
    critical_checks = [
        "report_exists",
        "score_tier_red_low",
        "draft_status_flagged",
        "failed_ci_flagged",
        "changes_requested_flagged",
        "blocking_label_flagged",
        "all_5_sections_present",
    ]
    
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )
    
    overall_passed = critical_passed and score >= 0.70
    
    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))