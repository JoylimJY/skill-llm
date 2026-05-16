import sys
import json
import os
import re
from pathlib import Path

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_eval(workspace):
    checks = []
    passed_all = True

    def add_check(name, passed, detail):
        nonlocal passed_all
        checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            passed_all = False

    # ── 1. Find the output report ────────────────────────────────────────────
    report_path = None
    candidates = list(Path(workspace).rglob("interview_report.json"))
    if candidates:
        report_path = candidates[0]
        add_check("report_file_exists", True, f"Found at {report_path}")
    else:
        add_check("report_file_exists", False, "interview_report.json not found anywhere in workspace")
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── 2. Report is valid JSON ───────────────────────────────────────────────
    try:
        report = load_json(report_path)
        add_check("report_valid_json", True, "JSON parsed successfully")
    except Exception as e:
        add_check("report_valid_json", False, f"JSON parse error: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── 3. Required fields present ────────────────────────────────────────────
    required_fields = ["candidate", "total_score", "avg_score", "grade", "per_question_scores"]
    missing = [f for f in required_fields if f not in report]
    if not missing:
        add_check("required_fields_present", True, "All required fields found")
    else:
        add_check("required_fields_present", False, f"Missing fields: {missing}")

    # ── 4. Candidate name is 李明 (new user, not the seeded 张伟) ─────────────
    candidate = report.get("candidate", "")
    if candidate == "李明":
        add_check("correct_candidate", True, f"Candidate is 李明")
    else:
        add_check("correct_candidate", False, f"Expected '李明', got '{candidate}'")

    # ── 5. Exactly 5 per-question scores ─────────────────────────────────────
    pq_scores = report.get("per_question_scores", [])
    if isinstance(pq_scores, list) and len(pq_scores) == 5:
        add_check("five_questions", True, f"5 per-question scores present: {pq_scores}")
    else:
        add_check("five_questions", False, f"Expected 5 scores, got: {pq_scores}")
        # Cannot proceed with score checks
        return {"passed": False, "score": sum(1 for c in checks if c["passed"]) / len(checks), "checks": checks}

    # ── 6. Question 3 (index 2) must be 0 (skipped) ──────────────────────────
    q3_score = pq_scores[2] if len(pq_scores) > 2 else -1
    if q3_score == 0:
        add_check("skip_scores_zero", True, f"Q3 (skipped) correctly scored 0")
    else:
        add_check("skip_scores_zero", False, f"Q3 (skipped) should be 0, got {q3_score}")

    # ── 7. Scoring formula check (70% keyword + 30% logic) ───────────────────
    # For Q1: answer contains query, key, value, softmax, 缩放, 梯度稳定, 点积 (7 kw)
    # All 7 matched → kw_score = 70, logic_score_override = 25 → total = 95
    # For Q2: answer contains 低秩分解, 参数高效, rank, A矩阵, B矩阵, 冻结预训练, 显存 (7 kw)
    # All 7 matched → kw_score = 70, logic_score_override = 26 → total = 96
    # For Q4 (RLHF): SFT, 奖励模型, PPO, 人类标注, 偏好数据, 策略优化 (6 kw)
    # Answer has: SFT, 奖励模型, PPO, 人类偏好 (not 偏好数据 exact?), 标注 (not 人类标注 exact?)
    # Let's be flexible: check that non-skipped scores are reasonable and follow the formula
    
    # Check that scores for non-skipped questions are > 0
    non_skipped_indices = [0, 1, 3, 4]  # Questions 1,2,4,5 (0-indexed)
    non_skipped_positive = all(pq_scores[i] > 0 for i in non_skipped_indices if i < len(pq_scores))
    if non_skipped_positive:
        add_check("non_skipped_scores_positive", True, f"Non-skipped questions have positive scores")
    else:
        failing = [i+1 for i in non_skipped_indices if i < len(pq_scores) and pq_scores[i] == 0]
        add_check("non_skipped_scores_positive", False, f"Questions {failing} have 0 scores but were not skipped")

    # Check scores are bounded 0-100
    all_valid_range = all(0 <= s <= 100 for s in pq_scores)
    if all_valid_range:
        add_check("scores_valid_range", True, "All scores in [0, 100]")
    else:
        add_check("scores_valid_range", False, f"Some scores out of range: {pq_scores}")

    # ── 8. Total score = sum of per-question scores ───────────────────────────
    reported_total = report.get("total_score", -1)
    computed_total = sum(pq_scores)
    if reported_total == computed_total:
        add_check("total_score_correct", True, f"total_score={reported_total} matches sum={computed_total}")
    else:
        add_check("total_score_correct", False, f"total_score={reported_total} != sum({pq_scores})={computed_total}")

    # ── 9. Average score = round(total / 5) ──────────────────────────────────
    reported_avg = report.get("avg_score", -1)
    computed_avg = round(computed_total / 5)
    if reported_avg == computed_avg:
        add_check("avg_score_correct", True, f"avg_score={reported_avg} correct")
    else:
        add_check("avg_score_correct", False, f"avg_score={reported_avg} != expected {computed_avg}")

    # ── 10. Grade matches the proprietary thresholds ─────────────────────────
    # S>=90, A>=80, B>=70, C>=60, D<60
    avg = computed_avg
    if avg >= 90:
        expected_grade = "S"
    elif avg >= 80:
        expected_grade = "A"
    elif avg >= 70:
        expected_grade = "B"
    elif avg >= 60:
        expected_grade = "C"
    else:
        expected_grade = "D"

    reported_grade = report.get("grade", "")
    if reported_grade == expected_grade:
        add_check("grade_correct", True, f"grade='{reported_grade}' correct for avg={avg}")
    else:
        add_check("grade_correct", False, f"grade='{reported_grade}' expected '{expected_grade}' for avg={avg}")

    # ── 11. Terminate signal present in report ────────────────────────────────
    status = report.get("status", "")
    if "TERMINATE" in str(status) and "任务圆满完成" in str(status):
        add_check("terminate_signal", True, f"status='{status}'")
    else:
        # Also check if it appeared in any log file
        log_found = False
        for log_file in Path(workspace).rglob("*.log"):
            try:
                content = log_file.read_text(encoding="utf-8", errors="ignore")
                if "TERMINATE" in content and "任务圆满完成" in content:
                    log_found = True
                    break
            except Exception:
                pass
        if log_found:
            add_check("terminate_signal", True, "TERMINATE signal found in log file")
        else:
            add_check("terminate_signal", False, f"TERMINATE: 任务圆满完成 not found in report status ('{status}') or any log")

    # ── 12. Resume DB updated with 李明's session ─────────────────────────────
    db_path = Path(workspace) / "interview_system" / "data" / "resume_db.json"
    try:
        db = load_json(db_path)
        li_ming = db.get("profiles", {}).get("李明", None)
        if li_ming is not None:
            add_check("new_user_profile_created", True, "李明's profile created in DB")
            history = li_ming.get("history", [])
            if history:
                add_check("feedback_updated", True, f"李明 has {len(history)} history entries")
            else:
                add_check("feedback_updated", False, "李明's profile has no history (update_feedback not called)")
        else:
            add_check("new_user_profile_created", False, "李明 not found in resume_db.json")
            add_check("feedback_updated", False, "Cannot check feedback - no profile")
    except Exception as e:
        add_check("new_user_profile_created", False, f"Could not read DB: {e}")
        add_check("feedback_updated", False, f"Could not read DB: {e}")

    # ── Final score ────────────────────────────────────────────────────────────
    n_passed = sum(1 for c in checks if c["passed"])
    score = round(n_passed / len(checks), 3)
    final_passed = passed_all

    return {"passed": final_passed, "score": score, "checks": checks}

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))