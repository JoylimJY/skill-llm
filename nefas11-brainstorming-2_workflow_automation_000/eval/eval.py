import sys
import json
import re
from pathlib import Path
from datetime import date

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    today_str = date.today().isoformat()  # YYYY-MM-DD
    design_dir = workspace / "docs" / "design"

    # ── Check 1: File exists at correct path with correct naming convention ──
    check_name = "file_exists_correct_path_and_name"
    try:
        # Must be in docs/design/ and named YYYY-MM-DD-<something>.md
        # The date must match today
        pattern = f"{today_str}-*.md"
        candidates = list(design_dir.glob(pattern))
        # Exclude the distractor draft
        candidates = [f for f in candidates if f.name != "DRAFT-do-not-use.md"]
        
        if not candidates:
            # Also check if any file with wrong date exists - useful for debug
            all_md = list(design_dir.glob("*.md"))
            non_draft = [f for f in all_md if f.name != "DRAFT-do-not-use.md"]
            detail = (
                f"No file matching '{pattern}' found in docs/design/. "
                f"Files present: {[f.name for f in all_md]}"
            )
            checks.append({"name": check_name, "passed": False, "detail": detail})
            # Can't continue without a file
            score = sum(c["passed"] for c in checks) / 10.0
            return {"passed": False, "score": score, "checks": checks}
        
        design_file = candidates[0]
        # Validate slug is kebab-case (no spaces)
        slug = design_file.stem[len(today_str)+1:]
        if not slug or ' ' in slug:
            checks.append({"name": check_name, "passed": False, 
                           "detail": f"Filename slug '{slug}' contains spaces or is empty."})
        else:
            checks.append({"name": check_name, "passed": True,
                           "detail": f"Found: {design_file.name}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    # Read the file content
    try:
        content = design_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        score = sum(c["passed"] for c in checks) / 10.0
        return {"passed": False, "score": score, "checks": checks}

    # ── Check 2: Has correct top-level heading with feature name ──
    check_name = "has_feature_heading"
    try:
        # Must start with: # Feature: [Name]
        has_heading = bool(re.search(r'^#\s+Feature:\s+\S', content, re.MULTILINE))
        checks.append({
            "name": check_name,
            "passed": has_heading,
            "detail": "Found '# Feature: ...' heading" if has_heading else "Missing '# Feature: ...' heading"
        })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── Check 3: Has ## Problem section ──
    check_name = "has_problem_section"
    try:
        problem_match = re.search(r'##\s+Problem\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
        if not problem_match:
            checks.append({"name": check_name, "passed": False, "detail": "No '## Problem' section found."})
        else:
            problem_text = problem_match.group(1).strip()
            # Must be 1-2 sentences (proprietary constraint)
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', problem_text) if s.strip()]
            is_1_to_2 = 1 <= len(sentences) <= 2
            checks.append({
                "name": check_name,
                "passed": is_1_to_2,
                "detail": f"Problem section has {len(sentences)} sentence(s). Must be 1-2. Content: {problem_text[:200]}"
            })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── Check 4: Has ## Solution section (3-5 sentences) ──
    check_name = "has_solution_section_3_to_5_sentences"
    try:
        solution_match = re.search(r'##\s+Solution\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
        if not solution_match:
            checks.append({"name": check_name, "passed": False, "detail": "No '## Solution' section found."})
        else:
            solution_text = solution_match.group(1).strip()
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', solution_text) if s.strip()]
            is_3_to_5 = 3 <= len(sentences) <= 5
            checks.append({
                "name": check_name,
                "passed": is_3_to_5,
                "detail": f"Solution has {len(sentences)} sentence(s). Must be 3-5. Content: {solution_text[:300]}"
            })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── Check 5: Has ## Components Affected section with bullet+colon format ──
    check_name = "has_components_affected_with_colon_bullets"
    try:
        comp_match = re.search(r'##\s+Components Affected\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
        if not comp_match:
            checks.append({"name": check_name, "passed": False, "detail": "No '## Components Affected' section found."})
        else:
            comp_text = comp_match.group(1).strip()
            # Must have bullet points with colon-separated format: - [Component]: [Change]
            bullet_colon_lines = re.findall(r'^\s*[-*]\s+\S.*?:\s+\S', comp_text, re.MULTILINE)
            has_correct_format = len(bullet_colon_lines) >= 2
            checks.append({
                "name": check_name,
                "passed": has_correct_format,
                "detail": f"Found {len(bullet_colon_lines)} bullet-colon entries. Need >=2. Content: {comp_text[:300]}"
            })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── Check 6: Has ## Testing Strategy with Unit and Integration subsections ──
    check_name = "has_testing_strategy_with_unit_and_integration"
    try:
        test_match = re.search(r'##\s+Testing Strategy\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
        if not test_match:
            checks.append({"name": check_name, "passed": False, "detail": "No '## Testing Strategy' section found."})
        else:
            test_text = test_match.group(1)
            has_unit = bool(re.search(r'[Uu]nit\s*(test)?s?\s*:', test_text))
            has_integration = bool(re.search(r'[Ii]ntegration\s*(test)?s?\s*:', test_text))
            passed = has_unit and has_integration
            checks.append({
                "name": check_name,
                "passed": passed,
                "detail": f"Unit tests mentioned: {has_unit}, Integration tests mentioned: {has_integration}"
            })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── Check 7: Has ## Edge Cases section ──
    check_name = "has_edge_cases_section"
    try:
        edge_match = re.search(r'##\s+Edge Cases\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
        if not edge_match:
            checks.append({"name": check_name, "passed": False, "detail": "No '## Edge Cases' section found."})
        else:
            edge_text = edge_match.group(1).strip()
            bullet_items = re.findall(r'^\s*[-*]\s+\S', edge_text, re.MULTILINE)
            has_items = len(bullet_items) >= 2
            checks.append({
                "name": check_name,
                "passed": has_items,
                "detail": f"Edge Cases has {len(bullet_items)} bullet(s). Need >=2. Content: {edge_text[:200]}"
            })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── Check 8: Has ## Success Criteria with checkbox format ──
    check_name = "has_success_criteria_with_checkboxes"
    try:
        sc_match = re.search(r'##\s+Success Criteria\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
        if not sc_match:
            checks.append({"name": check_name, "passed": False, "detail": "No '## Success Criteria' section found."})
        else:
            sc_text = sc_match.group(1).strip()
            # Must use checkbox format: - [ ] ...
            checkboxes = re.findall(r'^\s*-\s+\[\s*\]\s+\S', sc_text, re.MULTILINE)
            has_checkboxes = len(checkboxes) >= 2
            checks.append({
                "name": check_name,
                "passed": has_checkboxes,
                "detail": f"Found {len(checkboxes)} checkbox item(s). Need >=2. Content: {sc_text[:300]}"
            })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── Check 9: Content reflects actual feature (Kafka/AlertService/fraud context) ──
    check_name = "content_reflects_fraud_alerting_domain"
    try:
        content_lower = content.lower()
        domain_keywords = ["kafka", "alert", "fraud", "notification", "transaction"]
        found = [kw for kw in domain_keywords if kw in content_lower]
        passed = len(found) >= 3
        checks.append({
            "name": check_name,
            "passed": passed,
            "detail": f"Domain keywords found: {found}. Need at least 3 of {domain_keywords}."
        })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── Check 10: Correct chosen approach (Option B / Kafka event-driven) reflected ──
    check_name = "reflects_chosen_approach_kafka_event_driven"
    try:
        content_lower = content.lower()
        # CTO chose Option B: Kafka event-driven AlertService
        kafka_terms = ["kafka", "event-driven", "event driven", "consumer", "alertservice", "alert service"]
        found = [t for t in kafka_terms if t in content_lower]
        passed = len(found) >= 2
        checks.append({
            "name": check_name,
            "passed": passed,
            "detail": f"Kafka/event-driven terms found: {found}. Need at least 2."
        })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── Compute final score ──
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)
    overall_passed = passed_count >= 8  # Must pass at least 8/10

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)
    
    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))