import os
import json
import random
import uuid
import stat
from pathlib import Path
from datetime import datetime, date

random.seed(42)

workspace = Path(os.environ.get("WORKSPACE_DIR", "/workspace"))

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "references",
    "assets",
    "docs",
    "logs",
    "backups/2024",
    "backups/2023",
    "configs/network",
    "configs/storage",
    "reports/drafts",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── SKILL.md ─────────────────────────────────────────────────────────────────
skill_md = '''\
---
name: homelab-assets
description: Track and manage homelab hardware inventory — servers, switches, UPS units, drives, cables, and accessories. Records purchase dates, prices, warranty expiration, power draw, and physical location. Answers questions like "What\'s my total homelab spend?", "What warranties expire this year?", "What\'s my estimated monthly power cost?", and generates insurance-ready asset reports. Triggers on: homelab inventory, hardware assets, what hardware do I have, warranty check, homelab spend, asset tracker, insurance report, homelab hardware, track hardware.
---

# Homelab Assets Skill

Manages a local JSON inventory of homelab hardware. All data lives at `~/.openclaw/workspace/homelab-assets/inventory.json`.

## Scripts

All scripts live in `scripts/`. Run with `python3 scripts/<script>.py [args]`. Use `--help` on any script for full usage.

### add_asset.py — Add a hardware asset

```
python3 scripts/add_asset.py \\
  --name "Raspberry Pi 4" \\
  --type server \\
  --brand "Raspberry Pi Foundation" \\
  --model "Pi 4 Model B 8GB" \\
  --purchase-date 2023-06-15 \\
  --purchase-price 85.00 \\
  --warranty-months 12 \\
  --power-watts 8 \\
  --location "Rack Shelf 2" \\
  --serial ABC123 \\
  --notes "Runs Home Assistant"
```

Required: `--name`, `--type`. All others optional. UUID auto-generated.
Types: `server`, `switch`, `router`, `ups`, `drive`, `cable`, `accessory`, `other`

### update_asset.py — Update an existing asset

```
python3 scripts/update_asset.py --id <uuid> --status retired --location "Storage Box A"
python3 scripts/update_asset.py --search "Pi 4" --notes "Repurposed as DNS server" --power-watts 6
```

Target by `--id` (exact UUID) or `--search` (fuzzy name match). Updatable fields: `--status`, `--location`, `--notes`, `--power-watts`.
Statuses: `active`, `retired`, `sold`, `rma`

### inventory.py — List assets

```
python3 scripts/inventory.py
python3 scripts/inventory.py --type server --status active
python3 scripts/inventory.py --location "Rack" --warranty-expiring 90
python3 scripts/inventory.py --output json
```

Filters: `--type`, `--status`, `--location` (substring), `--warranty-expiring <days>`. Output: table (default) or `--output json`.

### report.py — Generate full asset report

```
python3 scripts/report.py
python3 scripts/report.py --kwh-rate 0.14 --output report.md
```

Produces Markdown with: total assets, total investment, estimated current value (straight-line depreciation over 5 years), total power draw, monthly power cost estimate, warranty alerts (expiring within 90 days), assets by type, assets by location. Configurable `--kwh-rate` (default: 0.12).

### search.py — Fuzzy search across all fields

```
python3 scripts/search.py "raspberry"
python3 scripts/search.py "rack shelf" --output json
```

Searches name, brand, model, location, notes, serial, type. Case-insensitive substring match across all text fields.

## Data Location

Default: `~/.openclaw/workspace/homelab-assets/inventory.json`
Override with env var: `HOMELAB_ASSETS_PATH=/path/to/inventory.json`

## References

See `references/power-estimates.md` for common homelab device power draw estimates.
See `assets/inventory.example.json` for example asset structure.
'''
(workspace / "SKILL.md").write_text(skill_md)

# ── inventory.json bootstrap (empty) ─────────────────────────────────────────
inv_dir = Path.home() / ".openclaw" / "workspace" / "homelab-assets"
inv_dir.mkdir(parents=True, exist_ok=True)
inv_path = inv_dir / "inventory.json"
if not inv_path.exists():
    inv_path.write_text(json.dumps({"assets": []}, indent=2))

