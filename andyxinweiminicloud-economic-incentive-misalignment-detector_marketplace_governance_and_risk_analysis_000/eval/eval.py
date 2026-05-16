import sys
import json
import re
from pathlib import Path

def find_report(workspace: Path):
    candidates = list(workspace.rglob("alignment_report.txt"))
    if candidates:
        return candidates[0]
    return None

def score_checks(checks):
    passed_count = sum(1 for c in checks if c["passed"])
    return round(passed_count / len(checks), 3)

def main():
    workspace = Path(sys.argv[1])
    checks = []

    report_path = find_report(workspace)
    if report_path is None:
        checks.append({"name": "report_file_exists", "passed": False, "detail": "alignment_report.txt not found anywhere in workspace"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({"name": "report_file_exists", "passed": True, "detail": f"Found at {report_path}"})

    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "report_readable", "passed": False, "detail": str(e)})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return
    checks.append({"name": "report_readable", "passed": True, "detail": "File read successfully"})

    content_lower = content.lower()

    # ── CHECK 1: Marketplace name present ────────────────────────────────────
    has_marketplace = "nexusskillhub" in content_lower
    checks.append({"name": "marketplace_name_present", "passed": has_marketplace,
                   "detail": "NexusSkillHub mentioned" if has_marketplace else "Marketplace name missing"})

    # ── CHECK 2: Publisher concentration section ──────────────────────────────
    # Top 10 publishers produce top10_total out of all_skills_30d
    # We need to recompute from gen_inputs for determinism
    # From gen: top_skills = [61,54,48,43,40,37,34,31,29,27] => top10 = 404
    # Remaining: 910 publishers with random seed 42
    import random
    random.seed(42)
    remaining_count = 910
    remaining_total = sum(random.randint(0, 4) for _ in range(remaining_count))
    top10_total = 404
    all_skills_30d = top10_total + remaining_total
    top10_pct = round(top10_total / all_skills_30d * 100, 1)

    has_concentration_section = bool(re.search(r'publisher\s+concentration', content_lower))
    checks.append({"name": "publisher_concentration_section", "passed": has_concentration_section,
                   "detail": "Publisher concentration section found" if has_concentration_section else "Missing publisher concentration section"})

    # Check that concentration percentage is approximately correct (top10 %)
    # top10_pct should be around 21-24% range given ~1630-1700 total skills
    # Let's verify the number is mentioned somewhere near publisher concentration
    pct_matches = re.findall(r'(\d{1,3}(?:\.\d+)?)\s*%', content)
    has_reasonable_pct = any(15.0 <= float(p) <= 35.0 for p in pct_matches)
    checks.append({"name": "concentration_percentage_present", "passed": has_reasonable_pct,
                   "detail": f"Found percentage values: {pct_matches[:10]}. Expected top-10 concentration ~{top10_pct}%"})

    # Check top publisher output mentioned (61 skills/30 days)
    has_top_publisher_rate = bool(re.search(r'61\s+skills|61\s*\/\s*30|2\.0\s+skills.day|2\.03|2\.1\s+skills', content_lower))
    checks.append({"name": "top_publisher_velocity_mentioned", "passed": has_top_publisher_rate,
                   "detail": "Top publisher output (61 skills/30d) mentioned" if has_top_publisher_rate else "Top publisher output not found"})

    # Check publisher count (920 total active)
    has_publisher_count = bool(re.search(r'920|1[,\s]?100|nine\s+hundred', content_lower))
    # The active publishers in data are 920 (10 + 910)
    has_publisher_count_920 = bool(re.search(r'920', content))
    checks.append({"name": "total_publisher_count", "passed": has_publisher_count_920,
                   "detail": "920 active publishers mentioned" if has_publisher_count_920 else "Expected 920 active publishers count"})

    # ── CHECK 3: Publication velocity vs review capacity ──────────────────────
    has_velocity_section = bool(re.search(r'publication\s+velocity|velocity.*review|review.*capacity|skills.*reviewer', content_lower))
    checks.append({"name": "velocity_vs_review_section", "passed": has_velocity_section,
                   "detail": "Velocity vs review capacity section found" if has_velocity_section else "Missing velocity/review section"})

    # 3210 new skills, 8 reviewers => 3210/8 = 401.25 skills per reviewer per 30 days => ~13.4/day
    # Max capacity: 8h/day / 0.75h (45min) = ~10.7 or 8h/90min = 5.3 skills/reviewer/day
    has_new_skills_count = bool(re.search(r'3[,\s]?210|3210', content))
    checks.append({"name": "new_skills_count_mentioned", "passed": has_new_skills_count,
                   "detail": "3,210 new skills published figure found" if has_new_skills_count else "3,210 new skills figure missing"})

    has_review_team = bool(re.search(r'\b8\s+reviewer|\b8\s+person|\b8\s+member|review\s+team.*\b8\b|\b8\b.*reviewer|trust.*safety.*\b8\b', content_lower))
    checks.append({"name": "review_team_size_mentioned", "passed": has_review_team,
                   "detail": "Review team size (8) mentioned" if has_review_team else "Review team size (8) not found"})

    # Skills per reviewer per day calculated? Should mention exceeds capacity
    has_capacity_exceeded = bool(re.search(r'exceed|structurally impossible|cannot.*review|review.*impossible|outpace', content_lower))
    checks.append({"name": "capacity_exceeded_assessment", "passed": has_capacity_exceeded,
                   "detail": "Conclusion that review capacity exceeded found" if has_capacity_exceeded else "Missing conclusion about capacity being exceeded"})

    # ── CHECK 4: Revenue model conflict of interest ───────────────────────────
    has_revenue_section = bool(re.search(r'revenue\s+model|conflict.*interest|per.download|transaction.*cut', content_lower))
    checks.append({"name": "revenue_model_section", "passed": has_revenue_section,
                   "detail": "Revenue model section found" if has_revenue_section else "Missing revenue model section"})

    has_perdownload = bool(re.search(r'per.download|per download', content_lower))
    checks.append({"name": "per_download_identified", "passed": has_perdownload,
                   "detail": "Per-download revenue model identified" if has_perdownload else "Per-download model not identified"})

    has_premium_placement = bool(re.search(r'premium\s+placement|featured\s+slot|\$499', content_lower))
    checks.append({"name": "premium_placement_conflict", "passed": has_premium_placement,
                   "detail": "Premium placement conflict identified" if has_premium_placement else "Premium placement issue not flagged"})

    # ── CHECK 5: Safety vs growth investment ratio ────────────────────────────
    has_safety_growth_section = bool(re.search(r'safety.*growth|safety.*investment|growth.*investment|safety.to.growth|safety.*ratio', content_lower))
    checks.append({"name": "safety_vs_growth_section", "passed": has_safety_growth_section,
                   "detail": "Safety vs growth investment section found" if has_safety_growth_section else "Missing safety vs growth section"})

    # Safety team ~9, growth ~72 => 1:8 ratio (or combined growth+product ~72+18=90 => 1:10)
    # Any ratio mentioning safety underinvestment
    has_safety_ratio = bool(re.search(r'1\s*:\s*[5-9]|1\s*:\s*1[0-9]|1:8|1:9|safety.*underinvest|underinvest.*safety', content_lower))
    checks.append({"name": "safety_growth_ratio_calculated", "passed": has_safety_ratio,
                   "detail": "Safety-to-growth ratio (expected ~1:8 or similar) found" if has_safety_ratio else "Safety-to-growth ratio calculation missing or incorrect"})

    # Industry comparable mentioned (1:2 to 1:3 for financial infrastructure or similar)
    has_industry_comparable = bool(re.search(r'1\s*:\s*2|1\s*:\s*3|industry\s*(standard|comparable|benchmark)', content_lower))
    checks.append({"name": "industry_comparable_mentioned", "passed": has_industry_comparable,
                   "detail": "Industry comparable for safety ratio mentioned" if has_industry_comparable else "Industry comparable (1:2 to 1:3) not mentioned"})

    # ── CHECK 6: Enforcement asymmetry ───────────────────────────────────────
    has_enforcement_section = bool(re.search(r'enforcement\s+(asym|consist|action)|asymmetric\s+enforcement|enforcement.*disparity', content_lower))
    checks.append({"name": "enforcement_asymmetry_section", "passed": has_enforcement_section,
                   "detail": "Enforcement asymmetry section found" if has_enforcement_section else "Missing enforcement asymmetry section"})

    # Specific top publishers with no action taken
    has_top_pub_no_action = bool(re.search(r'powerpublisher|top.tier.*no.*action|no.*public.*action|no\s+enforcement\s+action', content_lower))
    checks.append({"name": "top_publisher_no_enforcement", "passed": has_top_pub_no_action,
                   "detail": "No-enforcement-for-top-publishers pattern identified" if has_top_pub_no_action else "Top publisher enforcement gap not identified"})

    # ── CHECK 7: Alignment Verdict ────────────────────────────────────────────
    # All 5 dimensions are flagged => STRUCTURALLY-COMPROMISED
    has_verdict = bool(re.search(r'alignment\s+verdict|verdict\s*:', content_lower))
    checks.append({"name": "alignment_verdict_present", "passed": has_verdict,
                   "detail": "Alignment verdict section present" if has_verdict else "Alignment verdict missing"})

    has_correct_verdict = bool(re.search(r'structurally.compromised', content_lower))
    checks.append({"name": "correct_verdict_structurally_compromised", "passed": has_correct_verdict,
                   "detail": "Correct verdict STRUCTURALLY-COMPROMISED found" if has_correct_verdict else "Expected verdict STRUCTURALLY-COMPROMISED not found"})

    # ── CHECK 8: Recommended actions ─────────────────────────────────────────
    has_recommendations = bool(re.search(r'recommended\s+action|recommendation', content_lower))
    checks.append({"name": "recommended_actions_present", "passed": has_recommendations,
                   "detail": "Recommended actions section present" if has_recommendations else "Recommended actions missing"})

    # At least one concrete recommendation matching the expected actions
    has_scrutiny_rec = bool(re.search(r'higher\s+scrutin|scrutin.*standard|do\s+not\s+rely.*download|avoid.*download.*count|download\s+count.*proxy', content_lower))
    has_audit_artifacts = bool(re.search(r'audit\s+artifact|preemptiv.*audit|publisher.*audit|audit.*publish', content_lower))
    has_structural_reform = bool(re.search(r'structural\s+reform|fixed.fee|mandatory.*review|alternative\s+marketplace', content_lower))
    rec_count = sum([has_scrutiny_rec, has_audit_artifacts, has_structural_reform])
    checks.append({"name": "recommendations_quality", "passed": rec_count >= 2,
                   "detail": f"Found {rec_count}/3 expected recommendation types (scrutiny, audit artifacts, structural reform)"})

    # ── CHECK 9: Warning signals format (⚠️ arrows) ──────────────────────────
    has_warning_symbols = "⚠" in content
    has_arrows = "→" in content
    has_visual_format = has_warning_symbols or has_arrows
    checks.append({"name": "output_format_signals", "passed": has_visual_format,
                   "detail": f"Visual format signals present (⚠: {has_warning_symbols}, →: {has_arrows})" if has_visual_format else "Missing ⚠️ or → visual format signals from expected format"})

    # ── CHECK 10: Assessment timestamp ───────────────────────────────────────
    has_timestamp = bool(re.search(r'2025-06-01', content))
    checks.append({"name": "assessment_timestamp", "passed": has_timestamp,
                   "detail": "Assessment timestamp 2025-06-01 found" if has_timestamp else "Assessment timestamp not present"})

    # ── FINAL SCORE ──────────────────────────────────────────────────────────
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_checks / total_checks, 3)

    # Must pass critical checks to overall pass
    critical = ["report_file_exists", "correct_verdict_structurally_compromised",
                "publisher_concentration_section", "velocity_vs_review_section",
                "revenue_model_section", "enforcement_asymmetry_section",
                "alignment_verdict_present", "recommended_actions_present"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical)

    overall_passed = critical_passed and score >= 0.70

    print(json.dumps({
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()