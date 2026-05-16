#!/usr/bin/env python3
"""
Evaluation script for the code-stats audit task.
Usage: python3 eval.py /workspace
"""

import sys
import json
import re
import subprocess
import os
from pathlib import Path

def run_skill(workspace: str):
    """Run the skill and return its stdout, or None on failure."""
    try:
        result = subprocess.run(
            ["node", "skills/code-stats/index.js"],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout
    except Exception as e:
        return None


def parse_skill_output(output: str):
    """Parse the canonical skill output into a dict."""
    if not output:
        return None
    data = {"total_files": None, "total_lines": None, "languages": {}}

    for line in output.splitlines():
        m = re.match(r"Total Files:\s+([\d,]+)", line)
        if m:
            data["total_files"] = int(m.group(1).replace(",", ""))
        m = re.match(r"Total Lines:\s+([\d,]+)", line)
        if m:
            data["total_lines"] = int(m.group(1).replace(",", ""))
        # e.g.   JavaScript: 3 files, 45 lines (50.0%)
        m = re.match(r"\s+(\w[\w/\s\+]+):\s+([\d,]+)\s+files,\s+([\d,]+)\s+lines\s+\(([\d.]+)%\)", line)
        if m:
            lang = m.group(1).strip()
            data["languages"][lang] = {
                "files": int(m.group(2).replace(",", "")),
                "lines": int(m.group(3).replace(",", "")),
                "pct": float(m.group(4)),
            }
    return data


def find_report(workspace: str):
    """Find stats_report.json anywhere in workspace (not inside node_modules)."""
    for p in Path(workspace).rglob("stats_report.json"):
        parts = p.parts
        if "node_modules" in parts or ".git" in parts:
            continue
        return p
    return None


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []

    # ── Ground truth: run the skill ourselves ────────────────────────────────
    skill_output = run_skill(workspace)
    expected = parse_skill_output(skill_output)

    # Check 1: skill ran successfully
    checks.append({
        "name": "skill_executable",
        "passed": skill_output is not None and expected is not None
                  and expected["total_files"] is not None,
        "detail": f"Skill stdout length: {len(skill_output) if skill_output else 0}",
    })

    if not checks[-1]["passed"]:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # Check 2: stats_report.json exists
    report_path = find_report(workspace)
    checks.append({
        "name": "report_file_exists",
        "passed": report_path is not None,
        "detail": f"Found at: {report_path}" if report_path else "stats_report.json not found anywhere in workspace",
    })

    if not checks[-1]["passed"]:
        print(json.dumps({"passed": False, "score": 0.25, "checks": checks}))
        return

    # Check 3: JSON is valid
    try:
        with open(report_path) as f:
            report = json.load(f)
        checks.append({"name": "valid_json", "passed": True, "detail": f"Loaded from {report_path}"})
    except Exception as e:
        checks.append({"name": "valid_json", "passed": False, "detail": str(e)})
        print(json.dumps({"passed": False, "score": 0.3, "checks": checks}))
        return

    # ── Helper: find a value recursively (handles nested dicts) ──────────────
    def find_val(d, *keys):
        """Try multiple key variants, return first match (case-insensitive)."""
        if not isinstance(d, dict):
            return None
        for key in keys:
            for k, v in d.items():
                if k.lower().replace(" ", "_").replace("-", "_") == key.lower().replace(" ", "_").replace("-", "_"):
                    return v
        return None

    def find_nested(d, path_parts):
        cur = d
        for part in path_parts:
            cur = find_val(cur, part)
            if cur is None:
                return None
        return cur

    # Check 4: total_files correct
    report_total_files = None
    for key in ("total_files", "totalFiles", "total files", "files"):
        v = report.get(key)
        if v is not None:
            report_total_files = v
            break
    try:
        report_total_files_int = int(report_total_files)
    except (TypeError, ValueError):
        report_total_files_int = None

    files_ok = report_total_files_int == expected["total_files"]
    checks.append({
        "name": "total_files_correct",
        "passed": files_ok,
        "detail": f"Expected {expected['total_files']}, got {report_total_files_int}",
    })

    # Check 5: total_lines correct
    report_total_lines = None
    for key in ("total_lines", "totalLines", "total lines", "lines"):
        v = report.get(key)
        if v is not None:
            report_total_lines = v
            break
    try:
        report_total_lines_int = int(report_total_lines)
    except (TypeError, ValueError):
        report_total_lines_int = None

    lines_ok = report_total_lines_int == expected["total_lines"]
    checks.append({
        "name": "total_lines_correct",
        "passed": lines_ok,
        "detail": f"Expected {expected['total_lines']}, got {report_total_lines_int}",
    })

    # Check 6: languages section present and non-empty
    lang_section = None
    for key in ("languages", "by_language", "byLanguage", "language_breakdown", "by language"):
        v = report.get(key)
        if isinstance(v, dict) and len(v) > 0:
            lang_section = v
            break
    checks.append({
        "name": "languages_section_present",
        "passed": lang_section is not None,
        "detail": f"Found languages section: {list(lang_section.keys()) if lang_section else 'None'}",
    })

    # Check 7: unsupported-language files (.java, .cpp, .rb, .go) NOT counted
    # These should be absent from the language section
    if lang_section is not None:
        unsupported_langs = {"java", "c++", "cpp", "ruby", "go", "golang"}
        reported_langs_lower = {k.lower() for k in lang_section.keys()}
        false_langs = reported_langs_lower & unsupported_langs
        distractor_not_counted = len(false_langs) == 0
    else:
        distractor_not_counted = True  # can't check, but main check above already failed
    checks.append({
        "name": "unsupported_languages_excluded",
        "passed": distractor_not_counted,
        "detail": (
            "Distractor languages (.java/.cpp/.rb/.go) correctly excluded"
            if distractor_not_counted
            else f"Unsupported languages incorrectly included: {false_langs}"
        ),
    })

    # Check 8: node_modules / .git not counted
    # Proxy: total_files matches skill output (already checked), but also verify
    # report doesn't claim an absurdly large number
    nm_excluded = (report_total_files_int is not None and report_total_files_int < 50)
    checks.append({
        "name": "ignored_dirs_excluded",
        "passed": nm_excluded,
        "detail": f"total_files={report_total_files_int} (should be small, node_modules excluded)",
    })

    # Check 9: at least one language entry has correct file+line counts
    lang_counts_correct = False
    if lang_section and expected["languages"]:
        matches = 0
        for exp_lang, exp_info in expected["languages"].items():
            # find in report (flexible key matching)
            for rep_lang, rep_info in lang_section.items():
                if rep_lang.lower() == exp_lang.lower():
                    if isinstance(rep_info, dict):
                        rep_files = rep_info.get("files") or rep_info.get("file_count") or rep_info.get("fileCount")
                        rep_lines = rep_info.get("lines") or rep_info.get("line_count") or rep_info.get("lineCount")
                        try:
                            if int(rep_files) == exp_info["files"] and int(rep_lines) == exp_info["lines"]:
                                matches += 1
                        except (TypeError, ValueError):
                            pass
        lang_counts_correct = matches >= 1
    checks.append({
        "name": "language_counts_accurate",
        "passed": lang_counts_correct,
        "detail": f"At least one language has correct files+lines matching skill output",
    })

    # ── Final scoring ─────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / len(checks), 3)
    all_passed = all(c["passed"] for c in checks)

    print(json.dumps({
        "passed": all_passed,
        "score": score,
        "checks": checks,
    }, indent=2))


if __name__ == "__main__":
    main()