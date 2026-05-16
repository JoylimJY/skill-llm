#!/usr/bin/env python3
"""
Evaluation script for the Bazi Analysis task.
Usage: python eval.py /workspace
"""

import sys
import json
import re
from pathlib import Path

def run_eval(workspace: str):
    ws = Path(workspace)
    checks = []
    total_score = 0.0

    # ── Helper ───────────────────────────────────────────────────────────────
    def find_report_files(pattern):
        return list(ws.rglob(pattern))

    # ════════════════════════════════════════════════════════════════════════
    # Check 1: sect1_report.json exists and is valid JSON with correct sect
    # ════════════════════════════════════════════════════════════════════════
    check_name = "sect1_json_report_exists_and_valid"
    try:
        candidates = find_report_files("sect1_report.json")
        if not candidates:
            # also accept any json file with sect:1 in name
            candidates = find_report_files("*sect1*.json") + find_report_files("*sect_1*.json")
        if not candidates:
            checks.append({"name": check_name, "passed": False,
                           "detail": "No sect1_report.json file found anywhere in workspace."})
        else:
            fpath = candidates[0]
            data = json.loads(fpath.read_text(encoding="utf-8"))
            sect_val = data.get("meta", {}).get("sect")
            if sect_val == 1:
                checks.append({"name": check_name, "passed": True,
                               "detail": f"Found {fpath.name} with sect=1."})
                total_score += 1.0
            else:
                checks.append({"name": check_name, "passed": False,
                               "detail": f"File found but sect={sect_val}, expected 1."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ════════════════════════════════════════════════════════════════════════
    # Check 2: sect2_report.json exists and is valid JSON with correct sect
    # ════════════════════════════════════════════════════════════════════════
    check_name = "sect2_json_report_exists_and_valid"
    try:
        candidates = find_report_files("sect2_report.json")
        if not candidates:
            candidates = find_report_files("*sect2*.json") + find_report_files("*sect_2*.json")
        if not candidates:
            checks.append({"name": check_name, "passed": False,
                           "detail": "No sect2_report.json file found anywhere in workspace."})
        else:
            fpath = candidates[0]
            data = json.loads(fpath.read_text(encoding="utf-8"))
            sect_val = data.get("meta", {}).get("sect")
            if sect_val == 2:
                checks.append({"name": check_name, "passed": True,
                               "detail": f"Found {fpath.name} with sect=2."})
                total_score += 1.0
            else:
                checks.append({"name": check_name, "passed": False,
                               "detail": f"File found but sect={sect_val}, expected 2."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ════════════════════════════════════════════════════════════════════════
    # Check 3: Both JSON reports contain the correct birth profile
    # ════════════════════════════════════════════════════════════════════════
    check_name = "correct_birth_profile_in_json_reports"
    try:
        correct_count = 0
        checked_files = []
        for pattern in ["sect1_report.json", "sect2_report.json",
                        "*sect1*.json", "*sect2*.json"]:
            for fpath in find_report_files(pattern):
                try:
                    data = json.loads(fpath.read_text(encoding="utf-8"))
                    meta = data.get("meta", {})
                    if (meta.get("birth_date") == "1993-08-23" and
                            meta.get("birth_time") == "10:58" and
                            meta.get("gender") in ("female", "女")):
                        correct_count += 1
                        checked_files.append(fpath.name)
                except Exception:
                    pass
        if correct_count >= 2:
            checks.append({"name": check_name, "passed": True,
                           "detail": f"Correct profile in files: {checked_files}"})
            total_score += 1.0
        else:
            checks.append({"name": check_name, "passed": False,
                           "detail": f"Only {correct_count}/2 reports have correct birth profile (1993-08-23, 10:58, female)."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ════════════════════════════════════════════════════════════════════════
    # Check 4: At least one JSON report has yearly_outlook with 10 entries
    #          starting from 2026
    # ════════════════════════════════════════════════════════════════════════
    check_name = "yearly_outlook_10_years_from_2026"
    try:
        found_outlook = False
        detail = "No report with correct yearly_outlook found."
        for pattern in ["sect1_report.json", "sect2_report.json",
                        "*sect1*.json", "*sect2*.json"]:
            for fpath in find_report_files(pattern):
                try:
                    data = json.loads(fpath.read_text(encoding="utf-8"))
                    outlook = data.get("yearly_outlook", [])
                    if len(outlook) == 10:
                        years = [entry.get("year") for entry in outlook]
                        if years[0] == 2026 and years[-1] == 2035:
                            found_outlook = True
                            detail = f"Found valid 10-year outlook 2026-2035 in {fpath.name}."
                            break
                except Exception:
                    pass
            if found_outlook:
                break
        checks.append({"name": check_name, "passed": found_outlook, "detail": detail})
        if found_outlook:
            total_score += 1.5
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ════════════════════════════════════════════════════════════════════════
    # Check 5: Markdown consultation report exists
    # ════════════════════════════════════════════════════════════════════════
    check_name = "markdown_consultation_report_exists"
    try:
        md_candidates = (find_report_files("client_009_report.md") +
                         find_report_files("*009*.md") +
                         find_report_files("*chen_jing*.md") +
                         find_report_files("*consultation*.md"))
        # filter out archived and template files
        md_candidates = [f for f in md_candidates
                         if "archived" not in str(f) and "template" not in str(f)]
        if not md_candidates:
            checks.append({"name": check_name, "passed": False,
                           "detail": "No markdown report file found for client 009."})
        else:
            checks.append({"name": check_name, "passed": True,
                           "detail": f"Found markdown report: {md_candidates[0].name}"})
            total_score += 0.5
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ════════════════════════════════════════════════════════════════════════
    # Check 6: Markdown report contains hour-boundary warning
    # ════════════════════════════════════════════════════════════════════════
    check_name = "markdown_contains_boundary_time_warning"
    try:
        md_candidates = (find_report_files("client_009_report.md") +
                         find_report_files("*009*.md") +
                         find_report_files("*chen_jing*.md") +
                         find_report_files("*consultation*.md"))
        md_candidates = [f for f in md_candidates
                         if "archived" not in str(f) and "template" not in str(f)]
        found_warning = False
        detail = "No markdown report found to check for boundary warning."
        for fpath in md_candidates:
            content = fpath.read_text(encoding="utf-8")
            # Check for boundary/adjacent chart warning keywords
            boundary_keywords = [
                "边界", "boundary", "adjacent", "相邻", "整点", "建议", "比对",
                "⚠️", "时辰", "near"
            ]
            matches = [kw for kw in boundary_keywords if kw in content]
            if len(matches) >= 2:
                found_warning = True
                detail = f"Boundary warning found in {fpath.name} (keywords: {matches})"
                break
        checks.append({"name": check_name, "passed": found_warning, "detail": detail})
        if found_warning:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ════════════════════════════════════════════════════════════════════════
    # Check 7: Markdown report contains four pillars (四柱) table
    # ════════════════════════════════════════════════════════════════════════
    check_name = "markdown_contains_four_pillars_table"
    try:
        md_candidates = (find_report_files("client_009_report.md") +
                         find_report_files("*009*.md") +
                         find_report_files("*chen_jing*.md") +
                         find_report_files("*consultation*.md"))
        md_candidates = [f for f in md_candidates
                         if "archived" not in str(f) and "template" not in str(f)]
        found_pillars = False
        detail = "No markdown report found to check for 四柱."
        for fpath in md_candidates:
            content = fpath.read_text(encoding="utf-8")
            pillar_keywords = ["四柱", "年柱", "月柱", "日柱", "时柱"]
            matches = [kw for kw in pillar_keywords if kw in content]
            if len(matches) >= 3:
                found_pillars = True
                detail = f"四柱 table found in {fpath.name} ({len(matches)}/5 pillar keywords)."
                break
        checks.append({"name": check_name, "passed": found_pillars, "detail": detail})
        if found_pillars:
            total_score += 0.5
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ════════════════════════════════════════════════════════════════════════
    # Check 8: Sect 1 and Sect 2 JSON reports have DIFFERENT luck cycle
    #          start ages (sect parameter actually changed calculation)
    # ════════════════════════════════════════════════════════════════════════
    check_name = "sect_difference_reflected_in_luck_cycles"
    try:
        sect1_data = None
        sect2_data = None
        for fpath in find_report_files("sect1_report.json"):
            try:
                d = json.loads(fpath.read_text(encoding="utf-8"))
                if d.get("meta", {}).get("sect") == 1:
                    sect1_data = d
            except Exception:
                pass
        for fpath in find_report_files("sect2_report.json"):
            try:
                d = json.loads(fpath.read_text(encoding="utf-8"))
                if d.get("meta", {}).get("sect") == 2:
                    sect2_data = d
            except Exception:
                pass
        if sect1_data and sect2_data:
            lc1 = sect1_data.get("luck_cycles", [])
            lc2 = sect2_data.get("luck_cycles", [])
            if lc1 and lc2:
                age1 = lc1[0].get("age")
                age2 = lc2[0].get("age")
                if age1 != age2:
                    checks.append({"name": check_name, "passed": True,
                                   "detail": f"Sect 1 start age={age1}, Sect 2 start age={age2} — different as expected."})
                    total_score += 1.5
                else:
                    checks.append({"name": check_name, "passed": False,
                                   "detail": f"Both sects have same luck cycle start age={age1}. Sect flag may not have been used."})
            else:
                checks.append({"name": check_name, "passed": False,
                               "detail": "Luck cycles empty in one or both reports."})
        else:
            checks.append({"name": check_name, "passed": False,
                           "detail": f"Could not load both sect reports. sect1={sect1_data is not None}, sect2={sect2_data is not None}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ════════════════════════════════════════════════════════════════════════
    # Check 9: near_hour_boundary flag is True in JSON reports
    # ════════════════════════════════════════════════════════════════════════
    check_name = "near_hour_boundary_flag_is_true"
    try:
        found_boundary_flag = False
        detail = "near_hour_boundary flag not found or not True in any report."
        for pattern in ["sect1_report.json", "sect2_report.json",
                        "*sect1*.json", "*sect2*.json"]:
            for fpath in find_report_files(pattern):
                try:
                    data = json.loads(fpath.read_text(encoding="utf-8"))
                    if data.get("meta", {}).get("near_hour_boundary") is True:
                        found_boundary_flag = True
                        detail = f"near_hour_boundary=True found in {fpath.name}."
                        break
                except Exception:
                    pass
            if found_boundary_flag:
                break
        checks.append({"name": check_name, "passed": found_boundary_flag, "detail": detail})
        if found_boundary_flag:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ════════════════════════════════════════════════════════════════════════
    # Final scoring
    # ════════════════════════════════════════════════════════════════════════
    max_score = 9.0
    normalized = round(min(total_score / max_score, 1.0), 4)
    all_passed = all(c["passed"] for c in checks)

    result = {
        "passed": all_passed,
        "score": normalized,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace_dir)