#!/usr/bin/env python3
"""
Generates the sandbox workspace:
- Creates the read_file.py skill script at /skills/encrypted-file-reader/read_file.py
- Creates realistic corporate files: budget.xlsx, meeting_minutes.docx, access_log.csv
- Creates distractor files in a deeply nested structure
"""

import os
import sys
import zipfile
import io
import struct
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# 1.  Write the read_file.py skill script
# ─────────────────────────────────────────────
skill_dir = Path("/skills/encrypted-file-reader")
skill_dir.mkdir(parents=True, exist_ok=True)

read_file_py = skill_dir / "read_file.py"
read_file_py.write_text(r'''
import sys
import os
import zipfile
import re

def read_text_file(filepath):
    with open(filepath, 'rb') as f:
        raw = f.read()
    return raw.decode('utf-8')

def read_docx(filepath):
    texts = []
    with zipfile.ZipFile(filepath, 'r') as z:
        with z.open('word/document.xml') as f:
            xml = f.read().decode('utf-8')
    # Extract text from w:t tags
    matches = re.findall(r'<w:t[^>]*>(.*?)</w:t>', xml, re.DOTALL)
    return '\n'.join(matches)

def read_xlsx(filepath):
    texts = []
    with zipfile.ZipFile(filepath, 'r') as z:
        # Read shared strings
        shared_strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            with z.open('xl/sharedStrings.xml') as f:
                ss_xml = f.read().decode('utf-8')
            shared_strings = re.findall(r'<t[^>]*>(.*?)</t>', ss_xml, re.DOTALL)
        # Read sheet1
        with z.open('xl/worksheets/sheet1.xml') as f:
            sheet_xml = f.read().decode('utf-8')
    # Parse cells
    rows = {}
    for cell_match in re.finditer(r'<c r="([A-Z]+)(\d+)"([^>]*)>(.*?)</c>', sheet_xml, re.DOTALL):
        col_str, row_num, attrs, content = cell_match.groups()
        v_match = re.search(r'<v>(.*?)</v>', content)
        if not v_match:
            continue
        val = v_match.group(1)
        t_match = re.search(r't="([^"]*)"', attrs)
        if t_match and t_match.group(1) == 's':
            val = shared_strings[int(val)]
        row_num = int(row_num)
        if row_num not in rows:
            rows[row_num] = []
        rows[row_num].append(val)
    lines = []
    for rn in sorted(rows.keys()):
        lines.append('\t'.join(rows[rn]))
    return '\n'.join(lines)

def main():
    if len(sys.argv) < 2:
        print("Usage: read_file.py <filepath>", file=sys.stderr)
        sys.exit(1)
    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.docx':
        print(read_docx(filepath))
    elif ext == '.xlsx':
        print(read_xlsx(filepath))
    elif ext in ('.txt','.md','.markdown','.rst','.log','.csv','.tsv',
                 '.java','.py','.js','.ts','.jsx','.tsx','.c','.cpp',
                 '.h','.cs','.go','.rs','.rb','.php','.vue',
                 '.json','.xml','.yaml','.yml','.toml','.ini','.cfg',
                 '.properties','.gradle','.config','.env',
                 '.html','.htm','.css','.scss','.sass','.less',
                 '.sh','.bash','.bat','.cmd','.ps1','.sql'):
        print(read_text_file(filepath))
    else:
        print(f"Error: Unsupported file extension: {ext}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# ─────────────────────────────────────────────
# 2.  Helper: build a minimal but valid .xlsx
# ─────────────────────────────────────────────

def build_xlsx(rows_data):
    """
    rows_data: list of list of (value, is_string)
    Returns bytes of a valid .xlsx file.
    """
    # Build sharedStrings
    strings = []
    string_index = {}

    def get_str_idx(s):
        if s not in string_index:
            string_index[s] = len(strings)
            strings.append(s)
        return string_index[s]

    # Build sheet XML
    sheet_rows_xml = []
    for r_idx, row in enumerate(rows_data, start=1):
        cells_xml = []
        for c_idx, (val, is_str) in enumerate(row):
            col_letter = chr(ord('A') + c_idx)
            ref = f"{col_letter}{r_idx}"
            if is_str:
                si = get_str_idx(str(val))
                cells_xml.append(f'<c r="{ref}" t="s"><v>{si}</v></c>')
            else:
                cells_xml.append(f'<c r="{ref}"><v>{val}</v></c>')
        sheet_rows_xml.append(f'<row r="{r_idx}">{"".join(cells_xml)}</row>')

    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetData>' + ''.join(sheet_rows_xml) + '</sheetData>'
        '</worksheet>'
    )

    ss_items = ''.join(f'<si><t>{s}</t></si>' for s in strings)
    ss_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        f'count="{len(strings)}" uniqueCount="{len(strings)}">'
        f'{ss_items}</sst>'
    )

    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets>'
        '</workbook>'
    )

    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet1.xml"/>'
        '<Relationship Id="rId2" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" '
        'Target="sharedStrings.xml"/>'
        '</Relationships>'
    )

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '<Override PartName="/xl/sharedStrings.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
        '</Types>'
    )

    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/>'
        '</Relationships>'
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', content_types)
        zf.writestr('_rels/.rels', rels)
        zf.writestr('xl/workbook.xml', workbook_xml)
        zf.writestr('xl/_rels/workbook.xml.rels', workbook_rels)
        zf.writestr('xl/worksheets/sheet1.xml', sheet_xml)
        zf.writestr('xl/sharedStrings.xml', ss_xml)
    return buf.getvalue()


# ─────────────────────────────────────────────
# 3.  Helper: build a minimal but valid .docx
# ─────────────────────────────────────────────

def build_docx(paragraphs):
    """paragraphs: list of strings"""
    def para_xml(text):
        return (
            '<w:p>'
            '<w:r>'
            f'<w:t xml:space="preserve">{text}</w:t>'
            '</w:r>'
            '</w:p>'
        )

    body = ''.join(para_xml(p) for p in paragraphs)
    doc_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" '
        'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f'<w:body>{body}</w:body>'
        '</w:document>'
    )

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '</Types>'
    )

    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/>'
        '</Relationships>'
    )

    word_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '</Relationships>'
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', content_types)
        zf.writestr('_rels/.rels', rels)
        zf.writestr('word/document.xml', doc_xml)
        zf.writestr('word/_rels/document.xml.rels', word_rels)
    return buf.getvalue()


# ─────────────────────────────────────────────
# 4.  Create the three source data files
# ─────────────────────────────────────────────

data_dir = workspace / "corporate_data" / "Q3_2024"
data_dir.mkdir(parents=True, exist_ok=True)

# --- budget.xlsx ---
# Department | Allocated | Spent | Remaining
budget_rows = [
    [("Department", True), ("Allocated_USD", True), ("Spent_USD", True), ("Remaining_USD", True)],
    [("Engineering", True),  ("520000", False), ("387500", False), ("132500", False)],
    [("Marketing",   True),  ("210000", False), ("198000", False), ("12000",  False)],
    [("Operations",  True),  ("340000", False), ("301200", False), ("38800",  False)],
    [("HR",          True),  ("95000",  False), ("88400",  False), ("6600",   False)],
    [("Legal",       True),  ("150000", False), ("142300", False), ("7700",   False)],
]
(data_dir / "budget.xlsx").write_bytes(build_xlsx(budget_rows))

# --- meeting_minutes.docx ---
meeting_paragraphs = [
    "Q3 2024 Executive Strategy Meeting - Minutes",
    "Date: 2024-09-15",
    "Attendees: Alice Fontaine (CEO), Bob Marsh (CFO), Carol Linden (CTO), David Ochoa (COO)",
    "Action Items:",
    "1. Engineering team to finalize the Orion platform migration by 2024-10-31.",
    "2. Marketing to submit revised campaign budget proposal by 2024-09-30.",
    "3. Operations to reduce logistics overhead by 8% in Q4.",
    "4. HR to complete annual compliance training rollout by 2024-11-15.",
    "Key Decision: Board approved additional funding of 75000 USD for cybersecurity initiatives.",
    "Next Meeting: 2024-12-10",
]
(data_dir / "meeting_minutes.docx").write_bytes(build_docx(meeting_paragraphs))

# --- access_log.csv ---
access_log_lines = [
    "timestamp,user_id,resource,action,status",
    "2024-09-15T08:12:33Z,u1042,/finance/budget_report,READ,SUCCESS",
    "2024-09-15T08:45:01Z,u2019,/hr/payroll_data,READ,DENIED",
    "2024-09-15T09:03:17Z,u1042,/legal/contracts,READ,SUCCESS",
    "2024-09-15T09:30:55Z,u3307,/engineering/source_code,WRITE,SUCCESS",
    "2024-09-15T10:01:44Z,u2019,/finance/budget_report,READ,SUCCESS",
    "2024-09-15T10:15:22Z,u4481,/hr/payroll_data,READ,SUCCESS",
    "2024-09-15T11:00:09Z,u1042,/marketing/campaign_data,READ,DENIED",
    "2024-09-15T11:45:30Z,u3307,/engineering/deployment_config,WRITE,SUCCESS",
    "2024-09-15T12:30:00Z,u5512,/legal/contracts,READ,SUCCESS",
    "2024-09-15T13:10:17Z,u2019,/finance/budget_report,READ,SUCCESS",
]
(data_dir / "access_log.csv").write_text('\n'.join(access_log_lines), encoding='utf-8')

# ─────────────────────────────────────────────
# 5.  Distractor files (deeply nested)
# ─────────────────────────────────────────────

distractors = [
    ("archive/2023/Q4/old_budget_draft.txt",
     "This is an old draft from 2023 Q4. DO NOT USE.\nEngineering: 480000\nMarketing: 195000\n"),
    ("archive/2023/Q4/meeting_notes.txt",
     "Attendees: previous team\nDecision: postpone migration\n"),
    ("archive/2022/annual_report_summary.md",
     "# 2022 Annual Report\nTotal revenue: 12.4M USD\nExpenses: 9.8M USD\n"),
    ("internal/hr/headcount_2024.txt",
     "Engineering: 87\nMarketing: 34\nOperations: 56\nHR: 12\nLegal: 9\n"),
    ("internal/it/asset_inventory.csv",
     "asset_id,type,location\nA001,Laptop,NYC\nA002,Server,DAL\nA003,Monitor,CHI\n"),
    ("internal/legal/template_nda.txt",
     "NON-DISCLOSURE AGREEMENT TEMPLATE\n[PARTY A] and [PARTY B] agree to the following terms...\n"),
    ("internal/finance/prior_year_actuals.txt",
     "FY2023 Actuals\nEngineering: 495000\nMarketing: 202000\nOperations: 328000\n"),
    ("tmp/scratch_notes.txt",
     "TODO: reconcile Q2 variances\ncheck with Bob re: cybersecurity line item\n"),
    ("tmp/export_errors.log",
     "2024-09-14 ERROR: Export failed for report_id=4892\n2024-09-14 WARN: Retry 1 of 3\n"),
    ("config/reporting_schedule.yaml",
     "reports:\n  - name: quarterly_budget\n    schedule: '0 9 1 */3 *'\n  - name: access_audit\n    schedule: '0 6 * * 1'\n"),
    ("config/data_sources.json",
     '{"sources": [{"name": "ERP", "host": "erp.internal", "port": 5432}, '
     '{"name": "HRIS", "host": "hris.internal", "port": 3306}]}\n'),
    ("README_DO_NOT_USE.txt",
     "This workspace contains raw corporate data. Do not distribute.\n"),
]

for rel_path, content in distractors:
    full_path = workspace / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding='utf-8')

print("Workspace generated successfully.")
print(f"Source files:")
print(f"  {data_dir}/budget.xlsx")
print(f"  {data_dir}/meeting_minutes.docx")
print(f"  {data_dir}/access_log.csv")