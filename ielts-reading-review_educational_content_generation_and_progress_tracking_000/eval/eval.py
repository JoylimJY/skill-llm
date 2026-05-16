#!/usr/bin/env python3
"""
Evaluation script for IELTS Reading Review task.
Usage: python eval_script.py <workspace_dir>
"""
import sys
import json
import re
from pathlib import Path

def find_review_html(workspace: Path):
    """Find the generated HTML review file using the naming convention."""
    # Convention: 剑X-TestX-PassageX-TopicKeyword复盘.html
    # Must contain 剑17 and 复盘 and .html
    candidates = list(workspace.rglob("*.html"))
    # Filter out the template
    review_files = [
        f for f in candidates
        if "review-template" not in f.name
        and "old_template" not in f.name
        and "复盘" in f.name
        and ("剑17" in f.name or "C17" in f.name or "c17" in f.name)
    ]
    return review_files

def check_band_score(content: str) -> tuple[bool, str]:
    """
    Raw score 34 → Band 7.5 (No boundary per score-band-table.md).
    Must show 7.5 (not a range like 7.0-7.5 or 7.5-8.0).
    """
    # Look for 7.5 in band score context
    # Should NOT be a range like 6.5-7.5 or 7.5-8.0
    band_patterns = [
        r'7\.5[-–]8\.0',   # wrong: should not be range
        r'7\.0[-–]7\.5',   # wrong: should not be range
        r'7\.5',            # correct: exact 7.5
    ]
    has_range_with_75 = bool(re.search(r'7\.5[-–]\d', content) or re.search(r'\d[-–]7\.5', content))
    has_exact_75 = bool(re.search(r'7\.5', content))
    
    if has_exact_75 and not has_range_with_75:
        return True, "Band 7.5 correctly shown as exact value (score 34, no boundary)"
    elif has_range_with_75:
        return False, "Band score 7.5 incorrectly shown as a range — score 34 is not a boundary per score-band-table.md"
    else:
        return False, "Band score 7.5 not found in document"

def check_total_score(content: str) -> tuple[bool, str]:
    """Total = 13+10+11 = 34/40"""
    has_34 = bool(re.search(r'34\s*/\s*40|34/40', content))
    if has_34:
        return True, "Total score 34/40 found"
    return False, "Total score 34/40 not found in document"

def check_time_format(content: str) -> tuple[bool, str]:
    """
    Timing: P1=28:15, P2=31:44, P3=38:03
    Total = 28:15 + 31:44 + 38:03 = 98:02
    28*60+15 = 1695, 31*60+44 = 1904, 38*60+3 = 2283
    Total seconds = 1695+1904+2283 = 5882
    5882 / 60 = 98 min 2 sec => 98:02
    Must show breakdown format: 28:15+31:44+38:03=98:02
    """
    # Check for total time calculation
    total_seconds = (28*60+15) + (31*60+44) + (38*60+3)
    total_min = total_seconds // 60
    total_sec = total_seconds % 60
    expected_total = f"{total_min:02d}:{total_sec:02d}"  # "98:02"
    
    has_total = bool(re.search(r'98:02', content))
    has_breakdown = bool(re.search(r'28:15.*31:44.*38:03|28:15\+31:44\+38:03', content))
    
    if has_total and has_breakdown:
        return True, f"Time format correct: breakdown with total {expected_total}"
    elif has_total:
        return True, f"Total time {expected_total} found (breakdown format preferred but total is correct)"
    else:
        return False, f"Expected total time {expected_total} (98:02) not found. Check arithmetic: 28:15+31:44+38:03=98:02"

def check_file_naming(review_files: list) -> tuple[bool, str]:
    """File must follow: 剑X-TestX-PassageX-TopicKeyword复盘.html"""
    if not review_files:
        return False, "No review HTML file found with 剑17 and 复盘 in name"
    for f in review_files:
        name = f.name
        # Must contain 剑17, T2 or Test2, P3 or Passage3, and 复盘
        has_test = bool(re.search(r'T2|Test2|test2', name))
        has_passage = bool(re.search(r'P3|Passage3|passage3', name))
        has_jian17 = "剑17" in name
        has_review = "复盘" in name
        if has_jian17 and has_test and has_passage and has_review:
            return True, f"File naming convention correct: {name}"
    # Partial credit check
    names = [f.name for f in review_files]
    return False, f"File naming not fully following convention. Found: {names}. Expected pattern: 剑17-T2-P3-<topic>复盘.html"

