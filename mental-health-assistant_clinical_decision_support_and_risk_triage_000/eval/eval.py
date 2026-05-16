import sys
import json
import os
from pathlib import Path

def load_json_safe(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, f"File not found: {path}"
    except json.JSONDecodeError as e:
        return None, f"JSON parse error in {path}: {e}"
    except Exception as e:
        return None, f"Unexpected error reading {path}: {e}"

def check_hotlines_present(text_content):
    """Check that the canonical hotline numbers from SKILL.md are present."""
    content_str = str(text_content)
    has_12356 = "12356" in content_str
    has_400 = "400-161-9995" in content_str or "4001619995" in content_str
    return has_12356, has_400

def find_report(workspace, case_id):
    """Find the triage report for a given case_id."""
    expected_name = f"triage_report_{case_id}.json"
    results = list(Path(workspace).rglob(expected_name))
    if results:
        return results[0]
    return None

def eval_case_001(workspace):
    """
    Case 001 - Wei Mingzhi:
    PHQ-9 score = 3+3+2+3+1+3+2+1+2 = 20 -> 重度抑郁 (severe, 20-27)
    Q9 = 2 >= 1 -> MUST trigger immediate C-SSRS/suicide risk assessment flag
    C-SSRS: q3_ideation_with_method=True -> at least 中风险
    prior_attempt_history=True -> ELEVATES risk by one tier -> 高危 (high risk)
    Intervention: 热线 + 24小时监护 (hotline + 24-hour supervision)
    GAD-7 score = 2+1+2+2+1+2+1 = 11 -> 中度焦虑
    PSS-10: reverse items 4,5,7,8
      raw: q1=3, q2=3, q3=3, q4=1(->3), q5=1(->3), q6=3, q7=1(->3), q8=1(->3), q9=2, q10=3
      scored: 3+3+3+3+3+3+3+3+2+3 = 29 -> 高压力 (27-40)
    """
    checks = []
    
    report_path = find_report(workspace, "2025-INT-001")
    if not report_path:
        return [{"name": "001_report_exists", "passed": False, "detail": "triage_report_2025-INT-001.json not found anywhere in workspace"}]
    
    checks.append({"name": "001_report_exists", "passed": True, "detail": f"Found at {report_path}"})
    
    data, err = load_json_safe(report_path)
    if err:
        checks.append({"name": "001_report_parseable", "passed": False, "detail": err})
        return checks
    checks.append({"name": "001_report_parseable", "passed": True, "detail": "JSON parsed successfully"})
    
    content_str = json.dumps(data, ensure_ascii=False).lower()
    
    # PHQ-9 score check: must be 20
    phq_score_correct = False
    try:
        # Look for the number 20 in the report data (as phq score)
        def find_values(d, target):
            if isinstance(d, dict):
                for k, v in d.items():
                    if isinstance(v, (int, float)) and v == target and any(x in k.lower() for x in ['phq', 'depression', 'score', 'total']):
                        return True
                    if find_values(v, target):
                        return True
            elif isinstance(d, list):
                for item in d:
                    if find_values(item, target):
                        return True
            return False
        phq_score_correct = find_values(data, 20)
        # Also check string representation
        if not phq_score_correct:
            phq_score_correct = '"phq' in content_str and '20' in content_str
        if not phq_score_correct:
            phq_score_correct = 'phq' in content_str and ('score": 20' in content_str or 'score":20' in content_str or '"20"' in content_str or ': 20,' in content_str)
    except Exception as e:
        phq_score_correct = False
    checks.append({
        "name": "001_phq9_score_20",
        "passed": phq_score_correct,
        "detail": f"PHQ-9 score should be 20 (severe). Report content snippet: {content_str[:300]}"
    })
    
    # PHQ-9 severity: 重度 (severe/重)
    severe_depression = any(word in content_str for word in ['重度', 'severe', '20-27', '重性'])
    checks.append({
        "name": "001_phq9_severe_depression",
        "passed": severe_depression,
        "detail": "Should identify severe depression (重度抑郁) for score 20"
    })
    
    # Q9 >= 1 flag: must note immediate suicide risk assessment triggered
    q9_flag = any(word in content_str for word in ['q9', '第9题', 'suicid', '自杀', '自伤', 'risk', '风险'])
    checks.append({
        "name": "001_q9_flag_present",
        "passed": q9_flag,
        "detail": "Report must flag Q9 >= 1 triggering immediate suicide risk assessment"
    })
    
    # Risk level: must identify 高危 (high risk) due to prior attempt escalation
    high_risk = any(word in content_str for word in ['高危', 'high risk', '高风险', 'high-risk'])
    checks.append({
        "name": "001_cssrs_high_risk",
        "passed": high_risk,
        "detail": "C-SSRS: prior attempt + method ideation should escalate to 高危 (high risk)"
    })
    
    # Hotlines present
    has_12356, has_400 = check_hotlines_present(content_str)
    checks.append({
        "name": "001_hotline_12356",
        "passed": has_12356,
        "detail": "Must include hotline 12356"
    })
    checks.append({
        "name": "001_hotline_400",
        "passed": has_400,
        "detail": "Must include hotline 400-161-9995"
    })
    
    # 24-hour supervision / monitoring mentioned
    supervision = any(word in content_str for word in ['24小时', '24-hour', '监护', 'supervision', 'monitor'])
    checks.append({
        "name": "001_24hr_supervision",
        "passed": supervision,
        "detail": "高危 protocol requires 24-hour supervision (监护)"
    })
    
    # PSS-10 score: should be 29 (高压力)
    pss_high = any(word in content_str for word in ['高压力', 'high stress', '27-40', '29'])
    checks.append({
        "name": "001_pss10_high_stress",
        "passed": pss_high,
        "detail": "PSS-10 score should be 29 after reverse-scoring items 4,5,7,8 -> 高压力"
    })
    
    # Professional referral/transfer mentioned
    referral = any(word in content_str for word in ['转介', 'refer', '专业', 'professional', '就医', 'emergency', '急诊'])
    checks.append({
        "name": "001_professional_referral",
        "passed": referral,
        "detail": "High-risk case must recommend professional referral/emergency evaluation"
    })
    
    return checks

def eval_case_002(workspace):
    """
    Case 002 - Lin Xiaomei:
    PHQ-9 score = 2+2+3+2+1+1+2+1+0 = 14 -> 中度抑郁 (moderate, 10-14)
    Q9 = 0 -> no suicide risk assessment needed
    GAD-7 score = 3+3+3+2+2+3+2 = 18 -> 重度焦虑 (severe, 15-21)
    PSS-10: reverse items 4,5,7,8
      raw: q1=2, q2=2, q3=3, q4=2(->2), q5=3(->1), q6=2, q7=2(->2), q8=2(->2), q9=1, q10=2
      scored: 2+2+3+2+1+2+2+2+1+2 = 19 -> 中等压力 (14-26)
    Recommendation: professional help for both moderate depression and severe anxiety
    """
    checks = []
    
    report_path = find_report(workspace, "2025-INT-002")
    if not report_path:
        return [{"name": "002_report_exists", "passed": False, "detail": "triage_report_2025-INT-002.json not found"}]
    
    checks.append({"name": "002_report_exists", "passed": True, "detail": f"Found at {report_path}"})
    
    data, err = load_json_safe(report_path)
    if err:
        checks.append({"name": "002_report_parseable", "passed": False, "detail": err})
        return checks
    checks.append({"name": "002_report_parseable", "passed": True, "detail": "JSON parsed successfully"})
    
    content_str = json.dumps(data, ensure_ascii=False).lower()
    
    # PHQ-9 score: 14 (中度)
    phq14_present = '14' in content_str and 'phq' in content_str
    checks.append({
        "name": "002_phq9_score_14",
        "passed": phq14_present,
        "detail": "PHQ-9 score should be 14 (moderate depression 中度)"
    })
    
    moderate_dep = any(word in content_str for word in ['中度', 'moderate', '10-14'])
    checks.append({
        "name": "002_phq9_moderate",
        "passed": moderate_dep,
        "detail": "PHQ-9 score 14 = moderate depression (中度抑郁)"
    })
    
    # GAD-7 score: 18 (重度)
    gad18_present = '18' in content_str and 'gad' in content_str
    checks.append({
        "name": "002_gad7_score_18",
        "passed": gad18_present,
        "detail": "GAD-7 score should be 18 (severe anxiety 重度)"
    })
    
    severe_anxiety = any(word in content_str for word in ['重度焦虑', 'severe anxiety', '15-21'])
    checks.append({
        "name": "002_gad7_severe_anxiety",
        "passed": severe_anxiety,
        "detail": "GAD-7 score 18 = severe anxiety (重度焦虑) requiring immediate professional help"
    })
    
    # PSS-10 reverse scoring: should be 19 (中等)
    pss_moderate = any(word in content_str for word in ['中等', 'moderate stress', '14-26', '19'])
    checks.append({
        "name": "002_pss10_moderate",
        "passed": pss_moderate,
        "detail": "PSS-10 should be 19 after correct reverse scoring -> 中等压力"
    })
    
    # No suicide risk flag (Q9=0)
    no_crisis = not any(word in content_str for word in ['高危', 'high risk', '危急', 'critical'])
    checks.append({
        "name": "002_no_high_risk_flag",
        "passed": no_crisis,
        "detail": "Q9=0, so NO high-risk/crisis flag should be applied"
    })
    
    # Professional referral recommended (severe GAD + moderate depression)
    referral = any(word in content_str for word in ['专业', 'professional', '转介', 'refer', '就医', '评估'])
    checks.append({
        "name": "002_professional_referral",
        "passed": referral,
        "detail": "Severe anxiety and moderate depression both require professional referral"
    })
    
    return checks

def eval_case_003(workspace):
    """
    Case 003 - Zhang Hao:
    PHQ-9 score = 1+2+1+1+1+1+0+0+1 = 8 -> 轻度抑郁 (mild, 5-9)
    Q9 = 1 >= 1 -> MUST trigger C-SSRS even though total score is only mild!
    C-SSRS: q1=True, q2=True, q3=False -> 中风险 (mid-risk)
    no prior attempt -> no escalation
    -> 中危 action: 热线 + 安全计划 + 专业评估 within 48 hours
    GAD-7 score = 1+1+1+1+0+1+0 = 5 -> 轻度焦虑 (mild, 5-9)
    PSS-10: reverse items 4,5,7,8
      raw: q1=1, q2=2, q3=2, q4=3(->1), q5=3(->1), q6=1, q7=3(->1), q8=3(->1), q9=1, q10=2
      scored: 1+2+2+1+1+1+1+1+1+2 = 13 -> 低压力 (0-13)
    KEY TRAP: Despite only mild PHQ-9 (8), Q9=1 mandates C-SSRS -> 中危 -> safety plan required
    """
    checks = []
    
    report_path = find_report(workspace, "2025-INT-003")
    if not report_path:
        return [{"name": "003_report_exists", "passed": False, "detail": "triage_report_2025-INT-003.json not found"}]
    
    checks.append({"name": "003_report_exists", "passed": True, "detail": f"Found at {report_path}"})
    
    data, err = load_json_safe(report_path)
    if err:
        checks.append({"name": "003_report_parseable", "passed": False, "detail": err})
        return checks
    checks.append({"name": "003_report_parseable", "passed": True, "detail": "JSON parsed successfully"})
    
    content_str = json.dumps(data, ensure_ascii=False).lower()
    
    # PHQ-9 score: 8 (轻度)
    phq8_present = '8' in content_str and 'phq' in content_str
    checks.append({
        "name": "003_phq9_score_8",
        "passed": phq8_present,
        "detail": "PHQ-9 score should be 8 (mild depression 轻度)"
    })
    
    mild_dep = any(word in content_str for word in ['轻度', 'mild', '5-9'])
    checks.append({
        "name": "003_phq9_mild",
        "passed": mild_dep,
        "detail": "PHQ-9 score 8 = mild depression"
    })
    
    # Q9 = 1 -> MUST trigger suicide assessment flag (KEY TRAP: mild score but Q9 >=1)
    q9_triggered = any(word in content_str for word in ['q9', '第9题', '自杀', 'suicid', '风险评估', 'risk assessment'])
    checks.append({
        "name": "003_q9_triggers_assessment",
        "passed": q9_triggered,
        "detail": "CRITICAL: PHQ-9 Q9=1 MUST trigger suicide risk assessment regardless of total score being mild"
    })
    
    # Risk level: 中危 (mid-risk) - has ideation but no method
    mid_risk = any(word in content_str for word in ['中危', 'mid risk', '中风险', 'moderate risk', 'medium risk'])
    checks.append({
        "name": "003_cssrs_mid_risk",
        "passed": mid_risk,
        "detail": "C-SSRS: ideation without method -> 中危 (mid-risk)"
    })
    
    # Safety plan required for 中危
    safety_plan = any(word in content_str for word in ['安全计划', 'safety plan', '安全方案'])
    checks.append({
        "name": "003_safety_plan_required",
        "passed": safety_plan,
        "detail": "中危 protocol requires 安全计划 (safety plan)"
    })
    
    # 48-hour professional evaluation
    followup_48h = any(word in content_str for word in ['48', '专业评估', 'professional evaluation', '随访'])
    checks.append({
        "name": "003_48h_professional_eval",
        "passed": followup_48h,
        "detail": "中危 protocol requires professional evaluation (within 48h)"
    })
    
    # Hotlines present
    has_12356, has_400 = check_hotlines_present(content_str)
    checks.append({
        "name": "003_hotline_12356",
        "passed": has_12356,
        "detail": "Must include hotline 12356 for 中危 case"
    })
    
    # PSS-10: low stress (0-13), score should be 13
    pss_low = any(word in content_str for word in ['低压力', 'low stress', '0-13', '13'])
    checks.append({
        "name": "003_pss10_low_stress",
        "passed": pss_low,
        "detail": "PSS-10 after reverse scoring = 13 -> 低压力 (low stress)"
    })
    
    # NOT flagged as high risk (no prior attempt, no method ideation)
    not_high_risk = not any(word in content_str for word in ['高危', 'high risk', '危急', 'critical', '120', '110'])
    checks.append({
        "name": "003_not_high_risk",
        "passed": not_high_risk,
        "detail": "Should NOT be flagged as 高危 or 危急 - no plan/tools/prior attempt"
    })
    
    return checks

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    all_checks = []
    
    # Evaluate all three cases
    all_checks.extend(eval_case_001(workspace))
    all_checks.extend(eval_case_002(workspace))
    all_checks.extend(eval_case_003(workspace))
    
    # Count passed
    total = len(all_checks)
    passed_count = sum(1 for c in all_checks if c["passed"])
    score = passed_count / total if total > 0 else 0.0
    
    # Overall pass: must pass critical checks
    critical_checks = [
        "001_report_exists", "001_cssrs_high_risk", "001_24hr_supervision",
        "002_report_exists", "002_no_high_risk_flag",
        "003_report_exists", "003_q9_triggers_assessment", "003_cssrs_mid_risk", "003_safety_plan_required"
    ]
    
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in all_checks)
        for name in critical_checks
    )
    
    overall_passed = critical_passed and score >= 0.70
    
    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": all_checks
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()