# ── scripts/add_asset.py ──────────────────────────────────────────────────────
add_asset_py = '''\
#!/usr/bin/env python3
"""Add a hardware asset to the homelab inventory."""
import argparse, json, uuid, os, sys
from datetime import datetime, date
from pathlib import Path

VALID_TYPES = {"server","switch","router","ups","drive","cable","accessory","other"}
VALID_STATUSES = {"active","retired","sold","rma"}

def get_inventory_path():
    env = os.environ.get("HOMELAB_ASSETS_PATH")
    if env:
        return Path(env)
    return Path.home() / ".openclaw" / "workspace" / "homelab-assets" / "inventory.json"

def load(path):
    if path.exists():
        return json.loads(path.read_text())
    return {"assets": []}

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))

def main():
    p = argparse.ArgumentParser(description="Add a hardware asset")
    p.add_argument("--name", required=True)
    p.add_argument("--type", required=True, dest="asset_type")
    p.add_argument("--brand", default="")
    p.add_argument("--model", default="")
    p.add_argument("--purchase-date", default=None)
    p.add_argument("--purchase-price", type=float, default=None)
    p.add_argument("--warranty-months", type=int, default=None)
    p.add_argument("--power-watts", type=float, default=None)
    p.add_argument("--location", default="")
    p.add_argument("--serial", default="")
    p.add_argument("--notes", default="")
    p.add_argument("--status", default="active")
    args = p.parse_args()

    if args.asset_type not in VALID_TYPES:
        print(f"ERROR: invalid type \'{args.asset_type}\'. Must be one of: {sorted(VALID_TYPES)}", file=sys.stderr)
        sys.exit(1)
    if args.status not in VALID_STATUSES:
        print(f"ERROR: invalid status.", file=sys.stderr)
        sys.exit(1)

    warranty_expiry = None
    if args.purchase_date and args.warranty_months:
        pd = datetime.strptime(args.purchase_date, "%Y-%m-%d").date()
        import calendar
        month = pd.month - 1 + args.warranty_months
        year = pd.year + month // 12
        month = month % 12 + 1
        day = min(pd.day, calendar.monthrange(year, month)[1])
        warranty_expiry = str(date(year, month, day))

    asset = {
        "id": str(uuid.uuid4()),
        "name": args.name,
        "type": args.asset_type,
        "brand": args.brand,
        "model": args.model,
        "purchase_date": args.purchase_date,
        "purchase_price": args.purchase_price,
        "warranty_months": args.warranty_months,
        "warranty_expiry": warranty_expiry,
        "power_watts": args.power_watts,
        "location": args.location,
        "serial": args.serial,
        "notes": args.notes,
        "status": args.status,
        "added_at": datetime.now().isoformat(),
    }

    path = get_inventory_path()
    data = load(path)
    data["assets"].append(asset)
    save(path, data)
    print(f"Added asset: {args.name} [{asset[\'id\']}]")

if __name__ == "__main__":
    main()
'''
(workspace / "scripts" / "add_asset.py").write_text(add_asset_py)

