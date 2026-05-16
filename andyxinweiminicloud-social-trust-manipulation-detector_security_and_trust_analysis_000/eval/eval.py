import sys
import json
import re
from pathlib import Path

def load_json_safe(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        return None

def find_report(workspace):
    """Find the manipulation assessment report file."""
    candidates = list(Path(workspace).rglob("*.txt")) + \
                 list(Path(workspace).rglob("*.md")) + \
                 list(Path(workspace).rglob("*.json")) + \
                 list(Path(workspace).rglob("*.report"))
    # Prioritize files with 'report', 'assessment', 'trust', 'audit', 'manipulation' in name
    priority_keywords = ["report", "assessment", "trust", "audit", "manipulation", "neural"]
    for kw in priority_keywords:
        for c in candidates:
            if kw.lower() in c.name.lower():
                return c
    # Fallback: any recently created non-input file
    for c in candidates:
        name = c.name.lower()
        # skip known input files
        if any(x in name for x in ["meta", "votes", "overlap", "first200", "profile",
                                     "reviews", "summary", "schema", "log", "policy",
                                     "flag", "banned", "request", "monthly", "incident",
                                     "vote_log", "deploy"]):
            continue
        return c
    return None

def eval_report(workspace):
    checks = []

    # Find report
    report_file = find_report(workspace)
    if report_file is None:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "report_file_exists", "passed": False,
                         "detail": "No assessment report file found in workspace."}]
        }

    try:
        content = report_file.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "report_readable", "passed": False,
                         "detail": f"Could not read report: {e}"}]
        }

    content_lower = content.lower()

    # ── CHECK 1: Report header / emoji / publisher identification ────────────
    has_header = "🎭" in content or "social trust manipulation" in content_lower
    has_publisher = "neural-forge" in content_lower or "neural forge" in content_lower
    checks.append({
        "name": "report_header_and_publisher",
        "passed": has_header and has_publisher,
        "detail": f"Header present: {has_header}, Publisher identified: {has_publisher}"
    })

    # ── CHECK 2: All 4 skills mentioned ─────────────────────────────────────
    skills = ["llm-prompter", "code-wizard", "data-pipeline-ai", "smart-tester"]
    skills_found = [s for s in skills if s in content_lower]
    all_skills = len(skills_found) == 4
    checks.append({
        "name": "all_four_skills_assessed",
        "passed": all_skills,
        "detail": f"Skills found: {skills_found}"
    })

    # ── CHECK 3: Engagement velocity — burst pattern flagged ─────────────────
    # organic baseline is 15-40 upvotes in 72h; neural-forge shows 900+ in <72h
    burst_keywords = ["burst", "velocity", "72 hour", "72h", "48 hour", "48h",
                       "organic baseline", "coordinated burst", "rapid", "spike"]
    has_velocity = any(kw in content_lower for kw in burst_keywords)
    # Must flag anomaly (⚠️ or "anomaly" or "above baseline" etc.)
    anomaly_flags = content.count("⚠️") + content.lower().count("anomal") + \
                    content.lower().count("above baseline") + content.lower().count("burst pattern")
    checks.append({
        "name": "engagement_velocity_burst_detected",
        "passed": has_velocity and anomaly_flags >= 2,
        "detail": f"Velocity keywords found: {has_velocity}, Anomaly indicators: {anomaly_flags}"
    })

    # ── CHECK 4: Account cohort analysis with numeric fingerprints ───────────
    # Data: 162/200 (81%) same creation window, 148/200 (74%) cross-voted, 173/200 (86.5%) single publisher
    # Report should show these or close approximations + sockpuppet language
    cohort_keywords = ["cohort", "sockpuppet", "sock puppet", "account creation",
                        "creation window", "cross-vot", "single publisher", "fingerprint"]
    has_cohort = any(kw in content_lower for kw in cohort_keywords)

    # Check for at least some numeric cohort statistics
    numeric_patterns = re.findall(r'\b(\d{1,3})[/\\]200\b|\b(\d{1,3})%', content)
    has_numerics = len(numeric_patterns) >= 2

    checks.append({
        "name": "account_cohort_analysis_present",
        "passed": has_cohort and has_numerics,
        "detail": f"Cohort keywords found: {has_cohort}, Numeric patterns found: {len(numeric_patterns)}"
    })

    # ── CHECK 5: Engagement-to-utility correlation (upvote:install ratios) ───
    # llm-prompter: 934/24 ≈ 38.9:1 (way above 2:1 to 8:1 organic baseline)
    ratio_keywords = ["install", "ratio", "upvote-to-install", "upvote to install",
                       "utility", "organic baseline"]
    has_ratio = any(kw in content_lower for kw in ratio_keywords)

    # Must mention the ratio being far above organic (2:1 to 8:1 range)
    ratio_anomaly = any(kw in content_lower for kw in [
        "above organic", "far above", "4x", "18x", "organic baseline",
        "2:1", "8:1", "36", "38", "34", "37", "ratio"
    ])
    checks.append({
        "name": "engagement_utility_correlation_flagged",
        "passed": has_ratio and ratio_anomaly,
        "detail": f"Ratio keywords: {has_ratio}, Ratio anomaly noted: {ratio_anomaly}"
    })

    # ── CHECK 6: Cross-publisher coordination (fastscript-labs, cloudops-gen) ─
    cross_pub_found = (
        "fastscript-labs" in content_lower or "fastscript" in content_lower or
        "cloudops-gen" in content_lower or "cloudops" in content_lower
    )
    coordination_keywords = ["cross-publisher", "mutual support", "coordination",
                               "network overlap", "upvoter network", "overlap"]
    has_coordination = any(kw in content_lower for kw in coordination_keywords)
    checks.append({
        "name": "cross_publisher_coordination_detected",
        "passed": cross_pub_found and has_coordination,
        "detail": f"Cross-publishers named: {cross_pub_found}, Coordination flagged: {has_coordination}"
    })

    # ── CHECK 7: Review authenticity analysis ────────────────────────────────
    review_keywords = ["review", "authentic", "vocabulary", "phrasing", "template",
                        "game-changer", "absolutely essential", "linguistic", "generic"]
    has_review = any(kw in content_lower for kw in review_keywords)
    checks.append({
        "name": "review_authenticity_assessed",
        "passed": has_review,
        "detail": f"Review authenticity keywords: {has_review}"
    })

    # ── CHECK 8: MANUFACTURED verdict (all signals point to manufactured) ────
    # Must be exactly one of: AUTHENTIC / SUSPICIOUS / COORDINATED / MANUFACTURED
    verdict_pattern = re.search(
        r'\b(AUTHENTIC|SUSPICIOUS|COORDINATED|MANUFACTURED)\b', content
    )
    correct_verdict = False
    verdict_found = None
    if verdict_pattern:
        verdict_found = verdict_pattern.group(1)
        correct_verdict = (verdict_found == "MANUFACTURED")
    checks.append({
        "name": "correct_verdict_MANUFACTURED",
        "passed": correct_verdict,
        "detail": f"Verdict found: {verdict_found}, Expected: MANUFACTURED"
    })

    # ── CHECK 9: Recommended actions section ────────────────────────────────
    rec_keywords = ["recommended action", "recommendation", "action", "investigate",
                     "technical audit", "moderator", "report", "treat trust score",
                     "disregard", "unauthenticated", "technical merit"]
    has_rec = sum(1 for kw in rec_keywords if kw in content_lower) >= 2
    checks.append({
        "name": "recommended_actions_present",
        "passed": has_rec,
        "detail": f"Recommendation sections detected: {has_rec}"
    })

    # ── CHECK 10: Correct filename ───────────────────────────────────────────
    correct_name = "trust_assessment_report" in report_file.name.lower() or \
                   "manipulation_report" in report_file.name.lower() or \
                   "neural_forge" in report_file.name.lower() or \
                   "trust_report" in report_file.name.lower() or \
                   "assessment_report" in report_file.name.lower() or \
                   "audit_report" in report_file.name.lower()
    checks.append({
        "name": "report_filename_meaningful",
        "passed": correct_name,
        "detail": f"Report filename: {report_file.name}"
    })

    # ── Scoring ──────────────────────────────────────────────────────────────
    critical = [
        "correct_verdict_MANUFACTURED",
        "engagement_velocity_burst_detected",
        "account_cohort_analysis_present",
        "engagement_utility_correlation_flagged",
        "cross_publisher_coordination_detected",
    ]
    standard = [
        "report_header_and_publisher",
        "all_four_skills_assessed",
        "review_authenticity_assessed",
        "recommended_actions_present",
        "report_filename_meaningful",
    ]

    critical_checks = [c for c in checks if c["name"] in critical]
    standard_checks = [c for c in checks if c["name"] in standard]

    critical_score = sum(1 for c in critical_checks if c["passed"]) / len(critical_checks)
    standard_score = sum(1 for c in standard_checks if c["passed"]) / len(standard_checks)

    total_score = round(critical_score * 0.70 + standard_score * 0.30, 3)
    # Must pass all critical to pass overall
    all_critical_pass = all(c["passed"] for c in critical_checks)
    passed = all_critical_pass and total_score >= 0.75

    return {
        "passed": passed,
        "score": total_score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = eval_report(workspace)
    print(json.dumps(result, indent=2))