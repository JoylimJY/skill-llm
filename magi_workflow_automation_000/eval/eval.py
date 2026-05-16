import json
import sys
import re
from pathlib import Path

def load_file(path: Path):
    try:
        return path.read_text()
    except Exception as e:
        return None

def evaluate(workspace_dir: str):
    ws = Path(workspace_dir)
    magi_dir = ws / "skills" / "magi"

    corrections_path = magi_dir / "corrections.md"
    experiments_path = magi_dir / "experiments.md"
    memory_path = magi_dir / "memory.md"

    corrections_text = load_file(corrections_path) or ""
    experiments_text = load_file(experiments_path) or ""
    memory_text = load_file(memory_path) or ""

    checks = []

    # ── CHECK 1: corrections.md has original entries (append-only preserved) ──
    original_entries = [
        "2026-04-01 | flagged unused variable as critical → should be a warning only",
        "2026-04-03 | suggested rewriting entire function for minor style issue → suggest targeted fix only",
    ]
    preserved = all(e in corrections_text for e in original_entries)
    checks.append({
        "name": "corrections_original_entries_preserved",
        "passed": preserved,
        "detail": "Original corrections.md entries must not be modified or deleted (append-only)." if not preserved else "OK"
    })

    # ── CHECK 2: corrections.md has new entries for Event A and Event B ──
    # Must contain entries dated 2026-04-10 and 2026-04-11
    has_event_a = bool(re.search(r"2026-04-10", corrections_text))
    has_event_b = bool(re.search(r"2026-04-11", corrections_text))
    checks.append({
        "name": "corrections_event_a_logged",
        "passed": has_event_a,
        "detail": "Event A (2026-04-10) must be logged in corrections.md" if not has_event_a else "OK"
    })
    checks.append({
        "name": "corrections_event_b_logged",
        "passed": has_event_b,
        "detail": "Event B (2026-04-11) must be logged in corrections.md" if not has_event_b else "OK"
    })

    # ── CHECK 3: experiments.md baseline row preserved ──
    baseline_preserved = "2026-04-01 | — | — | 0 | baseline | keep" in experiments_text
    checks.append({
        "name": "experiments_baseline_preserved",
        "passed": baseline_preserved,
        "detail": "Baseline row must not be modified (append-only)" if not baseline_preserved else "OK"
    })

    # ── CHECK 4: experiments.md has correct columns (pipe-delimited, 6 cols) ──
    exp_lines = [l.strip() for l in experiments_text.splitlines() if l.strip() and "|" in l and not l.strip().startswith("date")]
    valid_format_lines = []
    for line in exp_lines:
        parts = [p.strip() for p in line.split("|")]
        if len(parts) == 6:
            valid_format_lines.append(line)
    # We expect at least 4 new experiment rows (baseline already there, plus at minimum events A, B, C, D)
    new_exp_lines = [l for l in exp_lines if "2026-04-01 | — | — | 0 | baseline | keep" not in l]
    checks.append({
        "name": "experiments_new_rows_added",
        "passed": len(new_exp_lines) >= 4,
        "detail": f"Expected at least 4 new experiment rows, found {len(new_exp_lines)}: {new_exp_lines}" if len(new_exp_lines) < 4 else "OK"
    })

    # ── CHECK 5: Event C experiment must be logged as "discard" (MAGI 1/3 failed) ──
    # The row must contain the discard status for event C
    # The outcome should mention BALTHASAR or CASPAR dissent or just show discard
    event_c_rows = [l for l in exp_lines if "2026-04-14" in l or "performance disclaimer" in l.lower() or "loop" in l.lower()]
    event_c_discard = any("discard" in l.lower() for l in event_c_rows)
    event_c_magi_fail = any(re.search(r"1/3", l) for l in event_c_rows)
    checks.append({
        "name": "experiments_event_c_discarded",
        "passed": event_c_discard,
        "detail": f"Event C hypothesis (1/3 MAGI) must be logged as 'discard'. Found rows: {event_c_rows}" if not event_c_discard else "OK"
    })
    checks.append({
        "name": "experiments_event_c_magi_vote_1_3",
        "passed": event_c_magi_fail,
        "detail": f"Event C must record magi=1/3. Found: {event_c_rows}" if not event_c_magi_fail else "OK"
    })

    # ── CHECK 6: Event C rule must NOT appear in memory.md (VERIFY failed → no APPLY) ──
    # The performance disclaimer / loop rule must not be in memory.md Applied section
    event_c_rule_in_memory = bool(re.search(r"performance disclaimer|loop.*disclaimer|disclaimer.*loop", memory_text, re.IGNORECASE))
    checks.append({
        "name": "memory_event_c_rule_not_applied",
        "passed": not event_c_rule_in_memory,
        "detail": "Event C rule must NOT be in memory.md (VERIFY failed, APPLY must be skipped)" if event_c_rule_in_memory else "OK"
    })

    # ── CHECK 7: Event D must be logged as "revert" in experiments.md ──
    event_d_rows = [l for l in exp_lines if "2026-04-15" in l or "revert" in l.lower()]
    event_d_revert = any("revert" in l.lower() for l in event_d_rows)
    checks.append({
        "name": "experiments_event_d_reverted",
        "passed": event_d_revert,
        "detail": f"Event D must be logged as 'revert' (rule failed measurement). Found: {event_d_rows}" if not event_d_revert else "OK"
    })

    # ── CHECK 8: Event B rule must NOT be in memory.md Applied section (reverted = deleted) ──
    # After revert, the rule from Event B (limit refactoring to specific lines) must be gone from Applied
    applied_section_match = re.search(r"## Applied.*", memory_text, re.DOTALL)
    applied_section = applied_section_match.group(0) if applied_section_match else ""
    # The rule involves refactoring / specific lines - should not be in Applied
    refactor_rule_in_applied = bool(re.search(r"refactor|rewrite|specific line|targeted|entire (class|module|function)", applied_section, re.IGNORECASE))
    checks.append({
        "name": "memory_event_b_rule_removed_from_applied",
        "passed": not refactor_rule_in_applied,
        "detail": "After revert, Event B rule must be deleted from memory.md Applied section. Still found refactoring rule there." if refactor_rule_in_applied else "OK"
    })

    # ── CHECK 9: Event A rule (about warning vs blocking) must be in memory.md Applied section ──
    # Event A went through full cycle and was applied (Event A has no failed MAGI and no failed measurement)
    # Look for some form of "warning" / "suggestion" / "private" / "blocking" rule in Applied
    applied_has_event_a_rule = bool(re.search(r"warning|suggestion|private|blocking|helper", applied_section, re.IGNORECASE))
    checks.append({
        "name": "memory_event_a_rule_in_applied",
        "passed": applied_has_event_a_rule,
        "detail": f"Event A rule (private functions → suggestion/warning, not blocking) should be in Applied section of memory.md. Applied section: {applied_section[:300]}" if not applied_has_event_a_rule else "OK"
    })

    # ── CHECK 10: Drift guard condition ──
    # Events B (applied then reverted), C (discarded), D (revert) = 3 consecutive failures
    # The agent must have noted/surfaced this drift guard condition somewhere
    # Check in experiments.md or memory.md for any mention of drift / pattern / consecutive
    all_text = experiments_text + memory_text + corrections_text
    drift_mentioned = bool(re.search(r"drift|consecutive|3 consecutive|pattern.*user|surface|misread", all_text, re.IGNORECASE))
    checks.append({
        "name": "drift_guard_surfaced",
        "passed": drift_mentioned,
        "detail": "After 3 consecutive revert/discard events (C discarded, D reverted, and depending on ordering), drift guard must be noted/surfaced. No mention found." if not drift_mentioned else "OK"
    })

    # ── CHECK 11: experiments.md rows have valid 6-column format ──
    all_exp_rows = [l.strip() for l in experiments_text.splitlines() if l.strip() and "|" in l and not l.strip().startswith("date")]
    malformed = [l for l in all_exp_rows if len([p.strip() for p in l.split("|")]) != 6]
    checks.append({
        "name": "experiments_rows_valid_format",
        "passed": len(malformed) == 0,
        "detail": f"All experiment rows must have exactly 6 pipe-delimited columns. Malformed: {malformed}" if malformed else "OK"
    })

    # ── CHECK 12: memory.md has both required sections ──
    has_rules_section = "## Rules (verified, kept)" in memory_text
    has_applied_section = "## Applied (awaiting measurement)" in memory_text
    checks.append({
        "name": "memory_has_required_sections",
        "passed": has_rules_section and has_applied_section,
        "detail": f"memory.md must have both '## Rules (verified, kept)' and '## Applied (awaiting measurement)'. Rules:{has_rules_section} Applied:{has_applied_section}" if not (has_rules_section and has_applied_section) else "OK"
    })

    # ── CHECK 13: memory.md does not exceed 50 lines ──
    mem_lines = [l for l in memory_text.splitlines()]
    mem_line_count = len(mem_lines)
    checks.append({
        "name": "memory_within_50_line_cap",
        "passed": mem_line_count <= 50,
        "detail": f"memory.md must not exceed 50 lines. Found {mem_line_count} lines." if mem_line_count > 50 else "OK"
    })

    # ── CHECK 14: corrections.md Event D logged ──
    # Event D is a user correction on 2026-04-15
    has_event_d_correction = bool(re.search(r"2026-04-15", corrections_text))
    checks.append({
        "name": "corrections_event_d_logged",
        "passed": has_event_d_correction,
        "detail": "Event D correction (2026-04-15) must be appended to corrections.md" if not has_event_d_correction else "OK"
    })

    # ── Scoring ──
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)
    overall = passed_count >= 10  # Must pass at least 10/14 checks

    return {
        "passed": overall,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))