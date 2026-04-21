import sys
import os
import json
import re
import csv
from pathlib import Path

def case_insensitive_search(text, keywords):
    text_l = text.lower()
    return any(keyword.lower() in text_l for keyword in keywords)

def safe_read_text(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception:
        return ''

def check_filename_pattern(fname, date, vendor, desc, ext):
    base = os.path.basename(fname)
    base_no_ext = base[:-len(ext)] if base.lower().endswith(ext.lower()) else base
    bne = base_no_ext.lower()
    
    if not re.search(r'\d{4}-\d{2}-\d{2}', bne):
        return False
    if vendor.lower() not in bne:
        return False

    # 【修复1】：去除强制要求 'invoice' 或 'receipt' 的死板校验，兼容 Claude 填入真实发票号
    
    desc_words = [w.lower() for w in re.findall(r'\w+', desc)]
    if not any(word in bne for word in desc_words):
        return False
    return True

def locate_renamed_files(base_dir):
    renamed_files = []
    invoices_dir = Path(base_dir) / 'Invoices'
    if not invoices_dir.exists():
        return []
    for root, dirs, files in os.walk(invoices_dir):
        for file in files:
            if file.lower().endswith(('.pdf','.jpg','.png')):
                renamed_files.append(Path(root) / file)
    return renamed_files

def parse_csv_summary(csv_path):
    data = []
    if not os.path.exists(csv_path):
        return data
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def main():
    if len(sys.argv) < 2:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name':'args','passed': False,'detail':'Missing workspace directory argument'}]}))
        return

    workspace = sys.argv[1]
    checks = []

    # 1. Check Invoices dir exists
    invoices_dir = Path(workspace) / 'Invoices'
    invoices_exists = invoices_dir.exists() and invoices_dir.is_dir()
    checks.append({'name': 'Invoices directory exists', 'passed': invoices_exists, 'detail': f'Invoices dir path: {invoices_dir} exists={invoices_exists}'})

    # 2. Check renamed files exist
    renamed_files = locate_renamed_files(workspace)
    renamed_files_count = len(renamed_files)
    checks.append({'name': 'Renamed files exist', 'passed': renamed_files_count > 0, 'detail': f'Found {renamed_files_count} renamed invoice files'})

    # 3. Validate filename patterns in renamed files
    valid_pattern_count = 0
    vendors_expected = {'Adobe', 'Staples', 'ConsultCorp', 'Microsoft', 'Amazon'}
    expected_categories = {'Software', 'Office Supplies', 'Travel', 'Professional Services'}
    categories_found = set()
    vendors_found = set()
    years_found = set()

    for fpath in renamed_files:
        fname = fpath.name
        ext = fpath.suffix
        parts = fpath.parts
        
        year_dir = None
        category_dir = None
        vendor_dir = None
        for i, p in enumerate(parts):
            if p == 'Invoices' and i+3 < len(parts):
                year_dir = parts[i+1]
                category_dir = parts[i+2]
                vendor_dir = parts[i+3]
                break

        valid_year = re.match(r'^\d{4}$', year_dir or '') is not None
        category_ok = category_dir in expected_categories
        vendor_ok = vendor_dir in vendors_expected

        if valid_year: years_found.add(year_dir)
        if category_ok: categories_found.add(category_dir)
        if vendor_ok: vendors_found.add(vendor_dir)

        # 【修复2】：用通用正则抓取三段内容，不管中间是发票号还是 Invoice
        filename_ok = False
        m = re.match(r"^(\d{4}-\d{2}-\d{2})\s+(.*?)\s+-\s+(.*?)\s+-\s+(.+?)(?:\.\w+)?$", fname, re.IGNORECASE)
        if m:
            date_str = m.group(1).strip()
            vendor_str = m.group(2).strip()
            desc_str = m.group(4).replace('_', ' ').strip()
            filename_ok = check_filename_pattern(fname, date_str, vendor_str, desc_str, ext)

        if filename_ok and valid_year and category_ok and vendor_ok:
            valid_pattern_count += 1

    checks.append({'name': 'Correct filename pattern and folder structure',
                   'passed': valid_pattern_count >= 5,
                   'detail': f'{valid_pattern_count} files have valid filenames and folder locations'})

    # 4. Check Needs-Review folder
    needs_review_dir = invoices_dir / 'Needs-Review'
    needs_review_exists = needs_review_dir.exists() and any(needs_review_dir.iterdir())
    needs_review_files_count = len(list(needs_review_dir.glob('*')) if needs_review_exists else [])
    flagged_ok = needs_review_files_count >= 2
    checks.append({'name': 'Needs-Review folder flags missing data files',
                  'passed': flagged_ok,
                  'detail': f'Needs-Review folder exists={needs_review_exists} with {needs_review_files_count} files'})

    # 5. Check CSV file with correct columns and content
    # 【修复3】：把路径改回工作区根目录
    csv_path = Path(workspace) / 'invoice-summary.csv'
    csv_exists = csv_path.exists()

    csv_correct = False
    if csv_exists:
        rows = parse_csv_summary(csv_path)
        columns_expected = {'Date','Vendor','Invoice Number','Description','Amount','Category','File Path'}
        csv_cols = set(rows[0].keys()) if rows else set()
        cols_ok = columns_expected.issubset(csv_cols)

        entries_ok = sum(1 for r in rows if r.get('Date') and r.get('Vendor') and r.get('Amount')) >= 5
        paths_ok = all(r.get('File Path', '').startswith('Invoices/') or r.get('File Path', '').startswith('organized') for r in rows if r.get('File Path'))

        csv_correct = cols_ok and entries_ok and paths_ok

    checks.append({'name': 'CSV summary with correct columns and content',
                  'passed': csv_correct,
                  'detail': f'CSV exists={csv_exists}, columns ok={cols_ok if csv_exists else False}, entries ok={entries_ok if csv_exists else False}'})

    score = sum(1 for c in checks if c['passed']) / len(checks) if checks else 0.0
    passed = score == 1.0

    result = {
        'passed': passed,
        'score': score,
        'checks': checks
    }
    print(json.dumps(result))

if __name__ == '__main__':
    main()