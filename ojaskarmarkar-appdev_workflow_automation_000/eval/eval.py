import sys
import json
import os

def evaluate(workspace: str):
    checks = []
    log_file = "/tmp/restate_requests.jsonl"

    # --- Check 1: Was the log file created at all? (did the agent hit any endpoint?) ---
    try:
        if not os.path.exists(log_file):
            checks.append({
                "name": "server_was_called",
                "passed": False,
                "detail": "No requests were recorded. The agent never called the mock server at 127.0.0.1:8080."
            })
            return finalize(checks)
        with open(log_file, "r") as f:
            raw_lines = [line.strip() for line in f if line.strip()]
        if not raw_lines:
            checks.append({
                "name": "server_was_called",
                "passed": False,
                "detail": "Log file exists but is empty. The agent never successfully reached the server."
            })
            return finalize(checks)
        checks.append({
            "name": "server_was_called",
            "passed": True,
            "detail": f"Server received {len(raw_lines)} request(s)."
        })
    except Exception as e:
        checks.append({"name": "server_was_called", "passed": False, "detail": str(e)})
        return finalize(checks)

    # Parse all recorded requests
    entries = []
    for line in raw_lines:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            pass

    # --- Check 2: Correct endpoint path `/AppFactory/buildFeature/send` was used ---
    correct_path = "/AppFactory/buildFeature/send"
    correct_path_entries = [e for e in entries if e.get("path") == correct_path and not e.get("wrong_path")]
    if correct_path_entries:
        checks.append({
            "name": "correct_endpoint_path",
            "passed": True,
            "detail": f"Request(s) hit the correct proprietary endpoint: {correct_path}"
        })
    else:
        wrong_paths = list({e.get("path") for e in entries})
        checks.append({
            "name": "correct_endpoint_path",
            "passed": False,
            "detail": (
                f"No request hit the required endpoint '{correct_path}'. "
                f"Paths actually called: {wrong_paths}. "
                "The agent likely guessed a generic endpoint instead of reading SKILL.md."
            )
        })
        return finalize(checks)

    # Use the first valid correct-path entry for further checks
    entry = correct_path_entries[0]

    # --- Check 3: HTTP method is POST ---
    method_ok = entry.get("method", "").upper() == "POST"
    checks.append({
        "name": "http_method_is_post",
        "passed": method_ok,
        "detail": f"HTTP method was '{entry.get('method')}'. Expected POST." if not method_ok else "HTTP method is correctly POST."
    })

    # --- Check 4: Content-Type is application/json ---
    content_type = entry.get("content_type", "")
    ct_ok = "application/json" in content_type
    checks.append({
        "name": "content_type_json",
        "passed": ct_ok,
        "detail": f"Content-Type was '{content_type}'. Expected 'application/json'." if not ct_ok else "Content-Type correctly set to application/json."
    })

    # --- Check 5: JSON body has required `prompt` key ---
    body = entry.get("body")
    if body is None:
        # Try to parse raw body
        try:
            body = json.loads(entry.get("raw_body", ""))
        except Exception:
            body = None

    has_prompt_key = isinstance(body, dict) and "prompt" in body
    checks.append({
        "name": "json_body_has_prompt_key",
        "passed": has_prompt_key,
        "detail": (
            f"JSON body was: {json.dumps(body)}. Missing required 'prompt' key."
            if not has_prompt_key
            else f"JSON body correctly contains 'prompt' key."
        )
    })

    # --- Check 6: The `prompt` value is non-empty and meaningfully describes the medication reminder feature ---
    if has_prompt_key:
        prompt_value = body["prompt"]
        is_non_empty = isinstance(prompt_value, str) and len(prompt_value.strip()) > 10
        # Check that it relates to the feature request (medication reminder / the task)
        keywords = ["medication", "reminder", "screen", "dose", "patient", "medic", "drug", "pill", "refill"]
        lowered = prompt_value.lower()
        is_relevant = any(kw in lowered for kw in keywords)
        prompt_ok = is_non_empty and is_relevant
        checks.append({
            "name": "prompt_value_describes_feature",
            "passed": prompt_ok,
            "detail": (
                f"prompt value: '{prompt_value[:300]}'. "
                + ("Value is too short or empty." if not is_non_empty else "")
                + (" Value does not appear to describe the medication reminder feature." if not is_relevant else "")
                if not prompt_ok
                else f"Prompt value is meaningful and relevant: '{prompt_value[:200]}...'"
            )
        })
    else:
        checks.append({
            "name": "prompt_value_describes_feature",
            "passed": False,
            "detail": "Cannot evaluate prompt value because 'prompt' key is missing from the body."
        })

    return finalize(checks)


def finalize(checks):
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    all_passed = all(c["passed"] for c in checks)
    return {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))