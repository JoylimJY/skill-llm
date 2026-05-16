import os
import random
import string

random.seed(42)

BASE = "/workspace/data_landing_zone"

# --- Directory structure ---
dirs = [
    "raw/sales/2023/q1",
    "raw/sales/2023/q2",
    "raw/sales/2023/q3",
    "raw/sales/2023/q4",
    "raw/inventory/daily",
    "raw/inventory/weekly",
    "raw/logistics/inbound",
    "raw/logistics/outbound",
    "raw/logistics/returns",
    "raw/hr/payroll",
    "raw/hr/attendance",
    "raw/finance/invoices",
    "raw/finance/expenses",
    "staging/processed",
    "staging/failed",
    "staging/pending",
    "archive/2022",
    "archive/2021",
    "tmp/scratch",
    "tmp/uploads",
]

for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# --- Helper ---
def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

def rand_word(n=8):
    return ''.join(random.choices(string.ascii_lowercase, k=n))

# --- CSV files (some large >1MB, some small) ---
csv_files = [
    ("raw/sales/2023/q1/transactions_q1.csv", 1.5),    # 1.5 MB
    ("raw/sales/2023/q2/transactions_q2.csv", 2.1),    # 2.1 MB
    ("raw/sales/2023/q3/transactions_q3.csv", 0.8),    # 0.8 MB
    ("raw/sales/2023/q4/transactions_q4.csv", 3.2),    # 3.2 MB  <-- largest
    ("raw/inventory/daily/stock_levels.csv", 1.2),     # 1.2 MB
    ("raw/inventory/weekly/weekly_summary.csv", 0.4),  # 0.4 MB
    ("raw/logistics/inbound/shipments_in.csv", 2.7),   # 2.7 MB  <-- 2nd
    ("raw/logistics/outbound/shipments_out.csv", 0.3), # 0.3 MB
    ("raw/logistics/returns/returns_log.csv", 0.15),   # 0.15 MB
    ("raw/finance/invoices/invoice_data.csv", 1.8),    # 1.8 MB
    ("raw/finance/expenses/expense_report.csv", 0.5),  # 0.5 MB
    ("raw/hr/payroll/payroll_aug.csv", 2.3),           # 2.3 MB  <-- 3rd
    ("raw/hr/attendance/attendance_log.csv", 0.6),     # 0.6 MB
    ("staging/processed/clean_output.csv", 0.9),       # 0.9 MB
    ("archive/2022/old_transactions.csv", 0.2),        # 0.2 MB
]

# CSV header
csv_header = "id,timestamp,value,category,status,region,user_id,amount\n"

for rel_path, size_mb in csv_files:
    full_path = os.path.join(BASE, rel_path)
    target_bytes = int(size_mb * 1024 * 1024)
    content = csv_header
    while len(content.encode()) < target_bytes:
        row = ",".join([
            str(random.randint(1000, 9999)),
            f"2023-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            f"{random.uniform(1.0, 9999.99):.2f}",
            random.choice(["A","B","C","D"]),
            random.choice(["active","inactive","pending"]),
            random.choice(["NA","EU","APAC"]),
            f"U{random.randint(100,999)}",
            f"{random.uniform(10.0, 5000.0):.2f}"
        ])
        content += row + "\n"
    write_file(full_path, content[:target_bytes])

# --- LOG files (we need total size of all .log files) ---
# Create a known set of log files with known ERROR lines
log_files_spec = [
    ("raw/logistics/inbound/ingest.log", 120 * 1024, 7),    # 7 ERROR lines
    ("raw/logistics/outbound/ship.log", 85 * 1024, 3),      # 3 ERROR lines
    ("staging/failed/pipeline_errors.log", 200 * 1024, 15), # 15 ERROR lines
    ("staging/processed/run_ok.log", 60 * 1024, 2),         # 2 ERROR lines
    ("tmp/scratch/debug.log", 40 * 1024, 0),                # 0 ERROR lines
    ("archive/2022/old_run.log", 310 * 1024, 5),            # 5 ERROR lines
    ("raw/finance/invoices/etl.log", 95 * 1024, 4),         # 4 ERROR lines
]
# Total ERROR count in .log files = 7+3+15+2+0+5+4 = 36

log_levels = ["INFO", "DEBUG", "WARN"]

def make_log_content(target_bytes, error_count):
    lines = []
    error_inserted = 0
    approx_lines = target_bytes // 80
    for i in range(approx_lines):
        if error_inserted < error_count and random.random() < (error_count / max(approx_lines, 1)) * 3:
            level = "ERROR"
            error_inserted += 1
        else:
            level = random.choice(log_levels)
        msg = rand_word(12)
        lines.append(f"2023-09-{random.randint(1,28):02d} {random.randint(0,23):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d} [{level}] {msg}\n")
    # Make sure we insert remaining errors
    while error_inserted < error_count:
        lines.append(f"2023-09-15 12:00:00 [ERROR] forced_error_{rand_word(4)}\n")
        error_inserted += 1
    content = "".join(lines)
    return content

