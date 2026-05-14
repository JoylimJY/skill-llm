import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    workspace = Path(workspace_dir)

    # --- Find the threat model file ---
    candidates = list(workspace.rglob("paystream_threat_model.md"))
    if not candidates:
        # Try alternate naming
        candidates = list(workspace.rglob("threat_model*.md"))

    file_found = len(candidates) > 0
    checks.append({
        "name": "threat_model_file_exists",
        "passed": file_found,
        "detail": f"Found: {candidates[0]}" if file_found else "No paystream_threat_model.md found anywhere in workspace"
    })

    if not file_found:
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    try:
        content = candidates[0].read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    content_lower = content.lower()

    # =========================================================
    # CHECK 1: Required top-level sections from Output Template
    # =========================================================
    required_sections = ["## scope", "## assets", "## trust boundaries", "## data flow diagram",
                         "## stride analysis", "## prioritized threats", "## residual risks", "## review schedule"]
    missing_sections = []
    for s in required_sections:
        if s not in content_lower:
            missing_sections.append(s)
    sections_ok = len(missing_sections) == 0
    checks.append({
        "name": "required_output_template_sections",
        "passed": sections_ok,
        "detail": f"Missing sections: {missing_sections}" if missing_sections else "All 8 required sections present"
    })

    # =========================================================
    # CHECK 2: STRIDE table — all 6 STRIDE categories present as columns
    # =========================================================
    stride_categories = ["spoofing", "tampering", "repudiation", "information disclosure", "dos", "elevation"]
    # Also accept abbreviated forms
    stride_abbrev = ["spoofing", "tampering", "repudiation", "info", "dos", "elevation", "eop", "denial"]
    
    # Look in the STRIDE Analysis section
    stride_section_match = re.search(r'## stride analysis(.*?)(?=^##|\Z)', content, re.IGNORECASE | re.DOTALL | re.MULTILINE)
    stride_section = stride_section_match.group(1).lower() if stride_section_match else content_lower
    
    stride_found = []
    for cat in stride_categories:
        if cat in stride_section:
            stride_found.append(cat)
    
    # Check for table format (| separator)
    has_table = "|" in stride_section
    
    stride_ok = len(stride_found) >= 5 and has_table
    checks.append({
        "name": "stride_table_all_six_categories",
        "passed": stride_ok,
        "detail": f"Found STRIDE categories: {stride_found}, table format: {has_table}"
    })

    # =========================================================
    # CHECK 3: STRIDE table covers at least 3 system components
    # =========================================================
    components_to_check = ["api gateway", "auth", "payment", "database", "web app", "mobile", 
                           "card tokenization", "settlement", "admin", "kafka"]
    found_components = []
    for comp in components_to_check:
        if comp in stride_section:
            found_components.append(comp)
    
    components_ok = len(found_components) >= 3
    checks.append({
        "name": "stride_table_multiple_components",
        "passed": components_ok,
        "detail": f"Components found in STRIDE table: {found_components}"
    })

    # =========================================================
    # CHECK 4: Attack tree — must use hierarchical tree notation
    # The skill shows: ├── │ └── notation
    # =========================================================
    # Look for tree-like characters
    has_tree_chars = any(c in content for c in ["├──", "└──", "│   ", "│\t"])
    # Also accept markdown indented lists as a fallback, but tree notation preferred
    has_indented_list_tree = bool(re.search(r'Goal:.*\n(\s+[-*].*\n){3,}', content, re.IGNORECASE))
    
    attack_tree_section_match = re.search(r'(attack tree|goal:.*\n)', content, re.IGNORECASE)
    has_attack_tree_section = attack_tree_section_match is not None
    
    attack_tree_ok = has_tree_chars and has_attack_tree_section
    checks.append({
        "name": "attack_tree_with_proper_notation",
        "passed": attack_tree_ok,
        "detail": f"Tree chars (├──/└──): {has_tree_chars}, Attack tree section: {has_attack_tree_section}"
    })

    # =========================================================
    # CHECK 5: Attack tree has at least 2 levels of branches
    # (at least one sub-branch under a main branch)
    # =========================================================
    # Count tree notation lines
    tree_lines = [line for line in content.split('\n') if '├──' in line or '└──' in line or '│' in line]
    has_multilevel = len(tree_lines) >= 5
    checks.append({
        "name": "attack_tree_multilevel_branches",
        "passed": has_multilevel,
        "detail": f"Tree notation lines found: {len(tree_lines)} (need >= 5)"
    })

    # =========================================================
    # CHECK 6: DREAD scoring — must have numeric scores for 5 factors
    # The skill requires: Damage, Reproducibility, Exploitability, Affected Users, Discoverability
    # Score: Sum / 5 = Risk Level
    # =========================================================
    dread_factors = ["damage", "reproducib", "exploitab", "affected", "discoverab"]
    dread_found = []
    for factor in dread_factors:
        if factor in content_lower:
            dread_found.append(factor)
    
    # Check for numeric DREAD scores (pattern: factor: number or factor | number)
    has_dread_numbers = bool(re.search(
        r'(damage|reproducib|exploitab|affected|discoverab)[^\n]*\d+', 
        content, re.IGNORECASE
    ))
    
    # Check for the Sum/5 formula or risk level calculation
    has_dread_formula = bool(re.search(
        r'(sum\s*/\s*5|total\s*/\s*5|score\s*[:=]\s*\d+\.?\d*\s*/\s*5|risk\s+level\s*[:=]\s*\d)', 
        content, re.IGNORECASE
    ))
    
    dread_ok = len(dread_found) >= 4 and has_dread_numbers
    checks.append({
        "name": "dread_scoring_five_factors_numeric",
        "passed": dread_ok,
        "detail": f"DREAD factors found: {dread_found}, numeric scores: {has_dread_numbers}"
    })

    checks.append({
        "name": "dread_sum_over_5_formula",
        "passed": has_dread_formula,
        "detail": f"DREAD Sum/5 formula or risk level calculation found: {has_dread_formula}"
    })

    # =========================================================
    # CHECK 7: Prioritized threats list with severity labels
    # Skill template: 1. [High] Description - Mitigation
    # =========================================================
    threat_section_match = re.search(r'## prioritized threats(.*?)(?=^##|\Z)', content, re.IGNORECASE | re.DOTALL | re.MULTILINE)
    threat_section = threat_section_match.group(1) if threat_section_match else ""
    
    # Must have severity markers
    has_severity_labels = bool(re.search(r'\[(high|medium|low|critical)\]', threat_section, re.IGNORECASE))
    # Must have at least 3 prioritized threats
    threat_count = len(re.findall(r'^\s*\d+\.\s*\[', threat_section, re.MULTILINE))
    
    prioritized_ok = has_severity_labels and threat_count >= 3
    checks.append({
        "name": "prioritized_threats_with_severity_labels",
        "passed": prioritized_ok,
        "detail": f"Severity labels: {has_severity_labels}, numbered threats: {threat_count}"
    })

    # =========================================================
    # CHECK 8: Residual Risks section has content
    # =========================================================
    residual_section_match = re.search(r'## residual risks(.*?)(?=^##|\Z)', content, re.IGNORECASE | re.DOTALL | re.MULTILINE)
    residual_section = residual_section_match.group(1).strip() if residual_section_match else ""
    residual_ok = len(residual_section) > 50
    checks.append({
        "name": "residual_risks_section_has_content",
        "passed": residual_ok,
        "detail": f"Residual risks content length: {len(residual_section)} chars"
    })

    # =========================================================
    # CHECK 9: Review Schedule section has content
    # =========================================================
    review_section_match = re.search(r'## review schedule(.*?)(?=^##|\Z)', content, re.IGNORECASE | re.DOTALL | re.MULTILINE)
    review_section = review_section_match.group(1).strip() if review_section_match else ""
    review_ok = len(review_section) > 10
    checks.append({
        "name": "review_schedule_section_has_content",
        "passed": review_ok,
        "detail": f"Review schedule content length: {len(review_section)} chars"
    })

    # =========================================================
    # CHECK 10: System-specific content — references PayStream components
    # Agent must have read the architecture docs, not produce a generic template
    # =========================================================
    paystream_specific = ["api gateway", "card tokenization", "settlement", "fraud", "kafka", "payment processor", "auth service"]
    found_specific = [t for t in paystream_specific if t in content_lower]
    specific_ok = len(found_specific) >= 4
    checks.append({
        "name": "paystream_specific_components_referenced",
        "passed": specific_ok,
        "detail": f"PayStream-specific components found: {found_specific}"
    })

    # =========================================================
    # CHECK 11: Trust Boundaries section — must distinguish at least 2 boundaries
    # =========================================================
    trust_section_match = re.search(r'## trust boundaries(.*?)(?=^##|\Z)', content, re.IGNORECASE | re.DOTALL | re.MULTILINE)
    trust_section = trust_section_match.group(1).lower() if trust_section_match else ""
    
    trust_concepts = ["external", "internal", "admin", "public", "private", "vpn", "internet", "user", "merchant"]
    found_trust = [t for t in trust_concepts if t in trust_section]
    trust_ok = len(found_trust) >= 2 and len(trust_section.strip()) > 30
    checks.append({
        "name": "trust_boundaries_section_has_boundaries",
        "passed": trust_ok,
        "detail": f"Trust boundary concepts found: {found_trust}"
    })

    # =========================================================
    # CHECK 12: Data Flow Diagram section exists and has DFD elements
    # =========================================================
    dfd_section_match = re.search(r'## data flow diagram(.*?)(?=^##|\Z)', content, re.IGNORECASE | re.DOTALL | re.MULTILINE)
    dfd_section = dfd_section_match.group(1) if dfd_section_match else ""
    
    # Must have arrows (→ or ->) showing data flow
    has_arrows = bool(re.search(r'(→|->|<-|←)', dfd_section))
    dfd_ok = len(dfd_section.strip()) > 50 and has_arrows
    checks.append({
        "name": "dfd_section_with_flow_arrows",
        "passed": dfd_ok,
        "detail": f"DFD content length: {len(dfd_section.strip())}, arrows present: {has_arrows}"
    })

    # =========================================================
    # CHECK 13: Risk Prioritization Matrix — HIGH/MEDIUM/LOW classification
    # Skill specifies: HIGH LIKELIHOOD + HIGH IMPACT = HIGH, etc.
    # =========================================================
    has_risk_matrix_concepts = bool(re.search(
        r'(high\s+(likelihood|impact|risk)|likelihood.*impact|impact.*likelihood)',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "risk_likelihood_impact_classification",
        "passed": has_risk_matrix_concepts,
        "detail": f"Risk matrix (likelihood/impact) concepts present: {has_risk_matrix_concepts}"
    })

    # =========================================================
    # SCORING
    # =========================================================
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)
    
    # Must pass all critical checks to pass overall
    critical_checks = [
        "threat_model_file_exists",
        "required_output_template_sections",
        "stride_table_all_six_categories",
        "attack_tree_with_proper_notation",
        "dread_scoring_five_factors_numeric",
        "prioritized_threats_with_severity_labels",
        "paystream_specific_components_referenced",
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )
    
    overall_passed = critical_passed and score >= 0.75

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))