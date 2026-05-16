#!/usr/bin/env python3
"""
Generate a realistic sandbox workspace with distractor files and the seasonal planting tool.
"""

import os
import json
import random
import stat
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

openclaw_workspace = Path("/root/.openclaw/workspace")
openclaw_workspace.mkdir(parents=True, exist_ok=True)

# ─── Create the actual seasonal_planting.py tool ───────────────────────────
tool_content = r'''#!/usr/bin/env python3
"""Seasonal Planting Guide CLI Tool"""

import argparse
import json
import sys
import os
from pathlib import Path
from datetime import datetime

CALENDAR_PATH = Path.home() / ".openclaw" / "workspace" / "planting_calendar.json"

SAFE_DIRS = [
    str(Path.home() / ".openclaw" / "workspace"),
    "/tmp",
    str(Path.home()),
]

BLOCKED_PATHS = [
    "/etc/", "/usr/", "/var/", "/bin/", "/sbin/", "/sys/", "/proc/",
    "/.bashrc", "/.ssh", "/.bash_profile", "/.bash_logout", "/.profile",
]

BUILTIN_PLANTS = {
    "tomato": {
        "name": "Tomato",
        "category": "warm-season",
        "zones": {
            "6a": ["may", "june"],
            "6b": ["may", "june"],
            "7a": ["april", "may", "june"],
            "7b": ["april", "may", "june"],
            "8a": ["march", "april", "may"],
            "8b": ["march", "april", "may"],
            "9a": ["february", "march", "april"],
            "9b": ["february", "march", "april"],
        },
        "notes": "Plant after last frost. Needs full sun.",
    },
    "pepper": {
        "name": "Pepper",
        "category": "warm-season",
        "zones": {
            "6a": ["may", "june"],
            "6b": ["may", "june"],
            "7a": ["april", "may"],
            "7b": ["april", "may"],
            "8a": ["march", "april"],
            "8b": ["march", "april"],
        },
        "notes": "Warm soil required. Start indoors 8 weeks before transplant.",
    },
    "lettuce": {
        "name": "Lettuce",
        "category": "cool-season",
        "zones": {
            "5a": ["march", "april", "august", "september"],
            "5b": ["march", "april", "august", "september"],
            "6a": ["march", "april", "august", "september"],
            "6b": ["march", "april", "august", "september"],
            "7a": ["february", "march", "april", "september", "october"],
            "7b": ["february", "march", "april", "september", "october"],
            "8a": ["january", "february", "march", "october", "november"],
            "8b": ["january", "february", "march", "october", "november"],
        },
        "notes": "Cool weather crop. Bolts in heat.",
    },
    "kale": {
        "name": "Kale",
        "category": "cool-season",
        "zones": {
            "5a": ["march", "april", "august"],
            "5b": ["march", "april", "august"],
            "6a": ["march", "april", "august", "september"],
            "6b": ["march", "april", "august", "september"],
            "7a": ["february", "march", "august", "september", "october"],
            "7b": ["february", "march", "august", "september", "october"],
            "8a": ["january", "february", "october", "november"],
            "8b": ["january", "february", "october", "november"],
        },
        "notes": "Frost tolerant. Flavor improves after frost.",
    },
    "basil": {
        "name": "Basil",
        "category": "herb",
        "zones": {
            "6a": ["may", "june"],
            "6b": ["may", "june"],
            "7a": ["april", "may", "june"],
            "7b": ["april", "may", "june"],
            "8a": ["march", "april", "may"],
            "8b": ["march", "april", "may"],
        },
        "notes": "Annual herb. Frost sensitive.",
    },
    "carrot": {
        "name": "Carrot",
        "category": "root-vegetable",
        "zones": {
            "5a": ["april", "may", "august"],
            "5b": ["april", "may", "august"],
            "6a": ["march", "april", "august"],
            "6b": ["march", "april", "august"],
            "7a": ["february", "march", "september"],
            "7b": ["february", "march", "september"],
            "8a": ["january", "february", "october"],
            "8b": ["january", "february", "october"],
        },
        "notes": "Loose, deep soil required. Thin to 2 inches.",
    },
    "spinach": {
        "name": "Spinach",
        "category": "cool-season",
        "zones": {
            "5a": ["march", "april", "august", "september"],
            "5b": ["march", "april", "august", "september"],
            "6a": ["march", "april", "august", "september"],
            "6b": ["march", "april", "august", "september"],
            "7a": ["february", "march", "september", "october"],
            "7b": ["february", "march", "september", "october"],
            "8a": ["january", "february", "october", "november"],
            "8b": ["january", "february", "october", "november"],
        },
        "notes": "Fast-growing cool-weather crop.",
    },
    "bean": {
        "name": "Bean",
        "category": "warm-season",
        "zones": {
            "6a": ["may", "june", "july"],
            "6b": ["may", "june", "july"],
            "7a": ["april", "may", "june", "july"],
            "7b": ["april", "may", "june", "july"],
            "8a": ["march", "april", "may", "june"],
            "8b": ["march", "april", "may", "june"],
        },
        "notes": "Direct sow after frost. Do not transplant.",
    },
    "cucumber": {
        "name": "Cucumber",
        "category": "warm-season",
        "zones": {
            "6a": ["may", "june"],
            "6b": ["may", "june"],
            "7a": ["april", "may", "june"],
            "7b": ["april", "may", "june"],
            "8a": ["march", "april", "may"],
            "8b": ["march", "april", "may"],
        },
        "notes": "Needs warm soil and consistent moisture.",
    },
    "corn": {
        "name": "Corn",
        "category": "warm-season",
        "zones": {
            "6a": ["may", "june"],
            "6b": ["may", "june"],
            "7a": ["april", "may", "june"],
            "7b": ["april", "may", "june"],
            "8a": ["march", "april", "may"],
            "8b": ["march", "april", "may"],
        },
        "notes": "Plant in blocks for pollination. Needs full sun.",
    },
    "garlic": {
        "name": "Garlic",
        "category": "root-vegetable",
        "zones": {
            "5a": ["october", "november"],
            "5b": ["october", "november"],
            "6a": ["october", "november"],
            "6b": ["october", "november"],
            "7a": ["october", "november", "december"],
            "7b": ["october", "november", "december"],
            "8a": ["november", "december", "january"],
            "8b": ["november", "december", "january"],
        },
        "notes": "Fall planting for summer harvest.",
    },
    "pea": {
        "name": "Pea",
        "category": "cool-season",
        "zones": {
            "5a": ["march", "april"],
            "5b": ["march", "april"],
            "6a": ["february", "march", "april"],
            "6b": ["february", "march", "april"],
            "7a": ["january", "february", "march"],
            "7b": ["january", "february", "march"],
            "8a": ["january", "february", "october", "november"],
            "8b": ["january", "february", "october", "november"],
        },
        "notes": "Plant as soon as soil can be worked.",
    },
    "radish": {
        "name": "Radish",
        "category": "cool-season",
        "zones": {
            "5a": ["march", "april", "august", "september"],
            "5b": ["march", "april", "august", "september"],
            "6a": ["march", "april", "august", "september"],
            "6b": ["march", "april", "august", "september"],
            "7a": ["february", "march", "april", "september", "october"],
            "7b": ["february", "march", "april", "september", "october"],
            "8a": ["january", "february", "march", "october", "november"],
            "8b": ["january", "february", "march", "october", "november"],
        },
        "notes": "Fast maturing, 25-30 days. Good succession crop.",
    },
    "squash": {
        "name": "Squash",
        "category": "warm-season",
        "zones": {
            "6a": ["may", "june"],
            "6b": ["may", "june"],
            "7a": ["april", "may", "june"],
            "7b": ["april", "may", "june"],
            "8a": ["march", "april", "may"],
            "8b": ["march", "april", "may"],
        },
        "notes": "Summer and winter varieties. Needs space.",
    },
}

def load_calendar():
    if CALENDAR_PATH.exists():
        with open(CALENDAR_PATH) as f:
            return json.load(f)
    return {"builtin": BUILTIN_PLANTS, "custom": {}}

def save_calendar(data):
    CALENDAR_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CALENDAR_PATH, "w") as f:
        json.dump(data, f, indent=2)

def validate_export_path(path_str):
    path_str = os.path.expanduser(path_str)
    abs_path = os.path.abspath(path_str)
    for blocked in BLOCKED_PATHS:
        expanded_blocked = os.path.expanduser(blocked)
        if abs_path.startswith(expanded_blocked) or blocked in abs_path:
            return None, f"BLOCKED: Path '{path_str}' is restricted."
    for safe in SAFE_DIRS:
        expanded_safe = os.path.expanduser(safe)
        if abs_path.startswith(expanded_safe):
            return abs_path, None
    # Home directory check
    home = str(Path.home())
    if abs_path.startswith(home):
        return abs_path, None
    return None, f"BLOCKED: Path '{path_str}' is outside allowed directories."

def get_all_plants(calendar):
    plants = {}
    plants.update(calendar.get("builtin", {}))
    plants.update(calendar.get("custom", {}))
    return plants

def cmd_now(args):
    zone = args.zone
    now = datetime.now()
    month = now.strftime("%B").lower()
    calendar = load_calendar()
    plants = get_all_plants(calendar)
    results = []
    for key, plant in plants.items():
        zones_data = plant.get("zones", {})
        if zone in zones_data and month in zones_data[zone]:
            results.append(plant.get("name", key))
    print(f"\n=== Plant Now - Zone {zone} ({month.capitalize()}) ===")
    if results:
        print(f"Plants to sow this month: {', '.join(sorted(results))}")
    else:
        print("No plants recommended for this month/zone combination.")
    print()

def cmd_month(args):
    zone = args.zone
    month = args.month.lower()
    calendar = load_calendar()
    plants = get_all_plants(calendar)
    results = []
    for key, plant in plants.items():
        zones_data = plant.get("zones", {})
        if zone in zones_data and month in zones_data[zone]:
            results.append(plant.get("name", key))
    print(f"\n=== Planting Guide - {month.capitalize()}, Zone {zone} ===")
    if results:
        print(f"Recommended plants: {', '.join(sorted(results))}")
    else:
        print(f"No plants found for zone {zone} in {month}.")
    print()

def cmd_year(args):
    zone = args.zone
    calendar = load_calendar()
    plants = get_all_plants(calendar)
    months_order = ["january","february","march","april","may","june",
                    "july","august","september","october","november","december"]
    output_lines = []
    output_lines.append(f"# Annual Planting Calendar - Zone {zone}")
    output_lines.append("")
    for month in months_order:
        results = []
        for key, plant in plants.items():
            zones_data = plant.get("zones", {})
            if zone in zones_data and month in zones_data[zone]:
                results.append(plant.get("name", key))
        output_lines.append(f"## {month.capitalize()}")
        if results:
            output_lines.append(f"Plant: {', '.join(sorted(results))}")
        else:
            output_lines.append("No plantings recommended.")
        output_lines.append("")
    output_text = "\n".join(output_lines)
    print(output_text)
    if hasattr(args, 'export') and args.export:
        abs_path, err = validate_export_path(args.export)
        if err:
            print(f"Export error: {err}", file=sys.stderr)
            sys.exit(1)
        Path(abs_path).parent.mkdir(parents=True, exist_ok=True)
        with open(abs_path, "w") as f:
            f.write(output_text)
        print(f"Calendar exported to: {abs_path}")

def cmd_search(args):
    query = args.query.lower()
    calendar = load_calendar()
    plants = get_all_plants(calendar)
    results = []
    for key, plant in plants.items():
        if query in key.lower() or query in plant.get("name", "").lower() or query in plant.get("category", "").lower():
            results.append((plant.get("name", key), plant.get("category", ""), plant.get("notes", "")))
    print(f"\n=== Search Results for '{args.query}' ===")
    for name, cat, notes in results:
        print(f"  {name} [{cat}] - {notes}")
    if not results:
        print("No plants found matching your search.")
    print()

def cmd_show(args):
    name = args.name.lower()
    calendar = load_calendar()
    plants = get_all_plants(calendar)
    plant = plants.get(name)
    if not plant:
        # Try partial match
        for key in plants:
            if name in key:
                plant = plants[key]
                break
    if not plant:
        print(f"Plant '{args.name}' not found.")
        return
    print(f"\n=== {plant.get('name', name)} ===")
    print(f"Category: {plant.get('category', 'unknown')}")
    print(f"Notes: {plant.get('notes', 'None')}")
    print("Planting Windows by Zone:")
    for zone, months in plant.get("zones", {}).items():
        print(f"  Zone {zone}: {', '.join(months)}")
    print()

def cmd_add(args):
    name_key = args.name.lower().replace(" ", "-")
    planting_months = [m.strip().lower() for m in args.planting.split(",")]
    zones_list = [z.strip() for z in args.zone.split(",")]
    notes = getattr(args, 'notes', '') or ''
    calendar = load_calendar()
    zones_dict = {}
    for z in zones_list:
        zones_dict[z] = planting_months
    plant_entry = {
        "name": args.name,
        "category": "custom",
        "zones": zones_dict,
        "notes": notes,
    }
    calendar.setdefault("custom", {})[name_key] = plant_entry
    save_calendar(calendar)
    print(f"Added '{args.name}' to your planting calendar.")
    print(f"  Zones: {', '.join(zones_list)}")
    print(f"  Planting months: {', '.join(planting_months)}")
    if notes:
        print(f"  Notes: {notes}")

def main():
    parser = argparse.ArgumentParser(description="Seasonal Planting Guide")
    subparsers = parser.add_subparsers(dest="command")

    # now
    p_now = subparsers.add_parser("now")
    p_now.add_argument("--zone", required=True)

    # month
    p_month = subparsers.add_parser("month")
    p_month.add_argument("--month", required=True)
    p_month.add_argument("--zone", required=True)

    # year
    p_year = subparsers.add_parser("year")
    p_year.add_argument("--zone", required=True)
    p_year.add_argument("--export", default=None)

    # search
    p_search = subparsers.add_parser("search")
    p_search.add_argument("query")

    # show
    p_show = subparsers.add_parser("show")
    p_show.add_argument("name")

    # add
    p_add = subparsers.add_parser("add")
    p_add.add_argument("name")
    p_add.add_argument("--planting", required=True)
    p_add.add_argument("--zone", required=True)
    p_add.add_argument("--notes", default="")

    args = parser.parse_args()
    if args.command == "now":
        cmd_now(args)
    elif args.command == "month":
        cmd_month(args)
    elif args.command == "year":
        cmd_year(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "show":
        cmd_show(args)
    elif args.command == "add":
        cmd_add(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
'''

