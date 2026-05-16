import sys
import json
import os
import re
import math
from pathlib import Path

workspace = sys.argv[1]
checks = []
total_score = 0.0
max_score = 0.0

def add_check(name, passed, detail, weight=1.0):
    global total_score, max_score
    checks.append({"name": name, "passed": passed, "detail": detail})
    max_score += weight
    if passed:
        total_score += weight

# ---- Find output files ----
# Agent must create: tune_review.json (analysis report)
# Agent must create: race_tune_v2.3_corrected.msq (corrected tune file)

review_files = list(Path(workspace).rglob("tune_review.json"))
corrected_msq_files = list(Path(workspace).rglob("race_tune_v2.3_corrected.msq"))

# ---- CHECK 1: tune_review.json exists ----
if review_files:
    add_check("tune_review.json exists", True, f"Found at {review_files[0]}", weight=0.5)
    review_path = review_files[0]
else:
    add_check("tune_review.json exists", False, "tune_review.json not found anywhere in workspace", weight=0.5)
    review_path = None

# ---- CHECK 2: corrected MSQ file exists ----
if corrected_msq_files:
    add_check("corrected MSQ file exists", True, f"Found at {corrected_msq_files[0]}", weight=0.5)
    corrected_path = corrected_msq_files[0]
else:
    add_check("corrected MSQ file exists", False, "race_tune_v2.3_corrected.msq not found", weight=0.5)
    corrected_path = None

# ---- CHECK 3: tune_review.json contains critical AFR issue ----
if review_path:
    try:
        with open(review_path) as f:
            review = json.load(f)
        review_str = json.dumps(review).lower()
        # Must flag lean/dangerous AFR targets (>14.0 at load/WOT)
        afr_critical = any(
            "afr" in str(v).lower() and any(word in str(v).lower() for word in ["critical", "lean", "danger", "14.0", "14.5", "14.7"])
            for v in (review.values() if isinstance(review, dict) else [review_str])
        ) or "lean" in review_str or "critical" in review_str or "14.7" in review_str or "afr" in review_str
        add_check(
            "Review flags dangerous AFR targets",
            afr_critical,
            f"Review must identify lean/dangerous AFR targets >14.0. Found: {'yes' if afr_critical else 'no'}",
            weight=1.5
        )
    except Exception as e:
        add_check("Review flags dangerous AFR targets", False, f"Could not parse tune_review.json: {e}", weight=1.5)
else:
    add_check("Review flags dangerous AFR targets", False, "No review file to check", weight=1.5)

# ---- CHECK 4: tune_review.json flags high ignition timing ----
if review_path:
    try:
        with open(review_path) as f:
            review = json.load(f)
        review_str = json.dumps(review).lower()
        timing_warned = any(
            kw in review_str for kw in ["timing", "spark", "ignition", "advance", "knock", "48", "46"]
        )
        add_check(
            "Review flags high ignition timing",
            timing_warned,
            f"Review must mention high ignition timing warning. Found: {'yes' if timing_warned else 'no'}",
            weight=1.0
        )
    except Exception as e:
        add_check("Review flags high ignition timing", False, f"Error: {e}", weight=1.0)
else:
    add_check("Review flags high ignition timing", False, "No review file", weight=1.0)

# ---- CHECK 5: tune_review.json includes corrected requiredFuel value ----
# Correct: (1998 * 5) / (4 * 550) * 2 = 9990/2200 * 2 = 9.08181...ms
CORRECT_REQ_FUEL = (1998 * 5) / (4 * 550) * 2  # = 9.0818...

if review_path:
    try:
        with open(review_path) as f:
            review = json.load(f)
        review_str = json.dumps(review)
        # Look for the correct value (within 0.05ms tolerance)
        numbers = re.findall(r'\d+\.\d+', review_str)
        found_correct = any(abs(float(n) - CORRECT_REQ_FUEL) < 0.1 for n in numbers)
        add_check(
            "Review contains correct requiredFuel calculation",
            found_correct,
            f"Expected requiredFuel ≈ {CORRECT_REQ_FUEL:.3f}ms. "
            f"Numbers found in review: {[n for n in numbers if 8.0 < float(n) < 11.0]}",
            weight=2.0
        )
    except Exception as e:
        add_check("Review contains correct requiredFuel calculation", False, f"Error: {e}", weight=2.0)
