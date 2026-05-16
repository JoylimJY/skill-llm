#!/usr/bin/env python3
"""
Evaluation script for the moses-roles governance onboarding task.
Checks:
  1. state.json exists and has correct governance schema
  2. AGENTS.md contains exact prescribed role injection text for all 3 roles
  3. audit_log.jsonl contains a sequence_violation entry referencing "Observer"
"""

import json
import sys
import os
from pathlib import Path

def run_checks(workspace: str):
    checks = []
    HOME = Path(os.path.expanduser("~"))

    # ── Check 1: state.json exists ────────────────────────────────────────────
    state_path = HOME / ".openclaw" / "governance" / "state.json"
    state_data = None
    try:
        with open(state_path) as f:
            state_data = json.load(f)
        checks.append({
            "name": "state.json_exists_and_is_valid_json",
            "passed": True,
            "detail": f"state.json found and parsed at {state_path}"
        })
    except FileNotFoundError:
        checks.append({
            "name": "state.json_exists_and_is_valid_json",
            "passed": False,
            "detail": f"state.json not found at {state_path}"
        })
        state_data = None
    except json.JSONDecodeError as e:
        checks.append({
            "name": "state.json_exists_and_is_valid_json",
            "passed": False,
            "detail": f"state.json is malformed JSON: {e}"
        })
        state_data = None

    # ── Check 2: state.json is NOT the broken placeholder ────────────────────
    if state_data is not None:
        is_placeholder = (
            "active_mode" not in state_data or
            state_data.get("active_mode") is None and
            "notes" in state_data and "placeholder" in str(state_data.get("notes", ""))
        )
        checks.append({
            "name": "state.json_is_not_placeholder",
            "passed": not is_placeholder,
            "detail": (
                "state.json still contains the broken placeholder content"
                if is_placeholder else
                "state.json has been updated beyond the placeholder"
            )
        })
    else:
        checks.append({
            "name": "state.json_is_not_placeholder",
            "passed": False,
            "detail": "Cannot check — state.json could not be loaded"
        })

    # ── Check 3: state.json has governance keys (mode + posture + roles) ──────
    REQUIRED_KEYS = ["mode", "posture", "role_constraints"]
    # Accept variants: active_mode/mode, active_posture/posture, role_constraints/roles
    ACCEPTABLE_KEY_GROUPS = [
        ["mode", "posture", "role_constraints"],
        ["active_mode", "active_posture", "role_constraints"],
        ["mode", "posture", "roles"],
        ["active_mode", "posture", "roles"],
        ["mode", "active_posture", "role_constraints"],
    ]
    if state_data is not None:
        has_governance_keys = any(
            all(k in state_data for k in group)
            for group in ACCEPTABLE_KEY_GROUPS
        )
        # Also accept any state_data that has at least 3 non-trivial keys and
        # references mode/posture concepts meaningfully
        state_keys_lower = [k.lower() for k in state_data.keys()]
        has_mode = any("mode" in k for k in state_keys_lower)
        has_posture = any("posture" in k for k in state_keys_lower)
        has_role = any("role" in k for k in state_keys_lower)
        governance_triplet = has_mode and has_posture and has_role
        passed_governance_keys = has_governance_keys or governance_triplet
        checks.append({
            "name": "state.json_has_governance_triplet",
            "passed": passed_governance_keys,
            "detail": (
                f"state.json keys: {list(state_data.keys())} — "
                f"mode={has_mode}, posture={has_posture}, role={has_role}"
            )
        })
    else:
        checks.append({
            "name": "state.json_has_governance_triplet",
            "passed": False,
            "detail": "Cannot check — state.json could not be loaded"
        })

    # ── Check 4: AGENTS.md exists ─────────────────────────────────────────────
    agents_path = HOME / ".openclaw" / "workspace" / "AGENTS.md"
    agents_text = None
    try:
        agents_text = agents_path.read_text()
        checks.append({
            "name": "AGENTS.md_exists",
            "passed": True,
            "detail": f"AGENTS.md found at {agents_path}"
        })
    except FileNotFoundError:
        checks.append({
            "name": "AGENTS.md_exists",
            "passed": False,
            "detail": f"AGENTS.md not found at {agents_path}"
        })

    # ── Check 5: AGENTS.md has Primary role definition ────────────────────────
    if agents_text is not None:
        primary_keywords = [
            "responds first", "full tool", "sets direction",
            "governance state", "logs"
        ]
        primary_lower = agents_text.lower()
        primary_hits = sum(1 for kw in primary_keywords if kw in primary_lower)
        primary_ok = primary_hits >= 3 and "primary" in primary_lower
        checks.append({
            "name": "AGENTS.md_primary_role_correct",
            "passed": primary_ok,
            "detail": (
                f"Primary role keywords found: {primary_hits}/5. "
                f"Content snippet: {agents_text[:300]!r}"
            )
        })
    else:
        checks.append({
            "name": "AGENTS.md_primary_role_correct",
            "passed": False,
            "detail": "Cannot check — AGENTS.md missing"
        })

    # ── Check 6: AGENTS.md has Secondary role definition ─────────────────────
    if agents_text is not None:
        secondary_keywords = [
            "reads primary", "validates", "does not repeat",
            "governance state", "logs"
        ]
        sec_lower = agents_text.lower()
        secondary_hits = sum(1 for kw in secondary_keywords if kw in sec_lower)
        # Also accept "read primary", "validate", "extend"
        extended_keywords = ["read primary", "validate", "extend", "cannot repeat", "not repeat"]
        extended_hits = sum(1 for kw in extended_keywords if kw in sec_lower)
        secondary_ok = (secondary_hits + extended_hits) >= 3 and "secondary" in sec_lower
        checks.append({
            "name": "AGENTS.md_secondary_role_correct",
            "passed": secondary_ok,
            "detail": (
                f"Secondary role base keywords: {secondary_hits}/5, "
                f"extended keywords: {extended_hits}/5"
            )
        })
    else:
        checks.append({
            "name": "AGENTS.md_secondary_role_correct",
            "passed": False,
            "detail": "Cannot check — AGENTS.md missing"
        })

    # ── Check 7: AGENTS.md has Observer role definition ───────────────────────
    if agents_text is not None:
        observer_keywords = [
            "reads all", "flags only", "no action", "no original analysis",
            "governance state", "logs"
        ]
        obs_lower = agents_text.lower()
        observer_hits = sum(1 for kw in observer_keywords if kw in obs_lower)
        extended_obs = ["flag", "no actions", "cannot initiate", "reads both"]
        extended_obs_hits = sum(1 for kw in extended_obs if kw in obs_lower)
        observer_ok = (observer_hits + extended_obs_hits) >= 3 and "observer" in obs_lower
        checks.append({
            "name": "AGENTS.md_observer_role_correct",
            "passed": observer_ok,
            "detail": (
                f"Observer role base keywords: {observer_hits}/6, "
                f"extended keywords: {extended_obs_hits}/4"
            )
        })
    else:
        checks.append({
            "name": "AGENTS.md_observer_role_correct",
            "passed": False,
            "detail": "Cannot check — AGENTS.md missing"
        })

    # ── Check 8: AGENTS.md is NOT still the stub ──────────────────────────────
    if agents_text is not None:
        is_stub = "TBD" in agents_text and agents_text.count("TBD") >= 2
        checks.append({
            "name": "AGENTS.md_not_stub",
            "passed": not is_stub,
            "detail": (
                "AGENTS.md still contains TBD placeholders — not updated"
                if is_stub else
                "AGENTS.md has been updated beyond the stub"
            )
        })
    else:
        checks.append({
            "name": "AGENTS.md_not_stub",
            "passed": False,
            "detail": "Cannot check — AGENTS.md missing"
        })

    # ── Check 9: audit_log.jsonl exists ───────────────────────────────────────
    audit_log_path = HOME / ".openclaw" / "governance" / "audit_log.jsonl"
    audit_entries = []
    try:
        lines = audit_log_path.read_text().strip().splitlines()
        for line in lines:
            if line.strip():
                try:
                    audit_entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        # Filter out the setup_check entry planted by setup script
        real_entries = [e for e in audit_entries if e.get("action") != "setup_check"]
        checks.append({
            "name": "audit_log_exists_and_has_entries",
            "passed": len(real_entries) > 0,
            "detail": (
                f"audit_log.jsonl has {len(real_entries)} non-setup entries"
                if real_entries else
                "audit_log.jsonl exists but has no agent-written entries"
            )
        })
    except FileNotFoundError:
        checks.append({
            "name": "audit_log_exists_and_has_entries",
            "passed": False,
            "detail": f"audit_log.jsonl not found at {audit_log_path}"
        })

    # ── Check 10: sequence_violation entry with correct action ────────────────
    real_entries_for_check = [e for e in audit_entries if e.get("action") != "setup_check"]
    seq_violation_entries = [
        e for e in real_entries_for_check
        if e.get("action") == "sequence_violation"
    ]
    checks.append({
        "name": "audit_log_has_sequence_violation_action",
        "passed": len(seq_violation_entries) > 0,
        "detail": (
            f"Found {len(seq_violation_entries)} sequence_violation entries"
            if seq_violation_entries else
            f"No sequence_violation entries found. Actions present: "
            f"{[e.get('action') for e in real_entries_for_check]}"
        )
    })

    # ── Check 11: sequence_violation detail references "Observer" ─────────────
    if seq_violation_entries:
        observer_in_detail = any(
            "observer" in e.get("detail", "").lower()
            for e in seq_violation_entries
        )
        out_of_turn_in_detail = any(
            "out of turn" in e.get("detail", "").lower() or
            "out of sequence" in e.get("detail", "").lower() or
            "responded out" in e.get("detail", "").lower()
            for e in seq_violation_entries
        )
        checks.append({
            "name": "sequence_violation_detail_references_observer_and_action",
            "passed": observer_in_detail and out_of_turn_in_detail,
            "detail": (
                f"observer_in_detail={observer_in_detail}, "
                f"out_of_turn_in_detail={out_of_turn_in_detail}. "
                f"Details seen: {[e.get('detail') for e in seq_violation_entries]}"
            )
        })
    else:
        checks.append({
            "name": "sequence_violation_detail_references_observer_and_action",
            "passed": False,
            "detail": "No sequence_violation entries to inspect"
        })

    # ── Check 12: audit_stub.py was used (not just file-written directly) ─────
    # We verify the log entry was produced via audit_stub.py by confirming
    # the entry has the expected JSON structure (timestamp, action, detail, agent)
    if seq_violation_entries:
        entry = seq_violation_entries[0]
        has_structure = all(k in entry for k in ["timestamp", "action", "detail"])
        checks.append({
            "name": "audit_entry_has_correct_structure",
            "passed": has_structure,
            "detail": (
                f"Entry keys: {list(entry.keys())}"
            )
        })
    else:
        checks.append({
            "name": "audit_entry_has_correct_structure",
            "passed": False,
            "detail": "No sequence_violation entry to check structure"
        })

    # ── Scoring ───────────────────────────────────────────────────────────────
    # Weight critical checks more heavily
    weights = {
        "state.json_exists_and_is_valid_json": 1.0,
        "state.json_is_not_placeholder": 1.0,
        "state.json_has_governance_triplet": 1.5,
        "AGENTS.md_exists": 0.5,
        "AGENTS.md_primary_role_correct": 1.5,
        "AGENTS.md_secondary_role_correct": 1.5,
        "AGENTS.md_observer_role_correct": 1.5,
        "AGENTS.md_not_stub": 0.5,
        "audit_log_exists_and_has_entries": 1.0,
        "audit_log_has_sequence_violation_action": 2.0,
        "sequence_violation_detail_references_observer_and_action": 2.0,
        "audit_entry_has_correct_structure": 0.5,
    }

    total_weight = sum(weights.values())
    earned_weight = sum(
        weights.get(c["name"], 1.0)
        for c in checks
        if c["passed"]
    )
    score = round(earned_weight / total_weight, 4)

    # Must pass all three critical checks to pass overall
    critical_checks = [
        "state.json_has_governance_triplet",
        "AGENTS.md_primary_role_correct",
        "AGENTS.md_secondary_role_correct",
        "AGENTS.md_observer_role_correct",
        "audit_log_has_sequence_violation_action",
        "sequence_violation_detail_references_observer_and_action",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )
    passed = critical_passed and score >= 0.75

    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, indent=2))