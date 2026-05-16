import sys
import json
import re
import math
from pathlib import Path
from datetime import date

workspace = Path(sys.argv[1])

checks = []
score = 0.0

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

# ─── Locate the report file ───────────────────────────────────────────────────
# Expected: ~/.openclaw/workspace/properties/comps-14-birchwood-lane-natick-<date>.md
# We search for any file matching the pattern.
props_dir = workspace / ".openclaw" / "workspace" / "properties"
today_str = date.today().isoformat()  # e.g. 2025-01-15

report_files = list(props_dir.glob("comps-14-birchwood-lane-natick-*.md"))
# Exclude the old distractor
report_files = [f for f in report_files if "framingham" not in f.name.lower()]

if not report_files:
    add_check("report_file_exists", False, f"No file matching comps-14-birchwood-lane-natick-*.md found in {props_dir}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

report_file = report_files[0]
add_check("report_file_exists", True, f"Found report: {report_file.name}")
score += 0.05

try:
    content = report_file.read_text()
except Exception as e:
    add_check("report_readable", False, f"Cannot read file: {e}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

add_check("report_readable", True, "Report file is readable")
score += 0.05

# ─── Check file naming convention ─────────────────────────────────────────────
# Must be comps-14-birchwood-lane-natick-YYYY-MM-DD.md  (address slug + date)
name_pattern = re.compile(r'^comps-14-birchwood-lane-natick-\d{4}-\d{2}-\d{2}\.md$')
name_ok = bool(name_pattern.match(report_file.name))
add_check("file_naming_convention", name_ok,
          f"File name '{report_file.name}' {'matches' if name_ok else 'does NOT match'} expected pattern comps-14-birchwood-lane-natick-YYYY-MM-DD.md")
if name_ok:
    score += 0.05

# ─── Subject property section ─────────────────────────────────────────────────
has_subject_header = "SUBJECT PROPERTY" in content.upper()
add_check("subject_property_section", has_subject_header,
          "Report contains SUBJECT PROPERTY section" if has_subject_header else "Missing SUBJECT PROPERTY section")
if has_subject_header:
    score += 0.03

subject_details_ok = all(x in content for x in ["14 Birchwood", "Natick", "2", "920"])
add_check("subject_property_details", subject_details_ok,
          "Subject property details (address, city, sqft) present" if subject_details_ok else "Missing key subject property details (address/sqft/beds)")
if subject_details_ok:
    score += 0.04

current_rent_ok = "1950" in content or "$1,950" in content
add_check("current_rent_present", current_rent_ok,
          "Current rent $1,950 present" if current_rent_ok else "Current rent $1,950 not found in report")
if current_rent_ok:
    score += 0.03

# ─── Comparable Properties section ────────────────────────────────────────────
has_comps_section = bool(re.search(r'COMPARABLE PROPERTIES', content, re.IGNORECASE))
add_check("comps_section_present", has_comps_section,
          "COMPARABLE PROPERTIES section present" if has_comps_section else "Missing COMPARABLE PROPERTIES section")
if has_comps_section:
    score += 0.03

# All 5 comp addresses should appear
comp_addresses = [
    "8 Chestnut",
    "31 Oak Terrace",
    "102 Pine Ridge",
    "55 Walnut",
    "19 Elmwood"
]
comps_found = sum(1 for addr in comp_addresses if addr in content)
comps_all_present = comps_found == 5
add_check("all_5_comps_present", comps_all_present,
          f"{comps_found}/5 comp addresses found in report")
if comps_all_present:
    score += 0.05
elif comps_found >= 3:
    score += 0.02

# ─── Adjustment logic validation ──────────────────────────────────────────────
# Subject: parking=T, in-unit laundry, central A/C, no-pets, updated
# Comp 2: 31 Oak Terrace — no parking, no laundry, no A/C → needs +75~150 (parking), +50~100 (laundry), +50~75 (A/C)
#   listed: 1875 → adjusted should be in range [1875+175, 1875+325] = [2050, 2200]
# Comp 3: 102 Pine Ridge — parking=T, shared laundry→+50-100, window AC→+50-75, average→+100-200
#   listed: 1950 → adjusted: [1950+200, 1950+375] = [2150, 2325]
# Comp 4: 55 Walnut — 2ba vs subject 1ba → subject has fewer baths, so comp is better → -75 to -150
#   listed: 2100 → adjusted: [2100-150, 2100-75] = [1950, 2025]
# Comp 5: 19 Elmwood — no parking (+75-150), no laundry (+50-100), no A/C (+50-75), pets(+25-50), average(+100-200)
#   listed: 1800 → adjusted: [1800+300, 1800+575] = [2100, 2375]
# Comp 1: 8 Chestnut — nearly identical → adjusted ≈ listed = 2050 (maybe +/- small)

# We check that adjustments section mentions dollar amounts for comp 2 and comp 5 (most adjustments)
has_adjustments = bool(re.search(r'[Aa]djustment', content))
add_check("adjustments_section_present", has_adjustments,
          "Adjustment details present in report" if has_adjustments else "No adjustment details found")
if has_adjustments:
    score += 0.04

# Check that adjusted rent for comp 2 is in a plausible range [2050, 2200]
# Extract dollar amounts near "31 Oak" or "Comp 2"
comp2_section = ""
comp2_match = re.search(r'31 Oak Terrace.*?(?=Comp \d|ANALYSIS|$)', content, re.DOTALL | re.IGNORECASE)
if comp2_match:
    comp2_section = comp2_match.group(0)

adjusted_amounts_comp2 = [int(m.replace(',', '')) for m in re.findall(r'\$?([\d,]{4,6})', comp2_section)]
comp2_adjusted_ok = any(2050 <= v <= 2250 for v in adjusted_amounts_comp2)
add_check("comp2_adjustment_correct", comp2_adjusted_ok,
          f"Comp 2 (31 Oak Terrace) adjusted rent in range $2050-$2250. Found values: {adjusted_amounts_comp2}"
          if adjusted_amounts_comp2 else "Could not find adjusted rent for Comp 2")
if comp2_adjusted_ok:
    score += 0.05

# ─── Analysis section ─────────────────────────────────────────────────────────
has_analysis = bool(re.search(r'ANALYSIS', content, re.IGNORECASE))
add_check("analysis_section_present", has_analysis,
          "ANALYSIS section present" if has_analysis else "Missing ANALYSIS section")
if has_analysis:
    score += 0.03

has_average = bool(re.search(r'[Aa]verage.*\$[\d,]+', content))
has_median = bool(re.search(r'[Mm]edian.*\$[\d,]+', content))
add_check("average_and_median_reported", has_average and has_median,
          "Both average and median adjusted rents are reported"
          if (has_average and has_median) else f"average={has_average}, median={has_median}")
if has_average and has_median:
    score += 0.05

has_range = bool(re.search(r'[Rr]ange.*\$[\d,]+.*\$[\d,]+', content))
add_check("range_reported", has_range,
          "Rent range (low - high) reported" if has_range else "Rent range not found")
if has_range:
    score += 0.03

# ─── RECOMMENDATION section ───────────────────────────────────────────────────
has_recommendation = bool(re.search(r'RECOMMENDATION', content, re.IGNORECASE))
add_check("recommendation_section_present", has_recommendation,
          "RECOMMENDATION section present" if has_recommendation else "Missing RECOMMENDATION section")
if has_recommendation:
    score += 0.03

# Recommended rent: formula = avg(mean, median) rounded to nearest $25 or $50
# Let's compute plausible range of adjusted rents:
# Comp1: ~2050 (no adjustments needed, similar)
# Comp2: 1875 + 75..150 (parking) + 50..100 (laundry) + 50..75 (A/C) = 2050..2200
# Comp3: 1950 + 50..100 (shared→in-unit) + 50..75 (window→central) + 100..200 (avg→updated) = 2150..2325
# Comp4: 2100 - 75..-150 (extra bath comp has, subject doesn't) = 1950..2025
# Comp5: 1800 + 75..150 (parking) + 50..100 (laundry) + 50..75 (A/C) + 25..50 (pets) + 100..200 (avg→updated) = 2100..2375

# Use midpoints for plausibility:
# Comp1: 2050, Comp2: 2125, Comp3: 2238, Comp4: 1988, Comp5: 2238
# Mean ~ (2050+2125+2238+1988+2238)/5 = 10639/5 = 2127.8
# Sorted: 1988, 2050, 2125, 2238, 2238 → Median = 2125
# Avg of mean+median = (2127.8+2125)/2 = 2126.4 → round to nearest $25 = $2125, or $50 = $2150
# Acceptable range for recommended rent: $2050 - $2200

rec_rent_match = re.search(r'[Rr]ecommended rent[:\s]*\$?([\d,]+)', content)
if rec_rent_match:
    rec_rent_val = int(rec_rent_match.group(1).replace(',', ''))
    rec_rent_plausible = 2000 <= rec_rent_val <= 2250
    # Also check it's a multiple of 25
    rec_rent_rounded = (rec_rent_val % 25 == 0)
    add_check("recommended_rent_plausible", rec_rent_plausible,
              f"Recommended rent ${rec_rent_val} is {'within' if rec_rent_plausible else 'outside'} plausible range $2000-$2250")
    add_check("recommended_rent_rounded_correctly", rec_rent_rounded,
              f"Recommended rent ${rec_rent_val} is {'a multiple of $25' if rec_rent_rounded else 'NOT rounded to nearest $25 or $50'}")
    if rec_rent_plausible:
        score += 0.08
    if rec_rent_rounded:
        score += 0.05
else:
    add_check("recommended_rent_plausible", False, "Could not find 'Recommended rent: $X' in report")
    add_check("recommended_rent_rounded_correctly", False, "Could not find recommended rent value")

# ─── Avg of mean and median formula (not just mean alone) ─────────────────────
# Detect that BOTH average and median are used to derive recommendation
# This is the proprietary trap — agent must compute avg(mean, median)
both_used_for_rec = bool(
    re.search(r'(average of|mean and median|median.*average|avg.*mean|mean.*median)', content, re.IGNORECASE)
)
add_check("formula_avg_of_mean_and_median", both_used_for_rec,
          "Report shows recommended rent is derived from average of mean and median"
          if both_used_for_rec else "No evidence of avg(mean, median) formula — agent may have only used mean or median alone")
if both_used_for_rec:
    score += 0.05

# ─── Renewal section: current rent, market rent, increase amount & % ──────────
has_current_rent_renewal = bool(re.search(r'[Cc]urrent rent.*\$1[,.]?950', content))
add_check("renewal_current_rent", has_current_rent_renewal,
          "Renewal section shows current rent $1,950" if has_current_rent_renewal else "Current rent $1,950 not found in renewal section")
if has_current_rent_renewal:
    score += 0.04

has_suggested_increase = bool(re.search(r'[Ss]uggested increase.*\$[\d]+', content))
add_check("suggested_increase_present", has_suggested_increase,
          "Suggested increase amount present" if has_suggested_increase else "Missing suggested increase dollar amount")
if has_suggested_increase:
    score += 0.04

has_increase_pct = bool(re.search(r'[Ss]uggested increase.*\d+(\.\d+)?%', content))
add_check("suggested_increase_percentage", has_increase_pct,
          "Suggested increase percentage present" if has_increase_pct else "Missing suggested increase percentage")
if has_increase_pct:
    score += 0.04

# ─── MA-specific legal notes ──────────────────────────────────────────────────
has_no_rent_control = bool(re.search(r'no rent control|rent control.*MA|MA.*rent control', content, re.IGNORECASE))
add_check("ma_no_rent_control_note", has_no_rent_control,
          "MA no rent control note present" if has_no_rent_control else "Missing MA rent control note")
if has_no_rent_control:
    score += 0.04

has_30days = bool(re.search(r'30.?day', content, re.IGNORECASE))
add_check("ma_30_days_notice", has_30days,
          "30 days notice requirement mentioned" if has_30days else "Missing 30 days notice requirement")
if has_30days:
    score += 0.04

has_mgl = bool(re.search(r'MGL|c\.186|186', content, re.IGNORECASE))
add_check("ma_mgl_citation", has_mgl,
          "MGL c.186 cited" if has_mgl else "Missing MGL c.186 citation")
if has_mgl:
    score += 0.03

has_lease_renewal_note = bool(re.search(r'(renewal|renew).*(effect|takes effect|at renewal)', content, re.IGNORECASE))
add_check("ma_lease_renewal_timing_note", has_lease_renewal_note,
          "Note about increase taking effect at renewal present" if has_lease_renewal_note else "Missing note about increase timing at lease renewal")
if has_lease_renewal_note:
    score += 0.03

# ─── Confidence level ─────────────────────────────────────────────────────────
has_confidence = bool(re.search(r'[Cc]onfidence.*[Hh]igh|[Cc]onfidence.*[Mm]edium|[Cc]onfidence.*[Ll]ow', content))
add_check("confidence_level_present", has_confidence,
          "Confidence level (High/Medium/Low) present" if has_confidence else "Missing confidence level")
if has_confidence:
    score += 0.03

# ─── Max 5 comps rule ─────────────────────────────────────────────────────────
comp_count_matches = re.findall(r'Comp \d+', content)
comp_numbers = [int(re.search(r'\d+', c).group()) for c in comp_count_matches]
max_comp_num = max(comp_numbers) if comp_numbers else 0
within_5_comps = max_comp_num <= 5
add_check("max_5_comps_rule", within_5_comps,
          f"Report contains {max_comp_num} comps (≤5 allowed)" if within_5_comps else f"Report contains {max_comp_num} comps — exceeds 5 comp maximum")
if within_5_comps and max_comp_num > 0:
    score += 0.03

# ─── File saved in correct directory ──────────────────────────────────────────
correct_dir = report_file.parent == props_dir
add_check("file_in_correct_directory", correct_dir,
          f"File saved in correct directory: {report_file.parent}"
          if correct_dir else f"File in wrong directory: {report_file.parent} (expected {props_dir})")
if correct_dir:
    score += 0.04

# ─── Final scoring ────────────────────────────────────────────────────────────
score = min(round(score, 3), 1.0)
passed = score >= 0.60

print(json.dumps({
    "passed": passed,
    "score": score,
    "checks": checks
}, indent=2))