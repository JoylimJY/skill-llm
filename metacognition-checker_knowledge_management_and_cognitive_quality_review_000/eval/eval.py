import sys
import json
import re
from pathlib import Path

def load_json_safe(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except Exception as e:
        return None, str(e)

def check_report(report_data):
    checks = []
    passed_all = True

    # CHECK 1: Top-level structure — must be a list or dict with entries
    is_list = isinstance(report_data, list)
    is_dict_with_entries = isinstance(report_data, dict) and ("entries" in report_data or "results" in report_data or "analyses" in report_data)
    struct_ok = is_list or is_dict_with_entries
    checks.append({
        "name": "top_level_structure_is_list_or_entries_dict",
        "passed": struct_ok,
        "detail": f"Report is {'list' if is_list else 'dict with entries key' if is_dict_with_entries else type(report_data).__name__}"
    })
    if not struct_ok:
        passed_all = False
        return passed_all, checks

    # Normalize to list
    if is_list:
        entries = report_data
    else:
        key = next(k for k in ("entries", "results", "analyses") if k in report_data)
        entries = report_data[key]

    # CHECK 2: Must have exactly 4 entries (matching the 4 input entries)
    correct_count = len(entries) == 4
    checks.append({
        "name": "entry_count_equals_4",
        "passed": correct_count,
        "detail": f"Found {len(entries)} entries, expected 4"
    })
    if not correct_count:
        passed_all = False

    # For each entry, check the 5 required template fields
    required_field_patterns = [
        # Field 1: 判断 (judgment)
        r"(你现在的判断是|current.*judgment|judgment.*is|判断)",
        # Field 2: 事实 (facts)
        r"(你依据的事实是|facts.*basis|stated.*facts|依据的事实|facts)",
        # Field 3: 解释 (interpretation added by user)
        r"(你加入的解释是|interpretation|added.*explanation|解释)",
        # Field 4: 盲点/反例 (blind spots)
        r"(你最可能忽略的是|blind.*spot|most.*likely.*overlook|盲点|忽略)",
        # Field 5: 最小验证动作 (minimal verification action)
        r"(在继续之前.*可以先验证|minimum.*verification|minimal.*action|验证动作|验证一件事)",
    ]
    field_names = [
        "field_1_judgment_present",
        "field_2_facts_present",
        "field_3_interpretation_present",
        "field_4_blind_spots_present",
        "field_5_minimal_verification_present",
    ]

    entries_to_check = entries[:4] if len(entries) >= 4 else entries
    
    for field_idx, (pattern, fname) in enumerate(zip(required_field_patterns, field_names)):
        field_found_count = 0
        for entry in entries_to_check:
            entry_str = json.dumps(entry, ensure_ascii=False)
            if re.search(pattern, entry_str, re.IGNORECASE):
                field_found_count += 1
        field_ok = field_found_count >= 3  # at least 3 of 4 entries have this field
        checks.append({
            "name": fname,
            "passed": field_ok,
            "detail": f"Field found in {field_found_count}/4 entries (need ≥3)"
        })
        if not field_ok:
            passed_all = False

    # CHECK 3: Verification actions must be MINIMAL (single action), not a full plan
    # Look for entries where verification field contains list-like multi-step plans
    minimal_ok = True
    minimal_details = []
    for i, entry in enumerate(entries_to_check):
        entry_str = json.dumps(entry, ensure_ascii=False)
        # Find verification section
        verif_match = re.search(
            r'(验证动作|验证一件事|minimal.*action|minimum.*verif)["\s:]*([^"}{]{10,200})',
            entry_str, re.IGNORECASE | re.DOTALL
        )
        if verif_match:
            verif_text = verif_match.group(2)
            # A bad sign: more than 4 numbered steps suggests it's not minimal
            step_count = len(re.findall(r'\b[1-9]\b\.|\bstep\s+[1-9]\b|第[一二三四五六七八九]步', verif_text, re.IGNORECASE))
            if step_count > 4:
                minimal_ok = False
                minimal_details.append(f"Entry {i} verification has {step_count} steps (too many, should be minimal)")
    
    checks.append({
        "name": "verification_actions_are_minimal",
        "passed": minimal_ok,
        "detail": "; ".join(minimal_details) if minimal_details else "All verification actions appear minimal (single action focus)"
    })
    if not minimal_ok:
        passed_all = False

    # CHECK 4: Facts vs Interpretation distinction — check that field_2 and field_3 are distinct content
    # At least 2 entries should show clearly different content between "事实" and "解释"
    distinction_count = 0
    for entry in entries_to_check:
        entry_str = json.dumps(entry, ensure_ascii=False)
        # Check both fact and interpretation fields exist and are non-empty
        has_fact = bool(re.search(r'(事实|facts?)["\s:]+.{10,}', entry_str, re.IGNORECASE))
        has_interp = bool(re.search(r'(解释|interpretation)["\s:]+.{10,}', entry_str, re.IGNORECASE))
        if has_fact and has_interp:
            distinction_count += 1
    
    distinction_ok = distinction_count >= 2
    checks.append({
        "name": "fact_vs_interpretation_distinction_present",
        "passed": distinction_ok,
        "detail": f"{distinction_count}/4 entries show separate fact vs interpretation fields (need ≥2)"
    })
    if not distinction_ok:
        passed_all = False

    # CHECK 5: Blind spots should include questions (暴露盲点) not just statements
    # At least 2 entries' blind spot sections should contain a question mark
    question_count = 0
    for entry in entries_to_check:
        entry_str = json.dumps(entry, ensure_ascii=False)
        blind_match = re.search(
            r'(盲点|忽略|blind.*spot|overlook)["\s:]+([^"}{]{5,300})',
            entry_str, re.IGNORECASE | re.DOTALL
        )
        if blind_match:
            blind_text = blind_match.group(2)
            if '?' in blind_text or '？' in blind_text:
                question_count += 1

    question_ok = question_count >= 2
    checks.append({
        "name": "blind_spots_use_questions_to_expose",
        "passed": question_ok,
        "detail": f"{question_count}/4 entries use question marks in blind spot section (need ≥2, per skill rule: use questions to expose blind spots)"
    })
    if not question_ok:
        passed_all = False

    # CHECK 6: Entry IDs or submitter names must be referenced (traceability)
    id_ref_count = 0
    id_patterns = ["entry_001", "entry_002", "entry_003", "entry_004",
                   "Zhang Wei", "Priya Nair", "Carlos Mendez", "Fatima"]
    for entry in entries_to_check:
        entry_str = json.dumps(entry, ensure_ascii=False)
        if any(p.lower() in entry_str.lower() for p in id_patterns):
            id_ref_count += 1
    
    id_ok = id_ref_count >= 3
    checks.append({
        "name": "entries_reference_source_ids_or_names",
        "passed": id_ok,
        "detail": f"{id_ref_count}/4 output entries reference source entry IDs or submitter names (need ≥3)"
    })
    if not id_ok:
        passed_all = False

    return passed_all, checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    workspace_path = Path(workspace)

    all_checks = []
    final_passed = False
    final_score = 0.0

    # --- FIND THE OUTPUT FILE ---
    # Task requires: cognitive_review_report.json
    target_filename = "cognitive_review_report.json"
    found_files = list(workspace_path.rglob(target_filename))

    if not found_files:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [
                {
                    "name": "output_file_exists",
                    "passed": False,
                    "detail": f"Could not find '{target_filename}' anywhere in workspace. Agent must create this file."
                }
            ]
        }
        print(json.dumps(result))
        return

    report_file = found_files[0]
    all_checks.append({
        "name": "output_file_exists",
        "passed": True,
        "detail": f"Found at {report_file}"
    })

    # --- LOAD AND VALIDATE THE REPORT ---
    report_data, load_err = load_json_safe(report_file)
    if load_err:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": all_checks + [
                {
                    "name": "output_file_valid_json",
                    "passed": False,
                    "detail": f"Failed to parse JSON: {load_err}"
                }
            ]
        }
        print(json.dumps(result))
        return

    all_checks.append({
        "name": "output_file_valid_json",
        "passed": True,
        "detail": "File parses as valid JSON"
    })

    # --- RUN CONTENT CHECKS ---
    try:
        content_passed, content_checks = check_report(report_data)
    except Exception as e:
        content_passed = False
        content_checks = [{"name": "content_check_error", "passed": False, "detail": str(e)}]

    all_checks.extend(content_checks)

    # --- CALCULATE SCORE ---
    passed_count = sum(1 for c in all_checks if c["passed"])
    total_count = len(all_checks)
    final_score = round(passed_count / total_count, 3) if total_count > 0 else 0.0
    final_passed = final_score >= 0.75  # Need 75%+ to pass

    result = {
        "passed": final_passed,
        "score": final_score,
        "checks": all_checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()