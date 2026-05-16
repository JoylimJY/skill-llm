#!/usr/bin/env python3
"""
Evaluation script for the netease-music-assistant task.
Usage: python3 eval.py <workspace_dir>
"""
import sys
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []

def check(name: str, passed: bool, detail: str):
    checks.append({"name": name, "passed": passed, "detail": detail})
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}: {detail}")

# ── Helper ───────────────────────────────────────────────────────────────────

def load_json_file(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8")), None
    except FileNotFoundError:
        return None, f"File not found: {path}"
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {e}"

# ════════════════════════════════════════════════════════════════════════════
# CHECK 1: ncm-preference.json exists and has been refreshed (within 24h)
# ════════════════════════════════════════════════════════════════════════════
pref_path = Path("/root/.config/ncm/ncm-preference.json")
pref_data, pref_err = load_json_file(pref_path)

if pref_err:
    check("preference_file_exists", False, pref_err)
    check("preference_refreshed_within_24h", False, "File missing, cannot check timestamp")
    check("preference_has_required_fields", False, "File missing")
    check("preference_keywords_count", False, "File missing")
    check("preference_temporal_pattern", False, "File missing")
    check("preference_content_tags", False, "File missing")
else:
    check("preference_file_exists", True, "ncm-preference.json exists")

    # Check updatedAt is within 24h
    try:
        updated_at_str = pref_data.get("updatedAt", "")
        # Parse ISO format (may have Z or +00:00)
        updated_at_str_clean = updated_at_str.replace("Z", "+00:00")
        try:
            updated_at = datetime.fromisoformat(updated_at_str_clean)
        except Exception:
            # Try without microseconds
            updated_at = datetime.fromisoformat(updated_at_str_clean[:19] + "+00:00")
        now = datetime.now(timezone.utc)
        age_hours = (now - updated_at).total_seconds() / 3600
        if age_hours <= 24:
            check("preference_refreshed_within_24h", True, f"updatedAt={updated_at_str}, age={age_hours:.1f}h")
        else:
            check("preference_refreshed_within_24h", False, f"Cache still stale: age={age_hours:.1f}h > 24h")
    except Exception as e:
        check("preference_refreshed_within_24h", False, f"Cannot parse updatedAt: {e}")

    # Check required fields
    required_fields = ["overallProfile", "recentTrend", "keywords", "temporalPattern", "contentTags", "updatedAt"]
    missing = [f for f in required_fields if f not in pref_data]
    if not missing:
        check("preference_has_required_fields", True, "All required fields present")
    else:
        check("preference_has_required_fields", False, f"Missing fields: {missing}")

    # Check keywords count (max 6)
    kw = pref_data.get("keywords", [])
    if isinstance(kw, list) and 1 <= len(kw) <= 6:
        check("preference_keywords_count", True, f"keywords count={len(kw)} (valid: 1-6)")
    else:
        check("preference_keywords_count", False, f"keywords must be a list with 1-6 items, got: {kw}")

    # Check temporalPattern has required sub-keys
    tp = pref_data.get("temporalPattern", {})
    tp_keys = {"peakHours", "peakDays", "cycleSummary"}
    missing_tp = tp_keys - set(tp.keys())
    if not missing_tp:
        check("preference_temporal_pattern", True, "temporalPattern has all required sub-keys")
    else:
        check("preference_temporal_pattern", False, f"temporalPattern missing keys: {missing_tp}")

    # Check contentTags (max 8)
    ct = pref_data.get("contentTags", [])
    if isinstance(ct, list) and 1 <= len(ct) <= 8:
        check("preference_content_tags", True, f"contentTags count={len(ct)} (valid: 1-8)")
    else:
        check("preference_content_tags", False, f"contentTags must be 1-8 items, got: {ct}")

# ════════════════════════════════════════════════════════════════════════════
# CHECK 2: recommendation_output.md exists with correct structure
# ════════════════════════════════════════════════════════════════════════════
# Search for the output file
output_files = list(workspace.rglob("recommendation_output.md"))
if not output_files:
    check("recommendation_output_exists", False, "recommendation_output.md not found anywhere in workspace")
    rec_content = ""
else:
    output_file = output_files[0]
    rec_content = output_file.read_text(encoding="utf-8")
    check("recommendation_output_exists", True, f"Found at {output_file}")

if rec_content:
    # ── 2a: Contains numeric playlist links (not hex encrypted IDs) ──────────
    # Valid: https://music.163.com/#/playlist?id=7183729472 (numeric)
    # Invalid: https://music.163.com/#/playlist?id=a3f2b4c1... (hex)
    playlist_links = re.findall(r'https://music\.163\.com/#/playlist\?id=(\S+?)(?:\s|$|\)|\])', rec_content)
    song_links = re.findall(r'https://music\.163\.com/#/song\?id=(\S+?)(?:\s|$|\)|\])', rec_content)
    album_links = re.findall(r'https://music\.163\.com/#/album\?id=(\S+?)(?:\s|$|\)|\])', rec_content)
    all_links = playlist_links + song_links + album_links

    if len(all_links) >= 1:
        check("recommendation_has_links", True, f"Found {len(all_links)} resource links")
    else:
        check("recommendation_has_links", False, "No resource links found (need at least 1)")

    # All IDs must be numeric (not hex)
    hex_pattern = re.compile(r'^[a-f0-9]{32}$', re.IGNORECASE)
    bad_ids = [lid for lid in all_links if hex_pattern.match(lid.strip('.,;:)>\n'))]
    numeric_ids = [lid for lid in all_links if re.match(r'^\d+$', lid.strip('.,;:)>\n'))]

    if bad_ids:
        check("links_use_numeric_ids", False, f"Encrypted hex IDs found in links: {bad_ids[:3]} — must use numeric originalId")
    elif numeric_ids:
        check("links_use_numeric_ids", True, f"All {len(numeric_ids)} links use numeric IDs")
    else:
        check("links_use_numeric_ids", False, f"Link IDs not clearly numeric: {all_links[:3]}")

    # ── 2b: No already-recommended IDs in output ─────────────────────────────
    already_recommended_ids = {"3778678", "2145765628", "19723756"}
    # Also exclude collected playlist: 2031574926
    excluded_ids = already_recommended_ids | {"2031574926"}

    found_excluded = []
    for eid in excluded_ids:
        # Check if eid appears as a link ID
        if eid in playlist_links or eid in song_links or eid in album_links:
            found_excluded.append(eid)

    if not found_excluded:
        check("no_already_recommended_in_output", True, "No already-recommended or collected playlists in output")
    else:
        check("no_already_recommended_in_output", False, f"Output contains excluded IDs: {found_excluded} (these are in history or collected)")

    # ── 2c: Has 4-6 recommendations ──────────────────────────────────────────
    # Count numbered entries ① ② ③ or 1. 2. 3. etc.
    circled_nums = re.findall(r'[①②③④⑤⑥]', rec_content)
    numbered = re.findall(r'(?:^|\n)\s*\d+[\.、]\s+[🎶🎵]', rec_content)
    total_recs = max(len(circled_nums), len(numbered))

    # Fallback: count ⭐ 评分 occurrences
    rating_count = len(re.findall(r'[⭐★]\s*评分', rec_content))
    final_count = max(total_recs, rating_count)

    if 4 <= final_count <= 6:
        check("recommendation_count_4_to_6", True, f"Found {final_count} recommendations (valid: 4-6)")
    else:
        check("recommendation_count_4_to_6", False, f"Expected 4-6 recommendations, found ~{final_count}")

    # ── 2d: Each recommendation has a score ──────────────────────────────────
    score_matches = re.findall(r'评分[：:]\s*(\d+)', rec_content)
    valid_scores = [s for s in score_matches if 0 <= int(s) <= 100]
    if len(valid_scores) >= 4:
        check("recommendations_have_scores", True, f"Found {len(valid_scores)} valid scores (0-100)")
    else:
        check("recommendations_have_scores", False, f"Expected ≥4 scores (0-100), found: {score_matches}")

    # ── 2e: Two-layer reasoning present ──────────────────────────────────────
    # Look for evidence of both layers: 偏好 evidence (red heart/曲风/艺人/红心) AND content feature
    pref_layer_patterns = [
        r'红心', r'偏好', r'曲风', r'艺人', r'近期', r'常听', r'R&B', r'古风', r'流行', r'周杰伦'
    ]
    content_layer_patterns = [
        r'氛围', r'场景', r'亮点', r'特质', r'适合', r'风格', r'收录', r'精选', r'歌曲数', r'热度', r'包含'
    ]
    pref_hits = sum(1 for p in pref_layer_patterns if re.search(p, rec_content))
    content_hits = sum(1 for p in content_layer_patterns if re.search(p, rec_content))

    if pref_hits >= 2 and content_hits >= 2:
        check("two_layer_reasoning", True, f"Both reasoning layers present (pref_hits={pref_hits}, content_hits={content_hits})")
    else:
        check("two_layer_reasoning", False, f"Insufficient two-layer reasoning (pref_hits={pref_hits}/2+, content_hits={content_hits}/2+ needed)")
else:
    check("recommendation_has_links", False, "No output file to check")
    check("links_use_numeric_ids", False, "No output file to check")
    check("no_already_recommended_in_output", False, "No output file to check")
    check("recommendation_count_4_to_6", False, "No output file to check")
    check("recommendations_have_scores", False, "No output file to check")
    check("two_layer_reasoning", False, "No output file to check")

# ════════════════════════════════════════════════════════════════════════════
# CHECK 3: ncm-history.json updated with newly recommended playlists
# ════════════════════════════════════════════════════════════════════════════
hist_path = Path("/root/.config/ncm/ncm-history.json")
hist_data, hist_err = load_json_file(hist_path)

if hist_err:
    check("history_file_exists", False, hist_err)
    check("history_has_new_entries", False, "File missing")
else:
    check("history_file_exists", True, "ncm-history.json exists")

    original_ids = {"3778678", "2145765628", "19723756"}  # pre-existing
    all_ids_in_history = {str(entry.get("id", "")) for entry in hist_data.get("recommendedPlaylists", [])}

    new_ids = all_ids_in_history - original_ids
    if len(new_ids) >= 1:
        check("history_has_new_entries", True, f"History has {len(new_ids)} new entries: {new_ids}")
    else:
        check("history_has_new_entries", False, f"No new entries added to history. Current IDs: {all_ids_in_history}")

    # Each entry must have id, name, recommendedAt
    malformed = []
    for entry in hist_data.get("recommendedPlaylists", []):
        if not all(k in entry for k in ["id", "name", "recommendedAt"]):
            malformed.append(entry)
    if not malformed:
        check("history_entries_well_formed", True, "All history entries have id, name, recommendedAt")
    else:
        check("history_entries_well_formed", False, f"{len(malformed)} malformed entries: {malformed[:2]}")

# ════════════════════════════════════════════════════════════════════════════
# CHECK 4: ncm-schedule.json updated with daily 08:30 rule
# ════════════════════════════════════════════════════════════════════════════
sched_path = Path("/root/.config/ncm/ncm-schedule.json")
sched_data, sched_err = load_json_file(sched_path)

if sched_err:
    check("schedule_file_exists", False, sched_err)
    check("schedule_has_daily_830", False, "File missing")
    check("schedule_enabled_true", False, "File missing")
else:
    check("schedule_file_exists", True, "ncm-schedule.json exists")

    # Check enabled=true
    enabled = sched_data.get("enabled", False)
    check("schedule_enabled_true", enabled, f"enabled={enabled}")

    # Check for 08:30 (or 8:30) daily rule
    found_830 = False
    found_daily = False

    def check_time_in_entry(entry):
        times = entry.get("times", [])
        for t in times:
            if re.match(r'^0?8:30$', str(t)):
                return True
        return False

    # Check schedules array
    for sched in sched_data.get("schedules", []):
        if check_time_in_entry(sched):
            found_830 = True
        day_val = sched.get("day", "")
        if day_val == "daily":
            found_daily = True

    # Check customRules array
    for rule in sched_data.get("customRules", []):
        if check_time_in_entry(rule):
            found_830 = True
        day_val = rule.get("day", "")
        if day_val == "daily":
            found_daily = True

    check("schedule_has_daily_830", found_830, f"Found 08:30 time slot: {found_830}")
    check("schedule_has_daily_rule", found_daily, f"Found 'daily' day rule: {found_daily}")

# ════════════════════════════════════════════════════════════════════════════
# CHECK 5: Crontab has been updated with a new job
# ════════════════════════════════════════════════════════════════════════════
try:
    crontab_output = subprocess.run(
        ["crontab", "-l"],
        capture_output=True, text=True, timeout=10
    )
    crontab_content = crontab_output.stdout

    # Check for 8:30 entry (cron format: 30 8 * * *)
    cron_830_pattern = re.compile(r'30\s+8\s+\*\s+\*\s+\*')
    # Also accept: minute=30, hour=8 or similar
    cron_morning_pattern = re.compile(r'30\s+8\b')

    if cron_830_pattern.search(crontab_content) or cron_morning_pattern.search(crontab_content):
        check("crontab_has_830_job", True, f"Crontab has 8:30 job registered")
    else:
        # Be flexible: check for any new cron job related to music/ncm
        ncm_cron = re.search(r'(?:ncm|music|main\.js)', crontab_content, re.IGNORECASE)
        if ncm_cron:
            check("crontab_has_830_job", False, f"Crontab has NCM-related job but not at 08:30. Content: {crontab_content[:200]}")
        else:
            check("crontab_has_830_job", False, f"No 08:30 cron job found. Crontab content: {repr(crontab_content[:300])}")

    # Check that crontab has at least one non-empty, non-comment line
    non_empty_lines = [l for l in crontab_content.splitlines() if l.strip() and not l.strip().startswith("#")]
    if non_empty_lines:
        check("crontab_has_entries", True, f"Crontab has {len(non_empty_lines)} active entries")
    else:
        check("crontab_has_entries", False, "Crontab is empty or has only comments")

except Exception as e:
    check("crontab_has_830_job", False, f"Error reading crontab: {e}")
    check("crontab_has_entries", False, f"Error reading crontab: {e}")

# ════════════════════════════════════════════════════════════════════════════
# CHECK 6: Preference correctly reflects JAY CHOU / R&B / 古风 content
#          (based on deterministic mock data - 20 recent songs are all Jay Chou
#           with songTags: 华语, 流行, R&B, 古风)
# ════════════════════════════════════════════════════════════════════════════
if pref_data:
    # Keywords should include some of: 周杰伦, 华语, 流行, R&B, 古风
    expected_keywords = {"周杰伦", "华语", "流行", "R&B", "古风", "华语流行", "流行华语"}
    kw_list = pref_data.get("keywords", [])
    kw_set = set(kw_list)
    overlap = kw_set & expected_keywords
    # Also check overallProfile / recentTrend mentions Jay Chou or relevant tags
    profile_text = pref_data.get("overallProfile", "") + " " + pref_data.get("recentTrend", "")
    profile_mentions_jay = bool(re.search(r'周杰伦|Jay Chou|R&B|古风|流行', profile_text))

    if len(overlap) >= 1 or profile_mentions_jay:
        check("preference_reflects_liked_songs", True, f"Keywords/profile reflect Jay Chou/R&B/古风 content. Overlap: {overlap}, profile_mentions: {profile_mentions_jay}")
    else:
        check("preference_reflects_liked_songs", False, f"Keywords {kw_list} and profile don't reflect the mock liked songs (mostly Jay Chou + 华语/流行/R&B/古风)")
else:
    check("preference_reflects_liked_songs", False, "No preference data to check")

# ════════════════════════════════════════════════════════════════════════════
# Final scoring
# ════════════════════════════════════════════════════════════════════════════
print("\n=== EVALUATION SUMMARY ===")
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])

# Weight critical checks more
critical_checks = {
    "preference_refreshed_within_24h": 2.0,
    "links_use_numeric_ids": 2.0,
    "no_already_recommended_in_output": 2.0,
    "crontab_has_830_job": 2.0,
    "two_layer_reasoning": 1.5,
    "history_has_new_entries": 1.5,
    "preference_reflects_liked_songs": 1.5,
}

weighted_score = 0.0
max_weighted = 0.0
for c in checks:
    w = critical_checks.get(c["name"], 1.0)
    max_weighted += w
    if c["passed"]:
        weighted_score += w

score = round(weighted_score / max_weighted, 3) if max_weighted > 0 else 0.0
all_passed = all(c["passed"] for c in checks)

print(f"Passed: {passed_count}/{total} checks")
print(f"Weighted score: {score:.3f}")

result = {
    "passed": score >= 0.70,
    "score": score,
    "checks": checks
}
print(json.dumps(result, indent=2, ensure_ascii=False))