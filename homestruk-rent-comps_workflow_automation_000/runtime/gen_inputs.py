import os
import json
import random
from pathlib import Path
from datetime import date

random.seed(42)

workspace = Path("/workspace")

# --- Create deep distractor directory structure ---
dirs = [
    ".openclaw/shared",
    ".openclaw/workspace/properties",
    ".openclaw/workspace/leases",
    ".openclaw/workspace/maintenance",
    ".openclaw/kb/masslandlords",
    ".openclaw/kb/templates",
    ".openclaw/logs",
    "projects/invoices",
    "projects/tenants",
    "projects/legal",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_files = {
    ".openclaw/workspace/leases/lease-456-main-st.md": "# Lease Agreement\nTenant: Jane Doe\nRent: $1,800/month\nStart: 2023-09-01\n",
    ".openclaw/workspace/maintenance/work-order-2024-03.txt": "Replace water heater at 22 Elm St. Cost: $1,200. Status: Complete.\n",
    ".openclaw/kb/masslandlords/security-deposits.md": "# Security Deposits\nMA law caps security deposit at 1 month's rent.\n",
    ".openclaw/kb/templates/lease-renewal-letter.txt": "Dear [Tenant],\nYour lease expires on [DATE]. We would like to renew...\n",
    ".openclaw/logs/activity-2024.log": "2024-01-10 10:00 User logged in\n2024-01-11 09:30 Comp search run for Somerville\n",
    "projects/invoices/inv-2024-001.txt": "Invoice #001\nPlumber: $350\nDate: 2024-02-15\n",
    "projects/tenants/tenant-profile-doe.json": json.dumps({"name": "Jane Doe", "unit": "2B", "email": "jane@example.com"}, indent=2),
    "projects/legal/eviction-notice-template.txt": "Notice to Quit\nTo: [Tenant Name]\nAddress: [Address]\n",
    ".openclaw/kb/masslandlords/rent-increase-guide.md": "# Rent Increase Guide\nSee MGL c.186 for at-will tenancy rules.\nAlways provide written notice.\n",
    "projects/invoices/inv-2024-002.txt": "Invoice #002\nElectrician: $480\nDate: 2024-03-20\n",
    ".openclaw/workspace/maintenance/hvac-inspection-2024.txt": "HVAC inspection passed. Filter replaced. Next service: 2025-01.\n",
}

for path, content in distractor_files.items():
    fp = workspace / path
    fp.write_text(content)

# --- Subject property in properties.json ---
properties = [
    {
        "id": "prop-001",
        "address": "14 Birchwood Lane",
        "city": "Natick",
        "state": "MA",
        "bedrooms": 2,
        "bathrooms": 1,
        "sqft": 920,
        "type": "SFR",
        "features": {
            "parking": True,
            "laundry": "in-unit",
            "ac": "central",
            "pets_allowed": False
        },
        "condition": "updated",
        "current_rent": 1950
    },
    {
        "id": "prop-002",
        "address": "77 Maple Court",
        "city": "Framingham",
        "state": "MA",
        "bedrooms": 3,
        "bathrooms": 2,
        "sqft": 1350,
        "type": "multi-family",
        "features": {
            "parking": True,
            "laundry": "in-unit",
            "ac": "window",
            "pets_allowed": True
        },
        "condition": "average",
        "current_rent": 2400
    }
]
(workspace / ".openclaw/shared/properties.json").write_text(json.dumps(properties, indent=2))

# --- Raw comp data for 14 Birchwood Lane, Natick MA ---
# These simulate data already gathered from searches.
# Subject: 2bd/1ba, 920sqft, parking, in-unit laundry, central A/C, no pets, updated, current_rent=1950
# Comps have deliberate feature gaps for adjustments.
comps_raw = {
    "subject_property_id": "prop-001",
    "comps": [
        {
            "comp_id": 1,
            "address": "8 Chestnut St, Natick, MA",
            "listed_rent": 2050,
            "bedrooms": 2,
            "bathrooms": 1,
            "sqft": 900,
            "features": {
                "parking": True,
                "laundry": "in-unit",
                "ac": "central",
                "pets_allowed": False
            },
            "condition": "updated",
            "days_on_market": 7,
            "source": "zillow"
        },
        {
            "comp_id": 2,
            "address": "31 Oak Terrace, Natick, MA",
            "listed_rent": 1875,
            "bedrooms": 2,
            "bathrooms": 1,
            "sqft": 850,
            "features": {
                "parking": False,
                "laundry": "none",
                "ac": "none",
                "pets_allowed": False
            },
            "condition": "updated",
            "days_on_market": 14,
            "source": "apartments.com"
        },
        {
            "comp_id": 3,
            "address": "102 Pine Ridge Rd, Natick, MA",
            "listed_rent": 1950,
            "bedrooms": 2,
            "bathrooms": 1,
            "sqft": 980,
            "features": {
                "parking": True,
                "laundry": "shared",
                "ac": "window",
                "pets_allowed": False
            },
            "condition": "average",
            "days_on_market": 21,
            "source": "craigslist"
        },
        {
            "comp_id": 4,
            "address": "55 Walnut Ave, Natick, MA",
            "listed_rent": 2100,
            "bedrooms": 2,
            "bathrooms": 2,
            "sqft": 1050,
            "features": {
                "parking": True,
                "laundry": "in-unit",
                "ac": "central",
                "pets_allowed": False
            },
            "condition": "updated",
            "days_on_market": 5,
            "source": "zillow"
        },
        {
            "comp_id": 5,
            "address": "19 Elmwood Dr, Natick, MA",
            "listed_rent": 1800,
            "bedrooms": 2,
            "bathrooms": 1,
            "sqft": 875,
            "features": {
                "parking": False,
                "laundry": "none",
                "ac": "none",
                "pets_allowed": True
            },
            "condition": "average",
            "days_on_market": 30,
            "source": "apartments.com"
        }
    ]
}

(workspace / ".openclaw/workspace/properties/raw-comps-14-birchwood-lane-natick.json").write_text(
    json.dumps(comps_raw, indent=2)
)

# --- A stale/old comps report from a different property as distractor ---
old_report = """RENT COMPS ANALYSIS — 77 Maple Court, Framingham MA
Date: 2023-11-15

SUBJECT PROPERTY
Address: 77 Maple Court, Framingham MA
Type: multi-family | 3bd/2ba | 1350 sqft
Features: parking, in-unit laundry, window A/C, pets allowed
Condition: average
Current rent: $2,400/month

COMPARABLE PROPERTIES (5 max)
Comp 1: 10 Grove St, Framingham MA — $2,350 — 3bd/2ba — 1200 sqft
  Adjustments: none
  Adjusted rent: $2,350

ANALYSIS
Average adjusted rent: $2,350
Median adjusted rent: $2,350
Range: $2,350 - $2,350

RECOMMENDATION
Recommended rent: $2,350/month
Confidence: Low based on 1 comp
  Current rent: $2,400
  Market rent: $2,350
  Suggested increase: $0 (0%)
  MA law note: No rent control in most MA cities.
  30 days notice required for at-will tenancies.
  Lease term increases take effect at renewal.
"""
(workspace / ".openclaw/workspace/properties/comps-77-maple-court-framingham-2023-11-15.md").write_text(old_report)

print("Workspace setup complete.")
print(f"Subject property: 14 Birchwood Lane, Natick MA")
print(f"Raw comps file: .openclaw/workspace/properties/raw-comps-14-birchwood-lane-natick.json")