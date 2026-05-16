import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def find_report_file(workspace):
    """Search for the weekly report markdown file."""
    candidates = list(Path(workspace).rglob("weekly_report_20260216.md"))
    if not candidates:
        # Also accept slight naming variants
        candidates = list(Path(workspace).rglob("*week*2026*02*16*.md")) + \
                     list(Path(workspace).rglob("*report*2026*02*16*.md")) + \
                     list(Path(workspace).rglob("*report*week*2026*.md"))
    return candidates[0] if candidates else None

def run_eval(workspace):
    checks = []
    
    # --- Find the report file ---
    report_path = find_report_file(workspace)
    if report_path is None:
        checks.append(check("report_file_exists", False, "Could not find weekly_report_20260216.md in workspace"))
        return checks, 0.0
    
    checks.append(check("report_file_exists", True, f"Found report at {report_path}"))
    
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append(check("report_readable", False, f"Could not read file: {e}"))
        return checks, 0.0
    
    checks.append(check("report_readable", True, "File is readable"))

    # --- CHECK 1: Week header with correct date ---
    week_header_ok = bool(re.search(r"2026-02-16", content))
    checks.append(check(
        "week_date_header",
        week_header_ok,
        "Report must reference the week of 2026-02-16" if not week_header_ok else "Week date found"
    ))

    # --- CHECK 2: Japanese section headers present ---
    required_jp_headers = ["サマリー", "プラットフォーム別", "ベスト投稿", "学び"]
    for h in required_jp_headers:
        found = h in content
        checks.append(check(
            f"japanese_header_{h}",
            found,
            f"Required Japanese header '{h}' {'found' if found else 'NOT found'}"
        ))

    # --- CHECK 3: Platform-specific Japanese field names ---
    x_fields = ["インプレッション", "いいね", "リポスト", "リプライ"]
    threads_fields = ["コメント"]
    note_fields = ["スキ", "PV"]
    
    for field in x_fields:
        found = field in content
        checks.append(check(
            f"x_field_{field}",
            found,
            f"X field '{field}' {'present' if found else 'MISSING'}"
        ))
    
    for field in threads_fields + note_fields:
        found = field in content
        checks.append(check(
            f"platform_field_{field}",
            found,
            f"Platform field '{field}' {'present' if found else 'MISSING'}"
        ))

    # --- CHECK 4: Summary totals correctness ---
    # Total posts: 5 (X) + 3 (Threads) + 2 (Note) = 10
    # Total impressions (X only): 4200+2100+6800+1800+3300 = 18200
    # Total engagement: likes+reposts+replies across all platforms
    # X: (87+23+15)+(34+8+6)+(142+56+29)+(21+4+11)+(65+12+48) = 125+48+227+36+125 = 561
    # Threads: (32+7+9)+(14+3+2)+(28+5+6) = 48+19+39 = 106
    # Note: (67+12)+(103+18) = 79+121 = 200
    # Total engagement = 561 + 106 + 200 = 867
    
    total_posts_ok = bool(re.search(r"10\s*件", content) or re.search(r"総投稿数[：:]\s*10", content))
    checks.append(check(
        "total_posts_10",
        total_posts_ok,
        f"Total posts should be 10件. {'Found' if total_posts_ok else 'NOT found'} in content."
    ))

    total_impressions_ok = "18200" in content or "18,200" in content
    checks.append(check(
        "total_impressions_18200",
        total_impressions_ok,
        f"Total impressions should be 18200. {'Found' if total_impressions_ok else 'NOT found'}."
    ))

    # --- CHECK 5: Best post ranking (ベスト投稿) ---
    # X003: impressions=6800, likes=142, reposts=56, replies=29 → engagement=227
    # X001: engagement=125, X005: engagement=125 (tie)
    # Top post must be X003's content or its likes/engagement
    best_post_section = ""
    if "ベスト投稿" in content:
        idx = content.index("ベスト投稿")
        best_post_section = content[idx:idx+500]
    
    top_post_ok = "おすすめAIツール5選" in best_post_section or "おすすめAIツール" in content[content.find("ベスト投稿"):] if "ベスト投稿" in content else False
    checks.append(check(
        "best_post_top_is_x003",
        top_post_ok,
        f"Top ベスト投稿 should be 'おすすめAIツール5選'. {'Confirmed' if top_post_ok else 'NOT found in ベスト投稿 section'}."
    ))

    # --- CHECK 6: Follower trend tables present ---
    # Must include X, Threads, Note follower tables
    platforms_in_tables = []
    for platform, marker in [("X", "@Yuki_"), ("Threads", "@"), ("Note", "Note")]:
        # Look for table-like structure with dates and follower numbers
        has_follower_data = bool(re.search(r"2026-02-0[18].*\d{2,4}", content))
        platforms_in_tables.append(has_follower_data)
    
    # Check specific follower numbers appear
    follower_numbers = ["312", "341", "378", "405", "87", "96", "108", "121", "34", "38", "41", "47"]
    found_followers = [n for n in follower_numbers if n in content]
    follower_data_ok = len(found_followers) >= 8  # at least 8 of 12 numbers present
    checks.append(check(
        "follower_tables_populated",
        follower_data_ok,
        f"Follower data: found {len(found_followers)}/12 expected numbers {found_followers}. Need ≥8."
    ))

    # --- CHECK 7: 増減 (delta) values computed ---
    # X deltas: +29, +37, +27; Threads: +9, +12, +13; Note: +4, +3, +6
    # Check for at least some deltas with + sign
    delta_pattern = re.findall(r'[+＋]\d+', content)
    has_deltas = len(delta_pattern) >= 5
    checks.append(check(
        "delta_values_computed",
        has_deltas,
        f"Found {len(delta_pattern)} delta values (need ≥5): {delta_pattern[:10]}"
    ))
    
    # Specific delta check for X: +29 (341-312), +37 (378-341), +27 (405-378)
    x_deltas_ok = "+29" in content and "+37" in content and "+27" in content
    checks.append(check(
        "x_specific_deltas_correct",
        x_deltas_ok,
        f"X deltas (+29,+37,+27) {'all found' if x_deltas_ok else 'some missing'} in content."
    ))

    # --- CHECK 8: KPI Achievement status included ---
    # Short-term KPI: X +100 followers (312→405 = +93 → NOT yet met), 
    # avg likes X = (87+34+142+21+65)/5 = 349/5 = 69.8 ≥ 10 ✓
    # Threads: 87→121 = +34 (not met), avg likes = (32+14+28)/3 = 24.7 ≥ 5 ✓
    # Note: 34→47 = +13 (not met), avg PV = (890+1240)/2 = 1065 ≥ 100 ✓
    
    kpi_section_ok = "KPI" in content
    checks.append(check(
        "kpi_section_present",
        kpi_section_ok,
        "KPI section/reference " + ("found" if kpi_section_ok else "NOT found")
    ))

    # --- CHECK 9: Platform sections X, Threads, Note present ---
    for platform, jp_label in [("X", "X:"), ("Threads", "Threads:"), ("Note", "Note:")]:
        found = jp_label in content or platform in content
        checks.append(check(
            f"platform_section_{platform}",
            found,
            f"Platform section for {platform} {'present' if found else 'MISSING'}"
        ))

    # --- CHECK 10: Code block formatting (triple backtick) for summary and platform data ---
    code_blocks = re.findall(r'```', content)
    has_code_blocks = len(code_blocks) >= 6  # at least 3 pairs of code blocks
    checks.append(check(
        "code_block_formatting",
        has_code_blocks,
        f"Found {len(code_blocks)} backtick markers (need ≥6 for 3+ code blocks). Template requires code blocks."
    ))

    # --- Compute score ---
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)
    
    return checks, score

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    try:
        checks, score = run_eval(workspace)
    except Exception as e:
        checks = [check("eval_crash", False, f"Evaluator crashed: {e}")]
        score = 0.0
    
    passed = score >= 0.75
    
    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()