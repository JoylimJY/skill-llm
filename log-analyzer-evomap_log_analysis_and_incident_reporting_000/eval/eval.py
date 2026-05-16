#!/usr/bin/env python3
"""
Evaluation script for the log-analyzer task.

Expected deliverables from the agent:
1. incident_analysis.json  — output of `node index.js analyze crash_report_2024-06-15.log`
   Must contain: 6 errors, correct categories (network, io, permission, memory, timeout, network),
   at least one lesson per category encountered.

2. evolver_summary.json    — output of `node index.js evolver`
   Must contain: sourceDir pointing to ~/evolver-memory, at least 3 logFiles,
   correct category coverage (network, io, memory, timeout).

3. batch_summary.txt       — output of summarize() with format:'text'
   Must contain the text banner "=== Log Analysis Summary ===" and category breakdown.
"""

import sys
import json
import re
from pathlib import Path

def find_file(workspace, filename):
    hits = list(Path(workspace).rglob(filename))
    return hits[0] if hits else None

def load_json(path):
    with open(path) as f:
        return json.load(f)

def main():
    workspace = sys.argv[1]
    checks = []
    
    # ── CHECK 1: incident_analysis.json exists ────────────────────────────────
    ia_path = find_file(workspace, "incident_analysis.json")
    c1_passed = ia_path is not None
    checks.append({
        "name": "incident_analysis.json exists",
        "passed": c1_passed,
        "detail": str(ia_path) if c1_passed else "File not found anywhere in workspace"
    })

    # ── CHECK 2: incident_analysis.json has correct error count ───────────────
    ia_data = None
    if c1_passed:
        try:
            ia_data = load_json(ia_path)
            total = ia_data.get("totalErrors", 0)
            c2_passed = total >= 5  # at least 5 of 6 incidents detected
            checks.append({
                "name": "incident_analysis: detected ≥5 errors from 6 incidents",
                "passed": c2_passed,
                "detail": f"totalErrors={total}"
            })
        except Exception as e:
            checks.append({
                "name": "incident_analysis: detected ≥5 errors from 6 incidents",
                "passed": False,
                "detail": f"JSON parse error: {e}"
            })
    else:
        checks.append({
            "name": "incident_analysis: detected ≥5 errors from 6 incidents",
            "passed": False,
            "detail": "Skipped — file missing"
        })

    # ── CHECK 3: incident_analysis.json has all 5 required categories ─────────
    required_cats = {"network", "io", "permission", "memory", "timeout"}
    if ia_data is not None:
        try:
            cats_found = set()
            errors_list = ia_data.get("errors", [])
            for e in errors_list:
                cat = e.get("category", "")
                if cat in required_cats:
                    cats_found.add(cat)
            # Also check categories dict at top level if present
            top_cats = ia_data.get("categories", {})
            cats_found.update(k for k in top_cats if k in required_cats)
            
            c3_passed = required_cats.issubset(cats_found)
            checks.append({
                "name": "incident_analysis: all 5 categories present (network/io/permission/memory/timeout)",
                "passed": c3_passed,
                "detail": f"Found categories: {sorted(cats_found)}; Required: {sorted(required_cats)}"
            })
        except Exception as e:
            checks.append({
                "name": "incident_analysis: all 5 categories present",
                "passed": False,
                "detail": f"Error: {e}"
            })
    else:
        checks.append({
            "name": "incident_analysis: all 5 categories present",
            "passed": False,
            "detail": "Skipped — data unavailable"
        })

    # ── CHECK 4: incident_analysis.json contains lessons ─────────────────────
    if ia_data is not None:
        try:
            lessons = ia_data.get("lessons", [])
            c4_passed = isinstance(lessons, list) and len(lessons) >= 4
            checks.append({
                "name": "incident_analysis: ≥4 distinct prevention lessons extracted",
                "passed": c4_passed,
                "detail": f"lessons count={len(lessons)}: {lessons[:2]}"
            })
        except Exception as e:
            checks.append({
                "name": "incident_analysis: ≥4 distinct prevention lessons extracted",
                "passed": False,
                "detail": str(e)
            })
    else:
        checks.append({
            "name": "incident_analysis: ≥4 distinct prevention lessons extracted",
            "passed": False,
            "detail": "Skipped — data unavailable"
        })

    # ── CHECK 5: evolver_summary.json exists ─────────────────────────────────
    ev_path = find_file(workspace, "evolver_summary.json")
    c5_passed = ev_path is not None
    checks.append({
        "name": "evolver_summary.json exists",
        "passed": c5_passed,
        "detail": str(ev_path) if c5_passed else "File not found anywhere in workspace"
    })

    # ── CHECK 6: evolver_summary.json references evolver-memory dir ──────────
    ev_data = None
    if c5_passed:
        try:
            ev_data = load_json(ev_path)
            source_dir = ev_data.get("sourceDir", "")
            c6_passed = "evolver-memory" in source_dir
            checks.append({
                "name": "evolver_summary: sourceDir references ~/evolver-memory",
                "passed": c6_passed,
                "detail": f"sourceDir={source_dir}"
            })
        except Exception as e:
            checks.append({
                "name": "evolver_summary: sourceDir references ~/evolver-memory",
                "passed": False,
                "detail": f"JSON parse error: {e}"
            })
    else:
        checks.append({
            "name": "evolver_summary: sourceDir references ~/evolver-memory",
            "passed": False,
            "detail": "Skipped — file missing"
        })

    # ── CHECK 7: evolver_summary.json covers multiple log files ──────────────
    if ev_data is not None:
        try:
            log_files = ev_data.get("logFiles", [])
            c7_passed = isinstance(log_files, list) and len(log_files) >= 3
            checks.append({
                "name": "evolver_summary: ≥3 log files processed from evolver-memory",
                "passed": c7_passed,
                "detail": f"logFiles count={len(log_files)}"
            })
        except Exception as e:
            checks.append({
                "name": "evolver_summary: ≥3 log files processed from evolver-memory",
                "passed": False,
                "detail": str(e)
            })
    else:
        checks.append({
            "name": "evolver_summary: ≥3 log files processed from evolver-memory",
            "passed": False,
            "detail": "Skipped — data unavailable"
        })

    # ── CHECK 8: evolver_summary.json has correct error categories ───────────
    if ev_data is not None:
        try:
            ev_cats = set(ev_data.get("categories", {}).keys())
            # network (ECONNREFUSED/fetch failed), io (ENOENT), memory (heap OOM), timeout
            needed = {"network", "io", "memory", "timeout"}
            c8_passed = needed.issubset(ev_cats)
            checks.append({
                "name": "evolver_summary: network/io/memory/timeout categories all detected",
                "passed": c8_passed,
                "detail": f"categories found: {sorted(ev_cats)}"
            })
        except Exception as e:
            checks.append({
                "name": "evolver_summary: network/io/memory/timeout categories all detected",
                "passed": False,
                "detail": str(e)
            })
    else:
        checks.append({
            "name": "evolver_summary: network/io/memory/timeout categories all detected",
            "passed": False,
            "detail": "Skipped — data unavailable"
        })

    # ── CHECK 9: batch_summary.txt exists ────────────────────────────────────
    bs_path = find_file(workspace, "batch_summary.txt")
    c9_passed = bs_path is not None
    checks.append({
        "name": "batch_summary.txt exists",
        "passed": c9_passed,
        "detail": str(bs_path) if c9_passed else "File not found anywhere in workspace"
    })

    # ── CHECK 10: batch_summary.txt is text format with correct sections ──────
    if c9_passed:
        try:
            content = bs_path.read_text()
            has_banner = "=== Log Analysis Summary ===" in content
            has_total = bool(re.search(r'Total errors:\s*\d+', content))
            has_category = "Category Breakdown:" in content
            has_recommendations = "Prevention Recommendations:" in content or "Recommendations:" in content
            c10_passed = has_banner and has_total and has_category
            checks.append({
                "name": "batch_summary.txt: correct text format with banner, totals, and category breakdown",
                "passed": c10_passed,
                "detail": (
                    f"has_banner={has_banner}, has_total={has_total}, "
                    f"has_category={has_category}, has_recommendations={has_recommendations}"
                )
            })
        except Exception as e:
            checks.append({
                "name": "batch_summary.txt: correct text format",
                "passed": False,
                "detail": str(e)
            })
    else:
        checks.append({
            "name": "batch_summary.txt: correct text format with banner, totals, and category breakdown",
            "passed": False,
            "detail": "Skipped — file missing"
        })

    # ── CHECK 11: batch_summary.txt covers both crash log AND evolver logs ────
    if c9_passed:
        try:
            content = bs_path.read_text()
            logs_match = re.search(r'Logs analyzed:\s*(\d+)', content)
            if logs_match:
                logs_analyzed = int(logs_match.group(1))
                c11_passed = logs_analyzed >= 2
                checks.append({
                    "name": "batch_summary.txt: covers ≥2 log files (batch mode)",
                    "passed": c11_passed,
                    "detail": f"Logs analyzed: {logs_analyzed}"
                })
            else:
                checks.append({
                    "name": "batch_summary.txt: covers ≥2 log files (batch mode)",
                    "passed": False,
                    "detail": "Could not find 'Logs analyzed:' line in batch_summary.txt"
                })
        except Exception as e:
            checks.append({
                "name": "batch_summary.txt: covers ≥2 log files (batch mode)",
                "passed": False,
                "detail": str(e)
            })
    else:
        checks.append({
            "name": "batch_summary.txt: covers ≥2 log files (batch mode)",
            "passed": False,
            "detail": "Skipped — file missing"
        })

    # ── Final scoring ─────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    overall_passed = passed_count >= 8  # Must pass 8/11 checks

    output = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()