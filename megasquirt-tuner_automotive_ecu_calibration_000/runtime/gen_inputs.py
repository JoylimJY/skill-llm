import os
import random
import json

random.seed(42)

# Create directory structure
dirs = [
    "workspace/scripts",
    "workspace/references",
    "workspace/datalogs",
    "workspace/tunes/archive",
    "workspace/tunes/working",
    "workspace/tunes/baseline",
    "workspace/sensor_data",
    "workspace/dyno_sheets",
    "workspace/notes",
    "workspace/firmware",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ---- Distractor files ----
with open("workspace/notes/session_notes.txt", "w") as f:
    f.write("Session notes - Feb 2024\nDriver reported hesitation at 3500rpm under boost.\nFuel smell from exhaust at light load.\nNeed to re-check AFR targets.\n")

with open("workspace/dyno_sheets/run_001.csv", "w") as f:
    f.write("rpm,torque,power,afr\n2000,180,52,13.8\n3000,210,90,13.2\n4000,230,131,12.8\n5000,215,154,12.6\n6000,195,167,12.4\n")

with open("workspace/datalogs/log_2024_02_10.csv", "w") as f:
    f.write("time,rpm,map,tps,clt,iat,afr1,egoCorrection,advance,pulseWidth\n")
    for i in range(50):
        f.write(f"{i*0.1:.1f},{800+i*10},{45+i},{i*2},{85},{32},{14.2+i*0.01},{-2+i*0.1},{18},{4.2}\n")

with open("workspace/datalogs/log_2024_02_11.csv", "w") as f:
    f.write("# Datalog from tuning session\ntime,rpm,map,afr1,advance\n")
    for i in range(30):
        f.write(f"{i*0.2:.1f},{1200+i*50},{60+i*2},{13.5+i*0.05},{22}\n")

with open("workspace/sensor_data/wideband_calibration.txt", "w") as f:
    f.write("Innovate LC-2 wideband\n0V = 10.0 AFR\n5V = 20.0 AFR\nCalibration verified 2024-02-08\n")

with open("workspace/sensor_data/temp_sensors.json", "w") as f:
    json.dump({"CLT": "GM_2wire", "IAT": "GM_2wire", "calibration_date": "2024-01-15"}, f, indent=2)

with open("workspace/firmware/ms3_v1.5.1_changelog.txt", "w") as f:
    f.write("MS3 Firmware v1.5.1\nFixed: Sequential injection timing\nAdded: Flex fuel ethanol sensor support\nFixed: Boost control PID stability\n")

with open("workspace/references/injector_specs.txt", "w") as f:
    f.write("Bosch EV14 550cc injectors\nFlow rate: 550 cc/min\nOpening time: 0.9ms at 13.2V\nResistance: 12 ohm\n")

with open("workspace/tunes/archive/baseline_2024_01_15.msq", "w") as f:
    f.write("[metadata]\nfirmware=MS3\ndate=2024-01-15\nversion=1.0\n\n[engineConstants]\ndisplacement=1998\ncylinders=4\ninjectorCCMin=440\n\n[veTable1]\n; Old baseline - not tuned\n")

with open("workspace/tunes/archive/old_tune_notes.txt", "w") as f:
    f.write("Old tune from previous owner. VE table was roughly estimated. Do not use without review.\n")

with open("workspace/dyno_sheets/target_afr_plan.txt", "w") as f:
    f.write("Target AFR plan for turbo setup:\nIdle: 14.0\nCruise: 15.0\nPart throttle: 14.0\nWOT (boosted): 11.8\n")

# ---- The analyze_msq.py script (as referenced in SKILL.md) ----
analyze_script = '''#!/usr/bin/env python3
"""
MSQ Tune File Analyzer for Megasquirt ECU
Analyzes .msq files for safety issues and optimization opportunities.
"""
import sys
import os
import re

CRITICAL = "CRITICAL"
WARNING = "WARNING"
SUGGESTION = "SUGGESTION"
NOTE = "NOTE"
OK = "OK"

issues = []

def add_issue(level, section, message):
    issues.append((level, section, message))

def check_safety_extension(filepath):
    if not filepath.endswith('.msq'):
        print(f"ERROR: Only .msq files are accepted. Got: {filepath}")
        sys.exit(1)

def check_path_traversal(filepath):
    if '../' in filepath or '..\\\\' in filepath:
        print("ERROR: Path traversal sequences are not allowed.")
        sys.exit(1)

def check_symlink(filepath):
    if os.path.islink(filepath):
        print("ERROR: Symbolic links are not allowed.")
        sys.exit(1)

def parse_msq(filepath):
    check_safety_extension(filepath)
    check_path_traversal(filepath)
    check_symlink(filepath)
    if not os.path.isfile(filepath):
        print(f"ERROR: File not found: {filepath}")
        sys.exit(1)
    with open(filepath, 'r') as fh:
        return fh.read()

def extract_section(content, section_name):
    pattern = rf"\\[{re.escape(section_name)}\\](.*?)(?=\\[|\\Z)"
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

def parse_key_value(section_text):
    result = {}
    if not section_text:
        return result
    for line in section_text.splitlines():
        line = line.strip()
        if line.startswith(';') or not line:
            continue
        if '=' in line:
            k, _, v = line.partition('=')
            result[k.strip()] = v.strip()
    return result

def parse_table_values(section_text):
    values = []
    if not section_text:
        return values
    for line in section_text.splitlines():
        line = line.strip()
        if line.startswith(';') or not line:
            continue
        for token in line.split():
            try:
                values.append(float(token))
            except ValueError:
                pass
    return values

def analyze_engine_constants(content):
    section = extract_section(content, "engineConstants")
    kv = parse_key_value(section)
    print("\\n📋 Engine Constants")
    print("-" * 40)
    required_keys = ["displacement", "cylinders", "injectorCCMin"]
    for k in required_keys:
        if k not in kv:
            add_issue(WARNING, "engineConstants", f"Missing key: {k}")
            print(f"  ⚠️ Missing: {k}")
        else:
            print(f"  ✓ {k} = {kv[k]}")
    
    # Required fuel check
    if all(k in kv for k in ["displacement", "cylinders", "injectorCCMin"]):
        try:
            disp = float(kv["displacement"])
            cyls = float(kv["cylinders"])
            inj_cc = float(kv["injectorCCMin"])
            req_fuel = (disp * 5) / (cyls * inj_cc) * 2
            print(f"  ℹ️ Calculated Required Fuel: {req_fuel:.3f} ms")
            add_issue(NOTE, "engineConstants", f"Required Fuel calculated: {req_fuel:.3f} ms")
            if "requiredFuel" in kv:
                stored = float(kv["requiredFuel"])
                diff = abs(stored - req_fuel)
                if diff > 0.5:
                    add_issue(WARNING, "engineConstants", 
                              f"requiredFuel ({stored:.3f}ms) differs from calculated ({req_fuel:.3f}ms) by {diff:.3f}ms")
                    print(f"  ⚠️ requiredFuel mismatch: stored={stored:.3f}, calculated={req_fuel:.3f}")
                else:
                    print(f"  ✓ requiredFuel ({stored:.3f}ms) matches calculated ({req_fuel:.3f}ms)")
        except (ValueError, ZeroDivisionError):
            add_issue(WARNING, "engineConstants", "Could not calculate required fuel")
    return kv

def analyze_ve_table(content):
    section = extract_section(content, "veTable1")
    values = parse_table_values(section)
    print("\\n📋 VE Table")
    print("-" * 40)
    if not values:
        add_issue(WARNING, "veTable1", "VE table is empty or missing")
        print("  ⚠️ VE table is empty or missing")
        return
    min_ve = min(values)
    max_ve = max(values)
    avg_ve = sum(values) / len(values)
    if min_ve < 20:
        add_issue(WARNING, "veTable1", f"VE table has very low values ({min_ve}) - check for empty/untuned cells")
        print(f"  ⚠️ VE table has very low values ({min_ve}) - check for empty/untuned cells")
    if max_ve > 120:
        add_issue(WARNING, "veTable1", f"VE table has very high values ({max_ve}) - verify table is correct")
        print(f"  ⚠️ VE table has very high values ({max_ve})")
    # Check for large jumps between adjacent cells
    large_jumps = 0
    for i in range(1, len(values)):
        if abs(values[i] - values[i-1]) > 30:
            large_jumps += 1
    if large_jumps > 0:
        add_issue(SUGGESTION, "veTable1", f"{large_jumps} cells have >30% jumps from neighbors - consider smoothing")
        print(f"  📊 {large_jumps} cells have >30% jumps from neighbors - consider smoothing")
    print(f"  ✓ VE table range: {min_ve} - {max_ve} (avg: {avg_ve:.1f})")

def analyze_spark_table(content):
    section = extract_section(content, "sparkTable1")
    values = parse_table_values(section)
    print("\\n📋 Ignition Timing")
    print("-" * 40)
    if not values:
        add_issue(NOTE, "sparkTable1", "No spark table found")
        print("  ℹ️ No spark table found")
        return
    max_adv = max(values)
    min_adv = min(values)
    if max_adv > 45:
        add_issue(WARNING, "sparkTable1", f"High ignition advance ({max_adv}°) - verify on dyno with knock detection")
        print(f"  ⚠️ High ignition advance ({max_adv}°) - verify on dyno with knock detection")
    if max_adv > 55:
        add_issue(CRITICAL, "sparkTable1", f"Extreme ignition advance ({max_adv}°) - severe knock risk, engine damage likely")
        print(f"  🚨 Extreme ignition advance ({max_adv}°) - CRITICAL: severe knock risk")
    print(f"  ✓ Spark advance range: {min_adv}° - {max_adv}° BTDC")

def analyze_afr_table(content):
    section = extract_section(content, "afrTable1")
    values = parse_table_values(section)
    print("\\n📋 AFR Targets")
    print("-" * 40)
    if not values:
        add_issue(NOTE, "afrTable1", "No AFR target table found")
        print("  ℹ️ No AFR target table found")
        return
    max_afr = max(values)
    min_afr = min(values)
    # Check for dangerously lean WOT targets
    lean_danger = [v for v in values if v > 14.0]
    if lean_danger:
        add_issue(CRITICAL, "afrTable1", f"AFR targets >14.0 detected ({max(lean_danger):.1f}) - lean under load causes engine damage")
        print(f"  🚨 AFR targets >14.0 detected ({max(lean_danger):.1f}) - CRITICAL: lean damage risk")
    very_rich = [v for v in values if v < 10.5]
    if very_rich:
        add_issue(WARNING, "afrTable1", f"Very rich AFR targets (<10.5) detected - excessive fuel consumption/emissions")
        print(f"  ⚠️ Very rich AFR targets (<10.5) detected")
    print(f"  ✓ AFR target range: {min_afr:.1f} - {max_afr:.1f}")

def analyze_rev_limiter(content):
    section = extract_section(content, "revLimiter")
    kv = parse_key_value(section)
    print("\\n📋 Rev Limiter")
    print("-" * 40)
    if not section or not kv:
        add_issue(WARNING, "revLimiter", "Rev limiter not configured - risk of engine over-rev")
        print("  ⚠️ Rev limiter not configured - risk of engine over-rev")
        return
    if "hardLimit" in kv:
        print(f"  ✓ Hard limit: {kv['hardLimit']} RPM")
    if "softLimit" in kv:
        print(f"  ✓ Soft limit: {kv['softLimit']} RPM")

def analyze_injector_duty(content):
    section = extract_section(content, "engineConstants")
    kv = parse_key_value(section)
    print("\\n📋 Injector Duty Estimate")
    print("-" * 40)
    if "maxRPM" in kv and "requiredFuel" in kv:
        try:
            max_rpm = float(kv["maxRPM"])
            req_fuel = float(kv["requiredFuel"])
            inj_period_ms = (60000.0 / max_rpm) * 2  # ms per cycle
            # At 100% VE, 100kPa the PW = requiredFuel
            duty = (req_fuel / inj_period_ms) * 100
            if duty > 90:
                add_issue(CRITICAL, "injectorDuty", f"Estimated injector duty {duty:.1f}% at max RPM - exceeds safe 90% limit")
                print(f"  🚨 Estimated injector duty {duty:.1f}% - CRITICAL: exceeds safe 90%")
            elif duty > 85:
                add_issue(WARNING, "injectorDuty", f"Estimated injector duty {duty:.1f}% at max RPM - approaching limit (85%)")
                print(f"  ⚠️ Estimated injector duty {duty:.1f}% - approaching 85% safety limit")
            else:
                print(f"  ✓ Estimated injector duty {duty:.1f}% - within safe range")
        except (ValueError, ZeroDivisionError):
            print("  ℹ️ Cannot estimate injector duty - missing parameters")
    else:
        print("  ℹ️ maxRPM or requiredFuel not found - cannot estimate duty cycle")

def print_summary():
    print("\\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    criticals = [i for i in issues if i[0] == CRITICAL]
    warnings = [i for i in issues if i[0] == WARNING]
    suggestions = [i for i in issues if i[0] == SUGGESTION]
    notes = [i for i in issues if i[0] == NOTE]
    print(f"🚨 CRITICAL ISSUES: {len(criticals)}")
    print(f"⚠️  WARNINGS: {len(warnings)}")
    print(f"✓ Suggestions: {len(suggestions)}")
    print(f"ℹ️  Notes: {len(notes)}")
    if criticals:
        print("\\nCRITICAL ISSUES:")
        for _, sec, msg in criticals:
            print(f"  [{sec}] {msg}")
    if warnings:
        print("\\nWARNINGS:")
        for _, sec, msg in warnings:
            print(f"  [{sec}] {msg}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_msq.py <tune.msq>")
        sys.exit(1)
    filepath = sys.argv[1]
    content = parse_msq(filepath)
    print(f"Analyzing: {filepath}")
    print("=" * 60)
    analyze_engine_constants(content)
    analyze_ve_table(content)
    analyze_spark_table(content)
    analyze_afr_table(content)
    analyze_rev_limiter(content)
    analyze_injector_duty(content)
    print_summary()

if __name__ == "__main__":
    main()
'''

with open("workspace/scripts/analyze_msq.py", "w") as f:
    f.write(analyze_script)

# ---- The problematic MSQ tune file the agent must analyze and fix ----
# Engine: 2.0L 4-cyl turbo, 550cc/min injectors
# Problems planted:
# 1. requiredFuel is WRONG (stored=5.500, correct = (1998*5)/(4*550)*2 = 9990/2200*2 = 4.541*2 = 9.082ms... let me recalculate)
# Correct: (1998 * 5) / (4 * 550) * 2 = 9990 / 2200 * 2 = 4.5409 * 2 = 9.082ms
# Let's plant stored=6.200 (wrong)
# 2. AFR table has some cells > 14.0 (dangerous lean)
# 3. Spark table has timing > 45° (warning)
# 4. VE cells need correction based on measured AFR data we provide

# VE table: 6x6 layout for simplicity
# We'll give 6 representative VE values that need correction
# measured AFR vs target AFR => new VE = current * (measured/target)
# Target AFR at these cells: 14.0
# We'll specify measured AFR values so agent must compute corrections

ve_table_values = [
    # Row 1 (low RPM): 45, 50, 55, 58, 60, 55
    # Row 2: 52, 58, 63, 67, 65, 60
    # Row 3: 55, 62, 70, 75, 72, 65
    # Row 4: 58, 65, 74, 80, 78, 70
    # Row 5: 55, 62, 70, 76, 74, 68
    # Row 6 (high RPM/WOT): 50, 58, 66, 72, 70, 63
    45, 50, 55, 58, 60, 55,
    52, 58, 63, 67, 65, 60,
    55, 62, 70, 75, 72, 65,
    58, 65, 74, 80, 78, 70,
    55, 62, 70, 76, 74, 68,
    50, 58, 66, 72, 70, 63,
]

ve_table_str = ""
for i, v in enumerate(ve_table_values):
    ve_table_str += f"{v}"
    if (i + 1) % 6 == 0:
        ve_table_str += "\n"
    else:
        ve_table_str += " "

# AFR table: some cells > 14.0 (dangerous under load) - planted deliberately
# 6x6, representing RPM rows vs MAP columns
# WOT turbo should be 11.5-12.5; we'll put 14.7 in a couple of high-load cells
afr_table_values = [
    # Low RPM / Low MAP → High RPM / High MAP
    14.7, 14.7, 14.5, 14.0, 13.5, 13.0,   # idle/very light
    14.7, 14.5, 14.0, 13.5, 13.0, 12.5,   # light cruise
    14.5, 14.0, 13.5, 13.0, 12.5, 12.0,   # part throttle
    14.0, 13.5, 13.0, 12.5, 12.0, 11.8,   # moderate load
    14.2, 14.5, 13.5, 12.5, 12.0, 11.8,   # high load (14.5 here is dangerous at high rpm)
    14.0, 14.7, 14.0, 12.5, 11.8, 11.5,   # WOT (14.7 at high rpm/WOT is CRITICAL)
]

afr_table_str = ""
for i, v in enumerate(afr_table_values):
    afr_table_str += f"{v}"
    if (i + 1) % 6 == 0:
        afr_table_str += "\n"
    else:
        afr_table_str += " "

# Spark table: some values > 45° (warning), one > 55° (critical)
spark_table_values = [
    20, 25, 30, 32, 28, 22,
    25, 30, 35, 38, 33, 26,
    28, 34, 38, 42, 37, 30,
    30, 36, 40, 44, 40, 33,
    32, 38, 42, 46, 43, 35,   # 46° > 45 → warning
    33, 39, 43, 48, 44, 36,   # 48° → warning (and > 45)
]

spark_table_str = ""
for i, v in enumerate(spark_table_values):
    spark_table_str += f"{v}"
    if (i + 1) % 6 == 0:
        spark_table_str += "\n"
    else:
        spark_table_str += " "

msq_content = f"""[metadata]
firmware=MS3
date=2024-02-01
version=2.3
author=PreviousTuner
description=Turbo 2.0L tune - partially completed

[engineConstants]
displacement=1998
cylinders=4
injectorCCMin=550
requiredFuel=6.200
maxRPM=7000
injectorOpenTime=0.9
battVoltCorrect=0.024

[veTable1]
; VE Table (RPM vs MAP) - 6x6
; Rows: 800, 1500, 2500, 3500, 5000, 6500 RPM
; Cols: 20, 40, 60, 80, 100, 120 kPa
{ve_table_str}
[sparkTable1]
; Spark advance table (degrees BTDC) - 6x6
; Rows: 800, 1500, 2500, 3500, 5000, 6500 RPM
; Cols: 20, 40, 60, 80, 100, 120 kPa
{spark_table_str}
[afrTable1]
; AFR target table - 6x6
; Rows: 800, 1500, 2500, 3500, 5000, 6500 RPM
; Cols: 20, 40, 60, 80, 100, 120 kPa
{afr_table_str}
[revLimiter]
softLimit=6800
hardLimit=7000
softMethod=retard
hardMethod=cut

[warmupEnrichment]
; temp(C) = enrichment(%)
-40=180
-20=160
0=140
20=120
40=110
70=100
80=100

[idleControl]
targetHotRPM=800
targetColdRPM=1300
closedPWM=30
openPWM=70
crankingPWM=60
"""

with open("workspace/tunes/working/race_tune_v2.3.msq", "w") as f:
    f.write(msq_content)

# ---- Measured AFR data for VE correction ----
# Agent must use: New VE = Current VE × (Measured AFR / Target AFR)
# We provide steady-state wideband measurements for specific cells
# Format: (RPM_idx, MAP_idx, measured_AFR, target_AFR)
# Using the 6x6 grid:
# RPM rows: 0=800, 1=1500, 2=2500, 3=3500, 4=5000, 5=6500
# MAP cols: 0=20, 1=40, 2=60, 3=80, 4=100, 5=120

measured_data = {
    "description": "Steady-state wideband AFR measurements from dyno session 2024-02-12",
    "engine": "2.0L turbo 4-cyl",
    "note": "Measurements taken at warm operating temp (CLT=87C). Apply corrections to VE table.",
    "measurements": [
        {"rpm": 800,  "map_kpa": 40,  "current_ve": 50, "measured_afr": 15.2, "target_afr": 14.0, "cell": "row0_col1"},
        {"rpm": 800,  "map_kpa": 60,  "current_ve": 55, "measured_afr": 14.8, "target_afr": 14.0, "cell": "row0_col2"},
        {"rpm": 1500, "map_kpa": 40,  "current_ve": 58, "measured_afr": 15.5, "target_afr": 14.0, "cell": "row1_col1"},
        {"rpm": 1500, "map_kpa": 60,  "current_ve": 63, "measured_afr": 14.4, "target_afr": 14.0, "cell": "row1_col2"},
        {"rpm": 2500, "map_kpa": 60,  "current_ve": 70, "measured_afr": 13.1, "target_afr": 13.5, "cell": "row2_col2"},
        {"rpm": 2500, "map_kpa": 80,  "current_ve": 75, "measured_afr": 12.8, "target_afr": 13.0, "cell": "row2_col3"},
        {"rpm": 3500, "map_kpa": 80,  "current_ve": 80, "measured_afr": 11.9, "target_afr": 12.5, "cell": "row3_col3"},
        {"rpm": 3500, "map_kpa": 100, "current_ve": 78, "measured_afr": 11.5, "target_afr": 12.0, "cell": "row3_col4"},
        {"rpm": 5000, "map_kpa": 100, "current_ve": 74, "measured_afr": 11.2, "target_afr": 12.0, "cell": "row4_col4"},
        {"rpm": 6500, "map_kpa": 100, "current_ve": 70, "measured_afr": 10.8, "target_afr": 12.0, "cell": "row5_col4"},
    ]
}

with open("workspace/sensor_data/dyno_afr_measurements.json", "w") as f:
    json.dump(measured_data, f, indent=2)

# ---- Additional distractors ----
with open("workspace/tunes/baseline/stock_ecu_map.txt", "w") as f:
    f.write("OEM ECU reference values - not applicable to Megasquirt\nDo not use these values directly.\n")

with open("workspace/notes/todo.txt", "w") as f:
    f.write("TODO:\n- Check fuel pump flow at high RPM\n- Verify MAP sensor calibration\n- Update rev limiter if changing cams\n- Review boost controller settings after intake install\n")

with open("workspace/dyno_sheets/power_goals.txt", "w") as f:
    f.write("Power targets:\n- 250whp @ 18psi\n- Peak torque at 4000rpm\n- Safe AFR throughout powerband\n")

with open("workspace/firmware/flashing_instructions.txt", "w") as f:
    f.write("MS3 Flashing Instructions:\n1. Backup current tune\n2. Use TunerStudio firmware upgrade tool\n3. Load .S19 file\n4. Reload tune after flash\n")

print("Workspace created successfully.")
print("Key files:")
print("  workspace/tunes/working/race_tune_v2.3.msq  <- tune to analyze and fix")
print("  workspace/sensor_data/dyno_afr_measurements.json  <- measured AFR data for VE corrections")
print("  workspace/scripts/analyze_msq.py  <- analysis tool")