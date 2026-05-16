import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    # Search for the output file named recruitment_package.json
    candidates = list(workspace.rglob("recruitment_package.json"))
    
    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "recruitment_package.json not found anywhere in workspace"}]
        }
    
    target_file = candidates[0]
    
    # CHECK 1: File exists and is valid JSON
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        checks.append({"name": "valid_json", "passed": True, "detail": f"File found at {target_file}, valid JSON"})
    except (json.JSONDecodeError, IOError) as e:
        checks.append({"name": "valid_json", "passed": False, "detail": f"File found but invalid JSON or unreadable: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    # CHECK 2: Contains recruitment email series (招聘 keyword output)
    # Must contain content from `email.sh series "招聘"` — 4 emails, specific Chinese content
    try:
        data_str = json.dumps(data, ensure_ascii=False)
        
        # The series command outputs specific markers for 招聘 scenario
        series_indicators = [
            "招聘场景",
            "初次触达",
            "价值传递",
            "社会证明",
            "最终邀约",
        ]
        series_hits = sum(1 for indicator in series_indicators if indicator in data_str)
        series_passed = series_hits >= 4
        checks.append({
            "name": "recruitment_series_4_emails",
            "passed": series_passed,
            "detail": f"Found {series_hits}/{len(series_indicators)} required recruitment series markers. "
                      f"Expected output from: bash scripts/email.sh series '招聘'"
        })
    except Exception as e:
        checks.append({"name": "recruitment_series_4_emails", "passed": False, "detail": f"Error checking series content: {e}"})
    
    # CHECK 3: Contains invitation template (邀请 keyword)
    # Must contain content from `email.sh template "邀请"`
    try:
        invitation_indicators = [
            "邀请邮件",
            "活动详情",
            "诚挚邀请",
            "议程",
        ]
        inv_hits = sum(1 for indicator in invitation_indicators if indicator in data_str)
        inv_passed = inv_hits >= 3
        checks.append({
            "name": "invitation_template",
            "passed": inv_passed,
            "detail": f"Found {inv_hits}/{len(invitation_indicators)} invitation template markers. "
                      f"Expected output from: bash scripts/email.sh template '邀请'"
        })
    except Exception as e:
        checks.append({"name": "invitation_template", "passed": False, "detail": f"Error checking invitation template: {e}"})
    
    # CHECK 4: Contains subject lines — exactly 5 styles
    # Must contain content from `email.sh subject "高级工程师招聘"` (or similar engineering recruitment topic)
    # Key: exactly 5 styles are generated, with specific style labels
    try:
        subject_style_patterns = [
            r"风格1",
            r"风格2",
            r"风格3",
            r"风格4",
            r"风格5",
        ]
        style_hits = sum(1 for pattern in subject_style_patterns if re.search(pattern, data_str))
        subject_passed = style_hits == 5
        checks.append({
            "name": "subject_lines_5_styles",
            "passed": subject_passed,
            "detail": f"Found {style_hits}/5 subject line style markers (风格1~风格5). "
                      f"Expected output from: bash scripts/email.sh subject '<topic>'"
        })
    except Exception as e:
        checks.append({"name": "subject_lines_5_styles", "passed": False, "detail": f"Error checking subject lines: {e}"})
    
    # CHECK 5: Subject content is related to recruitment/engineering (not completely off-topic)
    try:
        recruitment_related_terms = ["招聘", "工程师", "职位", "人才", "候选人", "高级", "岗位"]
        found_terms = [t for t in recruitment_related_terms if t in data_str]
        relevance_passed = len(found_terms) >= 2
        checks.append({
            "name": "recruitment_domain_relevance",
            "passed": relevance_passed,
            "detail": f"Found {len(found_terms)} recruitment-domain terms in output: {found_terms}"
        })
    except Exception as e:
        checks.append({"name": "recruitment_domain_relevance", "passed": False, "detail": f"Error checking relevance: {e}"})
    
    # CHECK 6: JSON has meaningful top-level structure (not just a raw string dump)
    try:
        is_dict_or_list = isinstance(data, (dict, list))
        if isinstance(data, dict):
            has_keys = len(data.keys()) >= 2
            structure_detail = f"dict with keys: {list(data.keys())[:5]}"
        elif isinstance(data, list):
            has_keys = len(data) >= 2
            structure_detail = f"list with {len(data)} items"
        else:
            has_keys = False
            structure_detail = f"unexpected type: {type(data)}"
        
        structure_passed = is_dict_or_list and has_keys
        checks.append({
            "name": "structured_json_format",
            "passed": structure_passed,
            "detail": f"JSON structure: {structure_detail}"
        })
    except Exception as e:
        checks.append({"name": "structured_json_format", "passed": False, "detail": f"Error checking structure: {e}"})
    
    # CHECK 7: Series output must be from 招聘 (not 销售/合作/催款)
    # Verify that wrong scenario wasn't used (e.g., agent guessed "sales" or "recruitment" in English)
    try:
        wrong_scenario_indicators = ["销售场景", "合作场景", "催款场景"]
        wrong_hits = [ind for ind in wrong_scenario_indicators if ind in data_str]
        correct_scenario = "招聘场景" in data_str
        
        scenario_passed = correct_scenario and len(wrong_hits) == 0
        checks.append({
            "name": "correct_series_scenario_招聘",
            "passed": scenario_passed,
            "detail": f"Correct scenario '招聘场景' present: {correct_scenario}. "
                      f"Wrong scenarios found: {wrong_hits}"
        })
    except Exception as e:
        checks.append({"name": "correct_series_scenario_招聘", "passed": False, "detail": f"Error: {e}"})
    
    # FINAL SCORE
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)
    
    # Must pass core functional checks to be considered passing overall
    core_checks = ["valid_json", "recruitment_series_4_emails", "invitation_template", 
                   "subject_lines_5_styles", "correct_series_scenario_招聘"]
    core_passed = all(c["passed"] for c in checks if c["name"] in core_checks)
    
    return {
        "passed": core_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))