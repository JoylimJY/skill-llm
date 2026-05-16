import os
import random
import json
import csv

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Distractor directory structure ──────────────────────────────────────────
dirs = [
    "client_records/2024/Q1",
    "client_records/2024/Q2",
    "client_records/2024/Q3",
    "client_records/2024/Q4",
    "internal/reports/monthly",
    "internal/reports/annual",
    "internal/config",
    "archive/legacy_csv",
    "archive/processed",
    "logs/system",
    "logs/access",
    "tmp/staging",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = [
    ("client_records/2024/Q1/client_summary.txt", "Client consultation summary Q1 2024.\nTotal sessions: 142\nPending reviews: 8\n"),
    ("client_records/2024/Q2/notes.txt", "Q2 follow-up notes. See manager for details.\n"),
    ("client_records/2024/Q3/flagged_sessions.txt", "Sessions 34, 78, 91 flagged for re-review.\n"),
    ("client_records/2024/Q4/billing.csv", "session_id,amount,status\n001,200,paid\n002,150,pending\n"),
    ("internal/reports/monthly/oct_2024.txt", "Monthly report October 2024. Revenue up 12%.\n"),
    ("internal/reports/annual/annual_2023.json", json.dumps({"year": 2023, "sessions": 1823, "revenue": 912400})),
    ("internal/config/app_config.json", json.dumps({"timezone": "Asia/Shanghai", "locale": "zh-CN", "version": "2.4.1"})),
    ("internal/config/feature_flags.json", json.dumps({"enable_divination": True, "beta_reporting": False})),
    ("archive/legacy_csv/old_sessions_2022.csv", "date,time,consultant\n2022-03-14,09:15,Wang\n2022-07-22,14:00,Li\n"),
    ("archive/processed/done.txt", "All Q3 2022 records processed and archived.\n"),
    ("logs/system/sys.log", "[INFO] Server started 2024-10-01 08:00:00\n[WARN] Slow query at 2024-10-01 09:23:11\n[INFO] Backup complete 2024-10-01 23:59:00\n"),
    ("logs/access/access.log", "192.168.1.10 - - [01/Oct/2024:09:00:01] GET /api/session 200\n192.168.1.11 - - [01/Oct/2024:09:01:44] POST /api/divination 201\n"),
    ("tmp/staging/import_queue.txt", "Pending import: batch_nov_2024.csv\nStatus: awaiting_validation\n"),
]

for rel_path, content in distractor_files:
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# ── THE ACTUAL PROBLEM FILE ──────────────────────────────────────────────────
# A messy CSV of client consultation timestamps including:
# - valid entries with normal hours/minutes
# - entries where hour%8==0 (the "0→8" trap for upper trigram)
# - entries where minute%8==0 (the "0→8" trap for lower trigram)
# - entries where (hour+minute)%6==0 (the "0→6" trap for moving yao)
# - entries where ALL three produce a 0-remainder (ultimate trap)
# - invalid/malformed entries that must be SKIPPED

consultation_rows = [
    # Valid entries
    # id, datetime_str, notes
    # hour=9 (9%8=1), minute=15 (15%8=7), yao=(9+15)%6=0→6
    ("C001", "2024-11-05 09:15", "Career guidance session"),
    # hour=14 (14%8=6), minute=32 (32%8=0→8), yao=(14+32)%6=4
    ("C002", "2024-11-05 14:32", "Relationship consultation"),
    # hour=16 (16%8=0→8), minute=45 (45%8=5), yao=(16+45)%6=1
    ("C003", "2024-11-06 16:45", "Business decision reading"),
    # hour=8 (8%8=0→8), minute=0 (0%8=0→8), yao=(8+0)%6=2
    ("C004", "2024-11-06 08:00", "Morning opening divination"),
    # hour=23 (23%8=7), minute=59 (59%8=3), yao=(23+59)%6=0→6
    ("C005", "2024-11-07 23:59", "Late night urgent reading"),
    # hour=12 (12%8=4), minute=24 (24%8=0→8), yao=(12+24)%6=0→6
    ("C006", "2024-11-07 12:24", "Health inquiry"),
    # hour=3 (3%8=3), minute=3 (3%8=3), yao=(3+3)%6=0→6
    ("C007", "2024-11-08 03:03", "Dream interpretation"),
    # hour=0 (0%8=0→8), minute=48 (48%8=0→8), yao=(0+48)%6=0→6
    ("C008", "2024-11-08 00:48", "Midnight consultation"),
    # hour=17 (17%8=1), minute=8 (8%8=0→8), yao=(17+8)%6=1
    ("C009", "2024-11-09 17:08", "Travel planning"),
    # hour=6 (6%8=6), minute=12 (12%8=4), yao=(6+12)%6=0→6
    ("C010", "2024-11-09 06:12", "Morning qi reading"),
    # MALFORMED / INVALID entries — must be skipped
    ("C011", "2024-11-10 25:61", "Invalid time — out of range"),
    ("C012", "NOT_A_DATE", "Corrupt record"),
    ("C013", "", "Empty datetime"),
    ("C014", "2024/11/10 10:30", "Wrong date separator format"),
    ("C015", "2024-11-11 10", "Missing minutes"),
]

csv_path = os.path.join(workspace, "client_records/2024/Q4/batch_consultations.csv")
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["session_id", "consultation_datetime", "notes"])
    for row in consultation_rows:
        writer.writerow(row)

print(f"[gen_inputs] Workspace prepared at {workspace}")
print(f"[gen_inputs] Problem file: {csv_path}")
print(f"[gen_inputs] Total rows (including malformed): {len(consultation_rows)}")