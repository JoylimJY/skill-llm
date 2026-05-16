import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    score = 0.0
    total_weight = 0.0

    def add_check(name, passed, detail, weight=1.0):
        nonlocal score, total_weight
        checks.append({"name": name, "passed": passed, "detail": detail})
        total_weight += weight
        if passed:
            score += weight

    # Find the output markdown file
    workspace_path = Path(workspace)
    md_files = list(workspace_path.rglob("*.md"))
    
    # Filter out distractor files
    distractor_paths = {
        "wrong_template.md",
        "analysis_draft.md",
        "template_analysis.md",
    }
    
    candidate_files = [
        f for f in md_files
        if f.name not in distractor_paths
        and "SKILL" not in f.name
        and "wrong" not in f.name.lower()
        and "template" not in f.name.lower()
        and "deprecated" not in f.name.lower()
    ]
    
    # Try to find an analysis output file
    analysis_file = None
    for f in candidate_files:
        try:
            content = f.read_text(encoding="utf-8")
            # Must contain at least one Chinese section header
            if "问题的提出" in content or "实证研究" in content or "识别策略" in content:
                analysis_file = f
                break
        except Exception:
            continue

    if analysis_file is None:
        add_check("output_file_exists", False, 
                  f"No valid analysis markdown file with Chinese headers found. Candidates: {[str(f) for f in candidate_files]}", 
                  weight=3.0)
        total_checks_passed = sum(1 for c in checks if c["passed"])
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    try:
        content = analysis_file.read_text(encoding="utf-8")
    except Exception as e:
        add_check("output_file_readable", False, f"Could not read file: {e}", weight=3.0)
        return {"passed": False, "score": 0.0, "checks": checks}

    add_check("output_file_exists", True, f"Found analysis file: {analysis_file}", weight=2.0)

    # Check 1: Paper title in output
    title_present = "Racial Bias" in content or "Algorithmic Risk Assessment" in content or "Bail Decisions" in content
    add_check(
        "paper_title_referenced",
        title_present,
        "Paper title keywords found in output." if title_present else "Paper title not found in output.",
        weight=1.0
    )

    # Check 2: Authors present
    authors_present = (
        ("Harrison" in content or "Michael" in content) and
        ("Sundaram" in content or "Priya" in content)
    )
    add_check(
        "authors_present",
        authors_present,
        "Author names found." if authors_present else "Author names not found.",
        weight=1.0
    )

    # Check 3: Section 1 - Chinese header 问题的提出
    has_section1 = bool(re.search(r'问题的提出', content))
    add_check(
        "section1_chinese_header",
        has_section1,
        "Section '问题的提出' found." if has_section1 else "Missing required Chinese section '问题的提出'.",
        weight=2.0
    )

    # Check 4: Section 2 - Chinese header 实证研究的核心难题
    has_section2 = bool(re.search(r'实证研究的核心难题', content))
    add_check(
        "section2_chinese_header",
        has_section2,
        "Section '实证研究的核心难题' found." if has_section2 else "Missing required Chinese section '实证研究的核心难题'.",
        weight=2.0
    )

    # Check 5: Section 2 sub-headers must use 难题一, 难题二 format
    has_nanti1 = bool(re.search(r'难题[一二三四五]', content))
    add_check(
        "section2_nanti_format",
        has_nanti1,
        "Empirical challenges labeled using '难题一/二...' format." if has_nanti1 else
        "Missing '难题一/二...' labels for empirical challenges. This is a required proprietary format.",
        weight=2.5
    )

    # Check 6: At least 2 distinct 难题 entries
    nanti_count = len(re.findall(r'难题[一二三四五]', content))
    has_multiple_nanti = nanti_count >= 2
    add_check(
        "section2_multiple_challenges",
        has_multiple_nanti,
        f"Found {nanti_count} empirical challenges (需≥2)." ,
        weight=1.5
    )

    # Check 7: Section 3 - 识别策略与方法设计
    has_section3 = bool(re.search(r'识别策略', content))
    add_check(
        "section3_chinese_header",
        has_section3,
        "Section '识别策略' found." if has_section3 else "Missing required Chinese section '识别策略'.",
        weight=2.0
    )

    # Check 8: Section 3 must contain data source sub-section (数据来源)
    has_data_source = bool(re.search(r'数据来源', content))
    add_check(
        "section3_data_source",
        has_data_source,
        "Sub-section '数据来源' found in identification strategy section." if has_data_source else
        "Missing '数据来源' sub-section within identification strategy section.",
        weight=1.5
    )

    # Check 9: Section 4 - 重要发现与结论
    has_section4 = bool(re.search(r'重要发现', content))
    add_check(
        "section4_chinese_header",
        has_section4,
        "Section '重要发现' found." if has_section4 else "Missing required Chinese section '重要发现'.",
        weight=2.0
    )

    # Check 10: Section 4 must use 发现一/发现二 bullet format
    has_finding_format = bool(re.search(r'发现[一二三四五]', content))
    add_check(
        "section4_finding_format",
        has_finding_format,
        "Findings labeled using '发现一/二...' format." if has_finding_format else
        "Missing '发现一/二...' labels for findings. Required by framework.",
        weight=2.5
    )

    # Check 11: Section 4 must include 政策含义
    has_policy = bool(re.search(r'政策含义', content))
    add_check(
        "section4_policy_implications",
        has_policy,
        "Policy implications '政策含义' found." if has_policy else
        "Missing '政策含义' in findings section. Required by framework.",
        weight=1.5
    )

    # Check 12: Section 5 - 学术价值
    has_section5 = bool(re.search(r'学术价值', content))
    add_check(
        "section5_chinese_header",
        has_section5,
        "Section '学术价值' found." if has_section5 else "Missing required Chinese section '学术价值'.",
        weight=2.0
    )

    # Check 13: Section 5 must include 方法论贡献
    has_method_contrib = bool(re.search(r'方法论贡献', content))
    add_check(
        "section5_methodological_contribution",
        has_method_contrib,
        "'方法论贡献' dimension found in academic contribution section." if has_method_contrib else
        "Missing '方法论贡献' in academic contribution section.",
        weight=1.5
    )

    # Check 14: Section 5 must include 理论贡献 or 政策相关性
    has_theory_or_policy = bool(re.search(r'理论贡献|政策相关性', content))
    add_check(
        "section5_theory_or_policy_relevance",
        has_theory_or_policy,
        "'理论贡献' or '政策相关性' found in academic contribution section." if has_theory_or_policy else
        "Missing '理论贡献' and '政策相关性' in academic contribution section.",
        weight=1.5
    )

    # Check 15: Mathematical notation present (regression equation)
    has_math = bool(re.search(r'\$.*Y.*=.*alpha|\\alpha|\$Y_\{|Y_\{ict\}|\\beta|beta_k', content)) or \
               bool(re.search(r'\$[^$]+\\beta[^$]+\$', content)) or \
               bool(re.search(r'Y_\{?ict\}?|\\delta_c|\\lambda_t|epsilon_\{', content)) or \
               bool(re.search(r'\$\$|\$Y|\$\\', content))
    add_check(
        "mathematical_notation_present",
        has_math,
        "Mathematical/LaTeX notation found for regression specification." if has_math else
        "No mathematical notation found. SKILL.md requires LaTeX regression specs.",
        weight=2.0
    )

    # Check 16: Key numbers from paper present (quantitative findings)
    has_key_numbers = (
        ("12.3" in content or "12.3%" in content) and
        ("18.7" in content or "4.1" in content or "14.6" in content)
    )
    add_check(
        "key_quantitative_findings",
        has_key_numbers,
        "Key quantitative findings (12.3pp, 18.7pp, 4.1pp differentials) found." if has_key_numbers else
        "Missing key quantitative findings. Effect sizes should be reported with magnitude.",
        weight=2.0
    )

    # Check 17: DID or staggered DID mentioned
    has_did = bool(re.search(r'双重差分|DID|difference.in.difference|Callaway|Sant.Anna|Goodman.Bacon', content, re.IGNORECASE))
    add_check(
        "identification_strategy_did",
        has_did,
        "DID/staggered DID identification strategy correctly identified." if has_did else
        "Identification strategy not clearly described. DID approach should be documented.",
        weight=1.5
    )

    # Check 18: Selective labels problem mentioned as a core challenge
    has_selective_labels = bool(re.search(r'selective label|选择性标签|选择偏误.*标签|标签.*选择', content, re.IGNORECASE))
    add_check(
        "selective_labels_challenge",
        has_selective_labels,
        "Selective labels problem identified as a core empirical challenge." if has_selective_labels else
        "Selective labels problem not clearly identified. This is a key challenge in the paper.",
        weight=1.5
    )

    # Check 19: Parallel trends assumption mentioned
    has_parallel_trends = bool(re.search(r'平行趋势|parallel trend|pre.trend|event.study|事件研究', content, re.IGNORECASE))
    add_check(
        "parallel_trends_assumption",
        has_parallel_trends,
        "Parallel trends assumption discussed in identification strategy." if has_parallel_trends else
        "Parallel trends assumption not mentioned. This is critical for DID validity.",
        weight=1.0
    )

    # Check 20: Output is substantially long (not a stub)
    content_length = len(content)
    is_substantial = content_length >= 2000
    add_check(
        "output_is_substantial",
        is_substantial,
        f"Output length {content_length} chars (minimum 2000 required).",
        weight=1.5
    )

    # Calculate final score
    final_score = score / total_weight if total_weight > 0 else 0.0
    
    # Must pass critical checks to pass overall
    critical_checks = [
        "section1_chinese_header",
        "section2_chinese_header", 
        "section2_nanti_format",
        "section3_chinese_header",
        "section4_chinese_header",
        "section4_finding_format",
        "section5_chinese_header",
    ]
    
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )
    
    overall_passed = critical_passed and final_score >= 0.65

    return {
        "passed": overall_passed,
        "score": round(final_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation_error", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)
    
    workspace = sys.argv[1]
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))