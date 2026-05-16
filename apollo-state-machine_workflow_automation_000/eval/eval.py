import sys
import json
import ast
import importlib.util
import traceback
from pathlib import Path

def load_module_from_path(path):
    spec = importlib.util.spec_from_file_location("coordinator", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def run_checks(workspace):
    checks = []
    passed_total = True

    # -----------------------------------------------------------------------
    # FIND coordinator.py
    # -----------------------------------------------------------------------
    candidates = list(Path(workspace).rglob("coordinator.py"))
    # Exclude legacy
    candidates = [p for p in candidates if "legacy" not in str(p)]
    
    if not candidates:
        checks.append({"name": "coordinator.py exists", "passed": False,
                        "detail": "No coordinator.py found outside legacy/"})
        return False, 0.0, checks

    coordinator_path = candidates[0]
    checks.append({"name": "coordinator.py exists", "passed": True,
                   "detail": str(coordinator_path)})

    # -----------------------------------------------------------------------
    # READ SOURCE FOR STATIC ANALYSIS
    # -----------------------------------------------------------------------
    try:
        source = coordinator_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "source readable", "passed": False, "detail": str(e)})
        return False, 0.0, checks

    # -----------------------------------------------------------------------
    # CHECK 1: All required state names present as strings in source
    # -----------------------------------------------------------------------
    required_states = [
        "queued",
        "awaiting-basic",
        "awaiting-response",
        "awaiting-tool-calls",
        "interrupted",
        "idle",
    ]
    missing_states = [s for s in required_states if s not in source]
    state_check = len(missing_states) == 0
    checks.append({
        "name": "all required state names defined",
        "passed": state_check,
        "detail": f"Missing states: {missing_states}" if missing_states else "All states found"
    })
    if not state_check:
        passed_total = False

    # -----------------------------------------------------------------------
    # CHECK 2: while loop present (the core state machine loop)
    # -----------------------------------------------------------------------
    has_while = "while" in source
    checks.append({
        "name": "while loop present",
        "passed": has_while,
        "detail": "while loop found" if has_while else "No while loop in source"
    })
    if not has_while:
        passed_total = False

    # -----------------------------------------------------------------------
    # CHECK 3: interrupted state appears BEFORE queued in interrupt flow
    # (interrupted must be set before queued in the transition)
    # -----------------------------------------------------------------------
    interrupted_idx = source.find('"interrupted"') if '"interrupted"' in source else source.find("'interrupted'")
    queued_after_interrupted = False
    if interrupted_idx != -1:
        # Find the next occurrence of "queued" after "interrupted"
        after_interrupted = source[interrupted_idx:]
        queued_idx_relative = after_interrupted.find('"queued"') if '"queued"' in after_interrupted else after_interrupted.find("'queued'")
        if queued_idx_relative != -1:
            queued_after_interrupted = True
    
    checks.append({
        "name": "interrupted transitions to queued (correct interrupt flow)",
        "passed": queued_after_interrupted,
        "detail": "interrupted → queued transition found" if queued_after_interrupted else 
                  "interrupted state must come before queued in the interrupt handling flow"
    })
    if not queued_after_interrupted:
        passed_total = False

    # -----------------------------------------------------------------------
    # CHECK 4: enqueueUserMessage (or enqueue_user_message) called in source
    # -----------------------------------------------------------------------
    has_enqueue = ("enqueueUserMessage" in source or 
                   "enqueue_user_message" in source or
                   "enqueue_message" in source)
    checks.append({
        "name": "enqueueUserMessage called during interrupt handling",
        "passed": has_enqueue,
        "detail": "enqueue function found" if has_enqueue else 
                  "enqueueUserMessage() or equivalent must be called during interrupt flow"
    })
    if not has_enqueue:
        passed_total = False

    # -----------------------------------------------------------------------
    # CHECK 5: awaiting-tool-calls transitions back to awaiting-basic
    # (not to awaiting-response)
    # -----------------------------------------------------------------------
    tool_calls_idx = source.find("awaiting-tool-calls")
    transitions_to_basic = False
    if tool_calls_idx != -1:
        # Look for awaiting-basic after awaiting-tool-calls context
        # We need to confirm that in the block handling awaiting-tool-calls,
        # the next state is awaiting-basic
        segment_after = source[tool_calls_idx:]
        # Check within a reasonable window (500 chars after first mention of awaiting-tool-calls)
        window = segment_after[:600]
        if "awaiting-basic" in window:
            transitions_to_basic = True
    
    checks.append({
        "name": "awaiting-tool-calls transitions to awaiting-basic",
        "passed": transitions_to_basic,
        "detail": "Correct: tool-calls → basic found" if transitions_to_basic else 
                  "awaiting-tool-calls must transition back to awaiting-basic, not awaiting-response"
    })
    if not transitions_to_basic:
        passed_total = False

    # -----------------------------------------------------------------------
    # CHECK 6: idle is the terminal/completion state (not "done"/"complete"/"finished")
    # -----------------------------------------------------------------------
    has_idle_terminal = "idle" in source
    # Also check that "done" or "complete" is NOT used as THE terminal state
    # (idle must be present; done/complete alone is wrong)
    bad_terminal = False
    for bad in ['"done"', "'done'", '"complete"', "'complete'", '"finished"', "'finished'"]:
        if bad in source:
            bad_terminal = True
            break
    
    idle_terminal_check = has_idle_terminal
    checks.append({
        "name": "idle is terminal state",
        "passed": idle_terminal_check,
        "detail": "'idle' state found as terminal" if idle_terminal_check else 
                  "Task completion must use 'idle' state, not 'done'/'complete'/'finished'"
    })
    if not idle_terminal_check:
        passed_total = False

    # -----------------------------------------------------------------------
    # CHECK 7: awaiting-response transitions to awaiting-tool-calls on tool calls
    # -----------------------------------------------------------------------
    response_idx = source.find("awaiting-response")
    has_response_to_tool_calls = False
    if response_idx != -1:
        segment = source[response_idx:]
        # within a window after awaiting-response, awaiting-tool-calls should appear
        window = segment[:500]
        if "awaiting-tool-calls" in window:
            has_response_to_tool_calls = True

    checks.append({
        "name": "awaiting-response can transition to awaiting-tool-calls",
        "passed": has_response_to_tool_calls,
        "detail": "awaiting-response → awaiting-tool-calls found" if has_response_to_tool_calls else
                  "awaiting-response must transition to awaiting-tool-calls when tool calls exist"
    })
    if not has_response_to_tool_calls:
        passed_total = False

    # -----------------------------------------------------------------------
    # CHECK 8: Try to dynamically load and run a basic simulation
    # -----------------------------------------------------------------------
    try:
        mod = load_module_from_path(str(coordinator_path))
        
        # Look for a class or function that implements the state machine
        coordinator_class = None
        for attr_name in dir(mod):
            attr = getattr(mod, attr_name)
            if isinstance(attr, type) and attr_name not in ("object",):
                coordinator_class = attr
                break
        
        if coordinator_class is None:
            checks.append({
                "name": "coordinator class instantiable",
                "passed": False,
                "detail": "No class found in coordinator.py"
            })
            passed_total = False
        else:
            instance = coordinator_class()
            # Check that instance has a state attribute
            has_state_attr = hasattr(instance, "state") or hasattr(instance, "status") or hasattr(instance, "current_state")
            checks.append({
                "name": "coordinator instance has state attribute",
                "passed": has_state_attr,
                "detail": f"State attribute found on {coordinator_class.__name__}" if has_state_attr else 
                          "Coordinator instance must expose a state/status attribute"
            })
            if not has_state_attr:
                passed_total = False
    except Exception as e:
        tb = traceback.format_exc()
        checks.append({
            "name": "coordinator module loads without error",
            "passed": False,
            "detail": f"Import/instantiation error: {str(e)}\n{tb[:300]}"
        })
        passed_total = False

    # -----------------------------------------------------------------------
    # SCORE
    # -----------------------------------------------------------------------
    num_passed = sum(1 for c in checks if c["passed"])
    score = round(num_passed / len(checks), 3)
    
    # Must pass core checks to be considered overall passing
    core_checks = [
        "all required state names defined",
        "while loop present", 
        "interrupted transitions to queued (correct interrupt flow)",
        "awaiting-tool-calls transitions to awaiting-basic",
        "idle is terminal state",
    ]
    core_passed = all(c["passed"] for c in checks if c["name"] in core_checks)
    
    return core_passed and (score >= 0.75), score, checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    try:
        passed, score, checks = run_checks(workspace)
    except Exception as e:
        tb = traceback.format_exc()
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_script_error", "passed": False, "detail": f"{str(e)}\n{tb[:500]}"}]
        }
        print(json.dumps(result))
        return

    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()