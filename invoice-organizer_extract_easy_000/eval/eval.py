import sys
import os
import csv
import re
import json

def safe_lower(text):
    if not text:
        return ""
    return text.lower()

def check_filename_format(filename):
    base = os.path.basename(filename)
    name, ext = os.path.splitext(base)
    
    # 修复：使用 (.*?) 非贪婪匹配，允许发票号里出现连字符！
    m = re.match(r"^(\d{4}-\d{2}-\d{2})\s+(.*?)\s+-\s+(.*?)\s+-\s+(.+)$", name, re.IGNORECASE)
    if not m:
        return False
        
    vendor_part = m.group(2).strip()
    
    if not re.match(r"^[a-zA-Z0-9 &()\[\]_\-]+$", vendor_part):
        return False
        
    return True

def find_invoice_files(root_dir):
    invoice_files = []
    for dirpath, dirs, files in os.walk(root_dir):
        for f in files:
            ext = f.lower().split('.')[-1]
            if ext in ['pdf', 'jpg', 'jpeg', 'png']:
                invoice_files.append(os.path.join(dirpath, f))
    return invoice_files

def find_organized_files(root_dir):
    organized_files = []
    for dirpath, dirs, files in os.walk(root_dir):
        for f in files:
            if check_filename_format(f):
                full_path = os.path.join(dirpath, f)
                organized_files.append(full_path)
    return organized_files

def check_csv_file(root_dir):
    candidates = [f for f in os.listdir(root_dir) if f.lower().endswith('.csv') and 'invoice' in f.lower()]
    if not candidates:
        return False, "No csv file matching 'invoice' found"
    csv_path = os.path.join(root_dir, candidates[0])
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = set(h.lower() for h in reader.fieldnames)
        required = set(['date','vendor','invoice number','description','amount','category','file path'])
        if not required.issubset(headers):
            return False, "CSV missing one or more required columns"
        rows = list(reader)
        if len(rows) < 1:
            return False, "CSV file is empty"
    return True, "CSV file looks valid"

def test():
    cwd = sys.argv[1]
    results = []

    input_files = {'invoice1.pdf': 'Adobe', 'amazon_invoice.pdf': 'Amazon', 'receipt1.jpg': 'Staples'}
    organized_files = find_organized_files(cwd)
    
    found_vendors = set()
    found_files = 0
    for f in organized_files:
        base = os.path.basename(f)
        passed = check_filename_format(base)
        if passed:
            name, _ = os.path.splitext(base)
            # 配合修好的正则提取 Vendor
            m = re.match(r"^(\d{4}-\d{2}-\d{2})\s+(.*?)\s+-\s+(.*?)\s+-\s+(.+)$", name, re.IGNORECASE)
            if m:
                vendor_name = m.group(2).strip()
                found_vendors.add(vendor_name.lower())
                found_files += 1

            results.append({
                "name": f"File naming for {base}",
                "passed": passed,
                "detail": f"Filename '{base}' proper format"
            })
        else:
            results.append({
                "name": f"File naming for {base}",
                "passed": False,
                "detail": f"Filename '{base}' NOT proper format"
            })

    vendors_expected = set(v.lower() for v in input_files.values())
    vendors_found_normalized = set(v.lower() for v in found_vendors)
    vendors_missing = vendors_expected - vendors_found_normalized
    vendors_pass = len(vendors_missing) == 0
    
    results.append({
        "name": "Vendors found",
        "passed": vendors_pass,
        "detail": f"Expected vendors: {vendors_expected}. Found: {vendors_found_normalized}. Missing: {vendors_missing}"
    })

    results.append({
        "name": "Sufficient organized files",
        "passed": found_files >= 3,
        "detail": f"Found {found_files} organized files (expected at least 3)"
    })

    vendor_folder_check_pass = True
    for f in organized_files:
        parts = os.path.normpath(f).split(os.sep)
        found_vendor_folder = False
        for part in parts:
            if part.lower() in vendors_expected:
                found_vendor_folder = True
                break
        if not found_vendor_folder:
            vendor_folder_check_pass = False
            results.append({
                "name": "Vendor folder inclusion",
                "passed": False,
                "detail": f"File {f} not inside a vendor folder"
            })
            break
            
    if vendor_folder_check_pass:
        results.append({
            "name": "Vendor folders verified",
            "passed": True,
            "detail": "All organized files are inside appropriate vendor folders"
        })

    csv_pass, csv_detail = check_csv_file(cwd)
    results.append({
        "name": "CSV invoice-summary.csv file",
        "passed": csv_pass,
        "detail": csv_detail
    })

    score = sum(1 for c in results if c.get("passed")) / len(results) if results else 0
    passed = score == 1.0

    output = {"passed": passed, "score": score, "checks": results}
    print(json.dumps(output))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "Expected one argument workspace dir"}]}))
        sys.exit(1)
    test()