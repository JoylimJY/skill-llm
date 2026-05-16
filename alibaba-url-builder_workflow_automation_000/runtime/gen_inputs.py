import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Deep directory structure with distractor files ---
dirs = [
    "procurement/sourcing_requests",
    "procurement/approved_vendors",
    "procurement/rfq_history",
    "analytics/traffic_reports",
    "analytics/conversion_logs",
    "config/env_settings",
    "config/api_mappings",
    "scripts/legacy",
    "scripts/utils",
    "data/raw_exports",
    "data/processed",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = {
    "procurement/approved_vendors/vendor_list.csv": "vendor_id,name,country\n001,Shenzhen TechCo,CN\n002,Hangzhou Gear,CN\n003,Guangzhou Bright,CN",
    "procurement/rfq_history/rfq_2023_q4.json": json.dumps({"rfq_id": "RFQ-2023-001", "status": "closed", "items": 12}),
    "analytics/traffic_reports/monthly_summary.txt": "Month: October 2024\nPageviews: 84000\nBounce Rate: 42%",
    "analytics/conversion_logs/clicks.log": "2024-10-01 09:12:00 product_click pid=1600000012345\n2024-10-01 09:13:45 search_click q=bluetooth+speaker",
    "config/env_settings/prod.env": "ENV=production\nLOG_LEVEL=warn\nMAX_RETRIES=3",
    "config/api_mappings/legacy_map.json": json.dumps({"old_endpoint": "/v1/search", "new_endpoint": "/trade/search"}),
    "scripts/legacy/old_url_gen.py": "# DEPRECATED - do not use\ndef make_url(q):\n    return 'http://alibaba.com/search?q=' + q\n",
    "scripts/utils/string_helpers.py": "def slugify(s):\n    return s.lower().replace(' ', '-')\n",
    "data/raw_exports/export_2024_09.csv": "sku,qty,price\nSKU001,500,12.00\nSKU002,200,34.50",
    "data/processed/cleaned_products.json": json.dumps([{"id": "prod001", "name": "Widget A", "price": 12.0}]),
    "procurement/sourcing_requests/archive_2023.txt": "Sourcing requests archived. Contact procurement@company.com for access.",
}
for fpath, content in distractors.items():
    with open(os.path.join(workspace, fpath), "w") as f:
        f.write(content)

# --- THE MAIN PROBLEM FILE: raw sourcing brief ---
# This is the messy, unstructured input the agent must process
sourcing_brief = {
    "team": "Global Procurement - Electronics Division",
    "prepared_by": "Sarah Chen",
    "date": "2024-11-15",
    "note": "Use the Alibaba URL builder skill documentation to generate all navigation URLs. Output file must be named alibaba_url_manifest.json",
    "tasks": [
        {
            "task_id": "T1",
            "type": "category_search",
            "description": "Search for 'noise cancelling headphones' in the Consumer Electronics category. Also enable the 4-tab view and set active tab to 'product'.",
            "query": "noise cancelling headphones",
            "category": "Consumer Electronics"
        },
        {
            "task_id": "T2",
            "type": "category_search",
            "description": "Search for 'foldable electric scooter' in the Electric Scooters category.",
            "query": "foldable electric scooter",
            "category": "Electric Scooters"
        },
        {
            "task_id": "T3",
            "type": "product_detail",
            "description": "Build a product detail page URL for this product.",
            "product_title": "Pro-X Noise Cancelling Headphones (Over-Ear, ANC) 2024 Edition!",
            "product_id": "1600987654321099"
        },
        {
            "task_id": "T4",
            "type": "product_detail",
            "description": "Build a product detail page URL for this product.",
            "product_title": "Smart LED TV 55\" 4K Ultra HD -- Wall Mount Ready",
            "product_id": "62000123456789"
        },
        {
            "task_id": "T5",
            "type": "supplier_profile",
            "description": "Build the company profile URL for supplier with subdomain 'shenzhen-innovatech'.",
            "supplier_subdomain": "shenzhen-innovatech"
        },
        {
            "task_id": "T6",
            "type": "supplier_product_search",
            "description": "Search for 'wireless earbuds' on the supplier page for company subdomain 'audiopromax'.",
            "supplier_subdomain": "audiopromax",
            "query": "wireless earbuds"
        },
        {
            "task_id": "T7",
            "type": "special_section",
            "description": "Get the URL for the Alibaba AI Mode section.",
            "section": "ai_mode"
        },
        {
            "task_id": "T8",
            "type": "special_section",
            "description": "Get the URL for the Top Ranking section.",
            "section": "top_ranking"
        },
        {
            "task_id": "T9",
            "type": "rfq",
            "description": "Get the standard RFQ submission page URL."
        }
    ]
}

with open(os.path.join(workspace, "procurement/sourcing_requests/sourcing_brief.json"), "w") as f:
    json.dump(sourcing_brief, f, indent=2)

print("Workspace initialized.")
print(f"Main input file: {workspace}/procurement/sourcing_requests/sourcing_brief.json")