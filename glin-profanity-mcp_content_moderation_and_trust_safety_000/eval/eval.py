import sys
import json
import os
from pathlib import Path

def run_eval(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ---- Find the output report file ----
    # The prompt asks for "moderation_audit_report.json"
    report_candidates = list(workspace.rglob("moderation_audit_report.json"))

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # CHECK 1: File exists
    if not report_candidates:
        score = add_check("report_file_exists", False, "moderation_audit_report.json not found anywhere in workspace", 2.0)
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks + [{"name": "all_remaining", "passed": False, "detail": "Skipped - report file missing"}]
        }

    report_path = report_candidates[0]
    total_score += add_check("report_file_exists", True, f"Found at {report_path}", 2.0)

    # Parse the report
    try:
        with open(report_path) as f:
            report = json.load(f)
    except Exception as e:
        total_score += add_check("report_valid_json", False, f"Failed to parse JSON: {e}", 2.0)
        return {"passed": False, "score": total_score / 20.0, "checks": checks}

    total_score += add_check("report_valid_json", True, "Valid JSON", 2.0)

    # ---- CHECK 2: Corpus statistics present ----
    # analyze_corpus or batch_check should give us total count and flagged count
    has_corpus_stats = False
    flagged_count = None
    total_count = None

    # Look for corpus-level stats in various possible structures
    corpus_section = None
    for key in ["corpus_analysis", "corpus_stats", "analysis", "statistics", "summary", "overview"]:
        if key in report:
            corpus_section = report[key]
            break

    if corpus_section is None and isinstance(report, dict):
        # Check top-level fields
        corpus_section = report

    if corpus_section:
        # Try to find total and flagged counts
        for total_key in ["total", "total_analyzed", "total_messages", "total_texts", "count"]:
            if total_key in corpus_section:
                try:
                    total_count = int(corpus_section[total_key])
                    break
                except:
                    pass
        for flagged_key in ["flagged", "flagged_count", "violations", "violation_count", "profane_count", "detected"]:
            if flagged_key in corpus_section:
                try:
                    flagged_count = int(corpus_section[flagged_key])
                    break
                except:
                    pass

    # The input has 35 messages total, with clearly profane ones being >=6 (explicit profanity)
    # and obfuscated adding more - we expect total_count to be around 35 and flagged >= 6
    corpus_stats_present = (total_count is not None and flagged_count is not None)
    total_score += add_check(
        "corpus_statistics_present",
        corpus_stats_present,
        f"total_count={total_count}, flagged_count={flagged_count}",
        2.0
    )

    if corpus_stats_present:
        # Total should be plausible (we generated ~35 messages, could be slightly different)
        total_plausible = 25 <= total_count <= 50
        total_score += add_check(
            "corpus_total_count_plausible",
            total_plausible,
            f"total_count={total_count} (expected 25-50 range for the chat log)",
            1.0
        )
        # Flagged should be > 0 and < total
        flagged_plausible = 0 < flagged_count < total_count
        total_score += add_check(
            "corpus_flagged_count_plausible",
            flagged_plausible,
            f"flagged_count={flagged_count} (should be >0 and <total)",
            1.0
        )
    else:
        total_score += add_check("corpus_total_count_plausible", False, "Corpus stats missing", 1.0)
        total_score += add_check("corpus_flagged_count_plausible", False, "Corpus stats missing", 1.0)

    # ---- CHECK 3: High-risk / repeat offender users identified ----
    # u_1003, u_1007, u_1010 are the clear repeat offenders
    expected_offenders = {"u_1003", "u_1007", "u_1010"}

    high_risk_section = None
    for key in ["high_risk_users", "repeat_offenders", "flagged_users", "violations_by_user", "users", "offenders"]:
        if key in report:
            high_risk_section = report[key]
            break

    # Also search nested
    if high_risk_section is None:
        def deep_find(obj, keys, depth=0):
            if depth > 4:
                return None
            if isinstance(obj, dict):
                for k in keys:
                    if k in obj:
                        return obj[k]
                for v in obj.values():
                    result = deep_find(v, keys, depth + 1)
                    if result is not None:
                        return result
            return None
        high_risk_section = deep_find(report, ["high_risk_users", "repeat_offenders", "flagged_users", "offenders"])

    found_offenders = set()
    if high_risk_section:
        # Could be a list of user objects or dict
        if isinstance(high_risk_section, list):
            for item in high_risk_section:
                if isinstance(item, dict):
                    for uid_key in ["user_id", "userId", "id", "user"]:
                        if uid_key in item:
                            found_offenders.add(str(item[uid_key]))
                            break
                elif isinstance(item, str):
                    found_offenders.add(item)
        elif isinstance(high_risk_section, dict):
            found_offenders = set(high_risk_section.keys())

    # Check all 3 known repeat offenders are identified
    all_offenders_found = expected_offenders.issubset(found_offenders)
    total_score += add_check(
        "repeat_offenders_identified",
        all_offenders_found,
        f"Found offenders: {found_offenders}, expected at least: {expected_offenders}",
        3.0
    )

    # At least 2 of 3 (partial credit check)
    partial_offenders = len(expected_offenders.intersection(found_offenders)) >= 2
    total_score += add_check(
        "repeat_offenders_partial",
        partial_offenders,
        f"At least 2/3 repeat offenders found: {found_offenders & expected_offenders}",
        1.0
    )

    # ---- CHECK 4: Strictness comparison for borderline messages ----
    # borderline_messages.json has 5 borderline messages
    # The agent should have used compare_strictness or validate_content at different levels
    strictness_section = None
    for key in ["strictness_comparison", "borderline_analysis", "strictness", "borderline", "comparison", "borderline_messages"]:
        if key in report:
            strictness_section = report[key]
            break

    if strictness_section is None:
        # Deep search
        def deep_find2(obj, keys, depth=0):
            if depth > 4:
                return None
            if isinstance(obj, dict):
                for k in keys:
                    if k in obj:
                        return obj[k]
                for v in obj.values():
                    r = deep_find2(v, keys, depth + 1)
                    if r is not None:
                        return r
            return None
        strictness_section = deep_find2(report, ["strictness_comparison", "borderline_analysis", "strictness", "comparison"])

    has_strictness = strictness_section is not None and (
        (isinstance(strictness_section, list) and len(strictness_section) > 0) or
        (isinstance(strictness_section, dict) and len(strictness_section) > 0)
    )
    total_score += add_check(
        "strictness_comparison_present",
        has_strictness,
        f"Strictness comparison section found: {type(strictness_section).__name__ if strictness_section else 'None'}",
        2.0
    )

    # Check that strictness comparison mentions at least 2 different levels
    if has_strictness:
        section_str = json.dumps(strictness_section).lower()
        level_keywords = ["low", "medium", "high", "mild", "strict", "moderate"]
        levels_mentioned = [kw for kw in level_keywords if kw in section_str]
        multiple_levels = len(levels_mentioned) >= 2
        total_score += add_check(
            "strictness_multiple_levels",
            multiple_levels,
            f"Strictness levels found in section: {levels_mentioned}",
            1.5
        )
    else:
        total_score += add_check("strictness_multiple_levels", False, "Strictness section missing", 1.5)

    # ---- CHECK 5: validate_content safety scores (0-100) present ----
    # Safety scores should appear somewhere in the report
    report_str = json.dumps(report).lower()

    # Look for numeric safety scores
    import re
    score_patterns = re.findall(r'"(?:safety_score|score|safe_score|content_score)"\s*:\s*(\d+(?:\.\d+)?)', report_str)
    has_safety_scores = len(score_patterns) > 0

    # Also look for action recommendations (approve/review/reject/block)
    action_keywords = ["approve", "reject", "review", "block", "allow", "flag", "warn"]
    actions_found = [kw for kw in action_keywords if kw in report_str]
    has_action_recs = len(actions_found) >= 1

    total_score += add_check(
        "safety_scores_in_report",
        has_safety_scores or has_action_recs,
        f"Safety scores found: {score_patterns[:5]}, Actions found: {actions_found}",
        1.5
    )

    # ---- CHECK 6: Obfuscation/leetspeak detection ----
    # u_1009 and u_1011 sent obfuscated messages like "f4ck", "@$$hole", "sh1t"
    obfuscation_keywords = ["f4ck", "sh1t", "b1tch", "obfuscat", "leetspeak", "leet", "unicode", "@$$"]
    has_obfuscation_detection = any(kw in report_str for kw in obfuscation_keywords)

    # Also check if u_1009 or u_1011 appear in violations
    obfuscation_users_flagged = "u_1009" in report_str or "u_1011" in report_str
    total_score += add_check(
        "obfuscation_detection",
        has_obfuscation_detection or obfuscation_users_flagged,
        f"Obfuscation keywords found: {has_obfuscation_detection}, Obfuscation users flagged: {obfuscation_users_flagged}",
        1.0
    )

    # ---- Final scoring ----
    max_score = 2.0 + 2.0 + 2.0 + 1.0 + 1.0 + 3.0 + 1.0 + 2.0 + 1.5 + 1.5 + 1.0
    normalized = total_score / max_score

    # Must pass core checks to pass overall
    core_checks_passed = (
        checks[0]["passed"] and  # file exists
        checks[1]["passed"] and  # valid JSON
        (checks[3]["passed"] or checks[4]["passed"]) and  # corpus stats
        (checks[7]["passed"] or checks[8]["passed"])  # offenders found
    )

    return {
        "passed": core_checks_passed and normalized >= 0.55,
        "score": round(normalized, 3),
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    result = run_eval(sys.argv[1])
    print(json.dumps(result, indent=2))