import sys
import json
import re
from pathlib import Path

workspace = Path(sys.argv[1])

checks = []

def find_report_file(workspace):
    """Search for nov_orders_report.json anywhere in the workspace."""
    candidates = list(workspace.rglob("nov_orders_report.json"))
    return candidates[0] if candidates else None

def make_check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

# ── Check 1: Report file exists ───────────────────────────────────────────────
report_path = find_report_file(workspace)
if report_path is None:
    checks.append(make_check("report_file_exists", False,
                              "nov_orders_report.json not found anywhere in workspace"))
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)
else:
    checks.append(make_check("report_file_exists", True,
                              f"Found at {report_path}"))

# ── Check 2: File is valid JSON ───────────────────────────────────────────────
try:
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()
    report_data = json.loads(content)
    checks.append(make_check("valid_json", True, "File parses as valid JSON"))
except Exception as e:
    checks.append(make_check("valid_json", False, f"JSON parse error: {e}"))
    result = {"passed": False, "score": 1.0/6, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

# ── Check 3: Contains November 2024 data (dt = 2024-11-01 partition used) ────
# The report should reflect data from the 2024-11-01 partition.
# We check that the data makes sense for that partition.
# Expected: query on orders_detail WHERE dt='2024-11-01' AND status='active'
# grouped by region, with NVL applied.
# Active orders on 2024-11-01: orders 10001,10002,10003,10005,10006,10007,10009,10010
# Grouped by region:
#   East: 10001(Alice Zhang), 10006(Eve Wu), 10010(Henry Liu) = 3
#   West: 10002(Bob Li), 10007(None→Unknown) = 2
#   North: 10003(None→Unknown) = 1
#   South: 10005(David Chen), 10009(Grace Zhao) = 2

content_str = json.dumps(report_data).lower()

# Check that the report mentions November 2024 or 2024-11-01 somewhere
nov_mentioned = (
    "2024-11" in content_str or
    "november" in content_str or
    "nov" in content_str
)
checks.append(make_check("contains_nov2024_reference", nov_mentioned,
    "Report should reference November 2024 / 2024-11 data" if not nov_mentioned
    else "November 2024 date reference found"))

# ── Check 4: Contains region-based order count data ──────────────────────────
# The report must contain region groupings with order counts.
# We look for either: rows/data array with region+order_count fields,
# or a summary dict.
has_region_data = False
regions_found = set()
counts_found = {}

def extract_rows(data):
    """Try to extract rows from various possible JSON shapes."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("rows", "data", "results", "records", "result"):
            if key in data and isinstance(data[key], list):
                return data[key]
        # Maybe it IS the grouped data directly as dict
        # e.g. {"East": 3, "West": 2, ...}
        region_keys = {"east", "west", "north", "south"}
        if any(k.lower() in region_keys for k in data.keys()):
            return [{"region": k, "order_count": v} for k, v in data.items()]
    return []

rows = extract_rows(report_data)

if rows:
    for row in rows:
        if isinstance(row, dict):
            # Normalize keys
            row_lower = {k.lower(): v for k, v in row.items()}
            region_val = row_lower.get("region", "")
            count_val = row_lower.get("order_count") or row_lower.get("count") or row_lower.get("orders")
            if region_val:
                regions_found.add(str(region_val).lower())
            if region_val and count_val is not None:
                try:
                    counts_found[str(region_val).lower()] = int(count_val)
                except (ValueError, TypeError):
                    pass

has_region_data = len(regions_found) >= 2
checks.append(make_check("has_region_grouping", has_region_data,
    f"Regions found: {regions_found}" if has_region_data
    else "Could not find region-grouped data in report"))

# ── Check 5: Order counts are correct (validates ODPS SQL was executed correctly) ─
# Expected active order counts for 2024-11-01 grouped by region:
# East=3, West=2, North=1, South=2
# We'll check at least two regions match.
EXPECTED_COUNTS = {"east": 3, "west": 2, "north": 1, "south": 2}

correct_count_matches = 0
count_details = []
for region, expected in EXPECTED_COUNTS.items():
    actual = counts_found.get(region)
    if actual == expected:
        correct_count_matches += 1
        count_details.append(f"{region}: OK ({actual})")
    else:
        count_details.append(f"{region}: expected {expected}, got {actual}")

counts_correct = correct_count_matches >= 3
checks.append(make_check("correct_order_counts", counts_correct,
    "; ".join(count_details)))

# ── Check 6: NVL was applied — 'Unknown' appears for null customer names ──────
# In the active orders data, order_ids 10003 and 10007 have null customer_name.
# If NVL was applied, 'Unknown' should appear in the output or the query
# (the mock enforces NVL; IFNULL would have caused an error from the mock).
# Since we're querying grouped-by-region, NVL affects intermediate processing.
# The mock correctly applies NVL internally when NVL() is in the SQL.
# We verify indirectly: if the count for North is 1 and West is 2,
# those null-name rows were counted (not silently dropped), suggesting NVL was used.
# Additionally, we can check if 'unknown' appears in the report for descriptive content.
unknown_in_report = "unknown" in content_str
nvl_applied = counts_found.get("north", 0) == 1 and counts_found.get("west", 0) == 2

nvl_check_passed = nvl_applied or unknown_in_report
checks.append(make_check("nvl_applied_for_null_names", nvl_check_passed,
    "NVL applied: null customer_names counted correctly (North=1, West=2 include null-name rows)"
    if nvl_check_passed
    else "NVL not properly applied: null customer_name rows may have been excluded"))

# ── Final scoring ─────────────────────────────────────────────────────────────
num_passed = sum(1 for c in checks if c["passed"])
score = round(num_passed / len(checks), 4)
passed = num_passed >= 5  # Must pass at least 5 out of 6 checks

result = {
    "passed": passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))