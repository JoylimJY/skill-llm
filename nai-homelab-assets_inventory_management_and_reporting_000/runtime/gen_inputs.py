import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "references",
    "assets",
    "docs/network",
    "docs/purchase_receipts",
    "docs/insurance",
    "logs/2023",
    "logs/2024",
    "backups/configs",
    "backups/snapshots",
    ".openclaw/workspace/homelab-assets",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
(workspace / "docs/network/topology.txt").write_text(
    "Core Switch -> TrueNAS -> Pi Cluster\nVLAN 10: Management\nVLAN 20: IoT\n"
)
(workspace / "docs/network/ip-allocations.csv").write_text(
    "hostname,ip,mac\ntrueNAS,192.168.1.10,AA:BB:CC:DD:EE:01\npi4-ha,192.168.1.11,AA:BB:CC:DD:EE:02\n"
)
(workspace / "docs/purchase_receipts/amazon_order_2023.txt").write_text(
    "Order #112-3456789\nRaspberry Pi 4 8GB - $85.00\nMicroSD 64GB - $12.99\nDate: 2023-06-15\n"
)
(workspace / "docs/purchase_receipts/newegg_order_2022.txt").write_text(
    "Order #45678123\nIntel NUC 11 Pro - $349.00\nDate: 2022-11-02\n"
)
(workspace / "docs/insurance/current_policy.txt").write_text(
    "Policy #: HO-2024-88771\nCoverage: Electronics up to $5000\nRenewal: 2025-03-01\n"
)
(workspace / "logs/2023/syslog-sample.txt").write_text(
    "2023-12-01 kernel: ata1.00 exception Emask 0x10\n2023-12-02 ups: low battery warning\n"
)
(workspace / "logs/2024/power-events.txt").write_text(
    "2024-07-14 03:22 UPS switched to battery\n2024-07-14 03:28 UPS overload detected\n2024-07-14 03:31 Shutdown initiated\n"
)
(workspace / "backups/configs/switch-config-2024.cfg").write_text(
    "interface GigabitEthernet0/1\n  switchport mode access\n  switchport access vlan 10\n"
)
(workspace / "backups/snapshots/snapshot_meta.json").write_text(
    json.dumps({"snapshot_date": "2024-07-13", "size_gb": 120, "status": "ok"}, indent=2)
)
(workspace / "references/power-estimates.md").write_text(
    """# Common Homelab Power Estimates

| Device            | Idle (W) | Load (W) |
|-------------------|----------|----------|
| Raspberry Pi 4    | 4        | 8        |
| Intel NUC 11      | 10       | 28       |
| Synology DS920+   | 15       | 30       |
| TP-Link TL-SG108E | 4        | 6        |
| APC Back-UPS 600  | 8        | 12       |
| 3.5" HDD          | 5        | 8        |
| SSD               | 1        | 3        |
"""
)

# ── Example inventory file (reference only, not the live inventory) ──────────
example_inventory = {
    "assets": [
        {
            "id": "aaaaaaaa-0000-0000-0000-000000000001",
            "name": "Example Server",
            "type": "server",
            "brand": "Example Brand",
            "model": "EX-1000",
            "purchase_date": "2022-01-01",
            "purchase_price": 500.0,
            "warranty_months": 24,
            "warranty_expires": "2024-01-01",
            "power_watts": 45,
            "location": "Rack U1",
            "serial": "SN00001",
            "status": "active",
            "notes": "Example only",
            "added_at": "2022-01-01T00:00:00"
        }
    ]
}
(workspace / "assets/inventory.example.json").write_text(
    json.dumps(example_inventory, indent=2)
)

# ── EMPTY live inventory (agent must populate it) ────────────────────────────
# The scripts expect the inventory at ~/.openclaw/workspace/homelab-assets/inventory.json
# We create the directory but leave inventory ABSENT so scripts auto-initialize
home_inv_dir = Path.home() / ".openclaw/workspace/homelab-assets"
home_inv_dir.mkdir(parents=True, exist_ok=True)
# Do NOT pre-create inventory.json — scripts should create it on first add

