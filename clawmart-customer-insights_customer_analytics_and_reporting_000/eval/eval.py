import sys
import json
import re
from pathlib import Path

def find_report(workspace: Path):
    """Find customer_insights_report.md anywhere in workspace."""
    candidates = list(workspace.rglob("customer_insights_report.md"))
    return candidates[0] if candidates else None

def check(name, condition, detail):
    return {"name": name, "passed": bool(condition), "detail": detail}

def run_eval(workspace_path: str):
    workspace = Path(workspace_path)
    checks = []

    # --- Find the report ---
    report_path = find_report(workspace)
    if report_path is None:
        checks.append(check("report_file_exists", False, "customer_insights_report.md not found anywhere in workspace"))
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append(check("report_file_exists", True, f"Found at {report_path.relative_to(workspace)}"))

    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append(check("report_readable", False, f"Cannot read file: {e}"))
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append(check("report_readable", True, f"File read OK, {len(content)} chars"))

    # ── CHECK 1: Top-level header with exact emoji ────────────────────────────
    has_top_header = bool(re.search(r"📊\s*客户洞察报告", content))
    checks.append(check(
        "header_emoji_客户洞察报告",
        has_top_header,
        "Must contain '📊 客户洞察报告' as top header" if not has_top_header else "Found '📊 客户洞察报告'"
    ))

    # ── CHECK 2: 客户概览 section ─────────────────────────────────────────────
    has_overview = bool(re.search(r"##\s*客户概览", content))
    checks.append(check("section_客户概览", has_overview, "Must have '## 客户概览' section"))

    # Total/active/closed customer numbers must be present
    has_total = bool(re.search(r"总客户[：:]\s*\d+", content))
    checks.append(check("overview_total_customers", has_total, "Must list 总客户 count"))

    # ── CHECK 3: VIP tier with star emoji ─────────────────────────────────────
    has_vip = bool(re.search(r"🌟\s*VIP\s*客户", content))
    checks.append(check(
        "tier_vip_emoji_🌟",
        has_vip,
        "Must have '🌟 VIP 客户' tier header" if not has_vip else "Found VIP tier"
    ))

    # VIP must include 张总 and 李经理 (both have purchases + repurchases)
    vip_has_zhang = bool(re.search(r"张总", content[content.find("🌟"):content.find("💎")] if "🌟" in content and "💎" in content else ""))
    vip_section = ""
    if "🌟" in content:
        start = content.find("🌟")
        end = content.find("💎") if "💎" in content else start + 500
        vip_section = content[start:end]
    vip_has_zhang = "张总" in vip_section
    vip_has_li = "李经理" in vip_section
    checks.append(check("vip_contains_zhang_zong", vip_has_zhang, "张总 should be in VIP tier (累计¥150,000, 2次购买)"))
    checks.append(check("vip_contains_li_jingli", vip_has_li, "李经理 should be in VIP tier (累计¥85,000, 3次复购)"))

    # ── CHECK 4: 高潜力客户 tier with diamond emoji ───────────────────────────
    has_gaopotential = bool(re.search(r"💎\s*高潜力客户", content))
    checks.append(check(
        "tier_高潜力_emoji_💎",
        has_gaopotential,
        "Must have '💎 高潜力客户' tier header" if not has_gaopotential else "Found 高潜力客户 tier"
    ))

    # 王先生 and 赵女士 should be in 高潜力 (not yet converted, high intent)
    gaopotential_section = ""
    if "💎" in content:
        start = content.find("💎")
        end = content.find("📋") if "📋" in content else start + 800
        gaopotential_section = content[start:end]
    wang_in_gaopotential = "王先生" in gaopotential_section
    zhao_in_gaopotential = "赵女士" in gaopotential_section
    checks.append(check("高潜力_contains_王先生", wang_in_gaopotential,
                        "王先生 (预算¥50,000, 咨询3次, 未成交) should be 高潜力"))
    checks.append(check("高潜力_contains_赵女士", zhao_in_gaopotential,
                        "赵女士 (预算¥30,000, 咨询2次, 未成交) should be 高潜力"))

    # ── CHECK 5: 普通客户 tier ────────────────────────────────────────────────
    has_putong = bool(re.search(r"📋\s*普通客户", content))
    checks.append(check(
        "tier_普通客户_emoji_📋",
        has_putong,
        "Must have '📋 普通客户' tier header" if not has_putong else "Found 普通客户 tier"
    ))

    # ── CHECK 6: 流失风险 tier with warning emoji ─────────────────────────────
    has_churn = bool(re.search(r"⚠️\s*流失风险", content))
    checks.append(check(
        "tier_流失风险_emoji_⚠️",
        has_churn,
        "Must have '⚠️ 流失风险' tier header" if not has_churn else "Found 流失风险 tier"
    ))

    # 刘总, 孙经理, 吴经理 should be in 流失风险 (long-term no contact)
    churn_section = ""
    if "⚠️" in content:
        start = content.find("⚠️")
        # Find next major section after churn
        next_sections = ["## 成交预测", "## 最佳跟进", "## 个性化"]
        end = len(content)
        for ns in next_sections:
            idx = content.find(ns, start)
            if idx != -1 and idx < end:
                end = idx
        churn_section = content[start:end]
    liu_in_churn = "刘总" in churn_section
    sun_in_churn = "孙经理" in churn_section
    checks.append(check("流失风险_contains_刘总", liu_in_churn,
                        "刘总 (4个月未联系) should be in 流失风险"))
    checks.append(check("流失风险_contains_孙经理", sun_in_churn,
                        "孙经理 (5个月未联系) should be in 流失风险"))

    # ── CHECK 7: 成交预测 section ─────────────────────────────────────────────
    has_prediction = bool(re.search(r"##\s*成交预测", content))
    checks.append(check("section_成交预测", has_prediction, "Must have '## 成交预测' section"))

    # Must contain 置信度 (confidence)
    has_confidence = bool(re.search(r"置信度[：:]\s*\d+%", content))
    checks.append(check("prediction_置信度", has_confidence,
                        "Conversion prediction must include 置信度 as a percentage"))

    # Must contain 概率 for individual customers
    has_probability = bool(re.search(r"概率\s*\d+%", content))
    checks.append(check("prediction_individual_概率", has_probability,
                        "Individual customers must have 概率 percentage in prediction section"))

    # Wang xiansheng must appear in high-prob conversion with ¥50,000
    wang_in_prediction = bool(re.search(r"王先生.{0,100}¥?50[,，]?000", content, re.DOTALL))
    checks.append(check("prediction_王先生_¥50000", wang_in_prediction,
                        "王先生 with ¥50,000 must appear in conversion prediction"))

    # ── CHECK 8: 最佳跟进时机 section ────────────────────────────────────────
    has_timing = bool(re.search(r"##\s*最佳跟进时机", content))
    checks.append(check("section_最佳跟进时机", has_timing, "Must have '## 最佳跟进时机' section"))

    # Must include 回复率 with percentages
    has_reply_rate = bool(re.search(r"回复率.{0,20}\d+%", content))
    checks.append(check("timing_回复率_percentages", has_reply_rate,
                        "Must include 回复率 with percentages in timing section"))

    # Should mention specific time windows (morning 10-11, afternoon 15-16)
    has_morning_window = bool(re.search(r"10[：:.]?0{0,2}[-–]?11[：:.]?0{0,2}", content))
    has_afternoon_window = bool(re.search(r"15[：:.]?0{0,2}[-–]?16[：:.]?0{0,2}", content))
    checks.append(check("timing_morning_window_10_11", has_morning_window,
                        "Must include morning 10:00-11:00 time window"))
    checks.append(check("timing_afternoon_window_15_16", has_afternoon_window,
                        "Must include afternoon 15:00-16:00 time window"))

    # ── CHECK 9: 个性化建议 section ───────────────────────────────────────────
    has_personal = bool(re.search(r"##\s*个性化建议", content))
    checks.append(check("section_个性化建议", has_personal, "Must have '## 个性化建议' section"))

    # VIP 张总 must have a personalized next-contact date suggestion
    zhang_personal = bool(re.search(r"张总.{0,200}跟进|跟进.{0,200}张总", content, re.DOTALL))
    checks.append(check("personal_suggestion_张总", zhang_personal,
                        "张总 should have a personalized follow-up suggestion"))

    # 王先生 should have immediate action recommended
    wang_personal = bool(re.search(r"王先生.{0,200}(立即|immediate|案例|优惠)|立即.{0,50}王先生", content, re.DOTALL | re.IGNORECASE))
    checks.append(check("personal_suggestion_王先生_immediate", wang_personal,
                        "王先生 should have immediate action recommended (立即跟进 or similar)"))

    # ── CHECK 10: 营销优化建议 section ───────────────────────────────────────
    has_marketing = bool(re.search(r"##\s*营销优化建议", content))
    checks.append(check("section_营销优化建议", has_marketing, "Must have '## 营销优化建议' section"))

    # Must have at least 2 bold bullet strategies
    bold_strategies = re.findall(r"\*\*.+?\*\*", content)
    has_enough_strategies = len(bold_strategies) >= 2
    checks.append(check("marketing_bold_strategies",
                        has_enough_strategies,
                        f"Must have at least 2 bold (**...**) strategy items, found {len(bold_strategies)}"))

    # ── CHECK 11: Monetary values in ¥ format ────────────────────────────────
    yuan_values = re.findall(r"¥[\d,，]+", content)
    has_yuan_format = len(yuan_values) >= 3
    checks.append(check("monetary_values_yuan_format", has_yuan_format,
                        f"Must use ¥ for monetary values (found {len(yuan_values)} instances, need ≥3)"))

    # ── CHECK 12: Content is in Chinese (not English-only report) ────────────
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
    has_chinese = chinese_chars >= 100
    checks.append(check("report_in_chinese", has_chinese,
                        f"Report must be primarily in Chinese ({chinese_chars} Chinese chars found, need ≥100)"))

    # ── Score calculation ─────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    total = len(checks)
    score = len(passed_checks) / total

    # Hard requirements: file must exist + be readable + have all 4 tier emojis
    hard_checks = [
        "report_file_exists", "report_readable",
        "header_emoji_客户洞察报告",
        "tier_vip_emoji_🌟", "tier_高潜力_emoji_💎",
        "tier_普通客户_emoji_📋", "tier_流失风险_emoji_⚠️",
        "section_成交预测", "section_最佳跟进时机", "section_个性化建议"
    ]
    hard_passed = all(
        any(c["name"] == hc and c["passed"] for c in checks)
        for hc in hard_checks
    )

    overall_passed = hard_passed and score >= 0.75

    return {
        "passed": overall_passed,
        "score": round(score, 4),
        "checks": checks
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))