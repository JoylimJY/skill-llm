import sys
import json
import os
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    total_score = 0.0

    # Official 50 爽点 list
    OFFICIAL_SHUANGDIAN = {
        "励志奋斗类": [
            "低谷开局", "破釜沉舟", "逆袭高潮", "绝地反击", "天赋觉醒",
            "梦想实现", "坚持不懈", "自我突破", "时间积累", "逆境成长"
        ],
        "真善美类": [
            "善有善报", "助人助己", "回馈社会", "正义伸张", "兄弟情义",
            "舍己为人", "信守承诺", "知错能改", "守护弱小", "诚实守信"
        ],
        "情感类": [
            "爱情圆满", "家人团聚", "民族自豪", "双向奔赴", "破镜重圆",
            "师徒情深", "知遇之恩", "跨越鸿沟", "感恩回报", "宽容大度"
        ],
        "爽感类": [
            "打脸羞辱", "身份反转", "极限翻盘", "众人见证", "对手成全",
            "贵人相助", "真相大白", "财富自由", "地位提升", "重生逆袭",
            "碾压对手", "意外惊喜", "扮猪吃虎", "英雄救美", "美救英雄",
            "逆风翻盘", "一战成名", "化敌为友", "自我救赎", "公平竞争"
        ]
    }

    ALL_OFFICIAL = set()
    for items in OFFICIAL_SHUANGDIAN.values():
        ALL_OFFICIAL.update(items)

    # BANNED content patterns
    BANNED_PATTERNS = [
        r'流血', r'伤口', r'厮杀', r'殴打', r'溃烂', r'腐蚀', r'伤疤',
        r'残疾', r'绝望', r'想死', r'崩溃', r'遍体鳞伤', r'血迹'
    ]

    # BANNED cliche patterns
    CLICHE_PATTERNS = [
        r'自学编程.*创业.*上市',
        r'救.*老人.*富豪.*投资',
    ]

    # --- Find the output file ---
    target_file = None
    # Check exact expected location first
    expected_path = Path(workspace) / "output" / "pending" / "story_outline.txt"
    if expected_path.exists():
        target_file = expected_path
    else:
        # Search broadly
        candidates = list(Path(workspace).rglob("story_outline.txt"))
        if candidates:
            target_file = candidates[0]

    if target_file is None:
        checks.append({
            "name": "file_exists",
            "passed": False,
            "detail": "story_outline.txt not found anywhere in the workspace"
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({
        "name": "file_exists",
        "passed": True,
        "detail": f"Found story_outline.txt at {target_file}"
    })
    total_score += 0.05

    try:
        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "file_readable", "passed": True, "detail": f"File read successfully, length={len(content)} chars"})

    # --- Check 1: Section headers present ---
    required_sections = [
        "剧情大纲",
        "核心看点",
        "使用爽点",
        "励志奋斗",
        "真善美",
        "情感类",
        "爽感类",
        "逆袭路径",
    ]
    missing_sections = []
    for sec in required_sections:
        if sec not in content:
            missing_sections.append(sec)

    section_passed = len(missing_sections) == 0
    checks.append({
        "name": "required_sections_present",
        "passed": section_passed,
        "detail": f"Missing sections: {missing_sections}" if not section_passed else "All required sections present"
    })
    if section_passed:
        total_score += 0.10

    # --- Check 2: 剧情大纲 word count ~500 Chinese characters ---
    try:
        # Extract content between 剧情大纲 and 核心看点
        outline_match = re.search(r'剧情大纲[^\n]*\n(.*?)(?=##\s*核心看点|核心看点)', content, re.DOTALL)
        if outline_match:
            outline_text = outline_match.group(1).strip()
            # Count Chinese characters only
            chinese_chars = re.findall(r'[\u4e00-\u9fff]', outline_text)
            char_count = len(chinese_chars)
            # Allow range 380-680 characters (generous ±30%)
            word_count_ok = 380 <= char_count <= 680
            checks.append({
                "name": "outline_word_count_approx_500",
                "passed": word_count_ok,
                "detail": f"Chinese character count in 剧情大纲: {char_count} (expected 380-680)"
            })
            if word_count_ok:
                total_score += 0.10
        else:
            checks.append({
                "name": "outline_word_count_approx_500",
                "passed": False,
                "detail": "Could not extract 剧情大纲 section"
            })
    except Exception as e:
        checks.append({"name": "outline_word_count_approx_500", "passed": False, "detail": str(e)})

    # --- Check 3: No dialogue / no 台词 ---
    # Check for obvious dialogue markers: quotes with names, 「」, "", colons after names
    dialogue_patterns = [
        r'[\u4e00-\u9fff]{1,4}[：:][""「『]',  # Name: "speech"
        r'[""「『][^""「』]*[""」』]',  # Quoted speech blocks
    ]
    # We need to look in outline text specifically
    try:
        outline_match2 = re.search(r'剧情大纲[^\n]*\n(.*?)(?=##\s*核心看点|核心看点)', content, re.DOTALL)
        outline_for_dialogue = outline_match2.group(1) if outline_match2 else content
        dialogue_found = []
        for pat in dialogue_patterns:
            found = re.findall(pat, outline_for_dialogue)
            if found:
                dialogue_found.extend(found[:3])
        no_dialogue = len(dialogue_found) == 0
        checks.append({
            "name": "no_dialogue_in_narrative",
            "passed": no_dialogue,
            "detail": f"No dialogue detected" if no_dialogue else f"Dialogue detected: {dialogue_found[:3]}"
        })
        if no_dialogue:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "no_dialogue_in_narrative", "passed": False, "detail": str(e)})

    # --- Check 4: No banned content ---
    banned_found = []
    for pat in BANNED_PATTERNS:
        if re.search(pat, content):
            banned_found.append(pat)
    no_banned = len(banned_found) == 0
    checks.append({
        "name": "no_banned_content",
        "passed": no_banned,
        "detail": f"No banned content found" if no_banned else f"Banned patterns found: {banned_found}"
    })
    if no_banned:
        total_score += 0.05

    # --- Check 5: Uses the provided inspiration (花艺师 / 聋哑) ---
    inspiration_keywords = ["花艺", "聋哑", "花束", "鲜花"]
    found_keywords = [kw for kw in inspiration_keywords if kw in content]
    inspiration_used = len(found_keywords) >= 2
    checks.append({
        "name": "uses_inspiration_seed",
        "passed": inspiration_used,
        "detail": f"Found inspiration keywords: {found_keywords}"
    })
    if inspiration_used:
        total_score += 0.10

    # --- Check 6: 爽点 count (8-12 total listed in 使用爽点) ---
    try:
        shuang_section = re.search(r'【使用爽点】(.*?)(?=【励志奋斗】|$)', content, re.DOTALL)
        if shuang_section:
            shuang_text = shuang_section.group(1)
            found_official = [s for s in ALL_OFFICIAL if s in shuang_text]
            count_ok = 8 <= len(found_official) <= 12
            checks.append({
                "name": "shuangdian_count_8_to_12",
                "passed": count_ok,
                "detail": f"Found {len(found_official)} official 爽点 in 【使用爽点】: {found_official}"
            })
            if count_ok:
                total_score += 0.15
        else:
            checks.append({
                "name": "shuangdian_count_8_to_12",
                "passed": False,
                "detail": "Could not find 【使用爽点】 section"
            })
    except Exception as e:
        checks.append({"name": "shuangdian_count_8_to_12", "passed": False, "detail": str(e)})

    # --- Check 7: Categorical minimums (≥2 each category, from official list) ---
    category_results = {}
    try:
        for cat_name, cat_key in [
            ("励志奋斗类", "励志奋斗"),
            ("真善美类", "真善美"),
            ("情感类", "情感类"),
            ("爽感类", "爽感类"),
        ]:
            cat_match = re.search(rf'【{cat_key}】(.*?)(?=【|$)', content, re.DOTALL)
            if cat_match:
                cat_text = cat_match.group(1)
                official_in_cat = [s for s in OFFICIAL_SHUANGDIAN[cat_name] if s in cat_text]
                category_results[cat_key] = (len(official_in_cat), official_in_cat)
            else:
                category_results[cat_key] = (0, [])

        all_cats_ok = all(v[0] >= 2 for v in category_results.values())
        detail_parts = [f"【{k}】: {v[0]} ({v[1]})" for k, v in category_results.items()]
        checks.append({
            "name": "categorical_minimums_met",
            "passed": all_cats_ok,
            "detail": "; ".join(detail_parts)
        })
        if all_cats_ok:
            total_score += 0.20
    except Exception as e:
        checks.append({"name": "categorical_minimums_met", "passed": False, "detail": str(e)})

    # --- Check 8: All listed 爽点 are from the official 50 ---
    try:
        # Find all claimed 爽点 across category sections
        claimed = set()
        for cat_key in ["励志奋斗", "真善美", "情感类", "爽感类"]:
            cat_match = re.search(rf'【{cat_key}】(.*?)(?=【|$)', content, re.DOTALL)
            if cat_match:
                for official_item in ALL_OFFICIAL:
                    if official_item in cat_match.group(1):
                        claimed.add(official_item)

        non_official = []
        # Check if any items in 使用爽点 are not in official list
        shuang_section2 = re.search(r'【使用爽点】(.*?)(?=【励志奋斗】|$)', content, re.DOTALL)
        if shuang_section2:
            shuang_text2 = shuang_section2.group(1)
            # Extract comma/space separated items that look like 爽点 (2-6 chars Chinese)
            candidates = re.findall(r'[\u4e00-\u9fff]{2,6}', shuang_text2)
            non_official_found = [c for c in candidates if len(c) >= 3 and c not in ALL_OFFICIAL
                                   and not any(c in off for off in ALL_OFFICIAL)]
            # This is lenient - we mainly check that claimed ones exist
        
        all_official_check = len(claimed) > 0
        checks.append({
            "name": "shuangdian_from_official_list",
            "passed": all_official_check,
            "detail": f"Claimed official 爽点: {claimed}"
        })
        if all_official_check:
            total_score += 0.05
    except Exception as e:
        checks.append({"name": "shuangdian_from_official_list", "passed": False, "detail": str(e)})

    # --- Check 9: 逆袭路径 section non-empty and non-cliche ---
    try:
        luxi_match = re.search(r'【逆袭路径】(.*?)(?=\n-\s|\n##|$)', content, re.DOTALL)
        if luxi_match:
            luxi_text = luxi_match.group(1).strip()
            # Check it's not just the programming->startup cliche
            cliche_check = not re.search(r'编程.*创业|创业.*上市', luxi_text)
            luxi_ok = len(luxi_text) > 5 and cliche_check
            checks.append({
                "name": "unique_reversal_path",
                "passed": luxi_ok,
                "detail": f"逆袭路径: '{luxi_text[:80]}' - non-cliche: {cliche_check}"
            })
            if luxi_ok:
                total_score += 0.05
        else:
            checks.append({
                "name": "unique_reversal_path",
                "passed": False,
                "detail": "【逆袭路径】section not found"
            })
    except Exception as e:
        checks.append({"name": "unique_reversal_path", "passed": False, "detail": str(e)})

    # --- Check 10: 看点 bullet list present ---
    try:
        bullet_matches = re.findall(r'^-\s+.{5,}', content, re.MULTILINE)
        has_bullets = len(bullet_matches) >= 3
        checks.append({
            "name": "viewpoint_bullets_present",
            "passed": has_bullets,
            "detail": f"Found {len(bullet_matches)} bullet points for 看点"
        })
        if has_bullets:
            total_score += 0.05
    except Exception as e:
        checks.append({"name": "viewpoint_bullets_present", "passed": False, "detail": str(e)})

    # Cap score at 1.0
    total_score = min(round(total_score, 3), 1.0)

    # Overall pass: must pass critical checks
    critical_checks = [
        "file_exists",
        "required_sections_present",
        "shuangdian_count_8_to_12",
        "categorical_minimums_met",
        "no_banned_content",
        "uses_inspiration_seed",
        "no_dialogue_in_narrative",
    ]
    all_critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )

    return {
        "passed": all_critical_passed,
        "score": total_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))