for rel_path, size_bytes, error_count in log_files_spec:
    full_path = os.path.join(BASE, rel_path)
    content = make_log_content(size_bytes, error_count)
    write_file(full_path, content)

# --- TXT files with ERROR pattern for counting ---
# The task: count lines matching "[ERROR]" pattern across ALL .txt files
txt_files_spec = [
    ("raw/hr/payroll/payroll_errors.txt", 8),      # 8 lines with [ERROR]
    ("raw/hr/attendance/attendance_notes.txt", 3), # 3 lines with [ERROR]
    ("staging/failed/error_summary.txt", 12),       # 12 lines with [ERROR]
    ("staging/pending/pending_notes.txt", 0),       # 0 lines with [ERROR]
    ("raw/sales/2023/q1/notes.txt", 2),             # 2 lines with [ERROR]
    ("raw/finance/expenses/audit_notes.txt", 5),    # 5 lines with [ERROR]
    ("tmp/uploads/upload_log.txt", 1),              # 1 line with [ERROR]
    ("archive/2021/legacy_notes.txt", 6),           # 6 lines with [ERROR]
]
# Total [ERROR] in .txt files = 8+3+12+0+2+5+1+6 = 37

def make_txt_content(error_count):
    lines = []
    total = random.randint(30, 80)
    error_inserted = 0
    for i in range(total):
        if error_inserted < error_count and random.random() < 0.4:
            lines.append(f"[ERROR] {rand_word(10)} failed at step {random.randint(1,20)}\n")
            error_inserted += 1
        else:
            lines.append(f"[{random.choice(['INFO','DEBUG','WARN'])}] {rand_word(10)} completed ok\n")
    while error_inserted < error_count:
        lines.append(f"[ERROR] {rand_word(10)} critical failure\n")
        error_inserted += 1
    return "".join(lines)

for rel_path, error_count in txt_files_spec:
    full_path = os.path.join(BASE, rel_path)
    content = make_txt_content(error_count)
    write_file(full_path, content)

# --- JSON files (distractors) ---
json_files = [
    "raw/sales/2023/q1/schema.json",
    "raw/inventory/daily/config.json",
    "staging/processed/manifest.json",
    "tmp/scratch/temp_state.json",
    "archive/2022/metadata.json",
]
for rel_path in json_files:
    full_path = os.path.join(BASE, rel_path)
    write_file(full_path, '{"status": "ok", "version": "1.0", "records": ' + str(random.randint(100, 9999)) + '}\n')

# --- YAML files (distractors) ---
yaml_files = [
    "staging/pending/pipeline_config.yaml",
    "raw/logistics/inbound/mapping.yaml",
]
for rel_path in yaml_files:
    full_path = os.path.join(BASE, rel_path)
    write_file(full_path, f"pipeline:\n  name: {rand_word()}\n  version: 2\n  enabled: true\n")

# --- XML files (distractors) ---
xml_files = [
    "raw/finance/invoices/invoice_schema.xml",
    "archive/2021/legacy_format.xml",
]
for rel_path in xml_files:
    full_path = os.path.join(BASE, rel_path)
    write_file(full_path, f'<?xml version="1.0"?><root><name>{rand_word()}</name></root>\n')

# --- SH scripts (distractors) ---
sh_files = [
    "staging/processed/post_process.sh",
    "tmp/scratch/cleanup.sh",
]
for rel_path in sh_files:
    full_path = os.path.join(BASE, rel_path)
    write_file(full_path, "#!/bin/bash\necho 'done'\n")

# --- Print summary for verification ---
import subprocess
result = subprocess.run(["find", BASE, "-type", "f"], capture_output=True, text=True)
files = result.stdout.strip().split("\n")
print(f"Total files created: {len(files)}")

# Print expected answers for reference (will be used in eval)
print("\n=== EXPECTED ANSWERS (for eval reference) ===")

# 1. File counts per extension
ext_counts = {}
for f in files:
    ext = f.rsplit(".", 1)[-1] if "." in f else "no_ext"
    ext_counts[ext] = ext_counts.get(ext, 0) + 1
print("File counts per extension:", dict(sorted(ext_counts.items())))

# 2. Total size of .log files
import os as _os
total_log_size = 0
for f in files:
    if f.endswith(".log"):
        total_log_size += _os.path.getsize(f)
print(f"Total .log size (bytes): {total_log_size}")

# 3. Top 3 largest .csv files
csv_sizes = [(f, _os.path.getsize(f)) for f in files if f.endswith(".csv")]
csv_sizes.sort(key=lambda x: x[1], reverse=True)
print("Top 3 largest CSV files:")
for path, size in csv_sizes[:3]:
    print(f"  {path}: {size} bytes")

# 4. [ERROR] lines in .txt files
import re
total_error_lines = 0
for f in files:
    if f.endswith(".txt"):
        with open(f) as fh:
            for line in fh:
                if re.search(r'\[ERROR\]', line):
                    total_error_lines += 1
print(f"Total [ERROR] lines in .txt files: {total_error_lines}")