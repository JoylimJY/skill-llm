import os
import random
import csv
import io

random.seed(42)

base = "/workspace"
os.makedirs(base, exist_ok=True)

# ── Directory structure with distractor files ──────────────────────────────
dirs = [
    "hospital_data/archives/2022",
    "hospital_data/archives/2023",
    "hospital_data/reports/monthly",
    "hospital_data/reports/quarterly",
    "hospital_data/scripts",
    "hospital_data/exports/raw",
    "hospital_data/exports/processed",
    "hospital_data/configs",
    "hospital_data/logs",
    "temp_uploads",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# ── Distractor files (red herrings) ────────────────────────────────────────
distractors = {
    "hospital_data/archives/2022/patients_2022.csv": (
        "patient_id,name,age,blood_pressure_systolic,blood_pressure_diastolic,ward\n"
        "1001,Alice Brown,34,120,80,Cardiology\n"
        "1002,Bob Smith,45,135,90,General\n"
    ),
    "hospital_data/archives/2023/patients_2023_v1.csv": (
        "id,full_name,dob,ward_name\n"
        "2001,Charlie Davis,1978-03-12,Oncology\n"
    ),
    "hospital_data/reports/monthly/jan_summary.txt": (
        "January Report\nTotal Admissions: 342\nDischarges: 310\n"
    ),
    "hospital_data/reports/monthly/feb_summary.txt": (
        "February Report\nTotal Admissions: 298\nDischarges: 289\n"
    ),
    "hospital_data/reports/quarterly/q1_2024.txt": (
        "Q1 2024\nAdmissions: 945\nPending Review: 23\n"
    ),
    "hospital_data/scripts/old_cleaner.py": (
        "# Deprecated script - do not use\nimport pandas as pd\n# TODO: replace with new tool\n"
    ),
    "hospital_data/configs/db_config.json": (
        '{"host": "localhost", "port": 5432, "database": "hospital_db"}\n'
    ),
    "hospital_data/configs/etl_settings.yaml": (
        "source: /data/raw\ndestination: /data/clean\nschedule: daily\n"
    ),
    "hospital_data/logs/etl_run_20240301.log": (
        "[2024-03-01 08:00] ETL started\n[2024-03-01 08:05] 1200 rows processed\n[2024-03-01 08:06] ETL completed\n"
    ),
    "hospital_data/exports/raw/export_dump_2024.csv": (
        "ID,Name,Date\n9001,Test Patient,2024-01-15\n9002,,2024-01-16\n"
    ),
    "temp_uploads/scratch.csv": (
        "col1,col2\na,b\nc,d\n"
    ),
    "hospital_data/exports/processed/.gitkeep": "",
}

for relpath, content in distractors.items():
    fpath = os.path.join(base, relpath)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)

# ── THE MAIN PROBLEM FILE: messy patient intake CSV ────────────────────────
# Column names: messy (spaces, caps, mixed case) → must be standardized
# Has duplicate rows → must be dropped
# Has missing numeric values (Age, BP Systolic, BP Diastolic) → must be filled with median
# Non-numeric columns (Name, Ward, Admitted) have some blanks but are NOT numeric → strategy only applies to numeric

random.seed(42)

# Define columns with messy names
columns = [
    "Patient ID",        # should become: patient_id
    "Full Name",         # should become: full_name
    "Age",               # should become: age          (NUMERIC - has NaN)
    "BP Systolic",       # should become: bp_systolic  (NUMERIC - has NaN)
    "BP Diastolic",      # should become: bp_diastolic (NUMERIC - has NaN)
    "Ward Name",         # should become: ward_name
    "Admitted",          # should become: admitted
]

wards = ["Cardiology", "Oncology", "General", "Neurology", "Pediatrics"]
names = [
    "Alice Brown", "Bob Smith", "Carol White", "David Jones", "Eva Martinez",
    "Frank Lee", "Grace Kim", "Henry Wilson", "Irene Chen", "James Taylor",
    "Karen Hall", "Leo Scott", "Mia Adams", "Nathan Clark", "Olivia Lewis",
    "Paul Walker", "Quinn Moore", "Rachel Allen", "Sam Baker", "Tina Hill",
]

rows = []
pid = 3001
for i in range(20):
    age = random.randint(18, 80) if random.random() > 0.15 else ""
    bp_sys = random.randint(100, 160) if random.random() > 0.15 else ""
    bp_dia = random.randint(60, 100) if random.random() > 0.15 else ""
    ward = random.choice(wards)
    name = names[i]
    admitted = random.choice(["2024-01-10", "2024-02-14", "2024-03-05", "2024-03-22"])
    rows.append([pid + i, name, age, bp_sys, bp_dia, ward, admitted])

# Inject 5 exact duplicate rows (duplicating rows 0, 3, 7, 11, 15)
dup_indices = [0, 3, 7, 11, 15]
for idx in dup_indices:
    rows.append(list(rows[idx]))

# Shuffle so duplicates aren't at end
random.shuffle(rows)

messy_csv_path = os.path.join(base, "hospital_data/exports/raw/patient_intake_2024.csv")
with open(messy_csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(columns)
    for row in rows:
        writer.writerow(row)

print(f"Generated messy input: {messy_csv_path}")
print(f"Total rows (including duplicates): {len(rows)}")
print(f"Columns: {columns}")