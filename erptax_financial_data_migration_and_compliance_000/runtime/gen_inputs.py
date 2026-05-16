import os
import random
import zipfile
import shutil
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side, Protection
from openpyxl.utils import get_column_letter
import xlwt
import struct
import xml.etree.ElementTree as ET

random.seed(42)

WORKSPACE = Path("/workspace")

# ─── Directory skeleton (distractors) ───────────────────────────────────────
dirs = [
    "scripts",
    "references",
    "erp_exports/2024Q1",
    "erp_exports/archive",
    "templates/official",
    "templates/drafts",
    "output",
    "logs",
    "config",
    "docs/internal",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# Distractor files
(WORKSPACE / "logs" / "fill_run_20240115.log").write_text(
    "2024-01-15 09:12:33 INFO Starting fill process\n2024-01-15 09:12:35 WARN calcChain not found, skipping\n"
)
(WORKSPACE / "config" / "db_conn.ini").write_text(
    "[database]\nhost=192.168.1.50\nport=3306\nname=erp_prod\n"
)
(WORKSPACE / "docs" / "internal" / "workflow_notes.txt").write_text(
    "Remember: never modify formula cells directly. Only update cached values.\n"
)
(WORKSPACE / "erp_exports" / "archive" / "README_OLD.txt").write_text(
    "Old ERP format - do not use. See 2024Q1 folder for current exports.\n"
)
(WORKSPACE / "references" / "erp-row-maps.md").write_text(
    """# ERP Row Maps

## 利润表 (Profit & Loss)
ERP col1=行次, col3=本期金额, col4=本年累计金额

| ERP 行次 | Template Row | 字段名称 |
|---------|-------------|---------|
| 1  | 7  | 营业收入 |
| 2  | 8  | 营业成本 |
| 3  | 9  | 税金及附加 |
| 4  | 10 | 销售费用 |
| 5  | 11 | 管理费用 |
| 6  | 12 | 研发费用 |
| 7  | 13 | 财务费用 |
| 14 | 20 | 其他收益 |
| 21 | 28 | 营业外收入 |
| 22 | 29 | 营业外支出 |
""")
(WORKSPACE / "references" / "xlsx-edit-guide.md").write_text(
    """# XLSX Edit Guide

## XML Cell Patterns

Only modify <v> tags. Never touch <f> or s= attributes.

### Data cell:
<c r="D7" s="34"><v>0</v></c>
→ <c r="D7" s="34"><v>9999.00</v></c>

### Formula cell (update cached value only):
<c r="D21" s="40"><f>ROUND(D7+D8,2)</f><v>0</v></c>
→ <c r="D21" s="40"><f>ROUND(D7+D8,2)</f><v>9999.00</v></c>
""")
(WORKSPACE / "templates" / "drafts" / "draft_profit_v1.txt").write_text(
    "Draft template - superseded by official version in templates/official/\n"
)
(WORKSPACE / "config" / "fill_config.yaml").write_text(
    "template_dir: templates/official\noutput_dir: output\nerp_dir: erp_exports/2024Q1\n"
)
(WORKSPACE / "docs" / "internal" / "tax_bureau_notes.txt").write_text(
    "Tax bureau requires all formulas to remain intact. Do not break formula cells.\n"
    "Submit output .xlsx files by Q2 deadline.\n"
)
(WORKSPACE / "erp_exports" / "archive" / "profit_2023Q4.xls").write_text("FAKE OLD XLS")

# ─── scripts/xlsx_unpack.py ──────────────────────────────────────────────────
(WORKSPACE / "scripts" / "xlsx_unpack.py").write_text(
    r"""#!/usr/bin/env python3
"""
    r"""\"\"\"Unpack an xlsx file into a directory with pretty-printed XML.\"\"\"
import sys, zipfile, os, shutil
from pathlib import Path
from lxml import etree

def unpack(xlsx_path, out_dir):
    out_dir = Path(out_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    with zipfile.ZipFile(xlsx_path, 'r') as z:
        for name in z.namelist():
            dest = out_dir / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            data = z.read(name)
            if name.endswith('.xml') or name.endswith('.rels'):
                try:
                    tree = etree.fromstring(data)
                    pretty = etree.tostring(tree, pretty_print=True, xml_declaration=True, encoding='UTF-8')
                    dest.write_bytes(pretty)
                    continue
                except Exception:
                    pass
            dest.write_bytes(data)
    print(f"Unpacked {xlsx_path} -> {out_dir}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: xlsx_unpack.py input.xlsx output_dir")
        sys.exit(1)
    unpack(sys.argv[1], sys.argv[2])
"""
)

# ─── scripts/xlsx_pack.py ────────────────────────────────────────────────────
(WORKSPACE / "scripts" / "xlsx_pack.py").write_text(
    r"""#!/usr/bin/env python3
"""
    r"""\"\"\"Repack a directory back into a valid xlsx file.\"\"\"
import sys, zipfile, os
from pathlib import Path

def pack(src_dir, out_xlsx):
    src_dir = Path(src_dir)
    out_xlsx = Path(out_xlsx)
    with zipfile.ZipFile(out_xlsx, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fpath in sorted(src_dir.rglob('*')):
            if fpath.is_file():
                arcname = fpath.relative_to(src_dir).as_posix()
                zf.write(fpath, arcname)
    print(f"Packed {src_dir} -> {out_xlsx}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: xlsx_pack.py src_dir output.xlsx")
        sys.exit(1)
    pack(sys.argv[1], sys.argv[2])
"""
)

# ─── Build the ERP export (利润表) ────────────────────────────────────────────
# Columns: 0=项目, 1=行次, 2=附注, 3=本期金额, 4=本年累计金额
erp_data = [
    # header rows (messy - agent must handle)
    ["公司名称：测试科技有限公司", "", "", "", ""],
    ["利润表", "", "", "", ""],
    ["单位：人民币元", "", "", "本期金额", "本年累计金额"],
    # actual data rows: col1=行次
    ["营业收入", "1",  "注1", 8523614.50,  17204390.00],
    ["营业成本", "2",  "注2", 6215430.20,  12543870.40],
    ["税金及附加", "3", "",  45230.00,    90460.00],
    ["销售费用", "4",  "",   312450.80,   625901.60],
    ["管理费用", "5",  "",   198760.50,   401521.00],
    ["研发费用", "6",  "",   85000.00,    170000.00],
    ["财务费用", "7",  "",   23410.30,    47820.60],
    # gap rows (no 行次 8-13 in our template map)
    ["加：公允价值变动收益", "8",  "", 0, 0],
    ["投资收益", "9",  "",   5200.00,    10400.00],
    ["其中：对联营企业投资收益", "10", "", 0, 0],
    ["净敞口套期收益", "11", "", 0, 0],
    ["汇兑收益", "12", "", 0, 0],
    ["资产处置收益", "13", "", 0, 0],
    ["其他收益", "14", "",  12500.00,    25000.00],
    # more gaps
    ['营业利润（亏损以"-"号填列）', "15", "", 0, 0],  # formula row in template
    ["加：营业外收入", "21", "", 8800.00,   17600.00],
    ["减：营业外支出", "22", "", 3200.00,    6400.00],
]

import xlwt
wb_erp = xlwt.Workbook(encoding='utf-8')
ws_erp = wb_erp.add_sheet('利润表')
for row_i, row_data in enumerate(erp_data):
    for col_i, val in enumerate(row_data):
        ws_erp.write(row_i, col_i, val)
erp_path = WORKSPACE / "erp_exports" / "2024Q1" / "erp_profit_2024Q1.xls"
wb_erp.save(str(erp_path))
print(f"Created ERP file: {erp_path}")

# ─── Build the official 利润表 template (.xlsx) with formulas ────────────────
# We build the xlsx manually as a zip with crafted XML to ensure
# formula cells, style attributes, and calcChain.xml are present.

import zipfile, io

# Minimal but realistic [Content_Types].xml
content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
  <Override PartName="/xl/calcChain.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.calcChain+xml"/>
</Types>"""

rels_root = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

xl_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/calcChain" Target="calcChain.xml"/>
</Relationships>"""

workbook_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="利润表" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>"""

# Shared strings: labels for columns A-C
shared_strings_list = [
    "项目",           # 0
    "行次",           # 1
    "附注",           # 2
    "本期金额",       # 3
    "本年累计金额",   # 4
    "营业收入",       # 5
    "营业成本",       # 6
    "税金及附加",     # 7
    "销售费用",       # 8
    "管理费用",       # 9
    "研发费用",       # 10
    "财务费用",       # 11
    "其他收益",       # 12
    "营业利润",       # 13
    "加：营业外收入", # 14
    "减：营业外支出", # 15
    "利润总额",       # 16
    "减：所得税费用", # 17
    "净利润",         # 18
    "利润表",         # 19  (title)
    "公司名称：测试科技有限公司", # 20
    "单位：人民币元", # 21
]

ss_items = "\n".join(f'  <si><t>{s}</t></si>' for s in shared_strings_list)
shared_strings_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="{len(shared_strings_list)}" uniqueCount="{len(shared_strings_list)}">
{ss_items}
</sst>"""

# Styles: we define a few style indices to test s= preservation
styles_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="3">
    <font><sz val="11"/><name val="Calibri"/></font>
    <font><sz val="12"/><b/><name val="Calibri"/></font>
    <font><sz val="11"/><color rgb="FF0070C0"/><name val="Calibri"/></font>
  </fonts>
  <fills count="3">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFDDEBF7"/></patternFill></fill>
  </fills>
  <borders count="2">
    <border><left/><right/><top/><bottom/><diagonal/></border>
    <border>
      <left style="thin"><color rgb="FF000000"/></left>
      <right style="thin"><color rgb="FF000000"/></right>
      <top style="thin"><color rgb="FF000000"/></top>
      <bottom style="thin"><color rgb="FF000000"/></bottom>
      <diagonal/>
    </border>
  </borders>
  <cellStyleXfs count="1">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
  </cellStyleXfs>
  <cellXfs count="6">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0"><alignment horizontal="center"/></xf>
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0"/>
    <xf numFmtId="2" fontId="0" fillId="0" borderId="1" xfId="0"/>
    <xf numFmtId="2" fontId="0" fillId="2" borderId="1" xfId="0"/>
    <xf numFmtId="2" fontId="2" fillId="2" borderId="1" xfId="0"/>
  </cellXfs>
</styleSheet>"""

# calcChain.xml — references to formula cells (must be deleted by agent)
calc_chain_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<calcChain xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <c r="D21" i="1"/>
  <c r="E21" i="1"/>
  <c r="D30" i="1"/>
  <c r="E30" i="1"/>
  <c r="D32" i="1"/>
  <c r="E32" i="1"/>
</calcChain>"""

# Sheet1: 利润表 template
# Layout:
#  Row 1: title
#  Row 2: company name  
#  Row 3: unit
#  Row 4: blank
#  Row 5: column headers
#  Row 6: blank separator
#  Row 7-13: data rows (营业收入..财务费用) — D col=本期, E col=本年累计
#  Row 14-20: more items
#  Row 21: 营业利润 — FORMULA row: D21=ROUND(D7-D8-D9-D10-D11-D12-D13+D14+D15+D16+D17+D18+D19+D20,2)
#  ...
#  Row 28: 营业外收入
#  Row 29: 营业外支出
#  Row 30: 利润总额 — FORMULA: D30=ROUND(D21+D28-D29,2)
#  Row 31: 所得税费用
#  Row 32: 净利润 — FORMULA: D32=ROUND(D30-D31,2)

# s=1 → bold centered (title/header)
# s=2 → text with border
# s=3 → number with border
# s=4 → number with blue bg + border (formula cells)
# s=5 → number blue font + blue bg (total cells)

sheet_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>
    <row r="1">
      <c r="A1" s="1" t="s"><v>19</v></c>
    </row>
    <row r="2">
      <c r="A2" s="2" t="s"><v>20</v></c>
    </row>
    <row r="3">
      <c r="A3" s="2" t="s"><v>21</v></c>
    </row>
    <row r="5">
      <c r="A5" s="1" t="s"><v>0</v></c>
      <c r="B5" s="1" t="s"><v>1</v></c>
      <c r="C5" s="1" t="s"><v>2</v></c>
      <c r="D5" s="1" t="s"><v>3</v></c>
      <c r="E5" s="1" t="s"><v>4</v></c>
    </row>
    <row r="7">
      <c r="A7" s="2" t="s"><v>5</v></c>
      <c r="B7" s="2"><v>1</v></c>
      <c r="D7" s="3"><v>0</v></c>
      <c r="E7" s="3"><v>0</v></c>
    </row>
    <row r="8">
      <c r="A8" s="2" t="s"><v>6</v></c>
      <c r="B8" s="2"><v>2</v></c>
      <c r="D8" s="3"><v>0</v></c>
      <c r="E8" s="3"><v>0</v></c>
    </row>
    <row r="9">
      <c r="A9" s="2" t="s"><v>7</v></c>
      <c r="B9" s="2"><v>3</v></c>
      <c r="D9" s="3"><v>0</v></c>
      <c r="E9" s="3"><v>0</v></c>
    </row>
    <row r="10">
      <c r="A10" s="2" t="s"><v>8</v></c>
      <c r="B10" s="2"><v>4</v></c>
      <c r="D10" s="3"><v>0</v></c>
      <c r="E10" s="3"><v>0</v></c>
    </row>
    <row r="11">
      <c r="A11" s="2" t="s"><v>9</v></c>
      <c r="B11" s="2"><v>5</v></c>
      <c r="D11" s="3"><v>0</v></c>
      <c r="E11" s="3"><v>0</v></c>
    </row>
    <row r="12">
      <c r="A12" s="2" t="s"><v>10</v></c>
      <c r="B12" s="2"><v>6</v></c>
      <c r="D12" s="3"><v>0</v></c>
      <c r="E12" s="3"><v>0</v></c>
    </row>
    <row r="13">
      <c r="A13" s="2" t="s"><v>11</v></c>
      <c r="B13" s="2"><v>7</v></c>
      <c r="D13" s="3"><v>0</v></c>
      <c r="E13" s="3"><v>0</v></c>
    </row>
    <row r="20">
      <c r="A20" s="2" t="s"><v>12</v></c>
      <c r="B20" s="2"><v>14</v></c>
      <c r="D20" s="3"><v>0</v></c>
      <c r="E20" s="3"><v>0</v></c>
    </row>
    <row r="21">
      <c r="A21" s="4" t="s"><v>13</v></c>
      <c r="B21" s="4"><v>15</v></c>
      <c r="D21" s="4">
        <f>ROUND(D7-D8-D9-D10-D11-D12-D13+D20,2)</f>
        <v>0</v>
      </c>
      <c r="E21" s="4">
        <f>ROUND(E7-E8-E9-E10-E11-E12-E13+E20,2)</f>
        <v>0</v>
      </c>
    </row>
    <row r="28">
      <c r="A28" s="2" t="s"><v>14</v></c>
      <c r="B28" s="2"><v>21</v></c>
      <c r="D28" s="3"><v>0</v></c>
      <c r="E28" s="3"><v>0</v></c>
    </row>
    <row r="29">
      <c r="A29" s="2" t="s"><v>15</v></c>
      <c r="B29" s="2"><v>22</v></c>
      <c r="D29" s="3"><v>0</v></c>
      <c r="E29" s="3"><v>0</v></c>
    </row>
    <row r="30">
      <c r="A30" s="4" t="s"><v>16</v></c>
      <c r="B30" s="4"><v>23</v></c>
      <c r="D30" s="4">
        <f>ROUND(D21+D28-D29,2)</f>
        <v>0</v>
      </c>
      <c r="E30" s="4">
        <f>ROUND(E21+E28-E29,2)</f>
        <v>0</v>
      </c>
    </row>
    <row r="31">
      <c r="A31" s="2" t="s"><v>17</v></c>
      <c r="B31" s="2"><v>24</v></c>
      <c r="D31" s="3"><v>0</v></c>
      <c r="E31" s="3"><v>0</v></c>
    </row>
    <row r="32">
      <c r="A32" s="5" t="s"><v>18</v></c>
      <c r="B32" s="5"><v>25</v></c>
      <c r="D32" s="5">
        <f>ROUND(D30-D31,2)</f>
        <v>0</v>
      </c>
      <c r="E32" s="5">
        <f>ROUND(E30-E31,2)</f>
        <v>0</v>
      </c>
    </row>
  </sheetData>
</worksheet>"""

template_path = WORKSPACE / "templates" / "official" / "profit_template_2024.xlsx"
with zipfile.ZipFile(str(template_path), 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("[Content_Types].xml", content_types)
    zf.writestr("_rels/.rels", rels_root)
    zf.writestr("xl/workbook.xml", workbook_xml)
    zf.writestr("xl/_rels/workbook.xml.rels", xl_rels)
    zf.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    zf.writestr("xl/sharedStrings.xml", shared_strings_xml)
    zf.writestr("xl/styles.xml", styles_xml)
    zf.writestr("xl/calcChain.xml", calc_chain_xml)

print(f"Created template: {template_path}")

# ─── Additional distractor files ──────────────────────────────────────────────
(WORKSPACE / "erp_exports" / "2024Q1" / "erp_balance_2024Q1.xls").write_text(
    "FAKE BALANCE SHEET XLS - NOT NEEDED FOR THIS TASK"
)
(WORKSPACE / "erp_exports" / "2024Q1" / "erp_cashflow_2024Q1.xls").write_text(
    "FAKE CASHFLOW XLS - NOT NEEDED FOR THIS TASK"
)
(WORKSPACE / "output" / ".gitkeep").write_text("")
(WORKSPACE / "templates" / "official" / "balance_template_2024.xlsx").write_text("FAKE BINARY")
(WORKSPACE / "templates" / "official" / "cashflow_template_2024.xlsx").write_text("FAKE BINARY")

print("Workspace setup complete.")
print("Files created:")
for f in sorted(WORKSPACE.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(WORKSPACE)}")