# ── scripts/update_asset.py ───────────────────────────────────────────────────
update_asset_py = '''\
#!/usr/bin/env python3
"""Update an existing homelab asset."""
import argparse, json, os, sys
from pathlib import Path

VALID_STATUSES = {"active","retired","sold","rma"}

def get_inventory_path():
    env = os.environ.get("HOMELAB_ASSETS_PATH")
    if env:
        return Path(env)
    return Path.home() / ".openclaw" / "workspace" / "homelab-assets" / "inventory.json"

def load(path):
    if path.exists():
        return json.loads(path.read_text())
    return {"assets": []}

def save(path, data):
    path.write_text(json.dumps(data, indent=2, default=str))

def fuzzy_match(name, query):
    return query.lower() in name.lower()

def main():
    p = argparse.ArgumentParser(description="Update a homelab asset")
    p.add_argument("--id", default=None, help="Exact asset UUID")
    p.add_argument("--search", default=None, help="Fuzzy name match")
    p.add_argument("--status", default=None)
    p.add_argument("--location", default=None)
    p.add_argument("--notes", default=None)
    p.add_argument("--power-watts", type=float, default=None)
    args = p.parse_args()

    if not args.id and not args.search:
        print("ERROR: must supply --id or --search", file=sys.stderr)
        sys.exit(1)

    if args.status and args.status not in VALID_STATUSES:
        print(f"ERROR: invalid status \'{args.status}\'", file=sys.stderr)
        sys.exit(1)

    path = get_inventory_path()
    data = load(path)
    matched = []
    for asset in data["assets"]:
        if args.id and asset["id"] == args.id:
            matched.append(asset)
        elif args.search and fuzzy_match(asset["name"], args.search):
            matched.append(asset)

    if not matched:
        print("ERROR: no matching asset found", file=sys.stderr)
        sys.exit(1)
    if len(matched) > 1:
        print(f"WARNING: {len(matched)} assets matched. Updating all.")

    for asset in matched:
        if args.status is not None:
            asset["status"] = args.status
        if args.location is not None:
            asset["location"] = args.location
        if args.notes is not None:
            asset["notes"] = args.notes
        if args.power_watts is not None:
            asset["power_watts"] = args.power_watts
        print(f"Updated: {asset[\'name\']} [{asset[\'id\']}]")

    save(path, data)

if __name__ == "__main__":
    main()
'''
(workspace / "scripts" / "update_asset.py").write_text(update_asset_py)

# ── scripts/inventory.py ──────────────────────────────────────────────────────
inventory_py = '''\
#!/usr/bin/env python3
"""List homelab assets with optional filters."""
import argparse, json, os
from datetime import date, datetime
from pathlib import Path

def get_inventory_path():
    env = os.environ.get("HOMELAB_ASSETS_PATH")
    if env:
        return Path(env)
    return Path.home() / ".openclaw" / "workspace" / "homelab-assets" / "inventory.json"

def load(path):
    if path.exists():
        return json.loads(path.read_text())
    return {"assets": []}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--type", default=None)
    p.add_argument("--status", default=None)
    p.add_argument("--location", default=None)
    p.add_argument("--warranty-expiring", type=int, default=None)
    p.add_argument("--output", default="table", choices=["table","json"])
    args = p.parse_args()

    data = load(get_inventory_path())
    assets = data["assets"]

    if args.type:
        assets = [a for a in assets if a.get("type") == args.type]
    if args.status:
        assets = [a for a in assets if a.get("status") == args.status]
    if args.location:
        assets = [a for a in assets if args.location.lower() in (a.get("location") or "").lower()]
    if args.warranty_expiring is not None:
        today = date.today()
        def within(a):
            we = a.get("warranty_expiry")
            if not we:
                return False
            exp = datetime.strptime(we, "%Y-%m-%d").date()
            delta = (exp - today).days
            return 0 <= delta <= args.warranty_expiring
        assets = [a for a in assets if within(a)]

    if args.output == "json":
        print(json.dumps(assets, indent=2, default=str))
    else:
        if not assets:
            print("No assets found.")
            return
        cols = ["name","type","status","location","purchase_price","power_watts","warranty_expiry"]
        header = " | ".join(f"{c:20}" for c in cols)
        print(header)
        print("-" * len(header))
        for a in assets:
            row = " | ".join(f"{str(a.get(c,\'\') or \'\'):20}" for c in cols)
            print(row)

if __name__ == "__main__":
    main()
'''
(workspace / "scripts" / "inventory.py").write_text(inventory_py)

