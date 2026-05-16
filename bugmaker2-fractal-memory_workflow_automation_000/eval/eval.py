import sys
import json
import os
from pathlib import Path
from datetime import date

workspace = Path(sys.argv[1])

checks = []
total_score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0

# ── 1. Directory structure: memory/diary/YYYY/{daily,weekly,monthly} ──────────
today = date.today()
year = today.strftime("%Y")

required_dirs = {
    f"memory/diary/{year}/daily": "daily log directory",
    f"memory/diary/{year}/weekly": "weekly summary directory",
    f"memory/diary/{year}/monthly": "monthly summary directory",
    "memory/diary/sticky-notes/workflows": "sticky-notes/workflows",
    "memory/diary/sticky-notes/apis": "sticky-notes/apis",
    "memory/diary/sticky-notes/commands": "sticky-notes/commands",
    "memory/diary/sticky-notes/facts": "sticky-notes/facts",
}

all_dirs_ok = True
dir_details = []
for d, label in required_dirs.items():
    full_path = workspace / d
    if full_path.is_dir():
        dir_details.append(f"✓ {d}")
    else:
        dir_details.append(f"✗ MISSING: {d}")
        all_dirs_ok = False

total_score += add_check(
    "Correct fractal directory structure created",
    all_dirs_ok,
    "; ".join(dir_details),
    weight=2.0
)

# ── 2. Flat daily files migrated to memory/diary/YYYY/daily/ ─────────────────
expected_migrated = [
    f"memory/diary/2026/daily/2026-01-13.md",
    f"memory/diary/2026/daily/2026-01-14.md",
    f"memory/diary/2026/daily/2026-01-15.md",
    f"memory/diary/2026/daily/2026-01-16.md",
    f"memory/diary/2026/daily/2026-01-17.md",
]

migrated_ok = True
migrated_details = []
for f in expected_migrated:
    p = workspace / f
    if p.exists() and p.stat().st_size > 0:
        migrated_details.append(f"✓ {f}")
    else:
        migrated_details.append(f"✗ MISSING/EMPTY: {f}")
        migrated_ok = False

total_score += add_check(
    "Flat daily files migrated to diary/YYYY/daily/ hierarchy",
    migrated_ok,
    "; ".join(migrated_details),
    weight=2.0
)

# ── 3. rollup-state.json exists and has correct schema ───────────────────────
rollup_state_path = workspace / "memory" / "rollup-state.json"
rollup_state_ok = False
rollup_state_detail = ""
try:
    if rollup_state_path.exists():
        state = json.loads(rollup_state_path.read_text())
        required_keys = {"lastDailyRollup", "lastWeeklyRollup", "lastMonthlyRollup", "currentWeek", "currentMonth"}
        missing_keys = required_keys - set(state.keys())
        if not missing_keys:
            rollup_state_ok = True
            rollup_state_detail = f"All required keys present: {sorted(required_keys)}"
        else:
            rollup_state_detail = f"Missing keys: {sorted(missing_keys)}. Found keys: {sorted(state.keys())}"
    else:
        rollup_state_detail = "memory/rollup-state.json does not exist"
except Exception as e:
    rollup_state_detail = f"Error reading rollup-state.json: {e}"

total_score += add_check(
    "rollup-state.json has correct schema (lastDailyRollup, lastWeeklyRollup, lastMonthlyRollup, currentWeek, currentMonth)",
    rollup_state_ok,
    rollup_state_detail,
    weight=2.0
)

# ── 4. heartbeat-state.json exists and has correct schema ────────────────────
heartbeat_path = workspace / "memory" / "heartbeat-state.json"
heartbeat_ok = False
heartbeat_detail = ""
try:
    if heartbeat_path.exists():
        hb = json.loads(heartbeat_path.read_text())
        if "lastMoltbookCheck" in hb:
            heartbeat_ok = True
            heartbeat_detail = f"Key 'lastMoltbookCheck' present. Value: {hb['lastMoltbookCheck']}"
        else:
            heartbeat_detail = f"Missing key 'lastMoltbookCheck'. Found: {list(hb.keys())}"
    else:
        heartbeat_detail = "memory/heartbeat-state.json does not exist"
except Exception as e:
    heartbeat_detail = f"Error reading heartbeat-state.json: {e}"

total_score += add_check(
    "heartbeat-state.json has correct schema (lastMoltbookCheck key)",
    heartbeat_ok,
    heartbeat_detail,
    weight=1.5
)

# ── 5. rollup-state.json lastDailyRollup was updated (not None) ──────────────
rollup_ran_ok = False
rollup_ran_detail = ""
try:
    if rollup_state_path.exists():
        state = json.loads(rollup_state_path.read_text())
        last_daily = state.get("lastDailyRollup")
        if last_daily is not None and isinstance(last_daily, str) and len(last_daily) > 5:
            rollup_ran_ok = True
            rollup_ran_detail = f"lastDailyRollup = {last_daily}"
        else:
            rollup_ran_detail = f"lastDailyRollup is still null/empty: {last_daily}"
    else:
        rollup_ran_detail = "rollup-state.json missing"
except Exception as e:
    rollup_ran_detail = f"Error: {e}"

total_score += add_check(
    "rollup-daily.py was executed (lastDailyRollup updated in rollup-state.json)",
    rollup_ran_ok,
    rollup_ran_detail,
    weight=1.5
)

# ── 6. Weekly file generated with correct ISO week naming (YYYY-Wnn.md) ──────
weekly_dir = workspace / f"memory/diary/{year}/weekly"
weekly_ok = False
weekly_detail = ""
try:
    if weekly_dir.is_dir():
        weekly_files = list(weekly_dir.glob("*.md"))
        # Check naming convention: YYYY-Wnn.md
        import re
        valid_weekly = [f for f in weekly_files if re.match(r'^\d{4}-W\d{2}\.md$', f.name)]
        if valid_weekly:
            weekly_ok = True
            weekly_detail = f"Found valid weekly files: {[f.name for f in valid_weekly]}"
        else:
            weekly_detail = f"No valid YYYY-Wnn.md files found. Files present: {[f.name for f in weekly_files]}"
    else:
        weekly_detail = f"Weekly directory missing: {weekly_dir}"
except Exception as e:
    weekly_detail = f"Error: {e}"

total_score += add_check(
    "Weekly summary file created with correct ISO week naming (YYYY-Wnn.md)",
    weekly_ok,
    weekly_detail,
    weight=1.5
)

# ── 7. Non-date flat files NOT migrated (scratch.md, ideas.md) ───────────────
distractor_migrated = []
for distractor in ["scratch.md", "ideas.md"]:
    if (workspace / "memory" / "diary" / "2026" / "daily" / distractor).exists():
        distractor_migrated.append(distractor)

distractor_ok = len(distractor_migrated) == 0
total_score += add_check(
    "Non-date files (scratch.md, ideas.md) were NOT migrated to daily/",
    distractor_ok,
    f"Wrongly migrated: {distractor_migrated}" if distractor_migrated else "No distractor files were incorrectly migrated",
    weight=1.0
)

# ── 8. AGENTS.md updated with context loading order ──────────────────────────
agents_md = workspace / "AGENTS.md"
agents_ok = False
agents_detail = ""
try:
    if agents_md.exists():
        content = agents_md.read_text()
        # Check for key phrases indicating correct context loading order
        checks_content = [
            ("daily" in content.lower() or "YYYY-MM-DD" in content),
            ("weekly" in content.lower() or "YYYY-Wnn" in content or "this week" in content.lower()),
            ("monthly" in content.lower() or "YYYY-MM" in content or "this month" in content.lower()),
            ("MEMORY.md" in content),
        ]
        passed_count = sum(checks_content)
        if passed_count >= 3:
            agents_ok = True
            agents_detail = f"AGENTS.md contains context loading hierarchy references ({passed_count}/4 checks passed)"
        else:
            agents_detail = f"AGENTS.md lacks complete context loading order ({passed_count}/4 checks). Content snippet: {content[:300]}"
    else:
        agents_detail = "AGENTS.md does not exist"
except Exception as e:
    agents_detail = f"Error reading AGENTS.md: {e}"

total_score += add_check(
    "AGENTS.md updated with correct memory context loading order",
    agents_ok,
    agents_detail,
    weight=1.0
)

# ── Normalize score to 0-1 range ─────────────────────────────────────────────
max_score = 2.0 + 2.0 + 2.0 + 1.5 + 1.5 + 1.5 + 1.0 + 1.0  # = 12.5
normalized_score = round(total_score / max_score, 4)
all_passed = all(c["passed"] for c in checks)

result = {
    "passed": all_passed,
    "score": normalized_score,
    "checks": checks
}

print(json.dumps(result, indent=2))