#!/usr/bin/env python3
"""
Generate the sandbox workspace for the office-hub task.
Creates the proprietary scripts with specific interfaces,
messy input data, and distractor files.
"""

import os
import random
import json
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "skills/_core",
    "skills/office-hub",
    "data/raw",
    "data/processed",
    "reports/archive",
    "reports/drafts",
    "logs",
    "config",
    "templates",
    "tmp",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── THE PROPRIETARY SCRIPTS (already exist in workspace) ────────────────────

# create_excel.py  — proprietary script with specific CLI interface
create_excel_py = '''\
#!/usr/bin/env python3
"""
Office Hub - Excel Report Generator
Usage:
    python3 create_excel.py --input <csv_file> --output <xlsx_file> [--sheet-name <name>] [--add-summary]

Flags:
    --input       Path to the input CSV file (required)
    --output      Path to the output Excel file (required)
    --sheet-name  Name of the primary data sheet (default: "Data")
    --add-summary If present, adds a "Summary" sheet with aggregate statistics

Output contract:
    The generated Excel file ALWAYS contains a hidden sheet named "_meta" with:
        A1 = "generator"   B1 = "office-hub-v3"
        A2 = "script"      B2 = "create_excel.py"
        A3 = "timestamp"   B3 = <ISO timestamp>
    The data sheet has a bold header row (row 1) with fill color FFD700 (gold).
    If --add-summary is given, a "Summary" sheet is added with:
        A1 = "Total Rows"   B1 = <count>
        A2 = "Columns"      B2 = <comma-separated column names>
        A3 = "Numeric Cols" B3 = <count of numeric columns>
        A4 = "Sum Revenue"  B4 = <sum of "revenue" column if present, else 0>
"""

import argparse
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
except ImportError:
    print("ERROR: openpyxl not installed", file=sys.stderr)
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--sheet-name", default="Data")
    parser.add_argument("--add-summary", action="store_true")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Read CSV
    with open(input_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    wb = openpyxl.Workbook()

    # ── Data sheet ──────────────────────────────────────────────────────────
    ws_data = wb.active
    ws_data.title = args.sheet_name

    gold_fill = PatternFill(start_color="FFD700", end_color="FFD700", fill_type="solid")
    bold_font = Font(bold=True, size=11)

    # Header row
    for col_idx, col_name in enumerate(fieldnames, start=1):
        cell = ws_data.cell(row=1, column=col_idx, value=col_name)
        cell.font = bold_font
        cell.fill = gold_fill
        cell.alignment = Alignment(horizontal="center")

    # Data rows — attempt numeric conversion
    for row_idx, row in enumerate(rows, start=2):
        for col_idx, col_name in enumerate(fieldnames, start=1):
            raw = row.get(col_name, "")
            try:
                val = float(raw) if "." in str(raw) else int(raw)
            except (ValueError, TypeError):
                val = raw
            ws_data.cell(row=row_idx, column=col_idx, value=val)

    # Auto-width columns
    for col_idx, col_name in enumerate(fieldnames, start=1):
        col_letter = get_column_letter(col_idx)
        ws_data.column_dimensions[col_letter].width = max(len(col_name) + 4, 12)

    # ── Summary sheet ────────────────────────────────────────────────────────
    if args.add_summary:
        ws_sum = wb.create_sheet("Summary")
        numeric_cols = 0
        revenue_sum = 0.0
        for col_name in fieldnames:
            vals = []
            for row in rows:
                raw = row.get(col_name, "")
                try:
                    v = float(raw)
                    vals.append(v)
                except (ValueError, TypeError):
                    pass
            if vals:
                numeric_cols += 1
            if col_name.lower() == "revenue":
                revenue_sum = sum(vals)

        ws_sum["A1"] = "Total Rows"
        ws_sum["B1"] = len(rows)
        ws_sum["A2"] = "Columns"
        ws_sum["B2"] = ",".join(fieldnames)
        ws_sum["A3"] = "Numeric Cols"
        ws_sum["B3"] = numeric_cols
        ws_sum["A4"] = "Sum Revenue"
        ws_sum["B4"] = round(revenue_sum, 2)

        # Bold the labels
        for row_num in range(1, 5):
            ws_sum.cell(row=row_num, column=1).font = Font(bold=True)

    # ── _meta hidden sheet ───────────────────────────────────────────────────
    ws_meta = wb.create_sheet("_meta")
    ws_meta.sheet_state = "hidden"
    ws_meta["A1"] = "generator"
    ws_meta["B1"] = "office-hub-v3"
    ws_meta["A2"] = "script"
    ws_meta["B2"] = "create_excel.py"
    ws_meta["A3"] = "timestamp"
    ws_meta["B3"] = datetime.now(timezone.utc).isoformat()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    print(f"[create_excel.py] Saved: {output_path}")

if __name__ == "__main__":
    main()
'''

