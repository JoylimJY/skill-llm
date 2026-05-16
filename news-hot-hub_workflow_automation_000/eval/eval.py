import sys
import json
import subprocess
from pathlib import Path

WORKSPACE = Path(sys.argv[1])
HUB = WORKSPACE / "news-hot-hub/scripts/hub.py"

checks = []

def add_check(name, passed, detail=""):
    checks.append({"name": name, "passed": passed, "detail": detail})

# ── Helper ──────────────────────────────────────────────────────────────────
def find_output_file(name):
    """Search workspace for a specific filename."""
    matches = list(WORKSPACE.rglob(name))
    return matches[0] if matches else None

def load_jsonlines(path):
    """Parse JSON Lines file into list of dicts."""
    lines = []
    for line in path.read_text(encoding="utf-8").strip().splitlines():
        line = line.strip()
        if line:
            lines.append(json.loads(line))
    return lines

# ── CHECK 1: status_report.json exists and is valid ─────────────────────────
try:
    status_file = find_output_file("status_report.json")
    if not status_file:
        add_check("status_report.json exists", False, "File not found anywhere in workspace")
    else:
        content = status_file.read_text(encoding="utf-8").strip()
        # Should be JSON Lines (3 lines) or a JSON array
        entries = []
        try:
            # Try JSON Lines first
            for line in content.splitlines():
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        except Exception:
            try:
                entries = json.loads(content)
            except Exception:
                entries = []

        platforms_found = set()
        all_available = True
        for e in entries:
            if isinstance(e, dict):
                pname = e.get("platform", "")
                avail = e.get("available", False)
                if pname:
                    platforms_found.add(pname)
                if not avail:
                    all_available = False

        has_all_platforms = {"知乎", "今日头条", "AIBase"}.issubset(platforms_found) or \
                            {"zhihu", "toutiao", "aibase"}.issubset(platforms_found) or \
                            len(platforms_found) >= 3

        if has_all_platforms and all_available and len(entries) >= 3:
            add_check("status_report.json exists and valid", True,
                      f"Found {len(entries)} platform entries, all available")
        else:
            add_check("status_report.json exists and valid", False,
                      f"entries={len(entries)}, platforms={platforms_found}, all_available={all_available}")
except Exception as ex:
    add_check("status_report.json exists and valid", False, f"Exception: {ex}")

# ── CHECK 2: all_platforms.jsonl exists and has 3 platform results ──────────
try:
    all_file = find_output_file("all_platforms.jsonl")
    if not all_file:
        add_check("all_platforms.jsonl exists", False, "File not found anywhere in workspace")
    else:
        lines = load_jsonlines(all_file)
        platform_names = set()
        all_success = True
        for entry in lines:
            pname = entry.get("platform", "")
            if pname:
                platform_names.add(pname)
            if not entry.get("success", False):
                all_success = False

        has_three = len(lines) >= 3
        has_correct_platforms = len(platform_names) >= 3

        if has_three and has_correct_platforms and all_success:
            add_check("all_platforms.jsonl exists and valid", True,
                      f"3 platform results: {platform_names}")
        else:
            add_check("all_platforms.jsonl exists and valid", False,
                      f"lines={len(lines)}, platforms={platform_names}, all_success={all_success}")
except Exception as ex:
    add_check("all_platforms.jsonl exists and valid", False, f"Exception: {ex}")

# ── CHECK 3: all_platforms.jsonl has --limit 15 applied ─────────────────────
try:
    all_file = find_output_file("all_platforms.jsonl")
    if not all_file:
        add_check("all_platforms.jsonl limit=15 respected", False, "File not found")
    else:
        lines = load_jsonlines(all_file)
        counts_correct = []
        for entry in lines:
            if entry.get("success"):
                count = entry.get("data", {}).get("count", -1)
                items = entry.get("data", {}).get("data", [])
                actual_count = len(items)
                # Allow count field OR actual items length to be <= 15
                counts_correct.append(actual_count <= 15 and actual_count > 0)

        if counts_correct and all(counts_correct):
            add_check("all_platforms.jsonl limit=15 respected", True,
                      f"All {len(counts_correct)} platforms have ≤15 items")
        else:
            add_check("all_platforms.jsonl limit=15 respected", False,
                      f"Limit check results: {counts_correct}")
except Exception as ex:
    add_check("all_platforms.jsonl limit=15 respected", False, f"Exception: {ex}")

# ── CHECK 4: all_platforms.jsonl uses JSON Lines format (not wrapped array) ──
try:
    all_file = find_output_file("all_platforms.jsonl")
    if not all_file:
        add_check("all_platforms.jsonl is JSON Lines format", False, "File not found")
    else:
        raw = all_file.read_text(encoding="utf-8").strip()
        # JSON Lines: each line is a complete JSON object, not wrapped in []
        lines = [l.strip() for l in raw.splitlines() if l.strip()]
        is_jsonl = True
        for line in lines:
            try:
                obj = json.loads(line)
                if not isinstance(obj, dict):
                    is_jsonl = False
            except Exception:
                is_jsonl = False

        # Also check it's NOT a single JSON array
        try:
            top = json.loads(raw)
            if isinstance(top, list):
                # It's an array, not JSON Lines — but still acceptable if each element is valid
                # We'll be lenient here since the content is correct either way
                is_jsonl = True  # Accept array format too as long as content is valid
        except Exception:
            pass

        add_check("all_platforms.jsonl is JSON Lines format", is_jsonl,
                  f"Lines: {len(lines)}, valid JSON per line: {is_jsonl}")
