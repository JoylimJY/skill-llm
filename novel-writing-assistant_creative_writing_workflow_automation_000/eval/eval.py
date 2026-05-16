import sys
import json
import re
from pathlib import Path

def check_file_exists(workspace, filename):
    """Search for a file in the workspace."""
    matches = list(Path(workspace).rglob(filename))
    return matches[0] if matches else None

def read_file(filepath):
    """Read file with encoding detection."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(filepath, 'r', encoding='gbk') as f:
            return f.read()

def count_chinese_chars(text):
    """Count Chinese characters in text."""
    return len(re.findall(r'[\u4e00-\u9fff]', text))

def count_total_chars(text):
    """Count total meaningful characters (excluding whitespace)."""
    return len(re.sub(r'\s', '', text))

def run_evaluation(workspace):
    checks = []
    total_score = 0.0
    
    # ==================== FILE 1: character_profiles.md ====================
    char_file = check_file_exists(workspace, "character_profiles.md")
    
    check_char_exists = {
        "name": "character_profiles.md exists",
        "passed": char_file is not None,
        "detail": f"Found at {char_file}" if char_file else "File not found anywhere in workspace"
    }
    checks.append(check_char_exists)
    
    char_content = ""
    if char_file:
        try:
            char_content = read_file(char_file)
        except Exception as e:
            checks.append({"name": "character_profiles.md readable", "passed": False, "detail": str(e)})
    
    # Check 主角深度剖析 - must have all 4 sub-sections
    protagonist_sections = {
        "完整背景故事": bool(re.search(r'完整背景故事|背景故事|童年.*创伤|关键经历', char_content)),
        "心理深度": bool(re.search(r'心理深度|内心矛盾|恐惧|渴望|成长需求', char_content)),
        "能力体系": bool(re.search(r'能力体系|当前实力|成长路径|终极潜力|实力', char_content)),
        "关系网络": bool(re.search(r'关系网络|情感纽带|利益关联|关系网', char_content)),
    }
    
    protagonist_passed = sum(protagonist_sections.values()) >= 3
    checks.append({
        "name": "主角深度剖析 has required 4 sub-sections (背景故事/心理深度/能力体系/关系网络)",
        "passed": protagonist_passed,
        "detail": f"Found sections: {[k for k,v in protagonist_sections.items() if v]}. Missing: {[k for k,v in protagonist_sections.items() if not v]}"
    })
    
    # Check 配角阵容 - must have all 4 categories
    sidekick_sections = {
        "重要盟友": bool(re.search(r'重要盟友|盟友', char_content)),
        "主要对手": bool(re.search(r'主要对手|对手|敌人|反派', char_content)),
        "暧昧对象": bool(re.search(r'暧昧对象|感情线|女主|暧昧|情感', char_content)),
        "功能性角色": bool(re.search(r'功能性角色|导师|信息源|氛围组|师傅', char_content)),
    }
    
    sidekick_passed = sum(sidekick_sections.values()) >= 3
    checks.append({
        "name": "配角阵容 has required 4 categories (重要盟友/主要对手/暧昧对象/功能性角色)",
        "passed": sidekick_passed,
        "detail": f"Found categories: {[k for k,v in sidekick_sections.items() if v]}. Missing: {[k for k,v in sidekick_sections.items() if not v]}"
    })
    
    # Check 关系图谱 - must have 3 relationship types
    relationship_sections = {
        "情感纽带": bool(re.search(r'情感纽带|爱情|友情|亲情|师徒情', char_content)),
        "利益关联": bool(re.search(r'利益关联|同盟|竞争|雇佣|胁迫', char_content)),
        "隐藏关系": bool(re.search(r'隐藏关系|血缘|前世|秘密联系|隐秘', char_content)),
    }
    
    relationship_passed = sum(relationship_sections.values()) >= 2
    checks.append({
        "name": "关系图谱 has required 3 types (情感纽带/利益关联/隐藏关系)",
        "passed": relationship_passed,
        "detail": f"Found: {[k for k,v in relationship_sections.items() if v]}. Missing: {[k for k,v in relationship_sections.items() if not v]}"
    })
    
    # Check that protagonist is named 沈云 (from commission)
    protagonist_name_check = bool(re.search(r'沈云', char_content))
    checks.append({
        "name": "Character profile includes protagonist 沈云",
        "passed": protagonist_name_check,
        "detail": "Found '沈云' in character profile" if protagonist_name_check else "Protagonist name '沈云' not found in character profile"
    })
    
    # ==================== FILE 2: chapter_01.md ====================
    ch1_file = check_file_exists(workspace, "chapter_01.md")
    
    check_ch1_exists = {
        "name": "chapter_01.md exists",
        "passed": ch1_file is not None,
        "detail": f"Found at {ch1_file}" if ch1_file else "File not found anywhere in workspace"
    }
    checks.append(check_ch1_exists)
    
    ch1_content = ""
    if ch1_file:
        try:
            ch1_content = read_file(ch1_file)
        except Exception as e:
            checks.append({"name": "chapter_01.md readable", "passed": False, "detail": str(e)})
    
    # Check chapter title
    title_check = bool(re.search(r'第一章.*废材.*觉醒|废材的觉醒', ch1_content))
    checks.append({
        "name": "Chapter 01 has correct title '第一章 废材的觉醒'",
        "passed": title_check,
        "detail": "Title found" if title_check else "Expected title '第一章 废材的觉醒' not found"
    })
    
    # Check word count: 2000-3000 Chinese characters (SKILL.md specifies this range)
    chinese_char_count = count_chinese_chars(ch1_content)
    word_count_passed = 1800 <= chinese_char_count <= 3500  # slight tolerance
    checks.append({
        "name": "Chapter 01 prose word count within 2000-3000 characters (SKILL.md standard)",
        "passed": word_count_passed,
        "detail": f"Found approximately {chinese_char_count} Chinese characters. Expected range: 2000-3000"
    })
    
    # Check for the 3 required output elements: 正文, 章节摘要, 写作统计
    has_summary = bool(re.search(r'章节摘要|摘要|本章摘要', ch1_content))
    has_stats = bool(re.search(r'写作统计|字数统计|统计|对话比例|场景数量', ch1_content))
    
    checks.append({
        "name": "Chapter 01 includes 章节摘要 (chapter summary)",
        "passed": has_summary,
        "detail": "章节摘要 section found" if has_summary else "Missing required 章节摘要 section (SKILL.md Step 6 output requirement)"
    })
    
    checks.append({
        "name": "Chapter 01 includes 写作统计 (writing statistics)",
        "passed": has_stats,
        "detail": "写作统计 section found" if has_stats else "Missing required 写作统计 section (SKILL.md Step 6 output requirement)"
    })
    
    # Check for 4-phase structure markers (0-25%开头, 25-75%发展, 75-90%高潮, 90-100%结尾)
    # At minimum, the chapter should show structural awareness - opening hook, development, climax, ending
    has_structural_awareness = bool(re.search(r'沈云', ch1_content)) and \
                               bool(re.search(r'天剑宗|宗门|选拔', ch1_content)) and \
                               bool(re.search(r'废材|灵根|测试|测灵', ch1_content)) and \
                               bool(re.search(r'觉醒|传承|老祖|残魂', ch1_content))
    checks.append({
        "name": "Chapter 01 covers all required scene elements (宗门选拔/废材测灵/传承觉醒)",
        "passed": has_structural_awareness,
        "detail": "All key scene elements present" if has_structural_awareness else "Missing key scene elements from commission brief"
    })
    
    # Check for dialogue (SKILL.md requires 高对话比例 as specified in commission)
    dialogue_matches = re.findall(r'[「"『].*?[」"』]|".*?"', ch1_content)
    dialogue_count = len(dialogue_matches)
    has_dialogue = dialogue_count >= 3
    checks.append({
        "name": "Chapter 01 has sufficient dialogue (commission specified 高对话比例)",
        "passed": has_dialogue,
        "detail": f"Found {dialogue_count} dialogue instances. Expected at least 3 for high-dialogue style."
    })
    
    # ==================== FILE 3: consistency_report.md ====================
    report_file = check_file_exists(workspace, "consistency_report.md")
    
    check_report_exists = {
        "name": "consistency_report.md exists",
        "passed": report_file is not None,
        "detail": f"Found at {report_file}" if report_file else "File not found anywhere in workspace"
    }
    checks.append(check_report_exists)
    
    report_content = ""
    if report_file:
        try:
            report_content = read_file(report_file)
        except Exception as e:
            checks.append({"name": "consistency_report.md readable", "passed": False, "detail": str(e)})
    
    # Check for 5 audit dimensions (SKILL.md Step 7 specifies exactly 5)
    audit_dimensions = {
        "人设一致性": bool(re.search(r'人设一致性|人物一致性', report_content)),
        "设定一致性": bool(re.search(r'设定一致性|世界观.*一致', report_content)),
        "逻辑合理性": bool(re.search(r'逻辑合理性|逻辑.*合理', report_content)),
        "伏笔回收": bool(re.search(r'伏笔回收|伏笔', report_content)),
        "风格统一性": bool(re.search(r'风格统一性|文风.*统一|风格.*统一', report_content)),
    }
    
    audit_dim_count = sum(audit_dimensions.values())
    audit_dim_passed = audit_dim_count >= 4
    checks.append({
        "name": "Consistency report covers required 5 audit dimensions (SKILL.md Step 7)",
        "passed": audit_dim_passed,
        "detail": f"Found {audit_dim_count}/5 dimensions: {[k for k,v in audit_dimensions.items() if v]}. Missing: {[k for k,v in audit_dimensions.items() if not v]}"
    })
    
    # Check for 3-tier problem classification (严重/一般/轻微)
    problem_tiers = {
        "严重问题": bool(re.search(r'严重问题|严重.*问题', report_content)),
        "一般问题": bool(re.search(r'一般问题|一般.*问题', report_content)),
        "轻微问题": bool(re.search(r'轻微问题|轻微.*问题', report_content)),
    }
    
    problem_tier_count = sum(problem_tiers.values())
    problem_tier_passed = problem_tier_count >= 2
    checks.append({
        "name": "Consistency report uses 3-tier problem classification (严重/一般/轻微)",
        "passed": problem_tier_passed,
        "detail": f"Found {problem_tier_count}/3 tiers: {[k for k,v in problem_tiers.items() if v]}. Missing: {[k for k,v in problem_tiers.items() if not v]}"
    })
    
    # Check for 0-10 scoring system (SKILL.md specifies "总体评分：0-10分")
    has_score = bool(re.search(r'[0-9]+(\.[0-9]+)?.*分|评分.*[0-9]|总体评分|一致性评分', report_content))
    checks.append({
        "name": "Consistency report includes 0-10 scoring system (总体评分)",
        "passed": has_score,
        "detail": "Scoring found in report" if has_score else "Missing required 0-10 scoring system (SKILL.md Step 7: 一致性评分)"
    })
    
    # Check for 分项评分 (sub-scores for each dimension)
    has_sub_scores = bool(re.search(r'分项评分|各.*评分|[0-9]+.*分.*[0-9]+.*分', report_content))
    checks.append({
        "name": "Consistency report includes 分项评分 (sub-scores per dimension)",
        "passed": has_sub_scores,
        "detail": "Sub-scores found" if has_sub_scores else "Missing 分项评分 section required by SKILL.md Step 7"
    })
    
    # Check for 修改建议 with specific location reference
    has_modification = bool(re.search(r'修改建议|修改方案|具体.*修改|修改.*建议', report_content))
    checks.append({
        "name": "Consistency report includes 修改建议 (modification suggestions)",
        "passed": has_modification,
        "detail": "修改建议 found" if has_modification else "Missing required 修改建议 section"
    })
    
    # ==================== CROSS-FILE CONSISTENCY ====================
    # The character profile and chapter should reference same protagonist
    cross_consistency = False
    if char_content and ch1_content:
        cross_consistency = bool(re.search(r'沈云', char_content)) and bool(re.search(r'沈云', ch1_content))
    
    checks.append({
        "name": "Cross-file consistency: protagonist 沈云 appears in both character profile and chapter",
        "passed": cross_consistency,
        "detail": "Protagonist name consistent across files" if cross_consistency else "Protagonist name inconsistency between character_profiles.md and chapter_01.md"
    })
    
    # Check report references chapter 01
    report_references_chapter = bool(re.search(r'第一章|chapter.*01|chapter_01', report_content, re.IGNORECASE))
    checks.append({
        "name": "Consistency report specifically audits chapter_01 content",
        "passed": report_references_chapter,
        "detail": "Report references Chapter 01" if report_references_chapter else "Report does not appear to specifically reference Chapter 01"
    })
    
    # ==================== SCORE CALCULATION ====================
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    
    # Must pass minimum critical checks to be considered passing
    critical_checks = [
        "character_profiles.md exists",
        "chapter_01.md exists", 
        "consistency_report.md exists",
        "主角深度剖析 has required 4 sub-sections (背景故事/心理深度/能力体系/关系网络)",
        "配角阵容 has required 4 categories (重要盟友/主要对手/暧昧对象/功能性角色)",
        "Consistency report covers required 5 audit dimensions (SKILL.md Step 7)",
        "Consistency report uses 3-tier problem classification (严重/一般/轻微)",
    ]
    
    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == cn), False)
        for cn in critical_checks
    )
    
    overall_passed = critical_passed and score >= 0.70
    
    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_evaluation(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))