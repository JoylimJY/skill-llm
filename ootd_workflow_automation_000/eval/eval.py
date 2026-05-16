#!/usr/bin/env python3
"""
Evaluation script for the OOTD skill task.
Usage: python3 eval_script.py <workspace_dir>
"""
import sys
import json
import re
import pathlib
import subprocess

workspace = pathlib.Path(sys.argv[1]).expanduser().resolve()
home      = pathlib.Path("~").expanduser()
openclaw_workspace = home / ".openclaw" / "workspace"

checks = []
total_weight = 0.0
earned_weight = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global total_weight, earned_weight
    total_weight += weight
    if passed:
        earned_weight += weight

# ── CHECK 1: wardrobe.json exists at the correct path ────────────────────────
wardrobe_path = openclaw_workspace / "wardrobe.json"
try:
    exists = wardrobe_path.exists()
    add_check(
        "wardrobe.json exists at ~/.openclaw/workspace/",
        exists,
        f"Found at {wardrobe_path}" if exists else f"Not found at {wardrobe_path}",
        weight=1.5
    )
except Exception as e:
    add_check("wardrobe.json exists at ~/.openclaw/workspace/", False, f"Exception: {e}", weight=1.5)

# ── CHECK 2: wardrobe.json uses correct top-level "items" key ────────────────
wardrobe_data = None
try:
    if wardrobe_path.exists():
        raw = wardrobe_path.read_text()
        wardrobe_data = json.loads(raw)
        has_items_key = "items" in wardrobe_data and isinstance(wardrobe_data["items"], list)
        add_check(
            "wardrobe.json uses top-level 'items' array (not 'clothes' or other)",
            has_items_key,
            f"Keys found: {list(wardrobe_data.keys())}" if wardrobe_data else "Could not parse JSON",
            weight=2.0
        )
    else:
        add_check("wardrobe.json uses top-level 'items' array", False, "File not found", weight=2.0)
except Exception as e:
    add_check("wardrobe.json uses top-level 'items' array", False, f"Exception parsing JSON: {e}", weight=2.0)

# ── CHECK 3: Each wardrobe item has all required schema fields ────────────────
try:
    if wardrobe_data and "items" in wardrobe_data:
        items = wardrobe_data["items"]
        required_fields = {"name", "type", "tags", "min_temp", "max_temp"}
        all_valid = True
        bad_items = []
        if len(items) == 0:
            all_valid = False
            bad_items.append("No items found — list is empty")
        for i, item in enumerate(items):
            missing = required_fields - set(item.keys())
            if missing:
                all_valid = False
                bad_items.append(f"Item {i} missing fields: {missing}")
            if not isinstance(item.get("tags", None), list):
                all_valid = False
                bad_items.append(f"Item {i}: 'tags' must be a list")
            min_t = item.get("min_temp")
            max_t = item.get("max_temp")
            if not isinstance(min_t, (int, float)) or not isinstance(max_t, (int, float)):
                all_valid = False
                bad_items.append(f"Item {i}: min_temp/max_temp must be numbers")
        add_check(
            "All wardrobe items have correct schema (name, type, tags[], min_temp, max_temp)",
            all_valid,
            "All items valid" if all_valid else "; ".join(bad_items),
            weight=2.5
        )
    else:
        add_check("All wardrobe items have correct schema", False, "No valid items array to check", weight=2.5)
except Exception as e:
    add_check("All wardrobe items have correct schema", False, f"Exception: {e}", weight=2.5)

# ── CHECK 4: At least one wardrobe item covers the cold-weather range (≤55°F) ─
try:
    if wardrobe_data and "items" in wardrobe_data:
        items = wardrobe_data["items"]
        cold_temp = 45  # mock weather returns 45°F
        cold_items = [
            i for i in items
            if isinstance(i.get("min_temp"), (int, float))
            and isinstance(i.get("max_temp"), (int, float))
            and i["min_temp"] <= cold_temp <= i["max_temp"]
        ]
        has_cold_item = len(cold_items) > 0
        add_check(
            "At least one wardrobe item covers 45°F (cold Chicago conditions)",
            has_cold_item,
            f"Items covering 45°F: {[i.get('name','?') for i in cold_items]}" if has_cold_item
            else "No items with min_temp <= 45 <= max_temp found",
            weight=2.0
        )
    else:
        add_check("At least one wardrobe item covers 45°F", False, "No items array", weight=2.0)
