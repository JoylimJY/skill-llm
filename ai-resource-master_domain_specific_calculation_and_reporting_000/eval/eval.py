import sys
import json
import math
import re
from pathlib import Path

def find_report(workspace):
    candidates = list(Path(workspace).rglob("gpu_assessment_report.txt"))
    return candidates[0] if candidates else None

def parse_number(text, pattern):
    m = re.search(pattern, text)
    if m:
        val = m.group(1).replace(',', '').replace('，', '')
        try:
            return float(val)
        except:
            return None
    return None

def check_approx(actual, expected, tol=0.05, label=""):
    if actual is None:
        return False, f"{label}: could not parse value"
    if abs(actual - expected) <= tol * abs(expected) + 0.5:
        return True, f"{label}: {actual} ≈ {expected} (within tolerance)"
    return False, f"{label}: got {actual}, expected ≈ {expected}"

def run_eval(workspace):
    checks = []

    # --- Ground truth calculations ---
    # Input data
    annual_outpatient = 1200  # 万人次/年
    annual_inpatient = 45     # 万人次/年

    daily_outpatient = annual_outpatient * 10000 / 365  # per day (absolute)
    daily_inpatient = annual_inpatient * 10000 / 365

    # In 万次 for display
    daily_op_wan = annual_outpatient / 365   # 万次/日
    daily_ip_wan = annual_inpatient / 365    # 万次/日

    # Scenarios and their parameters
    # (name, base_daily, seconds_per_call, coverage_rate)
    scenarios = [
        ("病历生成-门诊",    daily_outpatient, 30,  1.0),
        ("病历生成-住院",    daily_inpatient,  50,  1.0),
        ("辅助诊断",         daily_outpatient, 50,  1.0),
        ("病历质控-门诊",    daily_outpatient, 40,  1.0),
        ("病历质控-住院",    daily_inpatient,  60,  1.0),
        ("诊疗推荐-门诊",    daily_outpatient, 30,  1.0),
        ("诊疗推荐-住院",    daily_inpatient,  40,  1.0),
        ("导医导诊",         daily_outpatient, 24,  0.25),  # custom 25%
        ("患者画像提取",     daily_outpatient + daily_inpatient, 120, 1.0),
        ("报告解读-专用",    daily_outpatient, 20,  0.08),  # custom 8%
    ]

    scenario_hours = []
    for name, base, secs, cov in scenarios:
        calls = base * cov
        total_secs = calls * secs
        hours = total_secs / 3600
        scenario_hours.append((name, hours))

    total_hours = sum(h for _, h in scenario_hours)
    cards_needed_exact = total_hours / 80.0
    cards_needed_ceil = math.ceil(cards_needed_exact)
    machines_exact = cards_needed_ceil / 8.0
    machines_ceil = math.ceil(machines_exact)
    total_compute = machines_ceil * 2.5

    # Expected total hours (reference)
    # Let's compute precisely
    # daily_outpatient = 1200*10000/365 = 32876.712...
    # daily_inpatient  = 45*10000/365   = 1232.876...
    expected_total_hours = total_hours
    expected_cards = cards_needed_ceil
    expected_machines = machines_ceil
    expected_compute = total_compute

    # Find the report file
    report_path = find_report(workspace)

    if report_path is None:
        checks.append({"name": "file_exists", "passed": False, "detail": "gpu_assessment_report.txt not found anywhere in workspace"})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {report_path}"})

    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "file_readable", "passed": True, "detail": "File read successfully"})

    # Check 1: Region name present
    has_region = "渝北" in content
    checks.append({"name": "region_name_present", "passed": has_region,
                   "detail": "渝北 found in report" if has_region else "Region name 渝北 not found"})

    # Check 2: Annual volumes mentioned
    has_1200 = "1200" in content
    has_45 = re.search(r'\b45\b', content) is not None
    checks.append({"name": "annual_volumes_present", "passed": has_1200 and has_45,
                   "detail": f"1200万人次: {has_1200}, 45万人次: {has_45}"})

    # Check 3: Custom coverage rate for 导医导诊 (25%, NOT 30%)
    # Should NOT contain 30%门诊 for 导医导诊
    guidao_section = ""
    # Try to find the 导医导诊 block
    m = re.search(r'导医导诊.{0,300}', content, re.DOTALL)
    if m:
        guidao_section = m.group(0)
    has_25_percent = "25%" in guidao_section or "25%" in content
    has_wrong_30 = False
    # Check if 30% is mentioned in context of 导医导诊
    m30 = re.search(r'导医导诊.{0,150}30%', content, re.DOTALL)
    if m30:
        has_wrong_30 = True
    checks.append({"name": "custom_coverage_guidao_25pct", "passed": has_25_percent and not has_wrong_30,
                   "detail": f"25% found: {has_25_percent}, wrong 30% used: {has_wrong_30}"})

    # Check 4: Custom coverage rate for 报告解读-专用 (8%, NOT 5%)
    baogao_section = ""
    m = re.search(r'报告解读.{0,300}', content, re.DOTALL)
    if m:
        baogao_section = m.group(0)
    has_8_percent = "8%" in content
    has_wrong_5 = False
    m5 = re.search(r'报告解读.{0,150}5%', content, re.DOTALL)
    if m5:
        has_wrong_5 = True
    checks.append({"name": "custom_coverage_report_8pct", "passed": has_8_percent and not has_wrong_5,
                   "detail": f"8% found: {has_8_percent}, wrong 5% used: {has_wrong_5}"})

    # Check 5: 患者画像提取 uses BOTH outpatient and inpatient (120s)
    huaxiang_section = ""
    m = re.search(r'患者画像.{0,400}', content, re.DOTALL)
    if m:
        huaxiang_section = m.group(0)
    has_120 = "120" in huaxiang_section
    checks.append({"name": "patient_portrait_120s", "passed": has_120,
                   "detail": f"120秒 for 患者画像提取 found: {has_120}"})

    # Check 6: 病历质控-住院 uses 60s (not 40s)
    zhikong_ip_section = ""
    m = re.search(r'病历质控.{0,50}住院.{0,300}|住院.{0,50}病历质控.{0,300}', content, re.DOTALL)
    if m:
        zhikong_ip_section = m.group(0)
    has_60s = "60" in zhikong_ip_section or re.search(r'病历质控.{0,200}60[秒s]', content, re.DOTALL) is not None
    checks.append({"name": "zhikong_inpatient_60s", "passed": has_60s,
                   "detail": f"60秒 for 病历质控-住院 found: {has_60s}"})

    # Check 7: Total hours calculation approximately correct
    # Expected total hours
    exp_total = expected_total_hours
    # Try to find total hours in content
    total_h_found = None
    # Look for patterns like "XXXX.X小时" near 汇总 or 累加
    patterns = [
        r'累加[：:]\s*[\d\.\s\+]+[=＝]\s*([\d\.]+)\s*小时',
        r'总占用时间[^0-9]*([\d\.]+)\s*小时',
        r'([\d\.]+)\s*小时\s*$',
    ]
    for pat in patterns:
        m = re.search(pat, content)
        if m:
            try:
                total_h_found = float(m.group(1).replace(',',''))
                break
            except:
                pass

    # Also search more broadly for the total hours value near key words
    if total_h_found is None:
        # scan for all numbers near 小时 and find the largest plausible one
        all_hours = re.findall(r'([\d]{3,5}\.?\d*)\s*小时', content)
        candidates = []
        for h in all_hours:
            try:
                v = float(h)
                if 1000 < v < 100000:
                    candidates.append(v)
            except:
                pass
        if candidates:
            total_h_found = max(candidates)

    passed_total, detail_total = check_approx(total_h_found, exp_total, tol=0.03, label="Total hours")
    checks.append({"name": "total_hours_correct", "passed": passed_total, "detail": detail_total + f" | expected={exp_total:.1f}"})

    # Check 8: Card count correct (ceiling of total_hours/80)
    exp_cards_exact = exp_total / 80.0
    exp_cards_ceil = math.ceil(exp_cards_exact)
    cards_found = None
    card_patterns = [
        r'([\d\.]+)\s*卡\b',
        r'共需.{0,20}([\d\.]+).{0,10}卡',
        r'总显卡需求.{0,50}([\d\.]+)\s*卡',
        r'≈\s*([\d\.]+)\s*卡',
    ]
    for pat in card_patterns:
        for m in re.finditer(pat, content):
            try:
                v = float(m.group(1))
                if 5 < v < 500:
                    cards_found = v
            except:
                pass
    # Check for the ceiling value specifically
    cards_ceil_found = None
    for pat in card_patterns:
        for m in re.finditer(pat, content):
            try:
                v = float(m.group(1))
                if abs(v - exp_cards_ceil) <= 2:
                    cards_ceil_found = v
            except:
                pass

    passed_cards = cards_ceil_found is not None
    checks.append({"name": "card_count_correct", "passed": passed_cards,
                   "detail": f"Expected ceiling cards={exp_cards_ceil}, found mention: {cards_ceil_found} | exact={exp_cards_exact:.2f}"})

    # Check 9: Machine count correct (ceil of cards/8)
    exp_machines = machines_ceil
    machines_found = None
    machine_patterns = [
        r'([\d]+)\s*台.{0,10}一体机',
        r'一体机.{0,30}([\d]+)\s*台',
        r'向上取整\s*([\d]+)\s*台',
        r'取整\s*([\d]+)\s*台',
    ]
    for pat in machine_patterns:
        for m in re.finditer(pat, content):
            try:
                v = int(m.group(1))
                if 1 <= v <= 100:
                    machines_found = v
            except:
                pass

    passed_machines = machines_found == exp_machines
    checks.append({"name": "machine_count_correct", "passed": passed_machines,
                   "detail": f"Expected machines={exp_machines}, found={machines_found}"})

    # Check 10: Total compute power (machines * 2.5P)
    exp_compute = expected_compute
    compute_found = None
    compute_patterns = [
        r'([\d\.]+)\s*[Pp]\b',
        r'总算力.{0,30}([\d\.]+)\s*[Pp]',
        r'([\d\.]+)\s*P算力',
    ]
    for pat in compute_patterns:
        for m in re.finditer(pat, content):
            try:
                v = float(m.group(1))
                if 1 <= v <= 1000:
                    compute_found = v
            except:
                pass
    # Find the total compute value specifically
    total_compute_found = None
    for pat in compute_patterns:
        for m in re.finditer(pat, content):
            try:
                v = float(m.group(1))
                if abs(v - exp_compute) <= 2.5:
                    total_compute_found = v
            except:
                pass

    passed_compute = total_compute_found is not None
    checks.append({"name": "total_compute_correct", "passed": passed_compute,
                   "detail": f"Expected total compute={exp_compute}P, found={total_compute_found}"})

    # Check 11: Output format - no tables (no | characters used in table format)
    table_pattern = re.search(r'\|.+\|.+\|', content)
    no_tables = table_pattern is None
    checks.append({"name": "no_table_format", "passed": no_tables,
                   "detail": "No markdown tables found" if no_tables else "Found markdown table formatting (prohibited)"})

    # Check 12: Proper section numbering structure (e.g., 1.1 or similar)
    has_section_nums = bool(re.search(r'\d+\.\d+\.\d+', content))
    checks.append({"name": "section_numbering_present", "passed": has_section_nums,
                   "detail": "Multi-level section numbers found" if has_section_nums else "No multi-level section numbers found"})

    # Check 13: 80小时/卡 capacity mentioned (proprietary trap)
    has_80h = "80" in content and "小时" in content
    has_80h_card = bool(re.search(r'80\s*小时', content))
    checks.append({"name": "card_capacity_80h_mentioned", "passed": has_80h_card,
                   "detail": f"80小时/卡/日 mentioned: {has_80h_card}"})

    # Check 14: 10路并发 mentioned
    has_10_concurrent = bool(re.search(r'10\s*路', content))
    checks.append({"name": "concurrent_10_lanes_mentioned", "passed": has_10_concurrent,
                   "detail": f"10路并发 mentioned: {has_10_concurrent}"})

    # Scoring
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])
    score = passed_checks / total_checks

    # Must pass critical checks to overall pass
    critical = ["file_exists", "total_hours_correct", "machine_count_correct",
                "custom_coverage_guidao_25pct", "custom_coverage_report_8pct", "no_table_format"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical)

    overall_passed = critical_passed and score >= 0.75

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))