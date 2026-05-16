import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── distractor files / folders ──────────────────────────────────────────────
distractor_dirs = [
    "logs/2024-01", "logs/2024-02",
    "platform_configs/amazon", "platform_configs/qidian",
    "platform_configs/royalroad",
    "raw_exports/fanqie", "raw_exports/jjwxc",
    "reports/archive", "reports/drafts",
    "scripts/utils", "tmp/scratch",
]
for d in distractor_dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

distractor_files = {
    "logs/2024-01/crawler.log": "INFO 2024-01-15 fetch ok\nWARN 2024-01-16 timeout",
    "logs/2024-02/crawler.log": "INFO 2024-02-01 fetch ok",
    "platform_configs/amazon/config.yaml": "region: us-east-1\nformat: mobi",
    "platform_configs/qidian/config.yaml": "encoding: utf-8\nformat: txt",
    "raw_exports/fanqie/README_IGNORE.txt": "old format, do not use",
    "raw_exports/jjwxc/schema.txt": "columns: book_id,date,reads,likes",
    "reports/archive/2023_summary.txt": "archived report - do not edit",
    "reports/drafts/template.txt": "TEMPLATE ONLY",
    "scripts/utils/helpers.py": "# placeholder",
    "tmp/scratch/notes.txt": "scratch notes",
    "platform_configs/royalroad/settings.json": json.dumps({"base_url": "royalroad.com"}),
    "raw_exports/fanqie/old_data_2023.csv": "book_id,reads\n001,100000\n002,200000",
}
for path, content in distractor_files.items():
    with open(os.path.join(workspace, path), "w", encoding="utf-8") as f:
        f.write(content)

# ── MAIN INPUT: books metadata ───────────────────────────────────────────────
# Contains word count, time-per-thousand-words (hours), hourly rate, total revenue
books_meta = [
    {
        "book_id": "book_001",
        "title": "龙王归来",
        "platform": "起点中文网",
        "word_count": 300000,
        "time_per_thousand_words_hours": 2.0,
        "hourly_rate_cny": 50,
        "total_revenue_cny": 45000,
    },
    {
        "book_id": "book_002",
        "title": "Starfall Chronicles",
        "platform": "Royal Road",
        "word_count": 120000,
        "time_per_thousand_words_hours": 1.5,
        "hourly_rate_cny": 80,
        "total_revenue_cny": 9600,
    },
    {
        "book_id": "book_003",
        "title": "深海迷途",
        "platform": "番茄小说",
        "word_count": 200000,
        "time_per_thousand_words_hours": 2.5,
        "hourly_rate_cny": 40,
        "total_revenue_cny": 22000,
    },
    {
        "book_id": "book_004",
        "title": "Crimson Throne",
        "platform": "Amazon KDP",
        "word_count": 80000,
        "time_per_thousand_words_hours": 3.0,
        "hourly_rate_cny": 100,
        "total_revenue_cny": 38000,
    },
]

