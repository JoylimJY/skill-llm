import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str) -> dict:
    checks = []
    workspace = Path(workspace)
    
    # ─── Helper ─────────────────────────────────────────────────────────────
    def find_research_dir():
        """Find the Zimbabwe_mining research directory under Downloads/research/"""
        candidates = list((workspace / "Downloads" / "research").glob("Zimbabwe*mining*")) + \
                     list((workspace / "Downloads" / "research").glob("zimbabwe*mining*")) + \
                     list((workspace / "Downloads" / "research").glob("*Zimbabwe*")) + \
                     list((workspace / "Downloads" / "research").glob("*zimbabwe*"))
        if candidates:
            return candidates[0]
        # Also search globally
        all_candidates = list(workspace.rglob("*Zimbabwe*mining*")) + \
                         list(workspace.rglob("*zimbabwe*mining*"))
        dirs = [p for p in all_candidates if p.is_dir()]
        if dirs:
            return dirs[0]
        return None

    def read_file(path):
        try:
            return path.read_text(encoding='utf-8')
        except Exception:
            return None

    def find_file_in_dir(research_dir, pattern):
        """Find a file matching the pattern in the research directory."""
        if research_dir is None:
            return None
        matches = list(research_dir.glob(pattern))
        if matches:
            return matches[0]
        return None

    # ─── Check 1: Correct directory structure ───────────────────────────────
    research_dir = find_research_dir()
    check1_passed = research_dir is not None and research_dir.is_dir()
    checks.append({
        "name": "correct_directory_structure",
        "passed": check1_passed,
        "detail": f"Found research dir: {research_dir}" if check1_passed else 
                  "No Zimbabwe_mining research directory found under Downloads/research/"
    })

    # ─── Check 2: 00_问题拆解.md exists and contains required elements ──────
    wt_file = find_file_in_dir(research_dir, "00_问题拆解*") if research_dir else None
    if wt_file is None and research_dir:
        wt_file = find_file_in_dir(research_dir, "00*")
    wt_content = read_file(wt_file) if wt_file else None
    
    check2_required = ["Zimbabwe", "矿业", "时间", "主体"]
    check2_alt = ["zimbabwe", "mining", "platinum", "时间节点"]
    
    if wt_content:
        content_lower = wt_content.lower()
        has_country = "zimbabwe" in content_lower or "津巴布韦" in wt_content
        has_topic = any(k in wt_content for k in ["矿业", "mining", "platinum", "铂金", "platinum"])
        has_structure = any(k in wt_content for k in ["时间", "主体", "法律领域", "东道国", "边界"])
        check2_passed = has_country and has_topic and has_structure
    else:
        check2_passed = False
    
    checks.append({
        "name": "step1_problem_decomposition_00",
        "passed": check2_passed,
        "detail": f"00_问题拆解.md found: {wt_file is not None}, content ok: {check2_passed}"
    })

    # ─── Check 3: 01_资料来源.md with priority tier sources ─────────────────
    src_file = find_file_in_dir(research_dir, "01_资料来源*") if research_dir else None
    if src_file is None and research_dir:
        src_file = find_file_in_dir(research_dir, "01*")
    src_content = read_file(src_file) if src_file else None
    
    # Must reference at least 2 priority-1 sources from SKILL.md
    priority1_sources = ["iclg", "chambers", "legal500", "lex mundi", "lexmundi"]
    priority1_found = []
    if src_content:
        content_lower = src_content.lower()
        for src in priority1_sources:
            if src in content_lower:
                priority1_found.append(src)
    
    # Must include date/timeliness info
    has_date_info = bool(src_content and re.search(r'20\d\d', src_content))
    has_timeliness = bool(src_content and any(k in src_content for k in ["时效", "发布日期", "date", "时间", "截至"]))
    
    check3_passed = len(priority1_found) >= 2 and has_date_info and has_timeliness
    checks.append({
        "name": "step2_sources_with_priority_tiers_01",
        "passed": check3_passed,
        "detail": f"Priority-1 sources found: {priority1_found}, has_date: {has_date_info}, has_timeliness: {has_timeliness}"
    })

    # ─── Check 4: 02_事实卡片.md with 🟢/🟡/🔴 classification ─────────────
    fact_file = find_file_in_dir(research_dir, "02_事实卡片*") if research_dir else None
    if fact_file is None and research_dir:
        fact_file = find_file_in_dir(research_dir, "02*")
    fact_content = read_file(fact_file) if fact_file else None
    
    has_green = bool(fact_content and ("🟢" in fact_content or "官方规定" in fact_content))
    has_yellow = bool(fact_content and ("🟡" in fact_content or "机构解读" in fact_content))
    has_red = bool(fact_content and ("🔴" in fact_content or "推测分析" in fact_content or "待核实" in fact_content))
    has_zim_content = bool(fact_content and ("Zimbabwe" in fact_content or "津巴布韦" in fact_content or 
                                              "ZIDA" in fact_content or "mining" in (fact_content or "").lower()))
    
    check4_passed = has_green and (has_yellow or has_red) and has_zim_content
    checks.append({
        "name": "step3_fact_cards_color_classification_02",
        "passed": check4_passed,
        "detail": f"🟢:{has_green}, 🟡:{has_yellow}, 🔴:{has_red}, Zimbabwe content:{has_zim_content}"
    })

    # ─── Check 5: 05.5_校验记录.md (BLOCKING independent agent check) ───────
    verify_file = find_file_in_dir(research_dir, "05.5*") if research_dir else None
    if verify_file is None and research_dir:
        # Try alternate naming
        verify_file = find_file_in_dir(research_dir, "*校验*")
    verify_content = read_file(verify_file) if verify_file else None
    
    has_verification_content = bool(verify_content and len(verify_content.strip()) > 50)
    has_check_items = bool(verify_content and any(k in verify_content for k in 
                                                   ["核实", "校验", "逻辑", "遗漏", "数字", "条款", "验证", "check"]))
    
    check5_passed = verify_file is not None and has_verification_content and has_check_items
    checks.append({
        "name": "step6_5_blocking_independent_verification_05_5",
        "passed": check5_passed,
        "detail": f"05.5_校验记录.md found: {verify_file is not None}, has content: {has_verification_content}, has check items: {has_check_items}"
    })

    # ─── Check 6: 05_验证记录.md (Sanity Check) ─────────────────────────────
    sanity_file = find_file_in_dir(research_dir, "05_验证*") if research_dir else None
    if sanity_file is None and research_dir:
        sanity_file = find_file_in_dir(research_dir, "05_*")
    sanity_content = read_file(sanity_file) if sanity_file else None
    
    has_scenario = bool(sanity_content and any(k in sanity_content for k in 
                                                ["场景", "scenario", "例外", "验证", "适用", "案例", "情形", "sanity"]))
    check6_passed = sanity_file is not None and has_scenario and len((sanity_content or "").strip()) > 30
    checks.append({
        "name": "step7_sanity_check_05",
        "passed": check6_passed,
        "detail": f"05_验证记录.md found: {sanity_file is not None}, has scenario check: {has_scenario}"
    })

    # ─── Check 7: FINAL_调研报告.md exists and has 7-section structure ───────
    final_files = list(workspace.rglob("FINAL_调研报告*"))
    if not final_files and research_dir:
        final_files = list(research_dir.glob("FINAL*"))
    
    final_file = final_files[0] if final_files else None
    final_content = read_file(final_file) if final_file else None
    
    # Check 7-section structure
    required_sections = [
        r"摘要|summary|executive",
        r"免责声明|disclaimer",
        r"调研背景|背景|scope|范围",
        r"法律框架|legal framework|法律体系",
        r"核心规定|key provisions|主要规定",
        r"程序|procedure|流程",
        r"风险|risk|注意事项",
    ]
    sections_found = []
    if final_content:
        content_lower = final_content.lower()
        for pattern in required_sections:
            if re.search(pattern, final_content, re.IGNORECASE):
                sections_found.append(pattern.split("|")[0])
    
    check7_passed = final_file is not None and len(sections_found) >= 5
    checks.append({
        "name": "step8_final_report_7_section_structure",
        "passed": check7_passed,
        "detail": f"FINAL report found: {final_file is not None}, sections found ({len(sections_found)}/7): {sections_found}"
    })

    # ─── Check 8: Mandatory dual disclaimer in FINAL report ─────────────────
    has_legal_disclaimer = bool(final_content and any(k in final_content for k in 
                                                       ["不构成法律意见", "法律意见", "legal advice", "不构成", 
                                                        "当地律师", "local counsel", "local lawyer"]))
    has_timeliness_decl = bool(final_content and any(k in final_content for k in 
                                                      ["截至", "资料截至", "as of", "时效", "法律可能变化", 
                                                       "may change", "变化"]))
    check8_passed = has_legal_disclaimer and has_timeliness_decl
    checks.append({
        "name": "step8_mandatory_dual_disclaimer",
        "passed": check8_passed,
        "detail": f"Legal disclaimer: {has_legal_disclaimer}, Timeliness declaration: {has_timeliness_decl}"
    })

    # ─── Check 9: Source citations in FINAL report ───────────────────────────
    has_sources_section = bool(final_content and any(k in final_content for k in 
                                                      ["参考资源", "来源", "reference", "source", "资料来源"]))
    has_urls_or_citations = bool(final_content and (
        re.search(r'https?://', final_content) or
        re.search(r'iclg|lexmundi|chambers|legal500', final_content, re.IGNORECASE) or
        re.search(r'ICLG|Lex Mundi|Chambers|Legal500', final_content)
    ))
    check9_passed = has_sources_section and has_urls_or_citations
    checks.append({
        "name": "step8_source_citations_in_final_report",
        "passed": check9_passed,
        "detail": f"Sources section: {has_sources_section}, URL/citation present: {has_urls_or_citations}"
    })

    # ─── Check 10: Timeliness sensitivity marking (Step 0.5) ─────────────────
    # Should appear somewhere in the research docs - all foreign law is 🔴 extremely high
    sensitivity_files = []
    if research_dir:
        for f in research_dir.rglob("*.md"):
            content = read_file(f)
            if content and any(k in content for k in ["极高", "🔴", "时效", "6个月", "官方来源", "Official Gazette"]):
                sensitivity_files.append(f.name)
    
    check10_passed = len(sensitivity_files) >= 1
    checks.append({
        "name": "step0_5_timeliness_sensitivity_marked",
        "passed": check10_passed,
        "detail": f"Files with timeliness sensitivity marking: {sensitivity_files}"
    })

    # ─── Scoring ────────────────────────────────────────────────────────────
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks

    # BLOCKING checks: 05.5 and final report are required to pass
    blocking_passed = (
        checks[4]["passed"] and  # 05.5_校验记录
        checks[6]["passed"] and  # FINAL_调研报告
        checks[7]["passed"]      # dual disclaimer
    )
    
    overall_passed = score >= 0.7 and blocking_passed

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/home/researcher"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))