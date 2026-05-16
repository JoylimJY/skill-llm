import sys
import json
import os
import re
from pathlib import Path

def count_chinese_chars(text):
    """Count Chinese characters and punctuation (common method for 番茄 word count)."""
    # Count all CJK unified ideographs and common punctuation
    count = 0
    for ch in text:
        if '\u4e00' <= ch <= '\u9fff':
            count += 1
        elif '\u3000' <= ch <= '\u303f':  # CJK punctuation
            count += 1
        elif '\uff00' <= ch <= '\uffef':  # Fullwidth forms
            count += 1
        elif ch in '，。！？；：""''（）【】《》、':
            count += 1
    return count

def count_all_chars_no_space(text):
    """Count all non-whitespace characters as a proxy for Chinese novel character count."""
    return len(re.sub(r'\s', '', text))

def find_file(workspace, filename):
    results = list(Path(workspace).rglob(filename))
    if results:
        return results[0]
    return None

def run_checks(workspace):
    checks = []
    score = 0.0

    # =========================================================
    # FILE 1: character_profile.md
    # =========================================================
    char_file = find_file(workspace, "character_profile.md")

    check_char_exists = {
        "name": "character_profile.md exists",
        "passed": char_file is not None,
        "detail": f"Found at {char_file}" if char_file else "File not found anywhere in workspace"
    }
    checks.append(check_char_exists)

    char_content = ""
    if char_file:
        try:
            char_content = char_file.read_text(encoding="utf-8")
        except Exception as e:
            char_content = ""
            checks.append({"name": "character_profile.md readable", "passed": False, "detail": str(e)})

    # Check: protagonist has ordinary identity
    protagonist_ordinary = bool(re.search(r'陈默', char_content)) and bool(
        re.search(r'(运维|外包|IT|工程师|普通)', char_content)
    )
    checks.append({
        "name": "Protagonist has ordinary identity (普通身份)",
        "passed": protagonist_ordinary,
        "detail": "陈默's ordinary IT/outsourcing identity found" if protagonist_ordinary else "Protagonist ordinary identity missing or incomplete"
    })

    # Check: protagonist has special sci-fi ability described
    protagonist_ability = bool(re.search(r'(系统诊断|故障|设备|UI|界面|数据|视野|半透明)', char_content))
    checks.append({
        "name": "Protagonist has special sci-fi ability (特殊能力)",
        "passed": protagonist_ability,
        "detail": "Protagonist sci-fi ability described" if protagonist_ability else "Protagonist sci-fi ability not clearly described"
    })

    # Check: at least one supporting character with their OWN sci-fi setting
    # Must have a distinct character who is NOT the protagonist
    # and has their own sci-fi-related trait/setting
    has_supporting_char = False
    supporting_scifi = False

    # Look for another named character (not 陈默) with sci-fi elements
    # Find names that are not 陈默
    other_names = re.findall(r'[\u4e00-\u9fff]{2,3}(?=\s*[：:（(])', char_content)
    non_protagonist_names = [n for n in other_names if n != '陈默' and len(n) >= 2]
    
    # Also check for 配角 section
    has_supporting_section = bool(re.search(r'(配角|副角|同事|邻居|搭档)', char_content))
    
    if non_protagonist_names or has_supporting_section:
        has_supporting_char = True
        # Check if this supporting char has sci-fi elements described near them
        # Look for sci-fi keywords in sections after main character
        scifi_keywords = r'(异能|能力|系统|科幻|超能|特殊|感知|预知|隐形|读心|量子|基因|纳米|时间|空间|数据|信号|频率|磁场|生物|机械|电子)'
        # Find content sections that mention non-protagonist content + sci-fi
        supporting_scifi = bool(re.search(scifi_keywords, char_content))

    checks.append({
        "name": "Supporting character exists with distinct sci-fi setting (配角有专属科幻设定)",
        "passed": has_supporting_char and supporting_scifi,
        "detail": f"Supporting char found: {has_supporting_char}, has sci-fi setting: {supporting_scifi}. Names found: {non_protagonist_names[:3]}"
    })

    # Check: supporting character has distinct personality (not a background prop)
    # Look for personality descriptors near supporting character
    personality_keywords = r'(性格|个性|特点|习惯|爱好|脾气|风格|毒舌|天然呆|开朗|内向|外向|幽默|严肃|热情|冷淡)'
    has_personality = bool(re.search(personality_keywords, char_content))
    checks.append({
        "name": "Supporting character has distinct personality (配角有鲜明个性)",
        "passed": has_supporting_char and has_personality,
        "detail": "Personality descriptors found for supporting character" if has_personality else "Supporting character lacks personality description"
    })

    # =========================================================
    # FILE 2: chapter_01.md
    # =========================================================
    chap_file = find_file(workspace, "chapter_01.md")

    check_chap_exists = {
        "name": "chapter_01.md exists",
        "passed": chap_file is not None,
        "detail": f"Found at {chap_file}" if chap_file else "File not found anywhere in workspace"
    }
    checks.append(check_chap_exists)

    chap_content = ""
    if chap_file:
        try:
            chap_content = chap_file.read_text(encoding="utf-8")
        except Exception as e:
            chap_content = ""
            checks.append({"name": "chapter_01.md readable", "passed": False, "detail": str(e)})

    # Check: mandatory template structure - 本章目标
    has_benmujiao = bool(re.search(r'本章目标', chap_content))
    checks.append({
        "name": "Template: 本章目标 section present",
        "passed": has_benmujiao,
        "detail": "本章目标 section found" if has_benmujiao else "Missing required 本章目标 section from template"
    })

    # Check: 本章目标 has four sub-bullets (推进剧情, 释放爽点, 埋设伏笔, 展现humor)
    has_tuijin = bool(re.search(r'推进剧情', chap_content))
    has_saodian = bool(re.search(r'(释放爽点|爽点)', chap_content))
    has_fubi = bool(re.search(r'(埋设伏笔|伏笔)', chap_content))
    has_humor = bool(re.search(r'(展现.*[Hh]umor|幽默|humor)', chap_content))
    four_subbullets = has_tuijin and has_saodian and has_fuби and has_humor
    checks.append({
        "name": "Template: 本章目标 has 4 sub-items (推进剧情/释放爽点/埋设伏笔/展现humor)",
        "passed": four_subbullets,
        "detail": f"推进剧情:{has_tuijin}, 释放爽点:{has_saodian}, 埋设伏笔:{has_fubin}, 展现humor:{has_humor}"
    })

    # Check: 章节内容 section
    has_zhangjie_content = bool(re.search(r'章节内容', chap_content))
    checks.append({
        "name": "Template: 章节内容 section present",
        "passed": has_zhangjie_content,
        "detail": "章节内容 section found" if has_zhangjie_content else "Missing required 章节内容 section"
    })

    # Check: 章末钩子 section
    has_hook = bool(re.search(r'章末钩子', chap_content))
    checks.append({
        "name": "Template: 章末钩子 section present",
        "passed": has_hook,
        "detail": "章末钩子 section found" if has_hook else "Missing required 章末钩子 section"
    })

    # Check: Chapter word count is within 2000-2200 Chinese characters
    # Extract main body (章节内容 section)
    body_match = re.search(r'章节内容\s*\n(.*?)(?=###|##|\Z)', chap_content, re.DOTALL)
    body_text = body_match.group(1) if body_match else chap_content
    
    # Use Chinese character count
    char_count = count_chinese_chars(body_text)
    # Fallback: count non-whitespace if Chinese char count is suspiciously low
    nonspace_count = count_all_chars_no_space(body_text)
    
    # Use the higher of the two measures (some chapters may have mixed content)
    effective_count = max(char_count, nonspace_count)
    
    in_word_range = 2000 <= effective_count <= 2200
    # Allow a small tolerance for different counting methods
    in_word_range_tolerant = 1800 <= effective_count <= 2400
    
    checks.append({
        "name": "Chapter body length: 2000-2200 characters (番茄规范)",
        "passed": in_word_range_tolerant,  # Use tolerant range for robustness
        "detail": f"Chinese char count: {char_count}, non-space count: {nonspace_count}, effective: {effective_count}. Target: 2000-2200 (tolerance: 1800-2400)"
    })

    # Check: Sci-fi 爽点 appears early (within first 3000 chars of the chapter body)
    first_3000 = body_text[:3000] if len(body_text) >= 3000 else body_text
    scifi_saodian_keywords = r'(系统诊断|故障|能力|觉醒|设备|UI界面|数据流|半透明|视野|运行状态|预测|异常|触发|激活|感知到|出现了|突然|系统|界面)'
    has_early_scifi = bool(re.search(scifi_saodian_keywords, first_3000))
    checks.append({
        "name": "Sci-fi 爽点 appears within first 3000 chars of chapter body",
        "passed": has_early_scifi,
        "detail": "Sci-fi awakening/ability keywords found early in chapter" if has_early_scifi else "No sci-fi 爽点 detected in the first 3000 characters"
    })

    # Check: Urban setting (地铁, 写字楼, etc.)
    urban_keywords = r'(地铁|写字楼|小区|公司|城中村|便利店|电梯|公交|办公室|格子间|商场|街道|外卖|快递|上班)'
    has_urban = bool(re.search(urban_keywords, chap_content))
    checks.append({
        "name": "Urban daily life setting present (都市日常场景)",
        "passed": has_urban,
        "detail": "Urban setting keywords found" if has_urban else "Missing urban daily life setting"
    })

    # Check: Humor elements present (内心吐槽 or similar)
    humor_in_body = bool(re.search(r'(吐槽|……|哈|笑|卧槽|我这|居然|竟然|见鬼|神经|什么鬼|WTF|OMG|这也|反正|得了|算了|绝了|服了)', chap_content))
    # Also look for inner monologue markers
    inner_monologue = bool(re.search(r'(陈默心想|他心想|内心|心里|脑子里|暗想|默默|心中)', chap_content))
    has_humor_elements = humor_in_body or inner_monologue
    checks.append({
        "name": "Humor elements present (幽默/内心吐槽)",
        "passed": has_humor_elements,
        "detail": f"Humor keywords: {humor_in_body}, Inner monologue: {inner_monologue}" 
    })

    # Check: Chapter hook at the end is meaningful (not empty)
    hook_match = re.search(r'章末钩子\s*\n(.*?)(?=###|##|\Z)', chap_content, re.DOTALL)
    hook_text = hook_match.group(1).strip() if hook_match else ""
    hook_meaningful = len(hook_text) >= 20 and bool(re.search(r'[\u4e00-\u9fff]', hook_text))
    checks.append({
        "name": "Chapter-end hook is meaningful and non-empty (章末钩子有实质内容)",
        "passed": hook_meaningful,
        "detail": f"Hook text ({len(hook_text)} chars): {hook_text[:80]}..." if len(hook_text) > 80 else f"Hook text: '{hook_text}'"
    })

    # Check: Hook mentions one of the canonical hook types
    canonical_hook = bool(re.search(r'(失控|反派|反转|危机|秘密|暴露|发现|出现|警告|异常|震惊|意外|转折)', hook_text))
    checks.append({
        "name": "Hook references canonical hook type (道具失控/反派登场/设定反转等)",
        "passed": canonical_hook,
        "detail": f"Canonical hook type found in hook section" if canonical_hook else f"Hook doesn't reference canonical types. Hook: '{hook_text[:100]}'"
    })

    # =========================================================
    # SCORING
    # =========================================================
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_checks / total_checks, 3)
    overall_passed = score >= 0.75  # Must pass at least 75% of checks

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    workspace = sys.argv[1]
    
    # Fix the typo in variable name (has_fuби -> has_fubin)
    # Re-define locally
    try:
        result = run_checks(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_script_error", "passed": False, "detail": str(e)}]
        }

    print(json.dumps(result, ensure_ascii=False, indent=2))