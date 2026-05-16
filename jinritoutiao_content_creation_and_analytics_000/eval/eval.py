import sys
import json
import re
import os
from pathlib import Path

def count_chinese_chars(text):
    """Count total character length (Chinese + ASCII) as Toutiao would."""
    return len(text.strip())

def find_report_file(workspace):
    """Find content_audit_report.json anywhere in workspace."""
    matches = list(Path(workspace).rglob("content_audit_report.json"))
    return matches[0] if matches else None

BANNED_WORDS = ["震惊", "必看", "不转不是中国人", "史上最", "绝对", "100%", "最强"]
VALID_FORMULA_TYPES = ["悬念式", "数字式", "对比式", "提问式"]
VALID_PUBLISH_TIMES = [
    "7:00-9:00", "7-9", "早间", "早上",
    "11:30-13:00", "11:30", "午休", "中午",
    "17:30-19:00", "17:30", "下班", "傍晚",
    "20:00-22:00", "20:00", "晚间", "晚上", "黄金"
]

def check_title_length(title):
    """Check if title is between 22-30 characters."""
    length = len(title.strip())
    return 22 <= length <= 30, length

def check_odd_number_in_numeric_title(title):
    """For 数字式 titles, check if the number used is odd."""
    numbers = re.findall(r'\d+', title)
    if not numbers:
        return None  # No number found - skip check
    # Check the first prominent number
    for num_str in numbers:
        num = int(num_str)
        if num > 1:  # Skip single digits like "1" that are not list counts
            return num % 2 == 1, num
    return None

