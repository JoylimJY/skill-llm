#!/usr/bin/env python3
"""
Evaluation script for the PR triage task.
Checks that triage_report.md was correctly generated with:
- Proper duplicate groups (same-issue → score=100, file+keyword weighted → ≥75)
- Correct quality grades (including -5 FIRST_TIME_CONTRIBUTOR penalty)
- Stale PRs section
- Top-5 quality PRs limit respected
- Repository name in header
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime, timezone

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []
    total_score = 0.0

    # ── Load ground truth ──────────────────────────────────────────────────────
    try:
        gt = json.loads((workspace / ".eval_data" / "ground_truth.json").read_text())
        pairs = gt["pairs"]           # list of [pr1, pr2, score]
        quality = gt["quality_scores"]  # {str(number): {score, grade}}
        stale = gt["stale_prs"]       # list of PR numbers
        threshold = gt["threshold"]   # 75
        top_n = gt["top_n"]           # 5
        repo = gt["repo"]             # dataflow-org/etl-pipeline
    except Exception as e:
        checks.append({"name": "load_ground_truth", "passed": False, "detail": str(e)})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # ── Find report file ───────────────────────────────────────────────────────
    report_path = None
    try:
        candidates = list(workspace.rglob("triage_report.md"))
        if candidates:
            report_path = candidates[0]
    except Exception as e:
        pass

    if not report_path or not report_path.exists():
        checks.append({
            "name": "report_file_exists",
            "passed": False,
            "detail": "triage_report.md not found anywhere in workspace"
        })
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({
        "name": "report_file_exists",
        "passed": True,
        "detail": f"Found at {report_path}"
    })
    total_score += 5.0

    try:
        report = report_path.read_text()
    except Exception as e:
        checks.append({"name": "report_readable", "passed": False, "detail": str(e)})
        print(json.dumps({"passed": False, "score": total_score, "checks": checks}))
        return

    # ── Check 1: Repository mentioned in report ────────────────────────────────
    repo_in_report = repo.lower() in report.lower() or "etl-pipeline" in report.lower() or "dataflow" in report.lower()
    checks.append({
        "name": "repo_name_in_report",
        "passed": repo_in_report,
        "detail": f"Expected '{repo}' to appear in report header"
    })
    if repo_in_report:
        total_score += 5.0

    # ── Check 2: Same-issue duplicate group (PRs 101 & 102, score=100) ────────
    # Both reference Fixes/Closes #55, so same_issue=True → score=100 (above threshold 75)
    same_issue_group_found = False
    try:
        # Both PR numbers should appear in the report and near each other
        has_101 = "#101" in report or "101" in report
        has_102 = "#102" in report or "102" in report
        # They should be in a duplicate group section
        dup_section_match = re.search(
            r'(?i)duplicate',
            report
        )
        same_issue_group_found = has_101 and has_102 and dup_section_match is not None
    except Exception as e:
        same_issue_group_found = False

    checks.append({
        "name": "same_issue_duplicate_group_101_102",
        "passed": same_issue_group_found,
        "detail": "PRs #101 and #102 both reference issue #55 (same_issue→score=100) and must appear together in Duplicate Groups section"
    })
    if same_issue_group_found:
        total_score += 20.0

    # ── Check 3: File+keyword overlap duplicate group (PRs 201 & 202) ─────────
    # file_sim = 3/4 = 0.75 (3 shared files out of 4+4-3=5... wait let me recompute)
    # PR201 files: postgres.py, base_connector.py, retry_utils.py, test_postgres_retry.py
    # PR202 files: postgres.py, base_connector.py, retry_utils.py, pg_pool.py
    # intersection = 3, union = 5, file_sim = 3/5 = 0.6
    # keywords: need to check actual computed value from ground truth
    file_overlap_dup_found = False
    try:
        # Find the actual similarity score for (201, 202) from ground truth
        score_201_202 = None
        for p in pairs:
            if set([p[0], p[1]]) == {201, 202}:
                score_201_202 = p[2]
                break

        if score_201_202 is not None and score_201_202 >= threshold:
            has_201 = "#201" in report or "201" in report
            has_202 = "#202" in report or "202" in report
            dup_section = re.search(r'(?i)duplicate', report) is not None
            file_overlap_dup_found = has_201 and has_202 and dup_section
        else:
            # Score below threshold - they shouldn't be flagged as duplicates
            # This is still valid behavior
            file_overlap_dup_found = True  # Not applicable, give credit
            checks.append({
                "name": "file_overlap_duplicate_group_201_202",
                "passed": True,
                "detail": f"Score {score_201_202} is below threshold {threshold} - correctly not flagged"
            })
            total_score += 15.0
            # Skip rest of this check
            score_201_202 = None  # sentinel

        if score_201_202 is not None:
            checks.append({
                "name": "file_overlap_duplicate_group_201_202",
                "passed": file_overlap_dup_found,
                "detail": f"PRs #201 and #202 have file+keyword similarity score={score_201_202} (threshold={threshold}). Expected in duplicate section: {file_overlap_dup_found}"
            })
            if file_overlap_dup_found:
                total_score += 15.0
    except Exception as e:
        checks.append({
            "name": "file_overlap_duplicate_group_201_202",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # ── Check 4: Quality grades computed correctly ─────────────────────────────
    # Key grades to verify:
    # PR 401 (frank_lead, MEMBER): body>50(+10), fixes #88(+15), test file(+20), <100 lines(+10), labels(+5), recent(+10) = 70 → Grade A
    # PR 403 (newuser123, FIRST_TIME_CONTRIBUTOR): body≤50(0), no issue ref(0), no tests(0), <100 lines(+10), no labels(0), recent(+10), FIRST_TIME(-5) = 15 → Grade D
    # PR 102 (bob_newbie, FIRST_TIME_CONTRIBUTOR): body≤50(0), closes #55(+15), no test(0), <100 lines(+10), no labels(0), recent(+10), FIRST_TIME(-5) = 30 → Grade C

    grade_checks = [
        (401, "A", "frank_lead MEMBER with tests, issue ref, labels, recent, <100 lines"),
        (403, "D", "FIRST_TIME_CONTRIBUTOR with no description, no tests, no labels → -5 penalty → 15pts"),
        (102, "C", "FIRST_TIME_CONTRIBUTOR with issue ref but no tests → 30pts"),
    ]

    grades_passed = 0
    for pr_num, expected_grade, detail in grade_checks:
        # Look for grade in report
        # Patterns like "Grade A", "| A |", "(Grade A)", "A (quality)"
        # and the PR number nearby
        grade_pattern = re.compile(
            rf'#?{pr_num}[^\n]*(?:Grade\s+{expected_grade}|[\|]\s*{expected_grade}\s*[\|])'
            rf'|(?:Grade\s+{expected_grade}|[\|]\s*{expected_grade}\s*[\|])[^\n]*#?{pr_num}',
            re.IGNORECASE
        )
        # Also check quality summary section
        summary_pattern = re.compile(
            rf'[\|]\s*{expected_grade}\s*[\|][^\n]*{pr_num}|{pr_num}[^\n]*[\|]\s*{expected_grade}\s*[\|]',
            re.IGNORECASE
        )
        grade_found = bool(grade_pattern.search(report)) or bool(summary_pattern.search(report))

        # Fallback: check if grade appears in report at all near the PR number
        if not grade_found:
            # Look for PR number and grade in same table row (within 200 chars)
            pr_positions = [m.start() for m in re.finditer(rf'\b{pr_num}\b', report)]
            for pos in pr_positions:
                context = report[max(0, pos-100):pos+200]
                if re.search(rf'\b{expected_grade}\b', context):
                    grade_found = True
                    break

        checks.append({
            "name": f"quality_grade_pr_{pr_num}",
            "passed": grade_found,
            "detail": f"PR #{pr_num} expected Grade {expected_grade} ({detail}). grade_found={grade_found}"
        })
        if grade_found:
            grades_passed += 1
            total_score += 10.0

    # ── Check 5: Stale PRs section ─────────────────────────────────────────────
    # PR 301 updated 2024-01-10 = 64 days before 2024-03-15 → stale
    stale_section_found = False
    stale_pr_mentioned = False
    try:
        stale_section_found = bool(re.search(r'(?i)stale', report))
        stale_pr_mentioned = "301" in report
    except:
        pass

    checks.append({
        "name": "stale_prs_section",
        "passed": stale_section_found,
        "detail": "Report must contain a Stale PRs section"
    })
    if stale_section_found:
        total_score += 10.0

    checks.append({
        "name": "stale_pr_301_mentioned",
        "passed": stale_pr_mentioned,
        "detail": "PR #301 (64 days old) must appear in stale PRs section"
    })
    if stale_pr_mentioned:
        total_score += 10.0

    # ── Check 6: Top N limit applied ──────────────────────────────────────────
    # --top 5 means only top 5 PRs shown in report (by quality score)
    # With 7 total PRs, if the report shows all 7 in the main quality summary it violates --top 5
    # Top 5 by quality score (excluding the two lowest):
    # We check that the report doesn't list MORE than top_n PRs in the quality summary
    # Actually, per SKILL.md "Only show top N PRs in report (default: all)"
    # So we check the report has at most top_n+2 PR number mentions in non-duplicate sections
    # (some slack for section headers etc.)
    top_n_check = False
    try:
        # Count unique PR numbers mentioned in the report
        all_pr_nums_in_report = set(int(m) for m in re.findall(r'\b(1\d\d|2\d\d|3\d\d|4\d\d)\b', report)
                                    if m in {'101','102','201','202','301','401','402','403'})
        # The report may mention duplicate PRs in the duplicate section separately from main listing
        # Core check: there should be a "top" filtering effect visible
        # We verify the report has a reasonable number of entries, not all 8
        # Since --top 5 limits to top 5 quality, we expect ≤ 7 PR mentions total
        # (5 in main + 2 from duplicate group shown for context)
        # Relaxed: just verify the report was generated with top constraint awareness
        # Hard check: low-quality PRs (like #403 Grade D) may be excluded from "Ready to Merge"
        # Actually --top N applies to the whole report content shown
        # Let's check: the report has at most top_n distinct PRs mentioned in quality summary
        # We'll look for the quality summary table
        quality_section = re.search(r'Quality Summary.*?(?=##|\Z)', report, re.DOTALL | re.IGNORECASE)
        if quality_section:
            q_text = quality_section.group(0)
            prs_in_quality = set(int(m) for m in re.findall(r'\b(101|102|201|202|301|401|402|403)\b', q_text))
            # With 7 PRs and top 5, at most 5 should appear
            top_n_check = len(prs_in_quality) <= top_n + 1  # +1 slack
        else:
            # If no separate quality section, just verify report exists with meaningful content
            top_n_check = len(report) > 200
    except Exception as e:
        top_n_check = False

    checks.append({
        "name": "top_n_limit_applied",
        "passed": top_n_check,
        "detail": f"--top {top_n} should limit PRs shown in quality summary to at most {top_n}"
    })
    if top_n_check:
        total_score += 10.0

    # ── Check 7: Ready to Merge section ───────────────────────────────────────
    # PR 401 is Grade A, no duplicates → should appear in "Ready to Merge"
    ready_section = False
    pr401_ready = False
    try:
        ready_section = bool(re.search(r'(?i)ready.to.merge|ready for merge|merge.ready', report))
        if ready_section:
            ready_match = re.search(r'(?i)ready.to.merge.*?(?=##|\Z)', report, re.DOTALL)
            if ready_match:
                pr401_ready = "401" in ready_match.group(0)
    except:
        pass

    checks.append({
        "name": "ready_to_merge_section",
        "passed": ready_section,
        "detail": "Report must contain a 'Ready to Merge' section for high quality non-duplicate PRs"
    })
    if ready_section:
        total_score += 5.0

    checks.append({
        "name": "pr401_in_ready_to_merge",
        "passed": pr401_ready,
        "detail": "PR #401 (Grade A, no duplicates) should appear in Ready to Merge section"
    })
    if pr401_ready:
        total_score += 5.0

    # ── Check 8: First-time contributor penalty applied ────────────────────────
    # PR 403 must be Grade D (15 pts). If agent ignores FIRST_TIME_CONTRIBUTOR penalty,
    # it would be Grade C (20 pts). This is the key proprietary trap.
    # We already checked grade above; add an extra explicit check.
    pr403_grade_d_enforced = False
    try:
        # Verify PR 403 does NOT appear as Grade C or higher
        pr403_positions = [m.start() for m in re.finditer(r'\b403\b', report)]
        pr403_is_C_or_higher = False
        for pos in pr403_positions:
            ctx = report[max(0, pos-150):pos+150]
            if re.search(r'\b[ABC]\b', ctx):
                pr403_is_C_or_higher = True
                break
        pr403_grade_d_enforced = not pr403_is_C_or_higher
    except:
        pr403_grade_d_enforced = False

    checks.append({
        "name": "first_time_contributor_penalty_applied_pr403",
        "passed": pr403_grade_d_enforced,
        "detail": "PR #403 by FIRST_TIME_CONTRIBUTOR must be Grade D (15 pts), not C/B/A. Agent must apply -5 penalty."
    })
    if pr403_grade_d_enforced:
        total_score += 5.0

    # ── Final scoring ──────────────────────────────────────────────────────────
    max_score = 100.0
    normalized_score = min(total_score / max_score, 1.0)
    all_passed = all(c["passed"] for c in checks)

    print(json.dumps({
        "passed": all_passed and normalized_score >= 0.6,
        "score": round(normalized_score, 3),
        "checks": checks
    }, indent=2))


if __name__ == "__main__":
    main()