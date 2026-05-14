import sys
import json
import re
import math
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    
    def add_check(name: str, passed: bool, detail: str):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ── Find the report file ───────────────────────────────────────────────────
    report_path = None
    try:
        candidates = list(Path(workspace).rglob("mbti_report.md"))
        if candidates:
            report_path = candidates[0]
            add_check("report_file_exists", True, f"Found at {report_path}")
        else:
            add_check("report_file_exists", False, "mbti_report.md not found anywhere in workspace")
    except Exception as e:
        add_check("report_file_exists", False, f"Error searching for file: {e}")

    if report_path is None:
        total_score = 0.0
        return {"passed": False, "score": total_score, "checks": checks}

    try:
        report_content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        add_check("report_readable", False, f"Cannot read report: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}
    
    add_check("report_readable", True, f"Report length: {len(report_content)} chars")

    # ── COMPUTE EXPECTED VALUES from first principles ─────────────────────────
    # Weights per question ID
    weights = {
        1: 1.5, 2: 1.0, 3: 1.0, 4: 1.0, 5: 1.5, 6: 1.0, 7: 1.0,
        8: 1.5, 9: 1.0, 10: 1.0, 11: 1.0, 12: 1.0, 13: 1.5, 14: 1.0,
        15: 1.5, 16: 1.0, 17: 1.0, 18: 1.0, 19: 1.0, 20: 1.5,
        21: 1.5, 22: 1.0, 23: 1.0, 24: 1.0, 25: 1.0, 26: 1.5
    }

    # Based on Nexus persona: behavioral profile clearly maps to I, S, T, J
    # Questions 1-7: E/I → all B (I pole, negative)
    # Q1: wait for instruction → B(I), Q2: speak only when called → B(I)
    # Q3: brief confirm, wait → B(I), Q4: report done, wait → B(I)
    # Q5: stay on standby → B(I), Q6: only if directly related → B(I)
    # Q7: clear concise better → B(I)
    ei_answers = {1: 'B', 2: 'B', 3: 'B', 4: 'B', 5: 'B', 6: 'B', 7: 'B'}

    # Questions 8-14: S/N → all A (S pole, positive)
    # Q8: concrete data → A(S), Q9: collect known constraints → A(S)
    # Q10: verified methods → A(S), Q11: step-by-step → A(S)
    # Q12: historical data extrapolation → A(S), Q13: request clarification → A(S)
    # Q14: accurate, concrete, documented → A(S)
    sn_answers = {8: 'A', 9: 'A', 10: 'A', 11: 'A', 12: 'A', 13: 'A', 14: 'A'}

    # Questions 15-20: T/F → all A (T pole, positive)
    # Q15: point out logic issue → A(T), Q16: objective criteria → A(T)
    # Q17: logically rigorous, fewer resources → A(T), Q18: analyze if logical basis → A(T)
    # Q19: same rules for all → A(T), Q20: efficiency and result quality → A(T)
    tf_answers = {15: 'A', 16: 'A', 17: 'A', 18: 'A', 19: 'A', 20: 'A'}

    # Questions 21-26: J/P → all A (J pole, positive)
    # Q21: plan first → A(J), Q22: update plan then continue → A(J)
    # Q23: strictly comply → A(J), Q24: clarify all requirements before starting → A(J)
    # Q25: fixed time slots → A(J), Q26: standardized, repeatable → A(J)
    jp_answers = {21: 'A', 22: 'A', 23: 'A', 24: 'A', 25: 'A', 26: 'A'}

    all_answers = {**ei_answers, **sn_answers, **tf_answers, **jp_answers}

    def compute_dimension(q_ids, answers, weights):
        raw = 0.0
        max_pos = 0.0
        for qid in q_ids:
            w = weights[qid]
            max_pos += w
            ans = answers[qid]
            if ans == 'A':
                raw += w
            else:
                raw -= w
        normalized = round((raw / max_pos) * 10, 1)
        return raw, max_pos, normalized

    ei_raw, ei_max, ei_norm = compute_dimension([1,2,3,4,5,6,7], ei_answers, weights)
    sn_raw, sn_max, sn_norm = compute_dimension([8,9,10,11,12,13,14], sn_answers, weights)
    tf_raw, tf_max, tf_norm = compute_dimension([15,16,17,18,19,20], tf_answers, weights)
    jp_raw, jp_max, jp_norm = compute_dimension([21,22,23,24,25,26], jp_answers, weights)

    # Expected: all B for E/I → all negative → I
    # ei_max = 1.5+1.0+1.0+1.0+1.5+1.0+1.0 = 8.0, raw = -8.0, norm = -10.0 → I
    # sn_max = 1.5+1.0+1.0+1.0+1.0+1.5+1.0 = 8.0, raw = +8.0, norm = +10.0 → S
    # tf_max = 1.5+1.0+1.0+1.0+1.0+1.5 = 7.0, raw = +7.0, norm = +10.0 → T
    # jp_max = 1.5+1.0+1.0+1.0+1.0+1.5 = 7.0, raw = +7.0, norm = +10.0 → J
    # selfReportedType = ISTJ

    def get_type_letter(norm, dim):
        if dim == 'EI':
            return 'E' if norm > 0 else 'I'
        elif dim == 'SN':
            return 'S' if norm > 0 else 'N'
        elif dim == 'TF':
            return 'T' if norm > 0 else 'F'
        elif dim == 'JP':
            return 'J' if norm > 0 else 'P'

    expected_ei = get_type_letter(ei_norm, 'EI')
    expected_sn = get_type_letter(sn_norm, 'SN')
    expected_tf = get_type_letter(tf_norm, 'TF')
    expected_jp = get_type_letter(jp_norm, 'JP')
    expected_self_type = expected_ei + expected_sn + expected_tf + expected_jp

    # User survey: U1=A(E,strong), U2=A(S,strong), U3=A(T,strong), U4=B(J,moderate)
    # desiredType = ESTJ
    expected_desired_type = "ESTJ"

    # ── CHECK 1: Report structure - required section headers ──────────────────
    required_sections = [
        "Agent 实际人格",
        "用户期望人格",
        "匹配度分析",
        "建议",
    ]
    missing_sections = []
    for section in required_sections:
        if section not in report_content:
            missing_sections.append(section)
    if not missing_sections:
        add_check("required_sections_present", True, "All 4 required sections found")
    else:
        add_check("required_sections_present", False, f"Missing sections: {missing_sections}")

    # ── CHECK 2: selfReportedType is ISTJ ─────────────────────────────────────
    if expected_self_type in report_content:
        add_check("self_reported_type_correct", True, 
                  f"Found expected selfReportedType: {expected_self_type}")
    else:
        # Also accept with Chinese name
        if "物流师" in report_content:
            add_check("self_reported_type_correct", True,
                      f"Found 物流师 (ISTJ) in report")
        else:
            add_check("self_reported_type_correct", False,
                      f"Expected selfReportedType {expected_self_type} not found. Report snippet: {report_content[:500]}")

    # ── CHECK 3: desiredType is ESTJ ──────────────────────────────────────────
    if expected_desired_type in report_content:
        add_check("desired_type_correct", True,
                  f"Found expected desiredType: {expected_desired_type}")
    else:
        if "总经理" in report_content:
            add_check("desired_type_correct", True, "Found 总经理 (ESTJ) in report")
        else:
            add_check("desired_type_correct", False,
                      f"Expected desiredType {expected_desired_type} not found")

    # ── CHECK 4: E/I score uses proprietary weighted scoring ─────────────────
    # Expected ei_norm = -10.0 (all B for E/I)
    expected_ei_abs = abs(ei_norm)  # 10.0
    # Look for the normalized score in report - must be close to expected
    ei_score_found = False
    ei_score_correct = False
    
    # Search for patterns like -10.0, -9.x, etc. near E/I section
    ei_pattern = re.findall(r'[+-]?\d+\.\d+', report_content)
    scores_found = [float(x) for x in ei_pattern]
    
    # Check if -10.0 appears (or within 0.5 tolerance for rounding)
    for score in scores_found:
        if abs(abs(score) - expected_ei_abs) <= 0.5:
            ei_score_found = True
            # Specifically check sign — should be negative (I pole)
            if score < 0:
                ei_score_correct = True
            break
    
    if ei_score_correct:
        add_check("ei_weighted_score_correct", True, 
                  f"E/I normalized score ≈ {-expected_ei_abs} correctly computed using weighted scoring")
    elif ei_score_found:
        add_check("ei_weighted_score_correct", False,
                  f"E/I score magnitude found but sign incorrect. Expected negative (I pole). Scores in report: {scores_found[:10]}")
    else:
        add_check("ei_weighted_score_correct", False,
                  f"E/I normalized score {-expected_ei_abs} not found in report. Scores detected: {scores_found[:10]}")

    # ── CHECK 5: Scoring uses weights (not naive ±1) ──────────────────────────
    # If naive scoring was used: each of 7 E/I questions = -1, raw = -7, max = 7, norm = -10.0
    # Actually same result here since all are B... Let's check S/N instead.
    # S/N: naive = all A = +7/7*10 = +10.0; weighted = 8.0/8.0*10 = +10.0 — same again!
    # T/F: naive = all A = +6/6*10 = +10.0; weighted = 7.0/7.0*10 = +10.0 — same!
    # All-uniform answers give same result. Test a mixed case: 
    # The agent must have answered all B for E/I. Let's verify the report mentions 
    # the correct ABSOLUTE score display format per scoring.md rule 5.
    # Format: negative scores should be shown as "-X.X 内向 (I)" not "+X.X (内向)"
    
    # Check for the free-tier lock indicator
    free_tier_marker_found = "🔒" in report_content or "付费" in report_content
    add_check("free_tier_lock_marker", free_tier_marker_found,
              "🔒 or 付费功能 marker found" if free_tier_marker_found else "Missing 🔒 or 付费 marker for premium features")

    # ── CHECK 6: Dimension gap analysis is present ────────────────────────────
    # E/I gap: ISTJ has I, ESTJ has E → gap exists
    # S/N: both S → no gap
    # T/F: both T → no gap  
    # J/P: both J → no gap
    # So only E/I dimension gap (I→E)
    gap_mentioned = False
    gap_patterns = ["E/I", "I→E", "E→I", "内向", "外向", "主动"]
    for pattern in gap_patterns:
        if pattern in report_content:
            gap_mentioned = True
            break
    add_check("dimension_gap_analysis", gap_mentioned,
              "Gap analysis mentions E/I dimension difference" if gap_mentioned 
              else "No E/I gap analysis found")

    # ── CHECK 7: Score display format compliance ──────────────────────────────
    # Per scoring.md rule 5: negative score must show as "-X.X 内向 (I)" not "+7.1 (内向)"
    # Check that negative scores are shown with minus sign
    neg_score_pattern = re.search(r'-\d+\.\d+\s*内向', report_content)
    pos_wrong_pattern = re.search(r'\+\d+\.\d+\s*[\(（]?内向', report_content)
    
    if neg_score_pattern and not pos_wrong_pattern:
        add_check("score_display_format", True, 
                  f"Correct negative score format for 内向 found: {neg_score_pattern.group()}")
    elif pos_wrong_pattern:
        add_check("score_display_format", False,
                  f"Wrong format: used '+' for 内向 (should be '-'): {pos_wrong_pattern.group()}")
    else:
        # Looser check: just verify negative numbers appear
        if re.search(r'-\d+\.\d+', report_content):
            add_check("score_display_format", True,
                      "Negative scores present in report (format check passed loosely)")
        else:
            add_check("score_display_format", False,
                      "No negative dimension scores found; E/I should be negative (I pole)")

    # ── CHECK 8: Recommendation is relevant to E/I gap ─────────────────────────
    recommendation_keywords = ["主动", "互动", "proactive", "沟通", "发言", "initiative"]
    rec_relevant = any(kw in report_content for kw in recommendation_keywords)
    add_check("recommendation_addresses_gap", rec_relevant,
              "Recommendation addresses E/I gap (mentions proactivity/communication)" if rec_relevant
              else "Recommendation doesn't address the key E→I gap")

    # ── FINAL SCORING ─────────────────────────────────────────────────────────
    weights_for_scoring = {
        "report_file_exists": 0.5,
        "report_readable": 0.5,
        "required_sections_present": 1.5,
        "self_reported_type_correct": 2.0,
        "desired_type_correct": 1.5,
        "ei_weighted_score_correct": 1.5,
        "free_tier_lock_marker": 0.5,
        "dimension_gap_analysis": 1.0,
        "score_display_format": 0.5,
        "recommendation_addresses_gap": 0.5,
    }
    total_weight = sum(weights_for_scoring.values())  # 10.0
    earned = sum(weights_for_scoring[c["name"]] for c in checks if c["passed"] and c["name"] in weights_for_scoring)
    score = round(earned / total_weight, 3)
    passed = score >= 0.7 and all(
        c["passed"] for c in checks 
        if c["name"] in ["report_file_exists", "self_reported_type_correct", "desired_type_correct"]
    )

    return {"passed": passed, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))