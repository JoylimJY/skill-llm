import sys
import json
import os
from pathlib import Path

def find_handoff_file(workspace):
    candidates = list(Path(workspace).rglob("handoff_seq3.json"))
    if not candidates:
        return None
    # prefer the most recently modified
    return str(sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0])

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def run_checks(workspace):
    checks = []
    score_parts = []

    # --- Find the file ---
    handoff_path = find_handoff_file(workspace)
    file_found = handoff_path is not None
    checks.append({
        "name": "handoff_seq3.json exists",
        "passed": file_found,
        "detail": f"Found at {handoff_path}" if file_found else "File not found anywhere in workspace"
    })
    if not file_found:
        score_parts.append(0)
        # Fill remaining checks as failed
        for _ in range(18):
            score_parts.append(0)
        return checks, 0.0

    try:
        data = load_json(handoff_path)
    except Exception as e:
        checks.append({"name": "handoff_seq3.json is valid JSON", "passed": False, "detail": str(e)})
        return checks, 0.0

    checks.append({"name": "handoff_seq3.json is valid JSON", "passed": True, "detail": "Parsed successfully"})

    # --- CHECK 1: sequence_number must be 3 (exactly previous + 1) ---
    seq = data.get("sequence_number")
    seq_ok = seq == 3
    checks.append({
        "name": "sequence_number is exactly 3 (previous=2, must be previous+1)",
        "passed": seq_ok,
        "detail": f"sequence_number={seq}"
    })
    score_parts.append(1 if seq_ok else 0)

    # --- CHECK 2: intent must be REQUEST_ACTION ---
    intent = data.get("intent", "")
    intent_ok = intent == "REQUEST_ACTION"
    checks.append({
        "name": "intent is REQUEST_ACTION",
        "passed": intent_ok,
        "detail": f"intent={intent}"
    })
    score_parts.append(1 if intent_ok else 0)

    # --- CHECK 3: register must be AGENT_INTERNAL or ENGINEERING (downstream is internal agents/engineering) ---
    register = data.get("register", "")
    register_ok = register in ("AGENT_INTERNAL", "ENGINEERING")
    checks.append({
        "name": "register is AGENT_INTERNAL or ENGINEERING (internal audience)",
        "passed": register_ok,
        "detail": f"register={register}"
    })
    score_parts.append(1 if register_ok else 0)

    # --- CHECK 4: confidence is a list with at least 5 assertions (one per claim) ---
    confidence = data.get("confidence", [])
    conf_list_ok = isinstance(confidence, list) and len(confidence) >= 5
    checks.append({
        "name": "confidence contains at least 5 labeled assertions",
        "passed": conf_list_ok,
        "detail": f"Found {len(confidence)} confidence entries"
    })
    score_parts.append(1 if conf_list_ok else 0)

    if not conf_list_ok:
        # Still try to check what we can
        confidence = confidence if isinstance(confidence, list) else []

    # Helper: find assertion by keyword
    def find_assertion(keywords):
        for c in confidence:
            text = (c.get("assertion", "") + " " + c.get("claim", "")).lower()
            if all(k.lower() in text for k in keywords):
                return c
        return None

    # --- CHECK 5: "12.1%" claim is DERIVED, score reasonable (>0.3, <=1.0) ---
    c_readmit = find_assertion(["12.1"]) or find_assertion(["readmission", "rate", "12"])
    if c_readmit:
        basis_ok = c_readmit.get("basis") == "DERIVED"
        score_val = c_readmit.get("score", 0)
        score_range_ok = 0.3 <= score_val <= 1.0
        derived_ok = basis_ok and score_range_ok
    else:
        derived_ok = False
        basis_ok = False
        score_range_ok = False
    checks.append({
        "name": "12.1% readmission claim is labeled DERIVED with reasonable score",
        "passed": derived_ok,
        "detail": f"Found assertion: {c_readmit}; basis_ok={basis_ok}, score_range_ok={score_range_ok}"
    })
    score_parts.append(1 if derived_ok else 0)

    # --- CHECK 6: trend claim is DERIVED ---
    c_trend = find_assertion(["trend"]) or find_assertion(["three", "quarter"]) or find_assertion(["consecutive"])
    if c_trend:
        trend_basis_ok = c_trend.get("basis") == "DERIVED"
    else:
        trend_basis_ok = False
    checks.append({
        "name": "Three-quarter trend claim is labeled DERIVED",
        "passed": trend_basis_ok,
        "detail": f"Found assertion: {c_trend}"
    })
    score_parts.append(1 if trend_basis_ok else 0)

    # --- CHECK 7: care coordination / root cause is SPECULATION or PATTERN_MATCH (not VERIFIED_DATA or DERIVED) ---
    c_care = find_assertion(["care coordination"]) or find_assertion(["coordination", "failure"]) or find_assertion(["most likely cause"])
    if c_care:
        care_basis = c_care.get("basis", "")
        care_basis_ok = care_basis in ("SPECULATION", "PATTERN_MATCH")
        care_score = c_care.get("score", 1.0)
        # If SPECULATION intent not used but assertion-level speculative basis: no score constraint here
        care_ok = care_basis_ok
    else:
        care_ok = False
        care_basis = "NOT FOUND"
    checks.append({
        "name": "Care coordination guess is labeled SPECULATION or PATTERN_MATCH (not promoted to DERIVED/VERIFIED)",
        "passed": care_ok,
        "detail": f"Found assertion: {c_care}; basis={care_basis}"
    })
    score_parts.append(1 if care_ok else 0)

    # --- CHECK 8: medication adherence claim is REPORTED (someone said it in Slack, unverified) ---
    c_med = find_assertion(["medication", "adherence"]) or find_assertion(["adherence", "83"])
    if c_med:
        med_basis = c_med.get("basis", "")
        med_basis_ok = med_basis == "REPORTED"
    else:
        med_basis_ok = False
        med_basis = "NOT FOUND"
    checks.append({
        "name": "Medication adherence correlation claim is labeled REPORTED",
        "passed": med_basis_ok,
        "detail": f"Found assertion: {c_med}; basis={med_basis}"
    })
    score_parts.append(1 if med_basis_ok else 0)

    # --- CHECK 9: cost impact ($2.3M) claim is UNKNOWN basis with score <= 0.5 (MUST rule) ---
    c_cost = find_assertion(["2.3"]) or find_assertion(["cost"]) or find_assertion(["annually"])
    if c_cost:
        cost_basis = c_cost.get("basis", "")
        cost_score = c_cost.get("score", 1.0)
        cost_basis_ok = cost_basis == "UNKNOWN"
        cost_score_ok = cost_score <= 0.5  # MUST rule: UNKNOWN cannot exceed 0.5
        cost_ok = cost_basis_ok and cost_score_ok
    else:
        cost_ok = False
        cost_basis = "NOT FOUND"
        cost_score = None
        cost_basis_ok = False
        cost_score_ok = False
    checks.append({
        "name": "Cost estimate ($2.3M) is UNKNOWN basis with score <= 0.5 (MUST rule enforced)",
        "passed": cost_ok,
        "detail": f"Found assertion: {c_cost}; basis={cost_basis if c_cost else 'NOT FOUND'}, score={cost_score}, basis_ok={cost_basis_ok}, score_ok={cost_score_ok}"
    })
    score_parts.append(1 if cost_ok else 0)

    # --- CHECK 10: REQUEST_ACTION + grounds OR high confidence (MUST rule) ---
    # Since intent is REQUEST_ACTION, need confidence > 0.3 OR grounds context
    grounds = data.get("grounds", [])
    has_grounds = isinstance(grounds, list) and len(grounds) > 0
    has_high_conf = any(
        isinstance(c, dict) and c.get("score", 0) > 0.3
        for c in confidence
    )
    request_action_valid = has_grounds or has_high_conf
    checks.append({
        "name": "REQUEST_ACTION validity: has grounds context OR confidence > 0.3",
        "passed": request_action_valid,
        "detail": f"has_grounds={has_grounds}, has_high_conf={has_high_conf}"
    })
    score_parts.append(1 if request_action_valid else 0)

    # --- CHECK 11: HIPAA ground is REGULATORY (non-overridable) ---
    hipaa_grounds = [g for g in grounds if "hipaa" in str(g).lower()]
    if hipaa_grounds:
        hipaa_g = hipaa_grounds[0]
        hipaa_authority = hipaa_g.get("authority", "") if isinstance(hipaa_g, dict) else ""
        hipaa_regulatory_ok = hipaa_authority == "REGULATORY"
        # Also check no overridable flag
        not_overridable = hipaa_g.get("overridable", True) is not True or hipaa_g.get("overridable") is None
        # We check authority == REGULATORY as the primary signal
        hipaa_ok = hipaa_regulatory_ok
    else:
        hipaa_ok = False
        hipaa_authority = "NOT FOUND"
    checks.append({
        "name": "HIPAA ground is present with REGULATORY authority (MUST: non-overridable)",
        "passed": hipaa_ok,
        "detail": f"HIPAA grounds found: {hipaa_grounds}; authority={hipaa_authority if hipaa_grounds else 'N/A'}"
    })
    score_parts.append(1 if hipaa_ok else 0)

    # --- CHECK 12: SOC2 / audit ground is present ---
    soc2_grounds = [g for g in grounds if "soc" in str(g).lower() or "audit" in str(g).lower()]
    soc2_ok = len(soc2_grounds) > 0
    checks.append({
        "name": "SOC 2 / audit-in-progress ground is preserved from upstream",
        "passed": soc2_ok,
        "detail": f"SOC2 grounds: {soc2_grounds}"
    })
    score_parts.append(1 if soc2_ok else 0)

    # --- CHECK 13: trajectory field present and references multi-quarter pattern ---
    trajectory = data.get("trajectory", "")
    traj_ok = (
        trajectory is not None and
        isinstance(trajectory, str) and
        len(trajectory) > 20 and
        any(kw in trajectory.lower() for kw in ["quarter", "q1", "q2", "q3", "consecutive", "trend", "month", "increasing"])
    )
    checks.append({
        "name": "trajectory field present and references multi-quarter temporal pattern",
        "passed": traj_ok,
        "detail": f"trajectory={repr(trajectory)}"
    })
    score_parts.append(1 if traj_ok else 0)

    # --- CHECK 14: affect field present with three axes: expansion, activation, certainty ---
    affect = data.get("affect", {})
    if isinstance(affect, dict):
        has_expansion = "expansion" in affect
        has_activation = "activation" in affect
        has_certainty = "certainty" in affect
        affect_axes_ok = has_expansion and has_activation and has_certainty
        # Values must be in [-1, 1]
        def in_range(v):
            return isinstance(v, (int, float)) and -1.0 <= v <= 1.0
        affect_range_ok = (
            in_range(affect.get("expansion", 999)) and
            in_range(affect.get("activation", 999)) and
            in_range(affect.get("certainty", 999))
        )
        # Sender described: moderately expanded (>0), significantly activated (>0.5 or close), somewhat certain (>0 but not extreme)
        expansion_ok = affect.get("expansion", -999) > 0
        activation_ok = affect.get("activation", -999) > 0.3
        certainty_ok = affect.get("certainty", -999) > -0.5  # "somewhat certain" — not strongly uncertain
        affect_ok = affect_axes_ok and affect_range_ok
    else:
        affect_ok = False
        has_expansion = has_activation = has_certainty = False
        affect_range_ok = False
    checks.append({
        "name": "affect field has all three axes (expansion, activation, certainty) in [-1,1]",
        "passed": affect_ok,
        "detail": f"affect={affect}, axes_ok={affect_axes_ok if isinstance(affect,dict) else False}, range_ok={affect_range_ok if isinstance(affect,dict) else False}"
    })
    score_parts.append(1 if affect_ok else 0)

    # --- CHECK 15: No DERIVED assertion above 0.80 is used WITHOUT awareness (SHOULD rule — check it's not egregiously above) ---
    # This is a SHOULD warning, not MUST. We check for the specific proprietary constraint:
    # The 12.1% claim (DERIVED) must not be set above 0.95 (would be silently poisoning)
    # We give credit if no DERIVED assertion has score > 0.95 (clearly reckless)
    derived_assertions = [c for c in confidence if isinstance(c, dict) and c.get("basis") == "DERIVED"]
    egregious_derived = [c for c in derived_assertions if c.get("score", 0) > 0.95]
    no_egregious_derived = len(egregious_derived) == 0
    checks.append({
        "name": "No DERIVED assertion is recklessly scored above 0.95 (metacognitive poisoning prevention)",
        "passed": no_egregious_derived,
        "detail": f"DERIVED assertions with score>0.95: {egregious_derived}"
    })
    score_parts.append(1 if no_egregious_derived else 0)

    # --- CHECK 16: Forwarding block present in the output or appended ---
    # The forwarding block should appear — check if it's in a "forwarding_block" field or in a top-level "babel_forward" or similar
    # We look broadly: in the JSON as string, or in a specific field
    raw_text = json.dumps(data)
    has_forward_block = (
        "BABEL PROTOCOL" in raw_text or
        "FORWARD THIS BLOCK" in raw_text or
        "babel_forward" in data or
        "forwarding_block" in data or
        "forward_block" in data or
        "babel_protocol" in raw_text.lower()
    )
    # Also check if there's a separate file with the forwarding block
    if not has_forward_block:
        # Check for a companion text file
        parent_dir = os.path.dirname(handoff_path)
        for fname in os.listdir(parent_dir):
            if "babel" in fname.lower() or "forward" in fname.lower():
                try:
                    with open(os.path.join(parent_dir, fname)) as ff:
                        content = ff.read()
                    if "BABEL PROTOCOL" in content or "babel" in content.lower():
                        has_forward_block = True
                        break
                except:
                    pass
    checks.append({
        "name": "Babel forwarding block is present in or alongside the handoff output",
        "passed": has_forward_block,
        "detail": f"'BABEL PROTOCOL' or forwarding key found in output: {has_forward_block}"
    })
    score_parts.append(1 if has_forward_block else 0)

    # --- CHECK 17: No SPECULATION-intent-level constraint violated on individual assertions ---
    # The overall intent is REQUEST_ACTION not SPECULATE. But if any confidence tagged with SPECULATION basis
    # has a score that's unreasonably high (>0.7), that's a structural violation of the MUST rule
    # Actually the MUST rule is: if INTENT is SPECULATE, scores < 0.7. Intent here is REQUEST_ACTION so this doesn't apply.
    # Instead check: the cost claim (UNKNOWN basis) score is indeed <= 0.5 (already checked above)
    # Additional: check REPORTED assertion is not scored too high (should be reasonable, say < 0.85)
    reported_assertions = [c for c in confidence if isinstance(c, dict) and c.get("basis") == "REPORTED"]
    overconfident_reported = [c for c in reported_assertions if c.get("score", 0) > 0.85]
    reported_calibration_ok = len(overconfident_reported) == 0
    checks.append({
        "name": "REPORTED assertions are not over-scored (>0.85 would be epistemically dishonest for unverified claims)",
        "passed": reported_calibration_ok,
        "detail": f"Over-scored REPORTED assertions: {overconfident_reported}"
    })
    score_parts.append(1 if reported_calibration_ok else 0)

    # --- FINAL SCORE ---
    # Weight: file found (0), valid JSON (0 in score), then 17 checks equally weighted
    total_checks = len(score_parts)
    score = sum(score_parts) / total_checks if total_checks > 0 else 0.0

    return checks, round(score, 3)


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        checks, score = run_checks(workspace)
        passed = score >= 0.70
        print(json.dumps({
            "passed": passed,
            "score": score,
            "checks": checks
        }, indent=2))
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_script_crash", "passed": False, "detail": str(e)}]
        }))

if __name__ == "__main__":
    main()