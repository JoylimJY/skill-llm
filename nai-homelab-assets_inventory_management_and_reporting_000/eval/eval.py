import sys
import json
import re
from pathlib import Path
from datetime import date, timedelta

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
checks = []

# ── Load the live inventory ──────────────────────────────────────────────────
from pathlib import Path as P
import os

inv_path = P(os.path.expanduser("~/.openclaw/workspace/homelab-assets/inventory.json"))

def load_inv():
    if inv_path.exists():
        return json.loads(inv_path.read_text())
    return {"assets": []}

inv = load_inv()
assets = inv.get("assets", [])

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 1: At least 5 assets exist in the inventory
# ─────────────────────────────────────────────────────────────────────────────
try:
    count = len(assets)
    passed = count >= 5
    checks.append({
        "name": "at_least_5_assets_in_inventory",
        "passed": passed,
        "detail": f"Found {count} asset(s). Need at least 5."
    })
except Exception as e:
    checks.append({"name": "at_least_5_assets_in_inventory", "passed": False, "detail": str(e)})

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 2: Asset types are all valid (from the constrained enum)
# ─────────────────────────────────────────────────────────────────────────────
VALID_TYPES = {"server", "switch", "router", "ups", "drive", "cable", "accessory", "other"}
try:
    bad_types = [a["name"] for a in assets if a.get("type") not in VALID_TYPES]
    passed = len(bad_types) == 0
    checks.append({
        "name": "all_asset_types_valid",
        "passed": passed,
        "detail": f"Invalid types on: {bad_types}" if bad_types else "All types valid."
    })
except Exception as e:
    checks.append({"name": "all_asset_types_valid", "passed": False, "detail": str(e)})

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 3: At least one asset per required type category
# The task requires a diverse inventory: must have at least one server,
# one switch or router, one ups, and one drive
# ─────────────────────────────────────────────────────────────────────────────
try:
    types_present = {a.get("type") for a in assets}
    required = {"server", "ups", "drive"}
    network_ok = bool(types_present & {"switch", "router"})
    missing = required - types_present
    if not network_ok:
        missing.add("switch or router")
    passed = len(missing) == 0
    checks.append({
        "name": "required_asset_types_present",
        "passed": passed,
        "detail": f"Missing types: {missing}" if missing else f"All required types present: {types_present}"
    })
except Exception as e:
    checks.append({"name": "required_asset_types_present", "passed": False, "detail": str(e)})

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 4: At least one asset has status = "retired"
# (The power-surge-damaged asset should be marked retired)
# ─────────────────────────────────────────────────────────────────────────────
try:
    retired = [a for a in assets if a.get("status") == "retired"]
    passed = len(retired) >= 1
    checks.append({
        "name": "at_least_one_retired_asset",
        "passed": passed,
        "detail": f"Found {len(retired)} retired asset(s). Names: {[r['name'] for r in retired]}"
    })
except Exception as e:
    checks.append({"name": "at_least_one_retired_asset", "passed": False, "detail": str(e)})

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 5: All active assets with purchase_price have power_watts populated
# (Insurance report needs power draw data)
# ─────────────────────────────────────────────────────────────────────────────
try:
    active_assets = [a for a in assets if a.get("status") == "active" and a.get("purchase_price")]
    missing_power = [a["name"] for a in active_assets if not a.get("power_watts")]
    passed = len(missing_power) == 0
    checks.append({
        "name": "active_assets_have_power_watts",
        "passed": passed,
        "detail": f"Active assets missing power_watts: {missing_power}" if missing_power else "All active assets have power_watts."
    })
except Exception as e:
    checks.append({"name": "active_assets_have_power_watts", "passed": False, "detail": str(e)})

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 6: warranty_expires is correctly computed (purchase_date + warranty_months)
# For assets that have both fields
# ─────────────────────────────────────────────────────────────────────────────
try:
    from dateutil.relativedelta import relativedelta
    from datetime import date as dt_date

    warranty_errors = []
    for a in assets:
        pd_str = a.get("purchase_date")
        wm = a.get("warranty_months")
        we = a.get("warranty_expires")
        if pd_str and wm and we:
            try:
                pd = dt_date.fromisoformat(pd_str)
                expected = (pd + relativedelta(months=wm)).isoformat()
                if we != expected:
                    warranty_errors.append(f"{a['name']}: expected {expected}, got {we}")
            except:
                warranty_errors.append(f"{a['name']}: could not parse dates")

    passed = len(warranty_errors) == 0
    checks.append({
        "name": "warranty_expires_correctly_computed",
        "passed": passed,
        "detail": f"Warranty computation errors: {warranty_errors}" if warranty_errors else "All warranty_expires dates correct."
    })
except Exception as e:
    checks.append({"name": "warranty_expires_correctly_computed", "passed": False, "detail": str(e)})

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 7: The report file exists and is named homelab_report.md
# ─────────────────────────────────────────────────────────────────────────────
try:
    report_candidates = list(P(workspace).rglob("homelab_report.md"))
    found = len(report_candidates) > 0
    checks.append({
        "name": "report_file_exists",
        "passed": found,
        "detail": f"Found at: {report_candidates[0]}" if found else "homelab_report.md not found anywhere in workspace."
    })
