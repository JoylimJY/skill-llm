import os
import random
import csv
import io

random.seed(42)

# Create directory structure
dirs = [
    "/mnt/user-data/uploads",
    "/mnt/user-data/outputs",
    "/workspace/archive/2023Q4",
    "/workspace/archive/2024Q1",
    "/workspace/logs/system",
    "/workspace/logs/access",
    "/workspace/config/db",
    "/workspace/config/app",
    "/workspace/scripts/etl",
    "/workspace/scripts/reports",
    "/workspace/temp/cache",
    "/workspace/temp/staging",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# Create distractor files
distractor_files = {
    "/workspace/archive/2023Q4/inventory_snapshot.csv": "药品编码,库存量,更新时间\nM001,500,2023-10-01\nM002,320,2023-10-01\n",
    "/workspace/archive/2024Q1/budget_report.txt": "2024年第一季度预算报告\n总预算：1,200,000元\n已执行：876,000元\n",
    "/workspace/logs/system/error.log": "2024-01-15 ERROR: DB connection timeout\n2024-01-16 WARN: Slow query detected\n",
    "/workspace/logs/access/access_20240101.log": "GET /api/drugs 200\nPOST /api/dispense 201\n",
    "/workspace/config/db/db_config.ini": "[database]\nhost=localhost\nport=5432\nname=pharmacy_db\n",
    "/workspace/config/app/settings.yaml": "app_name: PharmacySystem\nversion: 2.3.1\ndebug: false\n",
    "/workspace/scripts/etl/transform.py": "# ETL transform stub\ndef transform(df):\n    pass\n",
    "/workspace/scripts/reports/monthly_summary.py": "# Monthly summary generator stub\ndef generate():\n    pass\n",
    "/workspace/temp/cache/session_abc123.tmp": "session_data_placeholder",
    "/workspace/temp/staging/upload_queue.json": '{"queue": [], "processed": 0}',
    "/workspace/archive/2023Q4/staff_roster.csv": "工号,姓名,科室\nE001,张三,药剂科\nE002,李四,急诊科\n",
    "/workspace/archive/2024Q1/equipment_list.txt": "设备清单\n高效液相色谱仪 x2\n药品自动分装机 x1\n",
}

for path, content in distractor_files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# ─────────────────────────────────────────────────────────────
# Generate the main messy dataset: pharmacy dispensing records
# Encoded in GBK to test the encoding fallback requirement
# ─────────────────────────────────────────────────────────────

# Column headers
headers = ["发药单号", "发药日期", "药品名称", "药品类别", "单价", "数量", "总金额", "科室", "经手药师", "患者ID", "备注"]

# Base data pools
drug_names = ["阿莫西林胶囊", "布洛芬片", "氯雷他定片", "头孢克洛颗粒", "蒙脱石散", "维生素C片",
              "复方感冒灵颗粒", "盐酸二甲双胍片", "阿托伐他汀钙片", "奥美拉唑肠溶胶囊"]
drug_categories = ["抗菌药物", "解热镇痛", "抗过敏", "抗菌药物", "消化科", "维生素类",
                   "感冒类", "降糖药", "降脂药", "消化科"]
departments = ["内科", "外科", "急诊科", "儿科", "妇产科", "皮肤科"]
pharmacists = ["王芳", "刘明", "陈静", "赵磊", "孙雪"]

# Use fullwidth yen sign (U+FFE5) which is properly encodable in GBK
YUAN = "\uffe5"

# Date formats mix: YYYY-MM-DD, MM/DD/YYYY, Chinese "YYYY年MM月DD日"
def random_date(seed_offset=0):
    r = random.Random(42 + seed_offset)
    year = 2024
    month = r.randint(1, 6)
    day = r.randint(1, 28)
    fmt = r.choice(["iso", "us", "chinese"])
    if fmt == "iso":
        return f"{year}-{month:02d}-{day:02d}"
    elif fmt == "us":
        return f"{month:02d}/{day:02d}/{year}"
    else:
        return f"{year}年{month}月{day}日"

rows = []
random.seed(42)
dispense_ids = set()

for i in range(300):
    dispense_id = f"RX{2024000 + i:07d}"
    drug_idx = random.randint(0, len(drug_names) - 1)
    drug_name = drug_names[drug_idx]
    category = drug_categories[drug_idx]
    
    unit_price = round(random.uniform(2.5, 180.0), 2)
    qty = random.randint(1, 10)
    
    # Introduce messy currency formats in total amount
    total = unit_price * qty
    fmt_choice = random.choice(["plain", "yuan_comma", "yuan_plain"])
    if fmt_choice == "yuan_comma":
        # e.g. ￥1,200.00
        total_str = f"{YUAN}{total:,.2f}"
    elif fmt_choice == "yuan_plain":
        total_str = f"{YUAN}{total:.2f}"
    else:
        total_str = f"{total:.2f}"
    
    dept = random.choice(departments)
    pharmacist = random.choice(pharmacists)
    patient_id = f"P{random.randint(10000, 99999)}"
    
    # Introduce ~5% negative amounts (simulating returns/refunds)
    if random.random() < 0.05:
        total_str = f"-{abs(total):.2f}"
        qty = -qty
    
    date_str = random_date(i)
    remark = ""
    
    row = [dispense_id, date_str, drug_name, category,
           f"{unit_price:.2f}", str(qty), total_str, dept, pharmacist, patient_id, remark]
    rows.append(row)
    dispense_ids.add(dispense_id)

# Inject exact duplicates (15 rows)
dup_rows = random.sample(rows[:100], 15)
rows.extend(dup_rows)

# Inject missing values: 20 rows with empty 科室, 10 rows with empty 药品名称
for i in range(20):
    rows[50 + i][7] = ""  # 科室 missing

for i in range(10):
    rows[150 + i][2] = ""  # 药品名称 missing
    rows[150 + i][3] = ""  # 药品类别 missing

# Inject a mostly-empty column: 备注 (already ~empty, add a few)
for i in [5, 12, 33]:
    rows[i][10] = "已复核"

# Inject 8 rows where 单价 is "N/A" or empty (阻断性问题 candidate)
for i in range(8):
    rows[200 + i][4] = "N/A"
    rows[200 + i][6] = "N/A"

# Shuffle rows
random.shuffle(rows)

# Write as GBK-encoded CSV (the encoding trap)
output_path = "/mnt/user-data/uploads/pharmacy_dispense_2024.csv"

with open(output_path, "w", encoding="gbk", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(rows)

print(f"Generated {len(rows)} rows (including duplicates) -> {output_path}")
print("File encoding: GBK")
print("Issues planted:")
print("  - 15 duplicate rows")
print("  - 20 rows with missing 科室")
print("  - 10 rows with missing 药品名称/药品类别")
print("  - 8 rows with 单价/总金额 = 'N/A'")
print("  - ~5% rows with negative amounts (returns)")
print("  - Mixed date formats (ISO, US, Chinese)")
print("  - Mixed currency formats in 总金额")
print("  - 备注 column ~99% empty")