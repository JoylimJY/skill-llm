import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    workspace_path = Path(workspace)

    # ── Helper ─────────────────────────────────────────────────────────────────
    def find_file(filename):
        results = list(workspace_path.rglob(filename))
        return results[0] if results else None

    # ══════════════════════════════════════════════════════════════════════════
    # FILE 1: structure_plan.txt
    # ══════════════════════════════════════════════════════════════════════════
    structure_file = find_file("structure_plan.txt")

    # Check 1: File exists
    checks.append({
        "name": "structure_plan.txt exists",
        "passed": structure_file is not None,
        "detail": str(structure_file) if structure_file else "File not found anywhere in workspace"
    })

    structure_content = ""
    if structure_file:
        try:
            structure_content = structure_file.read_text(encoding="utf-8")
        except Exception as e:
            checks.append({"name": "structure_plan.txt readable", "passed": False, "detail": str(e)})
            structure_content = ""

    # Check 2: Contains required header 【论文结构规划】
    has_structure_header = "【论文结构规划】" in structure_content
    checks.append({
        "name": "structure_plan.txt has '【论文结构规划】' header",
        "passed": has_structure_header,
        "detail": "Header found" if has_structure_header else f"Header '【论文结构规划】' not found in content"
    })

    # Check 3: Contains 论文类型 line
    has_type_line = "论文类型" in structure_content
    checks.append({
        "name": "structure_plan.txt contains '论文类型' field",
        "passed": has_type_line,
        "detail": "Found" if has_type_line else "Missing '论文类型' field"
    })

    # Check 4: Contains all IMRAD sections (摘要, 引言, 方法, 结果, 讨论)
    imrad_sections = ["摘要", "引言", "方法", "结果", "讨论"]
    missing_sections = [s for s in imrad_sections if s not in structure_content]
    has_imrad = len(missing_sections) == 0
    checks.append({
        "name": "structure_plan.txt contains all IMRAD sections (摘要/引言/方法/结果/讨论)",
        "passed": has_imrad,
        "detail": f"All sections present" if has_imrad else f"Missing sections: {missing_sections}"
    })

    # Check 5: Contains word count recommendations (字数 with numbers)
    has_word_counts = bool(re.search(r'字数.*?\d+', structure_content))
    checks.append({
        "name": "structure_plan.txt contains word count recommendations",
        "passed": has_word_counts,
        "detail": "Word count recommendations found" if has_word_counts else "No word count info found"
    })

    # Check 6: Abstract word count mentions 200-300 range
    abstract_section = ""
    lines = structure_content.split('\n')
    in_abstract = False
    for line in lines:
        if '摘要' in line:
            in_abstract = True
        elif any(s in line for s in ['引言', '方法', '结果', '讨论', '结论']):
            in_abstract = False
        if in_abstract:
            abstract_section += line + '\n'
    
    has_abstract_wordcount = bool(re.search(r'200|250|300', abstract_section))
    checks.append({
        "name": "structure_plan.txt abstract section mentions ~200-300 word count",
        "passed": has_abstract_wordcount,
        "detail": f"Abstract word count range found" if has_abstract_wordcount else "No 200-300 word count in abstract section"
    })

    # ══════════════════════════════════════════════════════════════════════════
    # FILE 2: polish_report.txt
    # ══════════════════════════════════════════════════════════════════════════
    polish_file = find_file("polish_report.txt")

    checks.append({
        "name": "polish_report.txt exists",
        "passed": polish_file is not None,
        "detail": str(polish_file) if polish_file else "File not found anywhere in workspace"
    })

    polish_content = ""
    if polish_file:
        try:
            polish_content = polish_file.read_text(encoding="utf-8")
        except Exception as e:
            checks.append({"name": "polish_report.txt readable", "passed": False, "detail": str(e)})
            polish_content = ""

    # Check 7: Contains required header 【润色报告】
    has_polish_header = "【润色报告】" in polish_content
    checks.append({
        "name": "polish_report.txt has '【润色报告】' header",
        "passed": has_polish_header,
        "detail": "Header found" if has_polish_header else "Header '【润色报告】' not found"
    })

    # Check 8: Contains ✗ marker for original text
    has_cross_marker = "✗" in polish_content
    checks.append({
        "name": "polish_report.txt uses '✗' marker for original text",
        "passed": has_cross_marker,
        "detail": "'✗' marker found" if has_cross_marker else "Required '✗' marker missing"
    })

    # Check 9: Contains ✓ marker for suggestions
    has_check_marker = "✓" in polish_content
    checks.append({
        "name": "polish_report.txt uses '✓' marker for suggestions",
        "passed": has_check_marker,
        "detail": "'✓' marker found" if has_check_marker else "Required '✓' marker missing"
    })

    # Check 10: Contains improvement type section (改进类型)
    has_improvement_types = "改进类型" in polish_content
    checks.append({
        "name": "polish_report.txt contains '改进类型' section",
        "passed": has_improvement_types,
        "detail": "Found" if has_improvement_types else "'改进类型' section missing"
    })

    # Check 11: Contains 原文 and 建议 labels
    has_yuanwen = "原文" in polish_content
    has_jianyi = "建议" in polish_content
    has_labels = has_yuanwen and has_jianyi
    checks.append({
        "name": "polish_report.txt uses '原文' and '建议' labels",
        "passed": has_labels,
        "detail": f"原文: {has_yuanwen}, 建议: {has_jianyi}"
    })

    # Check 12: At least 2 polish examples (multiple ✗ markers means multiple fixes)
    cross_count = polish_content.count("✗")
    has_multiple_polish = cross_count >= 2
    checks.append({
        "name": "polish_report.txt has at least 2 polishing examples",
        "passed": has_multiple_polish,
        "detail": f"Found {cross_count} '✗' markers (need ≥2)"
    })

    # Check 13: Academic language normalization improvement mentioned
    academic_keywords = ["学术用语", "规范化", "口语化", "表达", "专业"]
    has_academic_improvement = any(kw in polish_content for kw in academic_keywords)
    checks.append({
        "name": "polish_report.txt mentions academic language issues",
        "passed": has_academic_improvement,
        "detail": "Academic language issue noted" if has_academic_improvement else f"No mention of: {academic_keywords}"
    })

    # ══════════════════════════════════════════════════════════════════════════
    # FILE 3: references_formatted.txt
    # ══════════════════════════════════════════════════════════════════════════
    refs_file = find_file("references_formatted.txt")

    checks.append({
        "name": "references_formatted.txt exists",
        "passed": refs_file is not None,
        "detail": str(refs_file) if refs_file else "File not found anywhere in workspace"
    })

    refs_content = ""
    if refs_file:
        try:
            refs_content = refs_file.read_text(encoding="utf-8")
        except Exception as e:
            checks.append({"name": "references_formatted.txt readable", "passed": False, "detail": str(e)})
            refs_content = ""

    # Check 14: Contains header 【参考文献整理】
    has_refs_header = "【参考文献整理】" in refs_content
    checks.append({
        "name": "references_formatted.txt has '【参考文献整理】' header",
        "passed": has_refs_header,
        "detail": "Header found" if has_refs_header else "Header '【参考文献整理】' not found"
    })

    # Check 15: Mentions GB/T 7714 format
    has_gbt = bool(re.search(r'GB/T\s*7714', refs_content))
    checks.append({
        "name": "references_formatted.txt specifies GB/T 7714 format",
        "passed": has_gbt,
        "detail": "GB/T 7714 mentioned" if has_gbt else "Format specification missing"
    })

    # Check 16: Uses [J] tag for journal articles
    has_J_tag = "[J]" in refs_content
    checks.append({
        "name": "references_formatted.txt uses [J] tag for journal articles",
        "passed": has_J_tag,
        "detail": "[J] tag found" if has_J_tag else "[J] tag missing (required by GB/T 7714 for journals)"
    })

    # Check 17: Uses [C] tag for conference papers
    has_C_tag = "[C]" in refs_content
    checks.append({
        "name": "references_formatted.txt uses [C] tag for conference papers",
        "passed": has_C_tag,
        "detail": "[C] tag found" if has_C_tag else "[C] tag missing (required for conference papers)"
    })

    # Check 18: Contains all 5 references (McMahan/FedAvg, Dwork, Bonawitz, Geyer, 李志远)
    expected_authors = ["McMahan", "Dwork", "Bonawitz", "Geyer", "李志远"]
    found_authors = [a for a in expected_authors if a in refs_content]
    all_refs_present = len(found_authors) == len(expected_authors)
    checks.append({
        "name": "references_formatted.txt contains all 5 references",
        "passed": all_refs_present,
        "detail": f"Found {len(found_authors)}/5: {found_authors}" if not all_refs_present else "All 5 references present"
    })

    # Check 19: McMahan reference uses [C] (conference paper - AISTATS)
    mcmahan_idx = refs_content.find("McMahan")
    if mcmahan_idx != -1:
        # Get the line containing McMahan
        mcmahan_line_start = refs_content.rfind('\n', 0, mcmahan_idx) + 1
        mcmahan_line_end = refs_content.find('\n', mcmahan_idx)
        mcmahan_line = refs_content[mcmahan_line_start:mcmahan_line_end if mcmahan_line_end != -1 else len(refs_content)]
        # McMahan is a conference paper (AISTATS), should use [C]
        mcmahan_has_C = "[C]" in mcmahan_line
        checks.append({
            "name": "McMahan reference correctly tagged as [C] (conference paper)",
            "passed": mcmahan_has_C,
            "detail": f"McMahan line: '{mcmahan_line.strip()}'" 
        })
    else:
        checks.append({
            "name": "McMahan reference correctly tagged as [C] (conference paper)",
            "passed": False,
            "detail": "McMahan reference not found"
        })

    # Check 20: 李志远 reference uses [J] (journal article - 计算机学报)
    lzy_idx = refs_content.find("李志远")
    if lzy_idx != -1:
        lzy_line_start = refs_content.rfind('\n', 0, lzy_idx) + 1
        lzy_line_end = refs_content.find('\n', lzy_idx)
        lzy_line = refs_content[lzy_line_start:lzy_line_end if lzy_line_end != -1 else len(refs_content)]
        lzy_has_J = "[J]" in lzy_line
        checks.append({
            "name": "李志远 reference correctly tagged as [J] (journal article)",
            "passed": lzy_has_J,
            "detail": f"李志远 line: '{lzy_line.strip()}'"
        })
    else:
        checks.append({
            "name": "李志远 reference correctly tagged as [J] (journal article)",
            "passed": False,
            "detail": "李志远 reference not found"
        })

    # ══════════════════════════════════════════════════════════════════════════
    # Scoring
    # ══════════════════════════════════════════════════════════════════════════
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall_passed = score >= 0.75

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))