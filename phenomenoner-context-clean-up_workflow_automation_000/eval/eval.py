#!/usr/bin/env python3
"""
Evaluation script for context-clean-up skill task.
Checks:
1. Audit JSON was generated (context-cleanup-audit.json exists and is valid)
2. Audit JSON contains the correct offender classes from SKILL.md taxonomy
3. Fix plan document (context-cleanup-plan.md) exists
4. Fix plan covers top offenders from the audit
5. Fix plan orders fixes by trim ladder (Phase 1 / noise discipline before riskier changes)
6. Each fix proposal contains all 4 required elements (exact change, expected impact, rollback plan, verification steps)
7. Plan is audit-only — no automatic deletion commands proposed without rollback
8. Confidence labeled as lower since no /context json receipt is available
"""
import json
import re
import sys
from pathlib import Path


def find_file(workspace: Path, filename: str):
    matches = list(workspace.rglob(filename))
    return matches[0] if matches else None


def check_audit_json(workspace: Path) -> tuple[bool, list[dict]]:
    checks = []

    audit_file = find_file(workspace, "context-cleanup-audit.json")
    if not audit_file:
        checks.append({"name": "audit_json_exists", "passed": False,
                        "detail": "context-cleanup-audit.json not found anywhere in workspace"})
        return False, checks

    checks.append({"name": "audit_json_exists", "passed": True,
                   "detail": f"Found at {audit_file.relative_to(workspace)}"})

    try:
        data = json.loads(audit_file.read_text())
    except Exception as e:
        checks.append({"name": "audit_json_valid", "passed": False,
                        "detail": f"JSON parse error: {e}"})
        return False, checks

    checks.append({"name": "audit_json_valid", "passed": True, "detail": "Valid JSON"})

    # Check schema fields
    required_keys = ["offenders", "context_signals"]
    missing = [k for k in required_keys if k not in data]
    if missing:
        checks.append({"name": "audit_json_schema", "passed": False,
                        "detail": f"Missing required keys: {missing}"})
    else:
        checks.append({"name": "audit_json_schema", "passed": True,
                        "detail": "Required keys present"})

    # Check offender classes
    offenders = data.get("offenders", [])
    found_classes = {o.get("class") for o in offenders}
    expected_classes = {
        "tool_result_dump",
        "automation_transcript_noise",
        "bootstrap_reinjection_bloat",
        "ambient_specialist_surface",
        "summary_accretion",
    }
    missing_classes = expected_classes - found_classes
    if missing_classes:
        checks.append({"name": "audit_offender_classes", "passed": False,
                        "detail": f"Missing offender classes in audit: {missing_classes}. Found: {found_classes}"})
    else:
        checks.append({"name": "audit_offender_classes", "passed": True,
                        "detail": f"All 5 canonical offender classes detected: {found_classes}"})

    # Check high-severity offenders are present
    high_sev = [o for o in offenders if o.get("severity") == "high"]
    if len(high_sev) >= 2:
        checks.append({"name": "audit_high_severity", "passed": True,
                        "detail": f"{len(high_sev)} high-severity offenders identified"})
    else:
        checks.append({"name": "audit_high_severity", "passed": False,
                        "detail": f"Expected >=2 high-severity offenders, got {len(high_sev)}"})

    all_passed = all(c["passed"] for c in checks)
    return all_passed, checks