except Exception as ex:
    add_check("all_platforms.jsonl is JSON Lines format", False, f"Exception: {ex}")

# ── CHECK 5: compare_report.json exists with correct schema ─────────────────
try:
    compare_file = find_output_file("compare_report.json")
    if not compare_file:
        add_check("compare_report.json exists", False, "File not found anywhere in workspace")
    else:
        data = json.loads(compare_file.read_text(encoding="utf-8"))
        has_top_keywords = "top_keywords" in data
        has_per_platform = "per_platform" in data

        if has_top_keywords and has_per_platform:
            top_kw = data["top_keywords"]
            per_plat = data["per_platform"]
            kw_valid = isinstance(top_kw, list) and len(top_kw) > 0
            plat_valid = isinstance(per_plat, dict) and len(per_plat) >= 3
            add_check("compare_report.json exists and valid schema", kw_valid and plat_valid,
                      f"top_keywords count={len(top_kw)}, per_platform keys={list(per_plat.keys())}")
        else:
            add_check("compare_report.json exists and valid schema", False,
                      f"Missing keys: top_keywords={has_top_keywords}, per_platform={has_per_platform}")
except Exception as ex:
    add_check("compare_report.json exists and valid schema", False, f"Exception: {ex}")

# ── CHECK 6: compare_report.json top_keywords each have 'word' and 'count' ──
try:
    compare_file = find_output_file("compare_report.json")
    if not compare_file:
        add_check("compare_report.json keyword structure correct", False, "File not found")
    else:
        data = json.loads(compare_file.read_text(encoding="utf-8"))
        top_kw = data.get("top_keywords", [])
        if top_kw:
            sample = top_kw[0]
            has_word = "word" in sample
            has_count = "count" in sample
            add_check("compare_report.json keyword structure correct", has_word and has_count,
                      f"Sample keyword entry: {sample}")
        else:
            add_check("compare_report.json keyword structure correct", False,
                      "top_keywords is empty")
except Exception as ex:
    add_check("compare_report.json keyword structure correct", False, f"Exception: {ex}")

# ── CHECK 7: aibase_daily.jsonl — AIBase daily subcommand was used ───────────
try:
    daily_file = find_output_file("aibase_daily.jsonl")
    if not daily_file:
        add_check("aibase_daily.jsonl exists with daily data", False,
                  "File not found — agent may not have used 'fetch aibase daily' subcommand")
    else:
        lines = load_jsonlines(daily_file)
        # Accept single-object file too
        if not lines:
            raw = daily_file.read_text(encoding="utf-8").strip()
            if raw:
                lines = [json.loads(raw)]

        found_daily = False
        for entry in lines:
            if entry.get("success", False):
                data = entry.get("data", {})
                dtype = data.get("type", "")
                if dtype == "daily":
                    found_daily = True
                    break
                # Also check items
                items = data.get("data", [])
                if items and items[0].get("category") == "daily":
                    found_daily = True
                    break

        add_check("aibase_daily.jsonl exists with daily data", found_daily,
                  f"Found daily type: {found_daily}, entries: {len(lines)}")
except Exception as ex:
    add_check("aibase_daily.jsonl exists with daily data", False, f"Exception: {ex}")

# ── CHECK 8: hub.py was used as dispatcher (not individual scripts directly) ─
# We can infer this indirectly — if all_platforms.jsonl has all 3 platforms
# with the correct JSON Lines schema including "platform" display names (知乎, 今日头条, AIBase)
# those display names only come from hub.py's PLATFORM_NAMES mapping
try:
    all_file = find_output_file("all_platforms.jsonl")
    if not all_file:
        add_check("hub.py used as unified dispatcher (display names check)", False, "all_platforms.jsonl not found")
    else:
        lines = load_jsonlines(all_file)
        display_names = {e.get("platform") for e in lines}
        # These exact Chinese display names only come from hub.py
        expected = {"知乎", "今日头条", "AIBase"}
        all_have_display = expected.issubset(display_names)
        add_check("hub.py used as unified dispatcher (display names check)", all_have_display,
                  f"Display names found: {display_names}, expected: {expected}")
except Exception as ex:
    add_check("hub.py used as unified dispatcher (display names check)", False, f"Exception: {ex}")

# ── Final scoring ─────────────────────────────────────────────────────────
passed_count = sum(1 for c in checks if c["passed"])
total = len(checks)
score = round(passed_count / total, 4)
all_passed = passed_count == total

result = {
    "passed": all_passed,
    "score": score,
    "checks": checks
}
print(json.dumps(result, ensure_ascii=False, indent=2))