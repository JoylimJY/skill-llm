import os
import random
import json
import csv

random.seed(42)

WORKSPACE = "/workspace"

# ── directory structure (distractors) ──────────────────────────────────────
dirs = [
    "scripts",
    "references",
    "data/raw",
    "data/processed",
    "data/archive",
    "config",
    "logs",
    "tests",
    "docs/internal",
    "docs/external",
    "reports/monthly",
    "reports/quarterly",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── distractor files ────────────────────────────────────────────────────────
distractor_files = {
    "scripts/format_date.py": "# placeholder\n",
    "scripts/format_number.py": "# placeholder\n",
    "scripts/format_currency.py": "# placeholder\n",
    "scripts/format_phone.py": "# placeholder\n",
    "references/date-formats.md": "# Date format reference\nISO 8601: YYYY-MM-DD\n",
    "references/currency.md": "# Currency reference\nHUF = Hungarian Forint\n",
    "references/address-format.md": "# Address format\nirányítószám város, utca házszám\n",
    "config/app_config.json": json.dumps({"locale": "hu_HU", "currency": "HUF"}, indent=2),
    "logs/import_2024.log": "2024-01-10 INFO: Import started\n2024-01-10 INFO: 320 records processed\n",
    "logs/errors.log": "ERROR: invalid date format on row 7\nERROR: missing phone on row 14\n",
    "docs/internal/onboarding_process.md": "# Onboarding\nAll customer data must be validated before export.\n",
    "docs/external/compliance_note.txt": "Regulatory note: all exported data must comply with local HU standards.\n",
    "data/archive/customers_2023.csv": "id,name,dob\n1,Kovács István,1990-05-21\n2,Nagy Anna,1985-11-03\n",
    "tests/test_format.py": "# unit tests placeholder\ndef test_date(): pass\n",
    "reports/monthly/jan_summary.txt": "January: 145 new customers\n",
    "reports/quarterly/q1_2024.txt": "Q1 2024: 412 new customers, total deposits: 5120000 HUF\n",
}
for rel_path, content in distractor_files.items():
    with open(os.path.join(WORKSPACE, rel_path), "w", encoding="utf-8") as f:
        f.write(content)

# ── THE ACTUAL PROBLEM INPUT ────────────────────────────────────────────────
# Messy raw customer CSV with:
#  - ISO dates (need Hungarian short format: YYYY. MM. DD.)
#  - English-style floats for balance/income (need Hungarian: space-thousands, comma-decimal, Ft suffix)
#  - Raw international phone numbers (need +36 XX XXX XXXX)
#  - Flat address components (need Hungarian address string)

customers = [
    {
        "id": "C001",
        "name": "Kovács Béla",
        "birth_date": "1978-03-15",
        "account_balance": "2345678.50",
        "monthly_income": "485000.00",
        "phone_digits": "36301234567",   # raw digits, no formatting
        "zip": "1051",
        "city": "Budapest",
        "street": "Vörösmarty tér",
        "house_number": "5",
        "floor": "2",
        "door": "14",
    },
    {
        "id": "C002",
        "name": "Tóth Mária",
        "birth_date": "1990-11-02",
        "account_balance": "750000.00",
        "monthly_income": "320000.75",
        "phone_digits": "36209876543",
        "zip": "4024",
        "city": "Debrecen",
        "street": "Piac utca",
        "house_number": "18",
        "floor": "fsz",
        "door": "3",
    },
    {
        "id": "C003",
        "name": "Szabó László",
        "birth_date": "2001-07-28",
        "account_balance": "12500.25",
        "monthly_income": "195000.00",
        "phone_digits": "36703334444",
        "zip": "7621",
        "city": "Pécs",
        "street": "Király utca",
        "house_number": "33",
        "floor": "1",
        "door": "6",
    },
    {
        "id": "C004",
        "name": "Fekete Eszter",
        "birth_date": "1965-01-09",
        "account_balance": "9876543.00",
        "monthly_income": "1200000.00",
        "phone_digits": "36201112233",
        "zip": "9700",
        "city": "Szombathely",
        "street": "Fő tér",
        "house_number": "2",
        "floor": "3",
        "door": "1",
    },
    {
        "id": "C005",
        "name": "Varga Péter",
        "birth_date": "1983-06-30",
        "account_balance": "333333.33",
        "monthly_income": "410000.50",
        "phone_digits": "36305556677",
        "zip": "6720",
        "city": "Szeged",
        "street": "Dugonics tér",
        "house_number": "10",
        "floor": "fsz",
        "door": "2",
    },
]

fieldnames = ["id","name","birth_date","account_balance","monthly_income",
              "phone_digits","zip","city","street","house_number","floor","door"]

raw_csv_path = os.path.join(WORKSPACE, "data/raw/customers_raw.csv")
with open(raw_csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(customers)

print("Workspace generated successfully.")
print(f"Raw input: {raw_csv_path}")