import json
import os
import re
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})

try:
    files = list(workspace.iterdir())
except Exception as e:
    print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "workspace_access", "passed": False, "detail": f"Could not access workspace: {e}"}]}))
    raise SystemExit(0)

# Check 1: input marker exists
try:
    p = workspace / "task_input.json"
    if not p.exists():
        add_check("input_marker_exists", False, "task_input.json is missing")
    else:
        data = json.loads(p.read_text(encoding='utf-8'))
        ok = isinstance(data, dict) and data.get("task_id") == "colormind_easy_001"
        add_check("input_marker_exists", ok, f"task_input.json found; task_id={data.get('task_id') if isinstance(data, dict) else 'invalid'}")
except Exception as e:
    add_check("input_marker_exists", False, f"Failed to read/parse task_input.json: {e}")

# Check 2: default palette output exists and is JSON with palette data
try:
    # Fuzzy match: look for JSON files containing "default" and "palette" in the name
    json_files = [f for f in files if f.suffix.lower() == '.json']
    found = None
    for f in json_files:
        name_lower = f.name.lower()
        if re.search(r'default', name_lower) and re.search(r'palette', name_lower):
            found = f
            break
    if not found:
        add_check("default_palette_output", False, "Could not find default palette JSON file (expected filename containing 'default' and 'palette')")
    else:
        obj = json.loads(found.read_text(encoding='utf-8'))
        palette = obj.get("palette") if isinstance(obj, dict) else None
        ok = isinstance(palette, list) and len(palette) >= 4
        add_check("default_palette_output", ok, f"Found {found.name} with palette length {len(palette) if isinstance(palette, list) else 'invalid'}")
except Exception as e:
    add_check("default_palette_output", False, f"Failed to validate default palette output: {e}")

# Check 3: ui palette output exists and first color is locked-ish / contains a blue-like entry
try:
    # Fuzzy match: look for JSON files containing "ui" and "palette" in the name
    json_files = [f for f in files if f.suffix.lower() == '.json']
    found = None
    for f in json_files:
        name_lower = f.name.lower()
        if re.search(r'ui', name_lower) and re.search(r'palette', name_lower):
            found = f
            break
    if not found:
        add_check("ui_palette_output", False, "Could not find ui palette JSON file (expected filename containing 'ui' and 'palette')")
    else:
        obj = json.loads(found.read_text(encoding='utf-8'))
        palette = obj.get("palette") if isinstance(obj, dict) else None
        first = palette[0] if isinstance(palette, list) and palette else None
        # fuzzy check for a blue-ish first color representation if present
        ok = isinstance(palette, list) and len(palette) >= 4 and first is not None
        first_text = str(first).lower() if first is not None else ""
        blueish = ("0" in first_text and "122" in first_text and "255" in first_text) or ("#007aff" in first_text) or ("blue" in first_text)
        add_check("ui_palette_output", ok and blueish, f"Found {found.name}; first entry={first!r}")
except Exception as e:
    add_check("ui_palette_output", False, f"Failed to validate ui palette output: {e}")

# Check 4: markdown summary exists and references both models
try:
    # Fuzzy match: look for MD files containing "summary" or "palette" in the name
    md_files = [f for f in files if f.suffix.lower() == '.md']
    found = None
    for f in md_files:
        name_lower = f.name.lower()
        if re.search(r'summary', name_lower) or re.search(r'palette', name_lower):
            found = f
            break
    if not found:
        add_check("markdown_summary", False, "summary.md is missing (expected filename containing 'summary' or 'palette')")
    else:
        text = found.read_text(encoding='utf-8', errors='ignore').lower()
        ok = ("default" in text) and ("ui" in text) and ("#" in text or "-" in text)
        add_check("markdown_summary", ok, f"{found.name} found and checked for model references")
except Exception as e:
    add_check("markdown_summary", False, f"Failed to validate summary.md: {e}")

passed_count = sum(1 for c in checks if c["passed"])
score = passed_count / len(checks) if checks else 0.0
passed = all(c["passed"] for c in checks)
print(json.dumps({"passed": passed, "score": score, "checks": checks}))