def check_html_template_usage(content: str) -> tuple[bool, str]:
    """Must use review-template.html as foundation — check for CSS classes and structure."""
    checks = {
        "alert-box class": "alert-box" in content,
        "error-block class": "error-block" in content,
        "scorecard section": "scorecard" in content,
        "feedback-nudge": "feedback-nudge" in content or "GitHub" in content,
        "score-summary section": "score-summary" in content or "📌" in content,
        "error-breakdown section": "error-breakdown" in content or "❌" in content,
        "synonym section": "synonym" in content or "🔄" in content,
        "vocab section": "vocab" in content or "📝" in content,
        "recurring section": "recurring" in content or "💡" in content,
    }
    passed_count = sum(checks.values())
    total = len(checks)
    failed = [k for k, v in checks.items() if not v]
    if passed_count >= 7:
        return True, f"Template usage: {passed_count}/{total} structural elements found"
    return False, f"Template usage insufficient: {passed_count}/{total}. Missing: {failed}"

def check_sections_order(content: str) -> tuple[bool, str]:
    """Verify section order: score→errors→synonyms→vocab→mistakes→scorecard"""
    section_markers = [
        ("📌", "score summary"),
        ("❌", "error breakdown"),
        ("🔄", "synonym table"),
        ("📝", "vocabulary table"),
        ("💡", "recurring mistakes"),
        ("📊", "scorecard"),
    ]
    positions = []
    for marker, name in section_markers:
        pos = content.find(marker)
        positions.append((pos, name, marker))
    
    found = [(pos, name) for pos, name, _ in positions if pos != -1]
    if len(found) < 5:
        missing = [name for pos, name, _ in positions if pos == -1]
        return False, f"Only {len(found)}/6 section markers found. Missing: {missing}"
    
    # Check order
    found_sorted = sorted(found, key=lambda x: x[0])
    found_names = [name for _, name in found_sorted]
    expected_names = [name for _, name in found]
    if found_names == expected_names:
        return True, f"All {len(found)} sections found in correct order"
    return False, f"Sections found but order may be wrong. Found order: {found_names}"

def check_synonym_table_columns(content: str) -> tuple[bool, str]:
    """Column order: 原文表达 | 题目表达 | 中文释义 | 题号"""
    has_passage_expr = "原文表达" in content or ("passage" in content.lower() and "expression" in content.lower())
    has_question_expr = "题目表达" in content
    has_chinese = "中文释义" in content or "释义" in content
    has_qnum = "题号" in content
    
    if has_passage_expr and has_question_expr and has_chinese and has_qnum:
        # Check relative order
        p1 = content.find("原文表达")
        p2 = content.find("题目表达")
        p3 = max(content.find("中文释义"), content.find("释义"))
        p4 = content.find("题号")
        if p1 < p2 < p3 < p4:
            return True, "Synonym table columns in correct order: 原文表达→题目表达→中文释义→题号"
        return False, f"Synonym table columns present but order wrong (positions: {p1},{p2},{p3},{p4})"
    missing = []
    if not has_passage_expr: missing.append("原文表达")
    if not has_question_expr: missing.append("题目表达")
    if not has_chinese: missing.append("释义")
    if not has_qnum: missing.append("题号")
    return False, f"Synonym table missing columns: {missing}"

def check_vocabulary_ratings(content: str) -> tuple[bool, str]:
    """
    Check vocabulary frequency ratings from 538-keywords-guide.md:
    - innovative/innovate: Category 1 (⭐⭐⭐) — in top 54
    - ambiguity: NOT in top 54 or 171, likely ⭐ or — 
    - intrinsic: NOT in 538 list → —
    - conducive: NOT in 538 list → —
    - domain: Category 3 (⭐)
    """
    has_triple_star = "⭐⭐⭐" in content
    has_double_star = "⭐⭐" in content
    has_single_star = "⭐" in content
    has_not_listed = "—" in content or "not in" in content.lower()
    
    # Innovative is in Category 1 (top 54: "innovative" IS listed)
    innovative_rated = bool(re.search(r'innovat\w*.*⭐⭐⭐|⭐⭐⭐.*innovat\w*', content, re.IGNORECASE))
    
    if has_triple_star and (has_single_star or has_not_listed):
        detail = "Vocabulary ratings present with multiple levels"
        if innovative_rated:
            detail += ". innovative/innovate correctly rated ⭐⭐⭐"
        return True, detail
    elif has_triple_star or has_double_star or has_single_star:
        return True, "Vocabulary frequency ratings present (partial verification)"
    return False, "No vocabulary frequency ratings (⭐⭐⭐/⭐⭐/⭐/—) found in document"

