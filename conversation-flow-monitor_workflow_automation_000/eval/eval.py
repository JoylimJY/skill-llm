#!/usr/bin/env python3
"""
Evaluation script for the conversation-flow-monitor task.

Checks:
1. Plugin files with missing/empty/malformed YAML front matter have been repaired
   (both 'name' and 'description' must be present and non-empty)
2. An ERRORS.md file exists at .learnings/ERRORS.md
3. ERRORS.md contains entries for each error category encountered:
   - Skill Registration errors (from invalid plugins)
   - File Not Found errors (from op_001)
   - Browser/timeout errors (from op_003)
   - Network Timeout errors (from op_004, op_008)
4. ERRORS.md documents recovery strategies per the skill's error category table
5. Network timeout entries specifically mention exponential backoff (retry strategy)
6. The repair was an AUTO-FIX (not just flagging) — the files must be parseable after repair
"""

import sys
import json
import re
import os
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

def try_parse_yaml_frontmatter(content: str):
    """Extract and parse YAML front matter from markdown content."""
    if not content.startswith("---"):
        return None, "No front matter delimiter found at start"
    
    # Find the closing ---
    rest = content[3:]
    end_idx = rest.find("\n---")
    if end_idx == -1:
        return None, "No closing --- delimiter found"
    
    fm_text = rest[:end_idx].strip()
    if not fm_text:
        return {}, "Empty front matter"
    
    try:
        if yaml:
            data = yaml.safe_load(fm_text)
            return data if isinstance(data, dict) else {}, None
        else:
            # fallback: simple key:value parser
            data = {}
            for line in fm_text.splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    data[k.strip()] = v.strip()
            return data, None
    except Exception as e:
        return None, f"YAML parse error: {e}"


def check_field_valid(val):
    """Returns True if a field is present, non-None, and non-empty-string."""
    if val is None:
        return False
    if isinstance(val, str) and val.strip() == "":
        return False
    return True


