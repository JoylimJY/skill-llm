import sys
import json
import re
from pathlib import Path

def find_output_file(workspace: Path):
    """Search for the dual_plan.md output file anywhere in the workspace."""
    candidates = list(workspace.rglob("dual_plan.md"))
    return candidates[0] if candidates else None

def load_text(path):
    return path.read_text(encoding="utf-8", errors="replace")

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace_path: str):
    workspace = Path(workspace_path)
    checks = []
    total_score = 0.0

    # ── 1. File existence ────────────────────────────────────────────────────
    output_file = find_output_file(workspace)
    if output_file is None:
        checks.append(check("output_file_exists", False, "dual_plan.md not found anywhere in workspace"))
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return
    checks.append(check("output_file_exists", True, f"Found at {output_file}"))
    total_score += 0.05

    try:
        content = load_text(output_file)
    except Exception as e:
        checks.append(check("file_readable", False, f"Cannot read file: {e}"))
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return
    checks.append(check("file_readable", True, f"File readable, {len(content)} chars"))

    content_lower = content.lower()

    # ── 2. Learning Plan Template — mandatory sections ────────────────────────
    lp_header = bool(re.search(r"##\s+learning\s+plan", content, re.IGNORECASE))
    checks.append(check(
        "learning_plan_header",
        lp_header,
        "Found '## Learning Plan' header" if lp_header else "Missing '## Learning Plan' header"
    ))
    if lp_header: total_score += 0.05

    learner_profile = bool(re.search(r"###\s+learner\s+profile", content, re.IGNORECASE))
    checks.append(check(
        "learner_profile_section",
        learner_profile,
        "Found '### Learner Profile' section" if learner_profile else "Missing '### Learner Profile' section"
    ))
    if learner_profile: total_score += 0.05

    goals_milestones = bool(re.search(r"###\s+goals\s+[&and]+\s+milestones", content, re.IGNORECASE))
    checks.append(check(
        "goals_milestones_section",
        goals_milestones,
        "Found 'Goals & Milestones' section" if goals_milestones else "Missing 'Goals & Milestones' section"
    ))
    if goals_milestones: total_score += 0.05

    method_mix = bool(re.search(r"###\s+method\s+mix", content, re.IGNORECASE))
    checks.append(check(
        "method_mix_section",
        method_mix,
        "Found 'Method Mix' section" if method_mix else "Missing 'Method Mix' section"
    ))
    if method_mix: total_score += 0.05

    motivation_habit = bool(re.search(r"###\s+motivation\s+[&and]+\s+habit\s+support", content, re.IGNORECASE))
    checks.append(check(
        "motivation_habit_section",
        motivation_habit,
        "Found 'Motivation & Habit Support' section" if motivation_habit else "Missing 'Motivation & Habit Support' section"
    ))
    if motivation_habit: total_score += 0.05

    risks_mitigations_lp = bool(re.search(r"###\s+risks\s+[&and]+\s+mitigations", content, re.IGNORECASE))
    checks.append(check(
        "risks_mitigations_section",
        risks_mitigations_lp,
        "Found 'Risks & Mitigations' section" if risks_mitigations_lp else "Missing 'Risks & Mitigations' section"
    ))
    if risks_mitigations_lp: total_score += 0.05

    # ── 3. Learning Plan — must incorporate learner_assessment.py output ──────
    # The script for age=32, skill=coding, context=work outputs:
    # "developmental_stage": "Early Adulthood (26-64)"
    # "recommended_approach": "Efficiency-first with deliberate practice"
    # "primary_motivation_type": "Extrinsic (career advancement)"
    age_stage = bool(re.search(r"(early adulthood|26.{0,5}64)", content_lower))
    checks.append(check(
        "learner_assessment_age_stage",
        age_stage,
        "Learner profile references 'Early Adulthood (26-64)' from assessment script output" if age_stage
        else "Missing developmental stage from learner_assessment.py output (expected 'Early Adulthood (26-64)')"
    ))
    if age_stage: total_score += 0.08

    efficiency_approach = bool(re.search(r"efficiency.{0,20}deliberate\s+practice|deliberate\s+practice.{0,20}efficiency", content_lower))
    checks.append(check(
        "learner_assessment_approach",
        efficiency_approach,
        "Plan references 'Efficiency-first with deliberate practice' from assessment output" if efficiency_approach
        else "Missing 'Efficiency-first with deliberate practice' — must incorporate learner_assessment.py output"
    ))
    if efficiency_approach: total_score += 0.08

    extrinsic_motivation = bool(re.search(r"extrinsic.{0,30}career|career.{0,30}advancement", content_lower))
    checks.append(check(
        "learner_assessment_motivation",
        extrinsic_motivation,
        "Plan references extrinsic/career motivation from assessment output" if extrinsic_motivation
        else "Missing extrinsic career motivation — must incorporate learner_assessment.py output"
    ))
    if extrinsic_motivation: total_score += 0.07

    # ── 4. Marketing/Conversion Plan Template — mandatory sections ────────────
    conv_header = bool(re.search(r"##\s+conversion\s+optimization", content, re.IGNORECASE))
    checks.append(check(
        "conversion_optimization_header",
        conv_header,
        "Found '## Conversion Optimization' header" if conv_header else "Missing '## Conversion Optimization' header"
    ))
    if conv_header: total_score += 0.05

    audience_profile = bool(re.search(r"###\s+audience\s+profile", content, re.IGNORECASE))
    checks.append(check(
        "audience_profile_section",
        audience_profile,
        "Found '### Audience Profile' section" if audience_profile else "Missing '### Audience Profile' section"
    ))
    if audience_profile: total_score += 0.04

    psych_levers = bool(re.search(r"###\s+psychological\s+levers", content, re.IGNORECASE))
    checks.append(check(
        "psychological_levers_section",
        psych_levers,
        "Found '### Psychological Levers' section" if psych_levers else "Missing '### Psychological Levers' section"
    ))
    if psych_levers: total_score += 0.04

    messaging_hierarchy = bool(re.search(r"###\s+messaging\s+hierarchy", content, re.IGNORECASE))
    checks.append(check(
        "messaging_hierarchy_section",
        messaging_hierarchy,
        "Found '### Messaging Hierarchy' section" if messaging_hierarchy else "Missing '### Messaging Hierarchy' section"
    ))
    if messaging_hierarchy: total_score += 0.04

    experiment_design = bool(re.search(r"###\s+experiment\s+design", content, re.IGNORECASE))
    checks.append(check(
        "experiment_design_section",
        experiment_design,
        "Found '### Experiment Design' section" if experiment_design else "Missing '### Experiment Design' section"
    ))
    if experiment_design: total_score += 0.04

    # ── 5. Ethical Validation — checkbox format (critical proprietary trap) ───
    # Must use ☐ or ☑ checkbox symbols from the SKILL.md template
    checkbox_format = bool(re.search(r"[☐☑✅✓].*no\s+deception|[☐☑✅✓].*dark\s+pattern|[☐☑✅✓].*transparent", content_lower))
    checks.append(check(
        "ethical_validation_checkbox_format",
        checkbox_format,
        "Ethical Validation section uses checkbox format (☐/☑) with required items" if checkbox_format
        else "Missing checkbox-format Ethical Validation section — required by SKILL.md template"
    ))
    if checkbox_format: total_score += 0.06

    ethical_section = bool(re.search(r"###\s+ethical\s+validation", content, re.IGNORECASE))
    checks.append(check(
        "ethical_validation_section",
        ethical_section,
        "Found '### Ethical Validation' section" if ethical_section else "Missing '### Ethical Validation' section"
    ))
    if ethical_section: total_score += 0.04

    # ── 6. Bias detection results must be incorporated ────────────────────────
    # bias_detector.py on the copy file should find: "guaranteed", "limited time",
    # "everyone is", "you must", "don't miss out", "risk-free", "instantly"
    # The plan must reference NEEDS_REVIEW or specific flagged phrases
    bias_incorporated = bool(re.search(
        r"(needs.{0,10}review|bias.{0,20}detect|flagged|guaranteed|limited\s+time|dark\s+pattern|scarcity|FOMO|overstatement)",
        content, re.IGNORECASE
    ))
    checks.append(check(
        "bias_detection_results_incorporated",
        bias_incorporated,
        "Plan incorporates bias detection results (flagged phrases / NEEDS_REVIEW status)" if bias_incorporated
        else "Missing bias detection results — must run bias_detector.py and incorporate findings"
    ))
    if bias_incorporated: total_score += 0.08

    # Specific check: at least 2 specific flagged phrases mentioned
    flagged_phrases = ["guaranteed", "limited time", "don't miss out", "risk-free", "instantly", "you must", "everyone is"]
    mentioned_flags = [p for p in flagged_phrases if p.lower() in content_lower]
    specific_flags_check = len(mentioned_flags) >= 2
    checks.append(check(
        "bias_specific_phrases_mentioned",
        specific_flags_check,
        f"Found {len(mentioned_flags)} specific flagged phrases mentioned: {mentioned_flags}" if specific_flags_check
        else f"Only {len(mentioned_flags)} flagged phrase(s) mentioned — need at least 2 from bias_detector output"
    ))
    if specific_flags_check: total_score += 0.06

    # ── 7. Age 32 / Python / coding context correctly targeted ───────────────
    age_32 = bool(re.search(r"\b32\b", content))
    checks.append(check(
        "correct_age_32",
        age_32,
        "Plan targets age 32 learners as specified" if age_32 else "Age 32 not mentioned — wrong learner profile targeted"
    ))
    if age_32: total_score += 0.04

    python_coding = bool(re.search(r"\b(python|coding|programming)\b", content_lower))
    checks.append(check(
        "correct_skill_python_coding",
        python_coding,
        "Plan addresses Python/coding skill" if python_coding else "Python/coding skill not mentioned"
    ))
    if python_coding: total_score += 0.03

    # ── 8. Goals & Milestones table format ───────────────────────────────────
    table_format = bool(re.search(r"\|\s*week\s*\|.+\|\s*goal\s*\||\|\s*goal\s*\|.+\|\s*week\s*\|", content_lower))
    checks.append(check(
        "goals_milestones_table_format",
        table_format,
        "Goals & Milestones uses markdown table with Week/Goal columns" if table_format
        else "Goals & Milestones table missing Week/Goal column headers — required by SKILL.md template"
    ))
    if table_format: total_score += 0.05

    # ── 9. Messaging Hierarchy numbered list (Primary Promise, Proof Point…) ──
    msg_hierarchy_items = bool(re.search(
        r"(primary\s+promise|proof\s+point|differentiator|risk\s+reduc)",
        content_lower
    ))
    checks.append(check(
        "messaging_hierarchy_items",
        msg_hierarchy_items,
        "Messaging Hierarchy contains required items (Primary Promise, Proof Point, etc.)" if msg_hierarchy_items
        else "Messaging Hierarchy missing required items from SKILL.md template"
    ))
    if msg_hierarchy_items: total_score += 0.05

    # ── Final scoring ─────────────────────────────────────────────────────────
    total_score = min(round(total_score, 3), 1.0)
    passed_checks = sum(1 for c in checks if c["passed"])
    overall_passed = total_score >= 0.65 and passed_checks >= 14

    result = {
        "passed": overall_passed,
        "score": total_score,
        "checks": checks,
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace)