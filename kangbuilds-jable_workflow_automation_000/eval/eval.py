#!/usr/bin/env python3
"""
Evaluation script for the jable top_liked_recent task.
Checks that the agent:
  1. Ran the skill script with correct parameters (--hours 24 --top 5)
  2. Saved output to top_videos.txt
  3. Used the correct emoji output format (1️⃣, ❤️, 🔗)
  4. Got the correct top-5 videos sorted by likes within 24h window
  5. Excluded videos outside the 24h window
  6. Excluded videos not appearing in latest-updates pages (the "skip" rule)
"""
import sys
import json
import re
from pathlib import Path

def main(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    # ── Expected ground truth ─────────────────────────────────────────────────
    # From gen_inputs_script data (videos within 24h AND in latest pages):
    # videos with hours_ago < 24 AND in_pages=True:
    # ("aaa-001", "Studio Romance Collection Vol.3",  2,  4521, True)
    # ("bbb-002", "Midnight Encounter Series Ep.7",   5,  7830, True)
    # ("ccc-003", "Afternoon Delight Anthology",       8,  1200, True)
    # ("ddd-004", "Classic Beauty Showcase 2024",     12,  9100, True)
    # ("eee-005", "Urban Lifestyle Features Part 2",  15,  3344, True)
    # ("fff-006", "Seaside Summer Special Edition",   18,  5500, True)
    # ("ggg-007", "Winter Warmth Collection Ep.1",    20,  8200, True)
    # ("hhh-008", "Spring Festival Highlights",       22,  6750, True)
    # ("nnn-014", "New Release Preview Vol.1",         1,   500, True)
    # ("ooo-015", "Daily Update Morning Edition",      3,  2100, True)
    # NOT included: iii-009 (not in pages), jjj-010+ (outside 24h)
    # Sorted by likes desc: ddd(9100), ggg(8200), bbb(7830), hhh(6750), fff(5500)
    # Top 5:
    expected_top5 = [
        ("Classic Beauty Showcase 2024",       9100, "http://localhost:18888/videos/ddd-004/"),
        ("Winter Warmth Collection Ep.1",      8200, "http://localhost:18888/videos/ggg-007/"),
        ("Midnight Encounter Series Ep.7",     7830, "http://localhost:18888/videos/bbb-002/"),
        ("Spring Festival Highlights",         6750, "http://localhost:18888/videos/hhh-008/"),
        ("Seaside Summer Special Edition",     5500, "http://localhost:18888/videos/fff-006/"),
    ]
    
    # ── Find top_videos.txt ───────────────────────────────────────────────────
    output_file = None
    candidates = list(workspace.rglob("top_videos.txt"))
    
    check_file_exists = {
        "name": "output_file_exists",
        "passed": False,
        "detail": "top_videos.txt not found anywhere in workspace"
    }
    
    if candidates:
        output_file = candidates[0]
        check_file_exists["passed"] = True
        check_file_exists["detail"] = f"Found at {output_file}"
    
    checks.append(check_file_exists)
    
    if not output_file:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }
        print(json.dumps(result))
        return
    
    # ── Read file content ─────────────────────────────────────────────────────
    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({
            "name": "file_readable",
            "passed": False,
            "detail": f"Could not read file: {e}"
        })
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return
    
    checks.append({
        "name": "file_readable",
        "passed": True,
        "detail": f"File read successfully ({len(content)} chars)"
    })
    
    # ── Check emoji format ────────────────────────────────────────────────────
    # Must contain number emojis like 1️⃣, 2️⃣, etc.
    # Unicode: 1\ufe0f\u20e3, 2\ufe0f\u20e3...
    num_emoji_pattern = r'[1-9]\ufe0f\u20e3|\U0001f51f'
    heart_emoji = '\u2764\ufe0f'
    link_emoji = '\U0001f517'
    
    has_num_emojis = bool(re.search(num_emoji_pattern, content))
    has_heart = heart_emoji in content
    has_link = link_emoji in content
    
    checks.append({
        "name": "number_emoji_format",
        "passed": has_num_emojis,
        "detail": f"Number emoji (e.g. 1️⃣) present: {has_num_emojis}"
    })
    checks.append({
        "name": "heart_emoji_format",
        "passed": has_heart,
        "detail": f"Heart emoji ❤️ present: {has_heart}"
    })
    checks.append({
        "name": "link_emoji_format",
        "passed": has_link,
        "detail": f"Link emoji 🔗 present: {has_link}"
    })
    
    # ── Check correct number of results (5) ──────────────────────────────────
    # Count number emoji occurrences as proxy for result count
    result_count = len(re.findall(num_emoji_pattern, content))
    has_five_results = result_count == 5
    checks.append({
        "name": "correct_result_count",
        "passed": has_five_results,
        "detail": f"Expected 5 results, found {result_count} number emojis"
    })
    
    # ── Check correct titles present ──────────────────────────────────────────
    for rank_idx, (title, likes, url) in enumerate(expected_top5):
        title_present = title in content
        checks.append({
            "name": f"rank{rank_idx+1}_title_correct",
            "passed": title_present,
            "detail": f"Title '{title}' {'found' if title_present else 'NOT FOUND'} in output"
        })
    
    # ── Check correct likes present ───────────────────────────────────────────
    for rank_idx, (title, likes, url) in enumerate(expected_top5):
        likes_str = str(likes)
        likes_present = likes_str in content
        checks.append({
            "name": f"rank{rank_idx+1}_likes_correct",
            "passed": likes_present,
            "detail": f"Likes value {likes} {'found' if likes_present else 'NOT FOUND'} in output"
        })
    
    # ── Check excluded items NOT in output ────────────────────────────────────
    # Items that should NOT appear:
    # - iii-009 (not in pages) -> "Hidden Gem Exclusive Preview"
    # - jjj-010 (outside 24h) -> "Golden Era Classics Vol.12"
    # - kkk-011, lll-012, mmm-013 (outside 24h)
    excluded_titles = [
        "Hidden Gem Exclusive Preview",     # not in latest pages
        "Golden Era Classics Vol.12",       # outside 24h
        "Vintage Collection Remastered",    # outside 24h
    ]
    for excl_title in excluded_titles:
        not_present = excl_title not in content
        checks.append({
            "name": f"excluded_title_absent_{excl_title[:15].replace(' ','_')}",
            "passed": not_present,
            "detail": f"'{excl_title}' correctly absent: {not_present}"
        })
    
    # ── Check ordering: rank 1 should be #1 by likes ─────────────────────────
    # Verify that the first title in order is the highest liked
    top1_title = expected_top5[0][0]  # "Classic Beauty Showcase 2024"
    top2_title = expected_top5[1][0]  # "Winter Warmth Collection Ep.1"
    
    pos_top1 = content.find(top1_title)
    pos_top2 = content.find(top2_title)
    
    order_correct = (pos_top1 != -1 and pos_top2 != -1 and pos_top1 < pos_top2)
    checks.append({
        "name": "sort_order_by_likes_descending",
        "passed": order_correct,
        "detail": (
            f"Top-liked video appears before 2nd: {order_correct} "
            f"(pos1={pos_top1}, pos2={pos_top2})"
        )
    })
    
    # ── Check 24h window was used (not 48h default) ────────────────────────────
    # If agent used default 48h, items like jjj-010 (25h ago, 15000 likes) would appear
    extra_item_absent = "Golden Era Classics" not in content
    checks.append({
        "name": "correct_hours_window_24h",
        "passed": extra_item_absent,
        "detail": (
            f"'Golden Era Classics Vol.12' (25h old, would appear in 48h window) "
            f"correctly absent: {extra_item_absent}"
        )
    })
    
    # ── Scoring ────────────────────────────────────────────────────────────────
    # Weight critical checks more heavily
    critical_checks = [
        "output_file_exists",
        "number_emoji_format",
        "heart_emoji_format", 
        "link_emoji_format",
        "correct_result_count",
        "sort_order_by_likes_descending",
        "correct_hours_window_24h",
    ]
    
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])
    
    # Critical checks: if any fail, cap score
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )
    
    base_score = passed_checks / total_checks if total_checks > 0 else 0.0
    
    if not critical_passed:
        base_score = min(base_score, 0.5)
    
    all_passed = all(c["passed"] for c in checks)
    
    result = {
        "passed": all_passed,
        "score": round(base_score, 3),
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "invocation", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)
    main(sys.argv[1])