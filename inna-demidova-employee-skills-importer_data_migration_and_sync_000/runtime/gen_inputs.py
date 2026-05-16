import os
import csv
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Distractor directory structure ──────────────────────────────────────────
dirs = [
    "hr_system/archive/2022",
    "hr_system/archive/2023",
    "hr_system/reports/quarterly",
    "hr_system/reports/annual",
    "hr_system/scripts/migration",
    "hr_system/scripts/backup",
    "hr_system/configs",
    "hr_system/docs",
    "hr_system/exports/raw",
    "hr_system/exports/processed",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "hr_system/archive/2022/employee_export_2022.csv": "id,name,department\n1,John Doe,Engineering\n2,Jane Smith,HR\n",
    "hr_system/archive/2023/employee_export_2023.csv": "id,name,department\n1,John Doe,Engineering\n2,Jane Smith,HR\n3,Bob Marley,Finance\n",
    "hr_system/reports/quarterly/q3_2023.txt": "Q3 2023 headcount: 47 employees\nAttrition rate: 2.1%\n",
    "hr_system/reports/annual/annual_2023.txt": "Annual headcount report 2023\nTotal FTEs: 52\n",
    "hr_system/scripts/migration/old_import.py": "# deprecated import script - do not use\nimport csv\nprint('legacy script')\n",
    "hr_system/scripts/backup/db_backup.sh": "#!/bin/bash\npg_dump mydb > backup.sql\n",
    "hr_system/configs/db_config.json": '{"host": "localhost", "port": 5432, "db": "hrdb"}\n',
    "hr_system/docs/schema_v1.md": "# Old Schema\n## Tables\n- employees\n- departments\n",
    "hr_system/exports/raw/skills_old.csv": "employee,skill,years\nJohn Doe,Python,3\nJane Smith,Java,5\n",
    "hr_system/exports/processed/skills_processed_2022.json": '[{"employee":"John Doe","skills":["Python","Java"]}]\n',
    "hr_system/scripts/migration/README_old.txt": "Run migrate.py before running any import scripts.\n",
}
for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# ── Mock "database" state files ──────────────────────────────────────────────
# These represent what the agent is told already exists in the database.
# The agent must read these as the "current DB state" for comparison.

# skill_categories already in DB (agent must skip these)
existing_categories = ["Java", "DevOps"]
with open(os.path.join(workspace, "hr_system/configs/db_skill_categories.txt"), "w") as f:
    for c in existing_categories:
        f.write(c + "\n")

# skills already in DB (agent must skip these)
# format: skill_name|category_name
existing_skills = [
    ("Java", "Java"),
    ("Spring", "Java"),
    ("Docker", "DevOps"),
]
with open(os.path.join(workspace, "hr_system/configs/db_skills.txt"), "w") as f:
    for s, c in existing_skills:
        f.write(f"{s}|{c}\n")

# employees in DB - note: some have extra whitespace (proprietary trap: TRIM())
# format: id|first_name|last_name
db_employees = [
    ("uuid-001", "John", "Doe"),
    ("uuid-002", "Jane", "Smith"),
    ("uuid-003", "Viktoriia", "Kovalenko"),   # CSV will have "Victoriia" (spelling diff)
    ("uuid-004", "Yurii   ", "Solokha"),       # 3 trailing spaces (whitespace trap)
    ("uuid-005", "Marco", "Rossi"),
    ("uuid-006", "Anita", "Sharma"),
    # "Boris Karasov" intentionally absent - CSV will have "Boris Karasov" with no close match enough
]
with open(os.path.join(workspace, "hr_system/configs/db_employees.txt"), "w") as f:
    for eid, fn, ln in db_employees:
        f.write(f"{eid}|{fn}|{ln}\n")

# ── The main CSV input (messy, multi-row headers, duplicates, edge cases) ───
# Row 1: ignored metadata
# Row 2: category headers (some spanning multiple columns, some blank)
# Row 3: skill names
# Row 4+: employee data rows

# Categories: .NET (cols 2-4), Front-end (cols 5-7), Java (cols 8-9), DevOps (cols 10-11)
# Skills:     C#, ASP.net, MVC | JavaScript, HTML, CSS | Java, Spring | Docker, Kubernetes
# Employees: 7 people (with edge cases)

csv_path = os.path.join(workspace, "hr_system/exports/raw/employee_skills_2024.csv")

# We build the CSV manually to have precise control over multi-row headers
# and messy data. Using raw string writing (not csv module) for full control.

rows = []

# Row 1: metadata/ignored
rows.append(["Export Date: 2024-01-15", "", "", "", "", "", "", "", "", "", ""])

# Row 2: category row (blank for name cols, then category names spanning columns)
# cols:  0=FirstName, 1=LastName, 2=FullName, 3=Unit | 4=C#, 5=ASP.net, 6=MVC | 7=JavaScript, 8=HTML, 9=CSS | 10=Java, 11=Spring | 12=Docker, 13=Kubernetes
rows.append(["", "", "", "", ".NET", "", "", "Front-end", "", "", "Java", "", "DevOps", ""])

# Row 3: skill names (column headers)
rows.append(["First Name", "Last Name", "Full Name", "Unit", "C#", "ASP.net", "MVC", "JavaScript", "HTML", "CSS", "Java", "Spring", "Docker", "Kubernetes"])

# Employee data rows — with various edge cases:
# John Doe: normal, has skills
rows.append(["John", "Doe", "John Doe", "Backend", "5", "3", "0", "2", "0", "0", "0", "0", "0", "0"])

# Jane Smith: normal
rows.append(["Jane", "Smith", "Jane Smith", "Frontend", "0", "0", "0", "7", "5", "4", "0", "0", "0", "0"])

# Victoriia Kovalenko: misspelling (DB has "Viktoriia") - fuzzy match trap
rows.append(["Victoriia", "Kovalenko", "Victoriia Kovalenko", "Backend", "4", "4", "2", "0", "0", "0", "3", "2", "0", "0"])

# Yurii Solokha: DB has "Yurii   " (3 trailing spaces) - TRIM trap
rows.append(["Yurii", "Solokha", "Yurii Solokha", "DevOps", "0", "0", "0", "0", "0", "0", "0", "0", "6", "5"])

# Marco Rossi: normal
rows.append(["Marco", "Rossi", "Marco Rossi", "Java", "0", "0", "0", "0", "0", "0", "5", "4", "0", "0"])

# DUPLICATE ROW for John Doe with different experience values for C# (should keep max=7)
rows.append(["John", "Doe", "John Doe", "Backend", "7", "0", "0", "0", "0", "0", "0", "0", "0", "0"])

# Anita Sharma: normal, only DevOps
rows.append(["Anita", "Sharma", "Anita Sharma", "DevOps", "0", "0", "0", "0", "0", "0", "0", "0", "3", "0"])

# "Xanthe Zarakis": completely unknown employee - should be skipped and reported
rows.append(["Xanthe", "Zarakis", "Xanthe Zarakis", "QA", "2", "0", "0", "3", "0", "0", "0", "0", "0", "0"])

# "  Boris  " with leading/trailing spaces in CSV name, Karasov = no DB match → skip
rows.append(["  Boris  ", "Karasov", "Boris Karasov", "Backend", "3", "0", "0", "0", "0", "0", "0", "0", "0", "0"])

with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    for row in rows:
        writer.writerow(row)

print(f"Workspace prepared at {workspace}")
print(f"CSV written to {csv_path}")
print("Distractor files and DB state files created.")