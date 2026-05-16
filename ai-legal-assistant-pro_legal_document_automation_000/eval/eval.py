#!/usr/bin/env python3
"""
Evaluation script for AI Legal Assistant task.
Checks that the agent produced a correct, multi-section legal analysis report.
"""
import sys
import json
import re
from pathlib import Path

def find_report(workspace: Path):
    """Find the legal_analysis_report.md file anywhere in the workspace."""
    candidates = list(workspace.rglob("legal_analysis_report.md"))
    if candidates:
        return candidates[0]
    return None

def check_contract_risk_scan(content: str) -> tuple[bool, str]:
    """
    Check that contract risk scan section is present and correct.
    Must identify at least 3 high-risk items with proper 高/中/低 classification.
    """
    details = []
    
    # Check for risk table presence (must have 高/中/低 classification)
    has_high = "高" in content and ("风险" in content or "risk" in content.lower())
    has_risk_table = bool(re.search(r'[高中低]\s*[风险]|风险.*[高中低]|[高中低].*风险', content))
    
    if not has_risk_table:
        return False, "未找到使用'高/中/低'风险级别的风险分类"
    
    # Count high-risk mentions
    high_risk_count = len(re.findall(r'高\s*风险|风险.*高|高[^\n]{0,10}风险', content))
    
    # Check for specific known high-risk issues from the contract
    risk_checks = {
        "单方调岗/变更": bool(re.search(r'单方[^\n]{0,20}(调[岗位]|变更|调整)', content)),
        "竞业限制补偿不足": bool(re.search(r'竞业[^\n]{0,30}(补偿|1000|不足|过低|违规)', content)),
        "加班费包含月薪违规": bool(re.search(r'加班[^\n]{0,30}(月薪|包含|违|违法)', content)),
        "仲裁终局排除诉讼权": bool(re.search(r'(仲裁|终局)[^\n]{0,20}(诉|起诉|法院|违法|不当)', content)),
    }
    
    found_risks = sum(1 for v in risk_checks.values() if v)
    
    if found_risks < 2:
        return False, f"合同风险识别不足（仅识别出 {found_risks}/4 个关键风险点）: {risk_checks}"
    
    # Check contract type is mentioned
    has_contract_type = bool(re.search(r'劳动合同|劳务合同|雇佣合同', content))
    if not has_contract_type:
        return False, "未标注合同类型"
    
    return True, f"合同风险扫描通过: 识别出 {found_risks}/4 个关键风险, 风险等级分类正确"

def check_compensation_calculation(content: str) -> tuple[bool, str]:
    """
    Check that compensation calculation is present and mathematically correct.
    - 月均工资: 22,000元
    - 工作年限: 2021年3月15日 至 2024年1月10日 = 约2年10个月 → 按3年计
    - 末位淘汰 = 违法解除 → 2N
    - 未提前通知 → 代通知金1个月
    - N = 22000 * 3 = 66000
    - 2N = 132000
    - 代通知金 = 22000 (可并入2N争议，但常见为2N不重复)
    - 实际：违法解除适用2N，2N = 132000；+1个月代通知金22000（有争议）
    - 最终区间: ~132000 至 154000 元
    """
    details = []
    
    # Check that N calculation (66000) or 2N (132000) is present
    has_n_calc = bool(re.search(r'6[56]\s*[,，]?\s*000|6[56]000', content))
    has_2n_calc = bool(re.search(r'13[12]\s*[,，]?\s*000|13[12]000', content))
    
    # Check for illegal termination / 2N determination
    has_2n_rule = bool(re.search(r'(末位淘汰|违法解除)[^\n]{0,50}(2N|赔偿金|两倍)', content) or
                       re.search(r'2N|赔偿金[^\n]{0,30}(13|违法)', content))
    
    # Check for representative amount (anything in range 110000-160000)
    amounts_found = re.findall(r'(\d{5,7})', content.replace(',', '').replace('，', ''))
    numeric_amounts = [int(x) for x in amounts_found if 100000 <= int(x) <= 200000]
    
    has_reasonable_amount = len(numeric_amounts) > 0
    
    # Check calculation steps are present
    has_calc_steps = bool(re.search(r'(N\s*=|计算步骤|计算依据|工作年限)', content))
    
    # Check lawsuit fee calculation was done (script invocation)
    # The script output format: 预估诉讼费：XXX.XX 元
    has_lawsuit_fee = bool(re.search(r'(诉讼费|起诉费)[^\n]{0,30}[\d,，]+\s*元', content) or
                           re.search(r'预估诉讼费', content))
    
    issues = []
    if not (has_n_calc or has_2n_calc):
        issues.append("未找到N或2N的具体计算数值")
    if not has_2n_rule:
        issues.append("未明确指出末位淘汰违法解除→适用2N")
    if not has_reasonable_amount:
        issues.append("未给出合理的赔偿金额范围(10万-20万区间)")
    if not has_calc_steps:
        issues.append("未包含计算步骤")
    if not has_lawsuit_fee:
        issues.append("未包含诉讼费估算")
    
    if issues:
        return False, "赔偿计算问题: " + "; ".join(issues)
    
    return True, f"赔偿计算通过: 找到合理金额范围, 计算步骤存在, 2N规则识别正确, 诉讼费估算存在"

