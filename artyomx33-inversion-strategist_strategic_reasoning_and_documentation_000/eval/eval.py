import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []

    # --- Locate the output file ---
    target_files = list(workspace.rglob("failure_analysis.md"))
    
    if not target_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "failure_analysis.md not found anywhere in workspace"}]
        }
    
    # Use the most recently modified if multiple
    target_file = sorted(target_files, key=lambda f: f.stat().st_mtime, reverse=True)[0]
    
    try:
        content = target_file.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_readable", "passed": False, "detail": f"Could not read file: {e}"}]
        }

    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {target_file}"})

    # --- Check 1: GOAL section present with relevant content ---
    goal_match = bool(re.search(r'GOAL\s*:', content, re.IGNORECASE))
    goal_relevant = bool(re.search(r'(GreenSprint|subscription|200\s*subscriber|subscriber|launch)', content, re.IGNORECASE))
    checks.append({
        "name": "goal_section_present_and_relevant",
        "passed": goal_match and goal_relevant,
        "detail": f"GOAL: header found={goal_match}, relevant content={goal_relevant}"
    })

    # --- Check 2: INVERTED section with correct framing ---
    # Must have "INVERTED:" and contain "guarantee failure" or "guarantee" phrasing
    inverted_match = bool(re.search(r'INVERTED\s*:', content, re.IGNORECASE))
    inverted_framing = bool(re.search(r'guarantee\s*(failure|fail)', content, re.IGNORECASE))
    checks.append({
        "name": "inverted_section_with_guarantee_framing",
        "passed": inverted_match and inverted_framing,
        "detail": f"INVERTED: header={inverted_match}, 'guarantee failure' phrasing={inverted_framing}"
    })

    # --- Check 3: FATAL category with red circle emoji ---
    fatal_with_emoji = bool(re.search(r'🔴\s*(FATAL|fatal)', content))
    checks.append({
        "name": "fatal_category_red_emoji",
        "passed": fatal_with_emoji,
        "detail": f"🔴 FATAL marker found={fatal_with_emoji}"
    })

    # --- Check 4: DAMAGING category with yellow circle emoji ---
    damaging_with_emoji = bool(re.search(r'🟡\s*(DAMAGING|damaging)', content))
    checks.append({
        "name": "damaging_category_yellow_emoji",
        "passed": damaging_with_emoji,
        "detail": f"🟡 DAMAGING marker found={damaging_with_emoji}"
    })

    # --- Check 5: ANNOYING category with green circle emoji ---
    annoying_with_emoji = bool(re.search(r'🟢\s*(ANNOYING|annoying)', content))
    checks.append({
        "name": "annoying_category_green_emoji",
        "passed": annoying_with_emoji,
        "detail": f"🟢 ANNOYING marker found={annoying_with_emoji}"
    })

    # --- Check 6: AVOID BY pattern used on failure paths ---
    avoid_by_count = len(re.findall(r'AVOID\s*BY\s*:', content, re.IGNORECASE))
    avoid_by_ok = avoid_by_count >= 5
    checks.append({
        "name": "avoid_by_pattern_used",
        "passed": avoid_by_ok,
        "detail": f"'AVOID BY:' occurrences={avoid_by_count} (need >=5)"
    })

    # --- Check 7: Minimum 7 failure paths (count bullet points under failure sections) ---
    # Count lines that are failure path entries: start with •, -, *, or numbered
    failure_path_lines = re.findall(
        r'(?:^|\n)\s*[•\-\*\d]+[\.\)]\s*.{15,}.*AVOID',
        content, re.IGNORECASE
    )
    # Also try counting bullets with arrow pattern
    arrow_paths = re.findall(r'[•\-\*]\s*.+?→\s*AVOID', content, re.IGNORECASE | re.DOTALL)
    total_paths = max(len(failure_path_lines), len(arrow_paths))
    
    # More permissive: count any line with "AVOID BY:"
    avoid_by_lines = re.findall(r'AVOID\s*BY\s*:', content, re.IGNORECASE)
    total_paths = max(total_paths, len(avoid_by_lines))
    
    min_paths_ok = total_paths >= 7
    checks.append({
        "name": "minimum_7_failure_paths",
        "passed": min_paths_ok,
        "detail": f"Estimated failure paths with AVOID BY={len(avoid_by_lines)} (need >=7)"
    })

    # --- Check 8: ANTI-CHECKLIST section with □ Never items ---
    anti_checklist_header = bool(re.search(r'ANTI[\-\s]*CHECKLIST', content, re.IGNORECASE))
    never_items = re.findall(r'□\s*Never', content, re.IGNORECASE)
    anti_checklist_ok = anti_checklist_header and len(never_items) >= 3
    checks.append({
        "name": "anti_checklist_with_never_items",
        "passed": anti_checklist_ok,
        "detail": f"ANTI-CHECKLIST header={anti_checklist_header}, '□ Never' items={len(never_items)} (need >=3)"
    })

    # --- Check 9: PRO-CHECKLIST section with □ Always items ---
    pro_checklist_header = bool(re.search(r'PRO[\-\s]*CHECKLIST', content, re.IGNORECASE))
    always_items = re.findall(r'□\s*Always', content, re.IGNORECASE)
    pro_checklist_ok = pro_checklist_header and len(always_items) >= 2
    checks.append({
        "name": "pro_checklist_with_always_items",
        "passed": pro_checklist_ok,
        "detail": f"PRO-CHECKLIST header={pro_checklist_header}, '□ Always' items={len(always_items)} (need >=2)"
    })

    # --- Check 10: Content is domain-specific (GreenSprint / cold chain / subscription / logistics) ---
    domain_keywords = ['cold chain', 'subscription', 'churn', 'delivery', 'farm', 'packaging', 'billing', 'greensprint']
    domain_hits = [kw for kw in domain_keywords if kw.lower() in content.lower()]
    domain_specific_ok = len(domain_hits) >= 4
    checks.append({
        "name": "domain_specific_content",
        "passed": domain_specific_ok,
        "detail": f"Domain keywords found: {domain_hits} ({len(domain_hits)}/8, need >=4)"
    })

    # --- Check 11: Arrow separator → used in failure paths (proprietary style) ---
    arrow_separator = bool(re.search(r'→\s*AVOID', content, re.IGNORECASE))
    checks.append({
        "name": "arrow_separator_in_failure_paths",
        "passed": arrow_separator,
        "detail": f"'→ AVOID' pattern used={arrow_separator}"
    })

    # --- Check 12: Three categories are all present (structural completeness) ---
    all_three_categories = fatal_with_emoji and damaging_with_emoji and annoying_with_emoji
    checks.append({
        "name": "all_three_categories_present",
        "passed": all_three_categories,
        "detail": f"FATAL={fatal_with_emoji}, DAMAGING={damaging_with_emoji}, ANNOYING={annoying_with_emoji}"
    })

    # --- Scoring ---
    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks)

    # Must pass these critical checks to be considered overall passed
    critical = [
        "fatal_category_red_emoji",
        "damaging_category_yellow_emoji", 
        "annoying_category_green_emoji",
        "anti_checklist_with_never_items",
        "pro_checklist_with_always_items",
        "avoid_by_pattern_used",
        "inverted_section_with_guarantee_framing",
        "minimum_7_failure_paths",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical
    )

    overall_passed = critical_passed and score >= 0.75

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    
    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))