#!/usr/bin/env python3
"""
Evaluation script for the agent-orchestrator task.

Checks:
 1. At least 3 sub-agent workspaces exist under agents/ (created via create_agent.py)
 2. Each agent has a non-placeholder SKILL.md (dynamically generated, not the stub)
 3. Each agent's inbox/instructions.md follows the required protocol format
 4. Each agent's status.json reached "completed" state
 5. Each agent's outbox/ contains the mandatory summary.md
 6. Each agent's outbox/ contains at least one primary deliverable beyond summary.md
 7. A final consolidated report (audit_report.md or similar) exists somewhere
 8. dissolve_agents.py was run: _archive/ directory exists inside agents/ OR agents are gone
 9. SKILL.md for each sub-agent contains mandatory sections
10. instructions.md contains all required section headers from the protocol
"""

import json
import os
import re
import sys
from pathlib import Path

def load_json_safe(path):
    try:
        return json.loads(Path(path).read_text()), None
    except Exception as e:
        return None, str(e)

def check_instructions_format(instructions_path):
    """Verify inbox/instructions.md has the required section headers."""
    try:
        content = Path(instructions_path).read_text()
    except Exception as e:
        return False, f"Cannot read: {e}"

    required_sections = [
        r"^# Task:",
        r"^## Objective",
        r"^## Context",
        r"^## Inputs Provided",
        r"^## Requirements",
        r"^## Success Criteria",
        r"^## Output Expectations",
    ]
    missing = []
    for pattern in required_sections:
        if not re.search(pattern, content, re.MULTILINE):
            missing.append(pattern)
    if missing:
        return False, f"Missing sections: {missing}"
    return True, "OK"

def check_skill_md(skill_path):
    """Verify SKILL.md is not the default placeholder and has required content."""
    try:
        content = Path(skill_path).read_text()
    except Exception as e:
        return False, f"Cannot read: {e}"

    # Must not be the raw placeholder written by create_agent.py
    if content.strip() == "# SKILL.md\n# Orchestrator must populate this file.":
        return False, "SKILL.md is the default placeholder — not dynamically generated"

    # Must contain at least some of the mandatory sections expected from templates
    required_markers = ["## Objective", "## Communication Protocol"]
    missing = [m for m in required_markers if m not in content]
    if missing:
        return False, f"Missing required SKILL.md sections: {missing}"

    return True, "OK"

