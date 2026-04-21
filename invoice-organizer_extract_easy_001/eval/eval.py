import sys
import os
import json
import csv
import re
from pathlib import Path

def find_invoice_summary_csv(workspace):
    for f in os.listdir(workspace):
        if f.lower() == 'invoice-summary.csv':
            return os.path.join(workspace, f)
    return None

def check_csv(file_path):
    required_columns = ['Date', 'Vendor', 'Invoice Number', 'Description', 'Amount', 'File Path']
    rows = []
    passed_headers = False
    try:
        with open(file_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = [h.strip().lower() for h in reader.fieldnames or []]
            # Check all required columns present case-insensitive
            missing = [c for c in required_columns if c.lower() not in headers]
            if missing:
                return (False, f'Missing columns in CSV: {missing}')
            passed_headers = True
            for r in reader:
                rows.append(r)
    except Exception as e:
        return (False, f'Error reading CSV: {e}')
    return (passed_headers, rows)

def find_vendor_folders(workspace):
    # Vendor folders must be directories in workspace or subdirs
    # According to prompt, renamed files must be inside vendor folders in root
    # So we expect vendor folders immediately inside workspace
    vendor_dirs = []
    for p in os.listdir(workspace):
        full = os.path.join(workspace, p)
        if os.path.isdir(full):
            vendor_dirs.append(p)
    return vendor_dirs

def norm_str(s):
    return s.strip().lower() if s else ''

def contains_invoice_parts(filename):
    # Filename format: YYYY-MM-DD Vendor - Invoice - Description.ext
    # We check date prefix, then 'Invoice' part, hyphens present
    # This should be case insensitive
    base = os.path.basename(filename)
    pattern = re.compile(r'\d{4}-\d{2}-\d{2} .+ - Invoice|Receipt - .+\..+', re.IGNORECASE)
    if pattern.search(base):
        return True
    # Looser fallback - check date at start and vendor name
    date_match = re.match(r'(\d{4}-\d{2}-\d{2})', base)
    if date_match and 'invoice' in base.lower():
        return True
    return False

def parse_date(date_str):
    # Accept various date formats to normalize to YYYY-MM-DD
    import dateutil.parser
    try:
        dt = dateutil.parser.parse(date_str, dayfirst=False)
        return dt.strftime('%Y-%m-%d')
    except Exception:
        return None

def extract_invoice_info_from_text(text):
    # Case-insensitive search for keys
    # Return dict with keys: Date, Vendor, Invoice Number, Description, Amount
    info = {'Date': None, 'Vendor': None, 'Invoice Number': '', 'Description': None, 'Amount': None}

    lines = text.splitlines()

    # Heuristic: vendor is often in first few lines
    for i in range(min(5, len(lines))):
        line = lines[i].strip()
        if line:
            info['Vendor'] = line
            break
    # Patterns
    date_patterns = [r'invoice date[:\s]*([\w\d\-/,. ]+)', r'date[:\s]*([\w\d\-/,. ]+)', r'issued[:\s]*([\w\d\-/,. ]+)']
    invoice_number_patterns = [r'invoice number[:#\s]*([\w\d-]+)', r'invoice #[:\s]*([\w\d-]+)']
    description_patterns = [r'description[:\s]*(.+)', r'service[:\s]*(.+)', r'product[:\s]*(.+)']
    amount_patterns = [r'amount due[:\s]*\$?([\d.,]+)', r'total[:\s]*\$?([\d.,]+)', r'amount[:\s]*\$?([\d.,]+)']

    lower_text = text.lower()

    for line in lines:
        ll = line.lower()
        # Date
        if info['Date'] is None:
            for pat in date_patterns:
                m = re.search(pat, ll, re.IGNORECASE)
                if m:
                    dt = parse_date(m.group(1))
                    if dt:
                        info['Date'] = dt
                        break
        # Invoice Number
        if not info['Invoice Number']:
            for pat in invoice_number_patterns:
                m = re.search(pat, ll, re.IGNORECASE)
                if m:
                    info['Invoice Number'] = m.group(1).strip()
                    break
        # Description
        if info['Description'] is None:
            for pat in description_patterns:
                m = re.search(pat, ll, re.IGNORECASE)
                if m:
                    desc = m.group(1).strip()
                    info['Description'] = desc
                    break
        # Amount
        if info['Amount'] is None:
            for pat in amount_patterns:
                m = re.search(pat, ll, re.IGNORECASE)
                if m:
                    # Normalize number string
                    amt = m.group(1).replace(',', '').strip()
                    info['Amount'] = amt
                    break
    # fallback, if date still missing, try search standalone date patterns
    if info['Date'] is None:
        import re
        date_matches = re.findall(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', text)
        if date_matches:
            dt = parse_date(date_matches[0])
            info['Date'] = dt

    return info

def main():
    if len(sys.argv) != 2:
        print('Usage: eval.py <workspace>')
        sys.exit(1)
    workspace = sys.argv[1]

    checks = []
    # 1. Check invoice-summary.csv presence and valid header
    csv_path = find_invoice_summary_csv(workspace)
    if csv_path is None:
        checks.append({'name': 'CSV file presence', 'passed': False, 'detail': 'Missing invoice-summary.csv in workspace'})
    else:
        csv_check, csv_rows = check_csv(csv_path)
        if not csv_check:
            checks.append({'name': 'CSV file format', 'passed': False, 'detail': csv_rows})
        else:
            checks.append({'name': 'CSV file presence', 'passed': True, 'detail': 'Found and readable'})

    # 2. Check vendor directories exist (expecting vendors from CSV)
    expected_vendors = set()
    if csv_path and csv_check:
        for r in csv_rows:
            v = r.get('Vendor', '')
            if v:
                expected_vendors.add(v.strip())

    vendor_dirs = find_vendor_folders(workspace)
    vendor_check_passed = True
    missing_vendors = []
    for ev in expected_vendors:
        if ev not in vendor_dirs:
            missing_vendors.append(ev)
    if missing_vendors:
        vendor_check_passed = False
    checks.append({'name': 'Vendor folders', 'passed': vendor_check_passed, 'detail': f'Missing vendor folders: {missing_vendors}' if missing_vendors else 'All vendor folders present'})

    # 3. Check renamed filenames inside vendor folders
    # For each CSV row, check file path exists, filename matches pattern
    filename_check_passed = True
    missing_files = []
    bad_filenames = []

    all_files_found = []
    if csv_path and csv_check:
        for r in csv_rows:
            fp = r.get('File Path', '').strip()
            if not fp:
                missing_files.append('(empty file path)')
                filename_check_passed = False
                continue
            full_fp = os.path.join(workspace, fp)
            if not os.path.isfile(full_fp):
                missing_files.append(fp)
                filename_check_passed = False
            else:
                all_files_found.append(full_fp)
                # Check filename format
                fname = os.path.basename(fp)
                if not contains_invoice_parts(fname):
                    bad_filenames.append(fname)
                    filename_check_passed = False

    checks.append({'name': 'Renamed files with correct format', 'passed': filename_check_passed, 'detail': f'Missing files: {missing_files}, Bad filenames: {bad_filenames}'})

    # 4. Check originals preserved in workspace - prompt states originals are preserved, not moved
    # We expect input subfolder from gen_inputs_script is preserved with original files
    orig_folder = os.path.join(workspace, 'input')
    originals_present = False
    if os.path.isdir(orig_folder):
        files_in_orig = [f for f in os.listdir(orig_folder) if os.path.isfile(os.path.join(orig_folder, f))]
        if set(['invoice1.pdf','receipt_image.jpg','screenshot.png']).issubset(set(files_in_orig)):
            originals_present = True
    checks.append({'name': 'Original files preserved', 'passed': originals_present, 'detail': 'input folder with original files present' if originals_present else 'Missing original input files'})

    # Calculate score
    score = sum(1 for c in checks if c['passed']) / len(checks)
    passed = (score == 1.0)

    result = {
        'passed': passed,
        'score': score,
        'checks': checks
    }
    print(json.dumps(result))

if __name__ == '__main__':
    main()
