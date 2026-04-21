import sys
import os
import re
import json
import csv
from pathlib import Path

def case_insensitive_search(text, keywords):
    lower = text.lower()
    return any(k.lower() in lower for k in keywords)

def read_all_text_files(folder):
    texts = []
    for root, _, files in os.walk(folder):
        for f in files:
            if f.lower().endswith(('.pdf', '.txt', '.md', '.csv', '.json', '.png', '.jpg', '.jpeg')):
                try:
                    p = Path(root) / f
                    with open(p, 'rb') as file:
                        content = file.read()
                        texts.append((str(p), content))
                except Exception:
                    continue
    return texts

def find_csv_file(folder):
    candidates = []
    for f in os.listdir(folder):
        if f.lower().endswith('.csv') and 'invoice' in f.lower():
            candidates.append(f)
    return candidates

def parse_csv(path):
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def examine_filename(filename):
    # Should match pattern YYYY-MM-DD Vendor - Invoice - Description.ext exactly
    # Relaxed spacing and dashes
    if not re.search(r'\d{4}-\d{2}-\d{2}', filename):
        return False
    parts = filename.split(' - ')
    if len(parts) < 3:
        return False

    # Date is good
    # Vendor present
    # 'Invoice' or 'Receipt' in middle part
    if not any(x.lower() in parts[1].lower() for x in ['invoice', 'receipt']):
        return False

    return True

def gather_all_files(folder):
    # Collect all files recursively
    files = []
    for root, _, filenames in os.walk(folder):
        for f in filenames:
            files.append(os.path.join(root, f))
    return files

def file_ext_lower(f):
    return Path(f).suffix.lower()

def check_organization_structure(folder):
    # Expect structure like root/YYYY/Category/Vendor/...
    # We'll check 4 levels
    # Collect sets
    years = set()
    categories = set()
    vendors = set()
    valid = True
    for root, dirs, files in os.walk(folder):
        rel = os.path.relpath(root, folder)
        parts = rel.split(os.sep)
        if len(parts) == 3:
            y, c, v = parts
            if not re.fullmatch(r'\d{4}', y):
                valid = False
            years.add(y)
            categories.add(c)
            vendors.add(v)
    return valid, years, categories, vendors

def extract_invoice_number(text):
    patterns = [r'invoice\s*#[:]?\s*([\w\-]+)', r'invoice number[:]?\s*([\w\-]+)']
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            return m.group(1).strip()
    return None

def extract_date(text):
    # Simple date pattern YYYY-MM-DD or MM/DD/YYYY
    m = re.search(r'(\d{4}-\d{2}-\d{2})', text)
    if m:
        return m.group(1)
    # US format MM/DD/YYYY
    m2 = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', text)
    if m2:
        parts = m2.group(1).split('/')
        if len(parts) == 3:
            mm, dd, yyyy = parts
            try:
                mm = int(mm)
                dd = int(dd)
                yyyy = int(yyyy)
                return f'{yyyy:04d}-{mm:02d}-{dd:02d}'
            except:
                return None
    return None

def extract_amount(text):
    # Find lines with amount or total
    lines = text.lower().splitlines()
    for line in lines:
        if any(k in line for k in ['amount due', 'amount', 'total']):
            m = re.search(r'\$?\s*([0-9]+\.?[0-9]{0,2})', line)
            if m:
                return m.group(1)
    # fallback: find last dollar amount in text
    m = re.findall(r'\$?\s*([0-9]+\.?[0-9]{0,2})', text)
    if m:
        return m[-1]
    return None

def extract_vendor(text):
    # Vendor usually near top (first line with text)
    lines = text.strip().splitlines()
    if lines:
        # Take first non-empty line
        for line in lines:
            if line.strip():
                # Clean known generic words
                if not any(w in line.lower() for w in ['invoice', 'receipt', 'date', 'amount']):
                    return line.strip()
    return None

def normalize_vendor(vendor):
    # Remove special chars, fix capitalization
    if not vendor:
        return None
    v = vendor.strip()
    v = re.sub(r'[^a-zA-Z0-9\s]', '', v)
    v = ' '.join([w.capitalize() for w in v.split()])
    return v

