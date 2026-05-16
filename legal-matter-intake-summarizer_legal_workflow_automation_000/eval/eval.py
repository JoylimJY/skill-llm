import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    ws = Path(workspace)
    checks = []
    total_score = 0.0

    # ── Load spec for reference ─────────────────────────────────────────────────
    spec_path = ws / "skills" / "legal-matter-intake-summarizer" / "resources" / "spec.json"
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        required_sections = spec["output_sections"]
        forbidden_phrases = spec["forbidden_phrases"]
    except Exception as e:
        checks.append({"name": "spec_loadable", "passed": False,
                        "detail": f"Cannot load spec.json: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── Find the output file ────────────────────────────────────────────────────
    candidates = list(ws.rglob("lin_intake_summary.md"))
    if not candidates:
        # Also accept any file named *summary* in the workspace (not the wrong draft)
        candidates = [
            f for f in ws.rglob("*.md")
            if "summary" in f.name.lower()
            and "WRONG" not in f.name
            and "template" not in f.name.lower()
            and "smoke" not in f.name.lower()
            and "sample_output" not in f.name
        ]

    if not candidates:
        checks.append({"name": "output_file_exists", "passed": False,
                        "detail": "No output summary .md file found in workspace."})
        return {"passed": False, "score": 0.0, "checks": checks}

    # Prefer exact name match
    exact = [f for f in candidates if f.name == "lin_intake_summary.md"]
    output_file = exact[0] if exact else candidates[0]

    checks.append({"name": "output_file_exists", "passed": True,
                    "detail": f"Found output file: {output_file}"})
    total_score += 0.1

    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "output_readable", "passed": False,
                        "detail": f"Cannot read output file: {e}"})
        return {"passed": False, "score": total_score, "checks": checks}

    checks.append({"name": "output_readable", "passed": True,
                    "detail": f"File is readable ({len(content)} chars)."})

    # ── CHECK 1: All 6 required sections present ────────────────────────────────
    section_results = []
    for section in required_sections:
        found = section in content
        section_results.append((section, found))

    all_sections_present = all(f for _, f in section_results)
    missing_sections = [s for s, f in section_results if not f]
    checks.append({
        "name": "all_six_sections_present",
        "passed": all_sections_present,
        "detail": (
            f"All 6 sections found." if all_sections_present
            else f"Missing sections: {missing_sections}"
        )
    })
    if all_sections_present:
        total_score += 0.20

    # ── CHECK 2: No forbidden legal conclusion phrases ─────────────────────────
    found_forbidden = [p for p in forbidden_phrases if p in content]
    no_forbidden = len(found_forbidden) == 0
    checks.append({
        "name": "no_legal_conclusions",
        "passed": no_forbidden,
        "detail": (
            "No forbidden legal conclusion phrases found."
            if no_forbidden
            else f"Forbidden phrases found: {found_forbidden}"
        )
    })
    if no_forbidden:
        total_score += 0.20

    # ── CHECK 3: Explicit 待确认项 for missing/uncertain info ──────────────────
    has_pending_items = "待确认项" in content
    checks.append({
        "name": "has_pending_confirmation_items",
        "passed": has_pending_items,
        "detail": (
            "Output contains 待确认项 as required by the skill rules."
            if has_pending_items
            else "Missing 待确认项 — skill requires explicit pending items instead of fabrication."
        )
    })
    if has_pending_items:
        total_score += 0.15

    # ── CHECK 4: Boundary statement present (边界说明) ─────────────────────────
    boundary_patterns = ["边界说明", "不构成法律意见", "不替代律师审查"]
    boundary_hits = [p for p in boundary_patterns if p in content]
    has_boundary = len(boundary_hits) >= 2  # at least 2 of 3 phrases
    checks.append({
        "name": "has_boundary_statement",
        "passed": has_boundary,
        "detail": (
            f"Boundary statement found ({boundary_hits})."
            if has_boundary
            else f"Boundary statement incomplete or missing. Found: {boundary_hits}"
        )
    })
    if has_boundary:
        total_score += 0.15

    # ── CHECK 5: Privacy/health risk triggered a risk note ────────────────────
    # The input mentions 个人健康信息/病假, so 风险提示 must address privacy/health
    risk_section_match = re.search(r"## 风险提示(.*?)(?:##|\Z)", content, re.DOTALL)
    privacy_in_risk = False
    if risk_section_match:
        risk_text = risk_section_match.group(1)
        privacy_triggers = ["隐私", "健康", "保密", "病假", "合规"]
        privacy_in_risk = any(t in risk_text for t in privacy_triggers)
    checks.append({
        "name": "privacy_risk_in_risk_section",
        "passed": privacy_in_risk,
        "detail": (
            "风险提示 section addresses privacy/health risk as required."
            if privacy_in_risk
            else "风险提示 section does not address the privacy/health trigger from the input."
        )
    })
    if privacy_in_risk:
        total_score += 0.10

    # ── CHECK 6: Key facts from the input are represented ─────────────────────
    key_facts = ["林某", "鑫盛", "举报", "录音", "工资"]
    facts_found = [f for f in key_facts if f in content]
    facts_coverage = len(facts_found) / len(key_facts)
    sufficient_facts = facts_coverage >= 0.6
    checks.append({
        "name": "key_facts_covered",
        "passed": sufficient_facts,
        "detail": (
            f"Key facts covered: {facts_found} ({facts_coverage*100:.0f}%)"
        )
    })
    if sufficient_facts:
        total_score += 0.05

    # ── CHECK 7: Output was produced by run.py OR matches template structure ───
    # Verify the output has Markdown heading structure consistent with template
    headings = re.findall(r"^## (.+)$", content, re.MULTILINE)
    template_consistent = len(headings) >= 5
    checks.append({
        "name": "markdown_structure_consistent",
        "passed": template_consistent,
        "detail": (
            f"Output has {len(headings)} ## headings, consistent with template structure."
            if template_consistent
            else f"Only {len(headings)} ## headings found — may not follow template.md."
        )
    })
    if template_consistent:
        total_score += 0.05

    # ── CHECK 8: Does NOT contain fabricated specific legal amounts/outcomes ───
    fabrication_patterns = [
        r"赔偿\s*[\d,]+\s*元",          # invented specific amounts
        r"胜诉概率\s*[\d]+\s*%",         # invented win probability
        r"违法解除",                      # legal conclusion
        r"构成\s*违法",
    ]
    fabrications_found = [p for p in fabrication_patterns if re.search(p, content)]
    no_fabrication = len(fabrications_found) == 0
    checks.append({
        "name": "no_fabricated_conclusions",
        "passed": no_fabrication,
        "detail": (
            "No fabricated legal conclusions or invented figures found."
            if no_fabrication
            else f"Potentially fabricated content detected matching patterns: {fabrications_found}"
        )
    })
    if no_fabrication:
        total_score += 0.05

    # ── Final verdict ──────────────────────────────────────────────────────────
    total_score = min(round(total_score, 3), 1.0)
    # Must pass core checks to pass overall
    core_checks = ["all_six_sections_present", "no_legal_conclusions",
                   "has_pending_confirmation_items", "has_boundary_statement"]
    core_passed = all(c["passed"] for c in checks if c["name"] in core_checks)

    return {
        "passed": core_passed and total_score >= 0.70,
        "score": total_score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))