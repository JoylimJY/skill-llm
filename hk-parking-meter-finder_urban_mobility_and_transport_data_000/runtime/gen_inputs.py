import os
import csv
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── directory skeleton with distractors ──────────────────────────────────────
dirs = [
    "scripts",
    "data/raw",
    "data/processed",
    "data/archive",
    "logs",
    "reports/2024",
    "reports/2025",
    "config",
    "tools/geo",
    "tools/analytics",
    "cache",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ──────────────────────────────────────────────────────────
distractors = {
    "data/raw/bus_routes.csv": "route_id,origin,destination\nB1,Fo Tan,Sha Tin\nB2,Tai Po,Fanling\n",
    "data/raw/mtr_stations.json": json.dumps({"stations": ["火炭", "沙田", "大埔墟", "太和"]}),
    "data/processed/traffic_flow_2024.csv": "date,volume,road\n2024-01-01,1200,大埔道\n2024-01-02,1350,沙田道\n",
    "data/archive/old_parking_2022.csv": "id,location\n1,obsolete_location\n",
    "logs/system.log": "2025-01-01 INFO: System started\n2025-01-02 ERROR: Data feed timeout\n",
    "reports/2024/annual_summary.txt": "Annual transport utilisation summary 2024\nTotal metered spaces: 2400\n",
    "reports/2025/q1_draft.txt": "Q1 2025 draft — incomplete\n",
    "config/db_config.yaml": "host: localhost\nport: 5432\ndb: transport\n",
    "config/api_endpoints.json": json.dumps({"occupancy": "http://localhost:8080/occupancy", "inventory": "http://localhost:8080/inventory"}),
    "tools/geo/geocoder.py": "# legacy geocoder — deprecated\ndef geocode(addr): return None\n",
    "tools/analytics/cluster_stats.py": "# cluster statistics helper\ndef mean(data): return sum(data)/len(data)\n",
    "cache/last_query.txt": "query: 旺角 奶路臣街\ntimestamp: 2025-06-01T10:22:00\n",
    "data/raw/taxi_stands.csv": "stand_id,district,street\nT01,Sha Tin,源禾路\nT02,Tai Po,安慈路\n",
    "data/processed/parking_utilisation_june.csv": "district,utilisation_pct\nSha Tin,78\nTai Po,65\nCauseway Bay,92\n",
}
for rel_path, content in distractors.items():
    fpath = workspace / rel_path
    fpath.write_text(content, encoding="utf-8")

# ── parkingspaces.csv — static inventory ─────────────────────────────────────
# Columns: meterid, district_en, district_zh, subdistrict_en, subdistrict_zh,
#          street_en, street_zh, street_section, vehicle_type, spaces, lat, lon

parking_spaces_rows = [
    # 火炭
    ("PS001", "Sha Tin", "沙田", "Fo Tan", "火炭", "Sui Wo Road", "穗禾路", "Section 1", "Private Car", 8, 22.3958, 114.1986),
    ("PS002", "Sha Tin", "沙田", "Fo Tan", "火炭", "Sui Wo Road", "穗禾路", "Section 2", "Private Car", 6, 22.3962, 114.1990),
    ("PS003", "Sha Tin", "沙田", "Fo Tan", "火炭", "Kin Wing Street", "健榮街", "Section 1", "Private Car", 10, 22.3948, 114.1975),
    ("PS004", "Sha Tin", "沙田", "Fo Tan", "火炭", "Kin Wing Street", "健榮街", "Section 2", "Goods Vehicle", 4, 22.3944, 114.1971),
    ("PS005", "Sha Tin", "沙田", "Fo Tan", "火炭", "On Kui Street", "安鉅街", "All", "Private Car", 12, 22.3936, 114.1982),
    # 大埔
    ("PS006", "Tai Po", "大埔", "Tai Po Market", "大埔墟", "Fu Shin Street", "富善街", "Section 1", "Private Car", 14, 22.4462, 114.1699),
    ("PS007", "Tai Po", "大埔", "Tai Po Market", "大埔墟", "Fu Shin Street", "富善街", "Section 2", "Goods Vehicle", 5, 22.4458, 114.1695),
    ("PS008", "Tai Po", "大埔", "Tai Po Market", "大埔墟", "Kwong Fuk Road", "廣福路", "Section 1", "Private Car", 9, 22.4471, 114.1712),
    ("PS009", "Tai Po", "大埔", "Kwong Fuk", "廣福", "Kwong Fuk Square", "廣福坊", "All", "Private Car", 7, 22.4480, 114.1720),
    # 銅鑼灣
    ("PS010", "Wan Chai", "灣仔", "Causeway Bay", "銅鑼灣", "Yee Wo Street", "怡和街", "Section 1", "Private Car", 6, 22.2803, 114.1839),
    ("PS011", "Wan Chai", "灣仔", "Causeway Bay", "銅鑼灣", "Yee Wo Street", "怡和街", "Section 2", "Motorcycle", 8, 22.2799, 114.1843),
    ("PS012", "Wan Chai", "灣仔", "Causeway Bay", "銅鑼灣", "Kingston Street", "京士頓街", "All", "Private Car", 5, 22.2810, 114.1855),
    # 尖沙咀
    ("PS013", "Yau Tsim Mong", "油尖旺", "Tsim Sha Tsui", "尖沙咀", "Carnarvon Road", "加拿分道", "Section 1", "Private Car", 10, 22.2969, 114.1719),
    ("PS014", "Yau Tsim Mong", "油尖旺", "Tsim Sha Tsui", "尖沙咀", "Carnarvon Road", "加拿分道", "Section 2", "Goods Vehicle", 4, 22.2972, 114.1712),
    ("PS015", "Yau Tsim Mong", "油尖旺", "Tsim Sha Tsui", "尖沙咀", "Granville Road", "格蘭佛道", "All", "Private Car", 8, 22.2979, 114.1731),
    # Extra Sha Tin / Fo Tan area
    ("PS016", "Sha Tin", "沙田", "Fo Tan", "火炭", "Fo Tan Road", "火炭路", "Section 1", "Private Car", 5, 22.3971, 114.2001),
    ("PS017", "Sha Tin", "沙田", "Fo Tan", "火炭", "Fo Tan Road", "火炭路", "Section 2", "Goods Vehicle", 3, 22.3975, 114.2005),
    # Mong Kok
    ("PS018", "Yau Tsim Mong", "油尖旺", "Mong Kok", "旺角", "Nelson Street", "奶路臣街", "Section 1", "Private Car", 7, 22.3192, 114.1693),
    ("PS019", "Yau Tsim Mong", "油尖旺", "Mong Kok", "旺角", "Nelson Street", "奶路臣街", "Section 2", "Motorcycle", 6, 22.3196, 114.1697),
    ("PS020", "Yau Tsim Mong", "油尖旺", "Mong Kok", "旺角", "Fa Yuen Street", "花園街", "All", "Private Car", 9, 22.3200, 114.1701),
]

parking_fieldnames = [
    "meterid", "district_en", "district_zh", "subdistrict_en", "subdistrict_zh",
    "street_en", "street_zh", "street_section", "vehicle_type", "spaces", "lat", "lon"
]

with open(workspace / "parkingspaces.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=parking_fieldnames)
    writer.writeheader()
    for row in parking_spaces_rows:
        writer.writerow(dict(zip(parking_fieldnames, row)))

# ── occupancystatus.csv — live occupancy ──────────────────────────────────────
# Columns: meterid, occupied, vacant, last_updated

random.seed(42)
occupancy_rows = []
for row in parking_spaces_rows:
    meterid = row[0]
    spaces = row[9]  # spaces field (index 9, not 10)
    occupied = random.randint(0, spaces)
    vacant = spaces - occupied
    occupancy_rows.append({
        "meterid": meterid,
        "occupied": occupied,
        "vacant": vacant,
        "last_updated": "2025-06-15T09:30:00",
    })

# Ensure some 火炭 entries definitely have vacancies for test reliability
fo_tan_ids = ["PS001", "PS002", "PS003", "PS005", "PS016"]
for occ_row in occupancy_rows:
    if occ_row["meterid"] in fo_tan_ids:
        # Force at least 2 vacant spaces
        spaces_map = {r[0]: r[9] for r in parking_spaces_rows}
        total = spaces_map[occ_row["meterid"]]
        occ_row["occupied"] = max(0, total - random.randint(2, max(2, total // 2)))
        occ_row["vacant"] = total - occ_row["occupied"]

with open(workspace / "occupancystatus.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["meterid", "occupied", "vacant", "last_updated"])
    writer.writeheader()
    writer.writerows(occupancy_rows)

# ── the main script: scripts/hk_metered_parking.py ───────────────────────────
script_content = r'''#!/usr/bin/env python3
"""
HK Metered Parking Finder
Searches official Transport Department metered parking inventory + live occupancy.
Usage: python3 scripts/hk_metered_parking.py <keywords...> [--vacant-only] [--json]
"""

import argparse
import csv
import json
import math
import os
import sys
from pathlib import Path


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def load_csv(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def keyword_match(row, keywords):
    """Return True if ANY keyword matches any text field (case-insensitive)."""
    fields = [
        row.get("district_en", ""), row.get("district_zh", ""),
        row.get("subdistrict_en", ""), row.get("subdistrict_zh", ""),
        row.get("street_en", ""), row.get("street_zh", ""),
        row.get("street_section", ""),
    ]
    combined = " ".join(fields).lower()
    for kw in keywords:
        if kw.lower() in combined:
            return True
    return False


def maps_link(lat, lon, label=""):
    label_enc = label.replace(" ", "+")
    return f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"


def main():
    parser = argparse.ArgumentParser(description="HK Metered Parking Finder")
    parser.add_argument("keywords", nargs="+", help="Street, district, area, or landmark keywords")
    parser.add_argument("--vacant-only", action="store_true", help="Only show clusters with at least 1 vacant space")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Output results as JSON")
    args = parser.parse_args()

    # Resolve data file paths relative to this script's location
    script_dir = Path(__file__).parent.parent
    spaces_path = script_dir / "parkingspaces.csv"
    occupancy_path = script_dir / "occupancystatus.csv"

    if not spaces_path.exists():
        print(json.dumps({"error": f"parkingspaces.csv not found at {spaces_path}"}))
        sys.exit(1)
    if not occupancy_path.exists():
        print(json.dumps({"error": f"occupancystatus.csv not found at {occupancy_path}"}))
        sys.exit(1)

    spaces = load_csv(spaces_path)
    occupancy = load_csv(occupancy_path)

    # Build occupancy lookup
    occ_lookup = {}
    for occ in occupancy:
        occ_lookup[occ["meterid"]] = occ

    keywords = args.keywords

    # Match spaces
    matched = [s for s in spaces if keyword_match(s, keywords)]

    if not matched:
        result = {
            "query": keywords,
            "matched": False,
            "message": "No metered parking spaces found matching the given keywords in the official inventory.",
            "clusters": []
        }
        if args.json_output:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"No metered parking spaces found for: {' '.join(keywords)}")
        sys.exit(0)

    # Group into clusters: key = (district_en, subdistrict_en, street_zh, street_section, vehicle_type)
    clusters = {}
    for s in matched:
        key = (
            s["district_en"], s["district_zh"],
            s["subdistrict_en"], s["subdistrict_zh"],
            s["street_en"], s["street_zh"],
            s["street_section"], s["vehicle_type"]
        )
        if key not in clusters:
            clusters[key] = {
                "district_en": s["district_en"],
                "district_zh": s["district_zh"],
                "subdistrict_en": s["subdistrict_en"],
                "subdistrict_zh": s["subdistrict_zh"],
                "street_en": s["street_en"],
                "street_zh": s["street_zh"],
                "street_section": s["street_section"],
                "vehicle_type": s["vehicle_type"],
                "total_spaces": 0,
                "occupied": 0,
                "vacant": 0,
                "has_live_data": False,
                "lats": [],
                "lons": [],
                "meter_ids": [],
            }
        c = clusters[key]
        c["total_spaces"] += int(s["spaces"])
        c["lats"].append(float(s["lat"]))
        c["lons"].append(float(s["lon"]))
        c["meter_ids"].append(s["meterid"])
        occ = occ_lookup.get(s["meterid"])
        if occ:
            c["occupied"] += int(occ["occupied"])
            c["vacant"] += int(occ["vacant"])
            c["has_live_data"] = True

    # Build cluster list
    cluster_list = []
    for key, c in clusters.items():
        avg_lat = sum(c["lats"]) / len(c["lats"])
        avg_lon = sum(c["lons"]) / len(c["lons"])
        cluster_list.append({
            "district_en": c["district_en"],
            "district_zh": c["district_zh"],
            "subdistrict_en": c["subdistrict_en"],
            "subdistrict_zh": c["subdistrict_zh"],
            "street_en": c["street_en"],
            "street_zh": c["street_zh"],
            "street_section": c["street_section"],
            "vehicle_type": c["vehicle_type"],
            "total_spaces": c["total_spaces"],
            "occupied": c["occupied"],
            "vacant": c["vacant"],
            "has_live_data": c["has_live_data"],
            "lat": round(avg_lat, 6),
            "lon": round(avg_lon, 6),
            "maps_link": maps_link(round(avg_lat, 6), round(avg_lon, 6)),
            "meter_ids": c["meter_ids"],
        })

    # Sort: vacant descending
    cluster_list.sort(key=lambda x: (-x["vacant"], -x["total_spaces"]))

    if args.vacant_only:
        cluster_list = [c for c in cluster_list if c["vacant"] > 0]

    output = {
        "query": keywords,
        "matched": True,
        "total_clusters": len(cluster_list),
        "clusters": cluster_list,
    }

    if args.json_output:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"Found {len(cluster_list)} cluster(s) for: {' '.join(keywords)}\n")
        for i, c in enumerate(cluster_list, 1):
            status = f"{c['vacant']} vacant / {c['occupied']} occupied" if c["has_live_data"] else "no live data"
            print(f"{i}. [{c['district_zh']} / {c['subdistrict_zh']}] {c['street_zh']} ({c['street_en']}) "
                  f"- {c['street_section']} - {c['vehicle_type']}")
            print(f"   Spaces: {c['total_spaces']} total | {status}")
            print(f"   Map: {c['maps_link']}")
            print()


if __name__ == "__main__":
    main()
'''

script_path = workspace / "scripts" / "hk_metered_parking.py"
script_path.write_text(script_content, encoding="utf-8")

print("Workspace generated successfully.")
print(f"  parkingspaces.csv: {(workspace / 'parkingspaces.csv').stat().st_size} bytes")
print(f"  occupancystatus.csv: {(workspace / 'occupancystatus.csv').stat().st_size} bytes")
print(f"  scripts/hk_metered_parking.py: {script_path.stat().st_size} bytes")