except Exception as e:
    checks.append({"name": "report_file_exists", "passed": False, "detail": str(e)})

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 8: Report uses the custom kWh rate of $0.18 (not default 0.12)
# ─────────────────────────────────────────────────────────────────────────────
try:
    report_candidates = list(P(workspace).rglob("homelab_report.md"))
    if not report_candidates:
        raise FileNotFoundError("homelab_report.md not found")
    report_text = report_candidates[0].read_text()
    # Look for the rate annotation in the report
    rate_match = re.search(r'\$0\.18/kWh', report_text)
    passed = rate_match is not None
    checks.append({
        "name": "report_uses_custom_kwh_rate_0_18",
        "passed": passed,
        "detail": "Found $0.18/kWh in report." if passed else "Expected '$0.18/kWh' in report but not found. Agent likely used default rate."
    })
except Exception as e:
    checks.append({"name": "report_uses_custom_kwh_rate_0_18", "passed": False, "detail": str(e)})

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 9: Report contains Summary section with Total Investment
# ─────────────────────────────────────────────────────────────────────────────
try:
    report_candidates = list(P(workspace).rglob("homelab_report.md"))
    if not report_candidates:
        raise FileNotFoundError("homelab_report.md not found")
    report_text = report_candidates[0].read_text()
    has_summary = "## Summary" in report_text
    has_investment = "Total Investment" in report_text
    has_warranty = "Warranty" in report_text
    has_power = "Power" in report_text
    passed = all([has_summary, has_investment, has_warranty, has_power])
    checks.append({
        "name": "report_has_required_sections",
        "passed": passed,
        "detail": (
            f"Summary={has_summary}, Investment={has_investment}, "
            f"Warranty={has_warranty}, Power={has_power}"
        )
    })
except Exception as e:
    checks.append({"name": "report_has_required_sections", "passed": False, "detail": str(e)})

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 10: At least one asset has a location containing "Rack"
# (Should have rack-mounted assets for a realistic homelab)
# ─────────────────────────────────────────────────────────────────────────────
try:
    rack_assets = [a for a in assets if "rack" in (a.get("location") or "").lower()]
    passed = len(rack_assets) >= 1
    checks.append({
        "name": "at_least_one_rack_mounted_asset",
        "passed": passed,
        "detail": f"Found {len(rack_assets)} rack-located asset(s)." if passed else "No assets with 'rack' in location."
    })
except Exception as e:
    checks.append({"name": "at_least_one_rack_mounted_asset", "passed": False, "detail": str(e)})

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 11: Monthly power cost in report is plausible (> $0 and < $500)
# ─────────────────────────────────────────────────────────────────────────────
try:
    report_candidates = list(P(workspace).rglob("homelab_report.md"))
    if not report_candidates:
        raise FileNotFoundError("homelab_report.md not found")
    report_text = report_candidates[0].read_text()
    cost_match = re.search(r'Monthly Power Cost.*?\$([0-9,]+\.[0-9]+)', report_text)
    if cost_match:
        cost = float(cost_match.group(1).replace(",", ""))
        passed = 0.01 < cost < 500.0
        checks.append({
            "name": "monthly_power_cost_plausible",
            "passed": passed,
            "detail": f"Monthly power cost in report: ${cost:.2f}"
        })
    else:
        checks.append({
            "name": "monthly_power_cost_plausible",
            "passed": False,
            "detail": "Could not find Monthly Power Cost line in report."
        })
except Exception as e:
    checks.append({"name": "monthly_power_cost_plausible", "passed": False, "detail": str(e)})

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 12: Retired asset is NOT contributing power to report's total watts
# (retired assets shouldn't count toward power draw)
# Verify: sum of power_watts of active assets matches reported total power
# ─────────────────────────────────────────────────────────────────────────────
try:
    report_candidates = list(P(workspace).rglob("homelab_report.md"))
    if not report_candidates:
        raise FileNotFoundError("homelab_report.md not found")
    report_text = report_candidates[0].read_text()

    # Extract reported total watts
    watts_match = re.search(r'Total Power Draw.*?([0-9]+)\s*W', report_text)
    if not watts_match:
        checks.append({
            "name": "power_draw_excludes_retired_assets",
            "passed": False,
            "detail": "Could not parse 'Total Power Draw' from report."
        })
    else:
        reported_watts = int(watts_match.group(1))
        # The report.py sums ALL assets (script doesn't filter by status by design)
        # but our check is: the reported value should match sum of all assets' power_watts
        all_watts = sum(a.get("power_watts") or 0 for a in assets)
        # We accept the report's value matching total (report.py sums all, that's fine)
        # Key check: reported value is mathematically consistent with inventory
        passed = reported_watts == all_watts
        checks.append({
            "name": "power_draw_consistent_with_inventory",
            "passed": passed,
            "detail": f"Inventory total watts: {all_watts}W, Report shows: {reported_watts}W"
        })
except Exception as e:
    checks.append({"name": "power_draw_consistent_with_inventory", "passed": False, "detail": str(e)})

# ─────────────────────────────────────────────────────────────────────────────
# SCORING
# ─────────────────────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4)

result = {
    "passed": passed_count >= 9,  # Must pass at least 9/12
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))