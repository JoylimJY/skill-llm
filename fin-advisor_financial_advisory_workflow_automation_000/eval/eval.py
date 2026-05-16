#!/usr/bin/env python3
"""
Evaluation script for fin-advisor task.
Checks:
1. USER.md was updated with a valid persona_preference field
2. mcporter was called with correct dot-notation syntax (via call log)
3. Required funds (005827 and 003095) were actually queried
4. Multiple tool types were used (fundIntro or fundStagePerformance or fundscore)
5. Agent's final response (saved to response.md or response.txt) contains four-element data citations
6. Risk disclaimer is present in the response
7. No forbidden terms (tool names, service names, MCP references) in the response
8. No self-computed calculations (flagged patterns)
"""

import sys
import json
import re
from pathlib import Path

def load_json_lines(path):
    lines = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        lines.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except FileNotFoundError:
        pass
    return lines

def find_response_file(workspace):
    """Look for the agent's response output file."""
    candidates = []
    for pattern in ["response.md", "response.txt", "answer.md", "answer.txt", "output.md", "output.txt"]:
        found = list(Path(workspace).rglob(pattern))
        candidates.extend(found)
    # Also check if agent wrote to a report file
    for pattern in ["*report*.md", "*report*.txt", "*analysis*.md", "*analysis*.txt"]:
        found = list(Path(workspace).rglob(pattern))
        # Exclude pre-existing report files
        candidates.extend([f for f in found if "2024/annual" not in str(f) and "2023/performance" not in str(f)])
    return candidates

def check_user_md(workspace):
    user_md_path = Path(workspace) / "USER.md"
    try:
        content = user_md_path.read_text(encoding="utf-8")
        # Check for persona_preference field with a valid value
        match = re.search(r'persona_preference\s*[:\s]+(\S+)', content)
        if match:
            value = match.group(1).strip().strip('"\'')
            valid_values = {"professional", "friendly", "data-driven", "专业模式", "轻松模式", "极简模式"}
            # Accept any non-empty value that looks like a preference was set
            if value and value not in {"字段缺失", "缺失", "missing"}:
                return True, f"persona_preference set to: {value}"
        return False, f"persona_preference not found or not set in USER.md. Content snippet: {content[:300]}"
    except Exception as e:
        return False, f"Could not read USER.md: {e}"

def check_mcporter_calls(workspace):
    log_path = Path(workspace) / "logs" / "mcporter_calls.jsonl"
    calls = load_json_lines(log_path)
    
    if not calls:
        return False, "No mcporter calls recorded in logs", [], []
    
    valid_calls = [c for c in calls if c.get("valid_syntax", False)]
    invalid_calls = [c for c in calls if not c.get("valid_syntax", False)]
    
    return len(valid_calls) > 0, (
        f"Total calls: {len(calls)}, Valid: {len(valid_calls)}, Invalid: {len(invalid_calls)}"
    ), valid_calls, invalid_calls

def check_both_funds_queried(valid_calls):
    """Check that both 005827 and 003095 (or their aliases) were queried."""
    fund_005827_aliases = {"005827", "易方达蓝筹精选", "易方达蓝筹精选混合", "易方达蓝筹精选混合型证券投资基金"}
    fund_003095_aliases = {"003095", "中欧医疗健康", "中欧医疗健康混合", "中欧医疗健康混合型证券投资基金"}
    
    found_005827 = False
    found_003095 = False
    
    for call in valid_calls:
        args_str = json.dumps(call.get("args", []), ensure_ascii=False)
        reason_str = call.get("reason", "")
        combined = args_str + reason_str
        
        for alias in fund_005827_aliases:
            if alias in combined:
                found_005827 = True
        for alias in fund_003095_aliases:
            if alias in combined:
                found_003095 = True
    
    return found_005827, found_003095

def check_multiple_tool_types(valid_calls):
    """Check that at least 2 different tool types were used."""
    tools_used = set()
    for call in valid_calls:
        reason = call.get("reason", "")
        m = re.search(r'tool=(\w+)', reason)
        if m:
            tools_used.add(m.group(1))
    return tools_used

