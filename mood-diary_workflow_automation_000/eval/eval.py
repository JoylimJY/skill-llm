import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    
    checks = []
    total_score = 0.0
    
    data_file = Path.home() / ".openclaw" / "workspace" / "data" / "journal" / "entries.json"
    
    # --- Load journal data ---
    entries = []
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        entries = data.get("entries", [])
    except FileNotFoundError:
        checks.append({"name": "data_file_exists", "passed": False, "detail": f"Data file not found at {data_file}"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return
    except Exception as e:
        checks.append({"name": "data_file_readable", "passed": False, "detail": f"Error reading data file: {e}"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return
    
    checks.append({"name": "data_file_exists", "passed": True, "detail": f"Found data file with {len(entries)} entries"})
    total_score += 0.05
    
    today = datetime.now().date()
    expected_dates = {
        "6_days_ago": str(today - timedelta(days=6)),
        "5_days_ago": str(today - timedelta(days=5)),
        "4_days_ago": str(today - timedelta(days=4)),
        "3_days_ago": str(today - timedelta(days=3)),
        "2_days_ago": str(today - timedelta(days=2)),
        "yesterday": str(today - timedelta(days=1)),
        "today": str(today),
    }
    
    # --- Check 1: At least 7 entries exist ---
    if len(entries) >= 7:
        checks.append({"name": "entry_count_at_least_7", "passed": True, "detail": f"{len(entries)} entries found"})
        total_score += 0.10
    else:
        checks.append({"name": "entry_count_at_least_7", "passed": False, "detail": f"Only {len(entries)} entries found, need at least 7"})
    
    # Helper: get entries by date
    def get_entries_by_date(date_str):
        return [e for e in entries if e.get("date") == date_str]
    
    # --- Check 2: Day 1 (6_days_ago) - 兴奋 mood with score 9, "燃" keyword should trigger 兴奋 ---
    d6 = expected_dates["6_days_ago"]
    d6_entries = get_entries_by_date(d6)
    if d6_entries:
        # Check for 兴奋 mood (triggered by "燃" keyword)
        has_excited = any(e.get("mood") == "兴奋" for e in d6_entries)
        score_9 = any(e.get("score") == 9 for e in d6_entries)
        if has_excited and score_9:
            checks.append({"name": "day1_excited_mood_score9", "passed": True, "detail": f"Correct: 兴奋 mood with score 9 on {d6}"})
            total_score += 0.15
        elif has_excited:
            checks.append({"name": "day1_excited_mood_score9", "passed": False, "detail": f"Found 兴奋 mood but score is {[e.get('score') for e in d6_entries]}, expected 9"})
        else:
            checks.append({"name": "day1_excited_mood_score9", "passed": False, "detail": f"Expected 兴奋 mood on {d6}, got {[e.get('mood') for e in d6_entries]}"})
    else:
        checks.append({"name": "day1_excited_mood_score9", "passed": False, "detail": f"No entry found for {d6}"})
    
    # --- Check 3: Day 3 (4_days_ago) - 焦虑 or 平静 mood with score 5 ---
    d4 = expected_dates["4_days_ago"]
    d4_entries = get_entries_by_date(d4)
    if d4_entries:
        has_anxious = any(e.get("mood") == "焦虑" for e in d4_entries)
        score_5 = any(e.get("score") == 5 for e in d4_entries)
        if has_anxious and score_5:
            checks.append({"name": "day3_anxious_mood_score5", "passed": True, "detail": f"Correct: 焦虑 mood with score 5 on {d4}"})
            total_score += 0.10
        elif has_anxious or score_5:
            checks.append({"name": "day3_anxious_mood_score5", "passed": False, "detail": f"Partial: mood={[e.get('mood') for e in d4_entries]}, scores={[e.get('score') for e in d4_entries]} on {d4}"})
        else:
            checks.append({"name": "day3_anxious_mood_score5", "passed": False, "detail": f"Expected 焦虑 with score 5 on {d4}, got mood={[e.get('mood') for e in d4_entries]}"})
    else:
        checks.append({"name": "day3_anxious_mood_score5", "passed": False, "detail": f"No entry found for {d4}"})
    
    # --- Check 4: Day 4 (3_days_ago) - UPDATED entry must be 难过 mood with score 3 and 想哭 tag/content ---
    # The original entry would have been 焦虑 (because of "委屈" is actually 难过 keyword)
    # After update: content should contain 想哭, mood=难过, score=3
    d3 = expected_dates["3_days_ago"]
    d3_entries = get_entries_by_date(d3)
    if d3_entries:
        # Find the final state of the entry for this date
        # After update, it should be 难过 with score 3 and contain 想哭
        final_entry = None
        for e in d3_entries:
            if e.get("mood") == "难过" and e.get("score") == 3:
                final_entry = e
                break
        
        if final_entry:
            has_xiang_ku = "想哭" in final_entry.get("raw_text", "") or "想哭" in final_entry.get("content", "")
            if has_xiang_ku:
                checks.append({"name": "day4_updated_nanguo_score3_xiangku", "passed": True, "detail": f"Correct: Updated entry on {d3} has 难过 mood, score 3, and 想哭"})
                total_score += 0.20
            else:
                checks.append({"name": "day4_updated_nanguo_score3_xiangku", "passed": False, "detail": f"Entry has 难过/score3 but missing 想哭 in content/raw_text"})
        else:
            moods_found = [e.get("mood") for e in d3_entries]
            scores_found = [e.get("score") for e in d3_entries]
            checks.append({"name": "day4_updated_nanguo_score3_xiangku", "passed": False, "detail": f"No entry with 难过+score3 on {d3}. Found: moods={moods_found}, scores={scores_found}"})
    else:
        checks.append({"name": "day4_updated_nanguo_score3_xiangku", "passed": False, "detail": f"No entry found for {d3}"})
    
    # --- Check 5: Yesterday entry - 疲惫 mood (triggered by "累" or "没精神") ---
    d_yest = expected_dates["yesterday"]
    yest_entries = get_entries_by_date(d_yest)
    if yest_entries:
        has_tired = any(e.get("mood") == "疲惫" for e in yest_entries)
        if has_tired:
            checks.append({"name": "yesterday_tired_mood", "passed": True, "detail": f"Correct: 疲惫 mood detected on {d_yest}"})
            total_score += 0.10
        else:
            checks.append({"name": "yesterday_tired_mood", "passed": False, "detail": f"Expected 疲惫 on {d_yest}, got {[e.get('mood') for e in yest_entries]}"})
    else:
        checks.append({"name": "yesterday_tired_mood", "passed": False, "detail": f"No entry found for {d_yest}"})
    
    # --- Check 6: Today entry - 开心 mood with score 8 (朋友 tag expected) ---
    d_today = expected_dates["today"]
    today_entries = get_entries_by_date(d_today)
    if today_entries:
        has_happy = any(e.get("mood") == "开心" for e in today_entries)
        score_8 = any(e.get("score") == 8 for e in today_entries)
        if has_happy and score_8:
            checks.append({"name": "today_happy_score8", "passed": True, "detail": f"Correct: 开心 mood with score 8 on {d_today}"})
            total_score += 0.10
        else:
            checks.append({"name": "today_happy_score8", "passed": False, "detail": f"Expected 开心/score8 on {d_today}, got mood={[e.get('mood') for e in today_entries]}, scores={[e.get('score') for e in today_entries]}"})
    else:
        checks.append({"name": "today_happy_score8", "passed": False, "detail": f"No entry found for {d_today}"})
    
    # --- Check 7: trend_report.txt exists and has content ---
    trend_files = list(workspace.rglob("trend_report.txt"))
    if trend_files:
        try:
            with open(trend_files[0], "r", encoding="utf-8") as f:
                trend_content = f.read()
            
            if len(trend_content) > 50:
                # Check for key trend report markers
                has_trend_header = ("趋势" in trend_content or "trend" in trend_content.lower() or "📉" in trend_content)
                has_score_data = any(char.isdigit() for char in trend_content)
                has_week_data = ("周" in trend_content or "week" in trend_content.lower())
                
                if has_trend_header and has_score_data and has_week_data:
                    checks.append({"name": "trend_report_content_valid", "passed": True, "detail": f"trend_report.txt found at {trend_files[0]} with valid trend analysis content ({len(trend_content)} chars)"})
                    total_score += 0.15
                else:
                    checks.append({"name": "trend_report_content_valid", "passed": False, "detail": f"trend_report.txt found but content seems incomplete. has_trend={has_trend_header}, has_score={has_score_data}, has_week={has_week_data}"})
            else:
                checks.append({"name": "trend_report_content_valid", "passed": False, "detail": f"trend_report.txt found but content too short ({len(trend_content)} chars)"})
        except Exception as e:
            checks.append({"name": "trend_report_content_valid", "passed": False, "detail": f"Error reading trend_report.txt: {e}"})
    else:
        checks.append({"name": "trend_report_content_valid", "passed": False, "detail": "trend_report.txt not found anywhere in workspace"})
    
    # --- Check 8: Verify update was actually used (updated_at > created_at for d3 entry) ---
    d3_entries_final = get_entries_by_date(expected_dates["3_days_ago"])
    update_verified = False
    for e in d3_entries_final:
        if e.get("mood") == "难过":
            created = e.get("created_at", "")
            updated = e.get("updated_at", "")
            if created and updated and updated >= created:
                update_verified = True
                break
    
    if update_verified:
        checks.append({"name": "update_command_was_used", "passed": True, "detail": "Entry update confirmed: updated_at timestamp present on the corrected 难过 entry"})
        total_score += 0.05
    else:
        checks.append({"name": "update_command_was_used", "passed": False, "detail": "Could not verify update was used (no 难过 entry with timestamps on day4)"})
    
    # Final pass/fail
    passed = total_score >= 0.60
    
    print(json.dumps({
        "passed": passed,
        "score": round(total_score, 3),
        "checks": checks
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()