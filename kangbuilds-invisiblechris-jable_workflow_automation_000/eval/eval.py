import sys
import json
import re
import subprocess
from pathlib import Path

def run_checks(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    # ── Locate the output file ────────────────────────────────────────────────
    # The agent was asked to save output to 'trending_report.txt'
    report_candidates = list(workspace.rglob("trending_report.txt"))
    
    file_found = len(report_candidates) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found {len(report_candidates)} file(s) named 'trending_report.txt'" if file_found
                  else "No file named 'trending_report.txt' found anywhere in workspace"
    })
    
    if not file_found:
        return checks, 0.0
    
    report_path = report_candidates[0]
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return checks, 0.0
    
    checks.append({"name": "file_readable", "passed": True, "detail": f"File at {report_path}"})
    
    # ── Check: exactly 5 entries ──────────────────────────────────────────────
    # Expected top 5 by likes within 24h with pages scanned:
    # Eligible (in 24h AND in pages): ABC-001(3200), DEF-002(5800), GHI-003(4100), JKL-004(6700), MNO-005(2900)
    # PQR-006 is in 24h but NOT in pages → skipped
    # STU-007, VWX-008 are older than 24h → excluded
    # Sorted by likes desc: JKL-004(6700), DEF-002(5800), GHI-003(4100), ABC-001(3200), MNO-005(2900)
    
    expected_order = [
        {"title": "Velvet Storm Episode",       "likes": 6700, "url": "https://jable.tv/videos/jkl-004/"},
        {"title": "Midnight Breeze Collection", "likes": 5800, "url": "https://jable.tv/videos/def-002/"},
        {"title": "Golden Horizon Series",      "likes": 4100, "url": "https://jable.tv/videos/ghi-003/"},
        {"title": "Crystal Waters Adventure",   "likes": 3200, "url": "https://jable.tv/videos/abc-001/"},
        {"title": "Sapphire Dreams Showcase",   "likes": 2900, "url": "https://jable.tv/videos/mno-005/"},
    ]
    
    # Count emoji-numbered entries (1️⃣ through 5️⃣ or similar patterns)
    emoji_num_pattern = re.compile(
        r'(1️⃣|2️⃣|3️⃣|4️⃣|5️⃣|1⃣|2⃣|3⃣|4⃣|5⃣)'
    )
    emoji_matches = emoji_num_pattern.findall(content)
    has_five_entries = len(emoji_matches) == 5
    checks.append({
        "name": "exactly_five_entries",
        "passed": has_five_entries,
        "detail": f"Found {len(emoji_matches)} numbered emoji entries, expected 5"
    })
    
    # ── Check: proprietary emoji format ──────────────────────────────────────
    # Must use ❤️ for likes
    heart_count = content.count("❤️")
    has_heart_emoji = heart_count >= 5
    checks.append({
        "name": "heart_emoji_for_likes",
        "passed": has_heart_emoji,
        "detail": f"Found {heart_count} ❤️ emoji(s), expected at least 5"
    })
    
    # Must use 🔗 for URLs
    link_count = content.count("🔗")
    has_link_emoji = link_count >= 5
    checks.append({
        "name": "link_emoji_for_urls",
        "passed": has_link_emoji,
        "detail": f"Found {link_count} 🔗 emoji(s), expected at least 5"
    })
    
    # ── Check: correct first result (highest likes) ───────────────────────────
    first_correct = "Velvet Storm Episode" in content and "6700" in content
    checks.append({
        "name": "first_result_correct",
        "passed": first_correct,
        "detail": "Expected 'Velvet Storm Episode' (6700 likes) as first result"
                  if not first_correct else "First result matches expected top video"
    })
    
    # ── Check: correct second result ─────────────────────────────────────────
    second_correct = "Midnight Breeze Collection" in content and "5800" in content
    checks.append({
        "name": "second_result_correct",
        "passed": second_correct,
        "detail": "Expected 'Midnight Breeze Collection' (5800 likes) as second result"
                  if not second_correct else "Second result matches"
    })
    
    # ── Check: skip behavior respected (PQR-006 NOT in output) ───────────────
    # Ember Glow Feature has 9999 likes but should be SKIPPED (not in scanned pages)
    ember_absent = "Ember Glow Feature" not in content and "9999" not in content
    checks.append({
        "name": "skip_behavior_respected",
        "passed": ember_absent,
        "detail": "Correctly omitted 'Ember Glow Feature' (not in scanned pages)"
                  if ember_absent else "FAIL: 'Ember Glow Feature' (9999 likes) should be skipped — it was recent but not found in page scans"
    })
    
    # ── Check: time filter respected (old videos absent) ─────────────────────
    old_absent = "Silver Dusk Anthology" not in content and "Twilight Cascade Edition" not in content
    checks.append({
        "name": "time_filter_respected",
        "passed": old_absent,
        "detail": "Correctly excluded videos older than 24 hours"
                  if old_absent else "FAIL: Videos older than 24h (STU-007, VWX-008) should not appear"
    })
    
    # ── Check: all 5 expected URLs present ───────────────────────────────────
    urls_present = all(v["url"].rstrip("/") in content or v["url"] in content for v in expected_order)
    checks.append({
        "name": "all_expected_urls_present",
        "passed": urls_present,
        "detail": "All 5 expected video URLs found in output" if urls_present
                  else "One or more expected URLs missing from output"
    })
    
    # ── Check: correct ordering (position check for top 2) ───────────────────
    pos_velvet = content.find("Velvet Storm Episode")
    pos_midnight = content.find("Midnight Breeze Collection")
    pos_golden = content.find("Golden Horizon Series")
    ordering_correct = (pos_velvet != -1 and pos_midnight != -1 and pos_golden != -1 and
                        pos_velvet < pos_midnight < pos_golden)
    checks.append({
        "name": "correct_ordering",
        "passed": ordering_correct,
        "detail": "Results appear in correct like-count descending order"
                  if ordering_correct else f"Incorrect ordering: velvet@{pos_velvet}, midnight@{pos_midnight}, golden@{pos_golden}"
    })
    
    # ── Compute score ─────────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    # Weight the checks: format + correctness are critical
    weights = {
        "output_file_exists": 1,
        "file_readable": 1,
        "exactly_five_entries": 2,
        "heart_emoji_for_likes": 2,
        "link_emoji_for_urls": 2,
        "first_result_correct": 2,
        "second_result_correct": 1,
        "skip_behavior_respected": 3,
        "time_filter_respected": 2,
        "all_expected_urls_present": 2,
        "correct_ordering": 2,
    }
    total_weight = sum(weights.values())
    earned_weight = sum(weights.get(c["name"], 1) for c in checks if c["passed"])
    score = round(earned_weight / total_weight, 3)
    
    all_passed = all(c["passed"] for c in checks)
    return checks, score, all_passed


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "setup", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)
    
    try:
        checks, score, all_passed = run_checks(sys.argv[1])
    except Exception as e:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "eval_error", "passed": False, "detail": f"Evaluator crashed: {e}"}
        ]}))
        sys.exit(1)
    
    print(json.dumps({
        "passed": all_passed,
        "score": score,
        "checks": checks
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()