#!/usr/bin/env python3
"""
Evaluation script for the issue-prioritizer skill task.
Checks that the agent produced a correct issue_report.md with proper scoring.
"""
import sys
import json
import re
import math
from pathlib import Path

def find_report(workspace: str) -> Path | None:
    ws = Path(workspace)
    candidates = list(ws.rglob("issue_report.md"))
    if candidates:
        return candidates[0]
    # Also accept issue-report.md or similar
    for pat in ["issue-report.md", "report.md", "issues_report.md"]:
        found = list(ws.rglob(pat))
        if found:
            return found[0]
    return None

def normalize_title(title: str) -> set:
    """Remove punctuation, lowercase, split to words for fuzzy matching."""
    stop = {"the", "a", "an", "to", "for", "of", "in", "on", "with", "and", "or", "is", "be", "as"}
    words = re.sub(r"[^a-z0-9\s]", " ", title.lower()).split()
    return {w for w in words if w not in stop and len(w) > 1}

def check_issue_present(content: str, issue_num: int) -> bool:
    """Check if issue number appears in content."""
    return bool(re.search(rf'#?{issue_num}\b', content))

def check_issue_in_section(content: str, section_keywords: list, issue_num: int) -> bool:
    """
    Check if issue_num appears within a section identified by keywords.
    Scans for the first section header matching keywords, then looks for issue_num
    before the next section header (line starting with #, ═, or ---).
    """
    lines = content.split('\n')
    in_section = False
    section_start = -1

    for i, line in enumerate(lines):
        line_upper = line.upper()
        if any(kw.upper() in line_upper for kw in section_keywords):
            in_section = True
            section_start = i
            continue
        if in_section and section_start >= 0:
            # Check for next section boundary
            stripped = line.strip()
            is_boundary = (
                (stripped.startswith('═') and len(stripped) > 5) or
                (stripped.startswith('#') and len(stripped) > 1) or
                (stripped.startswith('---') and len(stripped) > 5)
            )
            if is_boundary and i > section_start + 1:
                # End of section, didn't find it
                in_section = False
                section_start = -1
            elif re.search(rf'#?{issue_num}\b', line):
                return True
    return False

