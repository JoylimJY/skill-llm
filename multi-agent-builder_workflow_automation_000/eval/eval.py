import sys
import json
import os
import re
from pathlib import Path

def load_json_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def find_file(workspace, filename):
    results = list(Path(workspace).rglob(filename))
    return results[0] if results else None

def evaluate(workspace):
    checks = []
    score = 0.0
    total_weight = 0.0

    def add_check(name, passed, detail, weight=1.0):
        nonlocal score, total_weight
        checks.append({"name": name, "passed": passed, "detail": detail})
        total_weight += weight
        if passed:
            score += weight

    # =========================================================
    # CHECK 1: openclaw.json exists and has agents array (weight 1.5)
    # =========================================================
    openclaw_path = os.path.join(workspace, "config", "openclaw.json")
    openclaw_data = None
    try:
        openclaw_data = load_json_file(openclaw_path)
        agents = openclaw_data.get("agents", [])
        has_agents = len(agents) >= 3
        add_check(
            "openclaw.json has at least 3 agents defined",
            has_agents,
            f"Found {len(agents)} agents in config/openclaw.json" if agents is not None else "agents key missing",
            weight=1.5
        )
    except FileNotFoundError:
        add_check("openclaw.json exists at config/openclaw.json", False, "File not found", weight=1.5)
    except json.JSONDecodeError as e:
        add_check("openclaw.json is valid JSON", False, f"JSON decode error: {e}", weight=1.5)

    # =========================================================
    # CHECK 2: team-leader agent ID must be team-prefixed (e.g., biotech-reg-team-leader) (weight 2.0)
    # =========================================================
    try:
        agents = openclaw_data.get("agents", []) if openclaw_data else []
        leader_agents = [a for a in agents if
                         isinstance(a, dict) and (
                             'team-leader' in a.get('role', '').lower() or
                             'team leader' in a.get('role', '').lower() or
                             a.get('id', '').endswith('-team-leader')
                         )]
        if leader_agents:
            leader = leader_agents[0]
            leader_id = leader.get('id', '')
            # Must end with -team-leader AND have a prefix (not just "team-leader")
            correct_format = bool(re.match(r'^[a-z][a-z0-9-]+-team-leader$', leader_id))
            add_check(
                "team-leader agent ID is team-prefixed (e.g., biotech-reg-team-leader)",
                correct_format,
                f"team-leader ID found: '{leader_id}'. Must match pattern <team>-team-leader (e.g., biotech-reg-team-leader)",
                weight=2.0
            )
        else:
            add_check(
                "team-leader agent ID is team-prefixed",
                False,
                "No team-leader agent found in openclaw.json agents array",
                weight=2.0
            )
    except Exception as e:
        add_check("team-leader ID check", False, f"Error: {e}", weight=2.0)

    # =========================================================
    # CHECK 3: All agent IDs are lowercase-hyphen format (weight 1.5)
    # =========================================================
    try:
        agents = openclaw_data.get("agents", []) if openclaw_data else []
        bad_ids = []
        for a in agents:
            if isinstance(a, dict):
                aid = a.get('id', '')
                if aid and not re.match(r'^[a-z][a-z0-9-]*$', aid):
                    bad_ids.append(aid)
        all_valid = len(bad_ids) == 0 and len(agents) > 0
        add_check(
            "All agent IDs are lowercase-hyphen format",
            all_valid,
            f"Invalid IDs: {bad_ids}" if bad_ids else f"All {len(agents)} agent IDs valid",
            weight=1.5
        )
    except Exception as e:
        add_check("Agent ID format check", False, f"Error: {e}", weight=1.5)

    # =========================================================
    # CHECK 4: Each agent in openclaw.json has required config fields (weight 1.5)
    # =========================================================
    try:
        agents = openclaw_data.get("agents", []) if openclaw_data else []
        required_fields = ['id', 'role', 'status', 'permissions', 'skills', 'team']
        agents_missing_fields = []
        for a in agents:
            if isinstance(a, dict):
                missing = [f for f in required_fields if f not in a]
                if missing:
                    agents_missing_fields.append(f"{a.get('id','?')}: missing {missing}")
        all_complete = len(agents_missing_fields) == 0 and len(agents) > 0
        add_check(
            "All agents have required config fields (id, role, status, permissions, skills, team)",
            all_complete,
            f"Agents with missing fields: {agents_missing_fields}" if agents_missing_fields else "All agents complete",
            weight=1.5
        )
    except Exception as e:
        add_check("Agent config fields check", False, f"Error: {e}", weight=1.5)

    # =========================================================
    # CHECK 5: team_creation_report.json exists and has correct structure (weight 2.0)
    # =========================================================
    report_path = os.path.join(workspace, "config", "team_creation_report.json")
    report_data = None
    try:
        report_data = load_json_file(report_path)
        has_team_name = 'team_name' in report_data or 'team_slug' in report_data
        has_status = 'status' in report_data
        has_agents_field = 'agents' in report_data
        # Must have been run through create_team.mjs (script sets _script_run)
        script_was_run = report_data.get('_script_run', False)
        report_valid = has_team_name and has_status and has_agents_field
        add_check(
            "team_creation_report.json has required structure (team_name/slug, status, agents)",
            report_valid,
            f"team_name/slug: {has_team_name}, status: {has_status}, agents: {has_agents_field}",
            weight=1.5
        )
        add_check(
            "create_team.mjs was executed (script_run marker present in report)",
            script_was_run,
            "Report shows _script_run=True (create_team.mjs executed)" if script_was_run
            else "create_team.mjs was NOT run - _script_run marker missing. Agent must run scripts/create_team.mjs",
            weight=2.0
        )
    except FileNotFoundError:
        add_check("team_creation_report.json exists at config/team_creation_report.json", False,
                  "File not found", weight=1.5)
        add_check("create_team.mjs was executed", False, "Report file missing", weight=2.0)
    except json.JSONDecodeError as e:
        add_check("team_creation_report.json is valid JSON", False, f"JSON decode error: {e}", weight=1.5)
        add_check("create_team.mjs was executed", False, "Report file malformed", weight=2.0)

    # =========================================================
    # CHECK 6: team_creation_report.json status is 'ready' (weight 1.5)
    # =========================================================
    try:
        if report_data:
            # The script sets _materialize_status; the agent's own status field should also be ready
            script_status = report_data.get('_materialize_status', '')
            agent_status = report_data.get('status', '')
            is_ready = (script_status == 'ready') or (agent_status == 'ready')
            add_check(
                "Team status is 'ready' (all materialization checks passed)",
                is_ready,
                f"Script materialize status: '{script_status}', report status: '{agent_status}'",
                weight=1.5
            )
        else:
            add_check("Team status is 'ready'", False, "Report data unavailable", weight=1.5)
    except Exception as e:
        add_check("Team status check", False, f"Error: {e}", weight=1.5)

    # =========================================================
    # CHECK 7: SOUL.md files exist for agents (weight 1.5)
    # =========================================================
    try:
        soul_files = list(Path(workspace).rglob("SOUL.md"))
        # Expect at least 3 agent SOUL files
        valid_souls = [f for f in soul_files if len(f.read_text().strip()) > 100]
        has_enough_souls = len(valid_souls) >= 3
        add_check(
            "At least 3 non-placeholder SOUL.md files created for agents (>100 chars)",
            has_enough_souls,
            f"Found {len(valid_souls)} valid SOUL.md files (>{100} chars) out of {len(soul_files)} total",
            weight=1.5
        )
    except Exception as e:
        add_check("SOUL.md files check", False, f"Error: {e}", weight=1.5)

    # =========================================================
    # CHECK 8: collaboration_protocol.md exists with required sections (weight 2.0)
    # =========================================================
    try:
        collab_files = list(Path(workspace).rglob("collaboration_protocol.md"))
        if not collab_files:
            # Try variant names
            collab_files = list(Path(workspace).rglob("*collaboration*protocol*"))
        if collab_files:
            content = collab_files[0].read_text()
            has_states = all(state in content for state in ['accepted', 'blocked', 'done'])
            has_callback = 'callback' in content.lower() or 'return' in content.lower()
            has_timeout = 'timeout' in content.lower() or 'escalat' in content.lower()
            has_no_bulk = 'bulk' in content.lower() or 'artifact' in content.lower() or 'summary' in content.lower()
            all_protocol_fields = has_states and has_callback and has_timeout and has_no_bulk
            add_check(
                "collaboration_protocol.md has all required fields (states, callback, timeout/escalation, no-bulk-output rule)",
                all_protocol_fields,
                f"states:{has_states}, callback:{has_callback}, timeout/escalation:{has_timeout}, no-bulk:{has_no_bulk}",
                weight=2.0
            )
        else:
            add_check(
                "collaboration_protocol.md exists and has required fields",
                False,
                "No collaboration_protocol.md file found anywhere in workspace",
                weight=2.0
            )
    except Exception as e:
        add_check("collaboration_protocol.md check", False, f"Error: {e}", weight=2.0)

    # =========================================================
    # CHECK 9: channel_binding_blueprint.md exists (weight 1.0)
    # =========================================================
    try:
        blueprint_files = list(Path(workspace).rglob("channel_binding_blueprint.md"))
        if not blueprint_files:
            blueprint_files = list(Path(workspace).rglob("*channel*binding*"))
        if blueprint_files:
            content = blueprint_files[0].read_text()
            has_routing = 'routing_mode' in content or 'single-bot' in content or 'multi-bot' in content
            has_token_ref = 'bot_token_ref' in content or 'secret' in content.lower() or 'vault' in content.lower() or 'token_ref' in content.lower()
            has_leader_ref = 'team-leader' in content or 'team_leader_id' in content
            blueprint_valid = has_routing and (has_token_ref or has_leader_ref)
            add_check(
                "channel_binding_blueprint.md exists with routing_mode and security-safe token reference",
                blueprint_valid,
                f"routing_mode:{has_routing}, safe_token_ref:{has_token_ref}, leader_ref:{has_leader_ref}",
                weight=1.0
            )
        else:
            add_check(
                "channel_binding_blueprint.md exists",
                False,
                "No channel_binding_blueprint.md found anywhere in workspace",
                weight=1.0
            )
    except Exception as e:
        add_check("channel_binding_blueprint.md check", False, f"Error: {e}", weight=1.0)

    # =========================================================
    # CHECK 10: team-leader subagents A2A binding in openclaw.json (weight 1.5)
    # =========================================================
    try:
        agents = openclaw_data.get("agents", []) if openclaw_data else []
        leader_agents = [a for a in agents if isinstance(a, dict) and a.get('id', '').endswith('-team-leader')]
        if leader_agents:
            leader = leader_agents[0]
            subagents = leader.get('subagents', [])
            has_subagents = isinstance(subagents, list) and len(subagents) > 0
            # Verify specialists list team-leader as escalation_agent
            specialists = [a for a in agents if isinstance(a, dict) and not a.get('id', '').endswith('-team-leader')]
            specialists_with_escalation = [
                a for a in specialists
                if a.get('escalation_agent', '') == leader.get('id', '') or
                   leader.get('id', '') in str(a.get('escalation_agent', ''))
            ]
            escalation_ok = len(specialists_with_escalation) >= len(specialists) * 0.5 and len(specialists) > 0
            add_check(
                "team-leader has subagents[] list with team members",
                has_subagents,
                f"team-leader subagents: {subagents}",
                weight=1.0
            )
            add_check(
                "Specialists have escalation_agent pointing to team-leader",
                escalation_ok,
                f"{len(specialists_with_escalation)}/{len(specialists)} specialists have correct escalation_agent",
                weight=1.0
            )
        else:
            add_check("team-leader A2A subagents binding", False,
                      "No agent with id ending in '-team-leader' found", weight=1.0)
            add_check("Specialists escalation_agent check", False,
                      "team-leader not found", weight=1.0)
    except Exception as e:
        add_check("A2A binding check", False, f"Error: {e}", weight=2.0)

    # =========================================================
    # CHECK 11: team-leader SOUL.md does NOT contain specialist deliverable language (weight 1.5)
    # =========================================================
    try:
        leader_agents = [a for a in (openclaw_data.get("agents", []) if openclaw_data else [])
                         if isinstance(a, dict) and a.get('id', '').endswith('-team-leader')]
        if leader_agents:
            leader_id = leader_agents[0].get('id', '')
            soul_path = Path(workspace) / "agents" / leader_id / "SOUL.md"
            if soul_path.exists():
                soul_content = soul_path.read_text().lower()
                # team-leader must orchestrate only, not produce specialist work
                bad_phrases = ['draft', 'write regulatory', 'conduct audit', 'compile dossier',
                               'analyze data', 'file safety report', 'prepare submission']
                has_specialist_work = any(phrase in soul_content for phrase in bad_phrases)
                has_orchestration_focus = any(word in soul_content for word in
                                              ['orchestrat', 'delegat', 'coordinat', 'monitor', 'track'])
                soul_correct = not has_specialist_work and has_orchestration_focus
                add_check(
                    "team-leader SOUL.md is orchestration-only (no specialist deliverables)",
                    soul_correct,
                    f"Orchestration focus: {has_orchestration_focus}, Specialist work phrases found: {has_specialist_work}",
                    weight=1.5
                )
            else:
                add_check("team-leader SOUL.md orchestration check",
                          False,
                          f"SOUL.md not found at agents/{leader_id}/SOUL.md",
                          weight=1.5)
        else:
            add_check("team-leader SOUL.md orchestration check", False,
                      "team-leader not identified", weight=1.5)
    except Exception as e:
        add_check("team-leader SOUL orchestration check", False, f"Error: {e}", weight=1.5)

    # =========================================================
    # CHECK 12: smoke_test.md exists (weight 0.5)
    # =========================================================
    try:
        smoke_files = list(Path(workspace).rglob("smoke_test.md"))
        add_check(
            "smoke_test.md exists",
            len(smoke_files) > 0,
            f"Found {len(smoke_files)} smoke_test.md file(s)",
            weight=0.5
        )
    except Exception as e:
        add_check("smoke_test.md exists", False, f"Error: {e}", weight=0.5)

    # =========================================================
    # FINAL SCORE
    # =========================================================
    final_score = round(score / total_weight, 4) if total_weight > 0 else 0.0
    all_passed = all(c["passed"] for c in checks)

    return {
        "passed": all_passed,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))