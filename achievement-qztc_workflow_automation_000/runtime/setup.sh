#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace/temp/
chmod -R 755 /workspace/scripts/

echo "Verifying input files..."
ls -la /workspace/temp/
python3 -c "
from docx import Document
import xlrd

# Check XLS
wb = xlrd.open_workbook('/workspace/temp/数据可视化技术23级软工.xls')
ws = wb.sheet_by_index(0)
print(f'XLS rows: {ws.nrows}')  # should be 10 (1 header + 9 students)

# Check template
doc = Document('/workspace/temp/课程目标达成情况分析表-数据可视化-模版.docx')
print(f'Template tables: {len(doc.tables)}')  # should be 9
print(f'Table8 rows: {len(doc.tables[8].rows)}')  # should be 6
print(f'Table7 rows: {len(doc.tables[7].rows)}')  # should be 15
"
echo "Setup complete."