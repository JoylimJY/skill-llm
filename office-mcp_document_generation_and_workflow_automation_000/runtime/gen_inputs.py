import os
import csv
import random

random.seed(42)

base = "/workspace"

# --- Create deeply nested distractor structure ---
dirs = [
    "archive/2022/q1", "archive/2022/q2", "archive/2022/q3", "archive/2022/q4",
    "archive/2023/q1", "archive/2023/q2",
    "data/raw", "data/processed", "data/temp",
    "reports/drafts", "reports/final",
    "templates/word", "templates/excel",
    "scripts/legacy", "scripts/utils",
    "configs",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# --- Distractor files ---
distractors = [
    ("archive/2022/q1/sales_summary.txt", "Q1 2022 summary - see finance team for details"),
    ("archive/2022/q4/annual_review.txt", "Annual review placeholder - not finalized"),
    ("archive/2023/q1/notes.txt", "Meeting notes: discuss pipeline for Q2"),
    ("data/processed/cleaned_old.csv", "store,revenue\nStore A,10000\nStore B,20000"),
    ("data/temp/scratch.txt", "temporary calculations - ignore"),
    ("reports/drafts/draft_v1.txt", "Draft report - superseded by v2"),
    ("reports/drafts/draft_v2.txt", "Draft report v2 - pending manager approval"),
    ("templates/word/old_template.txt", "Old Word template - deprecated"),
    ("templates/excel/old_sheet.txt", "Old Excel template - use new format"),
    ("scripts/legacy/generate_report_old.py", "# Deprecated script\nprint('old report')"),
    ("scripts/utils/helpers.py", "# Utility helpers\ndef fmt(x): return str(x)"),
    ("configs/settings.json", '{"region": "North", "fiscal_year": 2024, "currency": "USD"}'),
    ("configs/db_config.txt", "host=localhost\nport=5432\ndb=salesdb"),
    ("archive/2023/q2/partial_data.csv", "product,units\nWidget A,150\nWidget B,300"),
    ("data/raw/README_OLD.txt", "Raw data landing zone - files dropped by ETL at midnight"),
]
for relpath, content in distractors:
    with open(os.path.join(base, relpath), "w") as f:
        f.write(content)

# --- THE ACTUAL PROBLEM: Messy raw sales CSV ---
# Regional Q3 2024 sales data - messy: inconsistent casing, some blank rows, trailing spaces
stores = ["Downtown", "Westside", "Northgate", "Eastpark", "Southmall"]
products = ["Widget A", "Widget B", "Gadget Pro", "Gadget Lite", "SuperTool"]
months = ["July", "August", "September"]

rows = [["Store", "Product", "Month", "Units Sold", "Unit Price", "Total Revenue"]]

random.seed(42)
for store in stores:
    for product in products:
        for month in months:
            units = random.randint(50, 500)
            price = round(random.uniform(9.99, 99.99), 2)
            revenue = round(units * price, 2)
            # Introduce messiness: random trailing spaces, mixed case
            store_val = store + ("  " if random.random() > 0.7 else "")
            rows.append([store_val, product, month, units, price, revenue])

# Add a few blank rows (mess)
rows.insert(10, ["", "", "", "", "", ""])
rows.insert(25, ["", "", "", "", "", ""])
rows.insert(50, ["", "", "", "", "", ""])

raw_csv_path = os.path.join(base, "data/raw/q3_2024_sales_raw.csv")
with open(raw_csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(rows)

# --- Manager's briefing note ---
briefing = """Q3 2024 Regional Sales Review - Action Required
================================================

Please process the attached raw sales data file (data/raw/q3_2024_sales_raw.csv) and produce
the following three deliverables for the board meeting on Friday:

1. An Excel workbook (q3_sales_report.xlsx) containing the cleaned sales data table.
   - The first row must be the header: Store, Product, Month, Units Sold, Unit Price, Total Revenue
   - Skip any blank/empty rows from the raw file
   - Strip extra whitespace from store names
   - Include a final TOTALS row at the bottom summing Units Sold and Total Revenue

2. A Word document (q3_executive_summary.docx) with:
   - Document title: "Q3 2024 Regional Sales Executive Summary"
   - A paragraph body containing: the total number of transactions (non-blank data rows),
     the top-performing store by total revenue, and overall total revenue figure.

3. A PowerPoint presentation (q3_board_deck.pptx) with at least 3 slides:
   - Slide 1: Title slide with "Q3 2024 Board Review" as the title
   - Slide 2: Title "Performance Highlights" with a text body listing the top 3 stores by revenue
   - Slide 3: Title "Next Steps" with body text describing at least two recommended actions

All three files should be placed in the reports/final/ directory.
"""

with open(os.path.join(base, "BRIEFING.txt"), "w") as f:
    f.write(briefing)

print("Workspace generated successfully.")
print(f"Raw CSV: {raw_csv_path}")
print(f"Briefing: {os.path.join(base, 'BRIEFING.txt')}")