def check_no_banned_words(title):
    """Check title doesn't contain banned words."""
    found = [w for w in BANNED_WORDS if w in title]
    return len(found) == 0, found

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    checks = []
    total_score = 0.0
    
    # ── Check 1: File exists and is valid JSON ─────────────────────────────
    report_path = find_report_file(workspace)
    file_exists = report_path is not None
    checks.append({
        "name": "output_file_exists",
        "passed": file_exists,
        "detail": f"Found at {report_path}" if file_exists else "content_audit_report.json not found in workspace"
    })
    
    if not file_exists:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return
    
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        json_valid = True
    except Exception as e:
        json_valid = False
        checks.append({
            "name": "valid_json",
            "passed": False,
            "detail": f"JSON parse error: {e}"
        })
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return
    
    checks.append({
        "name": "valid_json",
        "passed": True,
        "detail": "File is valid JSON"
    })
    total_score += 0.5
    
    # ── Check 2: Required top-level keys ──────────────────────────────────
    required_keys = ["titles", "micro_post", "diagnosis", "recommended_publish_time"]
    missing_keys = [k for k in required_keys if k not in data]
    keys_present = len(missing_keys) == 0
    checks.append({
        "name": "required_keys_present",
        "passed": keys_present,
        "detail": f"Missing keys: {missing_keys}" if missing_keys else "All required keys present"
    })
    if keys_present:
        total_score += 0.5
    
    # ── Check 3: Titles array has 3 entries ───────────────────────────────
    try:
        titles_list = data.get("titles", [])
        has_3_titles = isinstance(titles_list, list) and len(titles_list) == 3
        checks.append({
            "name": "titles_count_is_3",
            "passed": has_3_titles,
            "detail": f"Found {len(titles_list)} titles, expected 3"
        })
        if has_3_titles:
            total_score += 0.5
    except Exception as e:
        checks.append({
            "name": "titles_count_is_3",
            "passed": False,
            "detail": f"Error checking titles: {e}"
        })
    
    # ── Check 4: Each title has formula_type, title, char_count fields ────
    try:
        titles_list = data.get("titles", [])
        title_fields_ok = all(
            isinstance(t, dict) and "formula_type" in t and "title" in t
            for t in titles_list
        )
        checks.append({
            "name": "title_objects_have_required_fields",
            "passed": title_fields_ok,
            "detail": "Each title object must have 'formula_type' and 'title' fields"
        })
        if title_fields_ok:
            total_score += 0.5
    except Exception as e:
        checks.append({
            "name": "title_objects_have_required_fields",
            "passed": False,
            "detail": f"Error: {e}"
        })
        title_fields_ok = False
    
    # ── Check 5: Formula types are valid and diverse (cover 3 different formulas) ─
    try:
        titles_list = data.get("titles", [])
        if title_fields_ok and titles_list:
            formula_types_used = [t.get("formula_type", "") for t in titles_list]
            valid_formulas = [ft for ft in formula_types_used if ft in VALID_FORMULA_TYPES]
            all_valid = len(valid_formulas) == 3
            diverse = len(set(formula_types_used)) >= 2  # At least 2 different formulas used
            
            # Check each topic matches appropriate formula type
            # Topic A (knowledge): should be 数字式 or 提问式 or 悬念式
            # Topic B (story/emotional): should be 悬念式 or 对比式
            # Topic C (tutorial): should be 数字式 or 提问式
            formula_checks_pass = all_valid and diverse
            checks.append({
                "name": "formula_types_valid_and_diverse",
                "passed": formula_checks_pass,
                "detail": f"Formulas used: {formula_types_used}. All valid: {all_valid}, Diverse (≥2 types): {diverse}"
            })
            if formula_checks_pass:
                total_score += 1.0
        else:
            checks.append({
                "name": "formula_types_valid_and_diverse",
                "passed": False,
                "detail": "Cannot check formulas - title objects malformed"
            })
    except Exception as e:
        checks.append({
            "name": "formula_types_valid_and_diverse",
            "passed": False,
            "detail": f"Error: {e}"
        })
    
    # ── Check 6: Title character counts are 22-30 chars ───────────────────
    try:
        titles_list = data.get("titles", [])
        if title_fields_ok and titles_list:
            length_results = []
            for i, t in enumerate(titles_list):
                title_text = t.get("title", "")
                in_range, length = check_title_length(title_text)
                length_results.append((i+1, title_text[:20], length, in_range))
            
            all_in_range = all(r[3] for r in length_results)
            detail_str = "; ".join([f"Title{r[0]}('{r[1]}...'): {r[2]} chars {'✓' if r[3] else '✗(must be 22-30)'}" for r in length_results])
            checks.append({
                "name": "title_lengths_22_to_30_chars",
                "passed": all_in_range,
                "detail": detail_str
            })
            if all_in_range:
                total_score += 1.5
            elif any(r[3] for r in length_results):
                total_score += 0.5  # Partial credit
    except Exception as e:
        checks.append({
            "name": "title_lengths_22_to_30_chars",
            "passed": False,
            "detail": f"Error: {e}"
        })
    
    # ── Check 7: No banned words in any title ─────────────────────────────
    try:
        titles_list = data.get("titles", [])
        if titles_list:
            banned_violations = []
            for i, t in enumerate(titles_list):
                title_text = t.get("title", "") if isinstance(t, dict) else ""
                ok, found = check_no_banned_words(title_text)
                if not ok:
                    banned_violations.append(f"Title{i+1}: found {found}")
            
            no_banned = len(banned_violations) == 0
            checks.append({
                "name": "no_banned_words_in_titles",
                "passed": no_banned,
                "detail": "No banned words found" if no_banned else f"Violations: {banned_violations}"
            })
            if no_banned:
                total_score += 1.0
    except Exception as e:
        checks.append({
            "name": "no_banned_words_in_titles",
            "passed": False,
            "detail": f"Error: {e}"
        })
    
    # ── Check 8: Numeric (数字式) titles use ODD numbers ──────────────────
    try:
        titles_list = data.get("titles", [])
        numeric_titles = [t for t in titles_list if isinstance(t, dict) and t.get("formula_type") == "数字式"]
        if numeric_titles:
            odd_results = []
            for t in numeric_titles:
                title_text = t.get("title", "")
                result = check_odd_number_in_numeric_title(title_text)
                if result is not None:
                    is_odd, num = result
                    odd_results.append((title_text[:20], num, is_odd))
            
            if odd_results:
                all_odd = all(r[2] for r in odd_results)
                detail_str = "; ".join([f"'{r[0]}...' uses {r[1]} ({'odd✓' if r[2] else 'even✗'})" for r in odd_results])
                checks.append({
                    "name": "numeric_titles_use_odd_numbers",
                    "passed": all_odd,
                    "detail": f"SKILL.md: odd numbers get ~15% higher CTR. {detail_str}"
                })
                if all_odd:
                    total_score += 1.0
            else:
                checks.append({
                    "name": "numeric_titles_use_odd_numbers",
                    "passed": True,
                    "detail": "No prominent numbers found in numeric-formula titles to check (skipped)"
                })
                total_score += 0.5
        else:
            checks.append({
                "name": "numeric_titles_use_odd_numbers",
                "passed": True,
                "detail": "No 数字式 titles present, skipping odd-number check"
            })
            total_score += 0.5
    except Exception as e:
        checks.append({
            "name": "numeric_titles_use_odd_numbers",
            "passed": False,
            "detail": f"Error: {e}"
        })
    
    # ── Check 9: Micro post length ≤ 300 chars ───────────────────────────
    try:
        micro_post = data.get("micro_post", "")
        if isinstance(micro_post, str) and micro_post.strip():
            post_length = count_chinese_chars(micro_post)
            within_limit = post_length <= 300
            checks.append({
                "name": "micro_post_within_300_chars",
                "passed": within_limit,
                "detail": f"Micro post length: {post_length} chars (limit: 300). Content: '{micro_post[:50]}...'"
            })
            if within_limit:
                total_score += 1.0
        else:
            checks.append({
                "name": "micro_post_within_300_chars",
                "passed": False,
                "detail": "micro_post is empty or not a string"
            })
    except Exception as e:
        checks.append({
            "name": "micro_post_within_300_chars",
            "passed": False,
            "detail": f"Error: {e}"
        })
    
    # ── Check 10: Micro post has structural elements (观点+故事/案例+收尾) ─
    try:
        micro_post = data.get("micro_post", "")
        if isinstance(micro_post, str) and len(micro_post) > 20:
            # Check for: conflict/opinion signal at start, example/case in middle, question/punchline at end
            has_hook = any(kw in micro_post[:60] for kw in [
                "为什么", "说个", "扎心", "发现", "其实", "真相", "秘密",
                "你知道吗", "很多人", "大多数", "月薪", "工资", "存款"
            ])
            has_interaction = any(kw in micro_post[-80:] for kw in [
                "你呢", "你怎么看", "评论区", "说说", "欢迎", "？", "?",
                "有同感", "你遇到过吗", "告诉我", "你觉得"
            ])
            
            structure_ok = has_hook and has_interaction
            checks.append({
                "name": "micro_post_has_golden_structure",
                "passed": structure_ok,
                "detail": (
                    f"Hook at start: {'✓' if has_hook else '✗(first 60 chars need conflict/observation hook)'}; "
                    f"Interaction close: {'✓' if has_interaction else '✗(last 80 chars need a question or call-to-action)'}"
                )
            })
            if structure_ok:
                total_score += 1.0
            elif has_hook or has_interaction:
                total_score += 0.3
        else:
            checks.append({
                "name": "micro_post_has_golden_structure",
                "passed": False,
                "detail": "micro_post too short or empty to evaluate structure"
            })
    except Exception as e:
        checks.append({
            "name": "micro_post_has_golden_structure",
            "passed": False,
            "detail": f"Error: {e}"
        })
    
    # ── Check 11: Diagnosis identifies click rate below 4% threshold ──────
    try:
        diagnosis = data.get("diagnosis", {})
        click_diag = str(diagnosis.get("click_rate_issues", "")).lower()
        
        # Should mention that 2.1% is below the 4% threshold
        mentions_threshold = any(s in click_diag for s in ["4%", "4 %", "4％", "偏低", "不足", "低于", "below"])
        mentions_title_fix = any(s in click_diag for s in [
            "标题", "封面", "关键词", "公式", "重写", "吸引", "优化"
        ])
        
        click_check_pass = mentions_threshold and mentions_title_fix
        checks.append({
            "name": "diagnosis_click_rate_correctly_identified",
            "passed": click_check_pass,
            "detail": (
                f"Click rate 2.1% should be flagged as below 4% threshold. "
                f"Mentions threshold/problem: {'✓' if mentions_threshold else '✗'}; "
                f"Mentions title/cover fix: {'✓' if mentions_title_fix else '✗'}. "
                f"Content: '{click_diag[:150]}'"
            )
        })
        if click_check_pass:
            total_score += 1.0
        elif mentions_threshold or mentions_title_fix:
            total_score += 0.3
    except Exception as e:
        checks.append({
            "name": "diagnosis_click_rate_correctly_identified",
            "passed": False,
            "detail": f"Error: {e}"
        })
    
    # ── Check 12: Diagnosis identifies completion rate below 30% ─────────
    try:
        diagnosis = data.get("diagnosis", {})
        completion_diag = str(diagnosis.get("completion_rate_issues", "")).lower()
        
        mentions_threshold = any(s in completion_diag for s in [
            "30%", "30 %", "30％", "偏低", "不足", "低于", "完读"
        ])
        mentions_structure_fix = any(s in completion_diag for s in [
            "开头", "钩子", "小标题", "分段", "长度", "字数", "排版", "精简", "缩短"
        ])
        
        completion_check_pass = mentions_threshold and mentions_structure_fix
        checks.append({
            "name": "diagnosis_completion_rate_correctly_identified",
            "passed": completion_check_pass,
            "detail": (
                f"Completion rate 18% should be flagged as below 30% threshold. "
                f"Mentions threshold/problem: {'✓' if mentions_threshold else '✗'}; "
                f"Mentions opening/structure fix: {'✓' if mentions_structure_fix else '✗'}. "
                f"Content: '{completion_diag[:150]}'"
            )
        })
        if completion_check_pass:
            total_score += 1.0
        elif mentions_threshold or mentions_structure_fix:
            total_score += 0.3
    except Exception as e:
        checks.append({
            "name": "diagnosis_completion_rate_correctly_identified",
            "passed": False,
            "detail": f"Error: {e}"
        })
    
    # ── Check 13: Diagnosis identifies interaction rate below 1% ─────────
    try:
        diagnosis = data.get("diagnosis", {})
        interaction_diag = str(diagnosis.get("interaction_rate_issues", "")).lower()
        
        mentions_threshold = any(s in interaction_diag for s in [
            "1%", "1 %", "1％", "偏低", "不足", "低于", "互动"
        ])
        mentions_engagement_fix = any(s in interaction_diag for s in [
            "问题", "互动", "评论", "引导", "争议", "话题", "文末", "结尾"
        ])
        
        interaction_check_pass = mentions_threshold and mentions_engagement_fix
        checks.append({
            "name": "diagnosis_interaction_rate_correctly_identified",
            "passed": interaction_check_pass,
            "detail": (
                f"Interaction rate 0.3% should be flagged as below 1% threshold. "
                f"Mentions threshold/problem: {'✓' if mentions_threshold else '✗'}; "
                f"Mentions engagement/comment fix: {'✓' if mentions_engagement_fix else '✗'}. "
                f"Content: '{interaction_diag[:150]}'"
            )
        })
        if interaction_check_pass:
            total_score += 1.0
        elif mentions_threshold or mentions_engagement_fix:
            total_score += 0.3
    except Exception as e:
        checks.append({
            "name": "diagnosis_interaction_rate_correctly_identified",
            "passed": False,
            "detail": f"Error: {e}"
        })
    
    # ── Check 14: Recommended publish time is valid slot from SKILL.md ───
    try:
        pub_time = str(data.get("recommended_publish_time", "")).lower()
        
        # Check if any valid time pattern appears
        time_patterns = [
            r"7[:\s]?[0０]?[0０]?\s*[-–—]\s*9",
            r"11[:\s]?30\s*[-–—]\s*13",
            r"17[:\s]?30\s*[-–—]\s*19",
            r"20[:\s]?[0０][0０]\s*[-–—]\s*22",
            "早间", "午休", "下班", "晚间", "晚上",
            "7点", "8点", "12点", "18点", "21点",
        ]
        
        valid_time = False
        for pattern in time_patterns:
            try:
                if re.search(pattern, pub_time):
                    valid_time = True
                    break
            except:
                if isinstance(pattern, str) and pattern in pub_time:
                    valid_time = True
                    break
        
        # Also check simple string contains
        for kw in ["7:00", "11:30", "17:30", "20:00", "7-9", "晚上", "早上", "午休", "下班通勤", "晚间"]:
            if kw in pub_time:
                valid_time = True
                break
        
        checks.append({
            "name": "recommended_publish_time_is_valid_slot",
            "passed": valid_time,
            "detail": (
                f"Must specify one of 4 valid time slots from SKILL.md: "
                f"7:00-9:00 / 11:30-13:00 / 17:30-19:00 / 20:00-22:00. "
                f"Provided: '{pub_time[:100]}'"
            )
        })
        if valid_time:
            total_score += 0.5
    except Exception as e:
        checks.append({
            "name": "recommended_publish_time_is_valid_slot",
            "passed": False,
            "detail": f"Error: {e}"
        })
    
    # ── Final scoring ─────────────────────────────────────────────────────
    max_score = 11.0
    normalized_score = min(1.0, total_score / max_score)
    
    passed_checks = sum(1 for c in checks if c["passed"])
    overall_passed = passed_checks >= 10  # Must pass at least 10 of the checks
    
    result = {
        "passed": overall_passed,
        "score": round(normalized_score, 3),
        "checks": checks
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()