# ── The add_asset.py script ──────────────────────────────────────────────────
add_asset_py = r'''#!/usr/bin/env python3
"""add_asset.py — Add a hardware asset to the homelab inventory."""
import argparse, json, uuid, os
from pathlib import Path
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

INVENTORY_PATH = Path(os.environ.get(
    "HOMELAB_ASSETS_PATH",
    Path.home() / ".openclaw/workspace/homelab-assets/inventory.json"
))
VALID_TYPES = ["server","switch","router","ups","drive","cable","accessory","other"]
VALID_STATUSES = ["active","retired","sold","rma"]

def load_inventory():
    if INVENTORY_PATH.exists():
        return json.loads(INVENTORY_PATH.read_text())
    return {"assets": []}

def save_inventory(inv):
    INVENTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    INVENTORY_PATH.write_text(json.dumps(inv, indent=2))

def main():
    p = argparse.ArgumentParser(description="Add a hardware asset")
    p.add_argument("--name", required=True)
    p.add_argument("--type", required=True, choices=VALID_TYPES)
    p.add_argument("--brand", default=None)
    p.add_argument("--model", default=None)
    p.add_argument("--purchase-date", default=None)
    p.add_argument("--purchase-price", type=float, default=None)
    p.add_argument("--warranty-months", type=int, default=None)
    p.add_argument("--power-watts", type=int, default=None)
    p.add_argument("--location", default=None)
    p.add_argument("--serial", default=None)
    p.add_argument("--notes", default=None)
    p.add_argument("--status", default="active", choices=VALID_STATUSES)
    args = p.parse_args()

    warranty_expires = None
    if args.purchase_date and args.warranty_months:
        pd = date.fromisoformat(args.purchase_date)
        warranty_expires = (pd + relativedelta(months=args.warranty_months)).isoformat()

    asset = {
        "id": str(uuid.uuid4()),
        "name": args.name,
        "type": args.type,
        "brand": args.brand,
        "model": args.model,
        "purchase_date": args.purchase_date,
        "purchase_price": args.purchase_price,
        "warranty_months": args.warranty_months,
        "warranty_expires": warranty_expires,
        "power_watts": args.power_watts,
        "location": args.location,
        "serial": args.serial,
        "status": args.status,
        "notes": args.notes,
        "added_at": datetime.utcnow().isoformat()
    }
    inv = load_inventory()
    inv["assets"].append(asset)
    save_inventory(inv)
    print(f"Added asset '{args.name}' with ID {asset['id']}")

if __name__ == "__main__":
    main()
'''
(workspace / "scripts/add_asset.py").write_text(add_asset_py)

# ── The update_asset.py script ───────────────────────────────────────────────
update_asset_py = r'''#!/usr/bin/env python3
"""update_asset.py — Update an existing homelab asset."""
import argparse, json, os
from pathlib import Path

INVENTORY_PATH = Path(os.environ.get(
    "HOMELAB_ASSETS_PATH",
    Path.home() / ".openclaw/workspace/homelab-assets/inventory.json"
))
VALID_STATUSES = ["active","retired","sold","rma"]

def load_inventory():
    if INVENTORY_PATH.exists():
        return json.loads(INVENTORY_PATH.read_text())
    return {"assets": []}

def save_inventory(inv):
    INVENTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    INVENTORY_PATH.write_text(json.dumps(inv, indent=2))

def main():
    p = argparse.ArgumentParser(description="Update an existing asset")
    target = p.add_mutually_exclusive_group(required=True)
    target.add_argument("--id")
    target.add_argument("--search")
    p.add_argument("--status", choices=VALID_STATUSES)
    p.add_argument("--location")
    p.add_argument("--notes")
    p.add_argument("--power-watts", type=int)
    args = p.parse_args()

    inv = load_inventory()
    matched = []
    if args.id:
        matched = [a for a in inv["assets"] if a["id"] == args.id]
    else:
        term = args.search.lower()
        matched = [a for a in inv["assets"] if term in a["name"].lower()]

    if not matched:
        print("No matching asset found.")
        return
    if len(matched) > 1:
        print(f"Multiple matches: {[a['name'] for a in matched]}. Be more specific.")
        return

    asset = matched[0]
    if args.status:   asset["status"] = args.status
    if args.location: asset["location"] = args.location
    if args.notes:    asset["notes"] = args.notes
    if args.power_watts is not None: asset["power_watts"] = args.power_watts

    save_inventory(inv)
    print(f"Updated asset '{asset['name']}' ({asset['id']})")

if __name__ == "__main__":
    main()
'''
(workspace / "scripts/update_asset.py").write_text(update_asset_py)