# ── MAIN INPUT: daily performance metrics (last 7 days) ──────────────────────
# Columns: book_id, date, reads, follow_rate, completion_rate, rating, daily_revenue_cny
daily_data = {
    "book_001": [
        {"date": "2024-06-10", "reads": 50000, "follow_rate": 0.35, "completion_rate": 0.48, "rating": 8.2, "daily_revenue_cny": 320},
        {"date": "2024-06-11", "reads": 52000, "follow_rate": 0.36, "completion_rate": 0.49, "rating": 8.2, "daily_revenue_cny": 330},
        {"date": "2024-06-12", "reads": 51000, "follow_rate": 0.34, "completion_rate": 0.47, "rating": 8.3, "daily_revenue_cny": 315},
        {"date": "2024-06-13", "reads": 53000, "follow_rate": 0.37, "completion_rate": 0.50, "rating": 8.3, "daily_revenue_cny": 340},
        {"date": "2024-06-14", "reads": 54000, "follow_rate": 0.38, "completion_rate": 0.51, "rating": 8.4, "daily_revenue_cny": 350},
        {"date": "2024-06-15", "reads": 55000, "follow_rate": 0.39, "completion_rate": 0.52, "rating": 8.5, "daily_revenue_cny": 360},
        # Last day: reads drop by 40% => should trigger 数据暴跌 alert
        {"date": "2024-06-16", "reads": 33000, "follow_rate": 0.25, "completion_rate": 0.44, "rating": 8.5, "daily_revenue_cny": 210},
    ],
    "book_002": [
        {"date": "2024-06-10", "reads": 8000, "follow_rate": 0.28, "completion_rate": 0.40, "rating": 7.5, "daily_revenue_cny": 80},
        {"date": "2024-06-11", "reads": 8200, "follow_rate": 0.29, "completion_rate": 0.41, "rating": 7.5, "daily_revenue_cny": 85},
        {"date": "2024-06-12", "reads": 7900, "follow_rate": 0.27, "completion_rate": 0.39, "rating": 7.4, "daily_revenue_cny": 78},
        {"date": "2024-06-13", "reads": 8100, "follow_rate": 0.28, "completion_rate": 0.40, "rating": 7.5, "daily_revenue_cny": 82},
        {"date": "2024-06-14", "reads": 8300, "follow_rate": 0.30, "completion_rate": 0.42, "rating": 7.6, "daily_revenue_cny": 90},
        {"date": "2024-06-15", "reads": 8000, "follow_rate": 0.28, "completion_rate": 0.40, "rating": 7.5, "daily_revenue_cny": 83},
        {"date": "2024-06-16", "reads": 8100, "follow_rate": 0.29, "completion_rate": 0.41, "rating": 7.5, "daily_revenue_cny": 85},
    ],
    "book_003": [
        {"date": "2024-06-10", "reads": 25000, "follow_rate": 0.52, "completion_rate": 0.63, "rating": 9.1, "daily_revenue_cny": 150},
        {"date": "2024-06-11", "reads": 26000, "follow_rate": 0.53, "completion_rate": 0.64, "rating": 9.1, "daily_revenue_cny": 155},
        {"date": "2024-06-12", "reads": 25500, "follow_rate": 0.51, "completion_rate": 0.62, "rating": 9.0, "daily_revenue_cny": 148},
        {"date": "2024-06-13", "reads": 26500, "follow_rate": 0.54, "completion_rate": 0.65, "rating": 9.2, "daily_revenue_cny": 160},
        {"date": "2024-06-14", "reads": 27000, "follow_rate": 0.55, "completion_rate": 0.66, "rating": 9.2, "daily_revenue_cny": 162},
        {"date": "2024-06-15", "reads": 26000, "follow_rate": 0.52, "completion_rate": 0.63, "rating": 9.1, "daily_revenue_cny": 153},
        # Last day: revenue spike > 2x average (avg ≈ 155, so spike would need > 310)
        # avg of first 6 = (150+155+148+160+162+153)/6 = 154.67, >2x = >309.33
        {"date": "2024-06-16", "reads": 40000, "follow_rate": 0.60, "completion_rate": 0.70, "rating": 9.3, "daily_revenue_cny": 650},
    ],
    "book_004": [
        {"date": "2024-06-10", "reads": 120000, "follow_rate": 0.55, "completion_rate": 0.65, "rating": 9.2, "daily_revenue_cny": 800},
        {"date": "2024-06-11", "reads": 122000, "follow_rate": 0.56, "completion_rate": 0.66, "rating": 9.2, "daily_revenue_cny": 810},
        {"date": "2024-06-12", "reads": 118000, "follow_rate": 0.54, "completion_rate": 0.64, "rating": 9.1, "daily_revenue_cny": 790},
        {"date": "2024-06-13", "reads": 125000, "follow_rate": 0.57, "completion_rate": 0.67, "rating": 9.3, "daily_revenue_cny": 820},
        {"date": "2024-06-14", "reads": 123000, "follow_rate": 0.56, "completion_rate": 0.66, "rating": 9.3, "daily_revenue_cny": 815},
        {"date": "2024-06-15", "reads": 121000, "follow_rate": 0.55, "completion_rate": 0.65, "rating": 9.2, "daily_revenue_cny": 805},
        {"date": "2024-06-16", "reads": 124000, "follow_rate": 0.56, "completion_rate": 0.66, "rating": 9.2, "daily_revenue_cny": 810},
    ],
}

# Save inputs
os.makedirs(os.path.join(workspace, "input_data"), exist_ok=True)

with open(os.path.join(workspace, "input_data", "books_meta.json"), "w", encoding="utf-8") as f:
    json.dump(books_meta, f, ensure_ascii=False, indent=2)

for book_id, records in daily_data.items():
    with open(os.path.join(workspace, "input_data", f"{book_id}_daily.json"), "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

# ── Additional distractor: old report formats ────────────────────────────────
old_report = {
    "generated_at": "2024-05-01",
    "books": [{"id": "book_000", "status": "archived"}]
}
with open(os.path.join(workspace, "reports/archive/old_report_2024_05.json"), "w") as f:
    json.dump(old_report, f)

print("Workspace generated successfully.")
print("Files created:")
for root, dirs, files in os.walk(workspace):
    for fn in files:
        print(" ", os.path.join(root, fn).replace(workspace, ""))