import json
import os
import sys
import csv
import re
from pathlib import Path


def case_insensitive_search(text, keywords):
    """Return True if any keyword found in text, case-insensitive."""
    if not text:
        return False
    text = text.lower()
    return any(k.lower() in text for k in keywords)


def normalize_filename_part(text):
    # Remove special characters except hyphens and commas, replace multiple spaces with single space
    if not text:
        return "" 
    # Replace underscores and multiple spaces with single space
    text = re.sub(r'[_]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove chars except letters, digits, space, hyphen, comma
    text = re.sub(r'[^\w\d\s\-,]', '', text)
    # Remove leading/trailing spaces
    text = text.strip()
    return text


def parse_invoice_csv(csv_path):
    data = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize keys
            data.append({k.strip(): (v.strip() if v else '') for k, v in row.items()})
    return data


# Validate directory and file structure, CSV contents

def main():
    # Arg1 is workspace dir
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "general", "passed": False, "detail": "Missing workspace dir argument."}]}))
        return

    root = Path(sys.argv[1])
    checks = []

    sorted_dir = root / 'SortedInvoices'
    if not sorted_dir.is_dir():
        checks.append({"name": "folder_exists", "passed": False, "detail": "SortedInvoices directory does not exist."})
    else:
        checks.append({"name": "folder_exists", "passed": True, "detail": "Found SortedInvoices directory."})

    # Check for subfolders for vendors and Needs-Review
    expected_vendors = {'Adobe', 'Amazon', 'Delta Airlines', 'Staples', 'Uber', 'Microsoft'}
    folder_vendors = set()
    needs_review_dir = sorted_dir / 'Needs-Review'

    if needs_review_dir.is_dir():
        needs_review_exists = True
    else:
        needs_review_exists = False

    # Gather all folders at top-level except csv and Needs-Review
    for child in sorted_dir.iterdir():
        if child.is_dir() and child.name != 'Needs-Review':
            folder_vendors.add(child.name)

    # Check vendor folders
    vendor_folder_check = any(v.lower() in (name.lower() for name in folder_vendors) for v in expected_vendors)
    checks.append({"name": "vendor_folders", "passed": vendor_folder_check, "detail": f"Vendor folders found: {sorted(folder_vendors)}"})

    # Find files inside Needs-Review, if folder exists
    needs_review_files = []
    if needs_review_exists:
        needs_review_files = list(needs_review_dir.glob('*'))
        # Check filenames start with NeedsReview_
        needs_review_name_valid = all(f.name.startswith('NeedsReview_') for f in needs_review_files)
        checks.append({"name": "needs_review_naming", "passed": needs_review_name_valid, "detail": f"NeedsReview folder files count: {len(needs_review_files)}"})
    else:
        checks.append({"name": "needs_review_folder", "passed": True, "detail": "No Needs-Review folder created (acceptable if no files missing info)."})

    # Check that original files still exist in root (or not moved)
    original_files_expected = {'inv123.pdf', 'bill_april.pdf', 'receipt_march.pdf', 'IMG_001.jpg', 'scan_April.png', 'receipt_001.png'}
    existing_originals = [f.name for f in root.iterdir() if f.is_file()]  
    origs_found = set(existing_originals) & original_files_expected
    origs_check = len(origs_found) == len(original_files_expected)
    checks.append({"name": "original_files_preserved", "passed": origs_check, "detail": f"Found original files {sorted(origs_found)}"})

    # Check renamed files contain correct info and are under SortedInvoices/Vendor/

    renamed_files = []
    for vendor_dir in folder_vendors:
        vdir = sorted_dir / vendor_dir
        if not vdir.is_dir():
            continue
        for f in vdir.glob('*'):
            if not f.is_file():
                continue
            renamed_files.append(f)

    # Check 6 files renamed properly
    rename_check = len(renamed_files) == 6 or (len(renamed_files) + len(needs_review_files) == 6)
    checks.append({"name": "renamed_files_count", "passed": rename_check, "detail": f"Renamed files count: {len(renamed_files)}"})

    # Check rename format: YYYY-MM-DD Vendor - Invoice - Description.ext
    # Lowercase all vendors for matching
    vendors_lower = {v.lower() for v in expected_vendors}

    format_pass = True
    format_detail_msgs = []
    for f in renamed_files:
        name = f.name
        # Check date
        date_match = re.search(r'20\d{2}-\d{2}-\d{2}', name)
        if not date_match:
            format_pass = False
            format_detail_msgs.append(f'{name} missing date in filename')
        # Check vendor
        # Extract vendor from filename parts
        parts = name.split(' ')
        # Vendor after date
        if len(parts) < 4:
            format_pass = False
            format_detail_msgs.append(f'{name} filename has less than 4 parts')
            continue
        vendor_part = parts[1]
        # Sometimes vendor may be two words, check vendors_lower contains any part
        # try case-insensitive
        vendor_match = False
        for v in vendors_lower:
            if v in name.lower():
                vendor_match = True
                break
        if not vendor_match:
            format_pass = False
            format_detail_msgs.append(f'{name} vendor not recognized')

    checks.append({"name": "renamed_filenames_format", "passed": format_pass, "detail": '; '.join(format_detail_msgs) if format_detail_msgs else "All filenames valid format."})

    # Check CSV existence and content
    csv_path = sorted_dir / 'invoice-summary.csv'
    if not csv_path.is_file():
        checks.append({"name": "csv_file_exists", "passed": False, "detail": "CSV file 'invoice-summary.csv' not found."})
    else:
        checks.append({"name": "csv_file_exists", "passed": True, "detail": "CSV file found."})
        # Parse CSV and check columns and entries
        try:
            data = parse_invoice_csv(csv_path)
            required_cols = {'Date', 'Vendor', 'Invoice Number', 'Description', 'Amount', 'Category', 'File Path'}
            csv_columns = set() if len(data) == 0 else set(data[0].keys())
            cols_pass = required_cols.issubset(csv_columns)
            if not cols_pass:
                checks.append({"name": "csv_columns", "passed": False, "detail": f"Missing columns in CSV. Found: {csv_columns}"})
            else:
                checks.append({"name": "csv_columns", "passed": True, "detail": "All required columns present in CSV."})
            # Check at least 6 rows
            rows_pass = len(data) >= 6
            checks.append({"name": "csv_rows_count", "passed": rows_pass, "detail": f"CSV row count: {len(data)}"})

            # Check dates format in CSV
            date_fmt_pass = True
            for row in data:
                dt = row.get('Date', '').strip()
                if not re.match(r'20\d{2}-\d{2}-\d{2}', dt):
                    date_fmt_pass = False
                    break
            checks.append({"name": "csv_dates_format", "passed": date_fmt_pass, "detail": "Dates formatted as YYYY-MM-DD in CSV." if date_fmt_pass else "Date format incorrect in CSV."})

            # Check categories only one of Software, Office Supplies, Travel
            valid_categories = {'software', 'office supplies', 'travel'}
            cat_pass = all(row.get('Category', '').strip().lower() in valid_categories for row in data)
            checks.append({"name": "csv_categories", "passed": cat_pass, "detail": "Invoice categories valid." if cat_pass else "Invalid categories detected."})

            # Check File Path columns files exist
            file_path_ok = True
            missing_files = []
            for row in data:
                fpath = row.get('File Path', '').strip()
                if not fpath:
                    file_path_ok = False
                    missing_files.append(fpath)
                else:
                    p = root / fpath
                    if not p.is_file():
                        file_path_ok = False
                        missing_files.append(fpath)
            checks.append({"name": "csv_filepaths_exist", "passed": file_path_ok, "detail": f"CSV file paths verified." if file_path_ok else f"Missing files in CSV paths: {missing_files}"})

        except Exception as e:
            checks.append({"name": "csv_parsing", "passed": False, "detail": f"Error parsing CSV: {str(e)}"})

    # Calculate final score
    passed_checks = sum(1 for c in checks if c['passed'])
    total_checks = len(checks) if checks else 1
    score = passed_checks / total_checks
    passed = score >= 0.8

    print(json.dumps({
        "passed": passed,
        "score": score,
        "checks": checks
    }))


if __name__ == '__main__':
    main()