# ── scripts/report.py ─────────────────────────────────────────────────────────
report_py = '''\
#!/usr/bin/env python3
"""Generate a full Markdown asset report."""
import argparse, json, os
from datetime import date, datetime
from pathlib import Path

def get_inventory_path():
    env = os.environ.get("HOMELAB_ASSETS_PATH")
    if env:
        return Path(env)
    return Path.home() / ".openclaw" / "workspace" / "homelab-assets" / "inventory.json"

def load(path):
    if path.exists():
        return json.loads(path.read_text())
    return {"assets": []}

def depreciated_value(price, purchase_date, years=5):
    if not price or not purchase_date:
        return 0.0
    try:
        pd = datetime.strptime(purchase_date, "%Y-%m-%d").date()
    except Exception:
        return price
    age_years = (date.today() - pd).days / 365.25
    remaining = max(0, 1 - age_years / years)
    return round(price * remaining, 2)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--kwh-rate", type=float, default=0.12)
    p.add_argument("--output", default=None, help="Output file path")
    args = p.parse_args()

    data = load(get_inventory_path())
    assets = data["assets"]
    active = [a for a in assets if a.get("status","active") == "active"]

    total_assets = len(assets)
    total_investment = sum((a.get("purchase_price") or 0) for a in assets)
    current_value = sum(depreciated_value(a.get("purchase_price"), a.get("purchase_date")) for a in assets)
    total_watts = sum((a.get("power_watts") or 0) for a in active)
    monthly_kwh = total_watts * 24 * 30 / 1000
    monthly_cost = monthly_kwh * args.kwh_rate

    today = date.today()
    expiring = []
    for a in assets:
        we = a.get("warranty_expiry")
        if we:
            exp = datetime.strptime(we, "%Y-%m-%d").date()
            delta = (exp - today).days
            if 0 <= delta <= 90:
                expiring.append((a["name"], we, delta))

    by_type = {}
    for a in assets:
        t = a.get("type","other")
        by_type.setdefault(t, []).append(a)

    by_loc = {}
    for a in assets:
        loc = a.get("location") or "Unknown"
        by_loc.setdefault(loc, []).append(a)

    lines = []
    lines.append("# Homelab Asset Report")
    lines.append(f"\\n_Generated: {today}_\\n")
    lines.append("## Summary")
    lines.append(f"- **Total Assets:** {total_assets}")
    lines.append(f"- **Total Investment:** ${total_investment:,.2f}")
    lines.append(f"- **Estimated Current Value:** ${current_value:,.2f}")
    lines.append(f"- **Total Active Power Draw:** {total_watts}W")
    lines.append(f"- **Monthly Power Cost (@ ${args.kwh_rate}/kWh):** ${monthly_cost:,.2f}")

    lines.append("\\n## Warranty Alerts (expiring within 90 days)")
    if expiring:
        for name, exp, days in sorted(expiring, key=lambda x: x[2]):
            lines.append(f"- {name}: expires {exp} ({days} days)")
    else:
        lines.append("- None")

    lines.append("\\n## Assets by Type")
    for t, lst in sorted(by_type.items()):
        lines.append(f"\\n### {t.capitalize()} ({len(lst)})")
        for a in lst:
            price = f"${a[\'purchase_price\']:,.2f}" if a.get("purchase_price") else "N/A"
            lines.append(f"- **{a[\'name\']}** | {a.get(\'status\',\'active\')} | {price} | {a.get(\'location\',\'\')}")

    lines.append("\\n## Assets by Location")
    for loc, lst in sorted(by_loc.items()):
        lines.append(f"\\n### {loc} ({len(lst)})")
        for a in lst:
            lines.append(f"- {a[\'name\']} ({a.get(\'type\',\'\')})")

    report = "\\n".join(lines) + "\\n"

    if args.output:
        Path(args.output).write_text(report)
        print(f"Report written to {args.output}")
    else:
        print(report)

if __name__ == "__main__":
    main()
'''
(workspace / "scripts" / "report.py").write_text(report_py)