def check_error_analysis_q28(content: str) -> tuple[bool, str]:
    """
    Q28: User answered NOT GIVEN, correct is FALSE.
    Error type should be D-NGvsFALSE (from error-taxonomy.md).
    Passage explicitly says participants WERE told to evaluate positively — direct contradiction.
    """
    has_q28 = bool(re.search(r'Q28|第28题|28题', content))
    has_d_type = bool(re.search(r'D-NGvsFALSE|D型|NOT GIVEN.*FALSE|FALSE.*NOT GIVEN', content, re.IGNORECASE))
    has_mueller = "Mueller" in content or "穆勒" in content
    
    if has_q28 and (has_d_type or has_mueller):
        return True, "Q28 error analysis present with correct D-NGvsFALSE classification or Mueller reference"
    elif has_q28:
        return True, "Q28 error analysis present"
    return False, "Q28 error analysis not found"

def check_error_analysis_q31(content: str) -> tuple[bool, str]:
    """
    Q31: User answered NOT GIVEN, correct is FALSE.
    Key: passage says extrinsic rewards CAN reduce performance — contradicts 'always improves'.
    Error type: D-NGvsFALSE or C-Inference.
    """
    has_q31 = bool(re.search(r'Q31|第31题|31题', content))
    has_analysis = bool(re.search(r'always|总是|extrinsic|外在|奖励|intrinsic', content, re.IGNORECASE))
    
    if has_q31 and has_analysis:
        return True, "Q31 error analysis present with relevant keywords"
    elif has_q31:
        return True, "Q31 error analysis found"
    return False, "Q31 error analysis not found"

def check_error_analysis_q32(content: str) -> tuple[bool, str]:
    """
    Q32: User answered FALSE, correct is TRUE.
    User thought 'consistently outperforms' was too extreme.
    Error type: C-Inference (over-skepticism) or B-Scope.
    Must note that 'consistently' in passage directly supports TRUE.
    """
    has_q32 = bool(re.search(r'Q32|第32题|32题', content))
    has_analysis = bool(re.search(r'brainstorm|独自|solitary|group|小组|consistently|一贯', content, re.IGNORECASE))
    
    if has_q32 and has_analysis:
        return True, "Q32 error analysis present with brainstorming/solitary reference"
    elif has_q32:
        return True, "Q32 error analysis found"
    return False, "Q32 error analysis not found"

def check_cumulative_progress_table(content: str) -> tuple[bool, str]:
    """
    Must include all 6 tests in cumulative table:
    剑4 T3, 剑4 T4, 剑5 T2, 剑5 T3, 剑5 T4, 剑17 T2 (new)
    """
    required_tests = ["剑4", "剑5", "剑17"]
    test_patterns = [
        r'剑4.*T3|C4.*T3',
        r'剑4.*T4|C4.*T4',
        r'剑5.*T2|C5.*T2',
        r'剑5.*T3|C5.*T3',
        r'剑5.*T4|C5.*T4',
        r'剑17.*T2|C17.*T2',
    ]
    found_count = 0
    found_tests = []
    for pattern in test_patterns:
        if re.search(pattern, content):
            found_count += 1
            found_tests.append(pattern.split('|')[0].replace('\\', ''))
    
    if found_count >= 5:
        return True, f"Cumulative progress table has {found_count}/6 test entries: {found_tests}"
    return False, f"Cumulative progress table incomplete: only {found_count}/6 tests found. Found: {found_tests}"

def check_progress_analysis(content: str) -> tuple[bool, str]:
    """
    Must have progress analysis after the cumulative table:
    - Accuracy trend mention
    - Speed/time analysis vs 60 min limit
    - At least one strategy suggestion
    """
    has_trend = bool(re.search(r'正确率|accuracy|trend|上升|提高|improving|进步', content, re.IGNORECASE))
    has_speed = bool(re.search(r'速度|speed|时间|time|60分钟|60 min|两倍|double', content, re.IGNORECASE))
    has_strategy = bool(re.search(r'建议|suggest|strategy|先|追|稳定|stable', content, re.IGNORECASE))
    
    passed = sum([has_trend, has_speed, has_strategy])
    if passed >= 2:
        return True, f"Progress analysis present with {passed}/3 required elements (trend, speed, strategy)"
    return False, f"Progress analysis insufficient: only {passed}/3 elements found (trend:{has_trend}, speed:{has_speed}, strategy:{has_strategy})"

