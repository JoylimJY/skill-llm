import sys
import json
import re
from pathlib import Path

def score_checks(checks):
    passed = sum(1 for c in checks if c["passed"])
    return round(passed / len(checks), 3)

def find_file(workspace, name):
    matches = list(Path(workspace).rglob(name))
    return matches[0] if matches else None

def read(p):
    try:
        return Path(p).read_text(encoding="utf-8")
    except Exception:
        return ""

def main():
    workspace = sys.argv[1]
    checks = []

    # ── Check 1: weekly_plan.md exists and was generated via template ──
    wp = find_file(workspace, "weekly_plan.md")
    c1_pass = wp is not None
    c1_detail = f"Found at {wp}" if c1_pass else "weekly_plan.md not found"
    checks.append({"name": "weekly_plan.md_exists", "passed": c1_pass, "detail": c1_detail})

    wp_text = read(wp) if wp else ""
    c2_pass = "周运营计划表" in wp_text and "每日动作" in wp_text
    checks.append({"name": "weekly_plan_has_template_structure",
                   "passed": c2_pass,
                   "detail": f"Template headers present: {c2_pass}"})

    # Weekly plan: has filled weekly goal (not blank table row)
    c3_pass = False
    if wp_text:
        # Look for non-empty rows in 本周目标 table
        lines = wp_text.splitlines()
        in_goal = False
        for line in lines:
            if "本周目标" in line:
                in_goal = True
            if in_goal and "|" in line:
                cells = [c.strip() for c in line.split("|") if c.strip()]
                if len(cells) >= 2 and not all(c in ("指标", "目标值", "当前值", "差距", "---", "") for c in cells):
                    c3_pass = True
                    break
    checks.append({"name": "weekly_plan_goals_filled",
                   "passed": c3_pass,
                   "detail": "Weekly goal table has non-empty content rows"})

    # ── Check 2: campaign.md exists and has all required sections ──
    cp = find_file(workspace, "campaign.md")
    c4_pass = cp is not None
    checks.append({"name": "campaign.md_exists",
                   "passed": c4_pass,
                   "detail": f"Found at {cp}" if c4_pass else "campaign.md not found"})

    cp_text = read(cp) if cp else ""
    required_campaign_sections = ["活动主题", "目标人群", "爆品", "利益点", "节奏", "素材清单", "页面改动", "客服话术", "风险"]
    missing_sections = [s for s in required_campaign_sections if s not in cp_text]
    c5_pass = len(missing_sections) == 0
    checks.append({"name": "campaign_has_all_9_sections",
                   "passed": c5_pass,
                   "detail": f"Missing sections: {missing_sections}" if not c5_pass else "All 9 required sections present"})

    # ── Check 3: repurchase_14d.md exists with all 14 day rows filled ──
    rp = find_file(workspace, "repurchase_14d.md")
    c6_pass = rp is not None
    checks.append({"name": "repurchase_14d.md_exists",
                   "passed": c6_pass,
                   "detail": f"Found at {rp}" if c6_pass else "repurchase_14d.md not found"})

    rp_text = read(rp) if rp else ""
    # Must have all D1..D14 rows
    day_rows_found = sum(1 for d in range(1, 15) if f"D{d}" in rp_text)
    c7_pass = day_rows_found == 14
    checks.append({"name": "repurchase_14d_all_days_present",
                   "passed": c7_pass,
                   "detail": f"Day rows found: {day_rows_found}/14"})

    # Check that at least 10 day rows have non-empty content beyond just day label
    filled_rows = 0
    if rp_text:
        for line in rp_text.splitlines():
            m = re.match(r"\|\s*D(\d+)\s*\|(.*)", line)
            if m:
                rest = m.group(2).replace("|", "").strip()
                if len(rest) > 4:
                    filled_rows += 1
    c8_pass = filled_rows >= 10
    checks.append({"name": "repurchase_14d_rows_filled",
                   "passed": c8_pass,
                   "detail": f"Filled day rows: {filled_rows} (need ≥10)"})

    # ── Check 4: customer_sop.md exists with required SOP sections ──
    sp = find_file(workspace, "customer_sop.md")
    c9_pass = sp is not None
    checks.append({"name": "customer_sop.md_exists",
                   "passed": c9_pass,
                   "detail": f"Found at {sp}" if c9_pass else "customer_sop.md not found"})

    sp_text = read(sp) if sp else ""
    sop_sections = ["新客", "催付", "催评", "售后"]
    missing_sop = [s for s in sop_sections if s not in sp_text]
    c10_pass = len(missing_sop) == 0
    checks.append({"name": "customer_sop_has_required_sections",
                   "passed": c10_pass,
                   "detail": f"Missing SOP sections: {missing_sop}" if not c10_pass else "All SOP sections present"})

    # SOP must have actual content (not just headers)
    sop_content_lines = [l for l in sp_text.splitlines() if l.strip() and not l.startswith("#")]
    c11_pass = len(sop_content_lines) >= 8
    checks.append({"name": "customer_sop_has_substantive_content",
                   "passed": c11_pass,
                   "detail": f"Non-header content lines: {len(sop_content_lines)} (need ≥8)"})

    # ── Check 5: review_report.md (復盤) exists and has retrospective structure ──
    rrp = find_file(workspace, "review_report.md")
    c12_pass = rrp is not None
    checks.append({"name": "review_report.md_exists",
                   "passed": c12_pass,
                   "detail": f"Found at {rrp}" if c12_pass else "review_report.md not found"})

    rrp_text = read(rrp) if rrp else ""
    retro_keys = ["动作", "数据结果", "结论", "下周实验"]
    missing_retro = [k for k in retro_keys if k not in rrp_text]
    c13_pass = len(missing_retro) == 0
    checks.append({"name": "review_report_has_retrospective_structure",
                   "passed": c13_pass,
                   "detail": f"Missing retro sections: {missing_retro}" if not c13_pass else "All 4 retrospective sections present"})

    # ── Check 6: Proprietary metric formula present in at least one doc ──
    all_text = wp_text + cp_text + rp_text + sp_text + rrp_text
    # Must contain the exact repurchase rate formula or equivalent
    metric_formula_present = (
        "30天" in all_text and "复购率" in all_text and
        ("再次购买人数" in all_text or "复购人数" in all_text)
    )
    checks.append({"name": "metric_formula_30d_repurchase_present",
                   "passed": metric_formula_present,
                   "detail": "30-day repurchase rate formula found in output docs"})

    # ── Check 7: Goods structure with all 4 roles ──
    goods_roles = ["引流款", "利润款", "形象款", "复购款"]
    missing_roles = [r for r in goods_roles if r not in all_text]
    c15_pass = len(missing_roles) == 0
    checks.append({"name": "goods_structure_all_4_roles",
                   "passed": c15_pass,
                   "detail": f"Missing goods roles: {missing_roles}" if not c15_pass else "All 4 goods roles present"})

    # ── Check 8: Funnel stages present ──
    funnel_stages = ["曝光", "点击", "加购", "下单", "复购"]
    missing_funnel = [s for s in funnel_stages if s not in all_text]
    c16_pass = len(missing_funnel) == 0
    checks.append({"name": "funnel_stages_covered",
                   "passed": c16_pass,
                   "detail": f"Missing funnel stages: {missing_funnel}" if not c16_pass else "All key funnel stages mentioned"})

    # ── Check 9: RFM or customer segmentation in any doc ──
    rfm_present = any(k in all_text for k in ["RFM", "新客", "活跃", "沉默", "流失", "高价值"])
    checks.append({"name": "customer_segmentation_rfm_present",
                   "passed": rfm_present,
                   "detail": "Customer segmentation (RFM-style) found in documents"})

    # ── Check 10: Stage diagnosis present ──
    stage_present = any(k in all_text for k in ["冷启动", "增长期", "成熟", "下滑"])
    checks.append({"name": "store_stage_diagnosis_present",
                   "passed": stage_present,
                   "detail": "Store lifecycle stage diagnosis present"})

    passed_all = all(c["passed"] for c in checks)
    score = score_checks(checks)

    result = {
        "passed": passed_all,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()