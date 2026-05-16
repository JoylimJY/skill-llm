import sys
import json
import os
from pathlib import Path

def load_output(workspace):
    """Find routing_decisions.json anywhere in workspace."""
    candidates = list(Path(workspace).rglob("routing_decisions.json"))
    if not candidates:
        return None, "routing_decisions.json not found anywhere in workspace"
    # prefer root-level
    for c in candidates:
        if c.parent == Path(workspace):
            return c, None
    return candidates[0], None

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def main():
    workspace = sys.argv[1]
    checks = []
    total = 0
    passed_count = 0

    # ── Load output file ──────────────────────────────────────────────────────
    file_path, err = load_output(workspace)
    if not file_path:
        checks.append(check("output_file_exists", False, err))
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    try:
        with open(file_path) as f:
            decisions = json.load(f)
    except Exception as e:
        checks.append(check("output_file_valid_json", False, str(e)))
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append(check("output_file_exists_and_valid_json", True, str(file_path)))

    # Build a lookup by message id
    if isinstance(decisions, list):
        by_id = {d.get("id"): d for d in decisions if isinstance(d, dict)}
    elif isinstance(decisions, dict):
        by_id = decisions
    else:
        checks.append(check("output_structure", False, "Expected a list or dict of routing decisions"))
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # ── Helper ────────────────────────────────────────────────────────────────
    def get(msg_id):
        return by_id.get(msg_id, {})

    def field_contains(d, field, *keywords):
        """Case-insensitive substring check on a string or list field."""
        val = d.get(field, "")
        if isinstance(val, list):
            val = " ".join(str(v) for v in val)
        val = str(val).lower()
        return all(kw.lower() in val for kw in keywords)

    def field_matches_any(d, field, *keywords):
        val = d.get(field, "")
        if isinstance(val, list):
            val = " ".join(str(v) for v in val)
        val = str(val).lower()
        return any(kw.lower() in val for kw in keywords)

    # ══════════════════════════════════════════════════════════════════════════
    # msg_001: [ISO: project-alpha][NOMEM]
    # Expected: scope=isolated/fresh, topic=project-alpha, memory=no-store
    # ══════════════════════════════════════════════════════════════════════════
    d = get("msg_001")
    c1a = bool(d) and field_matches_any(d, "scope_mode", "iso", "isolated", "fresh")
    checks.append(check("msg_001_iso_scope", c1a,
        f"msg_001 should have ISO/isolated scope. Got: {d.get('scope_mode','')}"))

    c1b = bool(d) and field_matches_any(d, "memory_intent", "nomem", "no", "no-store", "no_store", "none", "false")
    checks.append(check("msg_001_nomem", c1b,
        f"msg_001 should have NOMEM memory intent. Got: {d.get('memory_intent','')}"))

    c1c = bool(d) and ("project-alpha" in str(d).lower() or "project_alpha" in str(d).lower())
    checks.append(check("msg_001_topic", c1c,
        f"msg_001 topic should reference project-alpha. Got: {d}"))

    # ══════════════════════════════════════════════════════════════════════════
    # msg_002: [GLOBAL][REM]
    # Expected: cross-topic reuse allowed, persist preference, call out reuse
    # ══════════════════════════════════════════════════════════════════════════
    d = get("msg_002")
    c2a = bool(d) and field_matches_any(d, "scope_mode", "global")
    checks.append(check("msg_002_global_scope", c2a,
        f"msg_002 should have GLOBAL scope. Got: {d.get('scope_mode','')}"))

    c2b = bool(d) and field_matches_any(d, "memory_intent", "rem", "remember", "persist", "store", "true")
    checks.append(check("msg_002_rem_memory", c2b,
        f"msg_002 should have REM/persist memory intent. Got: {d.get('memory_intent','')}"))

    # GLOBAL must note what was reused or that reuse is allowed (call-out requirement)
    c2c = bool(d) and field_matches_any(d, "notes", "reuse", "cross", "global", "called_out", "callout")
    if not c2c:
        # also check any field for reuse callout
        full_str = str(d).lower()
        c2c = "reuse" in full_str or "cross-topic" in full_str or "cross_topic" in full_str
    checks.append(check("msg_002_global_reuse_callout", c2c,
        f"msg_002 [GLOBAL] must call out cross-topic reuse. Got: {d}"))

    # ══════════════════════════════════════════════════════════════════════════
    # msg_003: [SCOPE: marketing]
    # Expected: scoped to marketing, no cross-topic mixing
    # ══════════════════════════════════════════════════════════════════════════
    d = get("msg_003")
    c3a = bool(d) and field_matches_any(d, "scope_mode", "scope", "scoped")
    checks.append(check("msg_003_scope_mode", c3a,
        f"msg_003 should have SCOPE mode. Got: {d.get('scope_mode','')}"))

    c3b = bool(d) and "marketing" in str(d).lower()
    checks.append(check("msg_003_scope_topic", c3b,
        f"msg_003 topic should be 'marketing'. Got: {d}"))

    # ══════════════════════════════════════════════════════════════════════════
    # msg_004: [ISO: legal][GLOBAL]  ← conflict: ISO vs GLOBAL
    # PROPRIETARY TRAP: last-tag-wins → GLOBAL wins
    # ══════════════════════════════════════════════════════════════════════════
    d = get("msg_004")
    c4a = bool(d) and field_matches_any(d, "scope_mode", "global")
    checks.append(check("msg_004_conflict_last_tag_wins_global", c4a,
        f"msg_004 [ISO]+[GLOBAL]: last tag (GLOBAL) should win. Got: {d.get('scope_mode','')}"))

    c4b = bool(d) and ("conflict" in str(d).lower() or "last" in str(d).lower() or "override" in str(d).lower()
                        or "wins" in str(d).lower() or "resolved" in str(d).lower())
    checks.append(check("msg_004_conflict_noted", c4b,
        f"msg_004 conflict between ISO and GLOBAL should be noted in decision. Got: {d}"))

    # ══════════════════════════════════════════════════════════════════════════
    # msg_005: [REM][NOMEM]  ← conflict: REM vs NOMEM
    # PROPRIETARY TRAP: last-tag-wins → NOMEM wins
    # ══════════════════════════════════════════════════════════════════════════
    d = get("msg_005")
    c5a = bool(d) and field_matches_any(d, "memory_intent", "nomem", "no", "no-store", "no_store", "none", "false")
    checks.append(check("msg_005_conflict_last_tag_wins_nomem", c5a,
        f"msg_005 [REM]+[NOMEM]: last tag (NOMEM) should win. Got: {d.get('memory_intent','')}"))

    c5b = bool(d) and ("conflict" in str(d).lower() or "last" in str(d).lower() or "override" in str(d).lower()
                        or "wins" in str(d).lower() or "resolved" in str(d).lower())
    checks.append(check("msg_005_conflict_noted", c5b,
        f"msg_005 conflict between REM and NOMEM should be noted. Got: {d}"))

    # ══════════════════════════════════════════════════════════════════════════
    # msg_006: No tags at all
    # Expected: default behavior → conservative, no cross-topic mixing
    # ══════════════════════════════════════════════════════════════════════════
    d = get("msg_006")
    c6 = bool(d) and field_matches_any(d, "scope_mode", "default", "none", "no_tag", "untagged", "conservative")
    checks.append(check("msg_006_no_tags_default_behavior", c6,
        f"msg_006 has no tags → default conservative behavior. Got: {d.get('scope_mode','')}"))

    # ══════════════════════════════════════════════════════════════════════════
    # msg_007: [Isolated Context: backend-infra]  ← long-form alias
    # PROPRIETARY TRAP: must be treated identically to [ISO: backend-infra]
    # ══════════════════════════════════════════════════════════════════════════
    d = get("msg_007")
    c7a = bool(d) and field_matches_any(d, "scope_mode", "iso", "isolated", "fresh")
    checks.append(check("msg_007_long_form_iso_alias", c7a,
        f"msg_007 [Isolated Context:] long-form alias must equal ISO. Got: {d.get('scope_mode','')}"))

    c7b = bool(d) and ("backend" in str(d).lower() or "backend-infra" in str(d).lower() or "backend_infra" in str(d).lower())
    checks.append(check("msg_007_topic_backend_infra", c7b,
        f"msg_007 topic should be backend-infra. Got: {d}"))

    # ══════════════════════════════════════════════════════════════════════════
    # msg_008: [Global Context OK][Remember]  ← both long-form aliases
    # Expected: GLOBAL scope + REM memory intent
    # ══════════════════════════════════════════════════════════════════════════
    d = get("msg_008")
    c8a = bool(d) and field_matches_any(d, "scope_mode", "global")
    checks.append(check("msg_008_long_form_global_alias", c8a,
        f"msg_008 [Global Context OK] must equal GLOBAL. Got: {d.get('scope_mode','')}"))

    c8b = bool(d) and field_matches_any(d, "memory_intent", "rem", "remember", "persist", "store", "true")
    checks.append(check("msg_008_long_form_rem_alias", c8b,
        f"msg_008 [Remember] must equal REM. Got: {d.get('memory_intent','')}"))

    # ══════════════════════════════════════════════════════════════════════════
    # msg_009: Tag appears MID-message ("Hey team! [SCOPE: devops]")
    # PROPRIETARY TRAP: tags must be at the START → these are INVALID tags → treat as no-tag / default
    # ══════════════════════════════════════════════════════════════════════════
    d = get("msg_009")
    c9 = bool(d) and field_matches_any(d, "scope_mode", "default", "none", "no_tag", "untagged", "conservative", "invalid")
    if not c9:
        # Also accept if they explicitly mark the tags as "not at start" / invalid position
        full_str = str(d).lower()
        c9 = ("invalid" in full_str or "not at start" in full_str or "mid-message" in full_str
               or "ignored" in full_str or "no valid tag" in full_str)
    checks.append(check("msg_009_mid_message_tags_invalid", c9,
        f"msg_009 tags are mid-message → must be treated as invalid/default. Got: {d}"))

    # ══════════════════════════════════════════════════════════════════════════
    # msg_010: [No Memory][ISO: sandbox-test]  ← long-form NOMEM + ISO
    # Expected: ISO scope (sandbox-test), NOMEM memory
    # ══════════════════════════════════════════════════════════════════════════
    d = get("msg_010")
    c10a = bool(d) and field_matches_any(d, "scope_mode", "iso", "isolated", "fresh")
    checks.append(check("msg_010_no_memory_iso_scope", c10a,
        f"msg_010 [No Memory][ISO] → ISO scope. Got: {d.get('scope_mode','')}"))

    c10b = bool(d) and field_matches_any(d, "memory_intent", "nomem", "no", "no-store", "no_store", "none", "false")
    checks.append(check("msg_010_no_memory_long_form", c10b,
        f"msg_010 [No Memory] long-form must equal NOMEM. Got: {d.get('memory_intent','')}"))

    # ══════════════════════════════════════════════════════════════════════════
    # msg_011: [NOMEM][REM]  ← conflict: NOMEM vs REM, last tag = REM wins
    # ══════════════════════════════════════════════════════════════════════════
    d = get("msg_011")
    c11a = bool(d) and field_matches_any(d, "memory_intent", "rem", "remember", "persist", "store", "true")
    checks.append(check("msg_011_conflict_last_tag_wins_rem", c11a,
        f"msg_011 [NOMEM]+[REM]: last tag (REM) should win. Got: {d.get('memory_intent','')}"))

    c11b = bool(d) and ("conflict" in str(d).lower() or "last" in str(d).lower() or "override" in str(d).lower()
                         or "wins" in str(d).lower() or "resolved" in str(d).lower())
    checks.append(check("msg_011_conflict_noted", c11b,
        f"msg_011 conflict between NOMEM and REM should be noted. Got: {d}"))

    # ══════════════════════════════════════════════════════════════════════════
    # msg_012: [SCOPE: finance][GLOBAL]  ← SCOPE + GLOBAL combo
    # These don't directly conflict (different dimensions), both apply;
    # GLOBAL must callout reuse
    # ══════════════════════════════════════════════════════════════════════════
    d = get("msg_012")
    # GLOBAL overrides/augments SCOPE — acceptable to see either "scope+global" or "global"
    c12a = bool(d) and (field_matches_any(d, "scope_mode", "global", "scope")
                         or "global" in str(d).lower())
    checks.append(check("msg_012_scope_global_combo", c12a,
        f"msg_012 [SCOPE:finance][GLOBAL] should reflect both tags. Got: {d.get('scope_mode','')}"))

    c12b = bool(d) and "finance" in str(d).lower()
    checks.append(check("msg_012_finance_topic", c12b,
        f"msg_012 should reference 'finance' topic. Got: {d}"))

    # ── Ordering rule: all messages should record detected tags in order ───────
    ordered_ok = 0
    for msg_id in ["msg_001", "msg_002", "msg_003"]:
        d = get(msg_id)
        if d and ("tags" in str(d).lower() or "detected" in str(d).lower() or "parsed" in str(d).lower()):
            ordered_ok += 1
    checks.append(check("tag_order_recorded", ordered_ok >= 2,
        f"Decisions should record detected/parsed tags. Seen in {ordered_ok}/3 sampled messages"))

    # ── Overall structure: all 12 messages have decisions ────────────────────
    present = sum(1 for i in range(1, 13) if f"msg_{i:03d}" in by_id)
    checks.append(check("all_12_messages_covered", present == 12,
        f"{present}/12 message IDs found in routing decisions"))

    # ── Score ─────────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    passed = (score >= 0.75)

    print(json.dumps({
        "passed": passed,
        "score": score,
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main()