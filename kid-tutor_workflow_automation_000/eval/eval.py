import sys
import json
import os
from pathlib import Path
from datetime import datetime

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []
    
    # ── CHILD IDENTITY ────────────────────────────────────────────────────────
    # The task specifies: child name 小强 (xiaoqiang), age 8, grade 3,
    # interests 恐龙,太空, session with 4 specific questions, report for 7 days.
    child_dir = workspace / "data" / "kid-tutor" / "xiaoqiang"
    profile_path = child_dir / "profile.json"
    sessions_dir = child_dir / "sessions"

    # ── CHECK 1: Profile exists ───────────────────────────────────────────────
    check1 = {"name": "profile_exists", "passed": False, "detail": ""}
    try:
        if not profile_path.exists():
            check1["detail"] = f"profile.json not found at {profile_path}"
        else:
            check1["passed"] = True
            check1["detail"] = "profile.json exists"
    except Exception as e:
        check1["detail"] = f"Exception: {e}"
    checks.append(check1)

    # ── CHECK 2: Profile has correct fields ───────────────────────────────────
    check2 = {"name": "profile_correct_fields", "passed": False, "detail": ""}
    profile = {}
    try:
        profile = json.loads(profile_path.read_text())
        name_ok = profile.get("name", "") == "小强"
        age_ok = profile.get("age") == 8
        grade_ok = profile.get("grade") == 3
        interests = profile.get("interests", [])
        interests_ok = isinstance(interests, list) and len(interests) >= 1
        
        issues = []
        if not name_ok:
            issues.append(f"name='{profile.get('name')}' (expected '小强')")
        if not age_ok:
            issues.append(f"age={profile.get('age')} (expected 8)")
        if not grade_ok:
            issues.append(f"grade={profile.get('grade')} (expected 3)")
        if not interests_ok:
            issues.append(f"interests={interests} (expected non-empty list)")
        
        if not issues:
            check2["passed"] = True
            check2["detail"] = f"Profile fields correct: name={profile.get('name')}, age={profile.get('age')}, grade={profile.get('grade')}, interests={interests}"
        else:
            check2["detail"] = "Field errors: " + "; ".join(issues)
    except FileNotFoundError:
        check2["detail"] = "profile.json not found (depends on check 1)"
    except json.JSONDecodeError as e:
        check2["detail"] = f"Invalid JSON in profile: {e}"
    except Exception as e:
        check2["detail"] = f"Exception: {e}"
    checks.append(check2)

    # ── CHECK 3: Sessions directory exists and has at least one session file ──
    check3 = {"name": "session_file_exists", "passed": False, "detail": ""}
    session_files = []
    try:
        if not sessions_dir.exists():
            check3["detail"] = f"sessions/ directory not found at {sessions_dir}"
        else:
            session_files = list(sessions_dir.glob("*.json"))
            if not session_files:
                check3["detail"] = "sessions/ directory exists but contains no .json files"
            else:
                check3["passed"] = True
                check3["detail"] = f"Found {len(session_files)} session file(s): {[f.name for f in session_files]}"
    except Exception as e:
        check3["detail"] = f"Exception: {e}"
    checks.append(check3)

    # ── CHECK 4: Session JSON has correct structure and valid result values ────
    check4 = {"name": "session_valid_structure", "passed": False, "detail": ""}
    session_data = {}
    try:
        valid_results = {"correct", "helped", "incorrect"}
        if not session_files:
            check4["detail"] = "No session files to validate (depends on check 3)"
        else:
            # Use the most recently modified session file
            latest = max(session_files, key=lambda f: f.stat().st_mtime)
            session_data = json.loads(latest.read_text())
            
            issues = []
            if "duration_minutes" not in session_data:
                issues.append("missing 'duration_minutes'")
            if "questions" not in session_data:
                issues.append("missing 'questions'")
            else:
                questions = session_data["questions"]
                if not isinstance(questions, list) or len(questions) == 0:
                    issues.append("'questions' must be a non-empty list")
                else:
                    for i, q in enumerate(questions):
                        r = q.get("result", "__missing__")
                        if r not in valid_results:
                            issues.append(f"question[{i}].result='{r}' invalid (must be correct/helped/incorrect)")
                        if not isinstance(q.get("difficulty"), int):
                            issues.append(f"question[{i}].difficulty='{q.get('difficulty')}' must be int")
                        for key in ("subject", "topic", "question"):
                            if not q.get(key):
                                issues.append(f"question[{i}].{key} missing or empty")
            
            if not issues:
                check4["passed"] = True
                check4["detail"] = f"Session structure valid, {len(session_data.get('questions',[]))} questions logged."
            else:
                check4["detail"] = "Structure errors: " + "; ".join(issues)
    except json.JSONDecodeError as e:
        check4["detail"] = f"Invalid JSON in session file: {e}"
    except Exception as e:
        check4["detail"] = f"Exception: {e}"
    checks.append(check4)

    # ── CHECK 5: Session has >= 4 questions ───────────────────────────────────
    check5 = {"name": "session_has_four_questions", "passed": False, "detail": ""}
    try:
        questions = session_data.get("questions", [])
        if len(questions) >= 4:
            check5["passed"] = True
            check5["detail"] = f"Session contains {len(questions)} questions (≥4 required)"
        else:
            check5["detail"] = f"Session has only {len(questions)} question(s); at least 4 required"
    except Exception as e:
        check5["detail"] = f"Exception: {e}"
    checks.append(check5)

    # ── CHECK 6: Session covers both math and science subjects ────────────────
    check6 = {"name": "session_covers_math_and_science", "passed": False, "detail": ""}
    try:
        questions = session_data.get("questions", [])
        subjects = {q.get("subject", "") for q in questions}
        has_math = any("数学" in s or "math" in s.lower() for s in subjects)
        has_science = any("科学" in s or "science" in s.lower() for s in subjects)
        if has_math and has_science:
            check6["passed"] = True
            check6["detail"] = f"Session covers both math and science. Subjects found: {subjects}"
        elif has_math:
            check6["detail"] = f"Session has math but no science. Subjects: {subjects}"
        elif has_science:
            check6["detail"] = f"Session has science but no math. Subjects: {subjects}"
        else:
            check6["detail"] = f"Neither math nor science found. Subjects: {subjects}"
    except Exception as e:
        check6["detail"] = f"Exception: {e}"
    checks.append(check6)

    # ── CHECK 7: Report file exists ────────────────────────────────────────────
    check7 = {"name": "report_file_exists", "passed": False, "detail": ""}
    report_path = child_dir / "report_last_7days.json"
    try:
        if report_path.exists():
            check7["passed"] = True
            check7["detail"] = f"Report file found at {report_path}"
        else:
            # Also accept any report_last_*days.json
            alt_reports = list(child_dir.glob("report_last_*days.json"))
            if alt_reports:
                check7["passed"] = True
                check7["detail"] = f"Report file found (alt): {[f.name for f in alt_reports]}"
                report_path = alt_reports[0]
            else:
                check7["detail"] = f"No report file found in {child_dir}"
    except Exception as e:
        check7["detail"] = f"Exception: {e}"
    checks.append(check7)

    # ── CHECK 8: Report JSON is valid and references the correct child ─────────
    check8 = {"name": "report_correct_content", "passed": False, "detail": ""}
    try:
        if not report_path.exists():
            check8["detail"] = "Report file not found (depends on check 7)"
        else:
            report = json.loads(report_path.read_text())
            issues = []
            if report.get("child_name") != "小强":
                issues.append(f"child_name='{report.get('child_name')}' (expected '小强')")
            if "total_questions" not in report:
                issues.append("missing 'total_questions'")
            if "accuracy_percent" not in report:
                issues.append("missing 'accuracy_percent'")
            if "weak_topics" not in report:
                issues.append("missing 'weak_topics'")
            if "suggestions" not in report:
                issues.append("missing 'suggestions'")
            days_ok = report.get("report_days") == 7
            if not days_ok:
                issues.append(f"report_days={report.get('report_days')} (expected 7)")
            
            if not issues:
                check8["passed"] = True
                check8["detail"] = (
                    f"Report valid: child={report.get('child_name')}, "
                    f"questions={report.get('total_questions')}, "
                    f"accuracy={report.get('accuracy_percent')}%, "
                    f"weak_topics={report.get('weak_topics')}"
                )
            else:
                check8["detail"] = "Report errors: " + "; ".join(issues)
    except json.JSONDecodeError as e:
        check8["detail"] = f"Invalid JSON in report: {e}"
    except Exception as e:
        check8["detail"] = f"Exception: {e}"
    checks.append(check8)

    # ── CHECK 9: weak_topics updated in profile after session ─────────────────
    check9 = {"name": "profile_weak_topics_updated", "passed": False, "detail": ""}
    try:
        # After log-session, profile should have weak_topics field (can be empty list if all correct)
        profile_reread = json.loads(profile_path.read_text())
        if "weak_topics" in profile_reread:
            check9["passed"] = True
            check9["detail"] = f"weak_topics present in profile: {profile_reread['weak_topics']}"
        else:
            check9["detail"] = "weak_topics field missing from profile after session logging"
    except FileNotFoundError:
        check9["detail"] = "profile.json not found"
    except json.JSONDecodeError as e:
        check9["detail"] = f"Invalid JSON in profile: {e}"
    except Exception as e:
        check9["detail"] = f"Exception: {e}"
    checks.append(check9)

    # ── SCORING ───────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 3)
    overall_passed = passed_count >= 7  # Need at least 7/9 to pass

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()