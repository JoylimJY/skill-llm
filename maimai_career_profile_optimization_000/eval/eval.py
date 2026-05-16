import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    workspace = Path(workspace_dir)

    # Find the output file
    output_files = list(workspace.rglob("career_profile_package.json"))
    
    if not output_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_exists", "passed": False, "detail": "career_profile_package.json not found anywhere in workspace"}]
        }

    output_file = output_files[0]
    checks.append({"name": "output_file_exists", "passed": True, "detail": f"Found at {output_file}"})

    # Parse JSON
    try:
        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        checks.append({"name": "json_parseable", "passed": False, "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "json_parseable", "passed": True, "detail": "JSON parsed successfully"})

    # ========================================================
    # CHECK 1: 职业标签 (Career Tags) - Must be 3-5 keywords
    # ========================================================
    try:
        # Look for tags in profile_homepage or a top-level career_tags field
        tags = None
        profile = data.get("profile_homepage", data.get("maimai_profile", data.get("personal_profile", {})))
        
        if isinstance(profile, dict):
            tags = profile.get("职业标签", profile.get("career_tags", profile.get("tags", profile.get("skills_tags", None))))
        
        if tags is None:
            # Try top level
            tags = data.get("职业标签", data.get("career_tags", data.get("tags", None)))
        
        if tags is None:
            # Search recursively for any list that could be tags
            def find_tags(obj, depth=0):
                if depth > 4:
                    return None
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if any(kw in str(k).lower() for kw in ["标签", "tag", "keyword", "技能"]):
                            if isinstance(v, list) and 2 <= len(v) <= 8:
                                return v
                    for k, v in obj.items():
                        result = find_tags(v, depth+1)
                        if result:
                            return result
                return None
            tags = find_tags(data)

        if tags is None:
            checks.append({"name": "career_tags_3_to_5", "passed": False, "detail": "Could not find 职业标签/career_tags field in output"})
        else:
            tag_count = len(tags) if isinstance(tags, list) else len(str(tags).split("/"))
            is_valid = 3 <= tag_count <= 5
            checks.append({
                "name": "career_tags_3_to_5",
                "passed": is_valid,
                "detail": f"Found {tag_count} career tags: {tags}. Must be between 3 and 5 per 脉脉 guidelines."
            })
    except Exception as e:
        checks.append({"name": "career_tags_3_to_5", "passed": False, "detail": f"Error checking career tags: {e}"})

    # ========================================================
    # CHECK 2: STAR法则 - Must have all 4 components (S, T, A, R)
    #          with quantified results in at least 2 achievements
    # ========================================================
    try:
        star_section = data.get("star_achievements", data.get("work_achievements", data.get("achievements", None)))
        if star_section is None:
            # Try nested
            profile = data.get("profile_homepage", data.get("maimai_profile", {}))
            if isinstance(profile, dict):
                star_section = profile.get("star_achievements", profile.get("work_achievements", profile.get("工作经历", None)))
        
        if star_section is None:
            checks.append({"name": "star_format_present", "passed": False, "detail": "No STAR achievements section found"})
            checks.append({"name": "star_has_all_4_components", "passed": False, "detail": "No STAR section to evaluate"})
            checks.append({"name": "star_has_quantified_results", "passed": False, "detail": "No STAR section to evaluate"})
        else:
            # Convert to string for analysis
            star_text = json.dumps(star_section, ensure_ascii=False).lower()
            
            # Check for STAR markers (S/T/A/R labels or their Chinese equivalents)
            s_markers = ["situation", "背景", "s）", "s:", "（s）", "【s】", "situation）", "挑战", "困境"]
            t_markers = ["task", "职责", "目标", "t）", "t:", "（t）", "【t】", "task）"]
            a_markers = ["action", "行动", "措施", "方法", "a）", "a:", "（a）", "【a】", "action）", "采取"]
            r_markers = ["result", "成果", "结果", "r）", "r:", "（r）", "【r】", "result）", "取得"]
            
            has_s = any(m in star_text for m in s_markers)
            has_t = any(m in star_text for m in t_markers)
            has_a = any(m in star_text for m in a_markers)
            has_r = any(m in star_text for m in r_markers)
            
            all_4 = has_s and has_t and has_a and has_r
            checks.append({
                "name": "star_has_all_4_components",
                "passed": all_4,
                "detail": f"S:{has_s}, T:{has_t}, A:{has_a}, R:{has_r}. All 4 STAR components required."
            })
            
            # Check for quantified results (numbers/percentages in results)
            number_pattern = r'\d+[\w%万亿]+'
            numbers_found = re.findall(number_pattern, star_text)
            has_quantified = len(numbers_found) >= 3  # At least 3 quantified data points across achievements
            checks.append({
                "name": "star_has_quantified_results",
                "passed": has_quantified,
                "detail": f"Found {len(numbers_found)} quantified data points: {numbers_found[:5]}. Need at least 3."
            })
            
            # Check at least 2 achievements
            achievement_count = 1
            if isinstance(star_section, list):
                achievement_count = len(star_section)
            elif isinstance(star_section, dict):
                achievement_count = len(star_section)
            
            has_multiple = achievement_count >= 2
            checks.append({
                "name": "star_has_at_least_2_achievements",
                "passed": has_multiple,
                "detail": f"Found {achievement_count} STAR achievement(s). Need at least 2."
            })
    except Exception as e:
        checks.append({"name": "star_format_present", "passed": False, "detail": f"Error evaluating STAR section: {e}"})

    # ========================================================
    # CHECK 3: 破冰话术 / Outreach Message for 内推求职
    # Must follow template: 岗位, 经验年限, 公司/项目, 量化成果, 内推请求
    # ========================================================
    try:
        outreach = data.get("outreach_message", data.get("networking_message", data.get("内推消息", data.get("outreach", None))))
        if outreach is None:
            # Search nested
            for key in data:
                val = data[key]
                if isinstance(val, dict):
                    outreach = val.get("outreach_message", val.get("内推消息", None))
                    if outreach:
                        break

        if outreach is None:
            checks.append({"name": "outreach_message_exists", "passed": False, "detail": "No outreach_message field found"})
            checks.append({"name": "outreach_mentions_position", "passed": False, "detail": "No outreach message to evaluate"})
            checks.append({"name": "outreach_mentions_experience_years", "passed": False, "detail": "No outreach message to evaluate"})
            checks.append({"name": "outreach_mentions_achievement", "passed": False, "detail": "No outreach message to evaluate"})
            checks.append({"name": "outreach_requests_referral", "passed": False, "detail": "No outreach message to evaluate"})
        else:
            outreach_text = json.dumps(outreach, ensure_ascii=False)
            checks.append({"name": "outreach_message_exists", "passed": True, "detail": f"Found outreach message (length: {len(outreach_text)})"})
            
            # Check mentions target position (字节 or 数据工程师)
            has_position = any(kw in outreach_text for kw in ["数据工程师", "字节", "岗位", "职位", "招聘"])
            checks.append({
                "name": "outreach_mentions_position",
                "passed": has_position,
                "detail": f"Outreach must mention target position. Found: {has_position}"
            })
            
            # Check mentions experience/years
            has_experience = bool(re.search(r'\d+\s*年', outreach_text))
            checks.append({
                "name": "outreach_mentions_experience_years",
                "passed": has_experience,
                "detail": f"Outreach must mention years of experience per template. Found years pattern: {has_experience}"
            })
            
            # Check mentions quantified achievement
            has_achievement = bool(re.search(r'\d+[\w%万亿]+', outreach_text))
            checks.append({
                "name": "outreach_mentions_achievement",
                "passed": has_achievement,
                "detail": f"Outreach must mention quantified achievement per template. Found: {has_achievement}"
            })
            
            # Check contains referral request (内推)
            has_referral = any(kw in outreach_text for kw in ["内推", "推荐", "帮忙", "简历"])
            checks.append({
                "name": "outreach_requests_referral",
                "passed": has_referral,
                "detail": f"Outreach must include referral request. Found: {has_referral}"
            })
    except Exception as e:
        checks.append({"name": "outreach_message_exists", "passed": False, "detail": f"Error evaluating outreach: {e}"})

    # ========================================================
    # CHECK 4: 内容发布策略 - Must specify 2-3 per week AND
    #          correct time windows (8-9am or 12-13pm)
    # ========================================================
    try:
        content_strategy = data.get("content_strategy", data.get("posting_strategy", data.get("内容策略", None)))
        if content_strategy is None:
            for key in data:
                val = data[key]
                if isinstance(val, dict):
                    content_strategy = val.get("content_strategy", val.get("posting_strategy", None))
                    if content_strategy:
                        break

        if content_strategy is None:
            checks.append({"name": "content_frequency_2_to_3_per_week", "passed": False, "detail": "No content_strategy section found"})
            checks.append({"name": "content_optimal_time_slots", "passed": False, "detail": "No content_strategy section found"})
        else:
            strategy_text = json.dumps(content_strategy, ensure_ascii=False)
            
            # Check posting frequency: 2-3 per week
            freq_pattern = r'[2两二][^\d]*[3三]|每周\s*[2-3两二三]|[2-3]\s*[篇条次].*周|周.*[2-3]\s*[篇条次]'
            has_correct_freq = bool(re.search(freq_pattern, strategy_text))
            # Also check for plain "2-3篇" or "每周2" or "每周3"
            if not has_correct_freq:
                has_correct_freq = any(kw in strategy_text for kw in ["2-3篇", "2～3", "2~3", "每周2", "每周3", "两到三", "2到3"])
            checks.append({
                "name": "content_frequency_2_to_3_per_week",
                "passed": has_correct_freq,
                "detail": f"Must specify 2-3 posts per week per 脉脉 guidelines. Found match: {has_correct_freq}. Text: {strategy_text[:200]}"
            })
            
            # Check optimal time slots: 8-9am or 12-13pm
            time_pattern = r'[8八]\s*[-~到至]\s*[9九]|[12十二]\s*[-~到至]\s*[13十三]|早[上晨]?\s*8|午[休饭]?\s*12|上午8|中午12'
            has_correct_time = bool(re.search(time_pattern, strategy_text))
            if not has_correct_time:
                has_correct_time = any(kw in strategy_text for kw in ["8点", "9点", "12点", "13点", "8-9", "12-13", "早8", "午12"])
            checks.append({
                "name": "content_optimal_time_slots",
                "passed": has_correct_time,
                "detail": f"Must specify optimal time slots (8-9am or 12-13pm). Found: {has_correct_time}. Text: {strategy_text[:200]}"
            })
    except Exception as e:
        checks.append({"name": "content_frequency_2_to_3_per_week", "passed": False, "detail": f"Error checking content strategy: {e}"})

    # ========================================================
    # CHECK 5: 薪资谈判策略 - Must mention 110-120% pricing strategy
    # ========================================================
    try:
        salary_section = data.get("salary_negotiation", data.get("薪资谈判", data.get("negotiation_strategy", None)))
        if salary_section is None:
            for key in data:
                val = data[key]
                if isinstance(val, dict):
                    salary_section = val.get("salary_negotiation", val.get("薪资谈判", None))
                    if salary_section:
                        break

        if salary_section is None:
            checks.append({"name": "salary_110_120_strategy", "passed": False, "detail": "No salary_negotiation section found"})
        else:
            salary_text = json.dumps(salary_section, ensure_ascii=False)
            
            # Check for 110-120% strategy
            pct_pattern = r'11[05][%％]|12[05][%％]|110.*120|1\.1[0-9].*倍|报价.*高[出于].*10|10%.*20%.*高'
            has_pct_strategy = bool(re.search(pct_pattern, salary_text))
            if not has_pct_strategy:
                has_pct_strategy = any(kw in salary_text for kw in [
                    "110%", "120%", "110％", "120％", "110-120",
                    "1.1倍", "1.2倍", "高10", "高20",
                    "10%到20%", "10%-20%", "10%～20%"
                ])
            checks.append({
                "name": "salary_110_120_strategy",
                "passed": has_pct_strategy,
                "detail": f"Must include 110-120% pricing strategy from 脉脉 guidelines. Found: {has_pct_strategy}. Text: {salary_text[:300]}"
            })
    except Exception as e:
        checks.append({"name": "salary_110_120_strategy", "passed": False, "detail": f"Error checking salary strategy: {e}"})

    # ========================================================
    # CHECK 6: 个人简介 - Must be a single-sentence summary
    # ========================================================
    try:
        profile = data.get("profile_homepage", data.get("maimai_profile", data.get("personal_profile", {})))
        bio = None
        if isinstance(profile, dict):
            bio = profile.get("个人简介", profile.get("bio", profile.get("summary", profile.get("introduction", None))))
        
        if bio is None:
            bio = data.get("个人简介", data.get("bio", data.get("personal_summary", None)))
        
        if bio is None:
            checks.append({"name": "personal_bio_one_sentence", "passed": False, "detail": "No 个人简介/bio field found"})
        else:
            bio_text = str(bio)
            # Check it's reasonably concise (1-2 sentences, not a paragraph)
            sentence_count = len(re.split(r'[。！？.!?]', bio_text.strip()))
            is_concise = len(bio_text) <= 120 and sentence_count <= 3
            checks.append({
                "name": "personal_bio_one_sentence",
                "passed": is_concise,
                "detail": f"个人简介 should be one concise sentence. Length: {len(bio_text)}, sentences: {sentence_count}. Content: {bio_text[:100]}"
            })
    except Exception as e:
        checks.append({"name": "personal_bio_one_sentence", "passed": False, "detail": f"Error checking bio: {e}"})

    # ========================================================
    # FINAL SCORING
    # ========================================================
    critical_checks = [
        "career_tags_3_to_5",
        "star_has_all_4_components",
        "star_has_quantified_results",
        "outreach_mentions_experience_years",
        "content_frequency_2_to_3_per_week",
        "content_optimal_time_slots",
        "salary_110_120_strategy",
    ]
    
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])
    critical_passed = sum(1 for c in checks if c["name"] in critical_checks and c["passed"])
    
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    # Must pass at least 5 of 7 critical checks to pass overall
    overall_passed = critical_passed >= 5 and score >= 0.6

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))