import sys
import json
import re
from pathlib import Path
from datetime import datetime

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # -------------------------------------------------------------------------
    # CHECK 1: File exists at memory/thinking-YYYY-MM-DD.md
    # -------------------------------------------------------------------------
    memory_dir = workspace / "memory"
    thinking_files = list(memory_dir.glob("thinking-????-??-??.md"))
    
    if not thinking_files:
        # Also check rglob in case agent put it slightly differently
        thinking_files = list(workspace.rglob("thinking-????-??-??.md"))

    if not thinking_files:
        checks.append({
            "name": "thinking_file_exists",
            "passed": False,
            "detail": "No file matching 'thinking-YYYY-MM-DD.md' found in memory/ directory."
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    # Use the most recently modified thinking file
    thinking_file = sorted(thinking_files, key=lambda f: f.stat().st_mtime, reverse=True)[0]
    total_score += add_check(
        "thinking_file_exists",
        True,
        f"Found thinking file: {thinking_file.relative_to(workspace)}"
    )

    # Validate filename date format
    fname = thinking_file.name
    date_match = re.match(r"thinking-(\d{4}-\d{2}-\d{2})\.md$", fname)
    date_valid = False
    if date_match:
        try:
            datetime.strptime(date_match.group(1), "%Y-%m-%d")
            date_valid = True
        except ValueError:
            pass
    total_score += add_check(
        "filename_date_format_valid",
        date_valid,
        f"Filename '{fname}' {'has valid' if date_valid else 'has INVALID'} YYYY-MM-DD date format."
    )

    # Read content
    try:
        content = thinking_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": total_score / 10.0, "checks": checks}

    total_score += add_check("file_readable", True, "File is readable and non-empty." if content.strip() else "File is empty.", 0.5)

    # -------------------------------------------------------------------------
    # CHECK 2: Business context — mentions WMS / warehouse selection problem
    # -------------------------------------------------------------------------
    wms_keywords = ["WMS", "仓库", "仓储", "SAP", "Oracle", "warehouse", "EWM", "供应商", "选型"]
    wms_mentioned = any(kw.lower() in content.lower() for kw in wms_keywords)
    total_score += add_check(
        "business_context_wms",
        wms_mentioned,
        "Content references WMS/warehouse selection context." if wms_mentioned
        else "Content does NOT reference the WMS selection business problem."
    )

    # -------------------------------------------------------------------------
    # CHECK 3: Standard 8-step section headers present
    # The SKILL.md specifies: ## 步骤 N：<title>
    # -------------------------------------------------------------------------
    step_pattern = re.compile(r"##\s*步骤\s*(\d+)[：:]", re.MULTILINE)
    step_matches = step_pattern.findall(content)
    step_numbers = [int(n) for n in step_matches]
    unique_steps = sorted(set(step_numbers))

    has_min_steps = len(unique_steps) >= 6
    total_score += add_check(
        "minimum_6_step_sections",
        has_min_steps,
        f"Found step sections: {unique_steps}. {'OK (≥6)' if has_min_steps else 'FAIL (<6 steps)'}",
        weight=1.5
    )

    # Check that steps include at least steps 1 through 6 in sequence
    required_steps = {1, 2, 3, 4, 5, 6}
    has_required = required_steps.issubset(set(step_numbers))
    total_score += add_check(
        "required_steps_1_through_6",
        has_required,
        f"Steps 1-6 all present: {has_required}. Found: {unique_steps}"
    )

    # Check steps 7 and 8 (评估选择 and 实施反馈)
    has_step_7 = 7 in step_numbers
    has_step_8 = 8 in step_numbers
    total_score += add_check(
        "steps_7_and_8_present",
        has_step_7 and has_step_8,
        f"Step 7 present: {has_step_7}, Step 8 present: {has_step_8}."
    )

    # -------------------------------------------------------------------------
    # CHECK 4: Branch section present
    # SKILL.md format: branch with branchId/方案 in a section header or JSON block
    # -------------------------------------------------------------------------
    branch_patterns = [
        r"branchFromThought",
        r"branchId",
        r"分支",
        r"方案[AB]",
        r"Branch",
    ]
    has_branch = any(re.search(p, content) for p in branch_patterns)
    total_score += add_check(
        "branch_exploration_present",
        has_branch,
        "Branch exploration (branchFromThought/branchId/分支) found in document." if has_branch
        else "No branch exploration found. SKILL.md requires branching when comparing alternatives.",
        weight=1.5
    )

    # -------------------------------------------------------------------------
    # CHECK 5: Revision present
    # SKILL.md format: isRevision: true / revisesThought
    # -------------------------------------------------------------------------
    revision_patterns = [
        r"isRevision[:\s]+true",
        r"revisesThought",
        r"修订",
        r"修正",
        r"isRevision.*true",
    ]
    has_revision = any(re.search(p, content, re.IGNORECASE) for p in revision_patterns)
    total_score += add_check(
        "revision_step_present",
        has_revision,
        "Revision step (isRevision/revisesThought/修订) found in document." if has_revision
        else "No revision step found. SKILL.md requires revising earlier thoughts when errors are discovered.",
        weight=1.5
    )

    # -------------------------------------------------------------------------
    # CHECK 6: nextThoughtNeeded: false on final step
    # -------------------------------------------------------------------------
    next_thought_false_patterns = [
        r"nextThoughtNeeded[:\s]+false",
        r'"nextThoughtNeeded"\s*:\s*false',
        r"nextThoughtNeeded.*false",
    ]
    has_final_false = any(re.search(p, content, re.IGNORECASE) for p in next_thought_false_patterns)
    total_score += add_check(
        "final_step_nextThoughtNeeded_false",
        has_final_false,
        "Final step correctly marks nextThoughtNeeded as false." if has_final_false
        else "Missing nextThoughtNeeded: false on final step. SKILL.md requires this to signal completion."
    )

    # -------------------------------------------------------------------------
    # CHECK 7: thoughtNumber and totalThoughts fields present
    # -------------------------------------------------------------------------
    has_thought_number = bool(re.search(r"thoughtNumber[:\s]+\d+", content, re.IGNORECASE) or
                               re.search(r'"thoughtNumber"\s*:\s*\d+', content))
    has_total_thoughts = bool(re.search(r"totalThoughts[:\s]+\d+", content, re.IGNORECASE) or
                               re.search(r'"totalThoughts"\s*:\s*\d+', content))
    total_score += add_check(
        "thought_metadata_fields_present",
        has_thought_number and has_total_thoughts,
        f"thoughtNumber present: {has_thought_number}, totalThoughts present: {has_total_thoughts}."
    )

    # -------------------------------------------------------------------------
    # CHECK 8: totalThoughts increases after branching
    # Check that there are at least two different totalThoughts values
    # (initial estimate, then increased for branch exploration)
    # -------------------------------------------------------------------------
    total_thoughts_values = re.findall(r"totalThoughts[:\s]+(\d+)", content, re.IGNORECASE)
    total_thoughts_values += re.findall(r'"totalThoughts"\s*:\s*(\d+)', content)
    unique_totals = set(int(v) for v in total_thoughts_values)
    
    has_increasing_totals = len(unique_totals) > 1 and (max(unique_totals) > min(unique_totals))
    total_score += add_check(
        "totalThoughts_increases_for_branch",
        has_increasing_totals,
        f"totalThoughts values found: {sorted(unique_totals)}. {'Correctly increases for branch.' if has_increasing_totals else 'Should increase when branching per SKILL.md.'}",
        weight=1.0
    )

    # -------------------------------------------------------------------------
    # CHECK 9: Markdown H1 title present (# 思考记录：...)
    # -------------------------------------------------------------------------
    has_title = bool(re.search(r"#\s*思考记录[：:]", content))
    total_score += add_check(
        "markdown_title_present",
        has_title,
        "Document has '# 思考记录：...' title as specified in SKILL.md." if has_title
        else "Missing '# 思考记录：...' title header."
    )

    # -------------------------------------------------------------------------
    # CHECK 10: 评估选择 (evaluation/comparison) section mentions both SAP and Oracle
    # -------------------------------------------------------------------------
    evaluation_section_match = re.search(r"##\s*步骤\s*7[：:].*?(?=##\s*步骤|\Z)", content, re.DOTALL)
    if evaluation_section_match:
        eval_section = evaluation_section_match.group(0)
        has_comparison = ("SAP" in eval_section or "EWM" in eval_section) and \
                         ("Oracle" in eval_section or "SaaS" in eval_section or "云" in eval_section)
        total_score += add_check(
            "evaluation_section_compares_both_vendors",
            has_comparison,
            "Step 7 (评估选择) compares SAP EWM vs Oracle WMS Cloud." if has_comparison
            else "Step 7 should compare both shortlisted vendors."
        )
    else:
        total_score += add_check(
            "evaluation_section_compares_both_vendors",
            False,
            "Step 7 section not found for vendor comparison check."
        )

    # -------------------------------------------------------------------------
    # FINAL SCORING
    # -------------------------------------------------------------------------
    max_possible = sum([
        1.0,  # thinking_file_exists
        1.0,  # filename_date_format_valid
        0.5,  # file_readable
        1.0,  # business_context_wms
        1.5,  # minimum_6_step_sections
        1.0,  # required_steps_1_through_6
        1.0,  # steps_7_and_8_present
        1.5,  # branch_exploration_present
        1.5,  # revision_step_present
        1.0,  # final_step_nextThoughtNeeded_false
        1.0,  # thought_metadata_fields_present
        1.0,  # totalThoughts_increases_for_branch
        1.0,  # markdown_title_present
        1.0,  # evaluation_section_compares_both_vendors
    ])

    normalized_score = round(total_score / max_possible, 3)
    overall_passed = normalized_score >= 0.75

    return {
        "passed": overall_passed,
        "score": normalized_score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation_error", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))