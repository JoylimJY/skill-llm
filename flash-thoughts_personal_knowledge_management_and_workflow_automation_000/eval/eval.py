import sys
import json
import re
from pathlib import Path
from datetime import datetime

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []
score_weights = []

def make_check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

# ── Locate flash directory ────────────────────────────────────────────────────
flash_dir = Path.home() / "notes" / "flash"

# ── Check 1: Flash directory exists ──────────────────────────────────────────
check_name = "flash_dir_exists"
try:
    exists = flash_dir.exists() and flash_dir.is_dir()
    checks.append(make_check(check_name, exists,
        f"Flash directory {'found' if exists else 'NOT found'} at {flash_dir}"))
    score_weights.append((exists, 1))
except Exception as e:
    checks.append(make_check(check_name, False, f"Exception: {e}"))
    score_weights.append((False, 1))

# ── Check 2: At least one .md file created today ─────────────────────────────
check_name = "daily_md_file_exists"
try:
    today_str = datetime.now().strftime("%Y-%m-%d")
    md_files = list(flash_dir.glob("*.md")) if flash_dir.exists() else []
    today_files = [f for f in md_files if f.stem == today_str]
    passed = len(today_files) >= 1
    checks.append(make_check(check_name, passed,
        f"Found today's file(s): {[f.name for f in today_files]}"))
    score_weights.append((passed, 2))
except Exception as e:
    checks.append(make_check(check_name, False, f"Exception: {e}"))
    score_weights.append((False, 2))

# ── Check 3: File has correct header format "# YYYY-MM-DD 闪念" ──────────────
check_name = "correct_file_header"
try:
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_file = flash_dir / f"{today_str}.md"
    if today_file.exists():
        content = today_file.read_text(encoding="utf-8")
        header_pattern = re.compile(rf"^# {re.escape(today_str)} 闪念", re.MULTILINE)
        passed = bool(header_pattern.search(content))
        checks.append(make_check(check_name, passed,
            f"Header '# {today_str} 闪念' {'found' if passed else 'NOT found'} in file"))
    else:
        passed = False
        checks.append(make_check(check_name, False, f"Today's file does not exist: {today_file}"))
    score_weights.append((passed, 2))
except Exception as e:
    checks.append(make_check(check_name, False, f"Exception: {e}"))
    score_weights.append((False, 2))

# ── Check 4: Separator lines (---) present ───────────────────────────────────
check_name = "separator_lines_present"
try:
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_file = flash_dir / f"{today_str}.md"
    if today_file.exists():
        content = today_file.read_text(encoding="utf-8")
        separator_count = len(re.findall(r"^---\s*$", content, re.MULTILINE))
        passed = separator_count >= 2  # at least 2 separators for 3 thoughts
        checks.append(make_check(check_name, passed,
            f"Found {separator_count} separator line(s) ('---'). Expected >= 2."))
    else:
        passed = False
        checks.append(make_check(check_name, False, "Today's file does not exist"))
    score_weights.append((passed, 2))
except Exception as e:
    checks.append(make_check(check_name, False, f"Exception: {e}"))
    score_weights.append((False, 2))

# ── Check 5: Time-headed entries format "## HH:MM - <content>" ───────────────
check_name = "time_headed_entries"
try:
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_file = flash_dir / f"{today_str}.md"
    if today_file.exists():
        content = today_file.read_text(encoding="utf-8")
        time_headers = re.findall(r"^## \d{2}:\d{2} - .+", content, re.MULTILINE)
        passed = len(time_headers) >= 3
        checks.append(make_check(check_name, passed,
            f"Found {len(time_headers)} time-headed entries. Expected >= 3. Examples: {time_headers[:3]}"))
    else:
        passed = False
        checks.append(make_check(check_name, False, "Today's file does not exist"))
    score_weights.append((passed, 3))
except Exception as e:
    checks.append(make_check(check_name, False, f"Exception: {e}"))
    score_weights.append((False, 3))

# ── Check 6: All 3 required thoughts are present in file ─────────────────────
check_name = "all_three_thoughts_present"
required_keywords = ["quantum", "federated", "anomaly"]
try:
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_file = flash_dir / f"{today_str}.md"
    if today_file.exists():
        content = today_file.read_text(encoding="utf-8").lower()
        found = [kw for kw in required_keywords if kw in content]
        passed = len(found) == 3
        checks.append(make_check(check_name, passed,
            f"Found keywords: {found}. Missing: {[k for k in required_keywords if k not in found]}"))
    else:
        passed = False
        checks.append(make_check(check_name, False, "Today's file does not exist"))
    score_weights.append((passed, 3))
except Exception as e:
    checks.append(make_check(check_name, False, f"Exception: {e}"))
    score_weights.append((False, 3))

# ── Check 7: Search for "genomics" returns results ───────────────────────────
check_name = "search_genomics_works"
try:
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_file = flash_dir / f"{today_str}.md"
    if today_file.exists():
        content = today_file.read_text(encoding="utf-8").lower()
        passed = "genomics" in content
        checks.append(make_check(check_name, passed,
            f"Keyword 'genomics' {'found' if passed else 'NOT found'} in flash files"))
    else:
        passed = False
        checks.append(make_check(check_name, False, "Today's file does not exist, cannot verify search"))
    score_weights.append((passed, 2))
except Exception as e:
    checks.append(make_check(check_name, False, f"Exception: {e}"))
    score_weights.append((False, 2))

# ── Check 8: File is stored in ~/notes/flash/ (not workspace or elsewhere) ───
check_name = "correct_storage_location"
try:
    expected_dir = Path.home() / "notes" / "flash"
    if expected_dir.exists():
        md_files = list(expected_dir.glob("*.md"))
        passed = len(md_files) >= 1
        checks.append(make_check(check_name, passed,
            f"Found {len(md_files)} .md file(s) in correct location: {expected_dir}"))
    else:
        passed = False
        checks.append(make_check(check_name, False,
            f"Expected storage directory not found: {expected_dir}"))
    score_weights.append((passed, 2))
except Exception as e:
    checks.append(make_check(check_name, False, f"Exception: {e}"))
    score_weights.append((False, 2))

# ── Compute final score ───────────────────────────────────────────────────────
total_weight = sum(w for _, w in score_weights)
earned_weight = sum(w for passed, w in score_weights if passed)
score = round(earned_weight / total_weight, 4) if total_weight > 0 else 0.0
all_passed = all(c["passed"] for c in checks)

result = {
    "passed": all_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, ensure_ascii=False, indent=2))