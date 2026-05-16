import sys
import os
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    
    # ── Find the output file ───────────────────────────────────────────────
    # The task asks for a file named lidar_cost_analysis.md
    target_filename = "lidar_cost_analysis.md"
    found_files = list(Path(workspace_dir).rglob(target_filename))
    
    if not found_files:
        checks.append({
            "name": "output_file_exists",
            "passed": False,
            "detail": f"File '{target_filename}' not found anywhere in workspace."
        })
        return {"passed": False, "score": 0.0, "checks": checks}
    
    report_path = found_files[0]
    checks.append({
        "name": "output_file_exists",
        "passed": True,
        "detail": f"Found output file at: {report_path}"
    })
    
    # ── Read content ──────────────────────────────────────────────────────
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({
            "name": "file_readable",
            "passed": False,
            "detail": f"Could not read file: {e}"
        })
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({
        "name": "file_readable",
        "passed": True,
        "detail": f"File read successfully, length={len(content)} chars"
    })
    
    content_lower = content.lower()
    
    # ── Check 1: Must be a Markdown report with proper H1 title ───────────
    has_h1_report = bool(re.search(r'^#\s+第一性原理分析报告', content, re.MULTILINE))
    # Also accept English variant
    if not has_h1_report:
        has_h1_report = bool(re.search(r'^#\s+(first.?principle|第一性原理).*(report|分析报告)', content, re.MULTILINE | re.IGNORECASE))
    checks.append({
        "name": "markdown_report_title",
        "passed": has_h1_report,
        "detail": "Report must have a top-level H1 heading for the analysis report title."
    })
    
    # ── Check 2: Stage 1 — Problem classification section ─────────────────
    has_problem_classification = bool(
        re.search(r'##\s*(问题分类|问题.*分类|problem.*class|classification)', content, re.IGNORECASE | re.MULTILINE) or
        re.search(r'问题分类', content)
    )
    checks.append({
        "name": "stage1_problem_classification",
        "passed": has_problem_classification,
        "detail": "Stage 1: Must include a '问题分类' (problem classification) section identifying the problem type."
    })
    
    # ── Check 3: Stage 2 — Must identify AT LEAST 3 hidden assumptions ────
    # Look for assumption section
    has_assumption_section = bool(
        re.search(r'##\s*(识别的假设|隐含假设|假设识别|assumptions?)', content, re.IGNORECASE | re.MULTILINE)
    )
    
    # Count numbered assumptions (1. 2. 3. pattern) within assumption-related section
    assumption_section_match = re.search(
        r'(##\s*(?:识别的假设|隐含假设|假设识别|assumptions?).*?)(?=\n##|\Z)',
        content, re.DOTALL | re.IGNORECASE
    )
    assumption_count = 0
    if assumption_section_match:
        section_text = assumption_section_match.group(1)
        items = re.findall(r'^\s*\d+[\.\。]', section_text, re.MULTILINE)
        assumption_count = len(items)
    
    # Fallback: count 「assumption」markers globally with 「」quotes
    if assumption_count < 3:
        quoted_assumptions = re.findall(r'「[^」]{3,}」', content)
        assumption_count = max(assumption_count, len(quoted_assumptions))
    
    has_min_3_assumptions = has_assumption_section and assumption_count >= 3
    checks.append({
        "name": "stage2_min_3_assumptions_identified",
        "passed": has_min_3_assumptions,
        "detail": f"Stage 2: Must identify at least 3 hidden assumptions. Found section: {has_assumption_section}, counted: {assumption_count}"
    })
    
    # ── Check 4: Stage 2 — Each assumption must be questioned ─────────────
    has_questioning_section = bool(
        re.search(r'##\s*(假设质疑|质疑|questioning|challenge)', content, re.IGNORECASE | re.MULTILINE) or
        re.search(r'为什么.*假设|假设.*一定成立', content)
    )
    # Also check for "→" arrows indicating questioning results
    arrow_count = len(re.findall(r'→|->|⟶', content))
    has_questioning = has_questioning_section or arrow_count >= 3
    checks.append({
        "name": "stage2_assumptions_questioned",
        "passed": has_questioning,
        "detail": f"Stage 2: Each assumption must be questioned. Questioning section found: {has_questioning_section}, arrows (→) found: {arrow_count}"
    })
    
    # ── Check 5: Stage 3 — Must have 5-layer "why" decomposition ──────────
    # Look for 5 layers explicitly
    has_decomposition_section = bool(
        re.search(r'##\s*(逐层分解|分解到基本真理|层.*分解|decompos)', content, re.IGNORECASE | re.MULTILINE)
    )
    
    # Count "why" layers — look for patterns like "第1层", "第一层", "层1", numbered why questions
    layer_patterns = [
        r'第\s*[1-9一二三四五六七八九]\s*层',
        r'层\s*[1-9]',
        r'why\s*[1-9]',
        r'第\s*[1-9一二三四五六七八九]\s*个.*为什么',
    ]
    max_layer = 0
    for pat in layer_patterns:
        matches = re.findall(pat, content, re.IGNORECASE)
        if matches:
            # Try to extract the highest number
            for m in matches:
                nums = re.findall(r'[1-9]', m)
                chinese_map = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9}
                for ch, val in chinese_map.items():
                    if ch in m:
                        max_layer = max(max_layer, val)
                for n in nums:
                    max_layer = max(max_layer, int(n))
    
    # Also count occurrences of "为什么" questions in decomposition context
    why_count = len(re.findall(r'为什么', content))
    
    # A report needs either explicit 5-layer markers OR at least 5 "why" questions in decomposition
    has_5_layers = (max_layer >= 5) or (has_decomposition_section and why_count >= 5)
    checks.append({
        "name": "stage3_5layer_why_decomposition",
        "passed": has_5_layers,
        "detail": f"Stage 3: Must perform at least 5 layers of 'why' decomposition. Max layer found: {max_layer}, 为什么 count: {why_count}, has section: {has_decomposition_section}"
    })
    
    # ── Check 6: Stage 4 — Basic truth verification with 3 standards ──────
    verification_standards = [
        (r'不可再分', 'irreducible/不可再分'),
        (r'不证自明', 'self-evident/不证自明'),
        (r'独立于其他', 'independent/独立于其他命题'),
    ]
    standards_found = []
    for pattern, name in verification_standards:
        found = bool(re.search(pattern, content))
        standards_found.append((name, found))
    
    all_3_standards = all(f for _, f in standards_found)
    standards_detail = ", ".join(f"{n}: {'✓' if f else '✗'}" for n, f in standards_found)
    checks.append({
        "name": "stage4_basic_truth_verification_3_standards",
        "passed": all_3_standards,
        "detail": f"Stage 4: Must verify basic truths using all 3 standards (不可再分, 不证自明, 独立于其他命题). Found: {standards_detail}"
    })
    
    # ── Check 7: Stage 5 — At least 2 reconstructed solutions ─────────────
    has_solution_section = bool(
        re.search(r'##\s*(重构方案|创新方案|reconstructed|solution)', content, re.IGNORECASE | re.MULTILINE)
    )
    
    # Count solution A, B, C patterns
    solution_patterns = [
        r'方案\s*[ABC一二三αβγ]',
        r'[Ss]olution\s*[ABC123]',
        r'方案\s*[1-3]',
    ]
    solution_count = 0
    for pat in solution_patterns:
        matches = re.findall(pat, content)
        solution_count = max(solution_count, len(matches))
    
    has_min_2_solutions = has_solution_section and solution_count >= 2
    checks.append({
        "name": "stage5_min_2_reconstructed_solutions",
        "passed": has_min_2_solutions,
        "detail": f"Stage 5: Must derive at least 2 reconstructed solutions from first principles. Section found: {has_solution_section}, solutions counted: {solution_count}"
    })
    
    # ── Check 8: Stage 6 — Analogy comparison section ─────────────────────
    has_analogy_section = bool(
        re.search(r'##\s*(.*类比.*|.*对比.*|.*comparison.*|.*traditional.*)', content, re.IGNORECASE | re.MULTILINE)
    )
    has_traditional_mention = bool(re.search(r'传统(方案|方法|思维|做法)', content))
    has_innovation_mention = bool(re.search(r'(创新|差异|优势|innovation|advantage)', content, re.IGNORECASE))
    
    has_analogy_comparison = (has_analogy_section or has_traditional_mention) and has_innovation_mention
    checks.append({
        "name": "stage6_analogy_comparison",
        "passed": has_analogy_comparison,
        "detail": f"Stage 6: Must compare innovation solutions against traditional analogy-based solutions. Analogy section: {has_analogy_section}, traditional mention: {has_traditional_mention}, innovation mention: {has_innovation_mention}"
    })
    
    # ── Check 9: Domain relevance — must actually address LiDAR/sensor cost ──
    lidar_terms = ['lidar', 'laser', '激光', '传感器', 'sensor', 'cost', '成本', 'photon', '光', 'detector', 'autonomous', '自动驾驶']
    lidar_term_count = sum(1 for term in lidar_terms if term.lower() in content_lower)
    
    is_domain_relevant = lidar_term_count >= 4
    checks.append({
        "name": "domain_relevance_lidar_cost",
        "passed": is_domain_relevant,
        "detail": f"Report must address LiDAR/sensor cost analysis domain. Relevant terms found: {lidar_term_count}/required 4. Terms checked: {lidar_terms}"
    })
    
    # ── Check 10: Report is in Markdown with proper section structure ──────
    h2_sections = re.findall(r'^##\s+.+', content, re.MULTILINE)
    has_sufficient_structure = len(h2_sections) >= 4
    checks.append({
        "name": "stage7_structured_markdown_report",
        "passed": has_sufficient_structure,
        "detail": f"Stage 7: Report must be structured Markdown with at least 4 ## sections. Found {len(h2_sections)} sections: {[s.strip() for s in h2_sections[:8]]}"
    })
    
    # ── Scoring ────────────────────────────────────────────────────────────
    # Weight checks by importance
    weights = {
        "output_file_exists": 1,
        "file_readable": 1,
        "markdown_report_title": 1,
        "stage1_problem_classification": 1,
        "stage2_min_3_assumptions_identified": 2,
        "stage2_assumptions_questioned": 1,
        "stage3_5layer_why_decomposition": 2,
        "stage4_basic_truth_verification_3_standards": 2,
        "stage5_min_2_reconstructed_solutions": 2,
        "stage6_analogy_comparison": 1,
        "domain_relevance_lidar_cost": 1,
        "stage7_structured_markdown_report": 1,
    }
    
    total_weight = sum(weights.values())
    earned_weight = sum(weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights)
    score = round(earned_weight / total_weight, 4)
    
    # Must pass critical checks to pass overall
    critical_checks = [
        "output_file_exists",
        "stage2_min_3_assumptions_identified",
        "stage3_5layer_why_decomposition",
        "stage4_basic_truth_verification_3_standards",
        "stage5_min_2_reconstructed_solutions",
    ]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)
    overall_passed = critical_passed and score >= 0.70
    
    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))