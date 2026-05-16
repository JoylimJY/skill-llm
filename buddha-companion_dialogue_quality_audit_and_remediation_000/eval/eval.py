import sys
import json
import os
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    
    # Find the output file
    target_path = Path(workspace_dir) / "platform" / "data" / "processed" / "dialogue_audit_report.json"
    
    # Also search anywhere in workspace in case agent placed it differently
    found_paths = list(Path(workspace_dir).rglob("dialogue_audit_report.json"))
    
    # --- Check 1: File existence ---
    file_exists = target_path.exists() or len(found_paths) > 0
    actual_path = target_path if target_path.exists() else (found_paths[0] if found_paths else None)
    
    checks.append({
        "name": "output_file_exists",
        "passed": file_exists,
        "detail": f"dialogue_audit_report.json found at: {actual_path}" if file_exists else "dialogue_audit_report.json not found anywhere in workspace"
    })
    
    if not file_exists:
        return {"passed": False, "score": 0.0, "checks": checks}
    
    # --- Load JSON ---
    try:
        with open(actual_path, "r", encoding="utf-8") as f:
            report = json.load(f)
    except Exception as e:
        checks.append({"name": "json_parseable", "passed": False, "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "json_parseable", "passed": True, "detail": "JSON parsed successfully"})
    
    # --- Check 2: All 5 dialogue IDs present ---
    required_ids = {"dlg_001", "dlg_002", "dlg_003", "dlg_004", "dlg_005"}
    
    if isinstance(report, list):
        entries = report
    elif isinstance(report, dict) and "dialogues" in report:
        entries = report["dialogues"]
    elif isinstance(report, dict) and "results" in report:
        entries = report["results"]
    else:
        # Try to extract any list value
        entries = []
        for v in report.values():
            if isinstance(v, list):
                entries = v
                break
    
    found_ids = set()
    for entry in entries:
        if isinstance(entry, dict):
            for key in ["id", "dialogue_id", "dlg_id"]:
                if key in entry:
                    found_ids.add(entry[key])
    
    all_ids_present = required_ids.issubset(found_ids)
    checks.append({
        "name": "all_five_dialogues_present",
        "passed": all_ids_present,
        "detail": f"Found IDs: {found_ids}. Required: {required_ids}"
    })
    
    # --- Check 3: Each entry has required structural fields ---
    required_fields_variants = [
        # attachment/stuck point field
        ["attachment", "core_attachment", "stuck_point", "执着点", "用户执着", "卡点"],
        # remediated response field
        ["remediated_response", "corrected_response", "new_response", "improved_response", "修正回应", "修正后回应"],
        # stage classification field  
        ["stage", "practitioner_stage", "development_stage", "觉察阶段", "修行阶段", "stage_classification"],
        # violations field
        ["violations", "principle_violations", "violated_principles", "问题", "违反原则"],
    ]
    
    entries_with_all_fields = 0
    field_details = []
    
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        entry_id = entry.get("id") or entry.get("dialogue_id") or "unknown"
        if entry_id not in required_ids:
            continue
        
        has_all = True
        for field_group in required_fields_variants:
            found_field = any(f in entry for f in field_group)
            if not found_field:
                has_all = False
                field_details.append(f"{entry_id} missing field from group {field_group[:2]}")
        
        if has_all:
            entries_with_all_fields += 1
    
    structural_ok = entries_with_all_fields >= 4  # At least 4 of 5
    checks.append({
        "name": "entries_have_required_fields",
        "passed": structural_ok,
        "detail": f"{entries_with_all_fields}/5 entries have all required fields. Issues: {field_details[:3]}"
    })
    
    # --- Check 4: Stage classifications use the correct 3-tier system (初级/中级/高级) ---
    stage_field_candidates = ["stage", "practitioner_stage", "development_stage", "觉察阶段", "修行阶段", "stage_classification"]
    valid_stage_values = {"初级", "中级", "高级", "beginner", "intermediate", "advanced", 
                          "初级觉察", "中级觉察", "高级觉察"}
    
    stages_found = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        entry_id = entry.get("id") or entry.get("dialogue_id") or ""
        if entry_id not in required_ids:
            continue
        for f in stage_field_candidates:
            if f in entry:
                stages_found.append(str(entry[f]))
                break
    
    valid_stages_count = sum(1 for s in stages_found if any(v in s for v in valid_stage_values))
    stage_classification_ok = valid_stages_count >= 4
    checks.append({
        "name": "stage_classifications_use_3tier_system",
        "passed": stage_classification_ok,
        "detail": f"Valid stage values found: {stages_found}. Expected values from {{初级, 中级, 高级}} system. Valid count: {valid_stages_count}/5"
    })
    
    # --- Check 5: Remediated responses are SHORT (not verbose like originals) ---
    # The skill mandates 少说 - short, piercing responses. Flawed originals are 100+ chars each.
    # Compliant responses should be significantly shorter.
    response_field_candidates = ["remediated_response", "corrected_response", "new_response", "improved_response", "修正回应", "修正后回应"]
    
    response_lengths = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        entry_id = entry.get("id") or entry.get("dialogue_id") or ""
        if entry_id not in required_ids:
            continue
        for f in response_field_candidates:
            if f in entry and isinstance(entry[f], str):
                response_lengths.append(len(entry[f]))
                break
    
    # Original flawed responses are 200-400 chars. Compliant should be under 120 chars.
    short_responses = sum(1 for l in response_lengths if l < 150)
    brevity_ok = short_responses >= 3  # At least 3 of 5 should be brief
    checks.append({
        "name": "remediated_responses_are_brief",
        "passed": brevity_ok,
        "detail": f"Response lengths: {response_lengths}. Responses under 150 chars: {short_responses}/5. Skill requires 少说 (brevity). Originals were 200-400 chars."
    })
    
    # --- Check 6: Remediated responses contain questions (问 technique) ---
    # The skill's 心法提醒 explicitly says 问：把球踢回去
    question_markers = ["？", "?", "吗", "呢", "嘛"]
    responses_with_questions = 0
    question_detail = []
    
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        entry_id = entry.get("id") or entry.get("dialogue_id") or ""
        if entry_id not in required_ids:
            continue
        for f in response_field_candidates:
            if f in entry and isinstance(entry[f], str):
                resp = entry[f]
                has_question = any(m in resp for m in question_markers)
                if has_question:
                    responses_with_questions += 1
                else:
                    question_detail.append(f"{entry_id}: no question found in: '{resp[:60]}...'")
                break
    
    questioning_ok = responses_with_questions >= 3
    checks.append({
        "name": "remediated_responses_use_question_technique",
        "passed": questioning_ok,
        "detail": f"Responses containing questions: {responses_with_questions}/5. Skill mandates '问：把球踢回去'. Issues: {question_detail[:2]}"
    })
    
    # --- Check 7: Violations identified - must call out specific principles (not generic) ---
    # Should identify: 废话太多, 给答案, 证明自己懂, 渡己姿态, or similar
    violation_field_candidates = ["violations", "principle_violations", "violated_principles", "问题", "违反原则"]
    violation_keywords = [
        "废话", "答案", "证明", "渡己", "说教", "评判", "少说", "啰嗦",
        "advice", "verbose", "lecturing", "judging", "proving", "塞答案",
        "不问", "建议", "方法", "技巧", "方向", "边界", "力道"
    ]
    
    entries_with_meaningful_violations = 0
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        entry_id = entry.get("id") or entry.get("dialogue_id") or ""
        if entry_id not in required_ids:
            continue
        for f in violation_field_candidates:
            if f in entry:
                violation_val = entry[f]
                violation_str = json.dumps(violation_val, ensure_ascii=False) if not isinstance(violation_val, str) else violation_val
                if any(kw in violation_str for kw in violation_keywords) and len(violation_str) > 5:
                    entries_with_meaningful_violations += 1
                break
    
    violations_ok = entries_with_meaningful_violations >= 3
    checks.append({
        "name": "violations_identify_specific_principles",
        "passed": violations_ok,
        "detail": f"Entries with meaningful principle violations identified: {entries_with_meaningful_violations}/5. Must reference skill principles like 废话/说教/给答案/证明自己."
    })
    
    # --- Check 8: Attachment/stuck point analysis is specific per dialogue ---
    # Each entry should identify a unique, specific attachment point, not generic text
    attachment_field_candidates = ["attachment", "core_attachment", "stuck_point", "执着点", "用户执着", "卡点"]
    
    attachment_values = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        entry_id = entry.get("id") or entry.get("dialogue_id") or ""
        if entry_id not in required_ids:
            continue
        for f in attachment_field_candidates:
            if f in entry and isinstance(entry[f], str) and len(entry[f]) > 3:
                attachment_values.append(entry[f])
                break
    
    # Check they're not all identical (meaningful analysis)
    unique_attachments = len(set(attachment_values))
    attachment_ok = len(attachment_values) >= 4 and unique_attachments >= 4
    checks.append({
        "name": "attachment_analysis_is_specific_and_unique",
        "passed": attachment_ok,
        "detail": f"Found {len(attachment_values)} attachment analyses, {unique_attachments} unique. All must be specific to each user's situation."
    })
    
    # --- Check 9: dlg_003 (meditation/practice confusion) classified correctly ---
    # This is a 修行 question - the user is trying to CONTROL thoughts.
    # The correct awareness stage for "wanting to control thoughts" is 初级 (knows they have thoughts, wants to suppress).
    # The skill says: 修的是"看到"，不是"做到" - user is stuck at wanting to DO not SEE.
    dlg_003_stage = None
    dlg_003_entry = None
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        entry_id = entry.get("id") or entry.get("dialogue_id") or ""
        if entry_id == "dlg_003":
            dlg_003_entry = entry
            for f in stage_field_candidates:
                if f in entry:
                    dlg_003_stage = str(entry[f])
                    break
    
    # dlg_003 user is at 初级 (knows thoughts exist) - should NOT be classified as 高级
    dlg_003_stage_ok = dlg_003_stage is not None and "高级" not in dlg_003_stage
    checks.append({
        "name": "dlg_003_not_misclassified_as_advanced",
        "passed": dlg_003_stage_ok,
        "detail": f"dlg_003 (user trying to control meditation thoughts) stage: '{dlg_003_stage}'. Should be 初级 or 中级, not 高级. User is at control-seeking stage, not observation stage."
    })
    
    # --- Check 10: Remediated response for dlg_001 avoids giving advice/fixes ---
    # dlg_001 user says "天生这样改不了" - they are stuck on a fixed self-concept
    # Compliant response must NOT give lifestyle tips, must point to the attachment of "fixed self"
    dlg_001_response = None
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        entry_id = entry.get("id") or entry.get("dialogue_id") or ""
        if entry_id == "dlg_001":
            for f in response_field_candidates:
                if f in entry and isinstance(entry[f], str):
                    dlg_001_response = entry[f]
                    break
    
    # Advice keywords that should NOT appear in a compliant response
    advice_patterns = ["冥想", "运动", "饮食", "番茄", "书", "步骤", "方法", "技巧", "试试", "可以"]
    dlg_001_ok = False
    dlg_001_detail = "dlg_001 response not found"
    if dlg_001_response:
        bad_advice_found = [p for p in advice_patterns if p in dlg_001_response]
        dlg_001_ok = len(bad_advice_found) == 0
        dlg_001_detail = f"dlg_001 response: '{dlg_001_response[:100]}'. Forbidden advice patterns found: {bad_advice_found}"
    
    checks.append({
        "name": "dlg_001_response_avoids_advice_giving",
        "passed": dlg_001_ok,
        "detail": dlg_001_detail
    })
    
    # --- Compute final score ---
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks
    
    # Must pass core structural checks + at least 6 total to pass
    core_checks_passed = all(
        c["passed"] for c in checks 
        if c["name"] in ["output_file_exists", "json_parseable", "all_five_dialogues_present"]
    )
    overall_passed = core_checks_passed and passed_checks >= 7
    
    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))