# create_word.py — proprietary script with specific CLI interface
create_word_py = '''\
#!/usr/bin/env python3
"""
Office Hub - Word Report Generator
Usage:
    python3 create_word.py --input <xlsx_file> --output <docx_file>
                           [--title <report_title>]
                           [--read-sheet <sheet_name>]
                           [--include-summary]

Flags:
    --input          Path to the source Excel file (required)
    --output         Path to the output Word document (required)
    --title          Document title heading (default: "Report")
    --read-sheet     Which sheet to read data from (default: "Data")
    --include-summary If present, reads the "Summary" sheet and appends
                      a "Key Statistics" section to the document

Output contract:
    The Word document ALWAYS contains:
        1. A Title paragraph (Heading 1 style) using the --title value
        2. A "Generated by office-hub-v3" paragraph in Italic + Gray color (969696)
           immediately after the title
        3. A table rendering the data from --read-sheet (header row shaded)
        4. If --include-summary: a "Key Statistics" Heading 2 section
           followed by bullet-list paragraphs for each Summary row
    The document properties:
        core_properties.author = "office-hub-v3"
        core_properties.subject = "office-hub-automated-report"
"""

import argparse
import sys
from pathlib import Path

try:
    import openpyxl
    from docx import Document
    from docx.shared import Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
except ImportError as e:
    print(f"ERROR: missing dependency: {e}", file=sys.stderr)
    sys.exit(1)

def shade_row(row, hex_color="D3D3D3"):
    for cell in row.cells:
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), hex_color)
        tcPr.append(shd)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--title", default="Report")
    parser.add_argument("--read-sheet", default="Data")
    parser.add_argument("--include-summary", action="store_true")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    wb = openpyxl.load_workbook(input_path)

    if args.read_sheet not in wb.sheetnames:
        print(f"ERROR: sheet not found: {args.read_sheet}", file=sys.stderr)
        print(f"Available sheets: {wb.sheetnames}", file=sys.stderr)
        sys.exit(1)

    ws = wb[args.read_sheet]
    all_rows = list(ws.iter_rows(values_only=True))

    doc = Document()

    # ── Title ──────────────────────────────────────────────────────────────
    title_para = doc.add_heading(args.title, level=1)
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # ── Subtitle / attribution ─────────────────────────────────────────────
    attr_para = doc.add_paragraph()
    attr_run = attr_para.add_run("Generated by office-hub-v3")
    attr_run.italic = True
    attr_run.font.color.rgb = RGBColor(0x96, 0x96, 0x96)
    attr_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()  # spacer

    # ── Data table ─────────────────────────────────────────────────────────
    if len(all_rows) > 0:
        num_cols = max(len(r) for r in all_rows)
        table = doc.add_table(rows=len(all_rows), cols=num_cols)
        table.style = "Table Grid"
        for r_idx, row_data in enumerate(all_rows):
            for c_idx, val in enumerate(row_data):
                cell = table.cell(r_idx, c_idx)
                cell.text = str(val) if val is not None else ""
                if r_idx == 0:
                    run = cell.paragraphs[0].runs
                    if run:
                        run[0].bold = True
        # Shade header row
        if len(all_rows) > 0:
            shade_row(table.rows[0])

    # ── Summary section ────────────────────────────────────────────────────
    if args.include_summary:
        if "Summary" in wb.sheetnames:
            ws_sum = wb["Summary"]
            doc.add_paragraph()
            doc.add_heading("Key Statistics", level=2)
            for row in ws_sum.iter_rows(values_only=True):
                if row[0] is not None:
                    label = str(row[0])
                    value = str(row[1]) if len(row) > 1 and row[1] is not None else ""
                    p = doc.add_paragraph(style="List Bullet")
                    run_label = p.add_run(f"{label}: ")
                    run_label.bold = True
                    p.add_run(value)
        else:
            print("WARNING: --include-summary specified but no Summary sheet found", file=sys.stderr)

    # ── Document properties ────────────────────────────────────────────────
    core = doc.core_properties
    core.author = "office-hub-v3"
    core.subject = "office-hub-automated-report"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
    print(f"[create_word.py] Saved: {output_path}")

if __name__ == "__main__":
    main()
'''

