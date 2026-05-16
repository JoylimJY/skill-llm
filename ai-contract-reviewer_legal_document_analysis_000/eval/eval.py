import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []

    # ── Locate the report file ──────────────────────────────────────────────
    # The prompt specifies the output file should be named: contract_risk_report.txt
    candidates = list(workspace.rglob("contract_risk_report.txt"))
    if not candidates:
        # Also accept .md extension as a reasonable alternative
        candidates = list(workspace.rglob("contract_risk_report.md"))

    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "report_file_exists", "passed": False,
                         "detail": "contract_risk_report.txt not found anywhere in workspace."}]
        }

    report_path = candidates[0]
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "report_file_readable", "passed": False,
                         "detail": f"Could not read report file: {e}"}]
        }

    content_lower = content.lower()

    # ── CHECK 1: Disclaimer appears first ──────────────────────────────────
    # Must appear before any analysis content
    disclaimer_keywords = ["not legal advice", "informational purposes only",
                           "不构成法律建议", "仅供参考", "qualified attorney",
                           "ai analysis", "disclaimer", "免责声明"]
    disclaimer_found = any(kw in content_lower for kw in disclaimer_keywords)
    # Check that it appears in the first 20% of the document
    first_fifth = content[:max(200, len(content)//5)].lower()
    disclaimer_first = any(kw in first_fifth for kw in disclaimer_keywords)
    checks.append({
        "name": "disclaimer_present_and_first",
        "passed": disclaimer_found and disclaimer_first,
        "detail": f"Disclaimer found: {disclaimer_found}. In first section: {disclaimer_first}."
    })

    # ── CHECK 2: Report is in Chinese (since contract is Chinese) ──────────
    # Rule 3: Chinese contracts → full Chinese analysis
    # Count Chinese characters vs total meaningful characters
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
    total_chars = len(re.sub(r'\s', '', content))
    chinese_ratio = chinese_chars / max(total_chars, 1)
    is_chinese = chinese_ratio > 0.15  # At least 15% Chinese characters
    checks.append({
        "name": "output_in_chinese",
        "passed": is_chinese,
        "detail": f"Chinese character ratio: {chinese_ratio:.2%} ({chinese_chars} Chinese chars / {total_chars} total)."
    })

    # ── CHECK 3: Document Summary section present ──────────────────────────
    summary_keywords = ["document summary", "合同概要", "合同摘要", "文件摘要", "基本信息",
                        "合同信息", "### 文件", "### 合同"]
    has_summary = any(kw in content_lower for kw in summary_keywords)
    # Also check for parties identification
    parties_keywords = ["北京创新科技", "甲方", "乙方", "委托方", "服务方"]
    has_parties = any(kw in content for kw in parties_keywords)
    checks.append({
        "name": "document_summary_with_parties",
        "passed": has_summary and has_parties,
        "detail": f"Summary section found: {has_summary}. Parties identified: {has_parties}."
    })

    # ── CHECK 4: HIGH risk items flagged ──────────────────────────────────
    # Must have HIGH risk section with emoji 🔴 or text "HIGH" / "高风险"
    high_risk_indicators = ["🔴", "high risk", "高风险", "high\n", "**high**",
                             "风险等级：高", "风险：高", "## high", "### high"]
    has_high_risk = any(ind in content for ind in high_risk_indicators) or \
                    bool(re.search(r'high\s*risk|高风险|🔴', content, re.IGNORECASE))
    checks.append({
        "name": "high_risk_section_present",
        "passed": has_high_risk,
        "detail": f"HIGH risk section or markers found: {has_high_risk}."
    })

    # ── CHECK 5: Unlimited liability flagged (Rule 6 + Rule specific) ──────
    # The contract has unlimited liability in sections 4.3 and 6.1
    liability_keywords = ["无上限", "unlimited liability", "责任上限", "无限赔偿",
                          "赔偿金额不设上限", "赔偿金额无上限", "liability cap",
                          "不设上限", "liability"]
    has_liability_flag = any(kw in content for kw in liability_keywords)
    checks.append({
        "name": "unlimited_liability_flagged",
        "passed": has_liability_flag,
        "detail": f"Unlimited liability clause flagged: {has_liability_flag}. "
                  "Contract sections 4.3 and 6.1 both contain unlimited liability."
    })

    # ── CHECK 6: Non-compete > 2 years flagged (Rule 5) ──────────────────
    # Contract has 5-year non-compete across China + Asia-Pacific
    noncompete_keywords = ["竞业禁止", "non-compete", "non compete", "竞业限制",
                           "五年", "5年", "5 year", "five year"]
    has_noncompete_flag = any(kw in content for kw in noncompete_keywords)
    # Must flag it as problematic (>2 years is the threshold)
    excessive_scope_keywords = ["过长", "过宽", "excessive", "unreasonable", "不合理",
                                 "超过2年", "超过两年", "范围过广", "地域", "亚太"]
    has_scope_concern = any(kw in content for kw in excessive_scope_keywords) or \
                        (has_noncompete_flag and has_high_risk)
    checks.append({
        "name": "excessive_noncompete_flagged",
        "passed": has_noncompete_flag and has_scope_concern,
        "detail": f"Non-compete mentioned: {has_noncompete_flag}. Excessive scope flagged: {has_scope_concern}. "
                  "Contract has 5-year non-compete covering all of China + Asia-Pacific."
    })

    # ── CHECK 7: Automatic renewal flagged (Rule 7) ──────────────────────
    # Section 2.4 has automatic renewal with unilateral terms
    renewal_keywords = ["自动续期", "automatic renewal", "自动续约", "auto-renew",
                        "自动延续", "续期", "automatic renew"]
    has_renewal_flag = any(kw in content for kw in renewal_keywords)
    checks.append({
        "name": "automatic_renewal_flagged",
        "passed": has_renewal_flag,
        "detail": f"Automatic renewal clause flagged: {has_renewal_flag}. "
                  "Section 2.4 contains automatic renewal with no opt-out protection."
    })

    # ── CHECK 8: Unilateral modification right flagged (Rule 8) ──────────
    # Section 7.1 explicitly grants unilateral modification rights
    unilateral_keywords = ["单方面修改", "unilateral modification", "单方变更",
                           "单方面", "unilaterally", "第七条", "合同变更",
                           "单方面确定"]
    has_unilateral_flag = any(kw in content for kw in unilateral_keywords)
    checks.append({
        "name": "unilateral_modification_flagged",
        "passed": has_unilateral_flag,
        "detail": f"Unilateral modification right flagged: {has_unilateral_flag}. "
                  "Section 7.1 allows Party A to change any terms with 3 days notice."
    })

    # ── CHECK 9: Missing protections section ──────────────────────────────
    # Must check for missing protections from the 14-item list
    missing_prot_keywords = ["missing protection", "缺失", "缺少", "未包含",
                              "没有", "missing", "保护条款", "缺乏",
                              "missing protections", "缺失的保护"]
    has_missing_section = any(kw in content_lower for kw in missing_prot_keywords)
    # Specifically: force majeure and dispute resolution are missing
    specific_missing = ["不可抗力", "force majeure", "争议解决", "dispute resolution",
                        "仲裁", "arbitration"]
    has_specific_missing = any(kw in content for kw in specific_missing)
    checks.append({
        "name": "missing_protections_identified",
        "passed": has_missing_section and has_specific_missing,
        "detail": f"Missing protections section: {has_missing_section}. "
                  f"Specific items (force majeure/dispute resolution) flagged: {has_specific_missing}."
    })

    # ── CHECK 10: Power balance assessment ────────────────────────────────
    # Must assess who benefits more — clearly favors Party A heavily
    power_balance_keywords = ["power balance", "权力平衡", "偏向", "倾向",
                               "heavily favors", "严重偏向", "明显偏向",
                               "甲方", "party a", "不平衡", "平衡",
                               "balanced", "favors"]
    has_power_balance = any(kw in content_lower for kw in power_balance_keywords)
    # Should indicate it favors Party A / 甲方
    favors_a_keywords = ["heavily favors", "严重偏向甲方", "明显偏向甲方",
                          "偏向甲方", "favors party a", "甲方获益更多",
                          "对甲方有利", "不利于乙方"]
    favors_a = any(kw in content for kw in favors_a_keywords) or \
               ("甲方" in content and ("偏向" in content or "不平衡" in content or "不利" in content))
    checks.append({
        "name": "power_balance_assessment",
        "passed": has_power_balance and favors_a,
        "detail": f"Power balance section found: {has_power_balance}. "
                  f"Correctly identifies contract favors Party A: {favors_a}."
    })

    # ── CHECK 11: Suggested revision language for HIGH risk items ─────────
    # Must provide alternative clause wording
    revision_keywords = ["suggested revision", "建议修改", "替代条款", "修改建议",
                          "revision language", "suggested language", "alternative",
                          "建议版本", "参考条款", "修订建议", "可修改为"]
    has_revision = any(kw in content for kw in revision_keywords)
    checks.append({
        "name": "suggested_revision_language",
        "passed": has_revision,
        "detail": f"Suggested revision language provided: {has_revision}."
    })

    # ── CHECK 12: Asymmetric termination clause flagged ──────────────────
    # Section 8: Party A can terminate with 3 days notice, Party B needs 90 days + penalty
    termination_asymmetry_keywords = ["终止", "termination", "提前终止", "解除合同",
                                       "不对称", "asymmetric", "asymmetry",
                                       "不平等", "3日", "90日", "三日", "九十日"]
    has_termination_flag = any(kw in content for kw in termination_asymmetry_keywords)
    checks.append({
        "name": "asymmetric_termination_flagged",
        "passed": has_termination_flag,
        "detail": f"Asymmetric termination conditions flagged: {has_termination_flag}. "
                  "Party A: 3 days notice, no penalty. Party B: 90 days notice + 50% remaining fees penalty."
    })

    # ── CHECK 13: IP clause flagged ───────────────────────────────────────
    # Section 3.3 claims ALL inventions regardless of relevance
    ip_keywords = ["知识产权", "intellectual property", "ip ownership", "版权",
                    "所有权", "ownership", "第三条", "工作成果", "发明"]
    has_ip_flag = any(kw in content for kw in ip_keywords)
    checks.append({
        "name": "ip_ownership_clause_flagged",
        "passed": has_ip_flag,
        "detail": f"IP ownership clause flagged: {has_ip_flag}. "
                  "Section 3.3 claims all inventions even if unrelated to contract work."
    })

    # ── CHECK 14: Risk Summary counts ─────────────────────────────────────
    # Must have a risk summary with counts
    risk_count_patterns = [
        r'high\s*risk.*?[：:]\s*\d+',
        r'高风险.*?[：:]\s*\d+',
        r'\d+\s*high',
        r'high.*?\d+',
        r'高风险条款.*?\d+',
        r'risk summary',
        r'风险摘要',
        r'风险概述'
    ]
    has_risk_counts = any(re.search(p, content, re.IGNORECASE) for p in risk_count_patterns)
    checks.append({
        "name": "risk_summary_with_counts",
        "passed": has_risk_counts,
        "detail": f"Risk summary with counts present: {has_risk_counts}."
    })

    # ── Final scoring ──────────────────────────────────────────────────────
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks

    # Must pass critical checks to be considered "passed" overall
    critical_checks = [
        "disclaimer_present_and_first",
        "output_in_chinese",
        "unlimited_liability_flagged",
        "excessive_noncompete_flagged",
        "unilateral_modification_flagged",
        "automatic_renewal_flagged",
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )

    overall_passed = critical_passed and score >= 0.75

    return {
        "passed": overall_passed,
        "score": round(score, 4),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "invocation", "passed": False,
                                       "detail": "No workspace path provided."}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))