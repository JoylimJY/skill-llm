import sys
import json
import re
from pathlib import Path

def main(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})
    
    # ── Find the report file ──────────────────────────────────────────────────
    report_files = list(workspace.rglob("health_summary_report.md"))
    if not report_files:
        add_check("report_file_exists", False, "health_summary_report.md not found anywhere in workspace")
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}
    
    report_path = report_files[0]
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        add_check("report_readable", False, f"Could not read report: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}
    
    add_check("report_file_exists", True, f"Found at {report_path}")
    content_lower = content.lower()
    
    # ── CHECK 1: Contraction count ────────────────────────────────────────────
    # Total contractions = 15
    try:
        count_match = re.search(r'(\b15\b)', content)
        passed = count_match is not None
        add_check("contraction_count_15", passed,
                  "Report should mention 15 total contractions" + ("" if passed else " — not found"))
    except Exception as e:
        add_check("contraction_count_15", False, f"Exception: {e}")
    
    # ── CHECK 2: 5-1-1 rule mentioned ────────────────────────────────────────
    try:
        pattern_511 = re.search(r'5[\s\-–—]*1[\s\-–—]*1', content)
        passed = pattern_511 is not None
        add_check("511_rule_mentioned", passed,
                  "Report should reference the 5-1-1 rule" + ("" if passed else " — not found"))
    except Exception as e:
        add_check("511_rule_mentioned", False, f"Exception: {e}")
    
    # ── CHECK 3: Mum verdict is "Seek care" (not just "monitor") ─────────────
    try:
        seek_care = re.search(r'seek\s+care', content_lower)
        passed = seek_care is not None
        add_check("mum_verdict_seek_care", passed,
                  "Mum verdict should be 'Seek care' given 5-1-1 contractions for ~50 min" +
                  ("" if passed else " — not found"))
    except Exception as e:
        add_check("mum_verdict_seek_care", False, f"Exception: {e}")
    
    # ── CHECK 4: Contraction interval ~5 min mentioned ───────────────────────
    try:
        # The last 10 contractions have ~5 min intervals (endTime to next startTime ~4 min)
        # interval from endTime to startTime: startTime gap is 5 min, duration ~60s, so REST = ~4 min
        # agent should report approximately 4-5 min intervals for recent contractions
        interval_match = re.search(r'\b[34567]\s*(min|minute)', content_lower)
        passed = interval_match is not None
        add_check("contraction_interval_approx_5min", passed,
                  "Report should mention ~4-5 min intervals for recent contractions" +
                  ("" if passed else " — not found"))
    except Exception as e:
        add_check("contraction_interval_approx_5min", False, f"Exception: {e}")
    
    # ── CHECK 5: Contraction duration ~60 seconds mentioned ──────────────────
    try:
        dur_match = re.search(r'\b(58|59|60|61|62|63)\s*(s|sec|second)', content_lower) or \
                    re.search(r'\b1\s*(min|minute)', content_lower)
        passed = dur_match is not None
        add_check("contraction_duration_approx_60s", passed,
                  "Report should mention ~58-63s contraction duration" +
                  ("" if passed else " — not found"))
    except Exception as e:
        add_check("contraction_duration_approx_60s", False, f"Exception: {e}")
    
    # ── CHECK 6: Baby age ~6 days ─────────────────────────────────────────────
    try:
        age_match = re.search(r'\b[56]\s*(day|days)\b', content_lower) or \
                    re.search(r'\b6[-\s]day', content_lower)
        passed = age_match is not None
        add_check("baby_age_6_days", passed,
                  "Report should state baby is ~6 days old" +
                  ("" if passed else " — not found"))
    except Exception as e:
        add_check("baby_age_6_days", False, f"Exception: {e}")
    
    # ── CHECK 7: Bottle feeds in last 24h = 6 ────────────────────────────────
    try:
        # 6 bottle feeds in last 24h
        feed_match = re.search(r'\b6\b.{0,40}(feed|bottle|formula)', content_lower) or \
                     re.search(r'(feed|bottle|formula).{0,40}\b6\b', content_lower)
        passed = feed_match is not None
        add_check("bottle_feeds_24h_count_6", passed,
                  "Report should mention 6 bottle feeds in last 24h" +
                  ("" if passed else " — not found"))
    except Exception as e:
        add_check("bottle_feeds_24h_count_6", False, f"Exception: {e}")
    
    # ── CHECK 8: Total mL in 24h correct (55+60+45+65+50+55 = 330 mL) ────────
    try:
        ml_match = re.search(r'\b330\s*(ml|mL)', content)
        passed = ml_match is not None
        add_check("total_volume_330ml", passed,
                  "Report should state 330 mL total bottle feeding volume in 24h" +
                  ("" if passed else " — not found"))
    except Exception as e:
        add_check("total_volume_330ml", False, f"Exception: {e}")
    
    # ── CHECK 9: Breastfeeding session in 24h = 1 (8 min = 480s) ─────────────
    try:
        bf_match = re.search(r'\b1\b.{0,60}(breastfeed|breast\s*feed|nursing)', content_lower) or \
                   re.search(r'(breastfeed|breast\s*feed|nursing).{0,60}\b1\b', content_lower)
        passed = bf_match is not None
        add_check("breastfeeding_sessions_24h_count_1", passed,
                  "Report should mention 1 breastfeeding session in last 24h" +
                  ("" if passed else " — not found"))
    except Exception as e:
        add_check("breastfeeding_sessions_24h_count_1", False, f"Exception: {e}")
    
    # ── CHECK 10: Wet diapers count 24h = 5 (hasPee=True entries in 24h) ─────
    # In 24h window: (2h,pee), (5h,pee+poo), (8h,pee), (11h,nopee), (16h,pee), (21h,pee) → 5 wet
    try:
        wet_match = re.search(r'\b5\b.{0,40}(wet|pee|urine)', content_lower) or \
                    re.search(r'(wet|pee|urine).{0,40}\b5\b', content_lower)
        passed = wet_match is not None
        add_check("wet_diapers_24h_count_5", passed,
                  "Report should mention 5 wet diapers in last 24h" +
                  ("" if passed else " — not found"))
    except Exception as e:
        add_check("wet_diapers_24h_count_5", False, f"Exception: {e}")
    
    # ── CHECK 11: Dirty diapers count 24h = 2 (hasPoo=True) ─────────────────
    # (5h: poo), (11h: poo) → 2 dirty
    try:
        dirty_match = re.search(r'\b2\b.{0,40}(dirty|poo|stool|bowel)', content_lower) or \
                      re.search(r'(dirty|poo|stool|bowel).{0,40}\b2\b', content_lower)
        passed = dirty_match is not None
        add_check("dirty_diapers_24h_count_2", passed,
                  "Report should mention 2 dirty diapers in last 24h" +
                  ("" if passed else " — not found"))
    except Exception as e:
        add_check("dirty_diapers_24h_count_2", False, f"Exception: {e}")
    
    # ── CHECK 12: Baby verdict is Monitor or Concern (not fully healthy) ──────
    try:
        concern_match = re.search(r'\b(monitor|concern|below|insufficient|low)\b', content_lower)
        passed = concern_match is not None
        add_check("baby_verdict_not_fully_healthy", passed,
                  "Baby verdict should be Monitor/Concern given below-threshold feeds and diapers" +
                  ("" if passed else " — agent incorrectly marked baby as fully healthy"))
    except Exception as e:
        add_check("baby_verdict_not_fully_healthy", False, f"Exception: {e}")
    
    # ── CHECK 13: Medical caveat present ─────────────────────────────────────
    try:
        caveat_match = re.search(
            r'(not medical advice|midwife|obstetrician|paediatrician|ob|gp|doctor|healthcare)',
            content_lower
        )
        passed = caveat_match is not None
        add_check("medical_caveat_present", passed,
                  "Report must include a medical disclaimer/caveat" +
                  ("" if passed else " — not found"))
    except Exception as e:
        add_check("medical_caveat_present", False, f"Exception: {e}")
    
    # ── CHECK 14: Both sections present (mum + baby) ─────────────────────────
    try:
        has_mum = re.search(r'\b(mum|mom|mother|contraction)', content_lower) is not None
        has_baby = re.search(r'\b(baby|infant|newborn|feeding|diaper)', content_lower) is not None
        passed = has_mum and has_baby
        add_check("both_sections_present", passed,
                  "Report must cover both mum (contractions) and baby (feeding/diapers)" +
                  (f" — mum={has_mum}, baby={has_baby}" if not passed else ""))
    except Exception as e:
        add_check("both_sections_present", False, f"Exception: {e}")
    
    # ── Score ─────────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 3)
    
    # Must pass: report exists, seek care verdict, baby not fully healthy, 5-1-1 rule, 330 mL
    critical = ["report_file_exists", "mum_verdict_seek_care", "baby_verdict_not_fully_healthy",
                "511_rule_mentioned", "total_volume_330ml"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical)
    
    overall_passed = critical_passed and score >= 0.70
    
    return {"passed": overall_passed, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = main(workspace)
    print(json.dumps(result, indent=2))