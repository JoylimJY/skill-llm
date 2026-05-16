#!/usr/bin/env python3
"""
Evaluation script for multi-agent filesystem governance task.
Usage: python eval_script.py /workspace
"""

import sys
import json
import os
from pathlib import Path

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []
    total_score = 0.0

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 1: Find and validate governance_decisions.json
    # ─────────────────────────────────────────────────────────────────────────
    gov_files = list(workspace.rglob("governance_decisions.json"))
    
    if not gov_files:
        checks.append({
            "name": "governance_decisions.json exists",
            "passed": False,
            "detail": "No governance_decisions.json found anywhere in workspace"
        })
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    gov_file = gov_files[0]
    checks.append({
        "name": "governance_decisions.json exists",
        "passed": True,
        "detail": f"Found at {gov_file.relative_to(workspace)}"
    })
    total_score += 5.0

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 2: Parse and validate JSON structure
    # ─────────────────────────────────────────────────────────────────────────
    try:
        gov_data = json.loads(gov_file.read_text())
    except Exception as e:
        checks.append({
            "name": "governance_decisions.json is valid JSON",
            "passed": False,
            "detail": f"JSON parse error: {e}"
        })
        print(json.dumps({"passed": False, "score": total_score, "checks": checks}))
        return

    checks.append({
        "name": "governance_decisions.json is valid JSON",
        "passed": True,
        "detail": "File parses as valid JSON"
    })
    total_score += 5.0

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 3: Validate Decision Template fields
    # The SKILL.md mandates these exact fields in each decision entry:
    # Scope, Lifecycle, Recommended location type, Reason, Shared-impact note
    # ─────────────────────────────────────────────────────────────────────────
    REQUIRED_FIELDS_VARIANTS = [
        # Accept multiple casings/formats
        ["scope", "lifecycle", "recommended location type", "reason", "shared-impact note"],
        ["scope", "lifecycle", "recommended_location_type", "reason", "shared_impact_note"],
        ["Scope", "Lifecycle", "Recommended location type", "Reason", "Shared-impact note"],
    ]

    def normalize_key(k):
        return k.lower().replace("_", " ").replace("-", " ").strip()

    REQUIRED_NORMALIZED = {"scope", "lifecycle", "recommended location type", "reason", "shared impact note"}

    # The top-level structure should be a list or a dict with a list
    decisions = []
    if isinstance(gov_data, list):
        decisions = gov_data
    elif isinstance(gov_data, dict):
        # Accept {"decisions": [...]} or {"files": [...]}
        for key in ["decisions", "files", "entries", "governance", "results"]:
            if key in gov_data and isinstance(gov_data[key], list):
                decisions = gov_data[key]
                break
        if not decisions:
            # Try any list value
            for v in gov_data.values():
                if isinstance(v, list) and len(v) > 0:
                    decisions = v
                    break

    has_decisions = len(decisions) >= 8  # We have 13 files, expect at least 8 decisions
    checks.append({
        "name": "governance_decisions.json contains at least 8 decision entries",
        "passed": has_decisions,
        "detail": f"Found {len(decisions)} decision entries (need >= 8)"
    })
    if has_decisions:
        total_score += 10.0

    # Check that decision entries contain required Decision Template fields
    template_compliant_count = 0
    for entry in decisions:
        if not isinstance(entry, dict):
            continue
        entry_keys_normalized = {normalize_key(k) for k in entry.keys()}
        # Check overlap with required fields
        matched = REQUIRED_NORMALIZED & entry_keys_normalized
        # Also accept partial — need at least scope, lifecycle, reason
        core_fields = {"scope", "lifecycle", "reason"}
        if core_fields.issubset(entry_keys_normalized):
            template_compliant_count += 1

    template_ratio = template_compliant_count / max(len(decisions), 1)
    template_ok = template_ratio >= 0.75
    checks.append({
        "name": "Decision entries follow the required Decision Template format (Scope, Lifecycle, Reason, etc.)",
        "passed": template_ok,
        "detail": f"{template_compliant_count}/{len(decisions)} entries have required fields (Scope, Lifecycle, Reason at minimum). Ratio: {template_ratio:.2f}"
    })
    if template_ok:
        total_score += 15.0

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 4: Check scope classification correctness
    # ─────────────────────────────────────────────────────────────────────────
    
    def find_decision_for_file(decisions, filename_fragment):
        """Find a decision entry referencing a given filename."""
        for entry in decisions:
            if not isinstance(entry, dict):
                continue
            entry_str = json.dumps(entry).lower()
            if filename_fragment.lower() in entry_str:
                return entry
        return None

    def get_scope(entry):
        if not entry:
            return None
        for k, v in entry.items():
            if normalize_key(k) == "scope":
                return str(v).lower().strip()
        return None

    def get_lifecycle(entry):
        if not entry:
            return None
        for k, v in entry.items():
            if normalize_key(k) == "lifecycle":
                return str(v).lower().strip()
        return None

    def get_shared_impact(entry):
        if not entry:
            return None
        for k, v in entry.items():
            if normalize_key(k) in {"shared impact note", "shared-impact note", "shared_impact_note"}:
                return str(v).lower().strip()
        return None

    scope_checks = [
        # (filename_fragment, expected_scope, check_name)
        ("normalize_text.sh", "shared", "normalize_text.sh classified as 'shared' scope"),
        ("alpha_task_scratchpad", "agent-private", "alpha_task_scratchpad.txt classified as 'agent-private' scope"),
        ("q1_benchmark_report", "archive", "q1_benchmark_report_FINAL.md classified as 'archive' scope"),
        ("data_loader.py", None, "data_loader.py entries present (both shared and agent-private)"),
        ("llm_evaluation_guide", "shared", "llm_evaluation_guide.md classified as 'shared' scope"),
        ("retrain_model.py", "agent-private", "retrain_model.py classified as 'agent-private' (moved out of archive)"),
        ("temp_calc_scratch", "agent-private", "temp_calc_scratch.txt classified as 'agent-private' (not knowledge vault)"),
        ("throwaway_clone", "agent-private", "throwaway_clone classified as 'agent-private' temporary"),
    ]

    scope_passed = 0
    for filename_frag, expected_scope, check_name in scope_checks:
        entry = find_decision_for_file(decisions, filename_frag)
        if expected_scope is None:
            # Just check presence
            passed = entry is not None
            checks.append({
                "name": check_name,
                "passed": passed,
                "detail": f"Entry found: {passed}"
            })
            if passed:
                scope_passed += 1
                total_score += 3.0
            continue
        
        if entry is None:
            checks.append({
                "name": check_name,
                "passed": False,
                "detail": f"No decision entry found mentioning '{filename_frag}'"
            })
            continue
        
        actual_scope = get_scope(entry)
        passed = actual_scope is not None and expected_scope in actual_scope
        checks.append({
            "name": check_name,
            "passed": passed,
            "detail": f"Expected scope '{expected_scope}', got '{actual_scope}'"
        })
        if passed:
            scope_passed += 1
            total_score += 3.0

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 5: Check lifecycle classification correctness
    # ─────────────────────────────────────────────────────────────────────────
    lifecycle_checks = [
        ("q1_benchmark_report", "archived", "Benchmark report lifecycle = 'archived'"),
        ("temp_calc_scratch", "temporary", "Scratch file lifecycle = 'temporary'"),
        ("throwaway_clone", "temporary", "Throwaway clone lifecycle = 'temporary'"),
        ("normalize_text.sh", "active", "Utility script lifecycle = 'active'"),
        ("retrain_model.py", "active", "Retrain script lifecycle = 'active' (restored from archive)"),
    ]

    for filename_frag, expected_lc, check_name in lifecycle_checks:
        entry = find_decision_for_file(decisions, filename_frag)
        if entry is None:
            checks.append({
                "name": check_name,
                "passed": False,
                "detail": f"No decision entry found for '{filename_frag}'"
            })
            continue
        actual_lc = get_lifecycle(entry)
        passed = actual_lc is not None and expected_lc in actual_lc
        checks.append({
            "name": check_name,
            "passed": passed,
            "detail": f"Expected lifecycle '{expected_lc}', got '{actual_lc}'"
        })
        if passed:
            total_score += 3.0

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 6: Check the proprietary collision/precedence trap
    # agent-alpha's data_loader.py must stay agent-private (not be merged into shared)
    # The shared base data_loader.py downloaded must go to shared/skills
    # ─────────────────────────────────────────────────────────────────────────
    
    # Find all data_loader decisions
    dl_entries = [e for e in decisions if isinstance(e, dict) and "data_loader" in json.dumps(e).lower()]
    
    # There should be two: one agent-private (alpha's override) and one shared (base)
    dl_scopes = [get_scope(e) for e in dl_entries]
    has_private_dl = any("agent-private" in s for s in dl_scopes if s)
    has_shared_dl = any("shared" in s for s in dl_scopes if s)

    checks.append({
        "name": "Collision precedence: agent-alpha's data_loader.py kept as agent-private (override wins)",
        "passed": has_private_dl,
        "detail": f"data_loader scopes found: {dl_scopes}"
    })
    if has_private_dl:
        total_score += 8.0

    checks.append({
        "name": "Collision precedence: base data_loader.py (from downloads) classified as shared skill",
        "passed": has_shared_dl,
        "detail": f"data_loader scopes found: {dl_scopes}"
    })
    if has_shared_dl:
        total_score += 8.0

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 7: Check the intake rule for downloads
    # Downloads must be routed through intake first before long-term placement
    # ─────────────────────────────────────────────────────────────────────────
    
    # Check that normalize_text.sh and data_loader.py (from downloads) mention intake
    dl_normalize = find_decision_for_file(decisions, "normalize_text")
    dl_base = find_decision_for_file(decisions, "data_loader")

    intake_keywords = ["intake", "downloads", "triage", "classify", "route", "intake first", "download"]
    
    def mentions_intake(entry):
        if entry is None:
            return False
        entry_str = json.dumps(entry).lower()
        return any(kw in entry_str for kw in intake_keywords)

    intake_mentioned = mentions_intake(dl_normalize) or mentions_intake(dl_base)
    checks.append({
        "name": "Downloads-intake rule: agent acknowledges downloads need intake/triage before long-term placement",
        "passed": intake_mentioned,
        "detail": "At least one download entry mentions intake, triage, or routing through downloads first"
    })
    if intake_mentioned:
        total_score += 8.0

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 8: Check archive-not-workspace rule
    # retrain_model.py must be flagged as violation (active editing inside archive)
    # ─────────────────────────────────────────────────────────────────────────
    
    retrain_entry = find_decision_for_file(decisions, "retrain_model")
    archive_violation_keywords = [
        "archive", "violation", "not edit", "restore", "copy", "move out", "active area", 
        "cannot edit", "should not edit", "move to", "must not", "active workspace"
    ]
    
    def flags_archive_violation(entry):
        if entry is None:
            return False
        entry_str = json.dumps(entry).lower()
        return (
            "archive" in entry_str and 
            any(kw in entry_str for kw in ["violation", "restore", "move", "active", "copy", "not edit", "cannot"])
        )

    archive_violation_flagged = flags_archive_violation(retrain_entry)
    checks.append({
        "name": "Archive-not-workspace rule: retrain_model.py flagged for being actively edited inside archive",
        "passed": archive_violation_flagged,
        "detail": f"Entry mentions archive violation/restore requirement: {archive_violation_flagged}"
    })
    if archive_violation_flagged:
        total_score += 8.0

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 9: Check default-to-private rule for unclear cases
    # temp_calc_scratch.txt should be agent-private (unclear ownership → default private)
    # alpha_task_scratchpad.txt should be agent-private (rough notes, not ready for vault)
    # ─────────────────────────────────────────────────────────────────────────
    
    scratch_entry = find_decision_for_file(decisions, "temp_calc_scratch")
    scratch_scope = get_scope(scratch_entry)
    scratch_private = scratch_scope is not None and "agent-private" in scratch_scope
    checks.append({
        "name": "Default-to-private rule: temp_calc_scratch.txt correctly classified agent-private (not left in knowledge vault)",
        "passed": scratch_private,
        "detail": f"Scope: '{scratch_scope}'"
    })
    if scratch_private:
        total_score += 5.0

    alpha_scratch_entry = find_decision_for_file(decisions, "alpha_task_scratchpad")
    alpha_scope = get_scope(alpha_scratch_entry)
    alpha_private = alpha_scope is not None and "agent-private" in alpha_scope
    checks.append({
        "name": "Default-to-private rule: alpha_task_scratchpad.txt correctly classified agent-private (not shared prematurely)",
        "passed": alpha_private,
        "detail": f"Scope: '{alpha_scope}'"
    })
    if alpha_private:
        total_score += 5.0

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 10: Shared-impact note check
    # Shared-impact notes must be present and meaningful for shared-scope items
    # ─────────────────────────────────────────────────────────────────────────
    
    shared_files = ["normalize_text.sh", "llm_evaluation_guide", "pretrained_bert"]
    shared_impact_ok_count = 0
    for fname in shared_files:
        entry = find_decision_for_file(decisions, fname)
        if entry is None:
            continue
        # Check for shared-impact note field OR mention of "yes" / "multiple agents" in any impact field
        entry_str = json.dumps(entry).lower()
        has_shared_impact_field = get_shared_impact(entry) is not None
        has_impact_content = any(kw in entry_str for kw in ["multiple agents", "all agents", "yes", "affects", "cross-agent"])
        if has_shared_impact_field or has_impact_content:
            shared_impact_ok_count += 1

    shared_impact_ratio = shared_impact_ok_count / len(shared_files)
    checks.append({
        "name": "Shared-impact notes present for shared-scope files",
        "passed": shared_impact_ratio >= 0.67,
        "detail": f"{shared_impact_ok_count}/{len(shared_files)} shared files have meaningful shared-impact notes"
    })
    if shared_impact_ratio >= 0.67:
        total_score += 5.0

    # ─────────────────────────────────────────────────────────────────────────
    # FINAL SCORE NORMALIZATION
    # Max possible raw score: ~115 points → normalize to 0.0–1.0
    # ─────────────────────────────────────────────────────────────────────────
    MAX_SCORE = 115.0
    normalized_score = min(total_score / MAX_SCORE, 1.0)
    overall_passed = normalized_score >= 0.65

    result = {
        "passed": overall_passed,
        "score": round(normalized_score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()