# ── The inventory.py script ──────────────────────────────────────────────────
inventory_py = r'''#!/usr/bin/env python3
"""inventory.py — List homelab assets."""
import argparse, json, os
from pathlib import Path
from datetime import date, timedelta

INVENTORY_PATH = Path(os.environ.get(
    "HOMELAB_ASSETS_PATH",
    Path.home() / ".openclaw/workspace/homelab-assets/inventory.json"
))

def load_inventory():
    if INVENTORY_PATH.exists():
        return json.loads(INVENTORY_PATH.read_text())
    return {"assets": []}

def main():
    p = argparse.ArgumentParser(description="List homelab assets")
    p.add_argument("--type")
    p.add_argument("--status")
    p.add_argument("--location")
    p.add_argument("--warranty-expiring", type=int)
    p.add_argument("--output", choices=["table","json"], default="table")
    args = p.parse_args()

    inv = load_inventory()
    assets = inv["assets"]

    if args.type:     assets = [a for a in assets if a.get("type") == args.type]
    if args.status:   assets = [a for a in assets if a.get("status") == args.status]
    if args.location: assets = [a for a in assets if args.location.lower() in (a.get("location") or "").lower()]
    if args.warranty_expiring:
        cutoff = (date.today() + timedelta(days=args.warranty_expiring)).isoformat()
        today_str = date.today().isoformat()
        assets = [a for a in assets if a.get("warranty_expires") and today_str <= a["warranty_expires"] <= cutoff]

    if args.output == "json":
        print(json.dumps(assets, indent=2))
    else:
        try:
            from tabulate import tabulate
            rows = [[a.get("id","")[:8], a.get("name",""), a.get("type",""),
                     a.get("status",""), a.get("location",""), a.get("purchase_price",""),
                     a.get("warranty_expires","")] for a in assets]
            print(tabulate(rows, headers=["ID","Name","Type","Status","Location","Price","Warranty Exp"]))
        except ImportError:
            for a in assets:
                print(json.dumps(a))

if __name__ == "__main__":
    main()
'''
(workspace / "scripts/inventory.py").write_text(inventory_py)

