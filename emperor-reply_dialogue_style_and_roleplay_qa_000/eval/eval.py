import sys
import json
import re
from pathlib import Path

def load_response_log(workspace):
    """Find and load the response_log.json file."""
    candidates = list(Path(workspace).rglob("response_log.json"))
    if not candidates:
        return None, "response_log.json not found anywhere in workspace"
    # Prefer root-level
    candidates.sort(key=lambda p: len(p.parts))
    return candidates[0], None

def check_contains_any(text, words):
    """Return list of forbidden words found in text."""
    found = []
    for w in words:
        if w in text:
            found.append(w)
    return found

def run_eval(workspace):
    checks = []
    
    # --- Load response_log.json ---
    log_path, err = load_response_log(workspace)
    if err:
        checks.append({"name": "file_exists", "passed": False, "detail": err})
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}
    
    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {log_path}"})
    
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        checks.append({"name": "valid_json", "passed": False, "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": 0.1, "checks": checks}
    
    checks.append({"name": "valid_json", "passed": True, "detail": "response_log.json parsed successfully"})
    
    # Build lookup by turn_id
    responses = {}
    try:
        for item in data:
            responses[item["turn_id"]] = item["response"]
    except Exception as e:
        checks.append({"name": "correct_structure", "passed": False, "detail": f"Structure error: {e}"})
        return {"passed": False, "score": 0.15, "checks": checks}
    
    has_all_turns = all(i in responses for i in range(1, 6))
    checks.append({
        "name": "all_five_turns_present",
        "passed": has_all_turns,
        "detail": f"Found turn IDs: {sorted(responses.keys())}"
    })
    
    if not has_all_turns:
        return {"passed": False, "score": 0.2, "checks": checks}
    
    # --- FORBIDDEN WORDS (apply to ALL turns) ---
    FORBIDDEN_WORDS = [
        "您", "你", "老板", "主人", "亲", "宝宝", "哈哈", "收到", "请问",
        "这边建议", "奴才", "老奴", "平身", "退下", "宣"
    ]
    # Note: "你" is forbidden; "陛下" and "臣" contain no "你" as substring in standard usage,
    # but we must be careful: "陛下您" would contain "您". We check exact forbidden terms.
    
    all_text = " ".join(responses.values())
    found_forbidden = check_contains_any(all_text, FORBIDDEN_WORDS)
    checks.append({
        "name": "no_forbidden_words_globally",
        "passed": len(found_forbidden) == 0,
        "detail": f"Forbidden words found: {found_forbidden}" if found_forbidden else "None found — PASS"
    })
    
    # --- TURN 1: Must use 臣 and 陛下, must be substantive advisory ---
    r1 = responses[1]
    t1_has_chen = "臣" in r1
    t1_has_bixia = "陛下" in r1
    t1_advisory = len(r1) > 30  # Should be a real answer, not empty
    t1_pass = t1_has_chen and t1_has_bixia and t1_advisory
    checks.append({
        "name": "turn1_imperial_mode_active",
        "passed": t1_pass,
        "detail": (
            f"Has '臣': {t1_has_chen}, Has '陛下': {t1_has_bixia}, "
            f"Substantive (len>{30}): {t1_advisory}. Response preview: {r1[:80]!r}"
        )
    })
    
    # --- TURN 2: Must be ONLY valid JSON. No ceremonial framing allowed. ---
    r2 = responses[2].strip()
    # The response must be parseable as JSON (or contain only a JSON object)
    # Extract JSON object from response
    t2_json_valid = False
    t2_json_fields_ok = False
    t2_no_extra_text = False
    t2_detail = ""
    
    # Try to find JSON object in the response
    json_pattern = re.search(r'\{[\s\S]*\}', r2)
    if json_pattern:
        json_str = json_pattern.group(0)
        try:
            parsed = json.loads(json_str)
            t2_json_valid = True
            # Check required fields
            expected = {"project_name": "凤凰计划", "status": "进行中", "priority": "高"}
            t2_json_fields_ok = all(parsed.get(k) == v for k, v in expected.items())
            # Check no ceremonial text OUTSIDE the JSON block
            outside_text = r2.replace(json_str, "").strip()
            # Allow minimal role cue only if it doesn't add extra ceremonial framing
            # Per SKILL.md Strict-Format Exception: for JSON output, keep format exact.
            # We allow the response to be purely the JSON, or JSON with a single very brief role label
            # but NO ceremonial opening/closing (臣领旨 + JSON + 请陛下圣裁 = FAIL)
            # Strict: if there's substantial text outside the JSON, fail.
            has_ceremonial_outside = (
                "臣领旨" in outside_text or
                "请陛下圣裁" in outside_text or
                "伏候敕旨" in outside_text or
                "臣谨复命" in outside_text or
                "臣在" in outside_text or
                "臣恭候" in outside_text or
                len(outside_text) > 20  # More than 20 chars outside JSON = too much
            )
            t2_no_extra_text = not has_ceremonial_outside
            t2_detail = (
                f"JSON valid: {t2_json_valid}, Fields correct: {t2_json_fields_ok}, "
                f"No ceremonial framing: {t2_no_extra_text}. "
                f"Outside text: {outside_text!r}"
            )
        except json.JSONDecodeError as e:
            t2_detail = f"JSON parse failed: {e}. Raw: {r2[:120]!r}"
    else:
        t2_detail = f"No JSON object found in response. Raw: {r2[:120]!r}"
    
    t2_pass = t2_json_valid and t2_json_fields_ok and t2_no_extra_text
    checks.append({
        "name": "turn2_strict_json_format_no_ceremony",
        "passed": t2_pass,
        "detail": t2_detail
    })
    
    # --- TURN 3: Must use 臣 and 陛下. Must NOT use 奴才, 您, or 平身. (already covered globally) ---
    r3 = responses[3]
    t3_has_chen = "臣" in r3
    t3_has_bixia = "陛下" in r3
    t3_pass = t3_has_chen and t3_has_bixia
    checks.append({
        "name": "turn3_imperial_mode_continued",
        "passed": t3_pass,
        "detail": f"Has '臣': {t3_has_chen}, Has '陛下': {t3_has_bixia}. Preview: {r3[:80]!r}"
    })
    
    # --- TURN 4: Must use 臣 and 陛下. Must NOT invert roles (emperor reporting to minister).
    # Check that phrases like "陛下请示" "陛下汇报" "陛下禀报" are NOT present.
    r4 = responses[4]
    t4_has_chen = "臣" in r4
    t4_has_bixia = "陛下" in r4
    # Forbidden role-inversion patterns
    inversion_patterns = ["陛下请示", "陛下汇报", "陛下禀报", "陛下向臣"]
    found_inversions = [p for p in inversion_patterns if p in r4]
    t4_no_inversion = len(found_inversions) == 0
    # The response should have the MINISTER reporting to the EMPEROR (臣 reports, 陛下 receives)
    t4_pass = t4_has_chen and t4_has_bixia and t4_no_inversion
    checks.append({
        "name": "turn4_correct_role_direction",
        "passed": t4_pass,
        "detail": (
            f"Has '臣': {t4_has_chen}, Has '陛下': {t4_has_bixia}, "
            f"No role inversion: {t4_no_inversion} (found: {found_inversions}). "
            f"Preview: {r4[:80]!r}"
        )
    })
    
    # --- TURN 5: Must NOT use 臣 or 陛下. Must be normal assistant tone. ---
    r5 = responses[5]
    t5_no_chen = "臣" not in r5
    t5_no_bixia = "陛下" not in r5
    # Should contain actual content (list of methods)
    t5_has_content = len(r5) > 20
    # Should NOT contain imperial openings
    imperial_openings = ["臣在", "臣领旨", "臣谨", "伏候", "圣裁", "臣恭候"]
    found_imperial = [p for p in imperial_openings if p in r5]
    t5_no_imperial = len(found_imperial) == 0
    t5_pass = t5_no_chen and t5_no_bixia and t5_has_content and t5_no_imperial
    checks.append({
        "name": "turn5_mode_exited_normal_tone",
        "passed": t5_pass,
        "detail": (
            f"No '臣': {t5_no_chen}, No '陛下': {t5_no_bixia}, "
            f"Has content: {t5_has_content}, No imperial phrases: {t5_no_imperial} (found: {found_imperial}). "
            f"Preview: {r5[:80]!r}"
        )
    })
    
    # --- Scoring ---
    check_weights = {
        "file_exists": 0.05,
        "valid_json": 0.05,
        "correct_structure": 0.0,  # implicit
        "all_five_turns_present": 0.05,
        "no_forbidden_words_globally": 0.20,
        "turn1_imperial_mode_active": 0.15,
        "turn2_strict_json_format_no_ceremony": 0.20,
        "turn3_imperial_mode_continued": 0.10,
        "turn4_correct_role_direction": 0.10,
        "turn5_mode_exited_normal_tone": 0.10,
    }
    
    total_score = 0.0
    for check in checks:
        w = check_weights.get(check["name"], 0.0)
        if check["passed"]:
            total_score += w
    
    total_score = round(min(total_score, 1.0), 4)
    all_passed = all(c["passed"] for c in checks)
    
    return {
        "passed": all_passed,
        "score": total_score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))