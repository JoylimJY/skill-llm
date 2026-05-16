#!/usr/bin/env python3
import sys
import json
import re
from pathlib import Path

def load_state(workspace):
    state_path = Path(workspace) / ".openclaw_state" / "state.json"
    if not state_path.exists():
        return None, f"State file missing: {state_path}"
    try:
        with open(state_path) as f:
            return json.load(f), None
    except Exception as e:
        return None, f"Failed to parse state.json: {e}"

def load_command_log(workspace):
    log_path = Path(workspace) / ".openclaw_state" / "command_log.jsonl"
    if not log_path.exists():
        return [], "Command log missing"
    lines = log_path.read_text().strip().splitlines()
    cmds = []
    for line in lines:
        if line.strip():
            try:
                cmds.append(json.loads(line))
            except Exception:
                pass
    return cmds, None

def evaluate(workspace):
    checks = []
    overall_passed = True

    # ── Load state ────────────────────────────────────────────────────────────
    state, err = load_state(workspace)
    if state is None:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "state_file_readable", "passed": False, "detail": err}]
        }

    checks.append({"name": "state_file_readable", "passed": True, "detail": "state.json loaded successfully"})

    # ── Check 1: copilot-bridge/github-copilot is the default model ──────────
    default_model = state.get("default_model", "")
    correct_default = default_model == "copilot-bridge/github-copilot"
    checks.append({
        "name": "copilot_set_as_default_model",
        "passed": correct_default,
        "detail": (
            f"default_model is '{default_model}' — correct: copilot-bridge/github-copilot"
            if correct_default
            else f"default_model is '{default_model}', expected 'copilot-bridge/github-copilot'"
        )
    })
    if not correct_default:
        overall_passed = False

    # ── Check 2: copilot-auto alias exists and points to correct model ────────
    aliases = state.get("aliases", {})
    alias_val = aliases.get("copilot-auto", None)
    alias_correct = alias_val == "copilot-bridge/github-copilot"
    checks.append({
        "name": "copilot_auto_alias_created",
        "passed": alias_correct,
        "detail": (
            f"copilot-auto -> {alias_val} ✓"
            if alias_correct
            else f"copilot-auto alias is {'missing' if alias_val is None else f'wrong: {alias_val}'}; "
                 f"expected -> copilot-bridge/github-copilot"
        )
    })
    if not alias_correct:
        overall_passed = False

    # ── Check 3: Agent ran diagnostic commands before making changes ──────────
    log_cmds, log_err = load_command_log(workspace)

    # Reconstruct full command invocations (cmd + args string) in order
    all_invocations = []
    for entry in log_cmds:
        cmd = entry.get("cmd", "")
        args = entry.get("args", "")
        all_invocations.append((cmd, args))

    # Check that some form of status/diagnostic was run
    diagnostic_ran = any(
        cmd in ("copilot-status.sh", "copilot-quickstart.sh") or
        (cmd == "openclaw" and "status" in args)
        for cmd, args in all_invocations
    )
    checks.append({
        "name": "diagnostic_ran_before_activation",
        "passed": diagnostic_ran,
        "detail": (
            "Agent ran a diagnostic/status command as required by the skill workflow"
            if diagnostic_ran
            else "No diagnostic command detected in log (copilot-status.sh, copilot-quickstart.sh --probe, or openclaw models status)"
        )
    })
    if not diagnostic_ran:
        overall_passed = False

    # ── Check 4: Activation used the correct skill script path (not ad-hoc) ──
    # The agent should have used copilot-activate.sh, copilot-quickstart.sh --activate,
    # OR openclaw models set with the correct identifier
    activation_correct = False
    activation_detail = ""

    # Check for script-based activation
    script_activation = any(
        cmd in ("copilot-activate.sh", "copilot-quickstart.sh") and
        ("activate" in args or cmd == "copilot-activate.sh")
        for cmd, args in all_invocations
    )

    # Check for direct openclaw models set with correct target
    cli_activation = any(
        cmd == "openclaw" and "set" in args and
        ("copilot-bridge/github-copilot" in args or "copilot-auto" in args)
        for cmd, args in all_invocations
    )

    activation_correct = script_activation or cli_activation
    if script_activation:
        activation_detail = "Agent used the correct skill script for activation (copilot-activate.sh or quickstart --activate)"
    elif cli_activation:
        activation_detail = "Agent used openclaw models set with correct model/alias identifier"
    else:
        activation_detail = (
            "No valid activation command found. Expected: copilot-activate.sh, "
            "copilot-quickstart.sh --activate, or 'openclaw models set copilot-bridge/github-copilot' / 'openclaw models set copilot-auto'"
        )

    checks.append({
        "name": "activation_used_correct_method",
        "passed": activation_correct,
        "detail": activation_detail
    })
    if not activation_correct:
        overall_passed = False

    # ── Check 5: Models list was inspected (agent verified model existence) ───
    models_listed = any(
        (cmd == "openclaw" and "list" in args) or
        cmd in ("copilot-status.sh", "copilot-quickstart.sh")
        for cmd, args in all_invocations
    )
    checks.append({
        "name": "model_existence_verified",
        "passed": models_listed,
        "detail": (
            "Agent verified model existence via openclaw models list or status script"
            if models_listed
            else "Agent never verified model existence before acting"
        )
    })
    # This is a soft check — doesn't fail overall but reduces score
    if not models_listed:
        overall_passed = False

    # ── Check 6: The original model list was not corrupted ───────────────────
    expected_models = {"copilot-bridge/github-copilot", "local/ollama-llama3", "openai/gpt-4o"}
    actual_models = set(state.get("models", []))
    models_intact = expected_models.issubset(actual_models)
    checks.append({
        "name": "existing_models_not_corrupted",
        "passed": models_intact,
        "detail": (
            "All original models still present"
            if models_intact
            else f"Missing models: {expected_models - actual_models}"
        )
    })
    if not models_intact:
        overall_passed = False

    # ── Scoring ───────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "invocation", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)

    workspace_path = sys.argv[1]
    result = evaluate(workspace_path)
    print(json.dumps(result, indent=2))