except Exception as e:
    add_check("At least one wardrobe item covers 45°F", False, f"Exception: {e}", weight=2.0)

# ── CHECK 5: USER.md contains a style preference ─────────────────────────────
user_md_path = openclaw_workspace / "USER.md"
try:
    if user_md_path.exists():
        user_text = user_md_path.read_text()
        style_patterns = [
            r"style[:\s]+([^\n]+)",
            r"prefer[s]?[:\s]+([^\n]+)",
            r"fashion[:\s]+([^\n]+)",
            r"vibe[:\s]+([^\n]+)",
        ]
        has_style = any(re.search(p, user_text, re.IGNORECASE) for p in style_patterns)
        add_check(
            "USER.md contains a style preference entry",
            has_style,
            "Style entry found in USER.md" if has_style else "No style/prefer/fashion/vibe line found in USER.md",
            weight=1.5
        )
    else:
        add_check("USER.md contains a style preference entry", False, "USER.md not found", weight=1.5)
except Exception as e:
    add_check("USER.md contains a style preference entry", False, f"Exception: {e}", weight=1.5)

# ── CHECK 6: ootd_report.txt exists somewhere in the workspace ───────────────
report_path = None
try:
    candidates = list(workspace.rglob("ootd_report.txt")) + list(openclaw_workspace.rglob("ootd_report.txt"))
    if candidates:
        report_path = candidates[0]
    add_check(
        "ootd_report.txt file exists",
        report_path is not None,
        f"Found at {report_path}" if report_path else "ootd_report.txt not found anywhere in workspace",
        weight=1.5
    )
except Exception as e:
    add_check("ootd_report.txt file exists", False, f"Exception: {e}", weight=1.5)

# ── CHECK 7: ootd_report.txt contains all 4 required output sections ──────────
try:
    if report_path and report_path.exists():
        report_text = report_path.read_text()
        required_sections = [
            ("**Temperature:**", r"\*\*Temperature:\*\*"),
            ("**Sky:**",         r"\*\*Sky:\*\*"),
            ("**Vibe:**",        r"\*\*Vibe:\*\*"),
            ("**Recommendation:**", r"\*\*Recommendation:\*\*"),
        ]
        missing_sections = []
        for label, pattern in required_sections:
            if not re.search(pattern, report_text):
                missing_sections.append(label)
        all_sections_present = len(missing_sections) == 0
        add_check(
            "ootd_report.txt contains all 4 required sections (Temperature, Sky, Vibe, Recommendation)",
            all_sections_present,
            "All sections present" if all_sections_present else f"Missing sections: {missing_sections}",
            weight=2.5
        )
    else:
        add_check(
            "ootd_report.txt contains all 4 required sections",
            False,
            "File not found or unreadable",
            weight=2.5
        )
except Exception as e:
    add_check("ootd_report.txt contains all 4 required sections", False, f"Exception: {e}", weight=2.5)

# ── CHECK 8: Recommendation references wardrobe items (not generic fallback) ──
try:
    if report_path and report_path.exists() and wardrobe_data and "items" in wardrobe_data:
        report_text = report_path.read_text()
        items = wardrobe_data["items"]
        cold_temp = 45
        cold_item_names = [
            i["name"] for i in items
            if isinstance(i.get("min_temp"), (int, float))
            and isinstance(i.get("max_temp"), (int, float))
            and i["min_temp"] <= cold_temp <= i["max_temp"]
            and "name" in i
        ]
        # Check if at least one cold-weather item name appears in report
        referenced = any(name in report_text for name in cold_item_names)
        add_check(
            "Recommendation in ootd_report.txt references at least one wardrobe item by name",
            referenced,
            f"Wardrobe items in range: {cold_item_names}; referenced={'yes' if referenced else 'no'}",
            weight=2.0
        )
    else:
        add_check(
            "Recommendation references wardrobe items",
            False,
            "Cannot verify — report or wardrobe data missing",
            weight=2.0
        )
except Exception as e:
    add_check("Recommendation references wardrobe items", False, f"Exception: {e}", weight=2.0)

# ── Final scoring ─────────────────────────────────────────────────────────────
score = round(earned_weight / total_weight, 4) if total_weight > 0 else 0.0
passed = score >= 0.75  # 75% threshold to account for partial credit

result = {
    "passed": passed,
    "score": score,
    "checks": checks
}
print(json.dumps(result, indent=2))