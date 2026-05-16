import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0
    weights = {}

    # --- Locate the output file ---
    candidates = list(workspace.rglob("financial_analyst_oaisr_report.txt"))

    def check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return passed, weight

    if not candidates:
        checks.append({"name": "file_exists", "passed": False, "detail": "financial_analyst_oaisr_report.txt not found anywhere in workspace."})
        return {"passed": False, "score": 0.0, "checks": checks}

    report_path = candidates[0]
    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {report_path}"})

    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "file_readable", "passed": True, "detail": f"File length: {len(content)} chars"})

    # ---- CHECK 1: Dual Progress Bars ----
    # Must have bracket-enclosed blocks: [█...░...] pattern
    # Must appear twice (theoretical and actual)
    bar_pattern = re.compile(r'\[([█░]+)\]')
    bar_matches = bar_pattern.findall(content)
    has_two_bars = len(bar_matches) >= 2
    checks.append({
        "name": "dual_progress_bars_format",
        "passed": has_two_bars,
        "detail": f"Found {len(bar_matches)} bracket-enclosed block bar(s). Need >= 2. Bars: {bar_matches[:5]}"
    })

    # Must use filled block █ and empty block ░ characters
    uses_filled_block = '█' in content
    uses_empty_block = '░' in content
    checks.append({
        "name": "progress_bar_uses_block_chars",
        "passed": uses_filled_block and uses_empty_block,
        "detail": f"Uses filled block (█): {uses_filled_block}, uses empty block (░): {uses_empty_block}"
    })

    # ---- CHECK 2: No emoji ----
    # Detect common emoji ranges
    emoji_pattern = re.compile(
        u"[\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u2640-\u2642"
        u"\u2600-\u2B55"
        u"\u200d\u23cf\u23e9\u231a\ufe0f\u3030]+",
        flags=re.UNICODE
    )
    emoji_matches = emoji_pattern.findall(content)
    no_emoji = len(emoji_matches) == 0
    checks.append({
        "name": "no_emoji",
        "passed": no_emoji,
        "detail": f"Emoji found: {emoji_matches[:5]}" if not no_emoji else "No emoji detected."
    })

    # ---- CHECK 3: Theoretical exposure value (0.xx) present near bar ----
    # Numbers like 0.XX must appear as exposure values
    exposure_values = re.findall(r'\b0\.\d{2}\b', content)
    has_exposure_values = len(exposure_values) >= 2
    checks.append({
        "name": "exposure_values_present",
        "passed": has_exposure_values,
        "detail": f"Found {len(exposure_values)} 0.XX values: {exposure_values[:6]}"
    })

    # ---- CHECK 4: Task breakdown table (6-8 rows) ----
    # Look for markdown table rows: lines with multiple | separators
    table_rows = [line for line in content.splitlines() if line.count('|') >= 3]
    # Exclude header and separator rows
    data_rows = [r for r in table_rows if not re.match(r'^[\s|:\-]+$', r) and '---' not in r]
    # Header row likely contains column names — exclude it
    data_rows_excl_header = [r for r in data_rows if not any(kw in r for kw in ['任务名称', 'Task', '理论值', 'Theoretical', '实际值'])]
    row_count = len(data_rows_excl_header)
    has_proper_table = 6 <= row_count <= 8
    checks.append({
        "name": "task_breakdown_table_6_to_8_rows",
        "passed": has_proper_table,
        "detail": f"Found {row_count} non-header table data rows (need 6-8). Rows: {data_rows_excl_header[:3]}"
    })

    # ---- CHECK 5: β values in table ----
    beta_pattern = re.compile(r'β\s*=\s*0\.\d{2}')
    beta_matches = beta_pattern.findall(content)
    has_beta_values = len(beta_matches) >= 4
    checks.append({
        "name": "beta_values_in_table",
        "passed": has_beta_values,
        "detail": f"Found {len(beta_matches)} β=0.xx values: {beta_matches[:6]}"
    })

    # ---- CHECK 6: Estimation basis cited in table ----
    # Each row should have a basis. Check for at least 4 occurrences of basis keywords
    basis_keywords = ['报告原文', '类比推断', '经验系数', 'analogy', 'coefficient', 'inference', 'report', '估算']
    basis_found = sum(1 for kw in basis_keywords if kw in content)
    has_basis_citations = basis_found >= 2
    checks.append({
        "name": "estimation_basis_cited",
        "passed": has_basis_citations,
        "detail": f"Basis keyword matches: {basis_found} out of {len(basis_keywords)} keywords checked."
    })

    # ---- CHECK 7: Comprehensive Estimate section ----
    # Must contain weighted exposure mention and confidence level
    has_weighted = bool(re.search(r'(加权|[Ww]eighted)', content))
    has_confidence = bool(re.search(r'(置信度|[Cc]onfidence|高|中|低|High|Medium|Low)', content))
    has_key_conclusion = bool(re.search(r'(核心结论|[Kk]ey [Cc]onclusion|[Cc]onclusion)', content))
    comprehensive_ok = has_weighted and has_confidence and has_key_conclusion
    checks.append({
        "name": "comprehensive_estimate_section",
        "passed": comprehensive_ok,
        "detail": f"weighted={has_weighted}, confidence={has_confidence}, key_conclusion={has_key_conclusion}"
    })

    # ---- CHECK 8: Data gap handling (theory × 0.5~0.6) ----
    # The skill requires: "No actual data → theory × 0.5-0.6 experience coefficient"
    # Check for coefficient or the pattern indicating gap handling
    gap_handling_pattern = re.compile(r'(0\.5[0-9]?|×\s*0\.5|×\s*0\.6|经验系数|experience coefficient|×0\.5|×0\.6|0\.5~0\.6|\*\s*0\.5|\*\s*0\.6)')
    gap_matches = gap_handling_pattern.findall(content)
    has_gap_handling = len(gap_matches) >= 1
    checks.append({
        "name": "data_gap_handling_coefficient",
        "passed": has_gap_handling,
        "detail": f"Gap handling coefficient references: {gap_matches[:4]}"
    })

    # ---- CHECK 9: Coping Strategies section ----
    # Survey explicitly requested include_strategies=true and the config says so
    has_coping = bool(re.search(r'(AI不可替代|[Cc]oping [Ss]trateg|应对策略|irreplaceable|不可替代能力)', content))
    checks.append({
        "name": "coping_strategies_section",
        "passed": has_coping,
        "detail": f"Coping strategies section found: {has_coping}"
    })

    # ---- CHECK 10: Role is Financial Analyst (correct target identified) ----
    has_correct_role = bool(re.search(r'(Financial Analyst|金融分析师|财务分析师)', content, re.IGNORECASE))
    checks.append({
        "name": "correct_role_financial_analyst",
        "passed": has_correct_role,
        "detail": f"'Financial Analyst' or '金融分析师' found in report: {has_correct_role}"
    })

    # ---- CHECK 11: Key insight (AI replaces tasks, not occupations) ----
    has_key_insight = bool(re.search(
        r'(AI替代任务|replaces tasks|替代任务|not occupation|非职业|tasks.*not.*occupation|任务.*非职业)',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "key_insight_tasks_not_occupations",
        "passed": has_key_insight,
        "detail": f"Key insight 'AI replaces tasks, not occupations' found: {has_key_insight}"
    })

    # ---- CHECK 12: Progress bars have numeric values on right ----
    # Pattern: bar followed by space and 0.XX
    bar_with_value = re.compile(r'\[[█░]+\]\s+0\.\d{2}')
    bar_value_matches = bar_with_value.findall(content)
    has_bar_values = len(bar_value_matches) >= 2
    checks.append({
        "name": "progress_bars_have_numeric_labels",
        "passed": has_bar_values,
        "detail": f"Bars with numeric value on right: {len(bar_value_matches)}. Matches: {bar_value_matches}"
    })

    # ---- SCORING ----
    critical_checks = [
        "file_exists",
        "dual_progress_bars_format",
        "progress_bar_uses_block_chars",
        "no_emoji",
        "task_breakdown_table_6_to_8_rows",
        "beta_values_in_table",
        "correct_role_financial_analyst",
    ]
    weighted_checks = {
        "file_exists": 1.0,
        "file_readable": 0.5,
        "dual_progress_bars_format": 1.5,
        "progress_bar_uses_block_chars": 1.5,
        "no_emoji": 1.0,
        "exposure_values_present": 1.0,
        "task_breakdown_table_6_to_8_rows": 2.0,
        "beta_values_in_table": 1.5,
        "estimation_basis_cited": 1.0,
        "comprehensive_estimate_section": 1.5,
        "data_gap_handling_coefficient": 1.0,
        "coping_strategies_section": 1.0,
        "correct_role_financial_analyst": 1.0,
        "key_insight_tasks_not_occupations": 0.5,
        "progress_bars_have_numeric_labels": 1.0,
    }

    total_weight = sum(weighted_checks.values())
    earned = 0.0
    for c in checks:
        if c["passed"] and c["name"] in weighted_checks:
            earned += weighted_checks[c["name"]]

    score = round(earned / total_weight, 4)

    # Must pass all critical checks to pass overall
    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == name), False)
        for name in critical_checks
    )
    passed = critical_passed and score >= 0.70

    return {"passed": passed, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))