else:
    add_check("Review contains correct requiredFuel calculation", False, "No review file", weight=2.0)

# ---- CHECK 6: Corrected MSQ has fixed requiredFuel ----
if corrected_path:
    try:
        with open(corrected_path) as f:
            content = f.read()
        # Find requiredFuel value
        match = re.search(r'requiredFuel\s*=\s*([\d.]+)', content, re.IGNORECASE)
        if match:
            stored = float(match.group(1))
            correct = abs(stored - CORRECT_REQ_FUEL) < 0.1
            add_check(
                "Corrected MSQ has accurate requiredFuel",
                correct,
                f"requiredFuel should be ≈{CORRECT_REQ_FUEL:.3f}ms. Got: {stored:.3f}ms",
                weight=2.0
            )
        else:
            add_check(
                "Corrected MSQ has accurate requiredFuel",
                False,
                "requiredFuel key not found in corrected MSQ",
                weight=2.0
            )
    except Exception as e:
        add_check("Corrected MSQ has accurate requiredFuel", False, f"Error reading corrected MSQ: {e}", weight=2.0)
else:
    add_check("Corrected MSQ has accurate requiredFuel", False, "No corrected MSQ file", weight=2.0)

# ---- CHECK 7: Corrected MSQ has updated VE cells ----
# Formula: New VE = Current VE × (Measured AFR / Target AFR)
# Verify at least 5 of the 10 measured cells are corrected
# Expected corrections:
expected_ve_corrections = [
    {"cell": "row0_col1", "current_ve": 50,  "measured": 15.2, "target": 14.0, "new_ve": 50  * (15.2/14.0)},
    {"cell": "row0_col2", "current_ve": 55,  "measured": 14.8, "target": 14.0, "new_ve": 55  * (14.8/14.0)},
    {"cell": "row1_col1", "current_ve": 58,  "measured": 15.5, "target": 14.0, "new_ve": 58  * (15.5/14.0)},
    {"cell": "row1_col2", "current_ve": 63,  "measured": 14.4, "target": 14.0, "new_ve": 63  * (14.4/14.0)},
    {"cell": "row2_col2", "current_ve": 70,  "measured": 13.1, "target": 13.5, "new_ve": 70  * (13.1/13.5)},
    {"cell": "row2_col3", "current_ve": 75,  "measured": 12.8, "target": 13.0, "new_ve": 75  * (12.8/13.0)},
    {"cell": "row3_col3", "current_ve": 80,  "measured": 11.9, "target": 12.5, "new_ve": 80  * (11.9/12.5)},
    {"cell": "row3_col4", "current_ve": 78,  "measured": 11.5, "target": 12.0, "new_ve": 78  * (11.5/12.0)},
    {"cell": "row4_col4", "current_ve": 74,  "measured": 11.2, "target": 12.0, "new_ve": 74  * (11.2/12.0)},
    {"cell": "row5_col4", "current_ve": 70,  "measured": 10.8, "target": 12.0, "new_ve": 70  * (10.8/12.0)},
]

if corrected_path:
    try:
        with open(corrected_path) as f:
            content = f.read()
        
        # Extract veTable1 section
        ve_section_match = re.search(r'\[veTable1\](.*?)(?=\[|\Z)', content, re.DOTALL | re.IGNORECASE)
        if ve_section_match:
            ve_text = ve_section_match.group(1)
            # Parse all numeric values from VE table
            ve_values_in_file = []
            for line in ve_text.splitlines():
                line = line.strip()
                if line.startswith(';') or not line:
                    continue
                for token in line.split():
                    try:
                        ve_values_in_file.append(float(token))
                    except ValueError:
                        pass
            
            # Check how many expected corrected values appear in the VE table
            # The table is 6x6=36 values; we check that corrected values exist
            # Tolerance: ±1.5 VE units (rounding is acceptable)
            correct_count = 0
            details_found = []
            for corr in expected_ve_corrections:
                new_ve = corr["new_ve"]
                found = any(abs(v - new_ve) < 1.5 for v in ve_values_in_file)
                if found:
                    correct_count += 1
                    details_found.append(f"{corr['cell']}={new_ve:.1f}✓")
                else:
                    details_found.append(f"{corr['cell']}={new_ve:.1f}✗")
            
            threshold = 5  # at least 5 of 10 cells correctly updated
            passed_ve = correct_count >= threshold
            add_check(
                f"Corrected MSQ has updated VE cells (≥{threshold}/10)",
                passed_ve,
                f"Correctly updated cells: {correct_count}/10. Details: {', '.join(details_found)}",
                weight=3.0
            )
        else:
            add_check(
                "Corrected MSQ has updated VE cells",
                False,
                "veTable1 section not found in corrected MSQ",
                weight=3.0
            )
    except Exception as e:
        add_check("Corrected MSQ has updated VE cells", False, f"Error: {e}", weight=3.0)
