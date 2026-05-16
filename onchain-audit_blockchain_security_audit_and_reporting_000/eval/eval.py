import sys
import json
import re
import os
from pathlib import Path

workspace = sys.argv[1]

checks = []
total_score = 0.0
max_score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global total_score, max_score
    max_score += weight
    if passed:
        total_score += weight

def find_file(filename):
    """Search recursively for a file by name."""
    results = list(Path(workspace).rglob(filename))
    return results[0] if results else None

def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return None

# ============================================================
# FILE 1: alphaswap_deep_audit.md — Deep audit of AlphaSwap
# ============================================================
deep_file = find_file("alphaswap_deep_audit.md")
deep_content = read_file(deep_file) if deep_file else None

add_check(
    "deep_audit_file_exists",
    deep_file is not None and deep_content is not None,
    f"File 'alphaswap_deep_audit.md' {'found at: ' + str(deep_file) if deep_file else 'NOT FOUND'}",
    weight=1.0
)

if deep_content:
    # Check main header
    add_check(
        "deep_audit_main_header",
        "## 🔒 链上项目安全审计报告" in deep_content,
        f"Main header '## 🔒 链上项目安全审计报告' {'found' if '## 🔒 链上项目安全审计报告' in deep_content else 'MISSING'}",
        weight=1.5
    )

    # Check risk score section exists
    has_risk_score = bool(re.search(r'###\s*📊\s*综合风险评分', deep_content))
    add_check(
        "deep_audit_risk_score_section",
        has_risk_score,
        f"Risk score section '### 📊 综合风险评分' {'found' if has_risk_score else 'MISSING'}",
        weight=1.5
    )

    # Check risk score format: XX/100（风险级别）
    risk_score_match = re.search(r'(\d+)/100（(低风险|中风险|高风险)）', deep_content)
    add_check(
        "deep_audit_risk_score_format",
        risk_score_match is not None,
        f"Risk score format 'XX/100（风险级别）' {'found: ' + risk_score_match.group(0) if risk_score_match else 'MISSING or WRONG FORMAT'}",
        weight=2.0
    )

    # AlphaSwap: has mint_function + no LP lock >= 180d + anonymous team → should be HIGH risk (<=30) or MEDIUM
    # Based on mock tool logic: score starts 100, -15(LP short 90d), -15(anon team), -10(top10=78.5>70→-20), -10(vol<10k), -5(social<1k), -10(mint), -5(no timelock)
    # = 100 - 15 - 15 - 20 - 10 - 5 - 10 - 5 = 20 → 高风险
    if risk_score_match:
        score_val = int(risk_score_match.group(1))
        risk_level = risk_score_match.group(2)
        # AlphaSwap should be 高风险 (score <= 30)
        is_high_risk = risk_level == "高风险" and score_val <= 30
        add_check(
            "deep_audit_alphaswap_correct_risk_level",
            is_high_risk,
            f"AlphaSwap should be 高风险 (score ≤ 30), got: {score_val}/100（{risk_level}）. {'CORRECT' if is_high_risk else 'INCORRECT — wrong risk assessment'}",
            weight=2.0
        )

    # Check safe items section with [✓] format
    has_safe_section = bool(re.search(r'###\s*✅\s*安全项', deep_content))
    add_check(
        "deep_audit_safe_section",
        has_safe_section,
        f"Safe items section '### ✅ 安全项' {'found' if has_safe_section else 'MISSING'}",
        weight=1.0
    )
    
    check_format = re.findall(r'- \[✓\]', deep_content)
    add_check(
        "deep_audit_checkmark_format",
        len(check_format) >= 1,
        f"Safe item format '- [✓]' found {len(check_format)} time(s). Expected ≥1.",
        weight=1.5
    )

    # Check risk items section with [!] format
    has_risk_section = bool(re.search(r'###\s*⚠️\s*风险项', deep_content))
    add_check(
        "deep_audit_risk_section",
        has_risk_section,
        f"Risk items section '### ⚠️ 风险项' {'found' if has_risk_section else 'MISSING'}",
        weight=1.0
    )
    
    exclaim_format = re.findall(r'- \[!\]', deep_content)
    add_check(
        "deep_audit_exclaim_format",
        len(exclaim_format) >= 1,
        f"Risk item format '- [!]' found {len(exclaim_format)} time(s). Expected ≥1.",
        weight=1.5
    )

    # Check investment advice section
    has_invest = bool(re.search(r'###\s*💡\s*投资建议', deep_content))
    add_check(
        "deep_audit_investment_section",
        has_invest,
        f"Investment advice section '### 💡 投资建议' {'found' if has_invest else 'MISSING'}",
        weight=1.0
    )

    # Check project data section
    has_proj_data = bool(re.search(r'###\s*📈\s*项目数据', deep_content))
    add_check(
        "deep_audit_project_data_section",
        has_proj_data,
        f"Project data section '### 📈 项目数据' {'found' if has_proj_data else 'MISSING'}",
        weight=1.0
    )

    # DEEP MODE specific: Check for 深度分析 section (only present with --deep flag)
    has_deep_section = bool(re.search(r'###\s*🔬\s*深度分析', deep_content))
    add_check(
        "deep_audit_has_deep_analysis_section",
        has_deep_section,
        f"Deep analysis section '### 🔬 深度分析' {'found (--deep flag was used correctly)' if has_deep_section else 'MISSING — this section only appears with --deep flag'}",
        weight=3.0
    )

    # Check investment advice for high risk: should say 不建议投资
    if has_invest:
        has_no_invest = "不建议投资" in deep_content
        add_check(
            "deep_audit_high_risk_advice",
            has_no_invest,
            f"High-risk investment advice '不建议投资' {'found' if has_no_invest else 'MISSING — high risk projects should say 不建议投资'}",
            weight=2.0
        )

    # Check 建议仓位 and 止损位 fields
    has_position = "建议仓位" in deep_content
    has_stoploss = "止损位" in deep_content
    add_check(
        "deep_audit_investment_fields",
        has_position and has_stoploss,
        f"Investment fields: 建议仓位={'FOUND' if has_position else 'MISSING'}, 止损位={'FOUND' if has_stoploss else 'MISSING'}",
        weight=1.0
    )

