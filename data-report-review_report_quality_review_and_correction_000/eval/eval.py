import sys
import json
import re
from pathlib import Path

def find_reviewed_report(workspace):
    """Find the reviewed/corrected report file."""
    ws = Path(workspace)
    # Look for reviewed report - agent may create a new file or modify in place
    # Accept any .md file that contains the audit summary block
    candidates = list(ws.rglob("*.md"))
    for c in candidates:
        try:
            text = c.read_text(encoding="utf-8")
            if "审查结果" in text:
                return c, text
        except Exception:
            pass
    return None, None

def find_any_report_with_corrections(workspace):
    """Find a report that has been modified/corrected."""
    ws = Path(workspace)
    candidates = list(ws.rglob("*.md"))
    best = None
    best_text = ""
    for c in candidates:
        try:
            text = c.read_text(encoding="utf-8")
            # Prefer files with audit summary
            if "审查结果" in text and len(text) > 200:
                if len(text) > len(best_text):
                    best = c
                    best_text = text
        except Exception:
            pass
    if best:
        return best, best_text
    # fallback: check modified report
    try:
        p = Path(workspace) / "Q1_Q2_2024_sales_report.md"
        t = p.read_text(encoding="utf-8")
        return p, t
    except Exception:
        return None, ""

def run_checks(workspace):
    checks = []
    
    # ---- FIND THE OUTPUT FILE ----
    report_path, report_text = find_any_report_with_corrections(workspace)
    
    file_found = report_path is not None and len(report_text) > 100
    checks.append({
        "name": "输出文件存在",
        "passed": file_found,
        "detail": f"Found: {report_path}" if file_found else "No reviewed report file found."
    })
    if not file_found:
        # Fill remaining checks as failed
        for name in [
            "审查结果摘要格式正确",
            "数据准确性-Q1总计已更正(424000)",
            "数据准确性-西区Q1数字已更正(63000)",
            "数据准确性-Q2环比增长率已更正(实为负增长)",
            "逻辑一致性-东区领跑矛盾已修正",
            "逻辑一致性-客户满意度无依据推断已处理",
            "结论质量-过度泛化已修正",
            "结论质量-局限性声明已添加",
            "受众适配-专业术语已处理(GMV/CAGR/cohort)",
            "表达质量-模糊措辞已修正(大概/看起来/应该)",
            "审查摘要包含修改记录",
        ]:
            checks.append({"name": name, "passed": False, "detail": "File not found, skipped."})
        return checks

    text = report_text

    # ---- CHECK 1: 审查结果 FORMAT ----
    # Must contain ## 审查结果 header with the emoji status lines
    has_summary_header = bool(re.search(r'##\s*审查结果', text))
    has_data_line = bool(re.search(r'\*\*数据准确性[：:]\*\*\s*(✅|⚠️)', text))
    has_logic_line = bool(re.search(r'\*\*逻辑连贯性[：:]\*\*\s*(✅|⚠️)', text))
    has_conclusion_line = bool(re.search(r'\*\*结论质量[：:]\*\*\s*(✅|⚠️)', text))
    has_audience_line = bool(re.search(r'\*\*受众适配[：:]\*\*\s*(✅|⚠️)', text))
    has_expression_line = bool(re.search(r'\*\*表达质量[：:]\*\*\s*(✅|⚠️)', text))
    
    format_ok = all([has_summary_header, has_data_line, has_logic_line, has_conclusion_line, has_audience_line, has_expression_line])
    checks.append({
        "name": "审查结果摘要格式正确",
        "passed": format_ok,
        "detail": (
            f"Header={has_summary_header}, 数据={has_data_line}, 逻辑={has_logic_line}, "
            f"结论={has_conclusion_line}, 受众={has_audience_line}, 表达={has_expression_line}"
        )
    })

    # ---- CHECK 2: Q1 total corrected to 424,000 ----
    # Wrong was 450,000; correct is 424,000
    has_wrong_total = bool(re.search(r'45[0,]*[0,]*[0,]*0*\b', text.replace(',', '').replace('，', '')))
    # More precise: look for 450000 or 45万 (original wrong values)
    has_450000 = bool(re.search(r'450[,，]?000|45万', text))
    has_424000 = bool(re.search(r'424[,，]?000|42\.?4万', text))
    q1_total_fixed = has_424000 and not has_450000
    checks.append({
        "name": "数据准确性-Q1总计已更正(424000)",
        "passed": q1_total_fixed,
        "detail": f"Found 424000: {has_424000}, Still contains 450000: {has_450000}"
    })

    # ---- CHECK 3: West region Q1 corrected to 63,000 ----
    # Wrong was 71,000; correct is 63,000
    has_71000 = bool(re.search(r'71[,，]?000|7\.?1万', text))
    has_63000 = bool(re.search(r'63[,，]?000|6\.?3万', text))
    west_fixed = has_63000 and not has_71000
    checks.append({
        "name": "数据准确性-西区Q1数字已更正(63000)",
        "passed": west_fixed,
        "detail": f"Found 63000: {has_63000}, Still contains 71000: {has_71000}"
    })

    # ---- CHECK 4: Q2 growth rate corrected (was falsely positive 28.4%, actual is negative) ----
    # Original: 28.4% growth — actually Q2(320000) < Q1(424000), so it's a decline
    has_28_4 = bool(re.search(r'28\.?4\s*%', text))
    # Look for negative growth indication: 下降, 负增长, 下滑, or negative percentage like -24 or -25
    has_decline = bool(re.search(r'下降|负增长|下滑|减少|环比.*?-\d|下跌|-2[0-9]\.?\d*\s*%', text))
    growth_fixed = has_decline and not has_28_4
    checks.append({
        "name": "数据准确性-Q2环比增长率已更正(实为负增长)",
        "passed": growth_fixed,
        "detail": f"Contains decline indicator: {has_decline}, Still has 28.4%: {has_28_4}"
    })

    # ---- CHECK 5: East region "leads all regions in Q2" contradiction fixed ----
    # North Q2=119,000 > East Q2=79,000, so East does NOT lead
    # Original: "东区在Q2表现亮眼，领跑全部四个大区"
    has_east_leads = bool(re.search(r'东区.*?领跑|领跑.*?东区', text))
    checks.append({
        "name": "逻辑一致性-东区领跑矛盾已修正",
        "passed": not has_east_leads,
        "detail": f"Still contains East-leads-all false claim: {has_east_leads}"
    })

    # ---- CHECK 6: Customer satisfaction conclusion without data basis fixed ----
    # Original: "客户满意度在Q2得到了显著提升" — no customer satisfaction data cited
    # Agent should remove this claim or note lack of evidence
    has_unsubstantiated_sat = bool(re.search(r'客户满意度.*?显著提升|显著提升.*?客户满意度', text))
    checks.append({
        "name": "逻辑一致性-客户满意度无依据推断已处理",
        "passed": not has_unsubstantiated_sat,
        "detail": f"Still contains unsupported satisfaction claim: {has_unsubstantiated_sat}"
    })

    # ---- CHECK 7: Overgeneralization fixed ----
    # Original: "证明我们整体产品战略是成功的" / "所有区域均显示出正向发展趋势"
    has_overgeneralize = bool(re.search(r'整体产品战略.*?成功|证明.*?整体.*?战略|所有区域.*?正向发展', text))
    checks.append({
        "name": "结论质量-过度泛化已修正",
        "passed": not has_overgeneralize,
        "detail": f"Still contains overgeneralized conclusion: {has_overgeneralize}"
    })

    # ---- CHECK 8: Limitations section present ----
    # SKILL.md: "局限声明：分析的局限性是否已说明"
    has_limitations = bool(re.search(r'局限|限制|不足|数据范围|样本|分析范围|本报告.*?仅', text))
    checks.append({
        "name": "结论质量-局限性声明已添加",
        "passed": has_limitations,
        "detail": f"Contains limitations statement: {has_limitations}"
    })

    # ---- CHECK 9: Technical jargon handled for board audience ----
    # GMV, CAGR, cohort retention should be explained or replaced for board readers
    has_raw_gmv = bool(re.search(r'GMV弹性系数|cohort\s+retention|CAGR', text, re.IGNORECASE))
    checks.append({
        "name": "受众适配-专业术语已处理(GMV/CAGR/cohort)",
        "passed": not has_raw_gmv,
        "detail": f"Still contains unexplained jargon (GMV弹性系数/cohort retention/CAGR): {has_raw_gmv}"
    })

    # ---- CHECK 10: Vague hedges removed/properly labeled ----
    # SKILL.md danger sign: 使用"应该"、"大概"、"看起来"等模糊措辞
    vague_pattern = re.compile(r'大概是因为|看起来该|应该能继续', text)
    has_vague = bool(re.search(r'大概是因为|看起来该区域|应该能继续', text))
    checks.append({
        "name": "表达质量-模糊措辞已修正(大概/看起来/应该)",
        "passed": not has_vague,
        "detail": f"Still contains vague hedging phrases: {has_vague}"
    })

    # ---- CHECK 11: Modification summary present in audit block ----
    # SKILL.md: "修改摘要：（如有修改）" with bullet points
    has_modification_summary = bool(re.search(r'\*\*修改摘要[：:]\*\*|修改摘要', text))
    has_bullet_modifications = bool(re.search(r'修改摘要[\s\S]{0,200}[-\-–•]\s*\S', text))
    summary_ok = has_modification_summary and has_bullet_modifications
    checks.append({
        "name": "审查摘要包含修改记录",
        "passed": summary_ok,
        "detail": f"Has 修改摘要 header: {has_modification_summary}, Has bullet items: {has_bullet_modifications}"
    })

    return checks


def main():
    if len(sys.argv) < 2:
        workspace = "/workspace"
    else:
        workspace = sys.argv[1]

    try:
        checks = run_checks(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_error", "passed": False, "detail": str(e)}]
        }
        print(json.dumps(result, ensure_ascii=False))
        return

    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall_passed = passed_count >= int(total * 0.85)  # must pass 85%+ checks

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()