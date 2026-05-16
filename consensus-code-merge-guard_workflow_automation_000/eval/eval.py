import sys
import json
import os
import pathlib
import traceback

def evaluate(workspace_dir: str):
    workspace = pathlib.Path(workspace_dir)
    checks = []

    # ── Helper ────────────────────────────────────────────────────────────
    def check(name, passed, detail=""):
        checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})
        return bool(passed)

    # ── 1. The tool was invoked: look for any decision output JSON ─────────
    # The agent must have produced a decision artifact somewhere under the
    # configured CONSENSUS_STATE_ROOT or as stdout-captured output.
    # We search broadly for any JSON file that contains a decision field
    # with one of the canonical values.

    VALID_DECISIONS = {"MERGE", "BLOCK", "REVISE"}
    decision_files = []

    try:
        for candidate in workspace.rglob("*.json"):
            try:
                data = json.loads(candidate.read_text())
                # Accept both top-level "decision" and nested "decision.decision"
                d = None
                if isinstance(data, dict):
                    d = data.get("decision")
                    if isinstance(d, dict):
                        d = d.get("decision") or d.get("outcome") or d.get("status")
                if d and str(d).upper() in VALID_DECISIONS:
                    decision_files.append((candidate, data, str(d).upper()))
            except Exception:
                pass
    except Exception as e:
        check("decision_file_found", False, f"Error scanning workspace: {e}")
    
    if decision_files:
        check("decision_file_found", True,
              f"Found {len(decision_files)} file(s) with valid decision: "
              + ", ".join(str(f[0].relative_to(workspace)) for f in decision_files))
    else:
        check("decision_file_found", False,
              "No JSON file with a MERGE/BLOCK/REVISE decision found anywhere in workspace.")

    # ── 2. Decision value is one of the canonical three ───────────────────
    if decision_files:
        all_valid = all(d[2] in VALID_DECISIONS for d in decision_files)
        values = [d[2] for d in decision_files]
        check("decision_value_canonical", all_valid,
              f"Decision values found: {values}. All valid: {all_valid}")
    else:
        check("decision_value_canonical", False,
              "No decision file to evaluate.")

    # ── 3. PR reference (PR-2041) appears in at least one artifact ────────
    pr_referenced = False
    pr_detail = "PR-2041 not found in any artifact"
    try:
        for candidate in workspace.rglob("*.json"):
            try:
                raw = candidate.read_text()
                if "PR-2041" in raw or "pr_2041" in raw.lower() or "2041" in raw:
                    pr_referenced = True
                    pr_detail = f"PR reference found in {candidate.relative_to(workspace)}"
                    break
            except Exception:
                pass
    except Exception as e:
        pr_detail = f"Scan error: {e}"
    check("pr_reference_present", pr_referenced, pr_detail)

    # ── 4. external_agent mode was used (external_votes present) ──────────
    # The input JSON passed to the tool must contain external_votes[]
    # OR we find evidence of it in any written artifact
    external_agent_used = False
    ext_detail = "No evidence of external_agent mode (external_votes[]) found"
    try:
        for candidate in workspace.rglob("*.json"):
            try:
                raw = candidate.read_text()
                data = json.loads(raw)
                # Check if external_votes key exists anywhere in any json
                if "external_votes" in raw or "external_agent" in raw:
                    external_agent_used = True
                    ext_detail = f"external_agent mode evidence in {candidate.relative_to(workspace)}"
                    break
                # Also check nested
                if isinstance(data, dict):
                    if data.get("mode") == "external_agent":
                        external_agent_used = True
                        ext_detail = f"mode=external_agent in {candidate.relative_to(workspace)}"
                        break
            except Exception:
                pass
    except Exception as e:
        ext_detail = f"Scan error: {e}"
    check("external_agent_mode_used", external_agent_used, ext_detail)

    # ── 5. Board state artifacts written (CONSENSUS_STATE_ROOT used) ───────
    # Look for any new JSON files under board-state/ OR under any path
    # that looks like a state/decisions/artifacts directory
    board_artifact_written = False
    board_detail = "No board-state artifacts found"
    try:
        board_root = workspace / "board-state"
        if board_root.exists():
            artifact_files = list(board_root.rglob("*.json"))
            if artifact_files:
                board_artifact_written = True
                board_detail = (f"Found {len(artifact_files)} artifact(s) in board-state/: "
                                + ", ".join(str(f.relative_to(workspace)) for f in artifact_files[:3]))
        if not board_artifact_written:
            # Also accept any directory named "decisions", "artifacts", "state"
            for candidate_dir in ["decisions", "artifacts", "state", "audit"]:
                for d in workspace.rglob(candidate_dir):
                    if d.is_dir():
                        files = list(d.rglob("*.json"))
                        if files:
                            board_artifact_written = True
                            board_detail = (f"Found {len(files)} artifact(s) under {d.relative_to(workspace)}/: "
                                            + ", ".join(str(f.relative_to(workspace)) for f in files[:3]))
                            break
                if board_artifact_written:
                    break
    except Exception as e:
        board_detail = f"Error scanning board-state: {e}"
    check("board_state_artifacts_written", board_artifact_written, board_detail)

    # ── 6. CONSENSUS_STATE_ROOT env var was configured ─────────────────────
    # Check if there's any shell script, .env file, or invocation script
    # that sets CONSENSUS_STATE_ROOT
    env_configured = False
    env_detail = "CONSENSUS_STATE_ROOT not found in any script/config"
    try:
        patterns = ["*.sh", "*.env", "*.bash", "Makefile", "*.ts", "*.js", "*.mjs"]
        search_targets = []
        for pat in patterns:
            search_targets.extend(workspace.rglob(pat))
        # Also check plain text files
        for candidate in search_targets:
            try:
                raw = candidate.read_text(errors="ignore")
                if "CONSENSUS_STATE_ROOT" in raw:
                    env_configured = True
                    env_detail = f"CONSENSUS_STATE_ROOT found in {candidate.relative_to(workspace)}"
                    break
            except Exception:
                pass
        # Also check if env was set in process (via .env or exports in any file)
        if not env_configured:
            for candidate in workspace.rglob("*"):
                if candidate.is_file() and candidate.suffix in ("", ".txt", ".cfg", ".conf", ".env"):
                    try:
                        raw = candidate.read_text(errors="ignore")
                        if "CONSENSUS_STATE_ROOT" in raw:
                            env_configured = True
                            env_detail = f"CONSENSUS_STATE_ROOT in {candidate.relative_to(workspace)}"
                            break
                    except Exception:
                        pass
    except Exception as e:
        env_detail = f"Scan error: {e}"
    check("consensus_env_configured", env_configured, env_detail)

    # ── 7. Input JSON conforms to tool schema (has required signal fields) ─
    # The input used must have test/security/reliability signals
    input_schema_ok = False
    input_detail = "No properly structured tool input JSON found"
    try:
        required_signals = ["security", "test"]
        for candidate in workspace.rglob("*.json"):
            try:
                raw = candidate.read_text()
                if any(sig in raw.lower() for sig in required_signals):
                    data = json.loads(raw)
                    # Must NOT be the raw distractor file (which has _note key)
                    if isinstance(data, dict) and "_note" not in data:
                        if any(sig in raw.lower() for sig in required_signals):
                            input_schema_ok = True
                            input_detail = f"Structured input with signals found in {candidate.relative_to(workspace)}"
                            break
            except Exception:
                pass
    except Exception as e:
        input_detail = f"Scan error: {e}"
    check("input_schema_has_signals", input_schema_ok, input_detail)

    # ── Scoring ───────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 3)

    # Overall pass: must hit the core checks
    core_checks = ["decision_file_found", "decision_value_canonical",
                   "board_state_artifacts_written", "external_agent_mode_used"]
    core_passed = all(c["passed"] for c in checks if c["name"] in core_checks)

    result = {
        "passed": core_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    ws = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(ws)