import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    total_weight = 0.0
    earned_weight = 0.0

    def add_check(name: str, passed: bool, detail: str, weight: float):
        nonlocal total_weight, earned_weight
        checks.append({"name": name, "passed": passed, "detail": detail})
        total_weight += weight
        if passed:
            earned_weight += weight

    # --- Locate the output file ---
    ws = Path(workspace)
    candidates = list(ws.rglob("refactor_plan.md"))
    if not candidates:
        # Also accept .txt or .yaml variants but penalize
        candidates = list(ws.rglob("refactor_plan.*"))

    if not candidates:
        add_check("file_exists", False, "No refactor_plan.* file found anywhere in workspace.", 2.0)
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    plan_file = candidates[0]
    add_check("file_exists", True, f"Found plan file at: {plan_file}", 2.0)

    try:
        content = plan_file.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        add_check("file_readable", False, f"Could not read file: {e}", 1.0)
        return {"passed": False, "score": 0.0, "checks": checks}

    add_check("file_readable", True, f"File is readable, length={len(content)} chars", 1.0)
    content_lower = content.lower()

    # =====================================================================
    # CHECK 1: Situation Summary ≤ 5 lines (PROPRIETARY TRAP #1)
    # Must find a "situation summary" section and it must be ≤ 5 non-blank lines
    # =====================================================================
    try:
        # Find the situation summary block
        sit_pattern = re.search(
            r'(?i)(situation\s+summary|## situation|# situation)(.*?)(?=\n#{1,3}\s|\n\*\*[A-Z]|\Z)',
            content,
            re.DOTALL
        )
        if sit_pattern:
            raw_block = sit_pattern.group(2).strip()
            # Count non-blank, non-header lines
            lines = [l for l in raw_block.split('\n') if l.strip() and not l.strip().startswith('#')]
            line_count = len(lines)
            passed = (1 <= line_count <= 5)
            add_check(
                "situation_summary_max_5_lines",
                passed,
                f"Situation Summary has {line_count} non-blank lines (must be 1–5). Lines: {lines[:6]}",
                2.5
            )
        else:
            add_check(
                "situation_summary_max_5_lines",
                False,
                "No 'Situation Summary' section found in the document.",
                2.5
            )
    except Exception as e:
        add_check("situation_summary_max_5_lines", False, f"Error parsing situation summary: {e}", 2.5)

    # =====================================================================
    # CHECK 2: Top Findings section exists and findings are RANKED BY IMPACT
    # (must have ranked/numbered list, not alphabetical or unordered bullets)
    # =====================================================================
    try:
        findings_pattern = re.search(
            r'(?i)(top\s+findings?|## findings?|# findings?|key\s+findings?)(.*?)(?=\n#{1,3}\s|\n\*\*[A-Z]|\Z)',
            content,
            re.DOTALL
        )
        if findings_pattern:
            findings_block = findings_pattern.group(2).strip()
            # Check for numbered list (ranked) - must have at least 2 numbered entries
            numbered = re.findall(r'^\s*(\d+)\.\s+.+', findings_block, re.MULTILINE)
            # Also accept ranked labels like "1.", "#1", "rank 1"
            has_ranking = len(numbered) >= 2
            # Check that impact-related words appear (evidence of impact ranking)
            has_impact_language = bool(re.search(
                r'(?i)(critical|high.impact|highest|P0|most\s+severe|top\s+risk|highest\s+risk|'
                r'impact\s*:\s*(critical|high)|ranked\s+by\s+impact|#1|first\s+priority)',
                findings_block
            ))
            passed = has_ranking
            detail = (
                f"Found {len(numbered)} numbered findings. "
                f"Impact language present: {has_impact_language}. "
                f"Block snippet: {findings_block[:300]}"
            )
            add_check("top_findings_ranked_by_impact", passed, detail, 2.0)
        else:
            add_check(
                "top_findings_ranked_by_impact",
                False,
                "No 'Top Findings' section found.",
                2.0
            )
    except Exception as e:
        add_check("top_findings_ranked_by_impact", False, f"Error: {e}", 2.0)

    # =====================================================================
    # CHECK 3: Action Plan has TODAY and THIS WEEK subsections (PROPRIETARY TRAP #2)
    # =====================================================================
    try:
        action_pattern = re.search(
            r'(?i)(action\s+plan|## action|# action)(.*?)(?=\n#{1,3}\s|\n\*\*[A-Z]|\Z)',
            content,
            re.DOTALL
        )
        if action_pattern:
            action_block = action_pattern.group(2).strip()
            has_today = bool(re.search(r'(?i)\b(today|immediate|day\s*0|day\s*1)\b', action_block))
            has_this_week = bool(re.search(r'(?i)\b(this\s+week|week\s*1|week\s*one|by\s+friday|short.term)\b', action_block))
            passed = has_today and has_this_week
            add_check(
                "action_plan_today_vs_this_week",
                passed,
                f"'Today' subsection: {has_today}, 'This week' subsection: {has_this_week}. Block: {action_block[:300]}",
                2.5
            )
        else:
            add_check(
                "action_plan_today_vs_this_week",
                False,
                "No 'Action Plan' section found.",
                2.5
            )
    except Exception as e:
        add_check("action_plan_today_vs_this_week", False, f"Error: {e}", 2.5)

    # =====================================================================
    # CHECK 4: Each next step has OWNER + ETA (PROPRIETARY TRAP #3)
    # Must find at least 3 instances of owner assignment AND ETA/deadline
    # =====================================================================
    try:
        # Look for owner patterns: @name, Owner: X, Owned by X
        owner_matches = re.findall(
            r'(?i)(@\w+|owner\s*:\s*\w+|owned\s+by\s+\w+|assigned\s+to\s*:\s*\w+|responsible\s*:\s*\w+)',
            content
        )
        # Look for ETA patterns: ETA: X, by <date>, deadline, week of
        eta_matches = re.findall(
            r'(?i)(eta\s*:\s*[\w\s,/-]+|by\s+(friday|monday|tuesday|wednesday|thursday|nov\s+\d+|dec\s+\d+|sept\s+\d+|oct\s+\d+|\d{4}-\d{2}-\d{2})|deadline\s*:\s*[\w\s,/-]+|due\s*:\s*[\w\s,/-]+)',
            content
        )
        owner_count = len(set(owner_matches))
        eta_count = len(eta_matches)
        passed = owner_count >= 2 and eta_count >= 2
        add_check(
            "steps_have_owner_and_eta",
            passed,
            f"Owner assignments found: {owner_count} (need ≥2). ETA markers found: {eta_count} (need ≥2). "
            f"Owners: {list(set(owner_matches))[:5]}, ETAs: {[m[0] for m in eta_matches[:5]]}",
            2.0
        )
    except Exception as e:
        add_check("steps_have_owner_and_eta", False, f"Error: {e}", 2.0)

    # =====================================================================
    # CHECK 5: Risks + Mitigations section with FALLBACK plan (PROPRIETARY TRAP #4)
    # =====================================================================
    try:
        risk_pattern = re.search(
            r'(?i)(risks?\s*\+\s*mitigations?|## risks?|# risks?|risks?\s+and\s+mitigations?)(.*?)(?=\n#{1,3}\s|\n\*\*[A-Z]|\Z)',
            content,
            re.DOTALL
        )
        if risk_pattern:
            risk_block = risk_pattern.group(2).strip()
            has_fallback = bool(re.search(
                r'(?i)(fallback|roll.?back|contingency|if.*fails?|backup\s+plan|alternative|revert|undo)',
                risk_block
            ))
            has_mitigation = bool(re.search(
                r'(?i)(mitigat|reduc|prevent|monitor|alert|test\s+in\s+(staging|dev)|feature\s+flag)',
                risk_block
            ))
            passed = has_fallback and has_mitigation
            add_check(
                "risks_with_fallback",
                passed,
                f"Fallback/rollback mentioned: {has_fallback}. Mitigation language: {has_mitigation}. "
                f"Block snippet: {risk_block[:400]}",
                2.5
            )
        else:
            add_check(
                "risks_with_fallback",
                False,
                "No 'Risks + Mitigations' section found.",
                2.5
            )
    except Exception as e:
        add_check("risks_with_fallback", False, f"Error: {e}", 2.5)

    # =====================================================================
    # CHECK 6: Explicit assumptions and tradeoffs stated (Quality Gate)
    # =====================================================================
    try:
        has_assumptions = bool(re.search(
            r'(?i)(assumption|we\s+assume|assuming|trade.?off|tradeoff|caveat)',
            content
        ))
        has_tradeoffs = bool(re.search(
            r'(?i)(trade.?off|tradeoff|vs\.?\s|versus|alternative\s+approach|option\s+[AB12])',
            content
        ))
        passed = has_assumptions and has_tradeoffs
        add_check(
            "explicit_assumptions_and_tradeoffs",
            passed,
            f"Assumptions: {has_assumptions}, Tradeoffs: {has_tradeoffs}",
            1.5
        )
    except Exception as e:
        add_check("explicit_assumptions_and_tradeoffs", False, f"Error: {e}", 1.5)

    # =====================================================================
    # CHECK 7: Exact checklist or commands present (Quality Gate)
    # Must include at least one concrete command or checkbox item
    # =====================================================================
    try:
        has_checklist = bool(re.search(
            r'(?m)(^\s*[-*]\s+\[[ xX]\]|^\s*\d+\.\s+\[[ xX]\]|```[\s\S]*?```|`[^`]+`)',
            content
        ))
        has_commands = bool(re.search(
            r'(?i)(pytest|pip\s+install|git\s+|bash|\.sh|python\s+|grep\s+|sed\s+|docker\s+)',
            content
        ))
        passed = has_checklist or has_commands
        add_check(
            "checklist_or_commands_present",
            passed,
            f"Checklist items: {has_checklist}, Concrete commands: {has_commands}",
            1.5
        )
    except Exception as e:
        add_check("checklist_or_commands_present", False, f"Error: {e}", 1.5)

    # =====================================================================
    # CHECK 8: Evidence-backed claims — references actual artifacts from workspace
    # Must reference specific files/issues found in the provided materials
    # =====================================================================
    try:
        evidence_refs = []
        if re.search(r'(?i)(refund\.py|int.truncation|\$2[,.]?300|18\s+months)', content):
            evidence_refs.append("refund_bug_evidence")
        if re.search(r'(?i)(stripe\s+v[23]|sdk.*v2.*eol|dec.*2024|december.*2024)', content):
            evidence_refs.append("stripe_eol_evidence")
        if re.search(r'(?i)(pci|nov.*15|november.*15|compliance.*audit)', content):
            evidence_refs.append("pci_audit_evidence")
        if re.search(r'(?i)(test.*coverage|15\s*%|60\s*%|coverage.*threshold)', content):
            evidence_refs.append("coverage_evidence")
        if re.search(r'(?i)(pii|log.*transaction|transaction.*log|personally.*identifiable)', content):
            evidence_refs.append("pii_logging_evidence")
        passed = len(evidence_refs) >= 3
        add_check(
            "evidence_backed_claims",
            passed,
            f"Evidence references found: {evidence_refs} (need ≥3)",
            2.0
        )
    except Exception as e:
        add_check("evidence_backed_claims", False, f"Error: {e}", 2.0)

    # =====================================================================
    # CHECK 9: Reversible changes preferred — mentions phased/reversible approach
    # =====================================================================
    try:
        has_reversible = bool(re.search(
            r'(?i)(phase\s*[123]|phased|feature\s+flag|canary|rollback|revert|deploy.*separately|'
            r'reversible|incremental|step.?by.?step|staged)',
            content
        ))
        add_check(
            "reversible_or_phased_approach",
            has_reversible,
            f"Phased/reversible approach mentioned: {has_reversible}",
            1.5
        )
    except Exception as e:
        add_check("reversible_or_phased_approach", False, f"Error: {e}", 1.5)

    # =====================================================================
    # CHECK 10: Five required sections all present (structural completeness)
    # =====================================================================
    try:
        required_sections = {
            "situation_summary": bool(re.search(r'(?i)situation\s*summary', content)),
            "top_findings": bool(re.search(r'(?i)top\s+findings?|key\s+findings?', content)),
            "action_plan": bool(re.search(r'(?i)action\s+plan', content)),
            "risks_mitigations": bool(re.search(r'(?i)risks?\s*(\+|and)\s*mitigations?', content)),
            "checklist_or_commands": bool(re.search(r'(?i)checklist|commands?|steps?|acceptance\s+criteri', content)),
        }
        all_present = all(required_sections.values())
        missing = [k for k, v in required_sections.items() if not v]
        add_check(
            "all_five_sections_present",
            all_present,
            f"Sections present: {required_sections}. Missing: {missing}",
            2.0
        )
    except Exception as e:
        add_check("all_five_sections_present", False, f"Error: {e}", 2.0)

    # --- Final Score ---
    score = round(earned_weight / total_weight, 4) if total_weight > 0 else 0.0

    # Must pass critical checks to be considered passing overall
    critical_checks = [
        "situation_summary_max_5_lines",
        "action_plan_today_vs_this_week",
        "risks_with_fallback",
        "evidence_backed_claims",
        "all_five_sections_present",
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )
    overall_passed = critical_passed and score >= 0.65

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))