def evaluate(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0
    weights = {}

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        nonlocal total_score
        if passed:
            total_score += weight
        weights[name] = weight

    # ── Locate agents workspace ──
    agents_root = workspace / "agents"

    # Check 1: agents/ directory exists
    if not agents_root.exists():
        add_check("agents_dir_exists", False, "agents/ directory not found", 0.5)
        # Cannot continue — return early
        final_score = total_score / max(sum(weights.values()), 1)
        return {"passed": False, "score": round(final_score, 3), "checks": checks}
    else:
        add_check("agents_dir_exists", True, "agents/ directory found", 0.5)

    # Find agent subdirectories (skip _archive and dotfiles)
    # Agents may have been archived — look in both places
    archive_root = agents_root / "_archive"
    
    def find_agent_dirs(root):
        dirs = []
        if not root.exists():
            return dirs
        for d in root.iterdir():
            if d.is_dir() and not d.name.startswith(".") and not d.name.startswith("_"):
                # It's an agent dir if it has status.json
                if (d / "status.json").exists():
                    dirs.append(d)
        return dirs

    live_agents = find_agent_dirs(agents_root)
    archived_agents = find_agent_dirs(archive_root)
    all_agents = live_agents + archived_agents

    # Check 2: At least 3 agents were created
    min_agents = 3
    add_check(
        "min_3_agents_created",
        len(all_agents) >= min_agents,
        f"Found {len(all_agents)} agent workspace(s) (need ≥{min_agents}): "
        f"{[a.name for a in all_agents]}",
        weight=1.5
    )

    if not all_agents:
        final_score = total_score / max(sum(weights.values()), 1)
        return {"passed": False, "score": round(final_score, 3), "checks": checks}

    # Per-agent checks
    agents_with_valid_skill = 0
    agents_with_valid_instructions = 0
    agents_completed = 0
    agents_with_summary = 0
    agents_with_primary_deliverable = 0

    for agent_dir in all_agents:
        aname = agent_dir.name

        # SKILL.md check
        skill_ok, skill_detail = check_skill_md(agent_dir / "SKILL.md")
        if skill_ok:
            agents_with_valid_skill += 1

        # instructions.md check
        instructions_path = agent_dir / "inbox" / "instructions.md"
        if instructions_path.exists():
            instr_ok, instr_detail = check_instructions_format(instructions_path)
        else:
            instr_ok, instr_detail = False, "inbox/instructions.md missing"
        if instr_ok:
            agents_with_valid_instructions += 1

        # status.json check
        status_data, status_err = load_json_safe(agent_dir / "status.json")
        if status_data and status_data.get("state") == "completed":
            agents_completed += 1

        # outbox/summary.md check
        summary_path = agent_dir / "outbox" / "summary.md"
        if summary_path.exists() and len(summary_path.read_text().strip()) > 20:
            agents_with_summary += 1

        # At least one primary deliverable beyond summary.md
        outbox = agent_dir / "outbox"
        if outbox.exists():
            outbox_files = [
                f for f in outbox.iterdir()
                if f.is_file() and f.name != "summary.md"
            ]
            if outbox_files:
                agents_with_primary_deliverable += 1

    n = len(all_agents)

    add_check(
        "all_agents_have_valid_skill_md",
        agents_with_valid_skill == n,
        f"{agents_with_valid_skill}/{n} agents have a dynamically generated SKILL.md",
        weight=2.0
    )

    add_check(
        "all_agents_have_valid_instructions",
        agents_with_valid_instructions == n,
        f"{agents_with_valid_instructions}/{n} agents have correctly formatted inbox/instructions.md "
        f"(requires: # Task:, ## Objective, ## Context, ## Inputs Provided, ## Requirements, "
        f"## Success Criteria, ## Output Expectations)",
        weight=2.0
    )

    add_check(
        "all_agents_reached_completed_state",
        agents_completed == n,
        f"{agents_completed}/{n} agents have status.json state == 'completed'",
        weight=1.5
    )

    add_check(
        "all_agents_have_summary_md",
        agents_with_summary == n,
        f"{agents_with_summary}/{n} agents have a non-empty outbox/summary.md (mandatory protocol output)",
        weight=1.5
    )

    add_check(
        "all_agents_have_primary_deliverable",
        agents_with_primary_deliverable == n,
        f"{agents_with_primary_deliverable}/{n} agents have at least one primary deliverable in outbox/ beyond summary.md",
        weight=1.0
    )

    # Check 8: Dissolution — either _archive/ exists with agent dirs, or agents were removed
    dissolution_done = archive_root.exists() and len(archived_agents) >= min_agents
    # Also accept: live agents are all gone (deleted mode)
    all_live_gone = len(live_agents) == 0 and len(archived_agents) >= min_agents
    
    add_check(
        "dissolution_ran_with_archive",
        dissolution_done or all_live_gone,
        f"dissolve_agents.py --archive was run: _archive/ exists={archive_root.exists()}, "
        f"archived agents={len(archived_agents)}, live agents remaining={len(live_agents)}",
        weight=1.0
    )

    # Check 9: Final consolidated audit report exists somewhere in workspace
    # Search broadly — agent may place it in various locations
    possible_report_names = [
        "audit_report.md", "final_report.md", "consolidated_report.md",
        "compliance_report.md", "audit_summary.md", "final_audit.md",
        "report.md", "audit.md"
    ]
    found_report = None
    for name in possible_report_names:
        matches = list(workspace.rglob(name))
        if matches:
            found_report = matches[0]
            break
    # Also accept any .md in workspace root that is large enough to be a report
    if not found_report:
        for md_file in workspace.glob("*.md"):
            if md_file.stat().st_size > 200:
                found_report = md_file
                break

    report_content_ok = False
    report_detail = "No consolidated audit report found"
    if found_report:
        try:
            content = found_report.read_text()
            # Must reference multiple agents or contain audit findings
            has_agent_refs = sum(1 for a in all_agents if a.name in content) >= 2
            has_findings = any(kw in content.lower() for kw in
                               ["security", "compliance", "vulnerability", "finding",
                                "performance", "pci", "risk", "agent"])
            report_content_ok = has_findings and len(content) > 300
            report_detail = (f"Found report at {found_report.relative_to(workspace)}: "
                             f"size={len(content)} chars, findings_keywords={has_findings}, "
                             f"agent_refs≥2={has_agent_refs}")
        except Exception as e:
            report_detail = f"Found {found_report} but cannot read: {e}"

    add_check(
        "consolidated_audit_report_exists",
        report_content_ok,
        report_detail,
        weight=2.0
    )

    # ── Final scoring ──
    total_weight = sum(weights.values())
    final_score = round(total_score / total_weight, 3)
    overall_passed = (
        len(all_agents) >= min_agents
        and agents_with_valid_skill == n
        and agents_with_valid_instructions == n
        and agents_completed == n
        and agents_with_summary == n
        and report_content_ok
        and (dissolution_done or all_live_gone)
    )

    return {"passed": overall_passed, "score": final_score, "checks": checks}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "args", "passed": False,
                                      "detail": "Usage: eval.py <workspace>"}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))