def run_eval(workspace: str):
    checks = []
    workspace = Path(workspace)

    # ── KNOWN INVALID PLUGIN FILES (from gen_inputs_script) ──────────────────
    invalid_plugin_paths = [
        "plugins/core/scheduler.md",          # missing description
        "plugins/core/memory_cache.md",        # missing name
        "plugins/experimental/vision_parser.md",   # empty front matter
        "plugins/experimental/code_executor.md",   # NO front matter at all
        "plugins/experimental/sentiment_analyzer.md",  # name is empty string
        "plugins/deprecated/legacy_http.md",   # description is empty string
        "plugins/core/http_client_v2.md",      # unclosed front matter
        "plugins/experimental/graph_builder.md",  # name is whitespace only
    ]

    # ── KNOWN VALID PLUGIN FILES (should remain valid) ────────────────────────
    valid_plugin_paths = [
        "plugins/core/browser_navigator.md",
        "plugins/core/file_manager.md",
        "plugins/deprecated/old_ocr.md",
        "plugins/core/data_transformer.md",
    ]

    # CHECK 1: All originally-invalid plugin files have been repaired
    repaired_count = 0
    repair_details = []
    for rel_path in invalid_plugin_paths:
        full_path = workspace / rel_path
        try:
            content = full_path.read_text(encoding="utf-8")
            fm, err = try_parse_yaml_frontmatter(content)
            if fm is None:
                repair_details.append(f"FAIL {rel_path}: could not parse after repair ({err})")
            elif not check_field_valid(fm.get("name")) or not check_field_valid(fm.get("description")):
                missing = []
                if not check_field_valid(fm.get("name")):
                    missing.append("name")
                if not check_field_valid(fm.get("description")):
                    missing.append("description")
                repair_details.append(f"FAIL {rel_path}: still missing/empty: {missing}")
            else:
                repaired_count += 1
                repair_details.append(f"OK   {rel_path}: name='{fm['name']}', description present")
        except FileNotFoundError:
            repair_details.append(f"FAIL {rel_path}: file not found")
        except Exception as e:
            repair_details.append(f"FAIL {rel_path}: exception {e}")

    all_repaired = repaired_count == len(invalid_plugin_paths)
    checks.append({
        "name": "all_invalid_plugins_repaired",
        "passed": all_repaired,
        "detail": f"{repaired_count}/{len(invalid_plugin_paths)} invalid plugins repaired. Details: " + "; ".join(repair_details)
    })

    # CHECK 2: Valid plugin files were not corrupted
    valid_intact = 0
    valid_details = []
    for rel_path in valid_plugin_paths:
        full_path = workspace / rel_path
        try:
            content = full_path.read_text(encoding="utf-8")
            fm, err = try_parse_yaml_frontmatter(content)
            if fm and check_field_valid(fm.get("name")) and check_field_valid(fm.get("description")):
                valid_intact += 1
                valid_details.append(f"OK {rel_path}")
            else:
                valid_details.append(f"CORRUPTED {rel_path}: {err or 'missing fields'}")
        except Exception as e:
            valid_details.append(f"ERROR {rel_path}: {e}")

    checks.append({
        "name": "valid_plugins_not_corrupted",
        "passed": valid_intact == len(valid_plugin_paths),
        "detail": f"{valid_intact}/{len(valid_plugin_paths)} valid plugins still intact. " + "; ".join(valid_details)
    })

    # CHECK 3: .learnings/ERRORS.md exists
    errors_md_path = workspace / ".learnings" / "ERRORS.md"
    errors_md_exists = errors_md_path.exists() and errors_md_path.is_file()
    checks.append({
        "name": "errors_md_exists_at_learnings",
        "passed": errors_md_exists,
        "detail": f".learnings/ERRORS.md {'found' if errors_md_exists else 'NOT FOUND'} at {errors_md_path}"
    })

    errors_content = ""
    if errors_md_exists:
        try:
            errors_content = errors_md_path.read_text(encoding="utf-8")
        except Exception as e:
            errors_content = ""
            checks.append({
                "name": "errors_md_readable",
                "passed": False,
                "detail": f"Could not read ERRORS.md: {e}"
            })

    errors_lower = errors_content.lower()

    # CHECK 4: ERRORS.md covers "Skill Registration" error category
    skill_reg_patterns = [
        r"skill.{0,20}registr",
        r"yaml.{0,20}front.{0,20}matter",
        r"front.{0,20}matter",
        r"missing.{0,30}(name|description)",
        r"plugin.{0,20}(invalid|repair|fix|malform)",
    ]
    skill_reg_found = any(re.search(p, errors_lower) for p in skill_reg_patterns)
    checks.append({
        "name": "errors_md_covers_skill_registration",
        "passed": skill_reg_found,
        "detail": f"ERRORS.md {'contains' if skill_reg_found else 'MISSING'} skill registration / YAML front matter error entries"
    })

    # CHECK 5: ERRORS.md covers "File Not Found" error category
    fnf_patterns = [
        r"file.{0,20}not.{0,20}found",
        r"path.{0,20}(missing|not exist|invalid)",
        r"no such file",
        r"file.{0,20}(error|fail)",
        r"sensor_readings",  # the specific file from op_001
    ]
    fnf_found = any(re.search(p, errors_lower) for p in fnf_patterns)
    checks.append({
        "name": "errors_md_covers_file_not_found",
        "passed": fnf_found,
        "detail": f"ERRORS.md {'contains' if fnf_found else 'MISSING'} File Not Found error entries"
    })

    # CHECK 6: ERRORS.md covers timeout/browser hang errors
    timeout_patterns = [
        r"timeout",
        r"browser.{0,30}hang",
        r"browser.{0,30}(fail|error|stuck)",
        r"operation.{0,30}timed.{0,10}out",
        r"hung",
    ]
    timeout_found = any(re.search(p, errors_lower) for p in timeout_patterns)
    checks.append({
        "name": "errors_md_covers_timeout_errors",
        "passed": timeout_found,
        "detail": f"ERRORS.md {'contains' if timeout_found else 'MISSING'} timeout / browser hang error entries"
    })

    # CHECK 7: ERRORS.md covers Network Timeout errors specifically
    network_patterns = [
        r"network.{0,30}timeout",
        r"network.{0,30}(fail|error)",
        r"connection.{0,30}timeout",
        r"http.{0,30}(fail|error|timeout)",
        r"notify\.internal",
        r"weather\.service",
    ]
    network_found = any(re.search(p, errors_lower) for p in network_patterns)
    checks.append({
        "name": "errors_md_covers_network_timeout",
        "passed": network_found,
        "detail": f"ERRORS.md {'contains' if network_found else 'MISSING'} network timeout error entries"
    })

    # CHECK 8: ERRORS.md mentions exponential backoff for network retries (proprietary trap)
    backoff_patterns = [
        r"exponential.{0,20}backoff",
        r"backoff",
        r"exponential.{0,20}retry",
        r"retry.{0,30}exponential",
    ]
    backoff_found = any(re.search(p, errors_lower) for p in backoff_patterns)
    checks.append({
        "name": "errors_md_mentions_exponential_backoff",
        "passed": backoff_found,
        "detail": f"ERRORS.md {'mentions' if backoff_found else 'DOES NOT MENTION'} exponential backoff for network retry strategy (required by SKILL.md)"
    })

    # CHECK 9: ERRORS.md mentions recovery/auto-fix strategies (not just listing errors)
    recovery_patterns = [
        r"recover",
        r"auto.?fix",
        r"fallback",
        r"alternative",
        r"graceful",
        r"repair",
        r"mitigation",
        r"resolution",
    ]
    recovery_found = any(re.search(p, errors_lower) for p in recovery_patterns)
    checks.append({
        "name": "errors_md_documents_recovery_strategies",
        "passed": recovery_found,
        "detail": f"ERRORS.md {'documents' if recovery_found else 'MISSING'} recovery/auto-fix strategies (not just error listing)"
    })

    # CHECK 10: ERRORS.md is non-trivial (at least 200 characters, some structure)
    has_content = len(errors_content.strip()) >= 200
    has_structure = (
        "#" in errors_content or
        "|" in errors_content or
        "-" in errors_content or
        "*" in errors_content
    )
    checks.append({
        "name": "errors_md_has_meaningful_content",
        "passed": has_content and has_structure,
        "detail": f"ERRORS.md length={len(errors_content.strip())} chars, has_structure={has_structure}"
    })

    # ── SCORING ───────────────────────────────────────────────────────────────
    weights = {
        "all_invalid_plugins_repaired": 0.25,
        "valid_plugins_not_corrupted": 0.05,
        "errors_md_exists_at_learnings": 0.10,
        "errors_md_covers_skill_registration": 0.10,
        "errors_md_covers_file_not_found": 0.08,
        "errors_md_covers_timeout_errors": 0.08,
        "errors_md_covers_network_timeout": 0.08,
        "errors_md_mentions_exponential_backoff": 0.12,
        "errors_md_documents_recovery_strategies": 0.09,
        "errors_md_has_meaningful_content": 0.05,
    }

    score = 0.0
    for check in checks:
        w = weights.get(check["name"], 0.0)
        if check["passed"]:
            score += w

    all_passed = all(c["passed"] for c in checks)

    result = {
        "passed": all_passed,
        "score": round(score, 4),
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    run_eval(sys.argv[1])