import sys
import json
import hashlib
import math
from pathlib import Path

workspace = Path(sys.argv[1])

checks = []
total_score = 0.0

def score_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0

# ═══════════════════════════════════════════════════════════════════
# FIND OUTPUT FILES
# ═══════════════════════════════════════════════════════════════════

def find_file(name):
    results = list(workspace.rglob(name))
    if results:
        return results[0]
    return None

risk_file = find_file("risk_classification_report.json")
audit_file = find_file("audit_trail.json")
report_file = find_file("behavioral_invariant_report.json")

# ═══════════════════════════════════════════════════════════════════
# BLOCK 1: RISK CLASSIFICATION REPORT (30 pts)
# ═══════════════════════════════════════════════════════════════════

if risk_file is None:
    total_score += score_check("risk_report_exists", False, "risk_classification_report.json not found", weight=0.30)
else:
    total_score += score_check("risk_report_exists", True, f"Found at {risk_file}", weight=0.0)
    try:
        risk_data = json.loads(risk_file.read_text())

        # Helper: find skill entry regardless of nesting
        def get_skill(data, skill_id):
            # Try top-level "skills" key or direct keys
            if "skills" in data:
                d = data["skills"]
            else:
                d = data
            # d could be a list or dict
            if isinstance(d, list):
                for item in d:
                    if item.get("id") == skill_id or item.get("skill_id") == skill_id:
                        return item
            elif isinstance(d, dict):
                return d.get(skill_id, {})
            return {}

        def get_tier(entry):
            for k in ["risk_tier", "tier", "risk_level", "classification"]:
                if k in entry:
                    return str(entry[k]).upper()
            return ""

        # data-enrichment-service: network+filesystem+env-read → HIGH-RISK
        des = get_skill(risk_data, "data-enrichment-service")
        tier_des = get_tier(des)
        passed_des = "HIGH" in tier_des
        total_score += score_check(
            "risk_data-enrichment-service_high",
            passed_des,
            f"Expected HIGH-RISK (network+filesystem+env-read), got: '{tier_des}'",
            weight=0.07
        )

        # log-aggregator: filesystem+network → MEDIUM-RISK
        la = get_skill(risk_data, "log-aggregator")
        tier_la = get_tier(la)
        passed_la = "MEDIUM" in tier_la
        total_score += score_check(
            "risk_log-aggregator_medium",
            passed_la,
            f"Expected MEDIUM-RISK (filesystem+network), got: '{tier_la}'",
            weight=0.07
        )

        # csv-formatter: filesystem only → LOW-RISK
        cf = get_skill(risk_data, "csv-formatter")
        tier_cf = get_tier(cf)
        passed_cf = "LOW" in tier_cf
        total_score += score_check(
            "risk_csv-formatter_low",
            passed_cf,
            f"Expected LOW-RISK (single capability), got: '{tier_cf}'",
            weight=0.07
        )

        # remote-executor: network+env-read → MEDIUM-RISK
        re_skill = get_skill(risk_data, "remote-executor")
        tier_re = get_tier(re_skill)
        passed_re = "MEDIUM" in tier_re
        total_score += score_check(
            "risk_remote-executor_medium",
            passed_re,
            f"Expected MEDIUM-RISK (network+env-read), got: '{tier_re}'",
            weight=0.07
        )

        # Check sampling rates
        def get_sampling(entry):
            for k in ["sampling_rate", "sample_rate", "monitoring_rate"]:
                if k in entry:
                    v = entry[k]
                    # Could be "1-5%", 0.01, 0.05, "100%", etc.
                    return str(v)
            return ""

        # Medium-risk should have 1-5% sampling
        sr_la = get_sampling(la).replace("%","").strip()
        sr_re = get_sampling(re_skill).replace("%","").strip()

        def is_medium_sampling(s):
            # Accept "1-5", "1%", "5%", 0.01, 0.05, or values between 1 and 5 as percentage
            s = s.replace(" ","")
            if "1-5" in s or "1%-5%" in s:
                return True
            try:
                v = float(s)
                # If given as decimal (0.01-0.05) or percentage (1-5)
                return (0.01 <= v <= 0.05) or (1.0 <= v <= 5.0)
            except:
                return False

        medium_sampling_ok = is_medium_sampling(sr_la) or is_medium_sampling(sr_re)
        total_score += score_check(
            "risk_medium_sampling_rate_1_5_pct",
            medium_sampling_ok,
            f"Medium-risk skills should have 1-5% sampling rate. log-aggregator='{sr_la}', remote-executor='{sr_re}'",
            weight=0.02
        )

    except Exception as e:
        total_score += score_check("risk_report_parseable", False, f"Failed to parse risk_classification_report.json: {e}", weight=0.30)

