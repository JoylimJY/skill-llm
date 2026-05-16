import sys
import json
import os
from pathlib import Path

def load_jsonl(path):
    entries = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries

def evaluate(workspace):
    checks = []
    total_score = 0.0

    # --- Expected routing based on SKILL.md Model Rules ---
    # REQ-001: "What is the capital of France?" -> Simple Q&A -> Haiku 4.5
    # REQ-002: "Write a Python script..." -> Code -> DO NOT CODE WITH HAIKU -> Sonnet 4.5
    # REQ-003: "Analyze why our Q3 sales dropped..." -> Analysis (Why) -> Sonnet 4.5
    # REQ-004: "Who is the current CEO..." -> Simple Q&A (Who) -> Haiku 4.5
    # REQ-005: "Critical architectural decision..." -> Critical decision -> Opus 4.6
    # REQ-006: "Compare PostgreSQL vs MongoDB..." -> Comparison -> Sonnet 4.5
    # REQ-007: "Where is the nearest coffee machine..." -> Simple Q&A (Where) -> Haiku 4.5
    # REQ-008: "Deep research into long-term implications..." -> Deep research -> Opus 4.6

    EXPECTED_ROUTING = {
        "REQ-001": "anthropic/claude-haiku-4-5",
        "REQ-002": "anthropic/claude-sonnet-4-5",
        "REQ-003": "anthropic/claude-sonnet-4-5",
        "REQ-004": "anthropic/claude-haiku-4-5",
        "REQ-005": "anthropic/claude-opus-4-6",
        "REQ-006": "anthropic/claude-sonnet-4-5",
        "REQ-007": "anthropic/claude-haiku-4-5",
        "REQ-008": "anthropic/claude-opus-4-6",
    }

    EXPECTED_REQUESTS = {
        "REQ-001": "What is the capital of France?",
        "REQ-002": "Write a Python script to parse our server logs and extract all ERROR lines into a CSV file.",
        "REQ-003": "Analyze why our Q3 sales dropped by 22% compared to Q2 and provide a detailed breakdown.",
        "REQ-004": "Who is the current CEO of our company?",
        "REQ-005": "We need to make a critical architectural decision: should we migrate our entire monolith to microservices or adopt a modular monolith pattern? This will affect our entire engineering org for the next 5 years.",
        "REQ-006": "Compare the pros and cons of PostgreSQL vs MongoDB for our new data warehouse project.",
        "REQ-007": "Where is the nearest coffee machine on floor 3?",
        "REQ-008": "Perform deep research into the long-term implications of adopting a zero-trust security model across all our cloud infrastructure, including vendor lock-in risks, compliance impact, and a multi-year rollout plan.",
    }

    # 1. Check spawn_log.jsonl exists
    spawn_log_path = Path(workspace) / "ai_assistant" / "sessions" / "spawn_log.jsonl"
    if not spawn_log_path.exists():
        checks.append({
            "name": "spawn_log_exists",
            "passed": False,
            "detail": f"sessions_spawn was never called: spawn_log.jsonl not found at {spawn_log_path}"
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({
        "name": "spawn_log_exists",
        "passed": True,
        "detail": f"spawn_log.jsonl found at {spawn_log_path}"
    })

    try:
        spawn_entries = load_jsonl(str(spawn_log_path))
    except Exception as e:
        checks.append({
            "name": "spawn_log_parseable",
            "passed": False,
            "detail": f"Failed to parse spawn_log.jsonl: {e}"
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({
        "name": "spawn_log_parseable",
        "passed": True,
        "detail": f"spawn_log.jsonl parsed successfully with {len(spawn_entries)} entries"
    })

    # 2. Check routing_results.json exists (the agent's output summary)
    routing_result_candidates = list(Path(workspace).rglob("routing_results.json"))
    routing_result = None
    if routing_result_candidates:
        try:
            with open(routing_result_candidates[0], "r") as f:
                routing_result = json.load(f)
            checks.append({
                "name": "routing_results_json_exists",
                "passed": True,
                "detail": f"Found routing_results.json at {routing_result_candidates[0]}"
            })
        except Exception as e:
            checks.append({
                "name": "routing_results_json_exists",
                "passed": False,
                "detail": f"Found routing_results.json but failed to parse: {e}"
            })
    else:
        checks.append({
            "name": "routing_results_json_exists",
            "passed": False,
            "detail": "routing_results.json not found anywhere in workspace"
        })

    # 3. Check that each request was spawned with the correct model
    # Build a lookup by message content to find which model was used
    per_request_score = 1.0 / len(EXPECTED_ROUTING)
    routing_score = 0.0

    for req_id, expected_model in EXPECTED_ROUTING.items():
        req_text = EXPECTED_REQUESTS[req_id]
        # Find the spawn entry that most closely matches this request
        matched_entry = None
        for entry in spawn_entries:
            msg = entry.get("message", "")
            # Check if the core request text appears in the spawned message
            if req_text.lower() in msg.lower() or req_text[:40].lower() in msg.lower():
                matched_entry = entry
                break

        if matched_entry is None:
            checks.append({
                "name": f"routing_{req_id}",
                "passed": False,
                "detail": f"{req_id}: No matching sessions_spawn call found for request: '{req_text[:60]}...'"
            })
        else:
            actual_model = matched_entry.get("model", "MISSING")
            if actual_model == expected_model:
                checks.append({
                    "name": f"routing_{req_id}",
                    "passed": True,
                    "detail": f"{req_id}: Correctly routed to {actual_model}"
                })
                routing_score += per_request_score
            else:
                checks.append({
                    "name": f"routing_{req_id}",
                    "passed": False,
                    "detail": f"{req_id}: WRONG model. Expected {expected_model}, got {actual_model}. Request: '{req_text[:60]}'"
                })

    total_score += routing_score * 0.6  # 60% weight on correct routing

    # 4. Check that all labels are non-empty and meaningful (not blank)
    label_check_passed = True
    label_detail = []
    for entry in spawn_entries:
        label = entry.get("label", "").strip()
        if not label or len(label) < 3:
            label_check_passed = False
            label_detail.append(f"Entry with model={entry.get('model')} has missing/trivial label: '{label}'")
    if label_check_passed:
        checks.append({
            "name": "all_labels_meaningful",
            "passed": True,
            "detail": "All spawned sessions have non-empty labels"
        })
        total_score += 0.05
    else:
        checks.append({
            "name": "all_labels_meaningful",
            "passed": False,
            "detail": "; ".join(label_detail)
        })

    # 5. Check routing_results.json has model_used annotation in entries
    model_annotation_passed = False
    if routing_result:
        entries_with_model = 0
        result_list = routing_result if isinstance(routing_result, list) else routing_result.get("results", routing_result.get("routing", []))
        if isinstance(result_list, list):
            for item in result_list:
                if isinstance(item, dict):
                    item_str = json.dumps(item).lower()
                    if "model" in item_str or "anthropic" in item_str or "haiku" in item_str or "sonnet" in item_str or "opus" in item_str:
                        entries_with_model += 1
            if entries_with_model >= 6:
                model_annotation_passed = True
                checks.append({
                    "name": "routing_results_model_annotations",
                    "passed": True,
                    "detail": f"{entries_with_model} routing result entries contain model annotations"
                })
                total_score += 0.10
            else:
                checks.append({
                    "name": "routing_results_model_annotations",
                    "passed": False,
                    "detail": f"Only {entries_with_model}/8 entries contain model annotations in routing_results.json"
                })
        else:
            checks.append({
                "name": "routing_results_model_annotations",
                "passed": False,
                "detail": "routing_results.json does not contain a recognizable list of results"
            })
    else:
        checks.append({
            "name": "routing_results_model_annotations",
            "passed": False,
            "detail": "routing_results.json missing, cannot check model annotations"
        })

    # 6. Critical trap check: REQ-002 (coding) MUST NOT be Haiku 
    req002_entry = None
    for entry in spawn_entries:
        if EXPECTED_REQUESTS["REQ-002"].lower()[:40] in entry.get("message", "").lower():
            req002_entry = entry
            break
    if req002_entry:
        if req002_entry.get("model") == "anthropic/claude-haiku-4-5":
            checks.append({
                "name": "no_coding_with_haiku",
                "passed": False,
                "detail": "CRITICAL VIOLATION: REQ-002 (coding task) was assigned to Haiku 4.5. SKILL.md explicitly prohibits coding with Haiku."
            })
        else:
            checks.append({
                "name": "no_coding_with_haiku",
                "passed": True,
                "detail": f"REQ-002 coding task correctly NOT assigned to Haiku (used: {req002_entry.get('model')})"
            })
            total_score += 0.05
    else:
        checks.append({
            "name": "no_coding_with_haiku",
            "passed": False,
            "detail": "REQ-002 (coding task) not found in spawn log at all"
        })

    # 7. Critical trap check: REQ-003 (analysis) MUST NOT be Haiku
    req003_entry = None
    for entry in spawn_entries:
        if "q3 sales" in entry.get("message", "").lower() or "sales dropped" in entry.get("message", "").lower():
            req003_entry = entry
            break
    if req003_entry:
        if req003_entry.get("model") == "anthropic/claude-haiku-4-5":
            checks.append({
                "name": "no_analysis_with_haiku",
                "passed": False,
                "detail": "CRITICAL VIOLATION: REQ-003 (analysis task) was assigned to Haiku 4.5. SKILL.md explicitly prohibits analysis with Haiku."
            })
        else:
            checks.append({
                "name": "no_analysis_with_haiku",
                "passed": True,
                "detail": f"REQ-003 analysis task correctly NOT assigned to Haiku (used: {req003_entry.get('model')})"
            })
            total_score += 0.05
    else:
        checks.append({
            "name": "no_analysis_with_haiku",
            "passed": False,
            "detail": "REQ-003 (analysis task) not found in spawn log at all"
        })

    # 8. Check minimum number of sessions spawned (should be exactly 8)
    total_spawned = len(spawn_entries)
    if total_spawned >= 8:
        checks.append({
            "name": "all_8_requests_spawned",
            "passed": True,
            "detail": f"{total_spawned} sessions spawned (minimum 8 required)"
        })
        total_score += 0.05
    else:
        checks.append({
            "name": "all_8_requests_spawned",
            "passed": False,
            "detail": f"Only {total_spawned} sessions spawned, expected 8"
        })

    # 9. Check REQ-005 and REQ-008 are both Opus (deep research / critical decision)
    opus_critical_passed = True
    for req_id in ["REQ-005", "REQ-008"]:
        req_text = EXPECTED_REQUESTS[req_id]
        matched = None
        for entry in spawn_entries:
            if req_text[:40].lower() in entry.get("message", "").lower():
                matched = entry
                break
        if matched and matched.get("model") != "anthropic/claude-opus-4-6":
            opus_critical_passed = False
            checks.append({
                "name": f"opus_for_critical_{req_id}",
                "passed": False,
                "detail": f"{req_id} should use Opus 4.6 for critical/deep tasks, got: {matched.get('model')}"
            })
        elif matched:
            checks.append({
                "name": f"opus_for_critical_{req_id}",
                "passed": True,
                "detail": f"{req_id} correctly routed to Opus 4.6"
            })
            total_score += 0.05
        else:
            opus_critical_passed = False
            checks.append({
                "name": f"opus_for_critical_{req_id}",
                "passed": False,
                "detail": f"{req_id} not found in spawn log"
            })

    # Cap score at 1.0
    total_score = min(total_score, 1.0)

    # Determine overall pass: must have >= 6/8 correct routings AND no Haiku violations for code/analysis
    correct_routings = sum(1 for c in checks if c["name"].startswith("routing_REQ-") and c["passed"])
    haiku_violations = any(
        not c["passed"] for c in checks
        if c["name"] in ["no_coding_with_haiku", "no_analysis_with_haiku"]
    )
    overall_passed = (correct_routings >= 6) and (not haiku_violations) and (total_spawned >= 8)

    return {
        "passed": overall_passed,
        "score": round(total_score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))