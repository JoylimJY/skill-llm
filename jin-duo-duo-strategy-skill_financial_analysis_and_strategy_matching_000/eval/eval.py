#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evaluation script for jin-duo-duo strategy task.
Usage: python eval_script.py <workspace_dir>
"""

import sys
import json
import re
from pathlib import Path

def load_json_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    return json.loads(content)

def find_report_file(workspace: Path):
    """Search for analysis_report.json anywhere in workspace."""
    candidates = list(workspace.rglob('analysis_report.json'))
    if not candidates:
        return None
    # Prefer root-level or reports/ directory
    for c in candidates:
        if c.parent == workspace or 'report' in str(c.parent).lower():
            return c
    return candidates[0]

def check_strategy_identification(report: dict) -> tuple:
    """
    Check that the report correctly identifies Strategy 4 (减仓信号) as the winning strategy.
    Priority rule: sell > buy, so Strategy 4 must win over Strategy 2.
    """
    content_str = json.dumps(report, ensure_ascii=False).lower()
    
    # Check for strategy 4 indicators in Chinese
    strategy4_keywords = ['策略四', '减仓', '分批减仓', 'strategy4', 'strategy 4', '4']
    strategy4_present = any(kw.lower() in json.dumps(report, ensure_ascii=False) for kw in ['策略四', '减仓信号', '分批减仓'])
    
    # Check it does NOT incorrectly recommend Strategy 1 (强势买入) as primary
    strategy1_as_primary = False
    # Check top-level strategy fields
    for key in ['strategy', 'strategy_name', 'matched_strategy', 'recommended_strategy', 
                '策略', '推荐策略', '匹配策略', 'result', 'recommendation']:
        val = report.get(key, '')
        if isinstance(val, str) and ('策略一' in val or '强势买入' in val or '满仓推进' in val):
            strategy1_as_primary = True
            break
    
    return strategy4_present, strategy1_as_primary

def run_evaluation(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ─── CHECK 1: Report file exists ───
    report_path = find_report_file(workspace)
    file_exists = report_path is not None
    checks.append({
        "name": "analysis_report.json exists",
        "passed": file_exists,
        "detail": f"Found at: {report_path}" if file_exists else "File analysis_report.json not found anywhere in workspace"
    })
    if not file_exists:
        return {"passed": False, "score": 0.0, "checks": checks}

    # ─── CHECK 2: Report is valid JSON ───
    try:
        report = load_json_file(report_path)
        checks.append({
            "name": "Report is valid JSON",
            "passed": True,
            "detail": f"Parsed successfully from {report_path}"
        })
    except Exception as e:
        checks.append({
            "name": "Report is valid JSON",
            "passed": False,
            "detail": f"JSON parse error: {e}"
        })
        return {"passed": False, "score": 0.05, "checks": checks}

    report_str = json.dumps(report, ensure_ascii=False)

    # ─── CHECK 3: Technical indicators script was used ───
    # The report should contain data that could only come from running the script
    # (MA values, MACD values, or references to computed indicators)
    indicator_keywords = ['MA5', 'MA10', 'MA20', 'MACD', 'DIF', 'DEA', 'volume', 
                         '均线', 'macd', 'ma5', 'ma20', '成交量', '技术指标']
    has_indicator_data = any(kw in report_str for kw in indicator_keywords)
    checks.append({
        "name": "Report references technical indicators from script output",
        "passed": has_indicator_data,
        "detail": "Found indicator keywords in report" if has_indicator_data else 
                  "No technical indicator data found — agent may not have used the script"
    })

    # ─── CHECK 4: Correct strategy identified (Strategy 4 wins) ───
    strategy4_present, strategy1_primary = check_strategy_identification(report)
    
    # Strong check: "策略四" or "减仓" must appear
    checks.append({
        "name": "Correctly identifies Strategy 4 (减仓信号) as primary recommendation",
        "passed": strategy4_present,
        "detail": "Found '策略四' / '减仓信号' / '分批减仓' in report" if strategy4_present else 
                  "Missing Strategy 4 identification — agent may have incorrectly picked a buy strategy"
    })

    # ─── CHECK 5: Sell-over-buy priority rule applied ───
    # Strategy 2 (回踩买入) signals should be present but overridden
    has_strategy2_mention = any(kw in report_str for kw in ['策略二', '回踩', '分批建仓'])
    # Either explicitly mentioned as secondary/overridden, or just strategy 4 is the final answer
    priority_rule_applied = strategy4_present  # if strategy 4 is chosen, priority was applied
    
    # Bonus: explicitly mentions the conflict/priority
    mentions_priority = any(kw in report_str for kw in 
                           ['卖出', '优先', '优先级', 'sell', 'priority', '卖出信号优先'])
    
    checks.append({
        "name": "Sell-over-buy priority rule correctly applied (sell overrides buy)",
        "passed": priority_rule_applied and not strategy1_primary,
        "detail": (f"Strategy 4 selected as primary (sell>buy rule applied). "
                   f"Strategy 2 mentioned: {has_strategy2_mention}. "
                   f"Priority rule explicitly mentioned: {mentions_priority}")
                   if priority_rule_applied else 
                   "Strategy 4 not selected — sell-over-buy priority rule was not applied"
    })

    # ─── CHECK 6: Strategy 4 score ≥ 50 referenced or stated ───
    # Check if a score is mentioned that is ≥ 50 for strategy 4 or overall
    score_pattern = re.findall(r'(\d{2,3})\s*分?', report_str)
    valid_scores = [int(s) for s in score_pattern if 50 <= int(s) <= 100]
    has_valid_score = len(valid_scores) > 0
    
    checks.append({
        "name": "Report contains a valid score (≥50) consistent with Strategy 4 threshold",
        "passed": has_valid_score,
        "detail": f"Found scores: {valid_scores[:5]}" if has_valid_score else 
                  "No valid score (50-100) found in report"
    })

    # ─── CHECK 7: MACD-related signals mentioned ───
    macd_signal_keywords = ['顶背离', 'MACD顶背离', 'macd顶背离', '死叉', 'MACD死叉', 
                            'top_divergence', 'death_cross', 'DIF下穿DEA', '背离']
    has_macd_signal = any(kw in report_str for kw in macd_signal_keywords)
    checks.append({
        "name": "MACD top divergence or death cross identified as key signal",
        "passed": has_macd_signal,
        "detail": "Found MACD divergence/death cross mention" if has_macd_signal else 
                  "Missing MACD top divergence or death cross — key Strategy 4 trigger not mentioned"
    })

    # ─── CHECK 8: Report contains operation advice ───
    operation_keywords = ['减仓', '分批减仓', '止损', '锁定利润', '操作建议', '建议', 
                         '仓位', 'reduce', 'sell', '卖出']
    has_operation = any(kw in report_str for kw in operation_keywords)
    checks.append({
        "name": "Report contains operation advice/recommendation",
        "passed": has_operation,
        "detail": "Found operation advice keywords" if has_operation else 
                  "No operation advice found in report"
    })

    # ─── CHECK 9: Risk warning present ───
    risk_keywords = ['风险', '止损', 'risk', '注意', '可能', '回调', '谨慎', 'warning']
    has_risk = any(kw in report_str for kw in risk_keywords)
    checks.append({
        "name": "Report contains risk warning",
        "passed": has_risk,
        "detail": "Found risk warning keywords" if has_risk else 
                  "No risk warning found — required by strategy guide"
    })

    # ─── CHECK 10: Strategy 5 NOT incorrectly chosen over Strategy 4 ───
    # Strategy 5 needs score ≥ 60. In our data, MA arrangement is not fully bearish,
    # so Strategy 5 should NOT trigger as primary.
    # If Strategy 5 is chosen as primary, it's likely an error (unless the agent 
    # can justify it with the data — we accept both 4 and 5 if justified with score)
    strategy5_primary = any(kw in report_str for kw in ['策略五', '清仓信号', '立即清仓'])
    
    # Accept Strategy 5 as well if it has valid reasoning — the key constraint is
    # that Strategy 1/2/3 should NOT be the primary recommendation
    buy_strategy_primary = any(kw in report_str for kw in 
                               ['策略一·', '策略二·', '策略三·',
                                '强势买入（满仓推进）', '回踩买入（分批建仓）', '突破买入（突破确认）'])
    
    # More specific check: if the FINAL recommendation is a buy strategy
    final_rec_is_buy = False
    for key in ['final_recommendation', 'recommendation', 'strategy', 'matched_strategy',
                '最终推荐', '推荐策略', '匹配策略']:
        val = report.get(key, '')
        if isinstance(val, str):
            if any(kw in val for kw in ['策略一', '策略二', '策略三', '满仓推进', '分批建仓', '突破确认']):
                final_rec_is_buy = True
                break

    sell_strategy_correct = strategy4_present or strategy5_primary
    checks.append({
        "name": "Final recommendation is a SELL strategy (not a BUY strategy)",
        "passed": sell_strategy_correct and not final_rec_is_buy,
        "detail": (f"Correct: sell strategy found (Strategy4: {strategy4_present}, Strategy5: {strategy5_primary}). "
                   f"Final rec is buy: {final_rec_is_buy}")
    })

    # ─── Compute final score ───
    passed_checks = [c for c in checks if c["passed"]]
    n_checks = len(checks)
    n_passed = len(passed_checks)

    # Weighted scoring: critical checks get more weight
    weights = {
        0: 0.05,   # file exists
        1: 0.05,   # valid JSON
        2: 0.10,   # used indicators
        3: 0.20,   # strategy 4 identified (critical)
        4: 0.20,   # sell > buy priority (critical)
        5: 0.08,   # valid score
        6: 0.12,   # MACD signals
        7: 0.08,   # operation advice
        8: 0.05,   # risk warning
        9: 0.07,   # not a buy strategy
    }
    
    total_score = sum(weights[i] for i, c in enumerate(checks) if c["passed"])
    overall_passed = (
        checks[0]["passed"] and   # file exists
        checks[1]["passed"] and   # valid JSON
        checks[3]["passed"] and   # strategy 4 identified
        checks[4]["passed"] and   # priority rule
        checks[9]["passed"]       # not a buy strategy
    )

    return {
        "passed": overall_passed,
        "score": round(total_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, 
                          "checks": [{"name": "invocation", "passed": False, 
                                      "detail": "No workspace dir provided"}]}))
        sys.exit(1)
    
    result = run_evaluation(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))