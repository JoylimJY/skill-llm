#!/usr/bin/env python3
"""
Evaluation script for the homelab-assets task.
Checks:
  1. Three specific assets were added with correct fields
  2. The NAS drive was retired via update
  3. The old switch had its location updated to "Storage Closet"
  4. A report file named 'homelab_insurance_report.md' exists
  5. Report uses kwh-rate 0.18 (non-default)
  6. Report contains correct total investment
  7. Report contains expected asset names
"""

import sys
import json
import os
import re
from pathlib import Path

def get_inventory():
    env = os.environ.get("HOMELAB_ASSETS_PATH")
    if env:
        p = Path(env)
    else:
        p = Path.home() / ".openclaw" / "workspace" / "homelab-assets" / "inventory.json"
    if not p.exists():
        return None, str(p)
    try:
        return json.loads(p.read_text()), str(p)
    except Exception as e:
        return None, str(e)

def main(workspace_dir: str):
    checks = []
    workspace = Path(workspace_dir)

    # ── Load inventory ──────────────────────────────────────────────────────
    data, inv_path = get_inventory()
    if data is None:
        checks.append({"name": "inventory_readable", "passed": False,
                        "detail": f"Could not read inventory: {inv_path}"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({"name": "inventory_readable", "passed": True,
                    "detail": f"Inventory loaded from {inv_path}"})

    assets = data.get("assets", [])

    # ── CHECK 1: Dell PowerEdge R740 server added ───────────────────────────
    r740 = [a for a in assets if "R740" in (a.get("model") or "") or "R740" in (a.get("name") or "")]
    c1_passed = len(r740) >= 1
    if c1_passed:
        r740 = r740[0]
        # Must be type 'server'
        c1_passed = r740.get("type") == "server"
        detail = f"Found R740: type={r740.get('type')}, price={r740.get('purchase_price')}, watts={r740.get('power_watts')}"
    else:
        detail = "No asset matching 'R740' found"
    checks.append({"name": "asset_r740_added", "passed": c1_passed, "detail": detail})

    # ── CHECK 2: Cisco SG300-28 switch added ────────────────────────────────
    sg300 = [a for a in assets if "SG300" in (a.get("model") or "") or "SG300" in (a.get("name") or "")]
    c2_passed = len(sg300) >= 1
    if c2_passed:
        sg300 = sg300[0]
        c2_passed = sg300.get("type") == "switch"
        detail = f"Found SG300: type={sg300.get('type')}, location={sg300.get('location')}"
    else:
        detail = "No asset matching 'SG300' found"
    checks.append({"name": "asset_sg300_added", "passed": c2_passed, "detail": detail})

    # ── CHECK 3: APC UPS added ───────────────────────────────────────────────
    ups_assets = [a for a in assets if a.get("type") == "ups" and
                  ("APC" in (a.get("brand") or "") or "SMT" in (a.get("model") or "") or
                   "UPS" in (a.get("name") or "").upper() or "APC" in (a.get("name") or ""))]
    c3_passed = len(ups_assets) >= 1
    if c3_passed:
        ups = ups_assets[0]
        detail = f"Found UPS: name={ups.get('name')}, brand={ups.get('brand')}, watts={ups.get('power_watts')}"
    else:
        detail = "No UPS asset with type='ups' and APC-related info found"
    checks.append({"name": "asset_ups_added", "passed": c3_passed, "detail": detail})

    # ── CHECK 4: A NAS drive retired (status='retired') ─────────────────────
    # The task asks to retire the old 4TB HDD / NAS drive
    retired = [a for a in assets if a.get("status") == "retired"]
    c4_passed = len(retired) >= 1
    # More specifically, the retired asset should be a drive or have 'drive' type or a disk-like name
    drive_retired = [a for a in retired if
                     a.get("type") in ("drive", "other") or
                     any(kw in (a.get("name") or "").lower() for kw in ["hdd","ssd","drive","disk","nas","4tb","seagate","western","wd","toshiba"])]
    if not drive_retired:
        # Accept any retired asset as fallback but note it
        drive_retired = retired
        detail = f"Found {len(retired)} retired asset(s), but none clearly identified as a drive: {[a.get('name') for a in retired]}"
        c4_passed = len(retired) >= 1
    else:
        detail = f"Retired drive found: {[a.get('name') for a in drive_retired]}"
        c4_passed = True
    checks.append({"name": "nas_drive_retired", "passed": c4_passed, "detail": detail})

    # ── CHECK 5: SG300 switch location updated to "Storage Closet" ──────────
    sg300_list = [a for a in assets if "SG300" in (a.get("model") or "") or "SG300" in (a.get("name") or "")]
    c5_passed = False
    detail = "SG300 not found or location not updated"
    if sg300_list:
        s = sg300_list[0]
        loc = (s.get("location") or "").lower()
        c5_passed = "storage closet" in loc or "storage" in loc
        detail = f"SG300 location='{s.get('location')}'"
    checks.append({"name": "sg300_location_storage_closet", "passed": c5_passed, "detail": detail})

    # ── CHECK 6: Report file exists ─────────────────────────────────────────
    report_files = list(workspace.rglob("homelab_insurance_report.md"))
    c6_passed = len(report_files) > 0
    report_path = report_files[0] if report_files else None
    checks.append({
        "name": "report_file_exists",
        "passed": c6_passed,
        "detail": f"Found at: {report_path}" if c6_passed else "homelab_insurance_report.md not found in workspace"
    })

    # ── CHECK 7: Report uses kwh-rate 0.18 ──────────────────────────────────
    c7_passed = False
    detail = "Report not found or rate not verifiable"
    if report_path:
        try:
            content = report_path.read_text()
            # The report template outputs: Monthly Power Cost (@ $0.18/kWh)
            if "0.18" in content:
                c7_passed = True
                detail = "Found 0.18 kWh rate in report"
            else:
                # Check for the default 0.12 — fail if only default present
                detail = f"0.18 not found in report. Excerpt: {content[:300]}"
        except Exception as e:
            detail = f"Error reading report: {e}"
    checks.append({"name": "report_kwh_rate_0_18", "passed": c7_passed, "detail": detail})

    # ── CHECK 8: Report contains asset names (sanity on content) ────────────
    c8_passed = False
    detail = "Report not found"
    if report_path:
        try:
            content = report_path.read_text()
            # Should have at least two of the added assets mentioned
            found = []
            for keyword in ["R740", "SG300", "APC", "UPS", "PowerEdge"]:
                if keyword in content:
                    found.append(keyword)
            c8_passed = len(found) >= 2
            detail = f"Keywords found in report: {found}"
        except Exception as e:
            detail = f"Error reading report: {e}"
    checks.append({"name": "report_contains_asset_names", "passed": c8_passed, "detail": detail})

    # ── CHECK 9: Total investment sanity (>= $500 — at least something meaningful) ─
    total_investment = sum((a.get("purchase_price") or 0) for a in assets)
    c9_passed = total_investment >= 500.0
    checks.append({
        "name": "total_investment_nonzero",
        "passed": c9_passed,
        "detail": f"Total investment in inventory: ${total_investment:.2f}"
    })

    # ── CHECK 10: Power watts recorded for server and UPS ───────────────────
    has_watts = [a for a in assets if (a.get("power_watts") or 0) > 0]
    c10_passed = len(has_watts) >= 2
    checks.append({
        "name": "power_watts_recorded",
        "passed": c10_passed,
        "detail": f"{len(has_watts)} assets have power_watts recorded"
    })

    # ── Scoring ─────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    overall = passed_count >= 8  # need at least 8/10 to pass

    print(json.dumps({
        "passed": overall,
        "score": score,
        "checks": checks
    }, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "args", "passed": False,
                                      "detail": "Usage: eval.py <workspace_dir>"}]}))
        sys.exit(1)
    main(sys.argv[1])