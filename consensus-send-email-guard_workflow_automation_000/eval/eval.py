import sys
import json
import os
from pathlib import Path

def run_eval(workspace: str):
    checks = []
    total_score = 0.0

    # -----------------------------------------------------------------------
    # CHECK 1: guard_result.json exists somewhere in the workspace
    # -----------------------------------------------------------------------
    guard_result_files = list(Path(workspace).rglob("guard_result.json"))
    if not guard_result_files:
        checks.append({
            "name": "guard_result.json exists",
            "passed": False,
            "detail": "No guard_result.json found anywhere in the workspace."
        })
        # All subsequent checks will fail without this file
        result_data = None
    else:
        checks.append({
            "name": "guard_result.json exists",
            "passed": True,
            "detail": f"Found at: {guard_result_files[0]}"
        })
        total_score += 0.15
        try:
            with open(guard_result_files[0], "r") as f:
                result_data = json.load(f)
        except Exception as e:
            checks.append({
                "name": "guard_result.json is valid JSON",
                "passed": False,
                "detail": f"Failed to parse JSON: {e}"
            })
            result_data = None

    # -----------------------------------------------------------------------
    # CHECK 2: guard_result.json is valid JSON
    # -----------------------------------------------------------------------
    if result_data is not None and len(checks) == 1:
        # We parsed successfully above but didn't add a check yet
        checks.append({
            "name": "guard_result.json is valid JSON",
            "passed": True,
            "detail": "JSON parsed successfully."
        })
        total_score += 0.10

    # -----------------------------------------------------------------------
    # CHECK 3: Result contains a 'decision' field with BLOCK or REWRITE
    # (Given the email contains PHI, medical guarantees, and disallowed claims,
    #  the weighted majority votes BLOCK; REWRITE is also acceptable as one voter said REWRITE)
    # -----------------------------------------------------------------------
    if result_data is not None:
        decision = None
        # The decision may be at the top level or nested
        if isinstance(result_data, dict):
            decision = result_data.get("decision") or result_data.get("result") or result_data.get("status")
            # Search nested if needed
            if not decision:
                for key, val in result_data.items():
                    if isinstance(val, dict):
                        decision = val.get("decision") or val.get("result")
                        if decision:
                            break
                    elif isinstance(val, str) and val.upper() in ("BLOCK", "REWRITE", "APPROVE"):
                        decision = val
                        break

        if decision and isinstance(decision, str) and decision.upper() in ("BLOCK", "REWRITE", "APPROVE"):
            checks.append({
                "name": "decision field present and valid enum value",
                "passed": True,
                "detail": f"decision={decision.upper()}"
            })
            total_score += 0.20

            # Given hard-block triggers (PHI + medical guarantee + certainty claims),
            # the correct decision should be BLOCK (not APPROVE)
            if decision.upper() in ("BLOCK", "REWRITE"):
                checks.append({
                    "name": "decision is BLOCK or REWRITE (not APPROVE for policy-violating draft)",
                    "passed": True,
                    "detail": f"Correct: draft with guaranteed outcomes, PHI, and medical certainty claims resulted in {decision.upper()}"
                })
                total_score += 0.20
            else:
                checks.append({
                    "name": "decision is BLOCK or REWRITE (not APPROVE for policy-violating draft)",
                    "passed": False,
                    "detail": f"APPROVE was returned for a draft containing hard-block triggers (PHI, medical guarantees, certainty claims). Expected BLOCK or REWRITE."
                })
        else:
            checks.append({
                "name": "decision field present and valid enum value",
                "passed": False,
                "detail": f"Could not find a valid decision field (APPROVE/BLOCK/REWRITE) in the output. Got: {str(result_data)[:300]}"
            })

    # -----------------------------------------------------------------------
    # CHECK 4: Board/state artifact written under /workspace/state/
    # -----------------------------------------------------------------------
    state_root = Path(workspace) / "state"
    # Look for any artifact files written by the guard (decision artifacts, JSON, etc.)
    artifact_files = []
    for pattern in ["**/*.json", "**/*.jsonl", "**/*.log", "**/*.artifact"]:
        artifact_files.extend([
            p for p in state_root.rglob(pattern.replace("**/", ""))
            if p.name != ".gitkeep"
        ])
    # More thorough search
    all_state_files = [p for p in state_root.rglob("*") if p.is_file() and p.name != ".gitkeep"]

    if all_state_files:
        checks.append({
            "name": "Board/state artifact written under /workspace/state/",
            "passed": True,
            "detail": f"Found {len(all_state_files)} artifact(s) under state/: {[str(p.relative_to(workspace)) for p in all_state_files[:5]]}"
        })
        total_score += 0.20

        # Bonus: check if the artifact contains a recognizable decision record
        artifact_has_decision = False
        for af in all_state_files:
            try:
                content = af.read_text(errors="replace")
                if any(kw in content.upper() for kw in ["BLOCK", "REWRITE", "APPROVE", "DECISION", "ARTIFACT"]):
                    artifact_has_decision = True
                    break
            except Exception:
                pass

        if artifact_has_decision:
            checks.append({
                "name": "State artifact contains decision record",
                "passed": True,
                "detail": "At least one state artifact references a governance decision."
            })
            total_score += 0.10
        else:
            checks.append({
                "name": "State artifact contains decision record",
                "passed": False,
                "detail": "State artifacts found but none contain recognizable decision keywords."
            })
    else:
        checks.append({
            "name": "Board/state artifact written under /workspace/state/",
            "passed": False,
            "detail": "No artifacts found under /workspace/state/ — the guard's writeDecision/writeArtifact was not invoked or CONSENSUS_STATE_ROOT was not set to /workspace/state/"
        })

    # -----------------------------------------------------------------------
    # CHECK 5: CONSENSUS_STATE_ROOT was configured (infer from artifact presence + env)
    # -----------------------------------------------------------------------
    # Check if run.js or an invocation script was created by agent referencing state config
    run_scripts = list(Path(workspace).rglob("run*.js")) + list(Path(workspace).rglob("invoke*.js")) + \
                  list(Path(workspace).rglob("guard*.js")) + list(Path(workspace).rglob("*.mjs"))
    shell_scripts = list(Path(workspace).rglob("*.sh"))
    ts_scripts = list(Path(workspace).rglob("*.ts"))

    invocation_scripts = run_scripts + shell_scripts + ts_scripts
    state_env_configured = False
    external_agent_mode_used = False

    for script_path in invocation_scripts:
        try:
            content = script_path.read_text(errors="replace")
            if "CONSENSUS_STATE_ROOT" in content or "CONSENSUS_STATE_FILE" in content:
                state_env_configured = True
            if "external_agent" in content or "external_votes" in content:
                external_agent_mode_used = True
        except Exception:
            pass

    # Also check if env was set in any config or result files
    if not state_env_configured:
        for extra in list(Path(workspace).rglob("*.json")) + list(Path(workspace).rglob("*.env")):
            try:
                content = extra.read_text(errors="replace")
                if "CONSENSUS_STATE_ROOT" in content or "CONSENSUS_STATE_FILE" in content:
                    state_env_configured = True
                    break
            except Exception:
                pass

    if state_env_configured:
        checks.append({
            "name": "CONSENSUS_STATE_ROOT/CONSENSUS_STATE_FILE environment configured",
            "passed": True,
            "detail": "Found CONSENSUS_STATE_ROOT or CONSENSUS_STATE_FILE reference in agent-created scripts."
        })
        total_score += 0.05
    else:
        checks.append({
            "name": "CONSENSUS_STATE_ROOT/CONSENSUS_STATE_FILE environment configured",
            "passed": False,
            "detail": "Could not detect environment variable configuration. Agent may not have read the skill requirements."
        })

    # -----------------------------------------------------------------------
    # CHECK 6: external_agent mode used with external_votes
    # -----------------------------------------------------------------------
    if external_agent_mode_used:
        checks.append({
            "name": "external_agent mode with external_votes[] used",
            "passed": True,
            "detail": "Detected external_agent mode or external_votes in agent invocation scripts — correct proprietary pattern."
        })
        total_score += 0.10  # Bonus for using the correct proprietary mode
    else:
        # Also check the result data itself
        result_str = json.dumps(result_data) if result_data else ""
        if "external" in result_str.lower() or "votes" in result_str.lower():
            checks.append({
                "name": "external_agent mode with external_votes[] used",
                "passed": True,
                "detail": "Detected external_votes reference in result data."
            })
            total_score += 0.10
        else:
            checks.append({
                "name": "external_agent mode with external_votes[] used",
                "passed": False,
                "detail": "No evidence of external_agent mode or external_votes[] usage. Agent may have used persona mode instead or skipped vote integration."
            })

    # -----------------------------------------------------------------------
    # Final scoring
    # -----------------------------------------------------------------------
    total_score = min(total_score, 1.0)
    passed = total_score >= 0.55 and any(
        c["passed"] for c in checks if c["name"] == "decision is BLOCK or REWRITE (not APPROVE for policy-violating draft)"
    )

    return {
        "passed": passed,
        "score": round(total_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, indent=2))