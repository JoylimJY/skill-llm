import sys
import json
from pathlib import Path

def evaluate(workspace: str):
    ws = Path(workspace)
    checks = []

    # ── Locate the output file ───────────────────────────────────────────────
    candidates = list(ws.rglob("weekly_macro_report.json"))
    file_found = len(candidates) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found {len(candidates)} file(s) named 'weekly_macro_report.json'" if file_found
                  else "File 'weekly_macro_report.json' not found anywhere in workspace"
    })
    if not file_found:
        return {"passed": False, "score": 0.0, "checks": checks}

    report_path = candidates[0]
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
    except Exception as e:
        checks.append({"name": "json_parseable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "json_parseable", "passed": True, "detail": "Valid JSON"})

    # ── Check 1: Section 1 — global_overview data present ───────────────────
    section1_keys = ["global_overview", "global_market", "全球市场", "global"]
    sec1 = None
    for k in section1_keys:
        if k in report:
            sec1 = report[k]
            break
    # Also accept nested under a "sections" list or similar structures
    if sec1 is None:
        # Try iterating values for dict-like objects containing market data
        for v in report.values():
            if isinstance(v, dict) and any(kw in str(v).lower() for kw in ["市场", "market", "global"]):
                sec1 = v
                break
            if isinstance(v, list) and any("市场" in str(item) or "market" in str(item).lower() for item in v):
                sec1 = v
                break

    has_global = sec1 is not None and len(str(sec1)) > 20
    checks.append({
        "name": "section1_global_overview",
        "passed": has_global,
        "detail": f"Global overview section found and non-empty: {has_global}. "
                  f"Top-level keys: {list(report.keys())[:10]}"
    })

    # ── Check 2: Section 2 — GDP + CPI + PMI data all present ───────────────
    report_str = json.dumps(report, ensure_ascii=False)
    has_gdp = "GDP" in report_str or "gdp" in report_str.lower() or "国内生产总值" in report_str
    has_cpi = "CPI" in report_str or "cpi" in report_str.lower() or "居民消费" in report_str
    has_pmi = "PMI" in report_str or "pmi" in report_str.lower() or "采购经理"  in report_str

    checks.append({
        "name": "section2_gdp_present",
        "passed": has_gdp,
        "detail": f"GDP data found in report: {has_gdp}"
    })
    checks.append({
        "name": "section2_cpi_present",
        "passed": has_cpi,
        "detail": f"CPI data found in report: {has_cpi}"
    })
    checks.append({
        "name": "section2_pmi_present",
        "passed": has_pmi,
        "detail": f"PMI data found in report: {has_pmi}"
    })

    macro_all_present = has_gdp and has_cpi and has_pmi
    checks.append({
        "name": "section2_macro_data_complete",
        "passed": macro_all_present,
        "detail": f"All three macro indicators (GDP/CPI/PMI) present: {macro_all_present}"
    })

    # ── Check 3: Section 3 — industry rotation data present ─────────────────
    has_industry = (
        "industry" in report_str.lower()
        or "行业" in report_str
        or "板块" in report_str
        or "sector" in report_str.lower()
    )
    checks.append({
        "name": "section3_industry_rotation",
        "passed": has_industry,
        "detail": f"Industry/sector rotation data found: {has_industry}"
    })

    # ── Check 4: Section 4 — outlook / risk section present ─────────────────
    has_outlook = (
        "outlook" in report_str.lower()
        or "展望" in report_str
        or "risk" in report_str.lower()
        or "风险" in report_str
        or "下周" in report_str
        or "forecast" in report_str.lower()
    )
    checks.append({
        "name": "section4_outlook_and_risk",
        "passed": has_outlook,
        "detail": f"Outlook/risk section found: {has_outlook}"
    })

    # ── Check 5: Four-section structure (weekly report schema) ───────────────
    # Must have at least 4 distinct top-level keys or a structured list of 4 sections
    has_four_sections = False
    if isinstance(report, dict) and len(report) >= 4:
        has_four_sections = True
    elif isinstance(report, dict):
        # Accept if there's a nested "sections" list with >=4 entries
        for v in report.values():
            if isinstance(v, list) and len(v) >= 4:
                has_four_sections = True
                break
            if isinstance(v, dict) and len(v) >= 4:
                has_four_sections = True
                break

    checks.append({
        "name": "weekly_report_four_section_structure",
        "passed": has_four_sections,
        "detail": f"Report has ≥4 top-level keys or nested sections: {has_four_sections}. "
                  f"Top-level key count: {len(report) if isinstance(report, dict) else 'N/A'}"
    })

    # ── Check 6: Report type explicitly indicates 'weekly' ───────────────────
    is_weekly = (
        "weekly" in report_str.lower()
        or "周报" in report_str
        or "week" in report_str.lower()
        or "宏观周报" in report_str
    )
    checks.append({
        "name": "report_type_is_weekly",
        "passed": is_weekly,
        "detail": f"Report is identified as a weekly macro report: {is_weekly}"
    })

    # ── Scoring ──────────────────────────────────────────────────────────────
    critical_checks = [
        "output_file_exists",
        "json_parseable",
        "section2_macro_data_complete",
        "section3_industry_rotation",
        "section4_outlook_and_risk",
        "weekly_report_four_section_structure",
    ]
    bonus_checks = [
        "section1_global_overview",
        "report_type_is_weekly",
    ]

    critical_passed = sum(1 for c in checks if c["name"] in critical_checks and c["passed"])
    bonus_passed = sum(1 for c in checks if c["name"] in bonus_checks and c["passed"])

    score = (critical_passed / len(critical_checks)) * 0.85 + (bonus_passed / len(bonus_checks)) * 0.15
    all_critical = critical_passed == len(critical_checks)

    return {
        "passed": all_critical,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))