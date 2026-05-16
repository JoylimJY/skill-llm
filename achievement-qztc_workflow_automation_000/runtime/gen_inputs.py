#!/usr/bin/env python3
"""
Generate a realistic sandbox workspace for the achievement-qztc task.
"""
import os
import random
import re
from pathlib import Path

random.seed(999)  # deterministic workspace generation

# ─────────────────────────────────────────────
# 1. Directory structure with distractor files
# ─────────────────────────────────────────────
workspace = Path("/workspace")

dirs = [
    "temp",
    "archive/2022",
    "archive/2023",
    "scripts/utils",
    "scripts/old",
    "reports/draft",
    "reports/final",
    "data/raw",
    "data/processed",
    "config",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractors = {
    "archive/2022/课程目标达成情况分析表-旧版.docx.bak": b"FAKE_BACKUP",
    "archive/2023/成绩汇总-22级.xlsx.bak": b"FAKE_XLS",
    "scripts/utils/calc_score.py": b"# placeholder script\ndef calc(x): return x\n",
    "scripts/old/generate_report_v1.py": b"# deprecated\nimport os\nprint('old version')\n",
    "reports/draft/分析表草稿.txt": "这是草稿文件，不要使用此文件。".encode("utf-8"),
    "reports/final/README.txt": "最终报告目录。".encode("utf-8"),
    "data/raw/原始成绩.csv": "学号,姓名,成绩\n001,张三,85\n002,李四,90\n".encode("utf-8"),
    "data/processed/处理后成绩.csv": "学号,姓名,成绩\n001,张三,85\n".encode("utf-8"),
    "config/settings.json": b'{"version": "1.0", "output_dir": "/workspace/temp"}',
    "config/template_config.yaml": b"template: v2\nformat: docx\n",
    "temp/旧模版备份.docx.bak": b"BACKUP",
}
for rel_path, content in distractors.items():
    fp = workspace / rel_path
    fp.write_bytes(content)


# ─────────────────────────────────────────────
# 2. Generate the Excel student roster (XLS)
#    - 9 rows total, 2 with 旷考 → 7 valid students
#    - class name: "23级软工2班" → grade=23, major=软工
# ─────────────────────────────────────────────
import xlwt

wb = xlwt.Workbook(encoding='utf-8')
ws = wb.add_sheet('Sheet1')

headers = ['学号', '姓名', '班级', '备注']
for col, h in enumerate(headers):
    ws.write(0, col, h)

students_raw = [
    ('2301001', '陈晓明', '23级软工2班', ''),
    ('2301002', '李雨涵', '23级软工2班', ''),
    ('2301003', '王志远', '23级软工2班', '旷考'),
    ('2301004', '赵静雯', '23级软工2班', ''),
    ('2301005', '刘佳琪', '23级软工2班', '旷考'),
    ('2301006', '孙浩然', '23级软工2班', ''),
    ('2301007', '周思雨', '23级软工2班', ''),
    ('2301008', '吴明杰', '23级软工2班', ''),
    ('2301009', '郑晨曦', '23级软工2班', ''),
]

for row_idx, (sid, name, cls, remark) in enumerate(students_raw, start=1):
    ws.write(row_idx, 0, sid)
    ws.write(row_idx, 1, name)
    ws.write(row_idx, 2, cls)
    ws.write(row_idx, 3, remark)

xls_path = workspace / "temp" / "数据可视化技术23级软工.xls"
wb.save(str(xls_path))
print(f"Created: {xls_path}")


# ─────────────────────────────────────────────
# 3. Generate the Word template with placeholders
#    Tables 7 and 8 must be at specific indices.
#    We need at least 9 tables total (indices 0-8).
#    Table 8 (index 8): capacity for 3 students (5 rows = 2 header + 3 data + 1 avg)
#    Table 7 (index 7): has rows [5],[8],[11],[14] each with 8 cells
# ─────────────────────────────────────────────
from docx import Document
from docx.shared import Pt, Inches
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

doc = Document()

# Document-level paragraph with placeholders (split across runs to test robustness)
p = doc.add_paragraph()
run1 = p.add_run("学年：$acyear")
run1.font.name = "宋体"
run1.font.size = Pt(11)
run2 = p.add_run("$  学期：第$semester$学期")
run2.font.name = "宋体"
run2.font.size = Pt(11)

p2 = doc.add_paragraph()
run3 = p2.add_run("$g$级$major$专业，共$total$参加考核")
run3.font.name = "宋体"
run3.font.size = Pt(11)

p3 = doc.add_paragraph()
run4 = p3.add_run("填表日期：$year$年$month$月$day$日")
run4.font.name = "宋体"
run4.font.size = Pt(11)

# ── Tables 0-6: filler tables (so table7 is index 7, table8 is index 8) ──
for t_idx in range(7):
    tbl = doc.add_table(rows=3, cols=3)
    tbl.style = 'Table Grid'
    tbl.cell(0, 0).text = f"辅助表{t_idx+1}"
    tbl.cell(0, 1).text = "数据"
    tbl.cell(0, 2).text = "说明"
    for r in range(1, 3):
        for c in range(3):
            tbl.cell(r, c).text = f"R{r}C{c}"

# ── Table 7 (index 7): summary table ──
# Needs at least 15 rows, at least 8 columns
# rows[5].cells[7], rows[8].cells[7], rows[11].cells[7], rows[14].cells[7]
NUM_ROWS_T7 = 15
NUM_COLS_T7 = 8
t7 = doc.add_table(rows=NUM_ROWS_T7, cols=NUM_COLS_T7)
t7.style = 'Table Grid'
t7.cell(0, 0).text = "课程目标汇总"
t7.cell(0, 1).text = "评价方式"
t7.cell(0, 2).text = "权重"
t7.cell(0, 3).text = "满分"
t7.cell(0, 4).text = "均分"
t7.cell(0, 5).text = "最高分"
t7.cell(0, 6).text = "最低分"
t7.cell(0, 7).text = "达成值"

section_labels = {
    2: "课程目标1", 5: "目标1达成", 
    6: "课程目标2", 8: "目标2达成",
    9: "课程目标3", 11: "目标3达成",
    12: "课程目标4", 14: "目标4达成",
}
for r in range(1, NUM_ROWS_T7):
    for c in range(NUM_COLS_T7):
        if c == 0 and r in section_labels:
            t7.cell(r, c).text = section_labels[r]
        elif c == 7 and r in [5, 8, 11, 14]:
            t7.cell(r, c).text = "待填写"
        else:
            t7.cell(r, c).text = f"—"

# ── Table 8 (index 8): individual achievement table ──
# Template capacity = 3 students (rows: 2 header + 3 data + 1 avg = 6 rows total)
# Valid students = 7 → need to insert 4 rows
NUM_COLS_T8 = 11
TEMPLATE_DATA_ROWS = 3  # capacity for 3 students in template
TOTAL_T8_ROWS = 2 + TEMPLATE_DATA_ROWS + 1  # = 6

t8 = doc.add_table(rows=TOTAL_T8_ROWS, cols=NUM_COLS_T8)
t8.style = 'Table Grid'

# Row 0: header row 1
headers_r0 = [
    "序号", "学号", "姓名",
    "课程目标1(25分)", "课程目标1",
    "课程目标2(30分)", "课程目标2",
    "课程目标3(26.5分)", "课程目标3",
    "课程目标4(18.5分)", "课程目标4",
]
for c, h in enumerate(headers_r0):
    t8.cell(0, c).text = h

# Row 1: header row 2
headers_r1 = [
    "序号", "学号", "姓名",
    "得分", "达成值",
    "得分", "达成值",
    "得分", "达成值",
    "得分", "达成值",
]
for c, h in enumerate(headers_r1):
    t8.cell(1, c).text = h

# Rows 2 to 2+TEMPLATE_DATA_ROWS-1: placeholder data rows
for r in range(2, 2 + TEMPLATE_DATA_ROWS):
    for c in range(NUM_COLS_T8):
        t8.cell(r, c).text = ""

# Last row: average row
avg_row = t8.rows[-1]
avg_row.cells[0].text = "平均值"
for c in range(1, NUM_COLS_T8):
    avg_row.cells[c].text = ""

# Save template
template_path = workspace / "temp" / "课程目标达成情况分析表-数据可视化-模版.docx"
doc.save(str(template_path))
print(f"Created: {template_path}")

# Verify table count
doc_check = Document(str(template_path))
print(f"Total tables in template: {len(doc_check.tables)}")
assert len(doc_check.tables) == 9, f"Expected 9 tables, got {len(doc_check.tables)}"
assert len(doc_check.tables[8].rows) == 6, f"Table8 should have 6 rows"
assert len(doc_check.tables[7].rows) == 15, f"Table7 should have 15 rows"

print("Workspace setup complete.")
print(f"Valid students (non-旷考): 7")
print(f"Template table8 capacity: 3")
print(f"Rows to insert: 4")