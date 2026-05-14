import os
import random

random.seed(42)

workspace = "/workspace"

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "crm/raw/sales_reps",
    "crm/raw/exports",
    "crm/raw/legacy",
    "crm/processed",
    "crm/archive/2023",
    "crm/archive/2022",
    "logs",
    "config",
    "scripts",
    "temp/scratch",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "crm/archive/2023/old_contacts.txt": "Archived. Do not process.\nfoo@bar.com\n+44 20 7946 0958",
    "crm/archive/2022/backup.csv": "id,name\n1,Old Record\n2,Another",
    "logs/import.log": "[2024-01-01] Import started\n[2024-01-01] 0 records processed\nERROR: timeout",
    "config/db.conf": "[database]\nhost=localhost\nport=5432\nuser=crm_user",
    "config/settings.ini": "[app]\ndebug=false\nversion=2.3.1",
    "scripts/migrate.sh": "#!/bin/bash\necho 'migration script placeholder'",
    "temp/scratch/notes.txt": "TODO: clean up temp files\nmeeting notes from monday",
    "temp/scratch/junk.csv": "a,b,c\n1,2,3\n4,5,6",
    "crm/processed/.gitkeep": "",
    "crm/raw/legacy/very_old_data.txt": "Legacy format - incompatible\nNO VALID DATA HERE\njohn_doe AT example DOT com",
}
for path, content in distractors.items():
    full = os.path.join(workspace, path)
    with open(full, "w") as f:
        f.write(content)

# ── SOURCE 1: messy sales rep notes (plain text, multiple contacts) ──────────
# Contains valid Turkish phones, some invalid international ones, valid/invalid emails
sales_notes = """\
Sales Rep: Mehmet Yilmaz
Date: 2024-11-03

Client visit notes:
  - Spoke with Ayse Kaya, she can be reached at ayse.kaya@globalcorp.com
    and her mobile is 0532 444 55 66. Very interested in premium package.
  - Also met Ali Demir - email: ali.demir@techsolutions.net
    Cell: 0545 876 54 32. Needs follow-up next week.
  - Random note: weather was nice today, had lunch at the corner bistro.
  - Contacted old lead: bad_email_address (not valid)
  - International ref from London: james.bond@mi6.org  phone: +44 20 7946 0958 (not our format)
  - Fatma Celik - fatma.celik@startupzone.io  -  0533-111-22-33 (dash format, invalid)
  - Zeynep Arslan zeynep.arslan@innovate.biz  phone 0506 321 98 76

Misc: internal code XREF-2024-001, budget code CTX-449
"""
with open(os.path.join(workspace, "crm/raw/sales_reps/november_notes.txt"), "w") as f:
    f.write(sales_notes)

# ── SOURCE 2: another rep's notes ────────────────────────────────────────────
sales_notes2 = """\
Rep: Burak Sahin - December visits

   Emre Yildiz    emre.yildiz@databridge.com   0 5 5 2   9 9 9   1 1   2 2  (weird spacing)
   Selin Ozturk   selin.ozturk@cloudnine.net   0541 222 33 44

   Duplicate check: ayse.kaya@globalcorp.com  0532 444 55 66   (same as Mehmet's client)

   Not a real email: @nodomain.com
   Not a real phone: 1234567
   Canan Polat    canan.polat@enterprise.org   0530 555 66 77
"""
with open(os.path.join(workspace, "crm/raw/sales_reps/december_notes.txt"), "w") as f:
    f.write(sales_notes2)

# ── SOURCE 3: CSV export from old CRM ────────────────────────────────────────
csv_export = """\
full_name,email,phone,region,notes
Tuncay Berk,tuncay.berk@logistics.com,0544 111 22 33,Ankara,VIP client
Merve Aksoy,merve.aksoy@retailpro.net,0532 999 00 11,Istanbul,New lead
Hasan Gul,NOT_AN_EMAIL,0531 888 77 66,Izmir,Data entry error
Pinar Yurt,pinar.yurt@mediasphere.com,+90-532-111-2233,Bursa,International format
Bulent Erol,bulent.erol@fintech.io,0548 333 44 55,Ankara,Standard
"""
with open(os.path.join(workspace, "crm/raw/exports/crm_export_q4.csv"), "w") as f:
    f.write(csv_export)

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk(workspace):
    for fname in files:
        print(f"  {os.path.join(root, fname)}")