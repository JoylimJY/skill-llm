import sys
import json
from pathlib import Path


def load_json_file(path: Path):
    with open(path) as f:
        return json.load(f)


def run_eval(workspace: str):
    checks = []

    # ---------- 1. Intermediate: call payload was built ----------
    payload_paths = list(Path("/tmp").glob("call-payload.json")) + \
                    list(Path(workspace).rglob("call-payload.json"))
    payload_exists = len(payload_paths) > 0
    payload_data = None
    if payload_exists:
        try:
            payload_data = load_json_file(payload_paths[0])
        except Exception as e:
            payload_exists = False
    checks.append({
        "name": "call_payload_file_exists",
        "passed": payload_exists,
        "detail": f"call-payload.json found at {payload_paths[0]}" if payload_exists else "call-payload.json not found in /tmp or workspace"
    })

    # ---------- 2. Payload has required normalized fields ----------
    payload_fields_ok = False
    payload_field_detail = "payload file missing or unreadable"
    if payload_data:
        required_keys = {"job_id", "client_name", "listing_address", "office_phone",
                         "preferred_windows_text", "timezone", "call_prompt", "guardrails"}
        missing = required_keys - set(payload_data.keys())
        payload_fields_ok = len(missing) == 0
        payload_field_detail = f"missing keys: {missing}" if missing else "all required keys present"
    checks.append({
        "name": "call_payload_has_required_fields",
        "passed": payload_fields_ok,
        "detail": payload_field_detail
    })

    # ---------- 3. Payload job_id matches input ----------
    payload_job_id_ok = False
    if payload_data:
        payload_job_id_ok = payload_data.get("job_id") == "JOB-2024-0342"
    checks.append({
        "name": "payload_job_id_correct",
        "passed": payload_job_id_ok,
        "detail": f"job_id = {payload_data.get('job_id') if payload_data else 'N/A'}"
    })

    # ---------- 4. Guardrails populated correctly ----------
    guardrails_ok = False
    guardrails_detail = "guardrails missing"
    if payload_data and "guardrails" in payload_data:
        g = payload_data["guardrails"]
        guardrails_ok = (
            g.get("disclose_ai") == True and
            g.get("confirm_slot_before_hangup") == True and
            g.get("if_cannot_confirm") == "pending_callback"
        )
        guardrails_detail = str(g)
    checks.append({
        "name": "payload_guardrails_correct",
        "passed": guardrails_ok,
        "detail": guardrails_detail
    })

    # ---------- 5. Intermediate: call result produced ----------
    result_paths = list(Path("/tmp").glob("call-result.json")) + \
                   list(Path(workspace).rglob("call-result.json"))
    result_exists = len(result_paths) > 0
    result_data = None
    if result_exists:
        try:
            result_data = load_json_file(result_paths[0])
        except Exception:
            result_exists = False
    checks.append({
        "name": "call_result_file_exists",
        "passed": result_exists,
        "detail": f"call-result.json found at {result_paths[0]}" if result_exists else "call-result.json not found"
    })

    # ---------- 6. Call was done in dry-run mode (not live) ----------
    dry_run_used = False
    dry_run_detail = "call-result.json missing"
    if result_data:
        dry_run_used = result_data.get("mode") == "dry_run"
        dry_run_detail = f"mode field = '{result_data.get('mode')}'"
    checks.append({
        "name": "dry_run_mode_used",
        "passed": dry_run_used,
        "detail": dry_run_detail
    })

    # ---------- 7. Final outcome file exists ----------
    outcome_paths = list(Path("/tmp").glob("booking-outcome.json")) + \
                    list(Path(workspace).rglob("booking-outcome.json"))
    outcome_exists = len(outcome_paths) > 0
    outcome_data = None
    if outcome_exists:
        try:
            outcome_data = load_json_file(outcome_paths[0])
        except Exception:
            outcome_exists = False
    checks.append({
        "name": "booking_outcome_file_exists",
        "passed": outcome_exists,
        "detail": f"booking-outcome.json found at {outcome_paths[0]}" if outcome_exists else "booking-outcome.json not found"
    })

    # ---------- 8. Booking status is "confirmed" ----------
    status_ok = False
    status_detail = "outcome file missing"
    if outcome_data:
        status_ok = outcome_data.get("booking_status") == "confirmed"
        status_detail = f"booking_status = '{outcome_data.get('booking_status')}'"
    checks.append({
        "name": "booking_status_is_confirmed",
        "passed": status_ok,
        "detail": status_detail
    })

    # ---------- 9. Outcome has confirmed_slot populated ----------
    slot_ok = False
    slot_detail = "outcome file missing"
    if outcome_data:
        slot_ok = bool(outcome_data.get("confirmed_slot"))
        slot_detail = f"confirmed_slot = '{outcome_data.get('confirmed_slot')}'"
    checks.append({
        "name": "outcome_has_confirmed_slot",
        "passed": slot_ok,
        "detail": slot_detail
    })

    # ---------- 10. Outcome job_id matches input ----------
    outcome_job_id_ok = False
    if outcome_data:
        outcome_job_id_ok = outcome_data.get("job_id") == "JOB-2024-0342"
    checks.append({
        "name": "outcome_job_id_correct",
        "passed": outcome_job_id_ok,
        "detail": f"job_id = {outcome_data.get('job_id') if outcome_data else 'N/A'}"
    })

    # ---------- 11. Outcome call_mode reflects dry_run end-to-end ----------
    outcome_mode_ok = False
    if outcome_data:
        outcome_mode_ok = outcome_data.get("call_mode") == "dry_run"
    checks.append({
        "name": "outcome_call_mode_is_dry_run",
        "passed": outcome_mode_ok,
        "detail": f"call_mode = '{outcome_data.get('call_mode') if outcome_data else 'N/A'}'"
    })

    # ---------- 12. call_prompt in payload mentions AI disclosure ----------
    prompt_discloses_ai = False
    prompt_detail = "payload missing"
    if payload_data and "call_prompt" in payload_data:
        cp = payload_data["call_prompt"].lower()
        prompt_discloses_ai = "ai" in cp or "artificial intelligence" in cp or "automated" in cp or "assistant" in cp
        prompt_detail = f"call_prompt starts with: '{payload_data['call_prompt'][:80]}...'"
    checks.append({
        "name": "call_prompt_discloses_ai",
        "passed": prompt_discloses_ai,
        "detail": prompt_detail
    })

    # ---------- Score ----------
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)
    overall_passed = passed_count >= 10  # require at least 10/12

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace)