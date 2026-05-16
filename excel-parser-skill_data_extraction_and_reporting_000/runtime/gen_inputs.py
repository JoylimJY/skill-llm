import os
import random
import openpyxl
import xlwt

random.seed(42)

# Create workspace structure
base = "/workspace"

# Create directory structure
dirs = [
    "finance/Q3_2024/departments",
    "finance/Q3_2024/templates",
    "finance/archive/2023",
    "finance/archive/2022",
    "reports/processed",
    "reports/drafts",
    "tools/scripts",
    "tools/configs",
    "data/raw",
    "data/staging",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# -----------------------------------------------------------------------
# Distractor files
# -----------------------------------------------------------------------
distractor_texts = [
    ("finance/Q3_2024/templates/budget_template_notes.txt",
     "Template notes: Fill in all yellow cells. Do not modify formulas."),
    ("finance/archive/2023/summary_2023.txt",
     "2023 Annual summary - archived. Contact finance@corp.com for access."),
    ("finance/archive/2022/legacy_report.txt",
     "Legacy format - use new template from 2023 onwards."),
    ("reports/drafts/draft_notes.md",
     "# Draft Notes\n- Waiting for HR data\n- Check IT department numbers"),
    ("tools/scripts/convert_old.py",
     "# Old conversion script - deprecated\nprint('use excel_parser instead')"),
    ("tools/configs/db_config.ini",
     "[database]\nhost=localhost\nport=5432\ndbname=finance_db"),
    ("data/raw/README_raw.txt",
     "Raw data directory. Files here are unprocessed source data."),
    ("data/staging/staging_notes.txt",
     "Staging area for intermediate processing steps."),
    ("finance/Q3_2024/processing_log.txt",
     "Processing log:\n2024-09-01: Received files from 3 departments\n2024-09-02: Pending validation"),
    ("reports/processed/index.txt",
     "Processed reports index - auto-generated. Do not edit manually."),
    ("tools/configs/parser_config_old.json",
     '{"max_rows": 50, "engine": "xlrd", "deprecated": true}'),
]
for rel_path, content in distractor_texts:
    with open(os.path.join(base, rel_path), "w") as f:
        f.write(content)

# -----------------------------------------------------------------------
# Create the actual Excel files for the task
# -----------------------------------------------------------------------

# --- File 1: marketing_budget.xlsx (Excel 2007+) ---
# Has 2 sheets, one with many rows (>50), one with few rows
wb1 = openpyxl.Workbook()
ws1 = wb1.active
ws1.title = "Q3_Expenses"
headers = ["Category", "Description", "Amount_USD", "Approved", "Notes"]
ws1.append(headers)
categories = ["Digital Ads", "Events", "PR", "Content", "Research", "Brand", "Social", "Email", "SEO", "Influencer"]
for i in range(1, 80):  # 79 data rows + 1 header = 80 rows total (exceeds max_rows=50 cap)
    cat = categories[i % len(categories)]
    ws1.append([cat, f"Campaign item {i}", round(1000 + i * 37.5, 2), "Yes" if i % 3 != 0 else "No", f"Q3 ref-{i:04d}"])

ws2 = wb1.create_sheet("Summary")
ws2.append(["Department", "Total_Budget", "Spent", "Remaining"])
ws2.append(["Marketing", 500000, 312500, 187500])
ws2.append(["Digital", 200000, 145000, 55000])
ws2.append(["Events", 150000, 98000, 52000])
# Add some empty rows (to test EXCEL_KEEP_EMPTY_ROWS=false)
ws2.append([])
ws2.append([])
ws2.append(["Grand Total", 850000, 555500, 294500])

wb1.save(os.path.join(base, "finance/Q3_2024/departments/marketing_budget.xlsx"))

# --- File 2: it_budget.xls (Excel 97-2003 legacy format) ---
wb2 = xlwt.Workbook()
ws_it1 = wb2.add_sheet("Infrastructure")
it_headers = ["Item", "Vendor", "Cost_USD", "Priority", "Status"]
for col, h in enumerate(it_headers):
    ws_it1.write(0, col, h)
it_items = [
    ("Server Upgrade", "Dell", 45000, "High", "Approved"),
    ("Network Switch", "Cisco", 12000, "Medium", "Pending"),
    ("Firewall License", "Palo Alto", 8500, "High", "Approved"),
    ("Backup Storage", "NetApp", 22000, "High", "Approved"),
    ("Monitoring Tools", "Datadog", 6000, "Low", "Review"),
    ("Cloud Migration", "AWS", 75000, "Critical", "Approved"),
    ("Laptops x50", "Lenovo", 60000, "Medium", "Approved"),
    ("Security Audit", "CrowdStrike", 15000, "High", "Pending"),
    ("VPN Licenses", "Cisco", 4500, "Medium", "Approved"),
    ("UPS Systems", "APC", 9800, "High", "Approved"),
]
for row_idx, item in enumerate(it_items, 1):
    for col_idx, val in enumerate(item):
        ws_it1.write(row_idx, col_idx, val)

ws_it2 = wb2.add_sheet("Software")
sw_headers = ["License", "Seats", "Annual_Cost", "Renewal_Date"]
for col, h in enumerate(sw_headers):
    ws_it2.write(0, col, h)
sw_items = [
    ("Microsoft 365", 250, 37500, "2025-01-15"),
    ("Jira", 100, 12000, "2025-03-01"),
    ("Confluence", 100, 8000, "2025-03-01"),
    ("GitHub Enterprise", 80, 15000, "2025-06-01"),
    ("Zoom", 300, 9000, "2025-02-28"),
]
for row_idx, item in enumerate(sw_items, 1):
    for col_idx, val in enumerate(item):
        ws_it2.write(row_idx, col_idx, str(val))

wb2.save(os.path.join(base, "finance/Q3_2024/departments/it_budget.xls"))

# --- File 3: hr_budget.xlsm (Excel macro-enabled) ---
# openpyxl can create .xlsm with keep_vba=False workaround
wb3 = openpyxl.Workbook()
ws_hr1 = wb3.active
ws_hr1.title = "Headcount"
hr_headers = ["Department", "Headcount", "Avg_Salary", "Total_Payroll", "Bonus_Pool", "Training_Budget"]
ws_hr1.append(hr_headers)
depts = [
    ("Engineering", 45, 120000, 5400000, 540000, 90000),
    ("Sales", 30, 95000, 2850000, 427500, 45000),
    ("Marketing", 15, 88000, 1320000, 132000, 30000),
    ("Finance", 10, 105000, 1050000, 105000, 20000),
    ("HR", 8, 82000, 656000, 65600, 16000),
    ("IT", 20, 110000, 2200000, 220000, 55000),
    ("Operations", 25, 75000, 1875000, 187500, 37500),
    ("Legal", 5, 140000, 700000, 70000, 10000),
    ("Customer Success", 18, 78000, 1404000, 140400, 27000),
    ("Product", 12, 125000, 1500000, 150000, 24000),
]
for row in depts:
    ws_hr1.append(list(row))

# Empty rows in between
ws_hr1.append([])
ws_hr1.append([])

ws_hr2 = wb3.create_sheet("Recruitment")
rec_headers = ["Role", "Department", "Salary_Band", "Target_Q4", "Status"]
ws_hr2.append(rec_headers)
roles = [
    ("Senior Engineer", "Engineering", "110k-135k", 5, "Open"),
    ("Sales Manager", "Sales", "90k-115k", 2, "Interviewing"),
    ("Data Analyst", "Finance", "80k-100k", 3, "Open"),
    ("DevOps Engineer", "IT", "105k-130k", 2, "Offer"),
    ("Product Manager", "Product", "115k-140k", 1, "Open"),
    ("UX Designer", "Engineering", "90k-110k", 2, "Screening"),
    ("Legal Counsel", "Legal", "130k-160k", 1, "Open"),
]
for role in roles:
    ws_hr2.append(list(role))

wb3.save(os.path.join(base, "finance/Q3_2024/departments/hr_budget.xlsm"))

print("Input files generated successfully.")
print("Files created:")
print("  finance/Q3_2024/departments/marketing_budget.xlsx")
print("  finance/Q3_2024/departments/it_budget.xls")
print("  finance/Q3_2024/departments/hr_budget.xlsm")