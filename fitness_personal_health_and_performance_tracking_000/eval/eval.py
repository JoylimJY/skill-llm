import sys
import json
import re
import os
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    
    # ── Locate memory.md ──────────────────────────────────────────────────────
    # Primary location per SKILL.md: ~/fitness/memory.md
    home = Path.home()
    primary_path = home / "fitness" / "memory.md"
    
    memory_path = None
    if primary_path.exists():
        memory_path = primary_path
    else:
        # Fallback: search workspace
        candidates = list(Path(workspace).rglob("memory.md"))
        if candidates:
            memory_path = candidates[0]
    
    if memory_path is None:
        checks.append({"name": "file_exists", "passed": False, "detail": "memory.md not found at ~/fitness/memory.md or anywhere in workspace"})
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}
    
    checks.append({"name": "file_exists", "passed": True, "detail": f"Found memory.md at {memory_path}"})
    
    try:
        content = memory_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": f"Could not read file: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "file_readable", "passed": True, "detail": "File is readable"})
    
    # ── Check 1: Required section headers (proprietary format) ─────────────────
    required_sections = ["### Sources", "### Schedule", "### Correlations", "### Preferences", "### Flags", "### Achievements"]
    missing_sections = [s for s in required_sections if s not in content]
    sections_ok = len(missing_sections) == 0
    checks.append({
        "name": "required_sections_present",
        "passed": sections_ok,
        "detail": f"Missing sections: {missing_sections}" if missing_sections else "All 6 required sections present with correct ### headers"
    })
    
    content_lower = content.lower()
    
    # ── Check 2: Sources section — multi-source data absorption ───────────────
    # Must include garmin/garmin-connect AND strava AND conversation/chat
    sources_match = re.search(r'### Sources(.*?)###', content, re.DOTALL)
    sources_text = sources_match.group(1).lower() if sources_match else ""
    has_garmin = bool(re.search(r'garmin', sources_text))
    has_strava = bool(re.search(r'strava', sources_text))
    has_conversation = bool(re.search(r'conversation|chat', sources_text))
    sources_ok = has_garmin and has_strava and has_conversation
    checks.append({
        "name": "sources_multi_source",
        "passed": sources_ok,
        "detail": f"garmin={has_garmin}, strava={has_strava}, conversation={has_conversation}. Sources text (first 300 chars): {sources_text[:300]}"
    })
    
    # ── Check 3: Schedule section — training pattern detection ─────────────────
    schedule_match = re.search(r'### Schedule(.*?)###', content, re.DOTALL)
    schedule_text = schedule_match.group(1).lower() if schedule_match else ""
    # Should detect swim/bike/run triathlon pattern, AM sessions
    has_swim = bool(re.search(r'swim', schedule_text))
    has_bike = bool(re.search(r'bike|cycling|cycle', schedule_text))
    has_run = bool(re.search(r'run', schedule_text))
    schedule_ok = has_swim and has_bike and has_run
    checks.append({
        "name": "schedule_triathlon_pattern",
        "passed": schedule_ok,
        "detail": f"swim={has_swim}, bike={has_bike}, run={has_run}. Schedule text (first 300 chars): {schedule_text[:300]}"
    })
    
    # ── Check 4: Correlations — alcohol→bad performance, sleep, coffee ─────────
    corr_match = re.search(r'### Correlations(.*?)###', content, re.DOTALL)
    corr_text = corr_match.group(1).lower() if corr_match else ""
    has_alcohol_neg = bool(re.search(r'alcohol', corr_text)) and bool(re.search(r'next.?day|performance|-|poor|bad|destroy|negative', corr_text))
    has_coffee_pos = bool(re.search(r'coffee', corr_text)) and bool(re.search(r'intensity|\+|positive|boost|strong', corr_text))
    has_sleep = bool(re.search(r'sleep', corr_text))
    corr_ok = has_alcohol_neg and has_coffee_pos and has_sleep
    checks.append({
        "name": "correlations_key_factors",
        "passed": corr_ok,
        "detail": f"alcohol_negative={has_alcohol_neg}, coffee_positive={has_coffee_pos}, sleep={has_sleep}. Corr text (first 400 chars): {corr_text[:400]}"
    })
    
    # ── Check 5: Preferences — experienced athlete = less proactivity needed ───
    prefs_match = re.search(r'### Preferences(.*?)###', content, re.DOTALL)
    prefs_text = prefs_match.group(1).lower() if prefs_match else ""
    # Athlete explicitly said "just give me the data", "weekly summary is all i need"
    # So preferences should reflect autonomy, weekly summary, NOT daily check-ins/reminders
    has_weekly_summary = bool(re.search(r'weekly.{0,20}summary|summary.{0,20}only|weekly.{0,20}update', prefs_text))
    # Should NOT have "remind before workouts" type preferences for a beginner
    has_no_daily_lectures = not bool(re.search(r'remind before|daily.{0,20}check|daily.{0,20}reminder', prefs_text))
    # Should reflect autonomy / data-driven preference
    has_data_driven = bool(re.search(r'data|no.{0,20}lecture|no.{0,20}guilt|autonomy|self.{0,20}direct|own.{0,20}call', prefs_text))
    prefs_ok = has_weekly_summary and has_no_daily_lectures and has_data_driven
    checks.append({
        "name": "preferences_experienced_athlete",
        "passed": prefs_ok,
        "detail": f"weekly_summary={has_weekly_summary}, no_daily_lectures={has_no_daily_lectures}, data_driven={has_data_driven}. Prefs text (first 400 chars): {prefs_text[:400]}"
    })
    
    # ── Check 6: Flags — specific signals from SKILL.md + data ────────────────
    flags_match = re.search(r'### Flags(.*?)###', content, re.DOTALL)
    flags_text = flags_match.group(1).lower() if flags_match else ""
    # "too tired" is explicitly mentioned in SKILL.md flags and in data
    has_too_tired = bool(re.search(r'too.{0,5}tired', flags_text))
    # Injury/knee mention from chat logs
    has_injury = bool(re.search(r'injur|knee|sore', flags_text))
    # HRV crash / low HRV is a key signal from garmin data
    has_hrv = bool(re.search(r'hrv', flags_text))
    # "legs are dead" from SKILL.md example / chat logs
    has_legs_dead = bool(re.search(r'legs.{0,10}dead|dead.{0,10}legs', flags_text))
    flags_ok = has_too_tired and has_injury and has_hrv
    checks.append({
        "name": "flags_key_signals",
        "passed": flags_ok,
        "detail": f"too_tired={has_too_tired}, injury={has_injury}, hrv={has_hrv}, legs_dead={has_legs_dead}. Flags text (first 400 chars): {flags_text[:400]}"
    })
    
    # ── Check 7: Achievements — Kona finish, FTP PR, sub-10 goal ──────────────
    ach_match = re.search(r'### Achievements(.*?)$', content, re.DOTALL)
    ach_text = ach_match.group(1).lower() if ach_match else ""
    # Kona / Ironman World Championship finish
    has_kona = bool(re.search(r'kona|ironman.{0,30}world|world.{0,30}championship', ach_text))
    # Must have a date (YYYY-MM format per spec, or YYYY-MM-DD)
    has_kona_date = bool(re.search(r'kona|ironman.{0,50}2024', ach_text))
    # FTP PR 318w
    has_ftp = bool(re.search(r'ftp|318', ach_text))
    # Sub-10 achievement
    has_sub10 = bool(re.search(r'sub.?10|9:47|9h47', ach_text))
    ach_ok = has_kona and has_kona_date and has_ftp and has_sub10
    checks.append({
        "name": "achievements_key_milestones",
        "passed": ach_ok,
        "detail": f"kona={has_kona}, kona_date={has_kona_date}, ftp={has_ftp}, sub10={has_sub10}. Achievements text (first 400 chars): {ach_text[:400]}"
    })
    
    # ── Check 8: Format integrity — SKILL.md specifies comment-style format hints ──
    # The spec shows HTML comment placeholders; the actual data should be below them
    # At minimum: no sections should be entirely empty (agent must have filled them)
    def section_has_content(section_name: str) -> bool:
        pattern = rf'### {section_name}(.*?)(?=###|$)'
        m = re.search(pattern, content, re.DOTALL)
        if not m:
            return False
        section_body = m.group(1)
        # Strip HTML comments and whitespace
        stripped = re.sub(r'<!--.*?-->', '', section_body, flags=re.DOTALL).strip()
        return len(stripped) > 10  # Must have substantive content
    
    empty_sections = [s.replace('### ', '') for s in required_sections if not section_has_content(s.replace('### ', ''))]
    format_ok = len(empty_sections) == 0
    checks.append({
        "name": "all_sections_filled",
        "passed": format_ok,
        "detail": f"Empty/near-empty sections: {empty_sections}" if not format_ok else "All sections contain substantive content"
    })
    
    # ── Check 9: No guilt / negative framing about missed workouts ─────────────
    # SKILL.md: "Never guilt missed workouts"
    # Flags or Preferences should not contain guilt-trip language
    guilt_patterns = [r'you missed', r'should have', r'failed to', r'skipped again', r'lazy']
    has_guilt = any(bool(re.search(p, content_lower)) for p in guilt_patterns)
    no_guilt_ok = not has_guilt
    checks.append({
        "name": "no_guilt_language",
        "passed": no_guilt_ok,
        "detail": "No guilt language detected" if no_guilt_ok else "Detected guilt-trip language which violates SKILL.md rules"
    })
    
    # ── Score calculation ──────────────────────────────────────────────────────
    weights = {
        "file_exists": 0.05,
        "file_readable": 0.02,
        "required_sections_present": 0.13,
        "sources_multi_source": 0.10,
        "schedule_triathlon_pattern": 0.08,
        "correlations_key_factors": 0.15,
        "preferences_experienced_athlete": 0.15,
        "flags_key_signals": 0.12,
        "achievements_key_milestones": 0.12,
        "all_sections_filled": 0.05,
        "no_guilt_language": 0.03,
    }
    
    score = 0.0
    for check in checks:
        w = weights.get(check["name"], 0.0)
        if check["passed"]:
            score += w
    
    passed = score >= 0.75
    
    return {"passed": passed, "score": round(score, 3), "checks": checks}


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))