else:
    for _ in range(10):
        add_check("deep_audit_content_check_skipped", False, "File missing, skipping content checks", weight=1.0)

# ============================================================
# FILE 2: comparison_report.md — Compare BetaFarm vs GammaPool
# ============================================================
cmp_file = find_file("comparison_report.md")
cmp_content = read_file(cmp_file) if cmp_file else None

add_check(
    "comparison_file_exists",
    cmp_file is not None and cmp_content is not None,
    f"File 'comparison_report.md' {'found at: ' + str(cmp_file) if cmp_file else 'NOT FOUND'}",
    weight=1.0
)

if cmp_content:
    # Check comparison header
    has_cmp_header = "对比审计报告" in cmp_content or "## 🔒 链上项目对比审计报告" in cmp_content
    add_check(
        "comparison_header",
        has_cmp_header,
        f"Comparison report header {'found' if has_cmp_header else 'MISSING'}",
        weight=1.5
    )

    # Both project names must appear
    has_betafarm = "BetaFarm" in cmp_content
    has_gammapool = "GammaPool" in cmp_content
    add_check(
        "comparison_both_projects_present",
        has_betafarm and has_gammapool,
        f"Project names in comparison: BetaFarm={'FOUND' if has_betafarm else 'MISSING'}, GammaPool={'FOUND' if has_gammapool else 'MISSING'}",
        weight=2.0
    )

    # Both risk scores present
    scores_found = re.findall(r'(\d+)/100（(低风险|中风险|高风险)）', cmp_content)
    add_check(
        "comparison_two_risk_scores",
        len(scores_found) >= 2,
        f"Found {len(scores_found)} risk score(s) in comparison report. Expected ≥ 2.",
        weight=2.0
    )

    # BetaFarm should be lower risk than GammaPool
    # BetaFarm: verified, LP 365d ≥180 (safe), team doxxed, top10=42.1 (safe), vol=95k (safe), social=20900 (safe) → 100 = 低风险
    # GammaPool: not verified(-25), no LP(-30), anon(-15), top10=91.2>70(-20), vol=1200<10k(-10), social=67<1000(-5) = 100-25-30-15-20-10-5= -5 → 0 → 高风险
    if len(scores_found) >= 2:
        score_vals = [(int(s[0]), s[1]) for s in scores_found]
        # Check GammaPool is high risk
        gammapool_high = any(v <= 30 and l == "高风险" for v, l in score_vals)
        betafarm_low = any(v >= 60 for v, l in score_vals)
        add_check(
            "comparison_gammapool_high_risk",
            gammapool_high,
            f"GammaPool should be 高风险 (score ≤ 30). Scores found: {score_vals}. {'CORRECT' if gammapool_high else 'INCORRECT'}",
            weight=2.0
        )
        add_check(
            "comparison_betafarm_better",
            betafarm_low,
            f"BetaFarm should have score ≥ 60. Found: {score_vals}. {'CORRECT' if betafarm_low else 'INCORRECT'}",
            weight=1.5
        )

    # [✓] and [!] format used in comparison
    safe_fmt = re.findall(r'- \[✓\]', cmp_content)
    risk_fmt = re.findall(r'- \[!\]', cmp_content)
    add_check(
        "comparison_item_formats",
        len(safe_fmt) >= 1 and len(risk_fmt) >= 1,
        f"Item formats in comparison: [✓] count={len(safe_fmt)}, [!] count={len(risk_fmt)}. Both must be ≥ 1.",
        weight=1.5
    )

    # Comparison table or data section
    has_data_table = "市值" in cmp_content and "交易量" in cmp_content
    add_check(
        "comparison_data_section",
        has_data_table,
        f"Data comparison section (市值 + 交易量) {'found' if has_data_table else 'MISSING'}",
        weight=1.0
    )

    # Winner recommendation present
    has_recommendation = "相对更优" in cmp_content or "综合投资建议" in cmp_content
    add_check(
        "comparison_recommendation",
        has_recommendation,
        f"Comparison recommendation section {'found' if has_recommendation else 'MISSING'}",
        weight=1.0
    )