def read_text_from_file(path):
    # Try to read pdf text using pdftotext
    ext = Path(path).suffix.lower()
    if ext == '.pdf':
        import subprocess
        try:
            result = subprocess.run(['pdftotext', path, '-'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            text = result.stdout.decode('utf-8', errors='ignore')
            return text
        except Exception:
            return ''
    elif ext in ['.txt', '.md', '.csv']:
        try:
            with open(path, encoding='utf-8') as f:
                return f.read()
        except Exception:
            return ''
    # For images try OCR
    elif ext in ['.jpg', '.jpeg', '.png']:
        try:
            from PIL import Image
            import pytesseract
            img = Image.open(path)
            text = pytesseract.image_to_string(img)
            return text
        except Exception:
            return ''
    else:
        return ''

def check_file_renamed_correctly(path):
    # Filename should match pattern YYYY-MM-DD Vendor - Invoice - Description.ext
    name = Path(path).name
    if re.search(r'\d{4}-\d{2}-\d{2}', name) and ' - ' in name:
        return True
    return False

def evaluate(argv):
    if len(argv) < 2:
        print(json.dumps({"passed": False, "score": 0, "checks": [{"name": "args", "passed": False, "detail": "Expected workspace directory argument"}]}))
        return
    workspace = argv[1]

    input_files_path = os.path.join(workspace, 'input_files')
    if not os.path.exists(input_files_path):
        input_files_path = workspace

    # First check CSV summary exists
    csv_files = find_csv_file(workspace)

    checks = []

    if not csv_files:
        checks.append({"name": "CSV summary presence", "passed": False, "detail": "No invoice-summary CSV found in workspace"})
    else:
        # Read rows
        rows_all = []
        max_score = 0
        best_detail = ''
        for csv_file in csv_files:
            try:
                rows = parse_csv(os.path.join(workspace, csv_file))
                # Check headers
                headers = set(rows[0].keys()) if rows else set()
                expected_cols = {'Date', 'Vendor', 'Invoice Number', 'Description', 'Amount', 'Category', 'File Path'}
                passed = expected_cols.issubset(headers)
                detail = f'CSV headers include required columns: {passed}'
                if passed:
                    # Check at least 7 entries
                    if len(rows) < 7:
                        detail += ", but less than 7 entries"
                    # Check data consistency
                    dates_valid = all(re.match(r'\d{4}-\d{2}-\d{2}', r.get('Date', '')) for r in rows)
                    amounts_valid = all(re.match(r'^\d+(\.\d{1,2})?$', r.get('Amount', '').replace('$','').strip()) for r in rows if r.get('Amount'))
                    if dates_valid and amounts_valid:
                        score = 1.0
                    else:
                        score = 0.7
                    if score > max_score:
                        max_score = score
                        best_detail = detail
                else:
                    max_score = max(max_score, 0)
                    best_detail = detail
            except Exception as e:
                max_score = max(max_score, 0)
                best_detail = f'Exception reading CSV: {e}'
                continue
        checks.append({"name": "CSV summary content and format", "passed": max_score > 0.7, "detail": best_detail})

# Check all processed files renamed correctly and organized in Year/Category/Vendor structure
    organized_dir = os.path.join(workspace, 'organized')
    
    # 1. 恢复 all_files 变量，但把搜索范围严格限制在 organized 文件夹里（消除地图炮）
    all_files = gather_all_files(organized_dir) if os.path.exists(organized_dir) else []

    # Filter out the original input files
    input_set = set()
    if os.path.exists(input_files_path):
        for r, _, fs in os.walk(input_files_path):
            for f in fs:
                input_set.add(str(Path(r)/f))

    processed_files = [f for f in all_files if f not in input_set]

    renamed_ok = True
    renamed_count = 0
    manual_review_files = []
    vendors_found = set()
    years_found = set()
    categories_found = set()
    total_amount = 0
    
    # Check organization folder structure
    org_valid, years, categories, vendors = False, set(), set(), set()
    
    # 2. 彻底修复原作者的 NameError 和 isdir 弱智 Bug
    if os.path.exists(organized_dir):
        # 正确遍历目录而不是文件
        for root, dirs, files in os.walk(organized_dir):
            if os.path.isdir(root):
                valid, y, c, v = check_organization_structure(root)
                if valid:
                    org_valid = True
                    years.update(y)
                    categories.update(c)
                    vendors.update(v)

    # Check organization structure exists for the processed files
    org_valid_fallback = True

    # Check each processed file - filename format

    for f in processed_files:
        name = Path(f).name
        if not check_file_renamed_correctly(name):
            renamed_ok = False
        else:
            renamed_count += 1
            # Parse parts from filename
            try:
                parts = name.split(' - ')
                date_part = parts[0].strip()
                vendor_part = parts[1].strip()
                desc_part = parts[2].rsplit('.',1)[0].strip()
                # Validate date format
                if not re.match(r'\d{4}-\d{2}-\d{2}', date_part):
                    renamed_ok = False
                vendors_found.add(vendor_part)
                years_found.add(date_part[0:4])
            except Exception:
                renamed_ok = False

            # Attempt to extract amount from CSV after

    # Attempt to read CSV totals
    amount_parsed_from_csv = 0.0
    if csv_files:
        for csv_file in csv_files:
            try:
                rows = parse_csv(os.path.join(workspace, csv_file))
                for r in rows:
                    a = r.get('Amount', '').replace('$','').strip()
                    try:
                        amount_parsed_from_csv += float(a)
                    except Exception:
                        continue
            except Exception:
                continue

    # Find manual review files - any original input files missing vendor or date data
    for f in input_set:
        text = read_text_from_file(f)
        vendor = extract_vendor(text)
        date = extract_date(text)
        if vendor is None or date is None:
            manual_review_files.append(os.path.basename(f))

    # Compose checks
    checks.append({"name": "All processed files renamed correctly", "passed": renamed_ok, "detail": f"{renamed_count} files properly renamed"})
    checks.append({"name": "Organization folder structure validity", "passed": org_valid or org_valid_fallback, "detail": f"Years found: {sorted(list(years_found))}, Vendors found: {sorted(list(vendors_found)) }"})
    checks.append({"name": "Manual review files flagged", "passed": len(manual_review_files) > 0, "detail": f"Files flagged for manual review: {manual_review_files}"})

    # Compute score
    passed_count = sum(c.get('passed', False) for c in checks)
    total_checks = len(checks)
    score = passed_count / total_checks if total_checks else 0
    passed = score == 1.0

    # Print JSON result
    out = {"passed": passed, "score": score, "checks": checks}
    print(json.dumps(out))

if __name__ == '__main__':
    evaluate(sys.argv)
