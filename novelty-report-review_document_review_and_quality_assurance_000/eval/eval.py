import sys
import json
import re
from pathlib import Path

def find_output_file(workspace: Path):
    """Find the review output file - agent should create review_result.md"""
    candidates = list(workspace.rglob("review_result.md"))
    if candidates:
        return candidates[0]
    # Also check for other possible names
    for name in ["审核意见.md", "审核结果.md", "novelty_review.md", "report_review.md"]:
        candidates = list(workspace.rglob(name))
        if candidates:
            return candidates[0]
    return None

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []

    # Find the output file
    output_file = find_output_file(workspace)
    if output_file is None:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_exists", "passed": False, "detail": "No review output file found. Expected review_result.md or similar."}]
        }

    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_readable", "passed": False, "detail": f"Could not read output file: {e}"}]
        }

    # =========================================================
    # CHECK 1: "只报问题" principle - output must not be a praise summary
    # The output should NOT contain extensive compliments about correct parts
    # =========================================================
    praise_patterns = [
        r"合乎规范.*无问题", r"做得.*很好", r"符合.*规范.*整体",
        r"整体.*质量.*较高", r"报告.*完整.*规范"
    ]
    has_excessive_praise = any(re.search(p, content) for p in praise_patterns)
    checks.append({
        "name": "only_report_problems_principle",
        "passed": not has_excessive_praise,
        "detail": "Output correctly follows '只报问题' principle" if not has_excessive_praise else "Output contains excessive praise of correct parts, violating '只报问题' principle"
    })

    # =========================================================
    # CHECK 2: 查新点 ambiguity issue detected
    # 查新点1 mixes: electrospinning + microsphere encapsulation + dual growth factor + 
    # surface treatment — too many technical points in one 查新点
    # =========================================================
    xindiian_ambiguity_patterns = [
        r"查新点.{0,20}(含糊|混杂|拆分|多个技术|技术点.*混|建议.*拆|过多|复杂.*单一)",
        r"(拆分|分开|独立).{0,30}查新点",
        r"查新点.{0,50}(氧等离子|等离子体|表面处理|cell adhesion)",
        r"技术点.{0,30}(过多|混合|杂|多项)",
        r"查新点1.{0,100}(建议拆|应.*拆|混杂|不清晰|含糊)",
    ]
    xd_issue_found = any(re.search(p, content) for p in xindiian_ambiguity_patterns)
    checks.append({
        "name": "xindiian_ambiguity_detected",
        "passed": xd_issue_found,
        "detail": "Correctly identified that 查新点1 mixes too many distinct technical aspects (dual growth factor, electrospinning, surface treatment)" if xd_issue_found else "Failed to detect that 查新点1 conflates multiple distinct technical points that should be separated"
    })

    # =========================================================
    # CHECK 3: Translation error - "bone protein" for 骨形态发生蛋白
    # Should be "bone morphogenetic protein" or "BMP-2"
    # =========================================================
    bmp_translation_patterns = [
        r"bone protein.{0,50}(错误|不准确|不正确|建议|应为|应该)",
        r"(骨形态发生蛋白|BMP).{0,80}(bone protein|翻译.*错|误译|不准确)",
        r"bone morphogenetic protein",
        r"BMP.{0,30}(建议|推荐|应译|译为)",
        r"(翻译|译法).{0,50}bone protein.{0,50}(不|错|问题|建议)",
    ]
    bmp_issue_found = any(re.search(p, content, re.IGNORECASE) for p in bmp_translation_patterns)
    checks.append({
        "name": "bmp_translation_error_detected",
        "passed": bmp_issue_found,
        "detail": "Correctly identified 'bone protein' as wrong translation for 骨形态发生蛋白 (should be 'bone morphogenetic protein / BMP-2')" if bmp_issue_found else "Failed to detect critical translation error: '骨形态发生蛋白' translated as 'bone protein' instead of 'bone morphogenetic protein'"
    })

    # =========================================================
    # CHECK 4: Translation issue - "vascular growth factor" incomplete
    # Should be "vascular endothelial growth factor" / "VEGF"
    # =========================================================
    vegf_translation_patterns = [
        r"vascular.{0,30}(不完整|不准确|缺少|missing|endothelial|建议|错误)",
        r"(血管内皮生长因子|VEGF).{0,80}(vascular growth factor|翻译|不准|建议|应译)",
        r"vascular endothelial growth factor",
        r"VEGF.{0,30}(建议|推荐|应译|译为|缺失)",
        r"(翻译|译法).{0,50}vascular growth factor",
    ]
    vegf_issue_found = any(re.search(p, content, re.IGNORECASE) for p in vegf_translation_patterns)
    checks.append({
        "name": "vegf_translation_incomplete_detected",
        "passed": vegf_issue_found,
        "detail": "Correctly identified 'vascular growth factor' as incomplete translation for 血管内皮生长因子 (missing 'endothelial')" if vegf_issue_found else "Failed to detect incomplete translation: '血管内皮生长因子' should be 'vascular endothelial growth factor / VEGF', not just 'vascular growth factor'"
    })

    # =========================================================
    # CHECK 5: Over-broad term - "bone" alone as keyword for 骨再生
    # =========================================================
    overbroad_patterns = [
        r"(骨再生|bone regenerat).{0,100}(过宽|太宽|宽泛|噪声|无关|建议.*改|不够精确|检索词.*bone[^a-z])",
        r'"bone".{0,50}(过于宽泛|太宽|建议|不宜单独)',
        r"bone[^\w].{0,60}(过宽|宽泛|噪声|无关文献|不精确|太泛)",
        r"(过宽|过泛|宽泛).{0,60}(bone|骨再生)",
        r"检索词.{0,50}bone.{0,30}(建议|宽泛|噪声|改为|替换)",
    ]
    overbroad_found = any(re.search(p, content, re.IGNORECASE) for p in overbroad_patterns)
    checks.append({
        "name": "overbroad_keyword_bone_detected",
        "passed": overbroad_found,
        "detail": "Correctly identified 'bone' as an overly broad/vague keyword for 骨再生" if overbroad_found else "Failed to identify 'bone' alone as an over-broad keyword that will introduce excessive noise"
    })

    # =========================================================
    # CHECK 6: Missing English keywords issue (scope is 国内外)
    # The search strategy only uses Chinese databases (CNKI, 万方, 维普)
    # but scope is 国内外, so English databases and English keywords are required
    # =========================================================
    missing_en_db_patterns = [
        r"(国内外|检索范围).{0,200}(英文|外文|PubMed|Web of Science|Scopus|Embase|国际)",
        r"(缺少|缺乏|未|没有|未包含).{0,50}(英文数据库|外文数据库|PubMed|Web of Science)",
        r"(PubMed|Web of Science|Scopus|Embase).{0,100}(建议|应|需要|补充|添加)",
        r"(仅|只).{0,30}(中文|国内|CNKI|万方|维普).{0,80}(国内外|不足|建议|外文)",
        r"英文.{0,30}(数据库|检索|文献).{0,50}(缺|未|没|建议|应当)",
    ]
    missing_en_found = any(re.search(p, content, re.IGNORECASE) for p in missing_en_db_patterns)
    checks.append({
        "name": "missing_english_databases_detected",
        "passed": missing_en_found,
        "detail": "Correctly identified that English databases (PubMed/WoS/Scopus) are missing despite 国内外 scope" if missing_en_found else "Failed to detect: 检索范围 is 国内外 but only Chinese databases used — English databases and keywords required"
    })

    # =========================================================
    # CHECK 7: Search formula problem - incomplete/example-only issue
    # Report says "检索式示例" and "实际检索中根据结果调整" - not a complete actual formula
    # =========================================================
    formula_incomplete_patterns = [
        r"检索式.{0,80}(示例|不完整|仅.*示例|实际.*不明|完整.*缺|缺少完整|未提供完整|未列出完整)",
        r"(示例|example).{0,80}(检索式|问题|不足|建议|应提供完整)",
        r"(完整|实际|全部).{0,30}检索式.{0,50}(缺失|未见|未提供|应列出|建议)",
        r"检索策略.{0,100}(不透明|不完整|仅示例|示例.*不够|应.*完整)",
    ]
    formula_incomplete_found = any(re.search(p, content) for p in formula_incomplete_patterns)
    checks.append({
        "name": "incomplete_search_formula_detected",
        "passed": formula_incomplete_found,
        "detail": "Correctly identified that only example search formulas were provided, not complete actual ones" if formula_incomplete_found else "Failed to detect: search formula is labeled as 'example' only and actual full formulas are not documented"
    })

    # =========================================================
    # CHECK 8: Conclusion uses absolute language 填补国内空白/国际领先
    # =========================================================
    absolute_lang_patterns = [
        r"(填补.{0,10}空白|国际领先|国内领先|首创|绝无仅有|世界首).{0,100}(问题|不规范|绝对|建议|应改|不宜|禁用|避免|规范)",
        r"(绝对化|绝对.{0,10}用语|绝对.*表述).{0,100}(填补|领先|首创)",
        r"(不宜|不应|避免|禁止).{0,50}(填补|国际领先|首创|空白)",
        r"(填补.*空白|国际领先).{0,100}(建议改|建议.*修改|替换|不规范|措辞)",
        r"措辞.{0,50}(填补|领先|首创|绝对)",
    ]
    absolute_lang_found = any(re.search(p, content) for p in absolute_lang_patterns)
    checks.append({
        "name": "absolute_language_in_conclusion_detected",
        "passed": absolute_lang_found,
        "detail": "Correctly flagged absolute language ('填补国内空白', '国际领先') in conclusions" if absolute_lang_found else "Failed to detect absolute/prohibited language: '填补了国内空白' and '技术水平国际领先' in conclusions section"
    })

    # =========================================================
    # CHECK 9: 查新点2 has no individual conclusion
    # The conclusion only addresses 查新点1 explicitly; 查新点2 has no per-point analysis
    # =========================================================
    missing_conclusion_patterns = [
        r"查新点2.{0,200}(没有|缺少|缺乏|未见|未有|无对应|无独立|未单独|漏掉|遗漏)",
        r"(缺少|缺乏|未有).{0,50}查新点2.{0,100}(结论|分析|对应)",
        r"查新点.{0,10}2.{0,100}(结论.*缺|未.*结论|没有.*结论|无.*结论)",
        r"逐.{0,10}查新点.{0,100}(缺失|不足|不完整|漏|只有.*一|只.*查新点1)",
        r"(结论.*对应|逐点).{0,100}(缺.*查新点2|查新点2.*未)",
    ]
    missing_conc_found = any(re.search(p, content) for p in missing_conclusion_patterns)
    checks.append({
        "name": "missing_per_point_conclusion_detected",
        "passed": missing_conc_found,
        "detail": "Correctly identified that 查新点2 lacks its own individual conclusion" if missing_conc_found else "Failed to detect: 查新点2 has no corresponding individual conclusion in the conclusions section"
    })

    # =========================================================
    # CHECK 10: Conclusion missing scope qualifier 
    # "在所检索的文献范围内" is required; final conclusion lacks it
    # =========================================================
    scope_qualifier_patterns = [
        r"(缺少|缺乏|未.*使用|没有).{0,80}(在所检索|检索范围内|范围限定|时间.*限定|尚未见报道)",
        r"(规范|限定).{0,50}(在所检索|检索范围内|尚未见报道)",
        r"(在所检索的文献范围内|尚未见报道).{0,100}(建议|缺失|应.*加|应当|需要)",
        r"(结论|综合).{0,100}(缺少.*限定|限定.*缺|范围.*未.*明确)",
        r"(首创|领先|填补).{0,100}(应.*改为|建议.*改|替换为|在所检索)",
    ]
    scope_qual_found = any(re.search(p, content) for p in scope_qualifier_patterns)
    checks.append({
        "name": "missing_scope_qualifier_in_conclusion",
        "passed": scope_qual_found,
        "detail": "Correctly identified missing scope qualifier ('在所检索的文献范围内') in conclusions" if scope_qual_found else "Failed to detect: conclusion lacks required scope-limiting language '在所检索的文献范围内' and uses unqualified absolute statements"
    })

    # =========================================================
    # CHECK 11: Final output has 优先修改事项 section
    # =========================================================
    priority_section_patterns = [
        r"优先修改",
        r"优先.{0,10}(事项|建议|处理)",
        r"(最需要|首先|重点).{0,20}(修改|改进|处理)",
    ]
    priority_found = any(re.search(p, content) for p in priority_section_patterns)
    checks.append({
        "name": "priority_items_section_present",
        "passed": priority_found,
        "detail": "Output includes '优先修改事项' section as required by Step 7" if priority_found else "Missing required '优先修改事项' section in final output"
    })

    # =========================================================
    # CHECK 12: Mandatory disclaimer note at end
    # "本审核结果基于报告文本分析" + mention of time/database limitation
    # =========================================================
    disclaimer_patterns = [
        r"本审核结果基于",
        r"(无法完全替代|不能替代).{0,50}(系统.*检索|复现|全部数据库)",
        r"(当前时间|当前.*检索|百度学术|检索时间).{0,100}(无法|不能|仅供参考)",
        r"审核.*基于.*文本分析",
    ]
    disclaimer_found = any(re.search(p, content) for p in disclaimer_patterns)
    checks.append({
        "name": "mandatory_disclaimer_present",
        "passed": disclaimer_found,
        "detail": "Output includes mandatory disclaimer about limitations of text-based review" if disclaimer_found else "Missing mandatory disclaimer: '本审核结果基于报告文本分析...无法完全替代对全部数据库的系统复现检索'"
    })

    # =========================================================
    # SCORING
    # =========================================================
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_checks / total_checks, 3)
    
    # Must pass at least 8/12 to be considered passing
    overall_passed = passed_checks >= 8

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))