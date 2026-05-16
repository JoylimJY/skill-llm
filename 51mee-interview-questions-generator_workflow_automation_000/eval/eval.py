import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    workspace = Path(workspace_dir)

    # === Find output files ===
    json_files = list(workspace.rglob("interview_questions.json"))
    md_files = list(workspace.rglob("interview_questions.md"))

    # --- Check 1: JSON output file exists ---
    json_exists = len(json_files) > 0
    checks.append({
        "name": "JSON output file exists (interview_questions.json)",
        "passed": json_exists,
        "detail": f"Found at: {json_files[0]}" if json_exists else "interview_questions.json not found anywhere in workspace"
    })

    # --- Check 2: Markdown output file exists ---
    md_exists = len(md_files) > 0
    checks.append({
        "name": "Markdown output file exists (interview_questions.md)",
        "passed": md_exists,
        "detail": f"Found at: {md_files[0]}" if md_exists else "interview_questions.md not found anywhere in workspace"
    })

    # If no JSON file, we can't do further checks
    if not json_exists:
        checks.append({"name": "JSON parse check", "passed": False, "detail": "Skipped - no JSON file found"})
        score = sum(1 for c in checks if c["passed"]) / len(checks)
        return {"passed": False, "score": round(score, 2), "checks": checks}

    # --- Load JSON ---
    try:
        with open(json_files[0], "r", encoding="utf-8") as f:
            data = json.load(f)
        checks.append({"name": "JSON is valid and parseable", "passed": True, "detail": "JSON parsed successfully"})
    except Exception as e:
        checks.append({"name": "JSON is valid and parseable", "passed": False, "detail": f"JSON parse error: {e}"})
        score = sum(1 for c in checks if c["passed"]) / len(checks)
        return {"passed": False, "score": round(score, 2), "checks": checks}

    # --- Check 3: Top-level required fields ---
    required_top = ["position", "candidate", "focus_areas", "questions", "estimated_time", "tips"]
    missing_top = [f for f in required_top if f not in data]
    checks.append({
        "name": "JSON has all required top-level fields",
        "passed": len(missing_top) == 0,
        "detail": f"Missing fields: {missing_top}" if missing_top else "All top-level fields present"
    })

    # --- Check 4: position and candidate are non-empty strings ---
    try:
        pos_ok = isinstance(data.get("position"), str) and len(data["position"]) > 0
        cand_ok = isinstance(data.get("candidate"), str) and len(data["candidate"]) > 0
        checks.append({
            "name": "position and candidate are non-empty strings",
            "passed": pos_ok and cand_ok,
            "detail": f"position='{data.get('position')}', candidate='{data.get('candidate')}'"
        })
    except Exception as e:
        checks.append({"name": "position and candidate are non-empty strings", "passed": False, "detail": str(e)})

    # --- Check 5: candidate name contains 李明远 or Li Mingyuan (partial match ok) ---
    try:
        candidate_val = str(data.get("candidate", ""))
        cand_correct = "李明远" in candidate_val or "Li" in candidate_val or "liming" in candidate_val.lower() or "mingyuan" in candidate_val.lower()
        checks.append({
            "name": "Candidate name references Li Mingyuan from resume",
            "passed": cand_correct,
            "detail": f"candidate field: '{candidate_val}'"
        })
    except Exception as e:
        checks.append({"name": "Candidate name references Li Mingyuan from resume", "passed": False, "detail": str(e)})

    # --- Check 6: focus_areas is a non-empty list ---
    try:
        fa = data.get("focus_areas", [])
        fa_ok = isinstance(fa, list) and len(fa) >= 1
        checks.append({
            "name": "focus_areas is a non-empty list",
            "passed": fa_ok,
            "detail": f"focus_areas: {fa}"
        })
    except Exception as e:
        checks.append({"name": "focus_areas is a non-empty list", "passed": False, "detail": str(e)})

    # --- Check 7: questions object has technical, behavioral, situational ---
    try:
        qs = data.get("questions", {})
        has_tech = "technical" in qs and isinstance(qs["technical"], list)
        has_beh = "behavioral" in qs and isinstance(qs["behavioral"], list)
        has_sit = "situational" in qs and isinstance(qs["situational"], list)
        checks.append({
            "name": "questions has technical, behavioral, situational arrays",
            "passed": has_tech and has_beh and has_sit,
            "detail": f"technical={has_tech}, behavioral={has_beh}, situational={has_sit}"
        })
    except Exception as e:
        checks.append({"name": "questions has technical, behavioral, situational arrays", "passed": False, "detail": str(e)})

    # --- Check 8: technical question count 5-8 ---
    try:
        tech_count = len(data.get("questions", {}).get("technical", []))
        tech_ok = 5 <= tech_count <= 8
        checks.append({
            "name": "Technical question count is between 5 and 8 (inclusive)",
            "passed": tech_ok,
            "detail": f"Found {tech_count} technical questions"
        })
    except Exception as e:
        checks.append({"name": "Technical question count is between 5 and 8 (inclusive)", "passed": False, "detail": str(e)})

    # --- Check 9: behavioral question count 3-5 ---
    try:
        beh_count = len(data.get("questions", {}).get("behavioral", []))
        beh_ok = 3 <= beh_count <= 5
        checks.append({
            "name": "Behavioral question count is between 3 and 5 (inclusive)",
            "passed": beh_ok,
            "detail": f"Found {beh_count} behavioral questions"
        })
    except Exception as e:
        checks.append({"name": "Behavioral question count is between 3 and 5 (inclusive)", "passed": False, "detail": str(e)})

    # --- Check 10: situational question count 2-3 ---
    try:
        sit_count = len(data.get("questions", {}).get("situational", []))
        sit_ok = 2 <= sit_count <= 3
        checks.append({
            "name": "Situational question count is between 2 and 3 (inclusive)",
            "passed": sit_ok,
            "detail": f"Found {sit_count} situational questions"
        })
    except Exception as e:
        checks.append({"name": "Situational question count is between 2 and 3 (inclusive)", "passed": False, "detail": str(e)})

    # --- Check 11: Each question has required fields ---
    valid_difficulties = {"初级", "中级", "高级"}
    all_questions_valid = True
    question_detail_issues = []

    try:
        all_q_lists = []
        for category in ["technical", "behavioral", "situational"]:
            all_q_lists.extend(data.get("questions", {}).get(category, []))

        for i, q in enumerate(all_q_lists):
            issues = []
            if not isinstance(q.get("id"), int):
                issues.append("id must be int")
            if not isinstance(q.get("question"), str) or len(q.get("question","")) < 5:
                issues.append("question too short or missing")
            if q.get("difficulty") not in valid_difficulties:
                issues.append(f"difficulty '{q.get('difficulty')}' not in {{初级,中级,高级}}")
            if not isinstance(q.get("focus"), str) or len(q.get("focus","")) < 2:
                issues.append("focus missing or too short")
            fu = q.get("follow_ups", [])
            if not isinstance(fu, list) or len(fu) < 1:
                issues.append("follow_ups must be list with >=1 item")
            scoring = q.get("scoring", {})
            if not isinstance(scoring, dict):
                issues.append("scoring must be dict")
            else:
                for key in ["5", "3", "1"]:
                    if key not in scoring or not isinstance(scoring[key], str) or len(scoring[key]) < 3:
                        issues.append(f"scoring missing key '{key}' or value too short")
            if issues:
                all_questions_valid = False
                question_detail_issues.append(f"Q{i+1}: {'; '.join(issues)}")

        checks.append({
            "name": "All questions have required fields with correct types and valid difficulty",
            "passed": all_questions_valid,
            "detail": "; ".join(question_detail_issues) if question_detail_issues else "All questions valid"
        })
    except Exception as e:
        checks.append({"name": "All questions have required fields with correct types and valid difficulty", "passed": False, "detail": str(e)})

    # --- Check 12: Scoring keys are exactly "5", "3", "1" (not 5,3,1 as integers or other formats) ---
    try:
        all_scoring_ok = True
        scoring_issues = []
        for category in ["technical", "behavioral", "situational"]:
            for q in data.get("questions", {}).get(category, []):
                scoring = q.get("scoring", {})
                if isinstance(scoring, dict):
                    keys = set(scoring.keys())
                    if not {"5", "3", "1"}.issubset(keys):
                        all_scoring_ok = False
                        scoring_issues.append(f"id={q.get('id')}: scoring keys={list(keys)}, expected '5','3','1'")
                else:
                    all_scoring_ok = False
                    scoring_issues.append(f"id={q.get('id')}: scoring is not a dict")
        checks.append({
            "name": "Scoring uses string keys '5', '3', '1' (proprietary schema format)",
            "passed": all_scoring_ok,
            "detail": "; ".join(scoring_issues) if scoring_issues else "All scoring keys correct"
        })
    except Exception as e:
        checks.append({"name": "Scoring uses string keys '5', '3', '1' (proprietary schema format)", "passed": False, "detail": str(e)})

    # --- Check 13: estimated_time contains 分钟 ---
    try:
        et = str(data.get("estimated_time", ""))
        et_ok = "分钟" in et
        checks.append({
            "name": "estimated_time contains '分钟' (minutes unit in Chinese)",
            "passed": et_ok,
            "detail": f"estimated_time: '{et}'"
        })
    except Exception as e:
        checks.append({"name": "estimated_time contains '分钟' (minutes unit in Chinese)", "passed": False, "detail": str(e)})

    # --- Check 14: tips is a non-empty list ---
    try:
        tips = data.get("tips", [])
        tips_ok = isinstance(tips, list) and len(tips) >= 1
        checks.append({
            "name": "tips is a non-empty list",
            "passed": tips_ok,
            "detail": f"tips has {len(tips)} items" if isinstance(tips, list) else f"tips type: {type(tips)}"
        })
    except Exception as e:
        checks.append({"name": "tips is a non-empty list", "passed": False, "detail": str(e)})

    # --- Check 15: technical questions have 2-3 follow_ups ---
    try:
        followup_ok = True
        followup_issues = []
        for q in data.get("questions", {}).get("technical", []):
            fu = q.get("follow_ups", [])
            if not (2 <= len(fu) <= 3):
                followup_ok = False
                followup_issues.append(f"tech id={q.get('id')}: {len(fu)} follow_ups (expected 2-3)")
        checks.append({
            "name": "Technical questions have 2-3 follow_ups each",
            "passed": followup_ok,
            "detail": "; ".join(followup_issues) if followup_issues else "All technical follow_ups count OK"
        })
    except Exception as e:
        checks.append({"name": "Technical questions have 2-3 follow_ups each", "passed": False, "detail": str(e)})

    # --- Check 16: Content relevance - blockchain/Rust/Solidity keywords in questions ---
    try:
        tech_questions_text = " ".join(
            q.get("question", "") for q in data.get("questions", {}).get("technical", [])
        ).lower()
        blockchain_keywords = ["rust", "solidity", "区块链", "evm", "zk", "defi", "合约", "token", "gas", 
                               "以太坊", "ethereum", "smart contract", "链", "矿", "共识", "web3"]
        found_kw = [kw for kw in blockchain_keywords if kw in tech_questions_text]
        relevance_ok = len(found_kw) >= 3
        checks.append({
            "name": "Technical questions are relevant to blockchain/Rust/Solidity (at least 3 domain keywords)",
            "passed": relevance_ok,
            "detail": f"Found keywords: {found_kw}"
        })
    except Exception as e:
        checks.append({"name": "Technical questions are relevant to blockchain/Rust/Solidity", "passed": False, "detail": str(e)})

    # --- Check 17: Markdown file has emoji section headers ---
    if md_exists:
        try:
            with open(md_files[0], "r", encoding="utf-8") as f:
                md_content = f.read()
            has_tech_emoji = "🔧" in md_content
            has_beh_emoji = "🗣️" in md_content or "🗣" in md_content
            has_sit_emoji = "🎭" in md_content
            has_tip_emoji = "💡" in md_content
            md_emoji_ok = has_tech_emoji and has_beh_emoji and has_sit_emoji and has_tip_emoji
            checks.append({
                "name": "Markdown has required emoji section headers (🔧, 🗣️, 🎭, 💡)",
                "passed": md_emoji_ok,
                "detail": f"🔧={has_tech_emoji}, 🗣️={has_beh_emoji}, 🎭={has_sit_emoji}, 💡={has_tip_emoji}"
            })
        except Exception as e:
            checks.append({"name": "Markdown has required emoji section headers", "passed": False, "detail": str(e)})
    else:
        checks.append({"name": "Markdown has required emoji section headers", "passed": False, "detail": "No markdown file found"})

    # --- Check 18: Markdown has star rating format ---
    if md_exists:
        try:
            with open(md_files[0], "r", encoding="utf-8") as f:
                md_content = f.read()
            has_five_star = "⭐⭐⭐⭐⭐" in md_content
            has_three_star = "⭐⭐⭐" in md_content
            has_one_star = "⭐" in md_content
            has_5score = "(5分)" in md_content
            has_3score = "(3分)" in md_content
            has_1score = "(1分)" in md_content
            star_ok = has_five_star and has_three_star and has_one_star and has_5score
            checks.append({
                "name": "Markdown uses star rating format (⭐⭐⭐⭐⭐/⭐⭐⭐/⭐ with score labels)",
                "passed": star_ok,
                "detail": f"5-star={has_five_star}, 3-star={has_three_star}, 1-star={has_one_star}, (5分)={has_5score}"
            })
        except Exception as e:
            checks.append({"name": "Markdown uses star rating format", "passed": False, "detail": str(e)})
    else:
        checks.append({"name": "Markdown uses star rating format", "passed": False, "detail": "No markdown file found"})

    # --- Check 19: Markdown title references position and candidate ---
    if md_exists:
        try:
            with open(md_files[0], "r", encoding="utf-8") as f:
                md_content = f.read()
            first_100 = md_content[:300]
            has_title = first_100.startswith("#") or "# 面试题库" in first_100
            has_candidate_ref = "李明远" in md_content or "Li" in md_content
            checks.append({
                "name": "Markdown title follows '# 面试题库 - {职位} - {候选人}' format",
                "passed": has_title and has_candidate_ref,
                "detail": f"has_title_header={has_title}, has_candidate_ref={has_candidate_ref}"
            })
        except Exception as e:
            checks.append({"name": "Markdown title format", "passed": False, "detail": str(e)})
    else:
        checks.append({"name": "Markdown title format", "passed": False, "detail": "No markdown file found"})

    # --- Final scoring ---
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)
    # Must pass at least 14/19 checks to be considered passing
    overall_passed = passed_count >= 14

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))