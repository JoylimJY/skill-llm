import sys
import json
import subprocess
import os
from pathlib import Path

def run_mp_command(tool_name, params=None):
    """Run a memory-palace command and return parsed JSON result."""
    cmd = ["npx", f"memory-palace:{tool_name}"]
    if params:
        cmd.append(json.dumps(params))
    env = os.environ.copy()
    env["MEMORY_PALACE_DATA_DIR"] = "/data/agent-memory-palace"
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)
        output = result.stdout.strip()
        if output:
            return json.loads(output)
        return None
    except Exception as e:
        return None

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    
    # ===== CHECK 1: Report file exists =====
    report_path = None
    for p in Path(workspace).rglob("knowledge_base_report.json"):
        report_path = p
        break
    
    check1_passed = report_path is not None
    checks.append({
        "name": "report_file_exists",
        "passed": check1_passed,
        "detail": f"Found report at {report_path}" if check1_passed else "knowledge_base_report.json not found anywhere in workspace"
    })
    
    report_data = {}
    if check1_passed:
        try:
            with open(report_path) as f:
                report_data = json.load(f)
        except Exception as e:
            checks.append({"name": "report_parseable", "passed": False, "detail": str(e)})
            report_data = {}

    # ===== CHECK 2: Report has required sections =====
    required_keys = ["stats", "frequently_accessed", "verified_experiences", "unverified_experiences"]
    missing_keys = [k for k in required_keys if k not in report_data]
    checks.append({
        "name": "report_has_required_sections",
        "passed": len(missing_keys) == 0,
        "detail": f"Missing keys: {missing_keys}" if missing_keys else "All required sections present"
    })

    # ===== CHECK 3: Stats section is valid =====
    stats = report_data.get("stats", {})
    stats_valid = isinstance(stats, dict) and ("total" in stats or "totalCount" in stats or "count" in stats or len(stats) > 0)
    checks.append({
        "name": "stats_section_valid",
        "passed": stats_valid,
        "detail": f"Stats keys: {list(stats.keys())}" if stats else "Stats section is empty or missing"
    })

    # ===== CHECK 4: Memories were actually written - verify via memory_palace_list =====
    try:
        all_memories = run_mp_command("memory_palace_list", {"limit": 100})
        if all_memories is None:
            all_memories = []
        if isinstance(all_memories, dict):
            all_memories = all_memories.get("memories", all_memories.get("items", []))
        
        # Should have at least 5 memories (3 facts + 2 preferences + decisions)
        memory_count = len(all_memories) if isinstance(all_memories, list) else 0
        checks.append({
            "name": "sufficient_memories_written",
            "passed": memory_count >= 5,
            "detail": f"Found {memory_count} memories in storage (expected >= 5)"
        })
    except Exception as e:
        checks.append({"name": "sufficient_memories_written", "passed": False, "detail": str(e)})
        all_memories = []

    # ===== CHECK 5: Preferences stored in 'preferences' location =====
    try:
        pref_memories = run_mp_command("memory_palace_list", {"location": "preferences", "limit": 50})
        if isinstance(pref_memories, dict):
            pref_memories = pref_memories.get("memories", pref_memories.get("items", []))
        pref_count = len(pref_memories) if isinstance(pref_memories, list) else 0
        checks.append({
            "name": "preferences_stored_in_correct_location",
            "passed": pref_count >= 2,
            "detail": f"Found {pref_count} memories in 'preferences' location (expected >= 2)"
        })
    except Exception as e:
        checks.append({"name": "preferences_stored_in_correct_location", "passed": False, "detail": str(e)})

    # ===== CHECK 6: High-importance memories (importance >= 0.7) =====
    try:
        high_importance_count = 0
        if isinstance(all_memories, list):
            for m in all_memories:
                imp = m.get("importance", 0)
                if isinstance(imp, (int, float)) and imp >= 0.7:
                    high_importance_count += 1
        checks.append({
            "name": "high_importance_memories_exist",
            "passed": high_importance_count >= 3,
            "detail": f"Found {high_importance_count} memories with importance >= 0.7 (expected >= 3)"
        })
    except Exception as e:
        checks.append({"name": "high_importance_memories_exist", "passed": False, "detail": str(e)})

    # ===== CHECK 7: Experiences recorded =====
    try:
        experiences = run_mp_command("memory_palace_get_experiences", {})
        if isinstance(experiences, dict):
            experiences = experiences.get("experiences", experiences.get("items", []))
        exp_count = len(experiences) if isinstance(experiences, list) else 0
        checks.append({
            "name": "experiences_recorded",
            "passed": exp_count >= 3,
            "detail": f"Found {exp_count} experiences (expected 3: L001, L002, L003)"
        })
    except Exception as e:
        checks.append({"name": "experiences_recorded", "passed": False, "detail": str(e)})
        experiences = []

    # ===== CHECK 8: CRITICAL - Exactly verified experiences (2+ verifications = verified) =====
    # L001 and L002 have verify_count=2, L003 has verify_count=1
    # Only L001 and L002 should be "verified"
    try:
        verified_exps = run_mp_command("memory_palace_get_experiences", {"verified": True})
        if isinstance(verified_exps, dict):
            verified_exps = verified_exps.get("experiences", verified_exps.get("items", []))
        verified_count = len(verified_exps) if isinstance(verified_exps, list) else 0
        
        # Check report's verified_experiences matches
        report_verified = report_data.get("verified_experiences", [])
        report_verified_count = len(report_verified) if isinstance(report_verified, list) else 0
        
        # L001 (PostgreSQL) and L002 (client sync) should be verified
        # L003 (scope creep) should NOT be verified
        verified_passed = verified_count >= 2
        checks.append({
            "name": "correct_experiences_verified_2plus_rule",
            "passed": verified_passed,
            "detail": f"Found {verified_count} verified experiences (expected 2 with 2+ positive verifications; L003 with only 1 verification should remain unverified)"
        })
    except Exception as e:
        checks.append({"name": "correct_experiences_verified_2plus_rule", "passed": False, "detail": str(e)})
        verified_count = 0

    # ===== CHECK 9: L003 is NOT verified (the proprietary trap) =====
    try:
        verified_exps_check = run_mp_command("memory_palace_get_experiences", {"verified": True})
        if isinstance(verified_exps_check, dict):
            verified_exps_check = verified_exps_check.get("experiences", verified_exps_check.get("items", []))
        
        l003_verified = False
        if isinstance(verified_exps_check, list):
            for exp in verified_exps_check:
                content = exp.get("content", "").lower()
                if "zeus" in content or "scope creep" in content or "change request" in content:
                    l003_verified = True
                    break
        
        checks.append({
            "name": "l003_not_verified_requires_2plus",
            "passed": not l003_verified,
            "detail": "L003 (scope creep lesson) correctly NOT verified (only 1 verification < required 2)" if not l003_verified 
                      else "FAIL: L003 was incorrectly marked as verified despite only 1 verification (must require 2+ per SKILL.md)"
        })
    except Exception as e:
        checks.append({"name": "l003_not_verified_requires_2plus", "passed": False, "detail": str(e)})

    # ===== CHECK 10: Unverified experiences in report =====
    try:
        report_unverified = report_data.get("unverified_experiences", [])
        has_unverified_in_report = isinstance(report_unverified, list) and len(report_unverified) >= 1
        checks.append({
            "name": "unverified_experiences_in_report",
            "passed": has_unverified_in_report,
            "detail": f"Report has {len(report_unverified) if isinstance(report_unverified, list) else 'N/A'} unverified experiences (L003 should be here)"
        })
    except Exception as e:
        checks.append({"name": "unverified_experiences_in_report", "passed": False, "detail": str(e)})

    # ===== CHECK 11: Access tracking - frequently_accessed in report =====
    try:
        freq = report_data.get("frequently_accessed", [])
        freq_valid = isinstance(freq, list) and len(freq) >= 1
        checks.append({
            "name": "frequently_accessed_in_report",
            "passed": freq_valid,
            "detail": f"frequently_accessed has {len(freq) if isinstance(freq, list) else 0} entries (expected top 5)"
        })
    except Exception as e:
        checks.append({"name": "frequently_accessed_in_report", "passed": False, "detail": str(e)})

    # ===== CHECK 12: record_access used for simulated access =====
    # Verify via memory_palace_get_frequently_accessed that some memories have accessCount > 1
    try:
        freq_accessed = run_mp_command("memory_palace_get_frequently_accessed", {"limit": 5})
        if isinstance(freq_accessed, dict):
            freq_accessed = freq_accessed.get("memories", freq_accessed.get("items", []))
        
        has_multiple_accesses = False
        if isinstance(freq_accessed, list):
            for m in freq_accessed:
                access_count = m.get("accessCount", m.get("access_count", 0))
                if isinstance(access_count, (int, float)) and access_count >= 2:
                    has_multiple_accesses = True
                    break
        
        checks.append({
            "name": "access_tracking_simulated",
            "passed": has_multiple_accesses,
            "detail": "At least one memory has accessCount >= 2 indicating record_access was used for simulation" if has_multiple_accesses 
                      else "No memory shows multiple accesses; record_access may not have been called with ids array"
        })
    except Exception as e:
        checks.append({"name": "access_tracking_simulated", "passed": False, "detail": str(e)})

    # ===== CHECK 13: Memory types are correct (fact/decision/preference) =====
    try:
        decision_memories = run_mp_command("memory_palace_list", {"type": "decision", "limit": 50})
        if isinstance(decision_memories, dict):
            decision_memories = decision_memories.get("memories", decision_memories.get("items", []))
        decision_count = len(decision_memories) if isinstance(decision_memories, list) else 0
        checks.append({
            "name": "decision_type_memories_stored",
            "passed": decision_count >= 1,
            "detail": f"Found {decision_count} memories with type='decision' (code review SLA and TypeScript standard should be decisions)"
        })
    except Exception as e:
        checks.append({"name": "decision_type_memories_stored", "passed": False, "detail": str(e)})

    # ===== CHECK 14: Experiences have correct categories =====
    try:
        dev_exps = run_mp_command("memory_palace_get_experiences", {"category": "development"})
        if isinstance(dev_exps, dict):
            dev_exps = dev_exps.get("experiences", dev_exps.get("items", []))
        comm_exps = run_mp_command("memory_palace_get_experiences", {"category": "communication"})
        if isinstance(comm_exps, dict):
            comm_exps = comm_exps.get("experiences", comm_exps.get("items", []))
        
        dev_count = len(dev_exps) if isinstance(dev_exps, list) else 0
        comm_count = len(comm_exps) if isinstance(comm_exps, list) else 0
        
        checks.append({
            "name": "experiences_have_correct_categories",
            "passed": dev_count >= 1 and comm_count >= 1,
            "detail": f"development category: {dev_count} exp(s), communication category: {comm_count} exp(s)"
        })
    except Exception as e:
        checks.append({"name": "experiences_have_correct_categories", "passed": False, "detail": str(e)})

    # ===== SCORING =====
    critical_checks = [
        "report_file_exists",
        "correct_experiences_verified_2plus_rule",
        "l003_not_verified_requires_2plus",
        "experiences_recorded",
        "sufficient_memories_written",
    ]
    
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    
    # Critical checks must all pass for overall pass
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)
    overall_pass = critical_passed and passed_count >= (total * 0.7)
    
    score = passed_count / total if total > 0 else 0.0
    
    result = {
        "passed": overall_pass,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()