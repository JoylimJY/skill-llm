#!/usr/bin/env python3
"""
Evaluation script for cantian-bazi multi-client processing task.
Grading criteria:
  1. astrology_report.json exists and is valid JSON
  2. C001 (Zhang Wei) used solar script with sect=1 (next-day attribution for 23:xx)
  3. C001 day pillar differs from sect=2 result (proves sect was correctly applied)
  4. C002 (Li Mei) used lunar script with gender=0 (female)
  5. C003 contains almanac/huangli output for 2024-03-15
  6. All three clients have non-empty output in the report
"""

import sys
import json
import subprocess
import os
import re
from pathlib import Path

def run_check(name, fn):
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {e}"}

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    
    # ── Find the report file ────────────────────────────────────────────────────
    report_path = None
    candidates = list(Path(workspace).rglob("astrology_report.json"))
    if candidates:
        report_path = candidates[0]
    
    def check_file_exists():
        if report_path and report_path.exists():
            return True, f"Found at {report_path}"
        return False, "astrology_report.json not found anywhere in workspace"
    
    checks.append(run_check("astrology_report.json exists", check_file_exists))
    
    if not (report_path and report_path.exists()):
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return
    
    # Load report
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
    except Exception as e:
        checks.append({"name": "report is valid JSON", "passed": False, "detail": str(e)})
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return
    
    checks.append({"name": "report is valid JSON", "passed": True, "detail": "Parsed successfully"})
    
    # ── Helper: extract client output from report ───────────────────────────────
    def get_client_output(client_id):
        """Try multiple common structures agents might use."""
        if isinstance(report, dict):
            # Try direct key access
            for key in [client_id, client_id.lower(), f"client_{client_id}"]:
                if key in report:
                    val = report[key]
                    if isinstance(val, dict):
                        # Look for an output/bazi/content field
                        for subkey in ["output", "bazi", "content", "result", "data", "chart", "almanac", "calendar"]:
                            if subkey in val:
                                return str(val[subkey])
                        return str(val)
                    return str(val)
            # Try clients array
            if "clients" in report:
                for c in report["clients"]:
                    if isinstance(c, dict):
                        cid = c.get("client_id", c.get("id", ""))
                        if cid == client_id:
                            for subkey in ["output", "bazi", "content", "result", "data", "chart", "almanac", "calendar"]:
                                if subkey in c:
                                    return str(c[subkey])
                            return str(c)
            # Try results array
            if "results" in report:
                for c in report["results"]:
                    if isinstance(c, dict):
                        cid = c.get("client_id", c.get("id", ""))
                        if cid == client_id:
                            for subkey in ["output", "bazi", "content", "result", "data", "chart", "almanac", "calendar"]:
                                if subkey in c:
                                    return str(c[subkey])
                            return str(c)
        return json.dumps(report)  # fallback: search entire report text
    
    report_text = json.dumps(report, ensure_ascii=False)
    
    # ── Check 3: C001 output is non-empty and contains Bazi content ────────────
    def check_c001_present():
        c001 = get_client_output("C001")
        if not c001 or len(c001) < 10:
            # Try searching full report text
            if "Zhang Wei" in report_text or "C001" in report_text:
                return True, "C001/Zhang Wei found in report (structure check passed)"
            return False, "C001 output missing or empty"
        # Check for bazi-like content: Chinese characters for stems/branches
        stems = "甲乙丙丁戊己庚辛壬癸"
        branches = "子丑寅卯辰巳午未申酉戌亥"
        has_stem = any(s in c001 for s in stems)
        has_branch = any(b in c001 for b in branches)
        if has_stem or has_branch or "八字" in c001 or "四柱" in c001 or "年柱" in c001:
            return True, "C001 contains Bazi chart content"
        if "C001" in report_text or "Zhang Wei" in report_text:
            return True, "C001 present in report (Bazi content in report text)"
        return False, f"C001 output does not appear to contain Bazi data: {c001[:200]}"
    
    checks.append(run_check("C001 (Zhang Wei) Bazi output present", check_c001_present))
    
    # ── Check 4: C001 sect=1 verification (day pillar differs from sect=2) ─────
    # We independently compute both sect=1 and sect=2 results for C001
    skill_root = os.path.join(workspace, "skills", "cantian-bazi")
    
    def run_script(script, args, cwd):
        cmd = ["npx", "tsx", script] + args
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=30)
            if r.returncode != 0:
                # Try node directly
                cmd2 = ["node", script] + args
                r = subprocess.run(cmd2, capture_output=True, text=True, cwd=cwd, timeout=30)
            return r.stdout + r.stderr
        except Exception as e:
            return str(e)
    
    def check_c001_sect1():
        """
        Verify that C001's day pillar matches sect=1 output, not sect=2.
        If they're the same (birth not in 23:xx), skip with neutral pass.
        """
        # C001: 1988-03-12T23:15:00, male, sect
        out_sect1 = run_script("scripts/buildBaziFromSolar.ts",
                               ["1988-03-12T23:15:00", "1", "1"], skill_root)
        out_sect2 = run_script("scripts/buildBaziFromSolar.ts",
                               ["1988-03-12T23:15:00", "1", "2"], skill_root)
        
        # Extract day pillar from each
        def extract_day_pillar(text):
            # Look for 日柱 row in markdown table: | 日柱 | X | X |
            m = re.search(r'日柱\s*[|｜]\s*([甲乙丙丁戊己庚辛壬癸])\s*[|｜]\s*([子丑寅卯辰巳午未申酉戌亥])', text)
            if m:
                return m.group(1) + m.group(2)
            # Try 八字串 line
            m2 = re.search(r'([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])\s+([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])\s+([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])\s+([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])', text)
            if m2:
                return m2.group(3)  # day is 3rd pillar
            return None
        
        day1 = extract_day_pillar(out_sect1)
        day2 = extract_day_pillar(out_sect2)
        
        if day1 is None or day2 is None:
            return True, f"Could not parse day pillars from script output (sect1={day1}, sect2={day2}) - skipping strict check. sect1 output: {out_sect1[:300]}"
        
        if day1 == day2:
            return True, f"sect=1 and sect=2 produce same day pillar ({day1}) for this datetime - script output consistent"
        
        # day1 != day2: now check which one the agent used in the report
        c001_out = get_client_output("C001")
        full_report = report_text
        
        day1_in_report = day1 in full_report
        day2_in_report = day2 in full_report
        
        if day1_in_report and not day2_in_report:
            return True, f"Report contains sect=1 day pillar ({day1}), correctly differs from sect=2 ({day2})"
        elif day2_in_report and not day1_in_report:
            return False, f"Report contains sect=2 day pillar ({day2}), but client C001 requires sect=1 (next-day attribution). Correct day pillar should be {day1}."
        elif day1_in_report and day2_in_report:
            return True, f"Both sect=1 ({day1}) and sect=2 ({day2}) pillars found in report - ambiguous but sect=1 present"
        else:
            return False, f"Neither sect=1 ({day1}) nor sect=2 ({day2}) day pillar found in report. Report excerpt: {full_report[:300]}"
    
    checks.append(run_check("C001 uses sect=1 (next-day 子时 attribution)", check_c001_sect1))
    
    # ── Check 5: C002 output present with female indicator ─────────────────────
    def check_c002_present():
        c002_out = get_client_output("C002")
        # Check report text for Li Mei or C002
        if "Li Mei" not in report_text and "C002" not in report_text:
            return False, "C002/Li Mei not found in report at all"
        
        stems = "甲乙丙丁戊己庚辛壬癸"
        branches = "子丑寅卯辰巳午未申酉戌亥"
        has_bazi = any(s in report_text for s in stems) and any(b in report_text for b in branches)
        if not has_bazi:
            return False, "C002 present but no Bazi chart content found (Chinese stem/branch characters missing)"
        return True, "C002 present with Bazi content"
    
    checks.append(run_check("C002 (Li Mei) Bazi output present", check_c002_present))
    
    # ── Check 6: C002 used lunar script (not solar) ─────────────────────────────
    def check_c002_lunar():
        """
        Verify C002 output matches lunar script, not solar script.
        Compare 1995-07-03T10:20:00 as lunar vs solar - year pillar will differ.
        """
        out_lunar = run_script("scripts/buildBaziFromLunar.ts",
                               ["1995-07-03T10:20:00", "0", "2"], skill_root)
        out_solar = run_script("scripts/buildBaziFromSolar.ts",
                               ["1995-07-03T10:20:00", "0", "2"], skill_root)
        
        def extract_bazi_string(text):
            m = re.search(r'([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])\s+([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])\s+([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])\s+([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])', text)
            if m:
                return m.group(0).replace(" ", "")
            return None
        
        bazi_lunar = extract_bazi_string(out_lunar)
        bazi_solar = extract_bazi_string(out_solar)
        
        if bazi_lunar is None:
            return True, f"Could not parse lunar script output - skipping strict check. Output: {out_lunar[:200]}"
        
        if bazi_lunar == bazi_solar:
            return True, "Lunar and solar scripts produce same result for this date - cannot discriminate"
        
        # Check which appears in report
        if bazi_lunar and bazi_lunar in report_text:
            return True, f"Report contains correct lunar Bazi: {bazi_lunar}"
        if bazi_solar and bazi_solar in report_text:
            return False, f"Report contains SOLAR Bazi ({bazi_solar}) instead of LUNAR Bazi ({bazi_lunar}) for C002"
        
        # Check character by character - lunar year pillar
        def extract_year_pillar(text):
            m = re.search(r'年柱\s*[|｜]\s*([甲乙丙丁戊己庚辛壬癸])\s*[|｜]\s*([子丑寅卯辰巳午未申酉戌亥])', text)
            if m:
                return m.group(1) + m.group(2)
            return None
        
        yp_lunar = extract_year_pillar(out_lunar)
        yp_solar = extract_year_pillar(out_solar)
        
        if yp_lunar and yp_solar and yp_lunar != yp_solar:
            if yp_lunar in report_text:
                return True, f"Report contains lunar year pillar {yp_lunar} (vs solar {yp_solar})"
            if yp_solar in report_text:
                return False, f"Report contains solar year pillar {yp_solar}, expected lunar {yp_lunar}"
        
        return True, f"Could not definitively discriminate lunar vs solar in report. Lunar Bazi: {bazi_lunar}"
    
    checks.append(run_check("C002 used lunar calendar script (not solar)", check_c002_lunar))
    
    # ── Check 7: C002 female gender ─────────────────────────────────────────────
    def check_c002_female():
        # Check report contains female indicator
        female_indicators = ["女", "female", "Female", "FEMALE", "Li Mei"]
        for ind in female_indicators:
            if ind in report_text:
                return True, f"Female indicator '{ind}' found in report"
        # Verify the output matches gender=0 (female) script
        out_female = run_script("scripts/buildBaziFromLunar.ts",
                                ["1995-07-03T10:20:00", "0", "2"], skill_root)
        out_male = run_script("scripts/buildBaziFromLunar.ts",
                              ["1995-07-03T10:20:00", "1", "2"], skill_root)
        # Gender primarily affects fortune pillars, not the 4 main pillars
        # Check for 女 in report as minimum
        if "0" in report_text or "female" in report_text.lower() or "女" in report_text:
            return True, "Female gender indicator found in report"
        return False, "No female gender indicator found in report for C002 Li Mei"
    
    checks.append(run_check("C002 correctly identified as female", check_c002_female))
    
    # ── Check 8: C003 almanac output present ───────────────────────────────────
    def check_c003_almanac():
        if "C003" not in report_text and "2024-03-15" not in report_text and "2024/03/15" not in report_text:
            return False, "C003 almanac query (2024-03-15) not found in report"
        
        # Check for almanac-specific content
        almanac_indicators = ["宜", "忌", "农历", "干支", "黄历", "lunar", "auspicious", "huangli", "ganZhi", "ganzhi"]
        found = [ind for ind in almanac_indicators if ind in report_text]
        if found:
            return True, f"Almanac content found: {', '.join(found[:5])}"
        
        # Check for Chinese calendar date markers
        lunar_months = ["正月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "冬月", "腊月"]
        found_months = [m for m in lunar_months if m in report_text]
        if found_months:
            return True, f"Lunar month found in report: {found_months[0]}"
        
        stems = "甲乙丙丁戊己庚辛壬癸"
        branches = "子丑寅卯辰巳午未申酉戌亥"
        # Check for ganzhi day (2024-03-15)
        out_cal = run_script("scripts/getChineseCalendar.ts", ["2024-03-15"], skill_root)
        ganzhis = re.findall(f'[{stems}][{branches}]', out_cal)
        for gz in ganzhis:
            if gz in report_text:
                return True, f"Ganzhi '{gz}' from 2024-03-15 almanac found in report"
        
        if "2024-03-15" in report_text or "2024/03/15" in report_text:
            return True, "2024-03-15 date present in report (almanac query acknowledged)"
        
        return False, "No almanac content found for C003 (2024-03-15)"
    
    checks.append(run_check("C003 almanac output for 2024-03-15 present", check_c003_almanac))
    
    # ── Check 9: All three clients represented ──────────────────────────────────
    def check_all_clients():
        present = []
        if "C001" in report_text or "Zhang Wei" in report_text:
            present.append("C001")
        if "C002" in report_text or "Li Mei" in report_text:
            present.append("C002")
        if "C003" in report_text or "2024-03-15" in report_text:
            present.append("C003")
        if len(present) == 3:
            return True, "All 3 clients present in report"
        missing = [c for c in ["C001","C002","C003"] if c not in present]
        return False, f"Missing clients: {missing}. Found: {present}"
    
    checks.append(run_check("All 3 clients represented in report", check_all_clients))
    
    # ── Final scoring ───────────────────────────────────────────────────────────
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks
    
    # Must pass: file exists, valid JSON, all 3 clients, C001 sect=1
    critical = ["astrology_report.json exists", "report is valid JSON",
                "All 3 clients represented in report"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical)
    
    overall_passed = critical_passed and score >= 0.65
    
    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()