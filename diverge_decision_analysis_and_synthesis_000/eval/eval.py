import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []

    # ------------------------------------------------------------------ #
    # Locate the output file
    # ------------------------------------------------------------------ #
    target_filename = "stakeholder_analysis.md"
    found_files = list(Path(workspace_dir).rglob(target_filename))

    if not found_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False,
                         "detail": f"'{target_filename}' not found anywhere in workspace."}]
        }

    # Use the most recently modified one if duplicates exist
    target_path = sorted(found_files, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    checks.append({"name": "file_exists", "passed": True,
                   "detail": f"Found at {target_path}"})

    try:
        content = target_path.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks + [{"name": "file_readable", "passed": False,
                                  "detail": str(e)}]
        }

    content_lower = content.lower()

    # ------------------------------------------------------------------ #
    # CHECK 1: Perspective COUNT — must have 5-7 distinct perspectives
    # The SKILL.md mandates 5-7 for high-complexity / safety-critical tasks.
    # ------------------------------------------------------------------ #
    # We detect perspective headers: lines that look like "## Perspective: X" or
    # "### [Role]" or "**Perspective N:**" or "## [Role Name]"
    # We count unique role mentions from the required medical domain list
    # plus any clearly labeled perspective blocks.

    required_medical_roles = [
        r"doctor|physician|clinician|dr\.",
        r"patient",
        r"caregiver|family",
        r"insurance|payer",
    ]

    additional_valid_roles = [
        r"regulator|fda|regulatory",
        r"legal|lawyer|attorney|liability",
        r"security|privacy|data protection|infosec",
        r"engineer|developer|technical|maintainab",
        r"ethic",
    ]

    # Count required medical roles present
    req_found = []
    for pattern in required_medical_roles:
        if re.search(pattern, content_lower):
            req_found.append(pattern)

    required_roles_count = len(req_found)
    required_roles_ok = required_roles_count >= 4  # all 4 required medical roles present

    checks.append({
        "name": "required_medical_roles_present",
        "passed": required_roles_ok,
        "detail": f"Found {required_roles_count}/4 required domain roles (doctor/physician, patient, caregiver, insurance). "
                  f"Matched: {req_found}"
    })

    # Count total distinct perspective roles (required + additional)
    all_role_patterns = required_medical_roles + additional_valid_roles
    total_roles_found = sum(1 for p in all_role_patterns if re.search(p, content_lower))

    # Also count explicit perspective section headers as a signal
    # Look for patterns like "Perspective 1:", "## Physician", "### Patient Perspective", etc.
    perspective_header_patterns = [
        r"perspective\s*\d+",
        r"##\s+\w+\s+perspective",
        r"###\s+\w+\s+perspective",
        r"^\*\*perspective",
        r"^\#{1,4}\s+(physician|doctor|patient|caregiver|insurance|regulator|legal|security|engineer|ethic)",
    ]
    header_matches = set()
    for pat in perspective_header_patterns:
        for m in re.finditer(pat, content_lower, re.MULTILINE):
            header_matches.add(m.group(0).strip()[:60])

    # Perspective count: use max of (role mentions, header matches) to be fair
    perspective_count_estimate = max(total_roles_found, len(header_matches))
    perspective_count_ok = perspective_count_estimate >= 5

    checks.append({
        "name": "minimum_5_perspectives",
        "passed": perspective_count_ok,
        "detail": (
            f"Estimated {perspective_count_estimate} distinct perspectives (need ≥5 for high-complexity). "
            f"Role pattern hits: {total_roles_found}, Header hits: {len(header_matches)}. "
            f"Headers found: {list(header_matches)[:10]}"
        )
    })

    # ------------------------------------------------------------------ #
    # CHECK 2: DIVERGENCE section exists and is labeled/structured
    # ------------------------------------------------------------------ #
    has_diverge_section = bool(re.search(
        r"(diverge|perspectives?|stakeholder\s+views?|multiple\s+viewpoints?|analysis\s+by\s+role)",
        content_lower
    ))
    checks.append({
        "name": "divergence_section_present",
        "passed": has_diverge_section,
        "detail": "Document must contain a divergence/perspectives section with multiple distinct viewpoints."
    })

    # ------------------------------------------------------------------ #
    # CHECK 3: SYNTHESIS section with all 4 required steps
    # SKILL.md synthesis: conflicts → common ground → weigh by stakes → decide + trade-offs
    # ------------------------------------------------------------------ #
    synthesis_present = bool(re.search(r"synthesis|synthesiz", content_lower))
    checks.append({
        "name": "synthesis_section_present",
        "passed": synthesis_present,
        "detail": "Document must contain an explicit synthesis section."
    })

    # Step 1: Conflicts identified
    conflicts_present = bool(re.search(
        r"conflict|disagree|tension|diverge|contradict|oppose", content_lower
    ))
    checks.append({
        "name": "synthesis_conflicts_identified",
        "passed": conflicts_present,
        "detail": "Synthesis must explicitly identify conflicts/disagreements between perspectives."
    })

    # Step 2: Common ground
    common_ground_present = bool(re.search(
        r"common ground|agree|consensus|all\s+(perspectives?|stakeholders?|parties)\s+(agree|concur|share|support)",
        content_lower
    ))
    checks.append({
        "name": "synthesis_common_ground",
        "passed": common_ground_present,
        "detail": "Synthesis must identify common ground or areas of agreement across perspectives."
    })

    # Step 3: Weigh by stakes — safety must outweigh preferences
    safety_weighted = bool(re.search(
        r"safety\s+(concern|risk|issue|outweigh|priorit|critical|above|over|trump|supersede|paramount|first|>|greater than)",
        content_lower
    )) or bool(re.search(
        r"(safety|patient safety).{0,60}(outweigh|priorit|trump|supersede|above|over|paramount|first|critical|most important)",
        content_lower
    )) or bool(re.search(
        r"(weigh|stake|prioriti).{0,100}safety",
        content_lower
    ))
    checks.append({
        "name": "synthesis_safety_weighted_over_preferences",
        "passed": safety_weighted,
        "detail": "Synthesis must explicitly weigh safety concerns as higher priority than user preferences."
    })

    # Step 4: Final decision made with trade-offs documented
    decision_present = bool(re.search(
        r"(recommend|decision|conclusion|final|we\s+should|suggest\s+option|choose\s+option|recommend\s+option\s+[abcd]|option\s+[abcd])",
        content_lower
    ))
    tradeoffs_present = bool(re.search(
        r"trade.?off|tradeoff|downside|drawback|cost|risk|limitation|caveat|however|but\s+(it|this|the)",
        content_lower
    ))
    decision_with_tradeoffs = decision_present and tradeoffs_present
    checks.append({
        "name": "synthesis_decision_with_tradeoffs",
        "passed": decision_with_tradeoffs,
        "detail": (
            f"Synthesis must make a final decision AND document trade-offs. "
            f"Decision found: {decision_present}, Trade-offs found: {tradeoffs_present}"
        )
    })

    # ------------------------------------------------------------------ #
    # CHECK 4: Addresses the actual domain context (not generic boilerplate)
    # Must reference the specific feature context from the brief
    # ------------------------------------------------------------------ #
    domain_context_signals = [
        r"dosage|medication|drug",
        r"fda|samd|class\s+ii|regulatory",
        r"71%|concordance|clinical\s+trial",
        r"phi|hipaa|protected\s+health",
        r"pilot|launch|delay|abandon",
    ]
    domain_hits = sum(1 for p in domain_context_signals if re.search(p, content_lower))
    domain_grounded = domain_hits >= 3

    checks.append({
        "name": "domain_context_grounded",
        "passed": domain_grounded,
        "detail": (
            f"Document must reference specific context from the brief (dosage, FDA/SaMD, trial data, PHI, decision options). "
            f"Found {domain_hits}/5 domain signals."
        )
    })

    # ------------------------------------------------------------------ #
    # CHECK 5: Minimum document length (substantive, not a stub)
    # ------------------------------------------------------------------ #
    word_count = len(content.split())
    length_ok = word_count >= 600
    checks.append({
        "name": "document_is_substantive",
        "passed": length_ok,
        "detail": f"Document word count: {word_count} (minimum 600 required for a thorough multi-stakeholder analysis)."
    })

    # ------------------------------------------------------------------ #
    # SCORING
    # ------------------------------------------------------------------ #
    # Weights: perspective count and synthesis correctness are most critical
    weight_map = {
        "file_exists": 0.05,
        "required_medical_roles_present": 0.15,
        "minimum_5_perspectives": 0.15,
        "divergence_section_present": 0.05,
        "synthesis_section_present": 0.05,
        "synthesis_conflicts_identified": 0.10,
        "synthesis_common_ground": 0.10,
        "synthesis_safety_weighted_over_preferences": 0.15,
        "synthesis_decision_with_tradeoffs": 0.10,
        "domain_context_grounded": 0.05,
        "document_is_substantive": 0.05,
    }

    total_score = sum(
        weight_map.get(c["name"], 0.0) * (1.0 if c["passed"] else 0.0)
        for c in checks
    )

    # Must pass the two most critical checks to overall pass
    critical_checks = [
        "minimum_5_perspectives",
        "synthesis_safety_weighted_over_preferences",
        "synthesis_decision_with_tradeoffs",
        "required_medical_roles_present",
    ]
    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == name), False)
        for name in critical_checks
    )

    overall_passed = critical_passed and total_score >= 0.65

    return {
        "passed": overall_passed,
        "score": round(total_score, 3),
        "checks": checks,
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))