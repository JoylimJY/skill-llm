import sys
import os
import re
import json
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    total_score = 0.0
    
    # Find the output file - look for any file named 'humanized_output.txt' anywhere in workspace
    output_files = list(Path(workspace_dir).rglob("humanized_output.txt"))
    
    if not output_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_exists", "passed": False, "detail": "humanized_output.txt not found anywhere in workspace."}]
        }
    
    output_path = output_files[0]
    checks.append({"name": "output_file_exists", "passed": True, "detail": f"Found at {output_path}"})
    
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_readable", "passed": False, "detail": f"Cannot read file: {e}"}]
        }
    
    # -----------------------------------------------------------------------
    # CHECK 1: Required section headers present
    # -----------------------------------------------------------------------
    required_sections = [
        "【处理后的论文内容】",
        "【错别字清单】",
        "【语序/修辞错误清单】",
        "【新增引用】",
        "【技术使用记录】",
    ]
    missing_sections = []
    for section in required_sections:
        if section not in content:
            missing_sections.append(section)
    
    sections_passed = len(missing_sections) == 0
    checks.append({
        "name": "required_sections_present",
        "passed": sections_passed,
        "detail": f"Missing sections: {missing_sections}" if missing_sections else "All 5 required sections found."
    })
    if sections_passed:
        total_score += 15.0

    # -----------------------------------------------------------------------
    # CHECK 2: Typo count in 错别字清单 (must be 3-5)
    # -----------------------------------------------------------------------
    typo_section_match = re.search(r'【错别字清单】.*?(?=【|$)', content, re.DOTALL)
    typo_count_ok = False
    typo_detail = "错别字清单 section not found."
    
    if typo_section_match:
        typo_section = typo_section_match.group(0)
        # Count numbered entries like "1. " "2. " etc.
        entries = re.findall(r'^\s*\d+[\.、]\s+.+', typo_section, re.MULTILINE)
        num_typos = len(entries)
        # Also check for the count declaration pattern "共 X 处"
        count_decl = re.search(r'共\s*(\d+)\s*处', typo_section)
        declared_count = int(count_decl.group(1)) if count_decl else None
        
        if 3 <= num_typos <= 5:
            typo_count_ok = True
            typo_detail = f"Found {num_typos} typo entries (valid range: 3-5). Declared count: {declared_count}."
        else:
            typo_detail = f"Found {num_typos} typo entries in list (required: 3-5). Declared count: {declared_count}."
    
    checks.append({"name": "typo_count_3_to_5", "passed": typo_count_ok, "detail": typo_detail})
    if typo_count_ok:
        total_score += 20.0

    # -----------------------------------------------------------------------
    # CHECK 3: Inline typo annotation format [正确：X] in the main text
    # -----------------------------------------------------------------------
    # Find the processed text section
    processed_text_match = re.search(
        r'【处理后的论文内容】(.*?)(?=【错别字清单】|【语序|【新增|【技术|$)',
        content, re.DOTALL
    )
    inline_annotation_ok = False
    inline_detail = "Could not find 处理后的论文内容 section."
    
    if processed_text_match:
        processed_text = processed_text_match.group(1)
        # Must contain [正确：X] style annotations (with Chinese colon or ASCII colon)
        annotations = re.findall(r'\[正确[：:][^\]]+\]', processed_text)
        num_annotations = len(annotations)
        if 3 <= num_annotations <= 5:
            inline_annotation_ok = True
            inline_detail = f"Found {num_annotations} inline [正确：X] annotations in main text (valid: 3-5). Examples: {annotations[:3]}"
        else:
            inline_detail = f"Found {num_annotations} inline [正确：X] annotations in main text (required: 3-5). Found: {annotations}"
    
    checks.append({"name": "inline_typo_annotations_format", "passed": inline_annotation_ok, "detail": inline_detail})
    if inline_annotation_ok:
        total_score += 20.0

    # -----------------------------------------------------------------------
    # CHECK 4: Grammar/word-order error count in 语序/修辞错误清单 (must be ≤10, at least 1)
    # -----------------------------------------------------------------------
    grammar_section_match = re.search(r'【语序/修辞错误清单】.*?(?=【|$)', content, re.DOTALL)
    grammar_count_ok = False
    grammar_detail = "语序/修辞错误清单 section not found."
    
    if grammar_section_match:
        grammar_section = grammar_section_match.group(0)
        grammar_entries = re.findall(r'^\s*\d+[\.、]\s+.+', grammar_section, re.MULTILINE)
        num_grammar = len(grammar_entries)
        count_decl_g = re.search(r'共\s*(\d+)\s*处', grammar_section)
        declared_g = int(count_decl_g.group(1)) if count_decl_g else None
        
        if 1 <= num_grammar <= 10:
            grammar_count_ok = True
            grammar_detail = f"Found {num_grammar} grammar/word-order error entries (valid: 1-10). Declared: {declared_g}."
        else:
            grammar_detail = f"Found {num_grammar} grammar/word-order error entries (required: 1-10). Declared: {declared_g}."
    
    checks.append({"name": "grammar_error_count_valid", "passed": grammar_count_ok, "detail": grammar_detail})
    if grammar_count_ok:
        total_score += 15.0

    # -----------------------------------------------------------------------
    # CHECK 5: New citations added (3-5 citations in 新增引用 section)
    # -----------------------------------------------------------------------
    citation_section_match = re.search(r'【新增引用】.*?(?=【|$)', content, re.DOTALL)
    citation_count_ok = False
    citation_detail = "新增引用 section not found."
    
    if citation_section_match:
        citation_section = citation_section_match.group(0)
        citation_entries = re.findall(r'^\s*\d+[\.、]\s+.+', citation_section, re.MULTILINE)
        num_citations = len(citation_entries)
        if 3 <= num_citations <= 5:
            citation_count_ok = True
            citation_detail = f"Found {num_citations} citation entries (valid: 3-5)."
        else:
            citation_detail = f"Found {num_citations} citation entries (required: 3-5)."
    
    checks.append({"name": "citations_count_3_to_5", "passed": citation_count_ok, "detail": citation_detail})
    if citation_count_ok:
        total_score += 15.0

    # -----------------------------------------------------------------------
    # CHECK 6: 技术使用记录 contains all 7 required metrics
    # -----------------------------------------------------------------------
    tech_section_match = re.search(r'【技术使用记录】.*?(?=【|$)', content, re.DOTALL)
    tech_record_ok = False
    tech_detail = "技术使用记录 section not found."
    
    if tech_section_match:
        tech_section = tech_section_match.group(0)
        required_metrics = [
            "逻辑重构",
            "同义词替换",
            "句子结构重组",
            "注入个人观点",
            "新增引用",
            "植入错别字",
            "植入语序错误",
        ]
        missing_metrics = [m for m in required_metrics if m not in tech_section]
        if not missing_metrics:
            tech_record_ok = True
            tech_detail = "All 7 required metrics present in 技术使用记录."
        else:
            tech_detail = f"Missing metrics in 技术使用记录: {missing_metrics}"
    
    checks.append({"name": "tech_record_all_7_metrics", "passed": tech_record_ok, "detail": tech_detail})
    if tech_record_ok:
        total_score += 10.0

    # -----------------------------------------------------------------------
    # CHECK 7: Processed text actually differs substantially from AI original
    # (checks that AI-pattern words were replaced - at least 3 replacements from the mapping)
    # -----------------------------------------------------------------------
    ai_patterns = ["值得注意的是", "首先", "其次", "最后", "此外", "综上所述", "非常重要", "很大提高"]
    if processed_text_match:
        processed_text = processed_text_match.group(1)
        remaining_ai_patterns = [p for p in ai_patterns if p in processed_text]
        # Should have reduced AI patterns significantly (allow at most 3 remaining)
        patterns_reduced = len(remaining_ai_patterns) <= 3
        checks.append({
            "name": "ai_patterns_reduced",
            "passed": patterns_reduced,
            "detail": f"AI-pattern phrases still present: {remaining_ai_patterns} ({len(remaining_ai_patterns)} remaining, max allowed: 3)"
        })
        if patterns_reduced:
            total_score += 5.0
    else:
        checks.append({"name": "ai_patterns_reduced", "passed": False, "detail": "Could not evaluate: 处理后的论文内容 not found."})

    # -----------------------------------------------------------------------
    # FINAL RESULT
    # -----------------------------------------------------------------------
    max_score = 100.0
    normalized_score = round(total_score / max_score, 4)
    passed = (
        sections_passed
        and typo_count_ok
        and inline_annotation_ok
        and grammar_count_ok
        and citation_count_ok
        and tech_record_ok
    )

    return {
        "passed": passed,
        "score": normalized_score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)
    
    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))