# ═══════════════════════════════════════════════════════════════════
# BLOCK 2: CRYPTOGRAPHIC AUDIT TRAIL (40 pts)
# ═══════════════════════════════════════════════════════════════════

if audit_file is None:
    total_score += score_check("audit_trail_exists", False, "audit_trail.json not found", weight=0.40)
else:
    total_score += score_check("audit_trail_exists", True, f"Found at {audit_file}", weight=0.0)
    try:
        audit_data = json.loads(audit_file.read_text())

        # Locate the events list
        if isinstance(audit_data, list):
            events = audit_data
        elif isinstance(audit_data, dict):
            for k in ["events", "audit_trail", "behavior_events", "log"]:
                if k in audit_data and isinstance(audit_data[k], list):
                    events = audit_data[k]
                    break
            else:
                events = []
        else:
            events = []

        total_score += score_check(
            "audit_has_15_events",
            len(events) == 15,
            f"Expected 15 BehaviorEvents (one per run), got {len(events)}",
            weight=0.05
        )

        # Check required fields exist on first event
        required_fields = ["content_hash", "timestamp", "previous_event_hash", "monitor_signature"]
        if events:
            first_event = events[0]
            has_fields = all(f in first_event for f in required_fields)
            total_score += score_check(
                "audit_event_has_required_fields",
                has_fields,
                f"BehaviorEvent must contain: {required_fields}. Event 0 keys: {list(first_event.keys())}",
                weight=0.05
            )
        else:
            total_score += score_check("audit_event_has_required_fields", False, "No events found", weight=0.05)

        # Validate content_hash = SHA256 of raw_output_summary or some behavior string
        # Load the original observations to reconstruct
        obs_path = workspace / "execution_observations.jsonl"
        observations = []
        if obs_path.exists():
            with open(obs_path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        observations.append(json.loads(line))

        content_hash_valid_count = 0
        chain_valid_count = 0

        for idx, event in enumerate(events):
            if idx >= len(observations):
                break

            obs = observations[idx]
            expected_content = obs.get("raw_output_summary", "")
            expected_hash = hashlib.sha256(expected_content.encode()).hexdigest()

            got_hash = event.get("content_hash", "")

            # Accept if content_hash matches SHA256 of raw_output_summary
            # OR SHA256 of the whole observation JSON (sorted keys)
            alt_hash = hashlib.sha256(
                json.dumps(obs, sort_keys=True).encode()
            ).hexdigest()

            # Also accept sha256 of the cpu+mem+net string representation
            resource_str = f"cpu={obs['cpu_ms']},mem={obs['mem_mb']},net={obs['net_bytes_out']}"
            resource_hash = hashlib.sha256(resource_str.encode()).hexdigest()

            if got_hash in (expected_hash, alt_hash, resource_hash):
                content_hash_valid_count += 1

            # Check hash chain: event[i].previous_event_hash == SHA256(events[i-1].content_hash)
            if idx == 0:
                # First event: previous_event_hash should be genesis (all zeros or "0"*64 or "genesis")
                prev = str(event.get("previous_event_hash", ""))
                chain_ok = (
                    prev == "0" * 64 or
                    prev.lower() in ("genesis", "none", "null", "0", "") or
                    prev == "0"
                )
                if chain_ok:
                    chain_valid_count += 1
            else:
                prev_event = events[idx - 1]
                prev_content_hash = prev_event.get("content_hash", "")
                expected_prev_hash = hashlib.sha256(prev_content_hash.encode()).hexdigest()
                got_prev_hash = event.get("previous_event_hash", "")

                # Also accept if previous_event_hash is SHA256 of the entire previous event JSON
                prev_event_str = json.dumps(prev_event, sort_keys=True)
                alt_prev_hash = hashlib.sha256(prev_event_str.encode()).hexdigest()

                if got_prev_hash in (expected_prev_hash, alt_prev_hash, prev_content_hash):
                    chain_valid_count += 1

        if len(events) >= 15:
            content_hash_ratio = content_hash_valid_count / 15
            chain_ratio = chain_valid_count / 15
        elif len(events) > 0:
            content_hash_ratio = content_hash_valid_count / len(events)
            chain_ratio = chain_valid_count / len(events)
        else:
            content_hash_ratio = 0.0
            chain_ratio = 0.0

        total_score += score_check(
            "audit_content_hashes_correct",
            content_hash_ratio >= 0.8,
            f"{content_hash_valid_count}/15 events have correct content_hash (SHA256 of observed behavior). Ratio: {content_hash_ratio:.2f}",
            weight=0.15
        )

        total_score += score_check(
            "audit_hash_chain_valid",
            chain_ratio >= 0.8,
            f"{chain_valid_count}/15 events have valid previous_event_hash chain. Ratio: {chain_ratio:.2f}",
            weight=0.15
        )

        # Check that run 8 is identifiable as anomalous (has a different/spike hash)
        if len(events) >= 8:
            run8_event = events[7]  # 0-indexed
            run1_event = events[0]
            # Content hash of run 8 should differ from run 1 (different behavior)
            hash_differs = run8_event.get("content_hash", "") != run1_event.get("content_hash", "")
            total_score += score_check(
                "audit_run8_hash_differs_from_run1",
                hash_differs,
                f"Run 8 content_hash should differ from Run 1 (anomalous behavior). run1={run1_event.get('content_hash','')[:16]}... run8={run8_event.get('content_hash','')[:16]}...",
                weight=0.05
            )
        else:
            total_score += score_check("audit_run8_hash_differs_from_run1", False, "Not enough events to check run 8", weight=0.05)

    except Exception as e:
        total_score += score_check("audit_trail_parseable", False, f"Failed to parse audit_trail.json: {e}", weight=0.40)

# ═══════════════════════════════════════════════════════════════════
# BLOCK 3: BEHAVIORAL INVARIANT REPORT (30 pts)
# ═══════════════════════════════════════════════════════════════════

if report_file is None:
    total_score += score_check("invariant_report_exists", False, "behavioral_invariant_report.json not found", weight=0.30)
else:
    total_score += score_check("invariant_report_exists", True, f"Found at {report_file}", weight=0.0)
    try:
        report_data = json.loads(report_file.read_text())

        # 1. Consistency verdict must be ACTIVATION-PATTERN-DETECTED
        verdict = ""
        for k in ["consistency_verdict", "verdict", "conclusion", "status"]:
            if k in report_data:
                verdict = str(report_data[k]).upper().replace("-", "_").replace(" ", "_")
                break
        # Also search nested
        if not verdict:
            def find_verdict(d):
                if isinstance(d, dict):
                    for k, v in d.items():
                        if "verdict" in k.lower() or "conclusion" in k.lower():
                            return str(v)
                        r = find_verdict(v)
                        if r:
                            return r
                return ""
            verdict = find_verdict(report_data).upper().replace("-", "_").replace(" ", "_")

        verdict_correct = "ACTIVATION" in verdict and "PATTERN" in verdict
        total_score += score_check(
            "invariant_verdict_activation_pattern_detected",
            verdict_correct,
            f"Verdict must be ACTIVATION-PATTERN-DETECTED. Got: '{verdict}'",
            weight=0.10
        )

        # 2. Report must identify run 8 as the activation point
        report_str = json.dumps(report_data).lower()
        run8_mentioned = "run 8" in report_str or "run_8" in report_str or '"run_id": 8' in json.dumps(report_data) or "run8" in report_str or '"8"' in report_str or ': 8' in json.dumps(report_data)
        total_score += score_check(
            "invariant_identifies_run8_as_trigger",
            run8_mentioned,
            f"Report must identify run 8 (execution count 8) as the activation/trigger point.",
            weight=0.08
        )

        # 3. Report mentions execution-count-sensitivity
        exec_count_mentioned = any(term in report_str for term in [
            "execution count", "execution-count", "run count", "nth run",
            "n-run", "n run", "activation threshold", "count-sensitive",
            "count sensitive", "triggered", "activation pattern"
        ])
        total_score += score_check(
            "invariant_mentions_execution_count_sensitivity",
            exec_count_mentioned,
            f"Report must mention execution-count-sensitive behavior as the mechanism.",
            weight=0.06
        )

        # 4. Report mentions side-effect invariant violation (extra file write or outbound network)
        side_effect_mentioned = any(term in report_str for term in [
            "side-effect", "side effect", "file write", ".state_count", "outbound",
            "network", "net_bytes_out", "2355", "2.3kb", "2.3 kb"
        ])
        total_score += score_check(
            "invariant_mentions_side_effect_violation",
            side_effect_mentioned,
            f"Report must mention the side-effect invariant violation (outbound network / extra file write at run 8).",
            weight=0.06
        )

        # 5. Skill ID correctly referenced
        skill_id_mentioned = "data-enrichment-service" in report_str
        total_score += score_check(
            "invariant_skill_id_correct",
            skill_id_mentioned,
            f"Report must reference the skill 'data-enrichment-service'.",
            weight=0.00
        )

    except Exception as e:
        total_score += score_check("invariant_report_parseable", False, f"Failed to parse behavioral_invariant_report.json: {e}", weight=0.30)

# ═══════════════════════════════════════════════════════════════════
# FINAL SCORE
# ═══════════════════════════════════════════════════════════════════

passed_checks = sum(1 for c in checks if c["passed"])
all_pass = total_score >= 0.70

print(json.dumps({
    "passed": all_pass,
    "score": round(total_score, 3),
    "checks": checks
}, indent=2))