else:
    add_check("Corrected MSQ has updated VE cells", False, "No corrected MSQ file", weight=3.0)

# ---- CHECK 8: Corrected MSQ has fixed dangerous AFR targets ----
# The dangerous cells (>14.0 at high load/WOT) should be corrected
# Specifically row4/row5 (5000/6500 RPM) at mid-to-high MAP should not exceed 14.0
# For turbo WOT: should be ≤12.5

if corrected_path:
    try:
        with open(corrected_path) as f:
            content = f.read()
        
        afr_section_match = re.search(r'\[afrTable1\](.*?)(?=\[|\Z)', content, re.DOTALL | re.IGNORECASE)
        if afr_section_match:
            afr_text = afr_section_match.group(1)
            afr_values = []
            for line in afr_text.splitlines():
                line = line.strip()
                if line.startswith(';') or not line:
                    continue
                for token in line.split():
                    try:
                        afr_values.append(float(token))
                    except ValueError:
                        pass
            
            if afr_values:
                # The original had 14.7 in high-load/WOT positions (row4 col1=14.5, row5 col1=14.7)
                # These are indices in the 6x6 table:
                # row4 = indices 24-29, row5 = indices 30-35
                high_load_values = afr_values[24:36] if len(afr_values) >= 36 else []
                dangerous_remaining = [v for v in high_load_values if v > 14.0]
                
                afr_fixed = len(dangerous_remaining) == 0
                add_check(
                    "Dangerous AFR targets corrected in high-load rows",
                    afr_fixed,
                    f"High-load AFR values (rows 4-5): {[round(v,1) for v in high_load_values]}. "
                    f"Dangerous (>14.0) remaining: {dangerous_remaining}",
                    weight=2.0
                )
            else:
                add_check("Dangerous AFR targets corrected", False, "Could not parse AFR values from corrected MSQ", weight=2.0)
        else:
            add_check("Dangerous AFR targets corrected", False, "afrTable1 section not found in corrected MSQ", weight=2.0)
    except Exception as e:
        add_check("Dangerous AFR targets corrected", False, f"Error: {e}", weight=2.0)
else:
    add_check("Dangerous AFR targets corrected", False, "No corrected MSQ file", weight=2.0)

# ---- CHECK 9: Verify analyze_msq.py was actually used (script output evidence in review) ----
# The review should contain references to the analysis script output format OR
# contain findings consistent with running the script
if review_path:
    try:
        with open(review_path) as f:
            review_content = f.read()
        
        # Check for evidence that the analyzer was run - presence of structured findings
        has_structure = any(kw in review_content.lower() for kw in [
            "critical", "warning", "ve table", "spark", "afr", "required_fuel", "requiredfuel",
            "ignition", "injector", "summary", "issues"
        ])
        add_check(
            "Review shows structured analysis from analyzer tool",
            has_structure,
            f"Review should contain structured analysis findings. "
            f"Keywords found: {'yes' if has_structure else 'no'}",
            weight=1.0
        )
    except Exception as e:
        add_check("Review shows structured analysis", False, f"Error: {e}", weight=1.0)
else:
    add_check("Review shows structured analysis", False, "No review file", weight=1.0)

# ---- FINAL SCORING ----
final_score = total_score / max_score if max_score > 0 else 0.0

result = {
    "passed": final_score >= 0.65,
    "score": round(final_score, 3),
    "checks": checks
}

print(json.dumps(result, indent=2))