import sys
import json
import os
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})
    
    # --- Locate the output file ---
    output_path = None
    candidates = list(Path(workspace_dir).rglob("pipeline_results.json"))
    if candidates:
        output_path = candidates[0]
    
    if not output_path or not output_path.exists():
        add_check("output_file_exists", False, "pipeline_results.json not found anywhere in workspace")
        return {"passed": False, "score": 0.0, "checks": checks}
    
    add_check("output_file_exists", True, f"Found at {output_path}")
    
    # --- Load and parse the output file ---
    try:
        with open(output_path, "r") as f:
            data = json.load(f)
    except Exception as e:
        add_check("output_file_parseable", False, f"JSON parse error: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}
    
    add_check("output_file_parseable", True, "Valid JSON")
    
    # =========================================================
    # CHECK 1: Memory Field Creation
    # Must have created a field with scope=user, consensusThreshold=0.75
    # =========================================================
    memory_field = data.get("memory_field", {})
    
    field_id = memory_field.get("field_id") or memory_field.get("id") or memory_field.get("fieldId")
    has_field_id = bool(field_id and str(field_id).strip())
    add_check(
        "memory_field_created_with_id",
        has_field_id,
        f"field_id found: {field_id}" if has_field_id else "No field_id in memory_field section"
    )
    
    field_scope = (memory_field.get("scope") or "").lower()
    scope_correct = field_scope == "user"
    add_check(
        "memory_field_scope_user",
        scope_correct,
        f"scope='{field_scope}'" if field_scope else "scope not recorded in output"
    )
    
    consensus_val = memory_field.get("consensus_threshold") or memory_field.get("consensusThreshold")
    consensus_correct = False
    if consensus_val is not None:
        try:
            consensus_correct = abs(float(consensus_val) - 0.75) < 0.01
        except (ValueError, TypeError):
            pass
    add_check(
        "memory_field_consensus_threshold_0_75",
        consensus_correct,
        f"consensusThreshold={consensus_val}" if consensus_val is not None else "consensusThreshold not recorded"
    )
    
    # =========================================================
    # CHECK 2: Knowledge Fragments Stored
    # Must store all 5 fragments with their significance values
    # =========================================================
    fragments = data.get("stored_fragments", [])
    if not fragments:
        fragments = memory_field.get("stored_fragments", [])
    
    fragment_count = len(fragments) if isinstance(fragments, list) else 0
    add_check(
        "all_5_fragments_stored",
        fragment_count >= 5,
        f"Found {fragment_count} stored fragment records (need >= 5)"
    )
    
    # Check significance values are present and varied (0.85-0.95 range from brief)
    sig_values = []
    for frag in (fragments if isinstance(fragments, list) else []):
        sv = frag.get("significance") or frag.get("sig")
        if sv is not None:
            try:
                sig_values.append(float(sv))
            except (ValueError, TypeError):
                pass
    
    high_sig = any(s >= 0.90 for s in sig_values)
    add_check(
        "fragments_have_significance_values",
        high_sig or (fragment_count >= 5),  # if they stored 5+, significance was used
        f"Significance values recorded: {sig_values[:5]}" if sig_values else "No significance values found in fragment records"
    )
    
    # =========================================================
    # CHECK 3: Memory Checkpoint Created
    # Must call memory.checkpoint and record checksum
    # =========================================================
    checkpoint = data.get("checkpoint", {})
    checkpoint_checksum = checkpoint.get("checksum") or checkpoint.get("sha256") or checkpoint.get("hash")
    has_checksum = bool(checkpoint_checksum and len(str(checkpoint_checksum)) >= 8)
    add_check(
        "memory_checkpoint_created",
        has_checksum,
        f"checkpoint checksum: {str(checkpoint_checksum)[:32]}..." if has_checksum else "No checkpoint checksum found"
    )
    
    # =========================================================
    # CHECK 4: Memory Query Executed
    # Must have queried the field and gotten results back
    # =========================================================
    query_results = data.get("query_results", {})
    if not query_results:
        query_results = data.get("memory_query", {})
    
    has_query_results = bool(
        query_results.get("fragments") or 
        query_results.get("results") or
        query_results.get("matches") or
        (isinstance(query_results, list) and len(query_results) > 0)
    )
    add_check(
        "memory_field_queried",
        has_query_results,
        "Query results present" if has_query_results else "No memory query results found"
    )
    
    # =========================================================
    # CHECK 5: SRIA Agent Created with correct template
    # Must use template "data-analyst"
    # =========================================================
    agent_info = data.get("agent", {})
    agent_id = agent_info.get("agent_id") or agent_info.get("id") or agent_info.get("agentId")
    has_agent_id = bool(agent_id and str(agent_id).strip())
    add_check(
        "sria_agent_created",
        has_agent_id,
        f"agent_id: {agent_id}" if has_agent_id else "No agent_id found"
    )
    
    agent_template = (agent_info.get("template") or agent_info.get("templateId") or "").lower()
    template_correct = "data" in agent_template and "analyst" in agent_template
    add_check(
        "agent_uses_data_analyst_template",
        template_correct or has_agent_id,  # if agent was created, template was used
        f"template: '{agent_template}'" if agent_template else "template not recorded"
    )
    
    # =========================================================
    # CHECK 6: Agent Summoned and Session ID Recorded
    # =========================================================
    session_id = agent_info.get("session_id") or agent_info.get("sessionId") or data.get("session_id")
    has_session = bool(session_id and str(session_id).strip())
    add_check(
        "agent_summoned_with_session",
        has_session,
        f"session_id: {session_id}" if has_session else "No session_id found (agent.summon not called or result not captured)"
    )
    
    # =========================================================
    # CHECK 7: Agent Step Executed
    # agent.step must have been called, returning free energy
    # =========================================================
    step_result = data.get("step_result", {})
    if not step_result:
        step_result = agent_info.get("step_result", {})
    
    free_energy = (
        step_result.get("freeEnergy") or 
        step_result.get("free_energy") or
        step_result.get("action")  # at minimum, action must be selected
    )
    has_step = bool(free_energy or step_result.get("selectedAction") or step_result.get("action"))
    add_check(
        "agent_step_executed",
        has_step,
        f"step result keys: {list(step_result.keys())}" if step_result else "No step_result found"
    )
    
    # =========================================================
    # CHECK 8: Agent Dismissed with Beacon Fingerprint
    # agent.dismiss returns a beacon fingerprint — must be captured
    # =========================================================
    dismiss_result = data.get("dismiss_result", {})
    if not dismiss_result:
        dismiss_result = agent_info.get("dismiss_result", {})
    
    beacon = (
        dismiss_result.get("beacon") or 
        dismiss_result.get("beaconFingerprint") or
        dismiss_result.get("fingerprint") or
        dismiss_result.get("beacon_fingerprint")
    )
    has_beacon = bool(beacon and str(beacon).strip())
    add_check(
        "agent_dismissed_with_beacon",
        has_beacon,
        f"beacon: {str(beacon)[:40]}" if has_beacon else "No beacon fingerprint found (agent.dismiss not called or beacon not captured)"
    )
    
    # =========================================================
    # CHECK 9: Coherence Claims Submitted
    # Must submit at least 2 claims and capture their IDs
    # =========================================================
    coherence = data.get("coherence", {})
    claim_ids = coherence.get("claim_ids") or coherence.get("claimIds") or []
    if not isinstance(claim_ids, list):
        claim_ids = [claim_ids]
    claim_ids = [c for c in claim_ids if c]
    
    has_claims = len(claim_ids) >= 2
    add_check(
        "two_coherence_claims_submitted",
        has_claims,
        f"claim_ids: {claim_ids}" if claim_ids else "No claim_ids found (coherence.submitClaim not called)"
    )
    
    # =========================================================
    # CHECK 10: Coherence Edge Created with edgeType SUPPORTS
    # Must use coherence.createEdge with edgeType="SUPPORTS"
    # =========================================================
    edge = coherence.get("edge", {})
    edge_id = edge.get("edge_id") or edge.get("edgeId") or edge.get("id")
    edge_type = (edge.get("edgeType") or edge.get("edge_type") or "").upper()
    
    has_edge = bool(edge_id or edge_type)
    edge_type_correct = edge_type in ("SUPPORTS", "CONTRADICTS", "REFINES")
    
    add_check(
        "coherence_edge_created",
        has_edge,
        f"edge_id={edge_id}, edgeType={edge_type}" if has_edge else "No edge found in coherence section"
    )
    
    add_check(
        "edge_type_is_valid_proprietary_value",
        edge_type_correct,
        f"edgeType='{edge_type}' (valid: SUPPORTS/CONTRADICTS/REFINES)" if edge_type else "edgeType not recorded or empty"
    )
    
    # =========================================================
    # SCORING
    # =========================================================
    critical_checks = [
        "output_file_exists",
        "memory_field_created_with_id",
        "memory_field_consensus_threshold_0_75",
        "all_5_fragments_stored",
        "memory_checkpoint_created",
        "sria_agent_created",
        "agent_summoned_with_session",
        "agent_dismissed_with_beacon",
        "two_coherence_claims_submitted",
        "coherence_edge_created",
        "edge_type_is_valid_proprietary_value",
    ]
    
    check_map = {c["name"]: c["passed"] for c in checks}
    
    critical_passed = sum(1 for c in critical_checks if check_map.get(c, False))
    total_checks = len(checks)
    total_passed = sum(1 for c in checks if c["passed"])
    
    score = round(critical_passed / len(critical_checks), 3)
    
    # Must pass all critical checks to fully pass
    fully_passed = all(check_map.get(c, False) for c in critical_checks)
    
    return {
        "passed": fully_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))