else:
    for _ in range(8):
        add_check("comparison_content_check_skipped", False, "File missing, skipping content checks", weight=1.0)

# ============================================================
# FILE 3: batch_audit_report.md — Batch audit of all 5 projects
# ============================================================
batch_file = find_file("batch_audit_report.md")
batch_content = read_file(batch_file) if batch_file else None

add_check(
    "batch_file_exists",
    batch_file is not None and batch_content is not None,
    f"File 'batch_audit_report.md' {'found at: ' + str(batch_file) if batch_file else 'NOT FOUND'}",
    weight=1.0
)

if batch_content:
    # Check batch header
    has_batch_header = "批量" in batch_content and "审计报告" in batch_content
    add_check(
        "batch_header",
        has_batch_header,
        f"Batch report header containing '批量' and '审计报告' {'found' if has_batch_header else 'MISSING'}",
        weight=1.5
    )

    # All 5 projects must appear
    all_projects = ["AlphaSwap", "BetaFarm", "GammaPool", "DeltaToken", "EpsilonMoon"]
    missing = [p for p in all_projects if p not in batch_content]
    add_check(
        "batch_all_five_projects",
        len(missing) == 0,
        f"All 5 projects in batch: {'ALL PRESENT' if not missing else 'MISSING: ' + str(missing)}",
        weight=3.0
    )

    # At least 5 risk scores (one per project)
    batch_scores = re.findall(r'(\d+)/100（(低风险|中风险|高风险)）', batch_content)
    add_check(
        "batch_five_risk_scores",
        len(batch_scores) >= 5,
        f"Found {len(batch_scores)} risk score(s) in batch report. Expected ≥ 5.",
        weight=2.0
    )

    # Check [✓] and [!] used per-project
    safe_ct = len(re.findall(r'- \[✓\]', batch_content))
    risk_ct = len(re.findall(r'- \[!\]', batch_content))
    add_check(
        "batch_item_formats",
        safe_ct >= 3 and risk_ct >= 3,
        f"Batch item formats: [✓] count={safe_ct} (need ≥3), [!] count={risk_ct} (need ≥3).",
        weight=1.5
    )

    # DeltaToken should be 低风险 (verified, LP 720d, doxxed, top10=28.5, vol=420k, social=76k → 100 = 低风险)
    if len(batch_scores) >= 5:
        score_dict = {}
        # Try to map scores to projects by proximity
        for proj in all_projects:
            proj_pos = batch_content.find(proj)
            if proj_pos >= 0:
                nearby = batch_content[proj_pos:proj_pos+300]
                m = re.search(r'(\d+)/100（(低风险|中风险|高风险)）', nearby)
                if m:
                    score_dict[proj] = (int(m.group(1)), m.group(2))
        
        delta_ok = score_dict.get("DeltaToken", (0, ""))[1] == "低风险"
        gamma_ok = score_dict.get("GammaPool", (100, ""))[0] <= 30
        add_check(
            "batch_deltatoken_low_risk",
            delta_ok,
            f"DeltaToken risk level: expected 低风险, got: {score_dict.get('DeltaToken', 'NOT FOUND')}. {'CORRECT' if delta_ok else 'INCORRECT'}",
            weight=2.0
        )
        add_check(
            "batch_gammapool_high_risk",
            gamma_ok,
            f"GammaPool risk score: expected ≤ 30, got: {score_dict.get('GammaPool', 'NOT FOUND')}. {'CORRECT' if gamma_ok else 'INCORRECT'}",
            weight=1.5
        )

    # Batch used correct sub-sections (#### format for per-project)
    has_subsections = bool(re.search(r'####\s*(✅|⚠️|📈)', batch_content))
    add_check(
        "batch_subsection_format",
        has_subsections,
        f"Batch per-project subsections (#### ✅/⚠️/📈) {'found' if has_subsections else 'MISSING — batch mode uses #### for subsections'}",
        weight=1.0
    )

else:
    for _ in range(8):
        add_check("batch_content_check_skipped", False, "File missing, skipping content checks", weight=1.0)

# ============================================================
# FINAL SCORING
# ============================================================
final_score = round(total_score / max_score, 4) if max_score > 0 else 0.0
all_passed = all(c["passed"] for c in checks)

result = {
    "passed": all_passed and final_score >= 0.85,
    "score": final_score,
    "checks": checks
}

print(json.dumps(result, ensure_ascii=False, indent=2))