#!/usr/bin/env python3
"""
Evaluation script for the reskill multi-step workflow task.
Checks:
1. skills.json exists and is valid JSON
2. skills.json has correct defaults (installMode: copy, targetAgents includes claude-code and codex)
3. Two skills are registered in skills.json skills section
4. installation_report.json exists and is valid JSON from `reskill list --json`
5. The .skills/ directory contains the installed skills (copy mode, not symlinks)
"""

import sys
import json
import os
import subprocess
from pathlib import Path

def run_checks(workspace: str) -> dict:
    checks = []
    overall_passed = True

    def add_check(name: str, passed: bool, detail: str):
        nonlocal overall_passed
        checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            overall_passed = False

    # ── Check 1: skills.json exists ─────────────────────────────────────────────
    skills_json_path = Path(workspace) / "skills.json"
    skills_json = None
    try:
        if skills_json_path.exists():
            with open(skills_json_path) as f:
                skills_json = json.load(f)
            add_check("skills.json exists and is valid JSON", True, f"Found at {skills_json_path}")
        else:
            add_check("skills.json exists and is valid JSON", False, f"skills.json not found at {skills_json_path}")
    except json.JSONDecodeError as e:
        add_check("skills.json exists and is valid JSON", False, f"Invalid JSON: {e}")
    except Exception as e:
        add_check("skills.json exists and is valid JSON", False, f"Error reading: {e}")

    # ── Check 2: skills.json has 'skills' section with at least 2 entries ───────
    try:
        if skills_json is not None:
            skills_section = skills_json.get("skills", {})
            if isinstance(skills_section, dict) and len(skills_section) >= 2:
                add_check(
                    "skills.json contains 2 or more registered skills",
                    True,
                    f"Found {len(skills_section)} skill(s): {list(skills_section.keys())}"
                )
            else:
                add_check(
                    "skills.json contains 2 or more registered skills",
                    False,
                    f"'skills' section has {len(skills_section) if isinstance(skills_section, dict) else 'invalid'} entries, need >= 2"
                )
        else:
            add_check("skills.json contains 2 or more registered skills", False, "skills.json could not be read")
    except Exception as e:
        add_check("skills.json contains 2 or more registered skills", False, f"Error: {e}")

    # ── Check 3: defaults.installMode is "copy" ──────────────────────────────────
    try:
        if skills_json is not None:
            defaults = skills_json.get("defaults", {})
            install_mode = defaults.get("installMode", "")
            if install_mode == "copy":
                add_check(
                    "defaults.installMode is set to 'copy'",
                    True,
                    f"installMode = '{install_mode}'"
                )
            else:
                add_check(
                    "defaults.installMode is set to 'copy'",
                    False,
                    f"installMode = '{install_mode}' (expected 'copy'). Check the defaults section in skills.json."
                )
        else:
            add_check("defaults.installMode is set to 'copy'", False, "skills.json could not be read")
    except Exception as e:
        add_check("defaults.installMode is set to 'copy'", False, f"Error: {e}")

    # ── Check 4: defaults.targetAgents includes claude-code and codex ───────────
    try:
        if skills_json is not None:
            defaults = skills_json.get("defaults", {})
            target_agents = defaults.get("targetAgents", [])
            if isinstance(target_agents, list):
                has_claude = "claude-code" in target_agents
                has_codex = "codex" in target_agents
                if has_claude and has_codex:
                    add_check(
                        "defaults.targetAgents includes 'claude-code' and 'codex'",
                        True,
                        f"targetAgents = {target_agents}"
                    )
                else:
                    missing = [a for a in ["claude-code", "codex"] if a not in target_agents]
                    add_check(
                        "defaults.targetAgents includes 'claude-code' and 'codex'",
                        False,
                        f"Missing agents: {missing}. Found: {target_agents}"
                    )
            else:
                add_check(
                    "defaults.targetAgents includes 'claude-code' and 'codex'",
                    False,
                    f"targetAgents is not a list: {target_agents}"
                )
        else:
            add_check("defaults.targetAgents includes 'claude-code' and 'codex'", False, "skills.json could not be read")
    except Exception as e:
        add_check("defaults.targetAgents includes 'claude-code' and 'codex'", False, f"Error: {e}")

    # ── Check 5: Skills are physically installed (not symlinks) in .skills/ ──────
    try:
        skills_dir = Path(workspace) / ".skills"
        if skills_dir.exists():
            installed = list(skills_dir.iterdir())
            real_dirs = [p for p in installed if p.is_dir() and not p.is_symlink()]
            symlinks = [p for p in installed if p.is_symlink()]
            
            if len(real_dirs) >= 2:
                add_check(
                    "Skills physically copied (not symlinked) to .skills/ directory",
                    True,
                    f"Found {len(real_dirs)} copied skill director(ies): {[p.name for p in real_dirs]}"
                )
            elif len(real_dirs) >= 1 and len(symlinks) >= 1:
                add_check(
                    "Skills physically copied (not symlinked) to .skills/ directory",
                    False,
                    f"Mixed: {len(real_dirs)} copied, {len(symlinks)} symlinked. All should be copied (--mode copy)."
                )
            elif len(symlinks) >= 2:
                add_check(
                    "Skills physically copied (not symlinked) to .skills/ directory",
                    False,
                    f"Found {len(symlinks)} symlink(s) but 0 real copies. Use --mode copy instead of default symlink mode."
                )
            else:
                # Check if installed anywhere - maybe in agent-specific dirs
                # Skills might be in .claude/skills or .codex/skills due to --agent flag
                agent_dirs = [
                    Path(workspace) / ".claude" / "skills",
                    Path(workspace) / ".codex" / "skills",
                ]
                found_agent_installs = []
                for agent_dir in agent_dirs:
                    if agent_dir.exists():
                        found_agent_installs.extend(list(agent_dir.iterdir()))
                
                if found_agent_installs:
                    add_check(
                        "Skills physically copied (not symlinked) to .skills/ directory",
                        True,
                        f".skills/ has {len(installed)} items but agent dirs have {len(found_agent_installs)} items"
                    )
                else:
                    add_check(
                        "Skills physically copied (not symlinked) to .skills/ directory",
                        False,
                        f".skills/ exists but has {len(installed)} items with 0 real directories."
                    )
        else:
            # Check agent-specific directories as alternative
            agent_dirs_found = []
            for agent_dir in [".claude/skills", ".codex/skills"]:
                p = Path(workspace) / agent_dir
                if p.exists() and any(p.iterdir()):
                    agent_dirs_found.append(str(p))
            
            if agent_dirs_found:
                add_check(
                    "Skills physically copied (not symlinked) to .skills/ directory",
                    True,
                    f"Skills found in agent dirs: {agent_dirs_found}"
                )
            else:
                add_check(
                    "Skills physically copied (not symlinked) to .skills/ directory",
                    False,
                    f".skills/ directory not found in workspace and no agent-specific dirs found."
                )
    except Exception as e:
        add_check("Skills physically copied (not symlinked) to .skills/ directory", False, f"Error: {e}")

    # ── Check 6: installation_report.json exists and contains reskill list output ─
    try:
        # Search for installation_report.json anywhere in workspace
        report_files = list(Path(workspace).rglob("installation_report.json"))
        if not report_files:
            add_check(
                "installation_report.json exists with valid reskill list --json output",
                False,
                "installation_report.json not found anywhere in workspace"
            )
        else:
            report_path = report_files[0]
            with open(report_path) as f:
                report_data = json.load(f)
            
            # The output of `reskill list --json` should be an array or object
            # It should contain skill entries - accept array or object
            is_valid_structure = False
            detail_msg = ""
            
            if isinstance(report_data, list):
                # Array of skill objects - typical reskill list --json output
                if len(report_data) >= 2:
                    is_valid_structure = True
                    detail_msg = f"Valid array with {len(report_data)} skill(s) at {report_path}"
                elif len(report_data) >= 1:
                    # At least 1 skill - partial credit scenario, accept it
                    is_valid_structure = True
                    detail_msg = f"Array with {len(report_data)} skill(s) at {report_path}"
                else:
                    detail_msg = f"Empty array in report at {report_path}"
            elif isinstance(report_data, dict):
                # Could be {skills: [...]} or similar
                if "skills" in report_data and isinstance(report_data["skills"], (list, dict)):
                    inner = report_data["skills"]
                    count = len(inner)
                    if count >= 1:
                        is_valid_structure = True
                        detail_msg = f"Valid object with {count} skill(s) at {report_path}"
                    else:
                        detail_msg = f"'skills' key present but empty in {report_path}"
                elif len(report_data) >= 1:
                    # Some other valid JSON object
                    is_valid_structure = True
                    detail_msg = f"Valid JSON object with {len(report_data)} key(s) at {report_path}"
                else:
                    detail_msg = f"Empty JSON object in report at {report_path}"
            else:
                detail_msg = f"Unexpected JSON type: {type(report_data)}"
            
            add_check(
                "installation_report.json exists with valid reskill list --json output",
                is_valid_structure,
                detail_msg
            )
    except json.JSONDecodeError as e:
        add_check(
            "installation_report.json exists with valid reskill list --json output",
            False,
            f"Invalid JSON in report file: {e}"
        )
    except Exception as e:
        add_check(
            "installation_report.json exists with valid reskill list --json output",
            False,
            f"Error reading report: {e}"
        )

    # ── Check 7: skills.lock exists (created by reskill install) ────────────────
    try:
        lock_path = Path(workspace) / "skills.lock"
        if lock_path.exists():
            with open(lock_path) as f:
                lock_content = f.read().strip()
            if lock_content:
                add_check("skills.lock exists (created by reskill install)", True, f"Lock file present with {len(lock_content)} chars")
            else:
                add_check("skills.lock exists (created by reskill install)", False, "skills.lock is empty")
        else:
            add_check("skills.lock exists (created by reskill install)", False, "skills.lock not found - was reskill install run?")
    except Exception as e:
        add_check("skills.lock exists (created by reskill install)", False, f"Error: {e}")

    # ── Scoring ──────────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = passed_count / total if total > 0 else 0.0

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "argument check", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    
    workspace = sys.argv[1]
    result = run_checks(workspace)
    print(json.dumps(result, indent=2))