# ods.py — Office Document Specialist Suite (utility wrapper)
ods_py = '''\
#!/usr/bin/env python3
"""
Office Hub - Office Document Specialist Suite (ods.py)
A utility wrapper for inspecting and validating office documents.

Usage:
    python3 ods.py inspect --file <path>        # Print metadata of an Office file
    python3 ods.py validate --file <path>        # Validate office-hub-v3 contract compliance
    python3 ods.py list-sheets --file <xlsx>     # List sheets in an Excel file
"""

import argparse
import sys
from pathlib import Path

def inspect_file(filepath):
    p = Path(filepath)
    if not p.exists():
        print(f"ERROR: file not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    ext = p.suffix.lower()
    if ext == ".xlsx":
        import openpyxl
        wb = openpyxl.load_workbook(filepath, read_only=False)
        print(f"Sheets: {wb.sheetnames}")
        for name in wb.sheetnames:
            ws = wb[name]
            print(f"  [{name}] rows={ws.max_row} cols={ws.max_column}")
    elif ext == ".docx":
        from docx import Document
        doc = Document(filepath)
        cp = doc.core_properties
        print(f"Author: {cp.author}")
        print(f"Subject: {cp.subject}")
        print(f"Paragraphs: {len(doc.paragraphs)}")
        print(f"Tables: {len(doc.tables)}")
    else:
        print(f"Unsupported extension: {ext}")

def validate_file(filepath):
    p = Path(filepath)
    if not p.exists():
        print(f"ERROR: file not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    ext = p.suffix.lower()
    errors = []
    if ext == ".xlsx":
        import openpyxl
        wb = openpyxl.load_workbook(filepath)
        if "_meta" not in wb.sheetnames:
            errors.append("Missing _meta sheet")
        else:
            ws_meta = wb["_meta"]
            if ws_meta["B1"].value != "office-hub-v3":
                errors.append(f"_meta B1 expected office-hub-v3, got {ws_meta[\'B1\'].value}")
            if ws_meta["B2"].value != "create_excel.py":
                errors.append(f"_meta B2 expected create_excel.py, got {ws_meta[\'B2\'].value}")
    elif ext == ".docx":
        from docx import Document
        doc = Document(filepath)
        cp = doc.core_properties
        if cp.author != "office-hub-v3":
            errors.append(f"author expected office-hub-v3, got {cp.author}")
        if cp.subject != "office-hub-automated-report":
            errors.append(f"subject expected office-hub-automated-report, got {cp.subject}")
    if errors:
        print("INVALID:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("VALID: office-hub-v3 contract satisfied")

def list_sheets(filepath):
    import openpyxl
    wb = openpyxl.load_workbook(filepath)
    for name in wb.sheetnames:
        print(name)

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    p_inspect = sub.add_parser("inspect")
    p_inspect.add_argument("--file", required=True)
    p_validate = sub.add_parser("validate")
    p_validate.add_argument("--file", required=True)
    p_list = sub.add_parser("list-sheets")
    p_list.add_argument("--file", required=True)
    args = parser.parse_args()
    if args.cmd == "inspect":
        inspect_file(args.file)
    elif args.cmd == "validate":
        validate_file(args.file)
    elif args.cmd == "list-sheets":
        list_sheets(args.file)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
'''

# scheduler.py
scheduler_py = '''\
#!/usr/bin/env python3
"""Office Hub - Task Scheduler stub"""
import sys
print("scheduler: registered office-hub tasks (stub)")
'''

# autonomous.py
autonomous_py = '''\
#!/usr/bin/env python3
"""Office Hub - Autonomous core stub"""
import sys
print(f"autonomous: registered {sys.argv[2] if len(sys.argv)>2 else \'unknown\'} for {sys.argv[3] if len(sys.argv)>3 else \'unknown\'}")
'''

# Write the scripts
(WORKSPACE / "create_excel.py").write_text(create_excel_py)
(WORKSPACE / "create_word.py").write_text(create_word_py)
(WORKSPACE / "ods.py").write_text(ods_py)
(WORKSPACE / "scheduler.py").write_text(scheduler_py)
(WORKSPACE / "skills/_core/autonomous.py").write_text(autonomous_py)

# ── MESSY INPUT DATA ────────────────────────────────────────────────────────
# A realistic but messy CSV with mixed types, extra whitespace, BOM, inconsistent casing