def check_fix_plan(workspace: Path) -> tuple[bool, list[dict]]:
    checks = []

    plan_file = find_file(workspace, "context-cleanup-plan.md")
    if not plan_file:
        checks.append({"name": "plan_exists", "passed": False,
                        "detail": "context-cleanup-plan.md not found anywhere in workspace"})
        return False, checks

    checks.append({"name": "plan_exists", "passed": True,
                   "detail": f"Found at {plan_file.relative_to(workspace)}"})

    try:
        content = plan_file.read_text(encoding="utf-8", errors="replace").lower()
    except Exception as e:
        checks.append({"name": "plan_readable", "passed": False, "detail": f"Read error: {e}"})
        return False, checks

    checks.append({"name": "plan_readable", "passed": True, "detail": "Plan file readable"})

    # ── Check top offenders are mentioned ────────────────────────────────────
    offender_terms = [
        (["cron", "heartbeat", "automation", "no-op", "noop", "ok line"], "automation_transcript_noise"),
        (["agents.md", "memory.md", "soul.md", "bootstrap", "reinjection"], "bootstrap_reinjection_bloat"),
        (["exec", "read dump", "web_fetch", "tool result", "tool output", "session log", "exec_dump", "read_dump", "web_fetch"], "tool_result_dump"),
        (["always-on", "always on", "specialist", "ambient", "on-demand", "subagent", "worker"], "ambient_specialist_surface"),
        (["summary", "sprint", "accretion", "historical"], "summary_accretion"),
    ]
    for terms, offender_class in offender_terms:
        found = any(t in content for t in terms)
        checks.append({
            "name": f"plan_mentions_{offender_class}",
            "passed": found,
            "detail": f"Plan {'mentions' if found else 'MISSING'} offender class '{offender_class}' (looked for: {terms[:3]})"
        })

    # ── Check trim ladder ordering: Phase 1 (noise) must appear before Phase 3/4 ─
    # Look for noise discipline / automation silence BEFORE file deletion / config changes
    noise_pos = -1
    config_pos = -1
    noise_terms = ["no_reply", "no-reply", "silent", "silence", "noise discipline", "phase 1", "make.*silent", "truly silent"]
    config_terms = ["phase 4", "higher-risk", "config", "runtime", "tool-surface", "deeper runtime"]

    for term in noise_terms:
        m = re.search(term, content)
        if m and (noise_pos == -1 or m.start() < noise_pos):
            noise_pos = m.start()

    for term in config_terms:
        m = re.search(term, content)
        if m and (config_pos == -1 or m.start() < config_pos):
            config_pos = m.start()

    if noise_pos != -1 and config_pos != -1:
        ordered = noise_pos < config_pos
        checks.append({
            "name": "trim_ladder_ordering",
            "passed": ordered,
            "detail": f"Noise discipline (pos {noise_pos}) {'before' if ordered else 'AFTER'} higher-risk config changes (pos {config_pos}) — ladder ordering {'correct' if ordered else 'VIOLATED'}"
        })
    elif noise_pos != -1:
        checks.append({
            "name": "trim_ladder_ordering",
            "passed": True,
            "detail": "Noise discipline mentioned; no higher-risk Phase 4 changes found (acceptable for low-risk plan)"
        })
    else:
        checks.append({
            "name": "trim_ladder_ordering",
            "passed": False,
            "detail": "Plan does not mention noise discipline / Phase 1 fixes at all. Trim ladder not followed."
        })

    # ── Check 4 required elements per fix proposal ────────────────────────────
    required_elements = [
        (["exact change", "exact fix", "proposed change", "change:", "fix:"], "exact_change"),
        (["expected impact", "impact:", "reduction", "savings", "benefit"], "expected_impact"),
        (["rollback", "revert", "undo", "restore"], "rollback_plan"),
        (["verif", "confirm", "check after", "validate", "verification"], "verification_steps"),
    ]
    for terms, element_name in required_elements:
        found = any(t in content for t in terms)
        checks.append({
            "name": f"plan_has_{element_name}",
            "passed": found,
            "detail": f"Plan {'includes' if found else 'MISSING'} required element '{element_name}'"
        })

    # ── Audit-only contract: no automatic deletions without rollback mention ──
    auto_delete_signals = ["rm -rf", "rm -f", "delete automatically", "auto-delete", "automatically delete", "automatically remove"]
    has_auto_delete = any(t in content for t in auto_delete_signals)
    has_rollback = "rollback" in content or "revert" in content

    if has_auto_delete and not has_rollback:
        checks.append({
            "name": "audit_only_contract",
            "passed": False,
            "detail": "Plan proposes automatic deletions WITHOUT rollback notes — violates audit-only contract"
        })
    else:
        checks.append({
            "name": "audit_only_contract",
            "passed": True,
            "detail": "Plan respects audit-only contract (no unguarded automatic deletions)"
        })

    # ── Confidence labeling: must acknowledge lower confidence since no receipt ─
    confidence_terms = ["confidence", "lower confidence", "no receipt", "no /context", "estimates only",
                        "unavailable", "receipt not available", "without receipt", "no live session"]
    has_confidence_label = any(t in content for t in confidence_terms)
    checks.append({
        "name": "confidence_labeled_lower",
        "passed": has_confidence_label,
        "detail": f"Plan {'acknowledges' if has_confidence_label else 'MISSING acknowledgment of'} lower confidence due to missing /context json receipt"
    })

    # ── Minimum fix count (3-8 per SKILL.md) ──────────────────────────────────
    fix_count_patterns = [
        r"##\s+fix\s+\d",
        r"###\s+fix\s+\d",
        r"\d+\.\s+(fix|change|action|recommendation|proposal)",
        r"-\s+(fix|change|action):",
    ]
    fix_count = 0
    for pattern in fix_count_patterns:
        fix_count = max(fix_count, len(re.findall(pattern, content)))

    # Also count numbered items in lists as a fallback
    numbered_items = len(re.findall(r"^\s*\d+\.", content, re.MULTILINE))

    effective_fix_count = max(fix_count, min(numbered_items, 10))
    min_fixes = 3
    checks.append({
        "name": "fix_count_minimum",
        "passed": effective_fix_count >= min_fixes or numbered_items >= min_fixes,
        "detail": f"Detected ~{effective_fix_count} fix proposals (numbered items: {numbered_items}); minimum required: {min_fixes}"
    })

    all_passed = all(c["passed"] for c in checks)
    return all_passed, checks


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "args", "passed": False, "detail": "No workspace argument provided"}
        ]}))
        sys.exit(1)

    workspace = Path(sys.argv[1])

    all_checks = []

    # Section 1: Audit JSON
    _, audit_checks = check_audit_json(workspace)
    all_checks.extend(audit_checks)

    # Section 2: Fix Plan
    _, plan_checks = check_fix_plan(workspace)
    all_checks.extend(plan_checks)

    # ── Scoring ───────────────────────────────────────────────────────────────
    total = len(all_checks)
    passed_count = sum(1 for c in all_checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0

    # Critical checks that must pass for overall pass
    critical = [
        "audit_json_exists",
        "audit_json_valid",
        "audit_offender_classes",
        "plan_exists",
        "plan_mentions_automation_transcript_noise",
        "plan_mentions_bootstrap_reinjection_bloat",
        "plan_mentions_tool_result_dump",
        "audit_only_contract",
        "trim_ladder_ordering",
        "plan_has_rollback_plan",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in all_checks)
        for name in critical
    )

    overall_passed = critical_passed and score >= 0.70

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": all_checks,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()