def check_complaint_skeleton(content: str) -> tuple[bool, str]:
    """
    Check that a proper complaint skeleton (起诉状骨架) is present.
    Must have: 诉讼请求, 事实与理由, 证据清单, 缺失事实清单
    """
    required_sections = {
        "诉讼请求": bool(re.search(r'诉讼请求', content)),
        "事实与理由": bool(re.search(r'事实与理由|事实和理由', content)),
        "证据清单": bool(re.search(r'证据清单|证据列表', content)),
        "原告/被告信息": bool(re.search(r'(原告|被告)[：:]\s*(陈|北京|飞速)', content)),
    }
    
    missing = [k for k, v in required_sections.items() if not v]
    
    if missing:
        return False, f"起诉状骨架缺少以下部分: {missing}"
    
    # Check evidence list has at least 2 items
    evidence_items = re.findall(r'劳动合同|工资流水|银行流水|解除通知|仲裁|录音|邮件|社保', content)
    if len(set(evidence_items)) < 2:
        return False, f"证据清单内容不足（仅找到: {set(evidence_items)}）"
    
    # Check for missing facts list
    has_missing_facts = bool(re.search(r'(缺失|需补充|仍需|待补充)[^\n]{0,20}(事实|信息|材料)', content))
    if not has_missing_facts:
        return False, "未包含'缺失事实'或'待补充事项'清单"
    
    return True, "起诉状骨架通过: 包含诉讼请求、事实与理由、证据清单、缺失事实清单"

def check_disclaimer(content: str) -> tuple[bool, str]:
    """Check for mandatory disclaimer."""
    has_disclaimer = bool(re.search(
        r'(免责声明|仅供参考|不构成.*法律意见|应.*律师.*审核|不替代.*律师|参考.*律师)',
        content
    ))
    if not has_disclaimer:
        return False, "缺少免责声明（必须说明结果仅供参考，不构成正式法律意见）"
    return True, "免责声明存在"

def check_upgrade_hint(content: str) -> tuple[bool, str]:
    """Check for upgrade hint (Free Starter boundary)."""
    has_upgrade = bool(re.search(
        r'(Pro|Business|升级|免费版|Free\s*Starter|联系作者|专业版|更深)',
        content
    ))
    if not has_upgrade:
        return False, "缺少升级提示（应提及免费版限制或Pro/Business版本升级建议）"
    return True, "升级提示存在"

def check_structured_output(content: str) -> tuple[bool, str]:
    """Check that output is structured (has headers, tables, or lists), not pure prose."""
    # Count markdown headers
    headers = re.findall(r'^#{1,3}\s+.+', content, re.MULTILINE)
    # Count table rows
    table_rows = re.findall(r'\|.+\|', content)
    # Count list items
    list_items = re.findall(r'^[-*•]\s+.+', content, re.MULTILINE)
    
    structure_score = len(headers) + len(table_rows) + len(list_items)
    
    if structure_score < 5:
        return False, f"输出结构化不足（仅找到{len(headers)}个标题, {len(table_rows)}行表格, {len(list_items)}个列表项）"
    
    return True, f"输出结构化良好（{len(headers)}个标题, {len(table_rows)}行表格, {len(list_items)}个列表项）"

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "argument_check", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)
    
    workspace = Path(sys.argv[1])
    checks = []
    
    # ── 1. Find the output file ──────────────────────────────────────────────
    report_path = find_report(workspace)
    file_found = report_path is not None
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found at: {report_path}" if file_found else "legal_analysis_report.md not found anywhere in workspace"
    })
    
    if not file_found:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return
    
    # ── 2. Read the file ─────────────────────────────────────────────────────
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return
    
    checks.append({
        "name": "file_readable",
        "passed": True,
        "detail": f"File size: {len(content)} chars"
    })
    
    if len(content) < 500:
        checks.append({"name": "content_substantial", "passed": False,
                        "detail": f"File too short ({len(content)} chars), likely incomplete"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return
    
    checks.append({
        "name": "content_substantial",
        "passed": True,
        "detail": f"Content length: {len(content)} chars"
    })
    
    # ── 3. Run all checks ────────────────────────────────────────────────────
    eval_functions = [
        ("contract_risk_scan",       check_contract_risk_scan),
        ("compensation_calculation",  check_compensation_calculation),
        ("complaint_skeleton",        check_complaint_skeleton),
        ("disclaimer_present",        check_disclaimer),
        ("upgrade_hint_present",      check_upgrade_hint),
        ("structured_output",         check_structured_output),
    ]
    
    for name, func in eval_functions:
        try:
            passed, detail = func(content)
            checks.append({"name": name, "passed": passed, "detail": detail})
        except Exception as e:
            checks.append({"name": name, "passed": False, "detail": f"Exception: {e}"})
    
    # ── 4. Score ─────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)
    
    # Must pass core checks to be considered passing
    core_checks = ["contract_risk_scan", "compensation_calculation", "complaint_skeleton", "disclaimer_present"]
    core_passed = all(c["passed"] for c in checks if c["name"] in core_checks)
    
    overall_passed = core_passed and score >= 0.75
    
    print(json.dumps({
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()