csv_content = """\ufeffproduct_id,product_name,region,quarter,units_sold,unit_price,revenue,rep_name
P001,PharmaClear 500mg,North,Q1 2024,1200,45.50,54600.00,Alice Zhang
P002,VitaBoost Pro,South,Q1 2024,850,78.00,66300.00,Bob Chen
P003, CardioShield 10mg ,East,Q1 2024,2300,32.25,74175.00,Carol Wu
P004,NeuroCalm XR,West,Q1 2024,410,125.00,51250.00,David Li
P005,PharmaClear 500mg,East,Q1 2024,1750,45.50,79625.00,Emily Zhou
P006,DiabeStop Plus,North,Q1 2024,990,89.75,88852.50,Alice Zhang
P007,VitaBoost Pro,West,Q1 2024,620,78.00,48360.00,Frank Xu
P008,OsteoGuard Forte,South,Q1 2024,340,156.00,53040.00,Grace Mao
P009,CardioShield 10mg,North,Q1 2024,1890,32.25,60952.50,Bob Chen
P010,NeuroCalm XR,East,Q1 2024,275,125.00,34375.00,Carol Wu
P011,PharmaClear 500mg,South,Q1 2024,1100,45.50,50050.00,David Li
P012,DiabeStop Plus,West,Q1 2024,730,89.75,65517.50,Emily Zhou
P013,OsteoGuard Forte,North,Q1 2024,460,156.00,71760.00,Frank Xu
P014,VitaBoost Pro,East,Q1 2024,910,78.00,70980.00,Grace Mao
P015,CardioShield 10mg,West,Q1 2024,1560,32.25,50310.00,Alice Zhang
"""

(WORKSPACE / "data/raw/q1_2024_sales_raw.csv").write_text(csv_content, encoding="utf-8")

# ── DISTRACTOR FILES ─────────────────────────────────────────────────────────

# Old report template (distractor)
(WORKSPACE / "templates/old_report_template.txt").write_text(
    "LEGACY TEMPLATE - DO NOT USE\nThis template is deprecated as of 2023-06."
)

# Fake README that gives wrong instructions
(WORKSPACE / "reports/drafts/DRAFT_NOTES.txt").write_text(
    "Draft notes: sales data needs review. Units seem high for West region."
)

# Stale processed data (distractor)
old_data = "product_id,revenue\nP001,50000\nP002,60000\n"
(WORKSPACE / "data/processed/q4_2023_final.csv").write_text(old_data)

# Random config files
(WORKSPACE / "config/office_settings.json").write_text(json.dumps({
    "default_font": "Calibri",
    "default_size": 11,
    "theme": "office2016",
    "deprecated_script": "excel_gen_v1.py"
}, indent=2))

(WORKSPACE / "config/regions.json").write_text(json.dumps({
    "regions": ["North", "South", "East", "West"],
    "hq": "Shanghai"
}, indent=2))

# Log files (distractor)
(WORKSPACE / "logs/app.log").write_text(
    "2024-01-15 10:22:11 INFO  office-hub started\n"
    "2024-01-15 10:22:12 INFO  No scheduled tasks found\n"
    "2024-01-22 09:01:03 WARN  CSV parser: skipped empty line\n"
)

(WORKSPACE / "logs/error.log").write_text(
    "2024-01-10 08:55:02 ERROR  create_excel.py: output directory not found\n"
    "2024-01-10 08:55:03 INFO   Retried with mkdir -p, success\n"
)

# Archive report (distractor - wrong format, not the target)
(WORKSPACE / "reports/archive/q4_2023_summary.txt").write_text(
    "Q4 2023 Sales Summary\nTotal Revenue: 4,200,000\nTop Product: VitaBoost Pro\n"
)

# Fake Python scripts that look similar but are NOT the right ones
(WORKSPACE / "data/raw/quick_excel.py").write_text(
    "# Quick script - NOT part of office-hub\nimport openpyxl\n# stub\n"
)

(WORKSPACE / "tmp/scratch.py").write_text(
    "# Scratch file\n# trying to generate report manually\n# abandoned\n"
)

# skills metadata
(WORKSPACE / "skills/office-hub/metadata.json").write_text(json.dumps({
    "name": "office-hub",
    "version": "3.0.0",
    "author": "小绿瓶",
    "scripts": ["create_excel.py", "create_word.py", "create_ppt.py", "ods.py", "scheduler.py"]
}, indent=2))

print("Workspace generated successfully.")
print(f"Files created:")
for f in sorted(WORKSPACE.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(WORKSPACE)}")