def extract_adjusted_score(content: str, issue_num: int) -> float | None:
    """Try to extract AdjustedScore for an issue from the report."""
    # Look for patterns like: #30 ... Adj: 3.00 or AdjustedScore: 3.00 or [Adj: 3.00]
    patterns = [
        rf'#?{issue_num}[^\n]*\[Adj:\s*([\d.]+)\]',
        rf'#?{issue_num}[^\n]*Adj[^\n:]*:\s*([\d.]+)',
        rf'\b{issue_num}\b[^\n]*score[^\n:]*:\s*([\d.]+)',
    ]
    for pat in patterns:
        m = re.search(pat, content, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                pass
    return None

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    total_score = 0.0
    max_score = 0.0

    def add_check(name: str, passed: bool, detail: str, weight: float = 1.0):
        nonlocal total_score, max_score
        checks.append({"name": name, "passed": passed, "detail": detail})
        max_score += weight
        if passed:
            total_score += weight

    # ── 1. File existence ─────────────────────────────────────────────────────
    report_path = find_report(workspace)
    file_exists = report_path is not None
    add_check(
        "report_file_exists",
        file_exists,
        f"Found: {report_path}" if file_exists else "issue_report.md not found anywhere in workspace",
        weight=2.0
    )

    if not file_exists:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }
        print(json.dumps(result, indent=2))
        return

    try:
        content = report_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        add_check("report_readable", False, f"Cannot read file: {e}", weight=2.0)
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}, indent=2))
        return

    add_check("report_readable", True, f"File read successfully, {len(content)} chars", weight=0.5)

    # ── 2. Markdown format ────────────────────────────────────────────────────
    is_markdown = (
        bool(re.search(r'\|.+\|', content)) or     # table rows
        bool(re.search(r'^#+\s', content, re.M)) or # headings
        bool(re.search(r'^\*\*', content, re.M)) or # bold
        bool(re.search(r'^\s*[-*]\s', content, re.M)) # list items
    )
    add_check(
        "markdown_format",
        is_markdown,
        "Output uses markdown formatting (tables, headers, or lists)" if is_markdown
        else "Output does not appear to be markdown format",
        weight=1.0
    )

    # ── 3. Correct repository reference ───────────────────────────────────────
    has_repo = bool(re.search(r'datapipe-org/datapipe-cli', content, re.IGNORECASE))
    add_check(
        "correct_repository",
        has_repo,
        "Repository datapipe-org/datapipe-cli referenced in report" if has_repo
        else "Repository name not found in report",
        weight=1.0
    )

    # ── 4. PR-excluded issues (#10 and #20) ───────────────────────────────────
    # Both issues should be excluded from main analysis (they have linked PRs)
    # Check they appear in an "excluded" or "existing PRs" section

    # First check they appear somewhere in the report at all
    issue10_present = check_issue_present(content, 10)
    issue20_present = check_issue_present(content, 20)

    add_check(
        "excluded_issue_10_mentioned",
        issue10_present,
        f"Issue #10 (has explicit PR link via 'fixes #10') appears in report: {issue10_present}",
        weight=1.5
    )
    add_check(
        "excluded_issue_20_mentioned",
        issue20_present,
        f"Issue #20 (has title-similar PR) appears in report: {issue20_present}",
        weight=1.5
    )

    # Check they appear in excluded section
    excluded_keywords = ["EXCLUDED", "EXISTING PR", "existing prs", "PR already", "already pr", "linked pr", "with prs"]
    excl10 = check_issue_in_section(content, excluded_keywords, 10)
    excl20 = check_issue_in_section(content, excluded_keywords, 20)

    add_check(
        "issue_10_in_excluded_section",
        excl10,
        "Issue #10 correctly placed in excluded/existing-PRs section" if excl10
        else "Issue #10 not found in excluded section (should be excluded via explicit 'fixes #10' link)",
        weight=2.0
    )
    add_check(
        "issue_20_in_excluded_section",
        excl20,
        "Issue #20 correctly placed in excluded section (title similarity to PR #102)" if excl20
        else "Issue #20 not found in excluded section (should be excluded via title similarity: PR #102 title overlaps ~80%)",
        weight=2.0
    )

    # ── 5. Quick Win: Issue #30 ───────────────────────────────────────────────
    # #30: Difficulty=2, Importance=6, ROI=3.00, Trip=1, Arch=1, Act=5
    # AdjScore = 3.00 × 1.00 × 1.00 × 1.00 = 3.00
    # Qualifies: ROI≥1.5, Diff≤5, Trip≤3, Arch≤2, Act≥4
    qw_keywords = ["QUICK WIN", "quick win", "Quick Win", "QuickWin"]
    issue30_in_qw = check_issue_in_section(content, qw_keywords, 30)
    add_check(
        "issue_30_is_quick_win",
        issue30_in_qw,
        "Issue #30 (Add --timeout flag) correctly identified as Quick Win" if issue30_in_qw
        else "Issue #30 not found in Quick Wins section (it qualifies: Diff=2, Imp=6, ROI=3.00, Trip=1, Arch=1, Act=5)",
        weight=3.0
    )

    # ── 6. Critical Bug: Issue #40 ────────────────────────────────────────────
    # #40: issueType=bug, Importance=9≥8 → Critical Bug
    cb_keywords = ["CRITICAL BUG", "Critical Bug", "critical bug", "CRITICAL"]
    issue40_in_cb = check_issue_in_section(content, cb_keywords, 40)
    add_check(
        "issue_40_is_critical_bug",
        issue40_in_cb,
        "Issue #40 (race condition / data corruption) correctly in Critical Bugs section" if issue40_in_cb
        else "Issue #40 not in Critical Bugs section (Importance=9≥8, type=bug)",
        weight=3.0
    )

    # ── 7. Tripping Issue: Issue #50 ─────────────────────────────────────────
    # #50: "rewrite from scratch", "blockchain", "experimental" → Trip=5
    trip_keywords = ["TRIPPING", "Tripping", "tripping", "TRIP"]
    issue50_in_trip = check_issue_in_section(content, trip_keywords, 50)
    add_check(
        "issue_50_is_tripping",
        issue50_in_trip,
        "Issue #50 (Rust rewrite + blockchain) correctly in Tripping Issues section" if issue50_in_trip
        else "Issue #50 not in Tripping section (has red flags: rewrite from scratch, blockchain, experimental)",
        weight=3.0
    )

    # ── 8. Over-Engineered: Issue #60 ─────────────────────────────────────────
    # #60: Arch=4 (Significant) → Over-Engineered
    oe_keywords = ["OVER-ENGINEERED", "Over-Engineered", "over-engineered", "OVER ENGINEERED", "OVERENGINEERED"]
    issue60_in_oe = check_issue_in_section(content, oe_keywords, 60)
    add_check(
        "issue_60_is_over_engineered",
        issue60_in_oe,
        "Issue #60 (validation framework) correctly in Over-Engineered section" if issue60_in_oe
        else "Issue #60 not in Over-Engineered section (Arch≥4: 6 new files, refactor entire config module)",
        weight=3.0
    )

    # ── 9. Not Actionable: Issue #70 ─────────────────────────────────────────
    # #70: question → Act=1 → Not Actionable
    na_keywords = ["NOT ACTIONABLE", "Not Actionable", "not actionable", "NON-ACTIONABLE"]
    issue70_in_na = check_issue_in_section(content, na_keywords, 70)
    add_check(
        "issue_70_not_actionable",
        issue70_in_na,
        "Issue #70 (Kubernetes question) correctly in Not Actionable section" if issue70_in_na
        else "Issue #70 not in Not Actionable section (question: 'how do I?' → Act=1)",
        weight=3.0
    )

    # ── 10. AdjustedScore for #30 (should be ~3.00) ──────────────────────────
    score30 = extract_adjusted_score(content, 30)
    if score30 is not None:
        # Expected: ROI=6/2=3.00, all multipliers 1.00 → 3.00
        expected30 = 3.00
        close30 = abs(score30 - expected30) <= 0.15
        add_check(
            "adj_score_30_correct",
            close30,
            f"Issue #30 AdjustedScore={score30:.3f}, expected≈{expected30:.2f} (ROI=6/2=3.00, all multipliers 1.00)" if close30
            else f"Issue #30 AdjustedScore={score30:.3f} too far from expected {expected30:.2f}",
            weight=2.0
        )
    else:
        add_check(
            "adj_score_30_correct",
            False,
            "Could not find AdjustedScore for issue #30 in report",
            weight=2.0
        )

    # ── 11. AdjustedScore for #50 (should be heavily penalized, < 0.10) ──────
    score50 = extract_adjusted_score(content, 50)
    if score50 is not None:
        # Expected: ROI=4/8=0.50 (or similar), Trip=5→0.40, Arch=5→0.25, Act=2→0.40
        # = 0.50 × 0.40 × 0.25 × 0.40 = 0.020
        heavily_penalized = score50 < 0.15
        add_check(
            "adj_score_50_heavily_penalized",
            heavily_penalized,
            f"Issue #50 AdjustedScore={score50:.4f} correctly heavily penalized (<0.15)" if heavily_penalized
            else f"Issue #50 AdjustedScore={score50:.4f} not sufficiently penalized (Trip=5→×0.40, Arch=5→×0.25, Act=2→×0.40)",
            weight=2.0
        )
    else:
        add_check(
            "adj_score_50_heavily_penalized",
            False,
            "Could not find AdjustedScore for issue #50 in report",
            weight=2.0
        )

    # ── 12. Issue #30 ranked higher than #40 in top list ─────────────────────
    # In any top-N ranking, #30 (AdjScore=3.00) should appear before #40 (AdjScore≈0.40)
    pos30 = content.find(f'#{30}') if f'#{30}' in content else content.find('30')
    pos40 = content.find(f'#{40}') if f'#{40}' in content else content.find('40')
    
    # More robust: find first occurrence of each issue number in a ranked context
    # Look for issue numbers in context of a score/ranking table
    ranked_matches_30 = [m.start() for m in re.finditer(rf'#30\b', content)]
    ranked_matches_40 = [m.start() for m in re.finditer(rf'#40\b', content)]
    
    if ranked_matches_30 and ranked_matches_40:
        first30 = min(ranked_matches_30)
        first40 = min(ranked_matches_40)
        correct_order = first30 < first40
        add_check(
            "ranking_order_30_before_40",
            correct_order,
            f"#30 (Adj≈3.00) appears before #40 (Adj≈0.40) in report (correct descending order)" if correct_order
            else f"#40 appears before #30 — ranking should be descending by AdjustedScore",
            weight=2.0
        )
    else:
        add_check(
            "ranking_order_30_before_40",
            False,
            f"Could not verify ranking order: #30 found={bool(ranked_matches_30)}, #40 found={bool(ranked_matches_40)}",
            weight=2.0
        )

    # ── 13. All 6 analyzed issues appear in report ───────────────────────────
    analyzed_issues = [30, 40, 50, 60, 70, 80]
    all_present = all(check_issue_present(content, n) for n in analyzed_issues)
    missing = [n for n in analyzed_issues if not check_issue_present(content, n)]
    add_check(
        "all_analyzed_issues_in_report",
        all_present,
        f"All 6 analyzed issues (#30,#40,#50,#60,#70,#80) present in report" if all_present
        else f"Missing issues from report: {missing}",
        weight=2.0
    )

    # ── 14. Count check: 6 analyzed, 2 excluded ───────────────────────────────
    # Look for "Analyzed: 6" or "6 issues" near header, and "Excluded: 2"
    analyzed_count_ok = bool(re.search(r'[Aa]nalyzed[:\s]+6\b', content)) or \
                        bool(re.search(r'\b6\s+issues?\s+analyz', content, re.I))
    excluded_count_ok = bool(re.search(r'[Ee]xcluded[:\s]+2\b', content)) or \
                        bool(re.search(r'\b2\s+issues?\s+exclu', content, re.I))
    add_check(
        "correct_analyzed_count",
        analyzed_count_ok,
        "Report shows 6 analyzed issues" if analyzed_count_ok
        else "Could not confirm 6 analyzed issues in report header/summary",
        weight=1.0
    )
    add_check(
        "correct_excluded_count",
        excluded_count_ok,
        "Report shows 2 excluded issues" if excluded_count_ok
        else "Could not confirm 2 excluded issues (both #10 via explicit link and #20 via title similarity should be excluded)",
        weight=1.0
    )

    # ── Compute final score ───────────────────────────────────────────────────
    final_score = round(total_score / max_score, 4) if max_score > 0 else 0.0
    passed = final_score >= 0.70  # 70% threshold

    result = {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()