import sys
import json
import subprocess
from pathlib import Path

workspace = Path(sys.argv[1])

checks = []
passed_all = True

def add_check(name, passed, detail):
    global passed_all
    checks.append({"name": name, "passed": passed, "detail": detail})
    if not passed:
        passed_all = False

# ── Locate the output report file ────────────────────────────────────────────
report_files = list(workspace.rglob("macro_briefing_report.json"))

if not report_files:
    add_check("report_file_exists", False, "macro_briefing_report.json not found anywhere in workspace")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

report_path = report_files[0]
add_check("report_file_exists", True, f"Found at {report_path}")

# ── Load the report ──────────────────────────────────────────────────────────
try:
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    add_check("report_valid_json", True, "File is valid JSON")
except Exception as e:
    add_check("report_valid_json", False, f"JSON parse error: {e}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# ── Check top-level structure: must have 'china' and 'us' sections ────────────
has_china = isinstance(report.get("china"), dict)
has_us = isinstance(report.get("us"), dict)
add_check("report_has_china_section", has_china, 
          "Top-level 'china' key exists and is a dict" if has_china else "Missing or invalid 'china' section")
add_check("report_has_us_section", has_us,
          "Top-level 'us' key exists and is a dict" if has_us else "Missing or invalid 'us' section")

if not has_china or not has_us:
    print(json.dumps({"passed": False, "score": 0.3, "checks": checks}))
    sys.exit(0)

china = report["china"]
us = report["us"]

# ── China CPI check ──────────────────────────────────────────────────────────
# Must come from economic-china-cpi-monthly (not a stub or fabricated value)
# Mock data: latest date=2024-03, yoy=-1.0 or value=0.1
cpi_found = False
cpi_detail = "No CPI data found in china section"
try:
    cpi_data = china.get("cpi") or china.get("CPI") or china.get("cpi_monthly") or china.get("cpi_data")
    if cpi_data:
        cpi_str = json.dumps(cpi_data)
        # Check for mock-data values
        if "2024-03" in cpi_str or "-1.0" in cpi_str or "0.1" in cpi_str or "2024-02" in cpi_str:
            cpi_found = True
            cpi_detail = "CPI data present with expected mock values"
        else:
            cpi_detail = f"CPI key found but values don't match mock data: {cpi_str[:200]}"
    else:
        # Try flat structure
        report_str = json.dumps(china)
        if "2024-03" in report_str and ("-1.0" in report_str or "0.1" in report_str):
            cpi_found = True
            cpi_detail = "CPI mock values detected in china section"
except Exception as e:
    cpi_detail = f"Error checking CPI: {e}"
add_check("china_cpi_data_present", cpi_found, cpi_detail)

# ── China PMI check ──────────────────────────────────────────────────────────
# Mock data: latest 2024-03, manufacturing=50.8, non_manufacturing=53.0
pmi_found = False
pmi_detail = "No PMI data found in china section"
try:
    pmi_data = china.get("pmi") or china.get("PMI") or china.get("pmi_monthly") or china.get("pmi_data")
    if pmi_data:
        pmi_str = json.dumps(pmi_data)
        if "50.8" in pmi_str or "53.0" in pmi_str or ("2024-03" in pmi_str and "manufacturing" in pmi_str.lower()):
            pmi_found = True
            pmi_detail = "PMI data present with expected mock values"
        else:
            pmi_detail = f"PMI key found but values don't match: {pmi_str[:200]}"
    else:
        china_str = json.dumps(china)
        if "50.8" in china_str or "53.0" in china_str:
            pmi_found = True
            pmi_detail = "PMI mock values detected in china section"
except Exception as e:
    pmi_detail = f"Error checking PMI: {e}"
add_check("china_pmi_data_present", pmi_found, pmi_detail)

# ── China Money Supply (M0/M1/M2) check ─────────────────────────────────────
# Mock data: 2024-03, m0=11.7, m1=8.7, m2=308.7
money_found = False
money_detail = "No money supply data found in china section"
try:
    money_data = (china.get("money_supply") or china.get("M2") or china.get("m2") or 
                  china.get("money") or china.get("currency") or china.get("money_supply_monthly"))
    if money_data:
        m_str = json.dumps(money_data)
        if "11.7" in m_str or "308.7" in m_str or "8.7" in m_str:
            money_found = True
            money_detail = "Money supply data present with expected mock values"
        else:
            money_detail = f"Money supply key found but values don't match: {m_str[:200]}"
    else:
        china_str = json.dumps(china)
        if "11.7" in china_str or "308.7" in china_str or "8.7" in china_str:
            money_found = True
            money_detail = "Money supply mock values detected in china section"
except Exception as e:
    money_detail = f"Error checking money supply: {e}"
add_check("china_money_supply_data_present", money_found, money_detail)

# ── China Customs Trade check ────────────────────────────────────────────────
# Mock data: 2024-03, exports=279.7, imports=220.8, balance=58.9
trade_found = False
trade_detail = "No customs trade data found in china section"
try:
    trade_data = (china.get("customs_trade") or china.get("trade") or china.get("imports_exports") or
                  china.get("customs") or china.get("trade_monthly") or china.get("customs_trade_monthly"))
    if trade_data:
        t_str = json.dumps(trade_data)
        if "279.7" in t_str or "220.8" in t_str or "58.9" in t_str:
            trade_found = True
            trade_detail = "Trade data present with expected mock values"
        else:
            trade_detail = f"Trade key found but values don't match: {t_str[:200]}"
    else:
        china_str = json.dumps(china)
        if "279.7" in china_str or "220.8" in china_str or "58.9" in china_str:
            trade_found = True
            trade_detail = "Trade mock values detected in china section"
except Exception as e:
    trade_detail = f"Error checking customs trade: {e}"
add_check("china_customs_trade_data_present", trade_found, trade_detail)

# ── China LPR check ──────────────────────────────────────────────────────────
# Mock data: 2024-03, lpr_1y=3.45, lpr_5y=3.95
lpr_found = False
lpr_detail = "No LPR data found in china section"
try:
    lpr_data = china.get("lpr") or china.get("LPR") or china.get("lpr_monthly") or china.get("lpr_data")
    if lpr_data:
        l_str = json.dumps(lpr_data)
        if "3.45" in l_str or "3.95" in l_str:
            lpr_found = True
            lpr_detail = "LPR data present with expected mock values"
        else:
            lpr_detail = f"LPR key found but values don't match: {l_str[:200]}"
    else:
        china_str = json.dumps(china)
        if "3.45" in china_str or ("3.95" in china_str):
            lpr_found = True
            lpr_detail = "LPR mock values detected in china section"
except Exception as e:
    lpr_detail = f"Error checking LPR: {e}"
add_check("china_lpr_data_present", lpr_found, lpr_detail)

# ── US CPI mom check ─────────────────────────────────────────────────────────
# Must use --type cpi-mom; mock: 2024-03, value=0.4
us_cpi_found = False
us_cpi_detail = "No US CPI mom data found in us section"
try:
    us_cpi = (us.get("cpi_mom") or us.get("cpi-mom") or us.get("cpi") or 
              us.get("CPI") or us.get("us_cpi_mom"))
    if us_cpi:
        uc_str = json.dumps(us_cpi)
        if "0.4" in uc_str and ("2024-03" in uc_str or "2024-02" in uc_str):
            us_cpi_found = True
            us_cpi_detail = "US CPI mom data present with expected mock values"
        else:
            us_cpi_detail = f"US CPI key found but values don't match: {uc_str[:200]}"
    else:
        us_str = json.dumps(us)
        # 0.4 appears in multiple indicators, combine with date check
        if "0.4" in us_str and "2024-03" in us_str:
            us_cpi_found = True
            us_cpi_detail = "US CPI mock values (0.4, 2024-03) detected in us section"
except Exception as e:
    us_cpi_detail = f"Error checking US CPI: {e}"
add_check("us_cpi_mom_data_present", us_cpi_found, us_cpi_detail)

# ── US Nonfarm Payroll check ──────────────────────────────────────────────────
# Must use --type nonfarm-payroll; mock: 2024-03, value=303
us_nonfarm_found = False
us_nonfarm_detail = "No US nonfarm payroll data found in us section"
try:
    nonfarm_data = (us.get("nonfarm_payroll") or us.get("nonfarm-payroll") or
                    us.get("nonfarm") or us.get("nonfarm_payroll_monthly"))
    if nonfarm_data:
        n_str = json.dumps(nonfarm_data)
        if "303" in n_str or "275" in n_str or "256" in n_str:
            us_nonfarm_found = True
            us_nonfarm_detail = "Nonfarm payroll data present with expected mock values"
        else:
            us_nonfarm_detail = f"Nonfarm key found but values don't match: {n_str[:200]}"
    else:
        us_str = json.dumps(us)
        if "303" in us_str or ("275" in us_str and "256" in us_str):
            us_nonfarm_found = True
            us_nonfarm_detail = "Nonfarm payroll mock values detected in us section"
except Exception as e:
    us_nonfarm_detail = f"Error checking nonfarm: {e}"
add_check("us_nonfarm_payroll_data_present", us_nonfarm_found, us_nonfarm_detail)

# ── US Fed Funds Rate check ───────────────────────────────────────────────────
# Must use --type fed-funds-rate-upper; mock: 2024-03, value=5.50
us_fed_found = False
us_fed_detail = "No US fed funds rate data found in us section"
try:
    fed_data = (us.get("fed_funds_rate") or us.get("fed-funds-rate-upper") or
                us.get("fed_rate") or us.get("fed_funds_rate_upper") or
                us.get("federal_funds_rate"))
    if fed_data:
        f_str = json.dumps(fed_data)
        if "5.5" in f_str or "5.50" in f_str:
            us_fed_found = True
            us_fed_detail = "Fed funds rate data present with expected mock values"
        else:
            us_fed_detail = f"Fed rate key found but values don't match: {f_str[:200]}"
    else:
        us_str = json.dumps(us)
        if "5.5" in us_str or "5.50" in us_str:
            us_fed_found = True
            us_fed_detail = "Fed funds rate mock values (5.5) detected in us section"
except Exception as e:
    us_fed_detail = f"Error checking fed rate: {e}"
add_check("us_fed_funds_rate_data_present", us_fed_found, us_fed_detail)

# ── US Unemployment Rate check ────────────────────────────────────────────────
# Must use --type unemployment-rate; mock: 2024-03, value=3.8
us_unemp_found = False
us_unemp_detail = "No US unemployment rate data found in us section"
try:
    unemp_data = (us.get("unemployment_rate") or us.get("unemployment-rate") or
                  us.get("unemployment") or us.get("unemployment_monthly"))
    if unemp_data:
        u_str = json.dumps(unemp_data)
        if "3.8" in u_str or "3.9" in u_str or "3.7" in u_str:
            us_unemp_found = True
            us_unemp_detail = "Unemployment rate data present with expected mock values"
        else:
            us_unemp_detail = f"Unemployment key found but values don't match: {u_str[:200]}"
    else:
        us_str = json.dumps(us)
        if "3.8" in us_str and "3.9" in us_str:
            us_unemp_found = True
            us_unemp_detail = "Unemployment mock values detected in us section"
except Exception as e:
    us_unemp_detail = f"Error checking unemployment: {e}"
add_check("us_unemployment_rate_data_present", us_unemp_found, us_unemp_detail)

# ── US Core CPI yoy check ─────────────────────────────────────────────────────
# Must use --type core-cpi-yoy; mock: 2024-03, value=3.8
us_core_cpi_found = False
us_core_cpi_detail = "No US core CPI yoy data found in us section"
try:
    core_cpi = (us.get("core_cpi_yoy") or us.get("core-cpi-yoy") or
                us.get("core_cpi") or us.get("core_cpi_annual"))
    if core_cpi:
        cc_str = json.dumps(core_cpi)
        # core-cpi-yoy mock has 3.8, 3.8, 3.9
        if "3.8" in cc_str or "3.9" in cc_str:
            us_core_cpi_found = True
            us_core_cpi_detail = "Core CPI yoy data present with expected mock values"
        else:
            us_core_cpi_detail = f"Core CPI key found but values don't match: {cc_str[:200]}"
    else:
        us_str = json.dumps(us)
        # 3.8 could be unemployment too; look for "core" context or both 3.8 and 3.9
        if "3.8" in us_str and "3.9" in us_str and len(us_str) > 200:
            us_core_cpi_found = True
            us_core_cpi_detail = "Core CPI yoy values (3.8/3.9) detected alongside other US data"
except Exception as e:
    us_core_cpi_detail = f"Error checking core CPI yoy: {e}"
add_check("us_core_cpi_yoy_data_present", us_core_cpi_found, us_core_cpi_detail)

# ── Proprietary trap check: correct sub-skill naming ─────────────────────────
# The report MUST NOT contain evidence of wrong sub-skill names (the trap names from config)
wrong_names_used = False
wrong_detail = "No evidence of wrong sub-skill names"
try:
    report_str = json.dumps(report)
    wrong_keys = ["economic-china-m2-monthly", "economic-us-cpi-monthly", 
                  "economic-us-nonfarm-monthly", "economic-china-cpi",
                  "economic-china-pmi"]
    found_wrong = [k for k in wrong_keys if k in report_str]
    if found_wrong:
        wrong_names_used = True
        wrong_detail = f"Report references deprecated/wrong sub-skill names: {found_wrong}"
    else:
        wrong_detail = "No deprecated sub-skill names found in report"
except Exception as e:
    wrong_detail = f"Error checking sub-skill names: {e}"
# This is a negative check: passing means wrong names NOT used
add_check("no_wrong_subskill_names_in_report", not wrong_names_used, wrong_detail)

# ── Scoring ──────────────────────────────────────────────────────────────────
check_weights = {
    "report_file_exists": 0.05,
    "report_valid_json": 0.05,
    "report_has_china_section": 0.03,
    "report_has_us_section": 0.03,
    "china_cpi_data_present": 0.10,
    "china_pmi_data_present": 0.10,
    "china_money_supply_data_present": 0.10,
    "china_customs_trade_data_present": 0.09,
    "china_lpr_data_present": 0.09,
    "us_cpi_mom_data_present": 0.08,
    "us_nonfarm_payroll_data_present": 0.08,
    "us_fed_funds_rate_data_present": 0.08,
    "us_unemployment_rate_data_present": 0.07,
    "us_core_cpi_yoy_data_present": 0.07,
    "no_wrong_subskill_names_in_report": 0.08,
}

score = sum(
    check_weights.get(c["name"], 0.0)
    for c in checks
    if c["passed"]
)

final_passed = score >= 0.75

print(json.dumps({
    "passed": final_passed,
    "score": round(score, 4),
    "checks": checks
}, ensure_ascii=False, indent=2))