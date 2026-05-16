import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str) -> dict:
    checks = []
    workspace_path = Path(workspace)

    # ── Locate the output ledger file ─────────────────────────────────
    # The task asks the agent to produce decision_ledger.md
    # We search broadly but also check expected locations
    candidates = list(workspace_path.rglob("decision_ledger.md"))
    if not candidates:
        # Also accept any *ledger*.md file the agent may have named slightly differently
        candidates = list(workspace_path.rglob("*ledger*.md"))

    ledger_path = None
    ledger_text = ""

    if candidates:
        # Prefer the most recently modified, or just take first
        ledger_path = candidates[0]
        try:
            ledger_text = ledger_path.read_text(encoding="utf-8")
        except Exception as e:
            checks.append({
                "name": "file_readable",
                "passed": False,
                "detail": f"Found file {ledger_path} but could not read it: {e}"
            })
            return {"passed": False, "score": 0.0, "checks": checks}
    else:
        checks.append({
            "name": "output_file_exists",
            "passed": False,
            "detail": "No decision_ledger.md or *ledger*.md file found anywhere in workspace."
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({
        "name": "output_file_exists",
        "passed": True,
        "detail": f"Found ledger file at: {ledger_path}"
    })

    # ── Check 1: All 6 required section headers present ───────────────
    required_sections = [
        ("已确认决策",   r"##\s*已确认决策"),
        ("待确认事项",   r"##\s*待确认事项"),
        ("负责人和截止日", r"##\s*负责人和截止日"),
        ("前提假设",     r"##\s*前提假设"),
        ("推翻条件",     r"##\s*推翻条件"),
        ("后续依赖",     r"##\s*后续依赖"),
    ]

    all_sections_found = True
    missing_sections = []
    for label, pattern in required_sections:
        if not re.search(pattern, ledger_text):
            all_sections_found = False
            missing_sections.append(label)

    checks.append({
        "name": "all_six_sections_present",
        "passed": all_sections_found,
        "detail": (
            "All 6 required sections found."
            if all_sections_found
            else f"Missing sections: {missing_sections}"
        )
    })

    # ── Check 2: Confirmed decisions — must have at least 4 decisions ──
    # The raw notes contain 4 explicit decisions (Steelco partial delivery,
    # pier 4 rebar drawings update, ITT authorisation, safety audit scheduling,
    # budget variance report submission)
    decision_table_rows = re.findall(r"\|\s*(D\d+)\s*\|", ledger_text)
    unique_decisions = list(dict.fromkeys(decision_table_rows))  # preserve order, deduplicate
    enough_decisions = len(unique_decisions) >= 4

    checks.append({
        "name": "minimum_four_decisions_extracted",
        "passed": enough_decisions,
        "detail": (
            f"Found {len(unique_decisions)} unique decision IDs: {unique_decisions}"
        )
    })

    # ── Check 3: pending_marker "待确认" appears for missing info ──────
    # Safety audit owner is TBD, subcontractor final date not confirmed,
    # Finance Director name TBD — at least 2 待确认 markers expected
    pending_count = len(re.findall(r"待确认", ledger_text))
    has_pending = pending_count >= 2

    checks.append({
        "name": "pending_marker_used_for_missing_info",
        "passed": has_pending,
        "detail": f"Found {pending_count} occurrences of '待确认' (need ≥2)."
    })

    # ── Check 4: Inference tag 【推断】 applied to inferred assumptions ─
    inference_tag_count = len(re.findall(r"【推断】", ledger_text))
    has_inference_tag = inference_tag_count >= 1

    checks.append({
        "name": "inference_tag_applied_to_inferred_assumptions",
        "passed": has_inference_tag,
        "detail": f"Found {inference_tag_count} occurrences of '【推断】' (need ≥1)."
    })

    # ── Check 5: Revocation/pushback conditions extracted ──────────────
    # The notes have at least 3 explicit revocation conditions
    # (Steelco can't deliver → re-open ITT; ground survey →pier4 revisit;
    #  Riverstone rejects → suspend work; audit scheduler missed → escalate)
    revoke_section_match = re.search(r"##\s*推翻条件(.+?)(?:##|$)", ledger_text, re.DOTALL)
    revoke_content = revoke_section_match.group(1) if revoke_section_match else ""
    # Count non-header, non-separator rows in the table
    revoke_rows = re.findall(r"\|\s*(D\d+)\s*\|", revoke_content)
    has_revocation_conditions = len(revoke_rows) >= 2

    checks.append({
        "name": "revocation_conditions_extracted",
        "passed": has_revocation_conditions,
        "detail": f"Found {len(revoke_rows)} revocation condition rows (need ≥2)."
    })

    # ── Check 6: Followup dependencies section populated ───────────────
    followup_section_match = re.search(r"##\s*后续依赖(.+?)(?:##|$)", ledger_text, re.DOTALL)
    followup_content = followup_section_match.group(1) if followup_section_match else ""
    # Should mention at least finance director or planning portal or GeoScan
    dependency_keywords = ["Finance", "finance", "GeoScan", "planning", "规划", "审计师", "财务"]
    followup_populated = any(kw in followup_content for kw in dependency_keywords)
    # Also accept if there's at least one bullet with content
    has_bullet = bool(re.search(r"-\s+\S", followup_content))

    checks.append({
        "name": "followup_dependencies_populated",
        "passed": followup_populated or has_bullet,
        "detail": (
            "Followup dependencies section contains substantive content."
            if (followup_populated or has_bullet)
            else "Followup dependencies section appears empty or missing content."
        )
    })

    # ── Check 7: Audit footer present ────────────────────────────────
    has_footer = bool(re.search(r"可审阅草案|未经授权不得执行|审阅", ledger_text))

    checks.append({
        "name": "audit_footer_present",
        "passed": has_footer,
        "detail": (
            "Audit/review-only footer found."
            if has_footer
            else "Missing required audit footer ('可审阅草案' or similar)."
        )
    })

    # ── Check 8: run.py was actually invoked (verify via output provenance) ─
    # If run.py was used, the output will contain a '生成日期' line (added by render_ledger)
    has_generated_date = bool(re.search(r"生成日期", ledger_text))

    checks.append({
        "name": "generated_via_run_py_cli",
        "passed": has_generated_date,
        "detail": (
            "Output contains '生成日期' header, consistent with run.py CLI invocation."
            if has_generated_date
            else "Output missing '生成日期' — may not have been generated via run.py."
        )
    })

    # ── Check 9: Source reference to raw meeting notes ────────────────
    has_source_ref = bool(re.search(r"minutes_2024-07-10|来源|source", ledger_text, re.IGNORECASE))

    checks.append({
        "name": "source_reference_present",
        "passed": has_source_ref,
        "detail": (
            "Source reference to meeting notes found in ledger."
            if has_source_ref
            else "No source reference found — expected reference to input file."
        )
    })

    # ── Check 10: No hallucinated decision IDs that don't map to real content ─
    # A very basic check: if decisions exist, their descriptions shouldn't be
    # placeholder text like "example" or empty
    decision_desc_match = re.findall(r"\|\s*D\d+\s*\|\s*([^|]{5,})\|", ledger_text)
    has_real_descriptions = len(decision_desc_match) >= 2 and all(
        desc.strip() not in ("", "—", "N/A", "example") for desc in decision_desc_match[:2]
    )

    checks.append({
        "name": "decisions_have_real_descriptions",
        "passed": has_real_descriptions,
        "detail": (
            f"Decisions contain substantive descriptions (sample: {decision_desc_match[:2]})"
            if has_real_descriptions
            else "Decisions appear to have empty or placeholder descriptions."
        )
    })

    # ── Scoring ────────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    score = round(len(passed_checks) / len(checks), 3)

    # Must pass core structural checks to be considered passing overall
    core_checks = [
        "output_file_exists",
        "all_six_sections_present",
        "minimum_four_decisions_extracted",
        "pending_marker_used_for_missing_info",
        "inference_tag_applied_to_inferred_assumptions",
        "revocation_conditions_extracted",
    ]
    core_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in core_checks
    )

    overall_passed = core_passed and score >= 0.75

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "args", "passed": False, "detail": "Usage: eval.py <workspace_dir>"}
        ]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))