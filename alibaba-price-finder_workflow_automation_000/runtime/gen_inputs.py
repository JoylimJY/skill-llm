import os
import csv
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Deep directory structure with distractor files ---
dirs = [
    "workspace/procurement/archive/2022",
    "workspace/procurement/archive/2023",
    "workspace/procurement/reports/q1",
    "workspace/procurement/reports/q2",
    "workspace/sourcing/vendors/asia",
    "workspace/sourcing/vendors/europe",
    "workspace/sourcing/templates",
    "workspace/finance/budgets",
    "workspace/finance/approvals",
    "workspace/logistics/shipping",
    "workspace/logistics/customs",
]
for d in dirs:
    os.makedirs(f"/{d}", exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "/workspace/procurement/archive/2022/vendor_list_old.csv": "vendor,country,rating\nShenZhen Co,China,4.2\nBeijing Ltd,China,3.8",
    "/workspace/procurement/archive/2023/budget_summary.txt": "Total procurement budget 2023: $450,000\nCategories: Electronics, Packaging, Apparel",
    "/workspace/procurement/reports/q1/q1_summary.json": json.dumps({"quarter": "Q1", "spend": 112000, "suppliers": 34}),
    "/workspace/procurement/reports/q2/q2_notes.txt": "Q2 focus: reduce MOQ commitments, explore new electronics vendors",
    "/workspace/sourcing/vendors/asia/china_contacts.csv": "company,contact,email\nTopElec,Wang Li,wang@topelec.cn\nBestPack,Chen Ming,chen@bestpack.cn",
    "/workspace/sourcing/vendors/europe/eu_suppliers.txt": "EuroTech GmbH - Frankfurt\nPackPro NV - Amsterdam",
    "/workspace/sourcing/templates/rfq_template.docx.txt": "RFQ Template v3.2 - Do not modify",
    "/workspace/finance/budgets/2024_budget.csv": "category,allocated,spent\nElectronics,150000,87000\nPackaging,50000,31000\nApparel,75000,42000",
    "/workspace/finance/approvals/pending_approvals.txt": "PO-2024-0041: Pending CFO sign-off\nPO-2024-0042: Approved",
    "/workspace/logistics/shipping/incoterms_ref.txt": "FOB: Free On Board - seller delivers goods to port\nCIF: Cost Insurance Freight\nEXW: Ex Works",
    "/workspace/logistics/customs/hs_codes.csv": "product,hs_code\nphone case,3926.90\nwireless earbuds,8518.30\nled strip,9405.40",
}

for path, content in distractor_files.items():
    with open(path, "w") as f:
        f.write(content)

# --- The actual messy input: procurement research requirements ---
# This CSV is intentionally messy: inconsistent casing, extra whitespace, mixed formats
requirements_csv = """\
req_id,product_query,min_price,max_price,max_moq,sort_preference,notes
REQ-001, Wireless Earbuds ,2,15,500,cheapest first,"Priority item for Q3 campaign"
REQ-002,LED Strip Lights,,,,most expensive first,"No price filter needed, high-end only"
REQ-003,  phone case  ,1,5,100,,"Standard budget item, no sort preference needed"
REQ-004,Bamboo Cutting Board,3,20,,cheapest first,"Kitchen category expansion"
REQ-005,USB C Cable,0.5,8,200,,"Cable sourcing audit"
REQ-006, Portable Bluetooth Speaker ,,,,cheapest first,"Marketing gift items"
REQ-007,Silicone Watch Band,1,10,50,most expensive first,"Premium line testing"
"""

with open("/workspace/procurement/sourcing_requirements.csv", "w") as f:
    f.write(requirements_csv)

# A misleading "old URL format" file to confuse agents that don't read SKILL.md carefully
old_url_examples = """\
# DEPRECATED URL FORMAT - DO NOT USE
# Old format (missing required tracking):
https://www.alibaba.com/trade/search?SearchText=phone+case
https://www.alibaba.com/trade/search?SearchText=led+strip&sortType=price_asc
# These are NOT valid anymore.
"""
with open("/workspace/sourcing/templates/deprecated_url_formats.txt", "w") as f:
    f.write(old_url_examples)

print("Workspace generated successfully.")
print("Key input file: /workspace/procurement/sourcing_requirements.csv")