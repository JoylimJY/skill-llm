#!/usr/bin/env python3
"""
Evaluation script for the LegacyBank compliance audit task.
Checks that audit_report.json was correctly produced using the code-search skill.
"""

import sys
import json
import re
from pathlib import Path


def load_report(workspace: str):
    """Find audit_report.json anywhere in the workspace."""
    candidates = list(Path(workspace).rglob("audit_report.json"))
    if not candidates:
        return None, "audit_report.json not found anywhere in workspace"
    # If multiple, take the one modified most recently
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    target = candidates[0]
    try:
        with open(target) as f:
            data = json.load(f)
        return data, str(target)
    except Exception as e:
        return None, f"Failed to parse JSON at {target}: {e}"


def evaluate(workspace: str):
    checks = []

    # ── Load the report ───────────────────────────────────────────────────────
    report, location = load_report(workspace)

    if report is None:
        checks.append({
            "name": "report_exists_and_parseable",
            "passed": False,
            "detail": location,
        })
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    checks.append({
        "name": "report_exists_and_parseable",
        "passed": True,
        "detail": f"Found at {location}",
    })

    # ── CHECK 1: directory_tree section present ───────────────────────────────
    # Must contain some reference to key top-level dirs from the codebase
    try:
        tree_section = report.get("directory_tree", report.get("tree", ""))
        tree_str = str(tree_section)
        required_dirs = ["cmd", "internal", "pkg", "configs", "tests"]
        found_dirs = [d for d in required_dirs if d in tree_str]
        tree_ok = len(found_dirs) >= 4
        checks.append({
            "name": "directory_tree_section_present",
            "passed": tree_ok,
            "detail": f"Found {len(found_dirs)}/{len(required_dirs)} expected directories: {found_dirs}",
        })
    except Exception as e:
        checks.append({
            "name": "directory_tree_section_present",
            "passed": False,
            "detail": f"Error reading directory_tree section: {e}",
        })

    # ── CHECK 2: config files listed ─────────────────────────────────────────
    # Must list at least the 3 config files: app.yaml, logging.yaml, compliance.toml
    try:
        config_section = report.get("config_files", report.get("configs", []))
        config_str = str(config_section)
        expected_configs = ["app.yaml", "logging.yaml", "compliance.toml"]
        found_configs = [c for c in expected_configs if c in config_str]
        configs_ok = len(found_configs) == 3
        checks.append({
            "name": "config_files_correctly_identified",
            "passed": configs_ok,
            "detail": f"Found {len(found_configs)}/3 config files: {found_configs}",
        })
    except Exception as e:
        checks.append({
            "name": "config_files_correctly_identified",
            "passed": False,
            "detail": f"Error reading config_files section: {e}",
        })

    # ── CHECK 3: deprecated function `insecure_hash` occurrences ─────────────
    # The literal search for "insecure_hash(" (with parenthesis — requires --literal)
    # should find it in: crypto.go, payments.go, auth.go, checker.go, compliance.toml (no parens), fraud_detect.py
    # The parenthesis in the search pattern means it MUST use --literal or no regex interpretation
    # Specifically we expect matches in at least 4 source files
    try:
        deprecated_section = report.get(
            "deprecated_insecure_hash_usages",
            report.get("insecure_hash_usages",
            report.get("deprecated_usages", {}))
        )
        dep_str = str(deprecated_section)

        # Must mention the actual files where insecure_hash() appears
        required_files = ["crypto.go", "payments.go", "auth.go", "checker.go"]
        found_files = [f for f in required_files if f in dep_str]
        dep_ok = len(found_files) >= 3

        # Must also have some count/number reflecting real matches
        # We accept any numeric mention >= 4 (there are 5 occurrences of insecure_hash across .go files)
        numbers = re.findall(r'\b([4-9]|[1-9]\d+)\b', dep_str)
        has_count = len(numbers) > 0

        deprecated_passed = dep_ok and has_count
        checks.append({
            "name": "deprecated_insecure_hash_occurrences_found",
            "passed": deprecated_passed,
            "detail": (
                f"Files found: {found_files} ({len(found_files)}/4 required). "
                f"Numeric count present: {has_count} (numbers seen: {numbers[:5]})"
            ),
        })
    except Exception as e:
        checks.append({
            "name": "deprecated_insecure_hash_occurrences_found",
            "passed": False,
            "detail": f"Error reading deprecated usages section: {e}",
        })

    # ── CHECK 4: test file count ───────────────────────────────────────────────
    # There are exactly 7 *_test.go files in the codebase:
    #   payments_test.go, auth_test.go, checker_test.go,
    #   crypto_test.go, ledger_test.go,
    #   payment_integration_test.go, compliance_integration_test.go
    try:
        test_section = report.get(
            "test_file_count",
            report.get("test_files_count",
            report.get("go_test_files", -1))
        )
        # Accept either an integer or a dict with count field
        if isinstance(test_section, dict):
            count_val = test_section.get("count", test_section.get("total", -1))
        elif isinstance(test_section, (int, float)):
            count_val = int(test_section)
        elif isinstance(test_section, list):
            count_val = len(test_section)
        else:
            # Try to parse a number from string representation
            nums = re.findall(r'\b7\b', str(test_section))
            count_val = 7 if nums else -1

        test_ok = (count_val == 7)
        checks.append({
            "name": "go_test_file_count_correct",
            "passed": test_ok,
            "detail": f"Expected 7 *_test.go files, report shows: {count_val} (raw: {repr(test_section)[:120]})",
        })
    except Exception as e:
        checks.append({
            "name": "go_test_file_count_correct",
            "passed": False,
            "detail": f"Error reading test file count: {e}",
        })

    # ── CHECK 5: context lines captured for deprecated usages ─────────────────
    # The agent must have used --context to show surrounding lines (SKILL.md feature).
    # We verify this by checking that the report includes at least one of the
    # surrounding comment lines near insecure_hash calls, such as "DEPRECATED" or
    # "compliance" or "MD5" or "flagged" appearing alongside the function references.
    try:
        full_str = json.dumps(report)
        context_indicators = ["DEPRECATED", "MD5", "compliance", "flagged", "WARNING", "insecure"]
        found_indicators = [ci for ci in context_indicators if ci in full_str]
        # At least 2 context indicators suggests --context was used to capture surrounding lines
        context_ok = len(found_indicators) >= 2
        checks.append({
            "name": "context_lines_captured",
            "passed": context_ok,
            "detail": (
                f"Found {len(found_indicators)}/6 context indicators in report: {found_indicators}"
            ),
        })
    except Exception as e:
        checks.append({
            "name": "context_lines_captured",
            "passed": False,
            "detail": f"Error checking context lines: {e}",
        })

    # ── CHECK 6: report has structured sections (not just raw text dump) ──────
    try:
        is_dict = isinstance(report, dict)
        has_multiple_keys = is_dict and len(report.keys()) >= 3
        checks.append({
            "name": "report_is_structured_json",
            "passed": has_multiple_keys,
            "detail": f"Report is dict: {is_dict}, keys ({len(report.keys()) if is_dict else 'N/A'}): {list(report.keys())[:10] if is_dict else 'N/A'}",
        })
    except Exception as e:
        checks.append({
            "name": "report_is_structured_json",
            "passed": False,
            "detail": f"Error: {e}",
        })

    # ── Scoring ───────────────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    # Weight each check
    weights = {
        "report_exists_and_parseable": 0.10,
        "directory_tree_section_present": 0.15,
        "config_files_correctly_identified": 0.20,
        "deprecated_insecure_hash_occurrences_found": 0.25,
        "go_test_file_count_correct": 0.15,
        "context_lines_captured": 0.10,
        "report_is_structured_json": 0.05,
    }
    score = sum(weights.get(c["name"], 0.0) for c in checks if c["passed"])
    overall_passed = score >= 0.75 and all(
        c["passed"] for c in checks
        if c["name"] in {
            "report_exists_and_parseable",
            "deprecated_insecure_hash_occurrences_found",
            "config_files_correctly_identified",
        }
    )

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks,
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))