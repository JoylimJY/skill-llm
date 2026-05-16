import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ── Find the output report ──────────────────────────────────────────────
    report_path = None
    candidates = list(workspace.rglob("health_analysis_report.md"))
    if candidates:
        report_path = candidates[0]

    if not report_path or not report_path.exists():
        checks.append({"name": "output_file_exists", "passed": False,
                        "detail": "health_analysis_report.md not found anywhere in workspace."})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "output_file_exists", "passed": True,
                    "detail": f"Found at: {report_path}"})
    total_score += 0.05

    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False,
                        "detail": f"Could not read file: {e}"})
        return {"passed": False, "score": total_score, "checks": checks}

    checks.append({"name": "file_readable", "passed": True, "detail": "File read successfully."})

    # ── Check minimum content length ────────────────────────────────────────
    word_count = len(content)
    length_ok = word_count >= 1500
    checks.append({"name": "minimum_content_length",
                    "passed": length_ok,
                    "detail": f"Content length: {word_count} chars. Required >= 1500."})
    if length_ok:
        total_score += 0.05

    # ── Check: Output must be in Simplified Chinese ──────────────────────────
    # Count Chinese characters
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
    is_chinese = chinese_chars >= 300
    checks.append({"name": "output_in_simplified_chinese",
                    "passed": is_chinese,
                    "detail": f"Chinese characters found: {chinese_chars}. Required >= 300 (final output must be in Simplified Chinese per SKILL.md)."})
    if is_chinese:
        total_score += 0.08

    # ── Check: Section 1 – 健康画像更新 (Health Portrait Update) ────────────
    sec1_patterns = ["健康画像", "本次新增信息", "既往记录"]
    sec1_found = sum(1 for p in sec1_patterns if p in content)
    sec1_ok = sec1_found >= 2
    checks.append({"name": "section1_health_portrait_update",
                    "passed": sec1_ok,
                    "detail": f"Health portrait section markers found: {sec1_found}/3 ({sec1_patterns}). Required >= 2."})
    if sec1_ok:
        total_score += 0.10

    # ── Check: Section 2 – 西医评估 (Western Medicine Assessment) ───────────
    sec2_patterns = ["西医评估", "心血管", "HRV", "睡眠"]
    sec2_found = sum(1 for p in sec2_patterns if p in content)
    sec2_ok = sec2_found >= 3
    checks.append({"name": "section2_western_medicine_assessment",
                    "passed": sec2_ok,
                    "detail": f"Western medicine section markers found: {sec2_found}/4 ({sec2_patterns}). Required >= 3."})
    if sec2_ok:
        total_score += 0.10

    # ── Check: Section 2 – 中医辨证 (TCM Syndrome Differentiation) ──────────
    tcm_patterns = ["中医辨证", "体质", "脏腑", "证型"]
    tcm_found = sum(1 for p in tcm_patterns if p in content)
    tcm_ok = tcm_found >= 3
    checks.append({"name": "section2_tcm_syndrome_differentiation",
                    "passed": tcm_ok,
                    "detail": f"TCM section markers found: {tcm_found}/4 ({tcm_patterns}). Required >= 3."})
    if tcm_ok:
        total_score += 0.10

    # ── Check: TCM Five Elements analysis present ────────────────────────────
    five_elements = ["肝", "心", "脾", "肺", "肾"]
    elements_found = sum(1 for el in five_elements if el in content)
    elements_ok = elements_found >= 3
    checks.append({"name": "tcm_five_elements_analysis",
                    "passed": elements_ok,
                    "detail": f"Five Elements (肝心脾肺肾) referenced: {elements_found}/5. Required >= 3 (per SKILL.md 五行体质 framework)."})
    if elements_ok:
        total_score += 0.08

    # ── Check: TCM Syndrome patterns mentioned ───────────────────────────────
    syndrome_patterns = ["肝郁", "气滞", "心脾", "脾虚", "气血", "阴虚", "肝火", "湿", "虚"]
    syndrome_found = sum(1 for p in syndrome_patterns if p in content)
    syndrome_ok = syndrome_found >= 2
    checks.append({"name": "tcm_syndrome_patterns",
                    "passed": syndrome_ok,
                    "detail": f"TCM syndrome patterns found: {syndrome_found} matches from {syndrome_patterns[:5]}... Required >= 2."})
    if syndrome_ok:
        total_score += 0.07

    # ── Check: Seasonal/Solar Term analysis (小寒 or winter/冬) ──────────────
    seasonal_patterns = ["小寒", "节气", "冬季", "季节", "冬"]
    seasonal_found = sum(1 for p in seasonal_patterns if p in content)
    seasonal_ok = seasonal_found >= 1
    checks.append({"name": "seasonal_solar_term_analysis",
                    "passed": seasonal_ok,
                    "detail": f"Seasonal/solar term context referenced: {seasonal_found} mentions. Required >= 1 (SKILL.md mandates 24节气 integration)."})
    if seasonal_ok:
        total_score += 0.06

    # ── Check: HRV threshold analysis per SKILL.md ───────────────────────────
    # SKILL.md: HRV >50 good; 30-50 normal; <30 concerning
    # Weekly HRV avg is 35ms → should be mentioned as "normal range"
    # Thursday HRV 27ms → should be flagged as concerning (<30)
    hrv_mentioned = "HRV" in content or "心率变异" in content
    hrv_27_flagged = any(str(x) in content for x in ["27", "28", "29"]) and any(
        w in content for w in ["低", "偏低", "注意", "关注", "警惕", "恢复不足", "压力"])
    hrv_ok = hrv_mentioned and hrv_27_flagged
    checks.append({"name": "hrv_threshold_analysis",
                    "passed": hrv_ok,
                    "detail": f"HRV mentioned: {hrv_mentioned}. Thursday's concerning HRV (<30) flagged with context: {hrv_27_flagged}. Both required per SKILL.md threshold table."})
    if hrv_ok:
        total_score += 0.07

    # ── Check: Sleep depth analysis (深睡 <15% threshold) ───────────────────
    # SKILL.md: >15% deep sleep ideal; weekdays mostly below this threshold
    sleep_depth_ok = ("深睡" in content or "深度睡眠" in content) and any(
        p in content for p in ["15%", "14", "12", "11", "比例"])
    checks.append({"name": "sleep_depth_threshold_analysis",
                    "passed": sleep_depth_ok,
                    "detail": f"Deep sleep analysis with threshold reference found: {sleep_depth_ok}. SKILL.md requires >15% as ideal benchmark."})
    if sleep_depth_ok:
        total_score += 0.06

    # ── Check: hsCRP inflammation flag ───────────────────────────────────────
    # hsCRP is 2.8 mg/L → medium risk range, should be noted
    hsCRP_ok = any(p in content for p in ["CRP", "炎症", "C反应蛋白"]) and any(
        p in content for p in ["2.8", "中等", "中风险", "偏高", "需关注", "心血管"])
    checks.append({"name": "hscrp_inflammation_analysis",
                    "passed": hsCRP_ok,
                    "detail": f"hsCRP 2.8 mg/L (medium cardiovascular risk) addressed with value and context: {hsCRP_ok}."})
    if hsCRP_ok:
        total_score += 0.06

    # ── Check: IBS history referenced in current analysis ────────────────────
    ibs_ok = any(p in content for p in ["IBS", "肠易激", "肠易激综合征"]) and any(
        p in content for p in ["腹胀", "压力", "复发", "消化"])
    checks.append({"name": "ibs_history_longitudinal_correlation",
                    "passed": ibs_ok,
                    "detail": f"IBS history referenced and correlated with current digestive symptoms: {ibs_ok}. Tests longitudinal memory per SKILL.md."})
    if ibs_ok:
        total_score += 0.05

    # ── Check: Section 3 – 行动建议 (Actionable Recommendations) ────────────
    action_patterns = ["立即建议", "本周调整", "本月追踪", "行动建议", "建议"]
    action_found = sum(1 for p in action_patterns if p in content)
    action_ok = action_found >= 2
    checks.append({"name": "section3_actionable_recommendations",
                    "passed": action_ok,
                    "detail": f"Action recommendation section markers found: {action_found}/5. Required >= 2."})
    if action_ok:
        total_score += 0.05

    # ── Check: Section 4 – 营养与补剂 (Nutrition & Supplements) ────────────
    suppl_patterns = ["补剂", "营养", "饮食", "Omega", "鱼油", "维生素", "褪黑素"]
    suppl_found = sum(1 for p in suppl_patterns if p in content)
    suppl_ok = suppl_found >= 3
    checks.append({"name": "section4_nutrition_supplement_analysis",
                    "passed": suppl_ok,
                    "detail": f"Nutrition/supplement section markers found: {suppl_found}/7. Required >= 3."})
    if suppl_ok:
        total_score += 0.05

    # ── Check: Section 5 – 长期趋势提醒 (Long-term Trend Alert) ────────────
    trend_patterns = ["长期趋势", "趋势", "持续观察", "追踪", "下次"]
    trend_found = sum(1 for p in trend_patterns if p in content)
    trend_ok = trend_found >= 2
    checks.append({"name": "section5_longterm_trend_alert",
                    "passed": trend_ok,
                    "detail": f"Long-term trend section markers found: {trend_found}/5. Required >= 2."})
    if trend_ok:
        total_score += 0.05

    # ── Check: Risk level classification ────────────────────────────────────
    risk_ok = any(p in content for p in ["风险等级", "低风险", "中风险", "高风险", "风险：低", "风险：中", "风险：高", "低 /", "中 /"])
    checks.append({"name": "risk_level_classification",
                    "passed": risk_ok,
                    "detail": f"Risk level (低/中/高) explicitly stated: {risk_ok}. Required per SKILL.md output format."})
    if risk_ok:
        total_score += 0.04

    # ── Check: Uric acid family history noted ───────────────────────────────
    uric_ok = any(p in content for p in ["尿酸", "高尿酸", "痛风"]) and any(
        p in content for p in ["父亲", "家族", "遗传", "注意", "监测"])
    checks.append({"name": "uric_acid_family_history_integration",
                    "passed": uric_ok,
                    "detail": f"Uric acid (412 μmol/L near limit) cross-referenced with father's gout history: {uric_ok}. Tests multi-source longitudinal synthesis."})
    if uric_ok:
        total_score += 0.04

    # ── Final pass/fail ──────────────────────────────────────────────────────
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    total_score = round(min(total_score, 1.0), 3)
    passed = total_score >= 0.60 and passed_checks >= int(total_checks * 0.65)

    return {
        "passed": passed,
        "score": total_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))