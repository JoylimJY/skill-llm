#!/usr/bin/env python3
"""
Evaluation script for the maintenance skill audit task.
Checks that the agent:
  1. Used the maintenance CLI to add entries in each required category
     (add, inventory, schedule, cost, log) — verified via data directory logs.
  2. Exported the data as JSON using `maintenance export json`.
  3. The resulting audit_export.json exists at /workspace/audit_export.json
     and is valid JSON containing all five entry types.
"""

import sys
import json
import os
import re
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []
score = 0.0

# ── Helper ────────────────────────────────────────────────────────────────────
def check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed


# ── CHECK 1: audit_export.json exists ─────────────────────────────────────────
export_file = workspace / "audit_export.json"
if export_file.exists():
    check("audit_export.json exists", True, f"Found at {export_file}")
else:
    # Also search recursively in case agent placed it elsewhere
    candidates = list(workspace.rglob("audit_export.json"))
    if candidates:
        export_file = candidates[0]
        check("audit_export.json exists", True,
              f"Found at non-standard location: {export_file}")
    else:
        check("audit_export.json exists", False,
              "audit_export.json not found anywhere in workspace")

# ── CHECK 2: Valid JSON ────────────────────────────────────────────────────────
export_data = None
if export_file.exists():
    try:
        raw = export_file.read_text(encoding="utf-8")
        export_data = json.loads(raw)
        check("audit_export.json is valid JSON", True,
              f"Parsed successfully, type={type(export_data).__name__}")
    except json.JSONDecodeError as e:
        check("audit_export.json is valid JSON", False, f"JSON parse error: {e}")
    except Exception as e:
        check("audit_export.json is valid JSON", False, f"Read error: {e}")
else:
    check("audit_export.json is valid JSON", False, "File not found, skipping parse")

# ── CHECK 3: Maintenance data directory logs exist ─────────────────────────────
data_dir = Path(os.path.expanduser("~/.local/share/maintenance"))
log_files = list(data_dir.glob("*.log")) if data_dir.exists() else []
if log_files:
    check("maintenance data directory has log files", True,
          f"Found {len(log_files)} log file(s): {[f.name for f in log_files]}")
else:
    check("maintenance data directory has log files", False,
          f"No .log files found in {data_dir}. "
          "Agent may not have used the maintenance CLI at all.")

# ── CHECK 4: 'add' entries exist in logs ─────────────────────────────────────
def search_logs(data_dir: Path, keyword: str) -> list[str]:
    """Return all log lines containing keyword (case-insensitive)."""
    matches = []
    if not data_dir.exists():
        return matches
    for lf in data_dir.glob("*.log"):
        try:
            for line in lf.read_text(encoding="utf-8", errors="replace").splitlines():
                if keyword.lower() in line.lower():
                    matches.append(line.strip())
        except Exception:
            pass
    return matches

add_lines = search_logs(data_dir, "add:")
if add_lines:
    check("'add' entry recorded in logs", True,
          f"Found {len(add_lines)} add entry line(s): {add_lines[:2]}")
else:
    check("'add' entry recorded in logs", False,
          "No 'add:' entries found in maintenance logs")

# ── CHECK 5: 'inventory' entries exist in logs ────────────────────────────────
inv_lines = search_logs(data_dir, "inventory:")
if inv_lines:
    check("'inventory' entry recorded in logs", True,
          f"Found {len(inv_lines)} inventory line(s): {inv_lines[:2]}")
else:
    check("'inventory' entry recorded in logs", False,
          "No 'inventory:' entries found in maintenance logs")

# ── CHECK 6: 'schedule' entries exist in logs ─────────────────────────────────
sched_lines = search_logs(data_dir, "schedule:")
if sched_lines:
    check("'schedule' entry recorded in logs", True,
          f"Found {len(sched_lines)} schedule line(s): {sched_lines[:2]}")
else:
    check("'schedule' entry recorded in logs", False,
          "No 'schedule:' entries found in maintenance logs")

# ── CHECK 7: 'cost' entries exist in logs ─────────────────────────────────────
cost_lines = search_logs(data_dir, "cost:")
if cost_lines:
    check("'cost' entry recorded in logs", True,
          f"Found {len(cost_lines)} cost line(s): {cost_lines[:2]}")
else:
    check("'cost' entry recorded in logs", False,
          "No 'cost:' entries found in maintenance logs")

# ── CHECK 8: 'log' entries exist in logs ──────────────────────────────────────
log_lines = search_logs(data_dir, "log:")
if log_lines:
    check("'log' entry recorded in logs", True,
          f"Found {len(log_lines)} log line(s): {log_lines[:2]}")
else:
    check("'log' entry recorded in logs", False,
          "No 'log:' entries found in maintenance logs")

# ── CHECK 9: Export contains multiple entries / non-empty content ──────────────
if export_data is not None:
    # The export could be a list, a dict with a list, or structured differently.
    # We try to count total entries.
    entry_count = 0
    if isinstance(export_data, list):
        entry_count = len(export_data)
    elif isinstance(export_data, dict):
        # Could be {"add": [...], "inventory": [...], ...} or {"entries": [...]}
        for v in export_data.values():
            if isinstance(v, list):
                entry_count += len(v)
            elif isinstance(v, (str, int, float)):
                entry_count += 1

    if entry_count >= 5:
        check("export contains ≥5 entries", True,
              f"Counted {entry_count} entries in export")
    elif entry_count > 0:
        check("export contains ≥5 entries", False,
              f"Only {entry_count} entries found; expected at least 5 "
              "(one per recorded category)")
    else:
        check("export contains ≥5 entries", False,
              "export JSON appears empty or has no countable entries")
else:
    check("export contains ≥5 entries", False,
          "Skipped — JSON could not be parsed")

# ── CHECK 10: Export covers all 5 required categories ─────────────────────────
if export_data is not None:
    raw_str = json.dumps(export_data).lower()
    required_keywords = {
        "add/maintenance note":   ["hvac", "filter", "2024-02-20", "hvac filter"],
        "inventory/water heater": ["water heater", "bradford white", "40-gallon", "40 gallon"],
        "schedule/roof":         ["roof", "skyhigh", "2024-09-01", "sky high"],
        "cost/plumbing":         ["fastfix", "185", "plumbing", "fast fix"],
        "log/mold":              ["mold", "unit c", "north"],
    }
    all_found = True
    details = []
    for label, keywords in required_keywords.items():
        found = any(kw.lower() in raw_str for kw in keywords)
        details.append(f"{label}: {'✓' if found else '✗'}")
        if not found:
            all_found = False

    check("export covers all 5 required business entries", all_found,
          " | ".join(details))
else:
    check("export covers all 5 required business entries", False,
          "Skipped — JSON could not be parsed")

# ── Scoring ───────────────────────────────────────────────────────────────────
passed_checks = [c for c in checks if c["passed"]]
score = round(len(passed_checks) / len(checks), 4)
all_passed = all(c["passed"] for c in checks)

result = {
    "passed": all_passed,
    "score": score,
    "checks": checks,
}
print(json.dumps(result, indent=2))