tool_path = workspace / "seasonal_planting.py"
tool_path.write_text(tool_content)
tool_path.chmod(tool_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ─── Create realistic distractor file structure ─────────────────────────────

# Farm operations directory
farm_ops = workspace / "farm_operations"
farm_ops.mkdir(parents=True, exist_ok=True)

# Outdated crop list (distractor)
(farm_ops / "crop_list_2023.txt").write_text(
    "Crops grown in 2023:\n- Tomatoes (main field)\n- Peppers (greenhouse)\n- Basil (herb garden)\n- Dragon tongue beans (trial plot)\n- Squash (west field)\n"
)

# Old scheduling spreadsheet notes (distractor)
(farm_ops / "scheduling_notes.txt").write_text(
    "Scheduling notes from last season:\n"
    "- Bean trial: mixed results. Try different zones next year.\n"
    "- Zone confusion: some fields might be 6b vs 7a boundary.\n"
    "- Dragon tongue beans planted late May - good yield.\n"
    "- Need to register new varieties in the system for 2024.\n"
)

# Soil reports directory
soil = workspace / "farm_operations" / "soil_reports"
soil.mkdir(parents=True, exist_ok=True)
(soil / "field_a_soil_2024.txt").write_text(
    "Field A Soil Analysis 2024\npH: 6.8\nNitrogen: medium\nPhosphorus: high\nSuitable for: beans, tomatoes, peppers\n"
)
(soil / "field_b_soil_2024.txt").write_text(
    "Field B Soil Analysis 2024\npH: 7.1\nNitrogen: low\nPhosphorus: medium\nSuitable for: root vegetables, leafy greens\n"
)

# Vendor invoices directory (distractor)
vendors = workspace / "vendors"
vendors.mkdir(parents=True, exist_ok=True)
(vendors / "seed_invoice_april2024.txt").write_text(
    "Seed Purchase - April 2024\nVendor: Heritage Seed Co.\nItems:\n  Dragon Tongue Bean (heirloom) - 2 lbs - $18.50\n  Brandywine Tomato - 1 pkt - $4.25\n  Lemon Basil - 1 pkt - $3.00\nTotal: $25.75\n"
)
(vendors / "equipment_invoice_2024.txt").write_text(
    "Equipment Purchase 2024\nVendor: FarmSupply Inc.\nItems:\n  Drip Irrigation Kit - $245.00\n  Row Cover (50ft) - $32.00\nTotal: $277.00\n"
)

# Staff notes directory (distractor)
staff = workspace / "staff"
staff.mkdir(parents=True, exist_ok=True)
(staff / "planting_crew_schedule.txt").write_text(
    "Planting Crew Schedule - Spring 2024\nWeek 1 (April 8-12): Prepare beds, transplant lettuce\nWeek 2 (April 15-19): Tomatoes and peppers\nWeek 3 (April 22-26): Beans and squash\nWeek 4 (May 1-5): Dragon tongue bean trial (confirm zone first)\n"
)
(staff / "crew_contact_list.txt").write_text(
    "Crew Contacts:\nMaria Gonzalez - Lead Grower - ext 101\nJames Park - Irrigation Specialist - ext 102\nSarah Chen - Harvest Coordinator - ext 103\n"
)

# Old exports directory (distractor - wrong format, wrong zone)
exports = workspace / "old_exports"
exports.mkdir(parents=True, exist_ok=True)
(exports / "2023_zone6b_schedule.txt").write_text(
    "2023 Zone 6b Schedule (OUTDATED)\nApril: tomatoes, peppers\nMay: beans, cucumbers\nJune: corn, squash\n(Note: Dragon tongue bean not yet registered)\n"
)

# Config directory (distractor)
config = workspace / "config"
config.mkdir(parents=True, exist_ok=True)
(config / "farm_settings.json").write_text(json.dumps({
    "primary_zone": "7a",
    "secondary_zone": "6b",
    "farm_name": "Riverside Cooperative Farm",
    "established": 2018,
    "fields": ["Field A", "Field B", "Greenhouse", "Trial Plot"]
}, indent=2))

# Crop research directory (distractor)
research = workspace / "crop_research"
research.mkdir(parents=True, exist_ok=True)
(research / "dragon_tongue_bean_notes.txt").write_text(
    "Dragon Tongue Bean Research Notes\n"
    "Variety: Phaseolus vulgaris 'Dragon Tongue'\n"
    "Origin: Netherlands heirloom\n"
    "Days to maturity: 55-60 days\n"
    "Recommended planting: After last frost\n"
    "Our zone: primarily 7a, also testing in 6b\n"
    "Best months observed: May, June for zone 7a; May, June for zone 6b\n"
    "Notes: Beautiful yellow pods with purple streaks. High yield. \n"
    "ACTION REQUIRED: Register in planting system for 2024 season!\n"
    "Zones to register: 6b and 7a\n"
    "Planting months: april, may, june for 7a; may, june for 6b\n"
)
(research / "heirloom_variety_comparison.txt").write_text(
    "Heirloom Variety Comparison 2023\n"
    "Dragon Tongue Bean vs. Blue Lake Bush Bean:\n"
    "  Dragon Tongue: Higher yield, better flavor, more disease resistant\n"
    "  Blue Lake: More widely available, easier to source\n"
    "Recommendation: Prioritize Dragon Tongue for 2024 expansion.\n"
)

# Harvest logs (distractor)
harvest = workspace / "harvest_logs"
harvest.mkdir(parents=True, exist_ok=True)
(harvest / "harvest_log_2023.csv").write_text(
    "date,crop,field,weight_lbs,notes\n"
    "2023-06-15,Lettuce,Field B,45,Spring lettuce harvest\n"
    "2023-07-10,Tomato,Field A,120,First tomato harvest\n"
    "2023-07-28,Dragon Tongue Bean,Trial Plot,28,Trial harvest - excellent\n"
    "2023-08-05,Pepper,Greenhouse,67,Green peppers\n"
    "2023-09-01,Squash,West Field,200,Summer squash\n"
)

# Zone reference file (distractor - incomplete info)
(workspace / "zone_reference.txt").write_text(
    "Zone Reference for Our Farm\n"
    "Main fields: USDA Zone 7a\n"
    "North boundary fields: Possibly Zone 6b\n"
    "Last average frost: April 3\n"
    "First average frost: November 8\n"
    "Note: This is an approximation. Always verify with planting tool.\n"
)

print("Workspace generated successfully.")
print(f"Tool path: {tool_path}")
print(f"Openclaw workspace: {openclaw_workspace}")