def check_per_passage_scores(content: str) -> tuple[bool, str]:
    """P1=13, P2=10, P3=11 must be shown in scorecard."""
    has_p1_13 = bool(re.search(r'P1.*13|13.*P1', content))
    has_p2_10 = bool(re.search(r'P2.*10|10.*P2', content))
    has_p3_11 = bool(re.search(r'P3.*11|11.*P3', content))
    
    count = sum([has_p1_13, has_p2_10, has_p3_11])
    if count == 3:
        return True, "Per-passage scores P1=13, P2=10, P3=11 all found in scorecard"
    elif count >= 2:
        missing = []
        if not has_p1_13: missing.append("P1=13")
        if not has_p2_10: missing.append("P2=10")
        if not has_p3_11: missing.append("P3=11")
        return False, f"Per-passage scores: {count}/3 found. Missing: {missing}"
    return False, f"Per-passage scores not properly shown (P1=13, P2=10, P3=11 expected). Found: P1_13={has_p1_13}, P2_10={has_p2_10}, P3_11={has_p3_11}"

def check_feedback_nudge(content: str) -> tuple[bool, str]:
    """Must include feedback nudge with GitHub link."""
    has_github = "github.com/dengjiawei1226" in content or "GitHub" in content
    has_star = "Star" in content or "⭐" in content
    if has_github and has_star:
        return True, "Feedback nudge with GitHub link and Star present"
    elif has_github:
        return True, "Feedback nudge GitHub link present"
    return False, "Feedback nudge missing (should include GitHub link and Star encouragement)"

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "argument", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)
    
    workspace = Path(sys.argv[1])
    checks = []
    
    # ── Find the output file ────────────────────────────────────────────────
    try:
        review_files = find_review_html(workspace)
    except Exception as e:
        review_files = []
    
    # File naming check
    naming_passed, naming_detail = check_file_naming(review_files)
    checks.append({"name": "file_naming_convention", "passed": naming_passed, "detail": naming_detail})
    
    if not review_files:
        checks.append({"name": "file_exists", "passed": False, "detail": "No HTML review file found matching 剑17*复盘.html pattern"})
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    # Use the first matching file
    review_file = review_files[0]
    try:
        content = review_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": f"Could not read {review_file}: {e}"})
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    checks.append({"name": "file_exists", "passed": True, "detail": f"Review file found: {review_file.name}"})
    
    # ── Content checks ──────────────────────────────────────────────────────
    check_fns = [
        ("band_score_conversion",        check_band_score),
        ("total_score_34_40",            check_total_score),
        ("time_arithmetic_format",       check_time_format),
        ("html_template_structure",      check_html_template_usage),
        ("sections_mandatory_order",     check_sections_order),
        ("synonym_table_column_order",   check_synonym_table_columns),
        ("vocabulary_frequency_ratings", check_vocabulary_ratings),
        ("error_analysis_q28",           check_error_analysis_q28),
        ("error_analysis_q31",           check_error_analysis_q31),
        ("error_analysis_q32",           check_error_analysis_q32),
        ("per_passage_scores_scorecard", check_per_passage_scores),
        ("cumulative_progress_table",    check_cumulative_progress_table),
        ("progress_analysis_text",       check_progress_analysis),
        ("feedback_nudge",               check_feedback_nudge),
    ]
    
    for check_name, fn in check_fns:
        try:
            passed, detail = fn(content)
            checks.append({"name": check_name, "passed": passed, "detail": detail})
        except Exception as e:
            checks.append({"name": check_name, "passed": False, "detail": f"Check failed with exception: {e}"})
    
    # ── Scoring ─────────────────────────────────────────────────────────────
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])
    score = round(passed_checks / total_checks, 3)
    
    # Must pass critical checks to pass overall
    critical_checks = [
        "band_score_conversion",
        "total_score_34_40",
        "sections_mandatory_order",
        "cumulative_progress_table",
        "per_passage_scores_scorecard",
    ]
    critical_passed = all(
        any(c["name"] == cn and c["passed"] for c in checks)
        for cn in critical_checks
    )
    
    overall_passed = critical_passed and score >= 0.70
    
    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()