# ── The report.py script ─────────────────────────────────────────────────────
report_py = r'''#!/usr/bin/env python3
"""report.py — Generate a full asset report."""
import argparse, json, os
from pathlib import Path
from datetime import date, timedelta

INVENTORY_PATH = Path(os.environ.get(
    "HOMELAB_ASSETS_PATH",
    Path.home() / ".openclaw/workspace/homelab-assets/inventory.json"
))

def load_inventory():
    if INVENTORY_PATH.exists():
        return json.loads(INVENTORY_PATH.read_text())
    return {"assets": []}

def depreciated_value(price, purchase_date_str, years=5):
    if not price or not purchase_date_str:
        return 0.0
    try:
        pd = date.fromisoformat(purchase_date_str)
        age_years = (date.today() - pd).days / 365.25
        remaining = max(0, years - age_years) / years
        return round(price * remaining, 2)
    except:
        return 0.0

def main():
    p = argparse.ArgumentParser(description="Generate asset report")
    p.add_argument("--kwh-rate", type=float, default=0.12)
    p.add_argument("--output", default=None)
    args = p.parse_args()

    inv = load_inventory()
    assets = inv["assets"]
    today = date.today()

    total_assets = len(assets)
    total_investment = sum(a.get("purchase_price") or 0 for a in assets)
    total_current_value = sum(depreciated_value(a.get("purchase_price"), a.get("purchase_date")) for a in assets)
    total_watts = sum(a.get("power_watts") or 0 for a in assets)
    monthly_kwh = total_watts * 24 * 30 / 1000
    monthly_cost = monthly_kwh * args.kwh_rate

    cutoff_90 = (today + timedelta(days=90)).isoformat()
    today_str = today.isoformat()
    expiring = [a for a in assets if a.get("warranty_expires") and today_str <= a["warranty_expires"] <= cutoff_90]

    by_type = {}
    for a in assets:
        t = a.get("type","other")
        by_type.setdefault(t, []).append(a["name"])

    by_loc = {}
    for a in assets:
        l = a.get("location") or "Unknown"
        by_loc.setdefault(l, []).append(a["name"])

    lines = []
    lines.append("# Homelab Asset Report")
    lines.append(f"\n**Generated:** {today.isoformat()}\n")
    lines.append("## Summary")
    lines.append(f"- **Total Assets:** {total_assets}")
    lines.append(f"- **Total Investment:** ${total_investment:,.2f}")
    lines.append(f"- **Estimated Current Value:** ${total_current_value:,.2f}")
    lines.append(f"- **Total Power Draw:** {total_watts} W")
    lines.append(f"- **Monthly Power Cost:** ${monthly_cost:,.2f} (@ ${args.kwh_rate}/kWh)")

    lines.append("\n## Warranty Alerts (Expiring Within 90 Days)")
    if expiring:
        for a in expiring:
            lines.append(f"- **{a['name']}** — expires {a['warranty_expires']} (Serial: {a.get('serial','N/A')})")
    else:
        lines.append("- No warranties expiring within 90 days.")

    lines.append("\n## Assets by Type")
    for t, names in sorted(by_type.items()):
        lines.append(f"### {t.capitalize()} ({len(names)})")
        for n in names:
            lines.append(f"- {n}")

    lines.append("\n## Assets by Location")
    for loc, names in sorted(by_loc.items()):
        lines.append(f"### {loc} ({len(names)})")
        for n in names:
            lines.append(f"- {n}")

    lines.append("\n## Full Asset List")
    for a in assets:
        lines.append(f"\n### {a['name']}")
        for k, v in a.items():
            if k != "name" and v is not None:
                lines.append(f"- **{k}:** {v}")

    report_text = "\n".join(lines) + "\n"

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(report_text)
        print(f"Report written to {out_path}")
    else:
        print(report_text)

if __name__ == "__main__":
    main()
'''
(workspace / "scripts/report.py").write_text(report_py)

# ── The search.py script ─────────────────────────────────────────────────────
search_py = r'''#!/usr/bin/env python3
"""search.py — Fuzzy search across all asset fields."""
import argparse, json, os
from pathlib import Path

INVENTORY_PATH = Path(os.environ.get(
    "HOMELAB_ASSETS_PATH",
    Path.home() / ".openclaw/workspace/homelab-assets/inventory.json"
))

def load_inventory():
    if INVENTORY_PATH.exists():
        return json.loads(INVENTORY_PATH.read_text())
    return {"assets": []}

def main():
    p = argparse.ArgumentParser(description="Search assets")
    p.add_argument("query")
    p.add_argument("--output", choices=["table","json"], default="table")
    args = p.parse_args()

    inv = load_inventory()
    q = args.query.lower()
    TEXT_FIELDS = ["name","brand","model","location","notes","serial","type"]

    results = []
    for a in inv["assets"]:
        for f in TEXT_FIELDS:
            v = a.get(f) or ""
            if q in v.lower():
                results.append(a)
                break

    if args.output == "json":
        print(json.dumps(results, indent=2))
    else:
        try:
            from tabulate import tabulate
            rows = [[a.get("id","")[:8], a.get("name",""), a.get("type",""),
                     a.get("status",""), a.get("location","")] for a in results]
            print(tabulate(rows, headers=["ID","Name","Type","Status","Location"]))
        except ImportError:
            for a in results:
                print(json.dumps(a))

if __name__ == "__main__":
    main()
'''
(workspace / "scripts/search.py").write_text(search_py)

print("Workspace initialized successfully.")
print("Scripts written to /workspace/scripts/")
print("Distractor files created across docs/, logs/, backups/, references/")