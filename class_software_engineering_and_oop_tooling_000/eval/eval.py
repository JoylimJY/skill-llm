#!/usr/bin/env python3
"""
Evaluation script for the OOP Audit Report task.
Expected artifact: oop_audit_report.json (anywhere in workspace)
"""
import sys
import json
import re
from pathlib import Path

def run_eval(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ── Locate the report ────────────────────────────────────────────────────
    candidates = list(workspace.rglob("oop_audit_report.json"))
    # Exclude the old draft distractor
    candidates = [c for c in candidates if "old_reports" not in str(c)]

    if not candidates:
        checks.append({"name": "file_exists", "passed": False,
                        "detail": "oop_audit_report.json not found anywhere in workspace (excluding old_reports/)"})
        return {"passed": False, "score": 0.0, "checks": checks}

    report_path = candidates[0]
    checks.append({"name": "file_exists", "passed": True,
                    "detail": f"Found at {report_path.relative_to(workspace)}"})
    total_score += 0.05

    # ── Parse JSON ───────────────────────────────────────────────────────────
    try:
        with open(report_path) as f:
            report = json.load(f)
        checks.append({"name": "valid_json", "passed": True, "detail": "File is valid JSON"})
        total_score += 0.05
    except Exception as e:
        checks.append({"name": "valid_json", "passed": False, "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": total_score, "checks": checks}

    # ── CHECK 1: top-level keys for each required section ────────────────────
    required_sections = ["solid", "patterns", "abstract", "pitfalls"]
    for section in required_sections:
        # Accept keys like "solid", "solid_principles", "SOLID", etc.
        found_key = next(
            (k for k in report.keys() if section.lower() in k.lower()), None
        )
        if found_key is not None:
            checks.append({"name": f"section_present_{section}", "passed": True,
                            "detail": f"Section '{section}' found as key '{found_key}'"})
            total_score += 0.05
        else:
            checks.append({"name": f"section_present_{section}", "passed": False,
                            "detail": f"No key containing '{section}' found in report top-level keys: {list(report.keys())}"})

    # ── CHECK 2: SOLID section has 5 principles ───────────────────────────────
    solid_key = next((k for k in report.keys() if "solid" in k.lower()), None)
    if solid_key:
        solid_val = report[solid_key]
        solid_str = json.dumps(solid_val).upper()
        principles_found = []
        for abbr, name in [("SRP", "SINGLE"), ("OCP", "OPEN"), ("LSP", "LISKOV"),
                            ("ISP", "INTERFACE"), ("DIP", "DEPEND")]:
            if abbr in solid_str or name in solid_str:
                principles_found.append(abbr)
        count = len(principles_found)
        passed = count >= 4
        checks.append({"name": "solid_has_five_principles", "passed": passed,
                        "detail": f"Found {count}/5 SOLID principle references: {principles_found}"})
        if passed:
            total_score += 0.15
    else:
        checks.append({"name": "solid_has_five_principles", "passed": False,
                        "detail": "solid section missing; cannot check principles"})

    # ── CHECK 3: patterns section mentions all three categories ──────────────
    patterns_key = next((k for k in report.keys() if "pattern" in k.lower()), None)
    if patterns_key:
        pat_str = json.dumps(report[patterns_key]).upper()
        categories = {"CREATIONAL": False, "STRUCTURAL": False, "BEHAVIORAL": False}
        for cat in categories:
            if cat in pat_str:
                categories[cat] = True
        all_present = all(categories.values())
        checks.append({"name": "patterns_three_categories", "passed": all_present,
                        "detail": f"Pattern categories found: {categories}"})
        if all_present:
            total_score += 0.15
    else:
        checks.append({"name": "patterns_three_categories", "passed": False,
                        "detail": "patterns section missing"})

    # ── CHECK 4: patterns section mentions at least Factory, Strategy, Observer ──
    if patterns_key:
        pat_str = json.dumps(report[patterns_key]).upper()
        required_patterns = ["FACTORY", "STRATEGY", "OBSERVER"]
        found_patterns = [p for p in required_patterns if p in pat_str]
        passed = len(found_patterns) >= 2
        checks.append({"name": "patterns_key_patterns_present", "passed": passed,
                        "detail": f"Found patterns: {found_patterns} out of {required_patterns}"})
        if passed:
            total_score += 0.10
    else:
        checks.append({"name": "patterns_key_patterns_present", "passed": False,
                        "detail": "patterns section missing"})

    # ── CHECK 5: abstract section mentions ABC / abstractmethod / Protocol ────
    abstract_key = next((k for k in report.keys() if "abstract" in k.lower()), None)
    if abstract_key:
        abs_str = json.dumps(report[abstract_key]).upper()
        abc_terms = ["ABC", "ABSTRACTMETHOD", "PROTOCOL", "INTERFACE", "ABSTRACT CLASS"]
        found_terms = [t for t in abc_terms if t in abs_str]
        passed = len(found_terms) >= 2
        checks.append({"name": "abstract_mentions_abc_or_protocol", "passed": passed,
                        "detail": f"Found abstract-related terms: {found_terms}"})
        if passed:
            total_score += 0.10
    else:
        checks.append({"name": "abstract_mentions_abc_or_protocol", "passed": False,
                        "detail": "abstract section missing"})

    # ── CHECK 6: pitfalls section mentions God Class and deep hierarchy ───────
    pitfalls_key = next((k for k in report.keys() if "pitfall" in k.lower()), None)
    if pitfalls_key:
        pit_str = json.dumps(report[pitfalls_key]).upper()
        pit_terms = ["GOD CLASS", "DEEP", "HIERARCHY", "ANEMIC", "OVER-ENGINEER", "YAGNI", "LEAKY"]
        found_terms = [t for t in pit_terms if t in pit_str]
        passed = len(found_terms) >= 2
        checks.append({"name": "pitfalls_mentions_god_class_and_hierarchy", "passed": passed,
                        "detail": f"Found pitfall terms: {found_terms}"})
        if passed:
            total_score += 0.10
    else:
        checks.append({"name": "pitfalls_mentions_god_class_and_hierarchy", "passed": False,
                        "detail": "pitfalls section missing"})

    # ── CHECK 7: CLASS_DIR cache evidence (agent used the tool) ──────────────
    # The script writes cache files to CLASS_DIR (~/.class/ by default)
    # Check that at least 3 cache files were created (agent ran multiple commands)
    home_class_dir = Path.home() / ".class"
    cache_files = list(home_class_dir.glob("*.cache")) if home_class_dir.exists() else []

    # Also check custom CLASS_DIR if set (not easily detectable, so use home default)
    passed_cache = len(cache_files) >= 3
    checks.append({"name": "tool_invoked_multiple_commands", "passed": passed_cache,
                    "detail": f"Found {len(cache_files)} cache files in ~/.class/ (need >=3). Files: {[f.name for f in cache_files]}"})
    if passed_cache:
        total_score += 0.10

    # ── CHECK 8: report is not a copy of the old draft distractor ────────────
    old_draft_keys = {"date", "notes"}
    is_distractor_copy = all(k in report for k in old_draft_keys) and report.get("solid") == "TODO"
    if is_distractor_copy:
        checks.append({"name": "not_old_draft_distractor", "passed": False,
                        "detail": "Report appears to be a copy of old_reports/oop_audit_report_draft.json"})
    else:
        checks.append({"name": "not_old_draft_distractor", "passed": True,
                        "detail": "Report is original (not a copy of the old draft)"})
        total_score += 0.05

    # ── CHECK 9: report contains content from at least 4 distinct commands ───
    full_str = json.dumps(report).upper()
    command_signals = {
        "solid": ["SRP", "SINGLE RESPONSIBILITY", "OPEN/CLOSED", "LISKOV"],
        "patterns": ["FACTORY", "STRATEGY", "OBSERVER", "SINGLETON", "BUILDER"],
        "abstract": ["ABC", "ABSTRACTMETHOD", "@ABSTRACTMETHOD", "PROTOCOL"],
        "pitfalls": ["GOD CLASS", "DEEP INHERITANCE", "OVER-ENGINEER", "YAGNI", "ANEMIC"],
    }
    commands_with_content = []
    for cmd, signals in command_signals.items():
        if any(sig in full_str for sig in signals):
            commands_with_content.append(cmd)

    passed_coverage = len(commands_with_content) >= 3
    checks.append({"name": "content_from_multiple_commands", "passed": passed_coverage,
                    "detail": f"Detected content from commands: {commands_with_content} (need >=3)"})
    if passed_coverage:
        total_score += 0.10

    # ── Final verdict ─────────────────────────────────────────────────────────
    # Must pass: file_exists, valid_json, all 4 sections, solid principles,
    #            patterns categories, and content from multiple commands
    critical_checks = [
        "file_exists", "valid_json",
        "section_present_solid", "section_present_patterns",
        "section_present_abstract", "section_present_pitfalls",
        "solid_has_five_principles", "patterns_three_categories",
        "content_from_multiple_commands",
    ]
    failed_critical = [c["name"] for c in checks
                       if c["name"] in critical_checks and not c["passed"]]

    overall_passed = len(failed_critical) == 0
    total_score = round(min(total_score, 1.0), 3)

    return {
        "passed": overall_passed,
        "score": total_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, indent=2))