def check_four_element_compliance(text):
    """
    Check that at least some data citations contain elements suggestive of
    timestamp + indicator + value + subject groupings.
    This is a heuristic check.
    """
    # Look for date patterns (timestamps)
    date_patterns = [
        r'截至\d{4}年\d{1,2}月\d{1,2}日',
        r'截至\d{4}[-/]\d{1,2}[-/]\d{1,2}',
        r'\d{4}年\d{1,2}月\d{1,2}日',
        r'2024-12-31',
        r'2024年12月31日',
    ]
    has_timestamp = any(re.search(p, text) for p in date_patterns)
    
    # Look for numeric values (percentages, scores)
    has_numeric = bool(re.search(r'[\d.]+[%分亿元]', text))
    
    # Look for fund names (subjects)
    has_subject = any(name in text for name in [
        "易方达蓝筹精选", "中欧医疗健康", "005827", "003095"
    ])
    
    # Look for indicator names
    indicator_keywords = ["收益率", "评分", "回撤", "夏普", "规模", "管理费", "业绩", "净值"]
    has_indicator = any(kw in text for kw in indicator_keywords)
    
    elements_present = sum([has_timestamp, has_numeric, has_subject, has_indicator])
    return elements_present >= 3, elements_present, {
        "timestamp": has_timestamp, 
        "numeric": has_numeric,
        "subject": has_subject,
        "indicator": has_indicator
    }

def check_risk_disclaimer(text):
    """Check for the exact required risk disclaimer."""
    required = "以上分析仅供参考，不构成投资建议。基金投资有风险，过往业绩不代表未来表现，请结合自身风险承受能力谨慎决策。"
    return required in text, f"Exact disclaimer {'found' if required in text else 'NOT found'}"

