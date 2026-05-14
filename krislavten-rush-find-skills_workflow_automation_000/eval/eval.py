#!/usr/bin/env python3
"""
Evaluation script for the reskill skill-discovery task.
Usage: python3 eval.py <workspace_dir>
"""
import sys
import json
import os
from pathlib import Path

def load_json_file(path):
    with open(path, "r") as f:
        return json.load(f)

def read_lines(path):
    with open(path, "r") as f:
        return [line.strip() for line in f if line.strip()]

def parse_log(log_path):
    """Parse the reskill call log into a list of arg-lists."""
    calls = []
    try:
        for line in read_lines(log_path):
            entry = json.loads(line)
            calls.append(entry.get("args", []))
    except Exception:
        pass
    return calls

def parse_install_log(log_path):
    """Parse the reskill install log."""
    installs = []
    try:
        for line in read_lines(log_path):
            entry = json.loads(line)
            installs.append(entry.get("install_args", []))
    except Exception:
        pass
    return installs

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []

    # ── Load logs ─────────────────────────────────────────────────────────────
    call_log_path = "/tmp/reskill_calls.log"
    install_log_path = "/tmp/reskill_installs.log"

    all_calls = parse_log(call_log_path)
    install_calls = parse_install_log(install_log_path)

    # ── CHECK 1: reskill was invoked at all ───────────────────────────────────
    reskill_used = len(all_calls) > 0
    checks.append({
        "name": "reskill_cli_was_invoked",
        "passed": reskill_used,
        "detail": f"Total reskill calls: {len(all_calls)}. Calls: {all_calls[:5]}"
    })

    # ── CHECK 2: Progressive search - multi-word query attempted first ─────────
    # The agent should have tried "deployment automation" or similar two-word query
    find_calls = [c for c in all_calls if c and c[0] == "find"]
    find_queries = []
    for call in find_calls:
        # extract the query (first positional after 'find')
        q = None
        for token in call[1:]:
            if not token.startswith("--") and not token.startswith("-"):
                q = token.lower()
                break
        if q:
            find_queries.append(q)

    # Check that at least one multi-word or hyphenated search was done
    multi_word_searched = any(
        (" " in q or "-" in q) 
        for q in find_queries
    )
    checks.append({
        "name": "progressive_search_multi_word_attempted",
        "passed": multi_word_searched,
        "detail": f"Find queries observed: {find_queries}. At least one multi-word/hyphenated query required."
    })

    # ── CHECK 3: Single-keyword search was also used (broadening step) ─────────
    single_keyword_deployment_searched = any(
        q in ["deployment", "deploy", "ci-cd", "devops", "automation"]
        for q in find_queries
    )
    checks.append({
        "name": "progressive_search_single_keyword_used",
        "passed": single_keyword_deployment_searched,
        "detail": f"Find queries observed: {find_queries}. Expected a single-keyword broadening step."
    })

    # ── CHECK 4: --json flag used in search ───────────────────────────────────
    json_flag_used = any(
        "--json" in c
        for c in find_calls
    )
    checks.append({
        "name": "json_flag_used_in_search",
        "passed": json_flag_used,
        "detail": f"Find calls: {find_calls}. --json flag required for structured results."
    })

    # ── CHECK 5: @devops/ci-deploy was installed (not @ui/design-helper) ──────
    correct_skill_installed = False
    wrong_skill_installed = False
    for inst_args in install_calls:
        # skill name is the first non-flag arg after 'install'
        for token in inst_args:
            if not token.startswith("-"):
                if "@devops/ci-deploy" in token:
                    correct_skill_installed = True
                if "@ui/design-helper" in token:
                    wrong_skill_installed = True
    checks.append({
        "name": "correct_skill_installed",
        "passed": correct_skill_installed and not wrong_skill_installed,
        "detail": f"@devops/ci-deploy installed: {correct_skill_installed}, @ui/design-helper (wrong) installed: {wrong_skill_installed}. Install args: {install_calls}"
    })

    # ── CHECK 6: skills.json targetAgents respected (claude-code AND codex used) ─
    # Must NOT use 'cursor' (which would indicate directory-based detection was used)
    agents_used = set()
    for inst_args in install_calls:
        # Parse -a / --agent flags
        i = 0
        while i < len(inst_args):
            if inst_args[i] in ["-a", "--agent"]:
                i += 1
                while i < len(inst_args) and not inst_args[i].startswith("-"):
                    agents_used.add(inst_args[i])
                    i += 1
                continue
            i += 1

    claude_code_targeted = "claude-code" in agents_used
    codex_targeted = "codex" in agents_used
    cursor_not_targeted = "cursor" not in agents_used

    checks.append({
        "name": "skills_json_target_agents_respected_claude_code",
        "passed": claude_code_targeted,
        "detail": f"Agents used in install: {agents_used}. 'claude-code' required from skills.json targetAgents."
    })
    checks.append({
        "name": "skills_json_target_agents_respected_codex",
        "passed": codex_targeted,
        "detail": f"Agents used in install: {agents_used}. 'codex' required from skills.json targetAgents."
    })
    checks.append({
        "name": "cursor_directory_trap_avoided",
        "passed": cursor_not_targeted,
        "detail": f"Agents used in install: {agents_used}. 'cursor' should NOT be targeted because skills.json overrides directory detection."
    })

    # ── CHECK 7: -y flag used in install ─────────────────────────────────────
    y_flag_used = any(
        "-y" in inst_args
        for inst_args in install_calls
    )
    checks.append({
        "name": "yes_flag_used_in_install",
        "passed": y_flag_used,
        "detail": f"Install args: {install_calls}. -y flag required to skip confirmation prompts."
    })

    # ── CHECK 8: --registry explicitly specified in install ───────────────────
    registry_in_install = False
    for inst_args in install_calls:
        if "--registry" in inst_args:
            idx = inst_args.index("--registry")
            if idx + 1 < len(inst_args):
                registry_val = inst_args[idx + 1]
                if "rush.zhenguanyu.com" in registry_val:
                    registry_in_install = True
    checks.append({
        "name": "registry_explicitly_specified_in_install",
        "passed": registry_in_install,
        "detail": f"Install args: {install_calls}. --registry https://rush.zhenguanyu.com required in install command."
    })

    # ── CHECK 9: install_report.json exists and has required content ───────────
    report_files = list(Path(workspace).rglob("install_report.json"))
    report_valid = False
    report_detail = "install_report.json not found in workspace."
    if report_files:
        try:
            report = load_json_file(report_files[0])
            # Must contain at minimum: the skill name and the agents it was installed to
            has_skill = False
            has_agents = False
            report_str = json.dumps(report).lower()
            if "@devops/ci-deploy" in report_str or "ci-deploy" in report_str or "ci_deploy" in report_str:
                has_skill = True
            if "claude-code" in report_str or "claude_code" in report_str:
                has_agents = True
            if "codex" in report_str:
                has_agents = has_agents or True

            report_valid = has_skill and has_agents
            report_detail = (
                f"Found at {report_files[0]}. "
                f"has_skill={has_skill}, has_agents={has_agents}. "
                f"Keys: {list(report.keys()) if isinstance(report, dict) else 'non-dict'}"
            )
        except Exception as e:
            report_detail = f"Found at {report_files[0]} but failed to parse: {e}"
    checks.append({
        "name": "install_report_json_present_and_valid",
        "passed": report_valid,
        "detail": report_detail
    })

    # ── CHECK 10: --registry specified in find command ─────────────────────────
    registry_in_find = any(
        "--registry" in c
        for c in find_calls
    )
    checks.append({
        "name": "registry_specified_in_find_command",
        "passed": registry_in_find,
        "detail": f"Find calls: {find_calls}. --registry should be passed to find commands when not set by env."
    })

    # ── Compute score ─────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total_count = len(checks)
    score = passed_count / total_count

    # Overall pass: must pass all critical checks
    critical_checks = [
        "correct_skill_installed",
        "skills_json_target_agents_respected_claude_code",
        "skills_json_target_agents_respected_codex",
        "cursor_directory_trap_avoided",
        "yes_flag_used_in_install",
        "registry_explicitly_specified_in_install",
    ]
    overall_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )

    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()