#!/usr/bin/env python3
"""
Generate the sandbox workspace for the balance sheet generation task.
"""
import os
import random
from pathlib import Path
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import (
    Font, Border, Side, Alignment, PatternFill, numbers
)
from openpyxl.utils import get_column_letter

random.seed(42)

# ── workspace root ──────────────────────────────────────────────────────────
WORKSPACE = Path("/root/.openclaw/workspace")
WORKSPACE.mkdir(parents=True, exist_ok=True)

# ── skill directory (scripts already exist per spec, we write stubs) ─────────
SKILL_DIR = WORKSPACE / "skills" / "资产负债表"
SCRIPTS_DIR = SKILL_DIR / "scripts"
SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
REFS_DIR = SKILL_DIR / "references"
REFS_DIR.mkdir(parents=True, exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractor_dirs = [
    WORKSPACE / "archive" / "2024Q4",
    WORKSPACE / "archive" / "2025Q1",
    WORKSPACE / "drafts",
    WORKSPACE / "temp",
    WORKSPACE / "reports" / "monthly",
    WORKSPACE / "reports" / "annual",
    WORKSPACE / "data" / "raw",
    WORKSPACE / "data" / "processed",
]
for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

distractor_files = [
    (WORKSPACE / "archive" / "2024Q4" / "财务报表_202409-old.xlsx", b"PK\x03\x04"),
    (WORKSPACE / "archive" / "2024Q4" / "资产负债表_202409.xlsx", b"PK\x03\x04"),
    (WORKSPACE / "archive" / "2025Q1" / "财务报表_202501-t.xlsx", b"PK\x03\x04"),
    (WORKSPACE / "drafts" / "草稿_资产负债表.xlsx", b"PK\x03\x04"),
    (WORKSPACE / "drafts" / "notes.txt", b"draft notes - do not use"),
    (WORKSPACE / "temp" / "tmp_output.xlsx", b"PK\x03\x04"),
    (WORKSPACE / "temp" / "debug_log.txt", b"debug log"),
    (WORKSPACE / "reports" / "monthly" / "利润表_202510.xlsx", b"PK\x03\x04"),
    (WORKSPACE / "reports" / "annual" / "年度报表_2024.xlsx", b"PK\x03\x04"),
    (WORKSPACE / "data" / "raw" / "raw_transactions_202511.csv",
     b"date,amount,category\n2025-11-01,1000,income\n"),
    (WORKSPACE / "data" / "processed" / "processed_202511.json",
     b'{"status": "draft", "month": "202511"}'),
    (WORKSPACE / "data" / "processed" / "summary_202510.csv",
     b"item,value\ntotal,999999\n"),
]
for fpath, content in distractor_files:
    fpath.write_bytes(content)

# ── write the skill scripts ──────────────────────────────────────────────────
generate_script = SCRIPTS_DIR / "generate_balance_sheet.py"
generate_script.write_text(
    '''#!/usr/bin/env python3
"""Command-line entry point for balance sheet generation."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from balance_sheet_generator import BalanceSheetGenerator

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_balance_sheet.py <source_file> [output_file]")
        sys.exit(1)
    source = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else "资产负债表.xlsx"
    gen = BalanceSheetGenerator(source)
    gen.generate(output)
    print(f"Generated: {output}")

if __name__ == "__main__":
    main()
''',
    encoding="utf-8",
)

generator_script = SCRIPTS_DIR / "balance_sheet_generator.py"
generator_script.write_text(
    '''#!/usr/bin/env python3
"""
Core balance sheet generator implementing 11 rules.
"""
import openpyxl
from openpyxl import load_workbook
from copy import copy
from pathlib import Path


class BalanceSheetGenerator:
    def __init__(self, source_path: str):
        self.source_path = source_path
        self.wb_src = load_workbook(source_path)

    def _get_mingxi_data(self):
        """Read 明细表 sheet."""
        ws = self.wb_src["明细表"]
        bank_totals = {}
        category_totals = {}
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or len(row) < 13:
                continue
            yue_e = row[0]   # A列 余额
            cat1 = row[2]    # C列 分类1
            faheng = row[7]  # H列 发生金额
            bank = row[12]   # M列 银行账户名称
            if bank and isinstance(yue_e, (int, float)):
                bank_totals[bank] = bank_totals.get(bank, 0) + yue_e
            if cat1 and isinstance(faheng, (int, float)):
                category_totals[cat1] = category_totals.get(cat1, 0) + faheng
        return bank_totals, category_totals

    def _get_profit(self):
        """Read 利润表 - find 经营利润 row, return E column value."""
        ws = self.wb_src["利润表"]
        for row in ws.iter_rows(min_row=1, values_only=True):
            if not row:
                continue
            b_val = row[1] if len(row) > 1 else None  # B列
            e_val = row[4] if len(row) > 4 else None  # E列
            if b_val and "经营利润" in str(b_val):
                return e_val if isinstance(e_val, (int, float)) else 0
        return 0

    def generate(self, output_path: str):
        """Apply all 11 rules and save output."""
        wb_out = load_workbook(self.source_path)
        ws = wb_out["资产负债表"]

        bank_totals, category_totals = self._get_mingxi_data()
        profit = self._get_profit()

        # Rule 2: Copy D column computed values to B column (before changing D)
        d_values = {}
        for row_idx in range(1, ws.max_row + 1):
            d_cell = ws.cell(row=row_idx, column=4)  # D列
            val = d_cell.value
            # If it's a formula, we need the cached value - use data_only workbook
            d_values[row_idx] = val

        # Load data_only for formula values
        wb_data = load_workbook(self.source_path, data_only=True)
        ws_data = wb_data["资产负债表"]
        for row_idx in range(1, ws.max_row + 1):
            d_val_computed = ws_data.cell(row=row_idx, column=4).value
            if d_val_computed is not None:
                b_cell = ws.cell(row=row_idx, column=2)
                if not (isinstance(b_cell.value, str) and not b_cell.value.replace('.','').replace('-','').isdigit()):
                    b_cell.value = d_val_computed

        # Rule 3: C5 = 0
        ws["C5"] = 0

        # Rule 4: D7 = 招商银行 余额合计
        ws["D7"] = bank_totals.get("招商银行", 0)

        # Rule 5: D8 = 交通银行 余额合计
        ws["D8"] = bank_totals.get("交通银行", 0)

        # Rule 6: C9 = 应收 发生金额合计
        ws["C9"] = category_totals.get("应收", 0)

        # Rule 7: C11 = 预收 发生金额合计
        ws["C11"] = category_totals.get("预收", 0)

        # Rule 8: C12 = 应付 发生金额合计
        ws["C12"] = category_totals.get("应付", 0)

        # Rule 9: C14 = 经营利润
        ws["C14"] = profit

        # Rule 10: C15 = 0
        ws["C15"] = 0

        # Rule 11: Preserve formulas - they are already in the template
        wb_out.save(output_path)
        print(f"Balance sheet saved to {output_path}")
''',
    encoding="utf-8",
)

rules_doc = REFS_DIR / "rules.md"
rules_doc.write_text(
    """# 规则详细说明

## 规则执行顺序
必须严格按 1→11 顺序执行。

## 关键注意事项
- 规则2必须在规则4、5之前执行
- M列银行数据需要按名称求和（可能有多条）
- 公式单元格（如C7=D7-B7）必须保留为公式
- 金额保留2位小数
""",
    encoding="utf-8",
)

skill_md = SKILL_DIR / "SKILL.md"
skill_md.write_text(
    open("/dev/stdin").read() if False else """# 资产负债表生成技能\n见主文档""",
    encoding="utf-8",
)

# ── Create the main source Excel file: 财务报表 202511-t.xlsx ────────────────
SOURCE_FILE = WORKSPACE / "财务报表 202511-t.xlsx"

wb = Workbook()

# ─────────────────────────── Sheet 1: 资产负债表 ───────────────────────────
ws_bs = wb.active
ws_bs.title = "资产负债表"

thin = Side(style="thin")
thick = Side(style="medium")
thin_border = Border(left=thin, right=thin, top=thin, bottom=thin)
header_border = Border(left=thick, right=thick, top=thick, bottom=thick)

header_font = Font(name="宋体", bold=True, size=12)
normal_font = Font(name="宋体", size=11)
center_align = Alignment(horizontal="center", vertical="center")

# Header row 1 - merged title
ws_bs.merge_cells("A1:D1")
ws_bs["A1"] = "资产负债表（2025年11月）"
ws_bs["A1"].font = Font(name="宋体", bold=True, size=14)
ws_bs["A1"].alignment = center_align
ws_bs["A1"].border = header_border

# Header row 2 - column names
headers = ["科目", "上月余额", "本月发生额", "累计金额"]
for col_idx, h in enumerate(headers, 1):
    cell = ws_bs.cell(row=2, column=col_idx, value=h)
    cell.font = header_font
    cell.alignment = center_align
    cell.border = thin_border

# Data rows - structure:
# Row 3: 流动资产
# Row 4: 固定资产
# Row 5: 固定资产合计
# Row 6: 现金
# Row 7: 招商银行
# Row 8: 交通银行（公）
# Row 9: 应收款合计
# Row 10: 预付款
# Row 11: 预收款
# Row 12: 应付款
# Row 13: 其他往来
# Row 14: 当年利润
# Row 15: 未分配利润
# Row 16: 合计

data_rows = [
    # (row, subject, B_last_month, C_formula_or_value, D_formula_or_value)
    (3,  "流动资产合计",    None,         None,          None),
    (4,  "固定资产",        850000.00,    "=D4-B4",      "=B4+C4"),   # D4 will be set by rule2 from old D4
    (5,  "固定资产合计",    None,         None,          None),
    (6,  "现金",            5280.00,      "=D6-B6",      12500.00),
    (7,  "招商银行",        258498.64,    "=D7-B7",      228843.03),  # D7 overwritten by rule4; B7 set by rule2 first
    (8,  "交通银行（公）", 17153.55,     "=D8-B8",      78128.70),   # D8 overwritten by rule5
    (9,  "应收款合计",      1685000.00,   200000.00,     "=B9+C9"),
    (10, "预付款",          45000.00,     "=D10-B10",    48000.00),
    (11, "预收款",          689872.40,    201736.00,     "=B11+C11"),
    (12, "应付款",          320000.00,    -50000.00,     "=B12+C12"),
    (13, "其他往来",        125000.00,    "=D13-B13",    130000.00),
    (14, "当年利润",        557069.52,    29583.54,      "=B14+C14"),
    (15, "未分配利润",      88000.00,     0,             "=B15+C15"),
    (16, "合计",            None,         None,          None),
]

for row_num, subject, b_val, c_val, d_val in data_rows:
    # A column: subject name
    a_cell = ws_bs.cell(row=row_num, column=1, value=subject)
    a_cell.font = normal_font
    a_cell.border = thin_border
    a_cell.alignment = Alignment(horizontal="left", vertical="center")

    # B column: 上月余额
    b_cell = ws_bs.cell(row=row_num, column=2)
    b_cell.value = b_val
    b_cell.font = normal_font
    b_cell.border = thin_border
    b_cell.alignment = center_align
    if b_val is not None:
        b_cell.number_format = '#,##0.00'

    # C column: 本月发生额
    c_cell = ws_bs.cell(row=row_num, column=3)
    c_cell.value = c_val
    c_cell.font = normal_font
    c_cell.border = thin_border
    c_cell.alignment = center_align
    if c_val is not None and not isinstance(c_val, str):
        c_cell.number_format = '#,##0.00'

    # D column: 累计金额
    d_cell = ws_bs.cell(row=row_num, column=4)
    d_cell.value = d_val
    d_cell.font = normal_font
    d_cell.border = thin_border
    d_cell.alignment = center_align
    if d_val is not None and not isinstance(d_val, str):
        d_cell.number_format = '#,##0.00'

# Set column widths
ws_bs.column_dimensions['A'].width = 20
ws_bs.column_dimensions['B'].width = 16
ws_bs.column_dimensions['C'].width = 16
ws_bs.column_dimensions['D'].width = 16

# Row heights
for r in range(1, 17):
    ws_bs.row_dimensions[r].height = 22

# ─────────────────────────── Sheet 2: 明细表 ────────────────────────────────
ws_mx = wb.create_sheet("明细表")

# Headers: A=余额, B=..., C=分类1, D..G=..., H=发生金额, I..L=..., M=银行账户名称
mx_headers = ["余额", "日期", "分类1", "摘要", "凭证号", "借方", "贷方", "发生金额",
              "科目代码", "科目名称", "部门", "项目", "银行账户名称"]
for col_i, h in enumerate(mx_headers, 1):
    cell = ws_mx.cell(row=1, column=col_i, value=h)
    cell.font = Font(bold=True)
    cell.border = thin_border

# Detailed rows - carefully crafted test data
# Format: (A_余额, B_日期, C_分类1, D_摘要, E_凭证号, F_借方, G_贷方, H_发生金额,
#           I_科目代码, J_科目名称, K_部门, L_项目, M_银行账户名称)
mx_data = [
    # 招商银行 entries (2 rows, sum=27780.68+201062.35=228843.03)
    (27780.68,  "2025-11-05", "银行",  "销售收款",   "J001", 27780.68,   0,          27780.68,   "1002", "招商银行基本户", "销售部", "P01", "招商银行"),
    (201062.35, "2025-11-15", "银行",  "工程款回款", "J002", 201062.35,  0,          201062.35,  "1002", "招商银行项目户", "工程部", "P02", "招商银行"),
    # 交通银行 entries (1 row)
    (78128.70,  "2025-11-10", "银行",  "备用金归还", "J003", 78128.70,   0,          78128.70,   "1003", "交通银行对公户", "财务部", "P01", "交通银行"),
    # 应收 entries (sum=200000)
    (500000.00, "2025-11-08", "应收",  "应收货款A",  "J004", 0,          150000.00,  150000.00,  "1121", "应收账款-客户A","销售部","P03", None),
    (300000.00, "2025-11-20", "应收",  "应收货款B",  "J005", 0,          50000.00,   50000.00,   "1121", "应收账款-客户B","销售部","P03", None),
    # 预收 entries (sum=201736)
    (200000.00, "2025-11-12", "预收",  "预收定金C",  "J006", 200000.00,  0,          200000.00,  "2203", "预收账款-客户C","销售部","P04", None),
    (5000.00,   "2025-11-18", "预收",  "预收服务费", "J007", 1736.00,    0,          1736.00,    "2203", "预收账款-服务", "服务部","P04", None),
    # 应付 entries (sum=-50000, negative means payment outflow)
    (180000.00, "2025-11-03", "应付",  "付原材料款", "J008", 0,          50000.00,   -50000.00,  "2202", "应付账款-供应商A","采购部","P05", None),
    # Distractor entries with other categories
    (45000.00,  "2025-11-22", "预付",  "预付工程款", "J009", 3000.00,    0,          3000.00,    "1123", "预付账款",      "工程部","P06", None),
    (12000.00,  "2025-11-25", "其他",  "其他往来",   "J010", 5000.00,    0,          5000.00,    "2241", "其他应付款",    "综合部","P07", None),
    # Another bank entry with different bank name (distractor)
    (35000.00,  "2025-11-28", "银行",  "工行备用金", "J011", 35000.00,   0,          35000.00,   "1004", "工商银行备用金","财务部","P01", "工商银行"),
]

for row_i, row_data in enumerate(mx_data, 2):
    for col_i, val in enumerate(row_data, 1):
        cell = ws_mx.cell(row=row_i, column=col_i, value=val)
        cell.border = thin_border
        cell.font = normal_font

ws_mx.column_dimensions['A'].width = 14
ws_mx.column_dimensions['C'].width = 10
ws_mx.column_dimensions['H'].width = 14
ws_mx.column_dimensions['M'].width = 18

# ─────────────────────────── Sheet 3: 利润表 ────────────────────────────────
ws_pl = wb.create_sheet("利润表")

# Headers across columns A-F (B=科目名称, E=本期数)
pl_headers_row = ["序号", "科目名称", "上期数", "上年同期", "本期数", "备注"]
for col_i, h in enumerate(pl_headers_row, 1):
    cell = ws_pl.cell(row=1, column=col_i, value=h)
    cell.font = Font(bold=True)
    cell.border = thin_border

# Profit table data - B=科目, E=value
# 经营利润 is at row 8, value=29583.54
pl_data = [
    (1,  "营业收入",        820000.00,  780000.00,  850000.00,  ""),
    (2,  "营业成本",        650000.00,  620000.00,  680000.00,  ""),
    (3,  "毛利润",          170000.00,  160000.00,  170000.00,  ""),
    (4,  "销售费用",        25000.00,   22000.00,   28000.00,   ""),
    (5,  "管理费用",        38000.00,   35000.00,   40000.00,   ""),
    (6,  "财务费用",        12000.00,   11000.00,   13000.00,   ""),
    (7,  "其他收益",        500.00,     400.00,     583.54,     ""),
    (8,  "经营利润",        95000.00,   92000.00,   29583.54,   "关键指标"),  # <-- rule9 target
    (9,  "营业外收入",      2000.00,    1500.00,    2000.00,    ""),
    (10, "营业外支出",      1000.00,    800.00,     1000.00,    ""),
    (11, "利润总额",        96000.00,   92700.00,   30583.54,   ""),
    (12, "所得税费用",      24000.00,   23175.00,   7645.89,    ""),
    (13, "净利润",          72000.00,   69525.00,   22937.65,   ""),
]

for row_i, row_data in enumerate(pl_data, 2):
    for col_i, val in enumerate(row_data, 1):
        cell = ws_pl.cell(row=row_i, column=col_i, value=val)
        cell.border = thin_border
        cell.font = normal_font

ws_pl.column_dimensions['B'].width = 18
ws_pl.column_dimensions['E'].width = 14

# ── Save source file ─────────────────────────────────────────────────────────
wb.save(str(SOURCE_FILE))
print(f"Source file created: {SOURCE_FILE}")

# ── Additional distractor text files ─────────────────────────────────────────
(WORKSPACE / "data" / "raw" / "会计分录_202511.txt").write_text(
    "借：应收账款 200000\n贷：主营业务收入 200000\n(distractor - not the actual source file)",
    encoding="utf-8",
)
(WORKSPACE / "reports" / "monthly" / "财务分析202511.txt").write_text(
    "2025年11月财务分析报告\n营业收入同比增长8.97%\n(distractor report)",
    encoding="utf-8",
)
(WORKSPACE / "temp" / "backup_20251130.txt").write_text(
    "backup checkpoint - ignore",
    encoding="utf-8",
)

print("Sandbox workspace created successfully.")
print(f"Key file: {SOURCE_FILE}")
print("Distractor files: created in archive/, drafts/, temp/, reports/, data/")