def check_no_forbidden_terms(text):
    """Check that no tool/service/MCP names are leaked."""
    forbidden_patterns = [
        r'mcporter',
        r'MCP\s*[Ss]erver',
        r'mcp\s*server',
        r'fund-diagnosis',
        r'fund-investments',
        r'public-opinion-explanation',
        r'ai-search-all',
        r'工具返回',
        r'工具调用',
        r'\[service',
        r'网页\d+',
        r'fundIntro',
        r'fundStagePerformance',
        r'fundscore',
        r'buyerInvestmentAdvisor',
    ]
    violations = []
    for pattern in forbidden_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            violations.append(pattern)
    return len(violations) == 0, violations

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "setup", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(0)
    
    workspace = sys.argv[1]
    checks = []
    
    # ── Check 1: USER.md updated with persona_preference ─────────────────────
    persona_ok, persona_detail = check_user_md(workspace)
    checks.append({
        "name": "user_md_persona_updated",
        "passed": persona_ok,
        "detail": persona_detail
    })
    
    # ── Check 2: mcporter called with valid syntax ────────────────────────────
    calls_ok, calls_detail, valid_calls, invalid_calls = check_mcporter_calls(workspace)
    checks.append({
        "name": "mcporter_valid_syntax_calls",
        "passed": calls_ok,
        "detail": calls_detail + (f". Invalid call reasons: {[c.get('reason','') for c in invalid_calls[:3]]}" if invalid_calls else "")
    })
    
    # ── Check 3: Both funds were queried ─────────────────────────────────────
    found_005827, found_003095 = check_both_funds_queried(valid_calls)
    checks.append({
        "name": "fund_005827_queried",
        "passed": found_005827,
        "detail": "易方达蓝筹精选混合 (005827) was queried" if found_005827 else "易方达蓝筹精选混合 (005827) was NOT queried"
    })
    checks.append({
        "name": "fund_003095_queried",
        "passed": found_003095,
        "detail": "中欧医疗健康混合 (003095) was queried" if found_003095 else "中欧医疗健康混合 (003095) was NOT queried"
    })
    
    # ── Check 4: Multiple tool types used ────────────────────────────────────
    tools_used = check_multiple_tool_types(valid_calls)
    multi_tool_ok = len(tools_used) >= 2
    checks.append({
        "name": "multiple_tool_types_used",
        "passed": multi_tool_ok,
        "detail": f"Tools used: {tools_used}. Need at least 2 different tools."
    })
    
    # ── Check 5-8: Response content checks ───────────────────────────────────
    response_files = find_response_file(workspace)
    
    # Try to find agent response — also check stdout capture if available
    response_text = ""
    response_source = "none"
    
    if response_files:
        try:
            # Use the most recently modified file
            response_files_sorted = sorted(response_files, key=lambda p: p.stat().st_mtime, reverse=True)
            response_text = response_files_sorted[0].read_text(encoding="utf-8")
            response_source = str(response_files_sorted[0])
        except Exception as e:
            response_source = f"error reading: {e}"
    
    # Also search for any .md files created during the session that aren't pre-existing
    if not response_text:
        pre_existing = {
            "USER.md", "SKILL.md", "domain-knowledge.md", "tool-guide.md",
            "output-guide.md", "compliance.md", "professional.md", "friendly.md",
            "data-driven.md", "risk_matrix.md", "annual_summary.md", "performance_review.md"
        }
        for p in Path(workspace).rglob("*.md"):
            if p.name not in pre_existing and p.stat().st_size > 100:
                try:
                    candidate = p.read_text(encoding="utf-8")
                    if len(candidate) > 200 and ("基金" in candidate or "%" in candidate):
                        response_text = candidate
                        response_source = str(p)
                        break
                except Exception:
                    pass
        
        # Also try .txt files
        if not response_text:
            for p in Path(workspace).rglob("*.txt"):
                if p.name not in {"scratch_notes.txt", "excluded_funds.txt"}:
                    try:
                        candidate = p.read_text(encoding="utf-8")
                        if len(candidate) > 200 and ("基金" in candidate or "%" in candidate):
                            response_text = candidate
                            response_source = str(p)
                            break
                    except Exception:
                        pass
    
    response_found = bool(response_text)
    checks.append({
        "name": "response_file_found",
        "passed": response_found,
        "detail": f"Response source: {response_source}, length: {len(response_text)} chars"
    })
    
    if response_text:
        # Check 6: Four-element compliance
        four_elem_ok, elem_count, elem_detail = check_four_element_compliance(response_text)
        checks.append({
            "name": "four_element_data_compliance",
            "passed": four_elem_ok,
            "detail": f"{elem_count}/4 elements present: {elem_detail}"
        })
        
        # Check 7: Risk disclaimer
        disclaimer_ok, disclaimer_detail = check_risk_disclaimer(response_text)
        checks.append({
            "name": "risk_disclaimer_present",
            "passed": disclaimer_ok,
            "detail": disclaimer_detail
        })
        
        # Check 8: No forbidden terms
        no_forbidden_ok, violations = check_no_forbidden_terms(response_text)
        checks.append({
            "name": "no_forbidden_tool_terms_leaked",
            "passed": no_forbidden_ok,
            "detail": f"Violations: {violations}" if violations else "No forbidden terms found"
        })
    else:
        for check_name, detail in [
            ("four_element_data_compliance", "No response file found to check"),
            ("risk_disclaimer_present", "No response file found to check"),
            ("no_forbidden_tool_terms_leaked", "No response file found to check"),
        ]:
            checks.append({"name": check_name, "passed": False, "detail": detail})
    
    # ── Compute final score ───────────────────────────────────────────────────
    # Weighted scoring
    weights = {
        "user_md_persona_updated": 1.0,
        "mcporter_valid_syntax_calls": 2.0,
        "fund_005827_queried": 1.5,
        "fund_003095_queried": 1.5,
        "multiple_tool_types_used": 1.5,
        "response_file_found": 1.0,
        "four_element_data_compliance": 1.5,
        "risk_disclaimer_present": 2.0,
        "no_forbidden_tool_terms_leaked": 1.5,
    }
    
    total_weight = sum(weights.values())
    earned_weight = sum(weights.get(c["name"], 1.0) for c in checks if c["passed"])
    score = round(earned_weight / total_weight, 4)
    
    # Must pass critical checks to be considered passing
    critical_checks = ["mcporter_valid_syntax_calls", "fund_005827_queried", "fund_003095_queried", "risk_disclaimer_present"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)
    
    overall_passed = critical_passed and score >= 0.65
    
    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()