# ── scripts/search.py ─────────────────────────────────────────────────────────
search_py = '''\
#!/usr/bin/env python3
"""Fuzzy search across all asset fields."""
import argparse, json, os
from pathlib import Path

def get_inventory_path():
    env = os.environ.get("HOMELAB_ASSETS_PATH")
    if env:
        return Path(env)
    return Path.home() / ".openclaw" / "workspace" / "homelab-assets" / "inventory.json"

def load(path):
    if path.exists():
        return json.loads(path.read_text())
    return {"assets": []}

def matches(asset, query):
    fields = ["name","brand","model","location","notes","serial","type"]
    q = query.lower()
    for f in fields:
        val = str(asset.get(f) or "")
        if q in val.lower():
            return True
    return False

def main():
    p = argparse.ArgumentParser()
    p.add_argument("query")
    p.add_argument("--output", default="table", choices=["table","json"])
    args = p.parse_args()

    data = load(get_inventory_path())
    results = [a for a in data["assets"] if matches(a, args.query)]

    if args.output == "json":
        print(json.dumps(results, indent=2, default=str))
    else:
        if not results:
            print("No results found.")
            return
        for a in results:
            print(f"[{a[\'type\']}] {a[\'name\']} | {a.get(\'location\',\'\')} | {a.get(\'status\',\'active\')}")

if __name__ == "__main__":
    main()
'''
(workspace / "scripts" / "search.py").write_text(search_py)

# ── references/power-estimates.md ─────────────────────────────────────────────
(workspace / "references" / "power-estimates.md").write_text("""\
# Common Homelab Device Power Estimates

| Device | Typical Watts |
|--------|--------------|
| Raspberry Pi 4 | 6-8W |
| Intel NUC (idle) | 10-15W |
| Dell R720 (idle) | 80-120W |
| Cisco SG300-28 | 32W |
| APC SMT1500 (no load) | 60W |
| 3.5" HDD | 8-10W |
| 2.5" SSD | 2-3W |
| Unifi USG | 7W |
""")

# ── assets/inventory.example.json ─────────────────────────────────────────────
example = {
    "assets": [
        {
            "id": "11111111-0000-0000-0000-000000000001",
            "name": "Example Server",
            "type": "server",
            "brand": "Dell",
            "model": "PowerEdge R720",
            "purchase_date": "2022-01-10",
            "purchase_price": 450.00,
            "warranty_months": 12,
            "warranty_expiry": "2023-01-10",
            "power_watts": 95.0,
            "location": "Rack U1",
            "serial": "SRV001",
            "notes": "Primary VM host",
            "status": "active",
            "added_at": "2022-01-10T12:00:00"
        }
    ]
}
(workspace / "assets" / "inventory.example.json").write_text(json.dumps(example, indent=2))

# ── distractor files ──────────────────────────────────────────────────────────
(workspace / "docs" / "network-diagram.md").write_text("# Network Diagram\nTODO: draw vlans\n")
(workspace / "docs" / "backup-policy.md").write_text("# Backup Policy\nRsync nightly to NAS.\n")
(workspace / "configs" / "network" / "vlans.conf").write_text("vlan 10 name SERVERS\nvlan 20 name MGMT\n")
(workspace / "configs" / "storage" / "zpool.txt").write_text("tank ONLINE\n  mirror-0\n    sda\n    sdb\n")
(workspace / "logs" / "cron.log").write_text("2024-11-01 02:00 backup OK\n2024-11-02 02:00 backup OK\n")
(workspace / "backups" / "2024" / "inventory_backup_2024_10.json").write_text(
    json.dumps({"assets": [], "_note": "old snapshot"}, indent=2)
)
(workspace / "backups" / "2023" / "inventory_backup_2023_12.json").write_text(
    json.dumps({"assets": [], "_note": "older snapshot"}, indent=2)
)
(workspace / "reports" / "drafts" / "old_report_draft.md").write_text("# Draft\nIncomplete report from Q3.\n")
(workspace / "configs" / "network" / "firewall_rules.txt").write_text(
    "ALLOW 192.168.1.0/24 -> ANY\nDENY ALL\n"
)
(workspace / "references" / "vendor-contacts.md").write_text(
    "# Vendor Contacts\n- Dell Support: 1-800-XXX\n- Ubiquiti: forums.ui.com\n"
)
(workspace / "scripts" / "migrate_old_format.py").write_text(
    "#!/usr/bin/env python3\n# Legacy migration stub - not in use\nprint('nothing to do')\n"
)

print("Workspace generated successfully.")
print(f"Inventory path: {inv_dir / 'inventory.json'}")