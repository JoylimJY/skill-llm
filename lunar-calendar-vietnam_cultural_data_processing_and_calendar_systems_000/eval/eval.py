#!/usr/bin/env python3
"""
Evaluation script for the Vietnamese wedding date consulting task.
Checks that wedding_date_report.json was created with correct, tool-derived values.
"""
import sys
import json
import subprocess
import os
from pathlib import Path

def run_calculator(mode, date_str, workspace, extra_args=None):
    """Run the amlich_calculator and return parsed JSON."""
    skill_dir = os.path.join(workspace, "lunar-calendar-vietnam")
    cmd = ["node", "scripts/amlich_calculator.js", mode, date_str]
    if extra_args:
        cmd.extend(extra_args)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=skill_dir, timeout=15)
        if result.returncode != 0:
            return None
        return json.loads(result.stdout)
    except Exception as e:
        return None

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    checks = []
    
    # --- Find the output file ---
    report_files = list(Path(workspace).rglob("wedding_date_report.json"))
    
    if not report_files:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "wedding_date_report.json not found anywhere in workspace"}]
        }))
        return
    
    report_path = report_files[0]
    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {report_path}"})
    
    # --- Parse the report ---
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": checks + [{"name": "file_parseable", "passed": False, "detail": f"JSON parse error: {e}"}]
        }))
        return
    
    checks.append({"name": "file_parseable", "passed": True, "detail": "Valid JSON"})
    
    # --- Compute ground truth using the tool ---
    # Client WP-001: Bride DOB solar 1995-03-15, Groom DOB solar 1993-07-22
    # Ceremony: lunar 10/6/2025 -> solar
    
    gt_bride_001 = run_calculator("--solar", "1995-03-15", workspace)
    gt_groom_001 = run_calculator("--solar", "1993-07-22", workspace)
    gt_ceremony_001 = run_calculator("--lunar", "2025-06-10", workspace)
    
    # Client WP-002: Bride DOB solar 1998-11-08, Groom DOB solar 1996-04-30
    # Ceremony: lunar 15/8/2025 -> solar
    gt_bride_002 = run_calculator("--solar", "1998-11-08", workspace)
    gt_groom_002 = run_calculator("--solar", "1996-04-30", workspace)
    gt_ceremony_002 = run_calculator("--lunar", "2025-08-15", workspace)
    
    # Client WP-003: Bride DOB solar 2000-02-29 (leap year!), Groom DOB solar 1997-06-14
    # Ceremony: lunar 3/11/2025 -> solar
    gt_bride_003 = run_calculator("--solar", "2000-02-29", workspace)
    gt_groom_003 = run_calculator("--solar", "1997-06-14", workspace)
    gt_ceremony_003 = run_calculator("--lunar", "2025-11-03", workspace)
    
    def find_client(report, client_id):
        """Find client entry in report by various possible structures."""
        if isinstance(report, list):
            for item in report:
                if isinstance(item, dict):
                    val = str(item.get("client_id", item.get("id", item.get("clientId", ""))))
                    if client_id.upper() in val.upper() or client_id.lower() in val.lower():
                        return item
        elif isinstance(report, dict):
            for key in ["clients", "data", "results", "weddings"]:
                if key in report and isinstance(report[key], list):
                    for item in report[key]:
                        val = str(item.get("client_id", item.get("id", item.get("clientId", ""))))
                        if client_id.upper() in val.upper() or client_id.lower() in val.lower():
                            return item
            # Try direct keys
            for key in report:
                if client_id.upper() in key.upper() or client_id.lower() in key.lower():
                    if isinstance(report[key], dict):
                        return report[key]
        return None
    
    def extract_text(data, keys):
        """Recursively search for any of the given keys in nested dict/list."""
        if isinstance(data, dict):
            for k, v in data.items():
                if any(key.lower() in k.lower() for key in keys):
                    return str(v)
                result = extract_text(v, keys)
                if result:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = extract_text(item, keys)
                if result:
                    return result
        return None
    
    def report_str(report):
        return json.dumps(report).lower()
    
    report_text = report_str(report)
    
    # ====================== CHECK 1: WP-001 Zodiac ======================
    # Bride born 1995 -> lunar year from tool
    # Groom born 1993 -> lunar year from tool
    passed_001_zodiac = False
    detail_001_zodiac = "Could not verify WP-001 zodiac data"
    
    if gt_bride_001 and gt_groom_001:
        bride_con_giap = gt_bride_001.get("canChi", {}).get("conGiap", "").lower()
        groom_con_giap = gt_groom_001.get("canChi", {}).get("conGiap", "").lower()
        bride_can_chi = gt_bride_001.get("canChi", {}).get("year", "").lower()
        groom_can_chi = gt_groom_001.get("canChi", {}).get("year", "").lower()
        
        bride_found = bride_con_giap in report_text or bride_can_chi in report_text
        groom_found = groom_con_giap in report_text or groom_can_chi in report_text
        
        passed_001_zodiac = bride_found and groom_found
        detail_001_zodiac = (f"Bride zodiac: '{bride_con_giap}'/'{bride_can_chi}' {'found' if bride_found else 'NOT FOUND'}, "
                             f"Groom zodiac: '{groom_con_giap}'/'{groom_can_chi}' {'found' if groom_found else 'NOT FOUND'}")
    
    checks.append({"name": "wp001_zodiac_correct", "passed": passed_001_zodiac, "detail": detail_001_zodiac})
    
    # ====================== CHECK 2: WP-001 Ceremony Solar Date ======================
    passed_001_ceremony = False
    detail_001_ceremony = "Could not verify WP-001 ceremony solar date"
    
    if gt_ceremony_001:
        solar_formatted = gt_ceremony_001.get("solar", {}).get("formatted", "")
        s_day = str(gt_ceremony_001.get("solar", {}).get("day", ""))
        s_month = str(gt_ceremony_001.get("solar", {}).get("month", ""))
        s_year = str(gt_ceremony_001.get("solar", {}).get("year", ""))
        
        date_found = (solar_formatted in report_str(report) or 
                     (s_day in report_text and s_month in report_text and s_year in report_text and "2025" in report_text))
        
        passed_001_ceremony = date_found
        detail_001_ceremony = f"Expected ceremony solar date {solar_formatted}, {'found' if date_found else 'NOT FOUND'} in report"
    
    checks.append({"name": "wp001_ceremony_solar_date", "passed": passed_001_ceremony, "detail": detail_001_ceremony})
    
    # ====================== CHECK 3: WP-002 Zodiac ======================
    passed_002_zodiac = False
    detail_002_zodiac = "Could not verify WP-002 zodiac data"
    
    if gt_bride_002 and gt_groom_002:
        bride_con_giap = gt_bride_002.get("canChi", {}).get("conGiap", "").lower()
        groom_con_giap = gt_groom_002.get("canChi", {}).get("conGiap", "").lower()
        bride_can_chi = gt_bride_002.get("canChi", {}).get("year", "").lower()
        groom_can_chi = gt_groom_002.get("canChi", {}).get("year", "").lower()
        
        bride_found = bride_con_giap in report_text or bride_can_chi in report_text
        groom_found = groom_con_giap in report_text or groom_can_chi in report_text
        
        passed_002_zodiac = bride_found and groom_found
        detail_002_zodiac = (f"Bride zodiac: '{bride_con_giap}'/'{bride_can_chi}' {'found' if bride_found else 'NOT FOUND'}, "
                             f"Groom zodiac: '{groom_con_giap}'/'{groom_can_chi}' {'found' if groom_found else 'NOT FOUND'}")
    
    checks.append({"name": "wp002_zodiac_correct", "passed": passed_002_zodiac, "detail": detail_002_zodiac})
    
    # ====================== CHECK 4: WP-002 Ceremony Solar Date ======================
    passed_002_ceremony = False
    detail_002_ceremony = "Could not verify WP-002 ceremony solar date"
    
    if gt_ceremony_002:
        solar_formatted = gt_ceremony_002.get("solar", {}).get("formatted", "")
        s_day = str(gt_ceremony_002.get("solar", {}).get("day", ""))
        s_month = str(gt_ceremony_002.get("solar", {}).get("month", ""))
        s_year = str(gt_ceremony_002.get("solar", {}).get("year", ""))
        
        date_found = (solar_formatted in report_str(report) or
                     (s_day in report_text and s_month in report_text and s_year in report_text))
        
        passed_002_ceremony = date_found
        detail_002_ceremony = f"Expected ceremony solar date {solar_formatted}, {'found' if date_found else 'NOT FOUND'} in report"
    
    checks.append({"name": "wp002_ceremony_solar_date", "passed": passed_002_ceremony, "detail": detail_002_ceremony})
    
    # ====================== CHECK 5: WP-003 Leap Year Bride (Feb 29, 2000) ======================
    passed_003_bride = False
    detail_003_bride = "Could not verify WP-003 bride zodiac (leap year birthdate)"
    
    if gt_bride_003:
        bride_con_giap = gt_bride_003.get("canChi", {}).get("conGiap", "").lower()
        bride_can_chi = gt_bride_003.get("canChi", {}).get("year", "").lower()
        bride_lunar_year = str(gt_bride_003.get("lunar", {}).get("year", ""))
        
        bride_found = (bride_con_giap in report_text or bride_can_chi in report_text or
                      bride_lunar_year in report_text)
        
        passed_003_bride = bride_found
        detail_003_bride = (f"Bride (born 2000-02-29) zodiac: '{bride_con_giap}'/'{bride_can_chi}' "
                           f"{'found' if bride_found else 'NOT FOUND'} in report")
    
    checks.append({"name": "wp003_leap_year_bride_zodiac", "passed": passed_003_bride, "detail": detail_003_bride})
    
    # ====================== CHECK 6: WP-003 Ceremony Solar Date ======================
    passed_003_ceremony = False
    detail_003_ceremony = "Could not verify WP-003 ceremony solar date"
    
    if gt_ceremony_003:
        solar_formatted = gt_ceremony_003.get("solar", {}).get("formatted", "")
        s_day = str(gt_ceremony_003.get("solar", {}).get("day", ""))
        s_month = str(gt_ceremony_003.get("solar", {}).get("month", ""))
        s_year = str(gt_ceremony_003.get("solar", {}).get("year", ""))
        
        date_found = (solar_formatted in report_str(report) or
                     (s_day in report_text and s_month in report_text and s_year in report_text))
        
        passed_003_ceremony = date_found
        detail_003_ceremony = f"Expected ceremony solar date {solar_formatted}, {'found' if date_found else 'NOT FOUND'} in report"
    
    checks.append({"name": "wp003_ceremony_solar_date", "passed": passed_003_ceremony, "detail": detail_003_ceremony})
    
    # ====================== CHECK 7: Auspicious hours present ======================
    # At least one ceremony day should have auspicious hours listed
    passed_auspicious = False
    detail_auspicious = "Auspicious hours not found in report"
    
    auspicious_keywords = ["tý", "sửu", "dần", "mão", "thìn", "tỵ", "ngọ", "mùi", "thân", "dậu", "tuất", "hợi",
                          "hoàng đạo", "auspicious", "gio", "giờ"]
    for kw in auspicious_keywords:
        if kw in report_text:
            passed_auspicious = True
            detail_auspicious = f"Found auspicious hour indicator '{kw}' in report"
            break
    
    checks.append({"name": "auspicious_hours_present", "passed": passed_auspicious, "detail": detail_auspicious})
    
    # ====================== CHECK 8: All 3 clients present ======================
    passed_all_clients = False
    clients_found = sum([
        "wp-001" in report_text or "wp001" in report_text or "weddingplan-001" in report_text or "lan" in report_text,
        "wp-002" in report_text or "wp002" in report_text or "hoa" in report_text,
        "wp-003" in report_text or "wp003" in report_text or "mai" in report_text,
    ])
    passed_all_clients = clients_found >= 3
    detail_all_clients = f"Found {clients_found}/3 client entries in report"
    
    checks.append({"name": "all_three_clients_present", "passed": passed_all_clients, "detail": detail_all_clients})
    
    # ====================== SCORE ======================
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = passed_count / total
    overall_passed = score >= 0.75  # Need at least 75% to pass
    
    print(json.dumps({
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()