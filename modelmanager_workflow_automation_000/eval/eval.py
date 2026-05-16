import sys
import json
from pathlib import Path

def load_json(path: Path):
    return json.loads(path.read_text())

def run_checks(workspace: str):
    HOME = Path.home()
    session_path = HOME / ".qclaw/agents/main/agent/models.json"
    global_path  = HOME / ".qclaw/openclaw.json"

    checks = []
    all_passed = True

    # ── Check 1: Session file exists ─────────────────────────────────────────
    try:
        session = load_json(session_path)
        checks.append({
            "name": "session_file_readable",
            "passed": True,
            "detail": f"Session file exists and is valid JSON at {session_path}"
        })
    except Exception as e:
        checks.append({
            "name": "session_file_readable",
            "passed": False,
            "detail": f"Could not read session file: {e}"
        })
        all_passed = False
        session = {}

    # ── Check 2: Global config file exists ───────────────────────────────────
    try:
        glob = load_json(global_path)
        checks.append({
            "name": "global_config_readable",
            "passed": True,
            "detail": f"Global config exists and is valid JSON at {global_path}"
        })
    except Exception as e:
        checks.append({
            "name": "global_config_readable",
            "passed": False,
            "detail": f"Could not read global config: {e}"
        })
        all_passed = False
        glob = {}

    # ── Check 3: Primary model switched to ollama/nemotron-3-super:cloud ─────
    TARGET_MODEL = "ollama/nemotron-3-super:cloud"
    try:
        session_model = session.get("current_model", "")
        passed = (session_model == TARGET_MODEL)
        checks.append({
            "name": "primary_model_set_correctly",
            "passed": passed,
            "detail": (
                f"session current_model='{session_model}' "
                f"(expected '{TARGET_MODEL}')"
            )
        })
        if not passed:
            all_passed = False
    except Exception as e:
        checks.append({
            "name": "primary_model_set_correctly",
            "passed": False,
            "detail": f"Exception checking current_model: {e}"
        })
        all_passed = False

    # ── Check 4: Global default_model also updated ───────────────────────────
    try:
        glob_model = glob.get("default_model", "")
        passed = (glob_model == TARGET_MODEL)
        checks.append({
            "name": "global_default_model_updated",
            "passed": passed,
            "detail": (
                f"global default_model='{glob_model}' "
                f"(expected '{TARGET_MODEL}')"
            )
        })
        if not passed:
            all_passed = False
    except Exception as e:
        checks.append({
            "name": "global_default_model_updated",
            "passed": False,
            "detail": f"Exception checking global default_model: {e}"
        })
        all_passed = False

    # ── Check 5: phi-3:mini removed from fallbacks ────────────────────────────
    REMOVED_FALLBACK = "ollama/phi-3:mini"
    try:
        session_fallbacks = session.get("fallbacks", [])
        passed = (REMOVED_FALLBACK not in session_fallbacks)
        checks.append({
            "name": "stale_fallback_removed",
            "passed": passed,
            "detail": (
                f"'{REMOVED_FALLBACK}' should NOT be in fallbacks. "
                f"Current fallbacks: {session_fallbacks}"
            )
        })
        if not passed:
            all_passed = False
    except Exception as e:
        checks.append({
            "name": "stale_fallback_removed",
            "passed": False,
            "detail": f"Exception checking fallback removal: {e}"
        })
        all_passed = False

    # ── Check 6: mistral:7b added as new fallback ────────────────────────────
    NEW_FALLBACK = "ollama/mistral:7b"
    try:
        session_fallbacks = session.get("fallbacks", [])
        passed = (NEW_FALLBACK in session_fallbacks)
        checks.append({
            "name": "new_fallback_added",
            "passed": passed,
            "detail": (
                f"'{NEW_FALLBACK}' should be in fallbacks. "
                f"Current fallbacks: {session_fallbacks}"
            )
        })
        if not passed:
            all_passed = False
    except Exception as e:
        checks.append({
            "name": "new_fallback_added",
            "passed": False,
            "detail": f"Exception checking fallback addition: {e}"
        })
        all_passed = False

    # ── Check 7: ministral-3:14b still present (not accidentally removed) ────
    KEPT_FALLBACK = "ollama/ministral-3:14b"
    try:
        session_fallbacks = session.get("fallbacks", [])
        passed = (KEPT_FALLBACK in session_fallbacks)
        checks.append({
            "name": "existing_fallback_preserved",
            "passed": passed,
            "detail": (
                f"'{KEPT_FALLBACK}' should STILL be in fallbacks. "
                f"Current fallbacks: {session_fallbacks}"
            )
        })
        if not passed:
            all_passed = False
    except Exception as e:
        checks.append({
            "name": "existing_fallback_preserved",
            "passed": False,
            "detail": f"Exception checking preserved fallback: {e}"
        })
        all_passed = False

    # ── Check 8: Global fallbacks consistent with session ────────────────────
    try:
        glob_fallbacks   = set(glob.get("fallbacks", []))
        session_fallbacks_set = set(session.get("fallbacks", []))
        passed = (glob_fallbacks == session_fallbacks_set)
        checks.append({
            "name": "global_and_session_fallbacks_consistent",
            "passed": passed,
            "detail": (
                f"global fallbacks={sorted(glob_fallbacks)}, "
                f"session fallbacks={sorted(session_fallbacks_set)}"
            )
        })
        if not passed:
            all_passed = False
    except Exception as e:
        checks.append({
            "name": "global_and_session_fallbacks_consistent",
            "passed": False,
            "detail": f"Exception checking consistency: {e}"
        })
        all_passed = False

    # ── Score ─────────────────────────────────────────────────────────────────
    num_passed = sum(1 for c in checks if c["passed"])
    score = round(num_passed / len(checks), 4) if checks else 0.0

    return {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, indent=2))