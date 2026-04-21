import sys
import os
import re
import csv
import json
from pathlib import Path


def read_all_text_from_pdf(path):
    # Use pdfminer.six to extract text
    from pdfminer.high_level import extract_text
    try:
        return extract_text(path)
    except Exception:
        return ""


def read_text_from_image(path):
    # Use pytesseract
    from PIL import Image
    import pytesseract
    try:
        img = Image.open(path)
        text = pytesseract.image_to_string(img)
        return text
    except Exception:
        return ""


def extract_fields(text):
    # Case insensitive search
    text_lower = text.lower()

    # Extract date. Look for 'invoice date:', 'date:', 'issued:' patterns
    date_pattern = re.compile(r'(invoice date|date|issued)\s*[:\-]\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})', re.IGNORECASE)
    m_date = date_pattern.search(text)
    date = None
    if m_date:
        date = m_date.group(2)

    # Invoice number: look for 'invoice #:', 'invoice number:', 'receipt #:'
    invoice_num_pattern = re.compile(r'(invoice #|invoice number|receipt #)\s*[:\-]\s*([\w\-]+)', re.IGNORECASE)
    m_inv = invoice_num_pattern.search(text)
    invoice_num = m_inv.group(2) if m_inv else ""

    # Vendor: assume the first line often is vendor if alphanumeric line
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    vendor = ""
    for line in lines[:5]:
        # Like Adobe or Amazon and not a date or amount
        if re.search(r'\d{4}[-/]', line):
            continue
        if any(w in line.lower() for w in ['invoice', 'date', 'amount', 'total', 'description']):
            continue
        if len(line) > 1 and len(line) < 40 and re.match(r'^[\w \.-]+$', line):
            vendor = line
            break

    # Amount: look for 'amount due:', 'total:', etc.
    amount_pattern = re.compile(r'(amount due|total|amount|subtotal)\s*[:\-]?\s*\$?\s*([0-9,.]+)', re.IGNORECASE)
    m_amt = amount_pattern.search(text)
    amount = m_amt.group(2) if m_amt else ""

    # Description: look for 'description:', 'product:', 'service:'
    description_pattern = re.compile(r'(description|product|service)\s*[:\-]\s*(.+)', re.IGNORECASE)
    m_desc = description_pattern.search(text)
    description = m_desc.group(2).strip() if m_desc else ""

    return {
        'date': date,
        'vendor': vendor,
        'invoice_number': invoice_num,
        'amount': amount,
        'description': description
    }


def sanitize_filename(s):
    # Remove special chars except hyphens and spaces
    s = re.sub(r'[^\w\s\-]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()  # collapse spaces
    return s


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "Workspace directory argument missing"}]}))
        return
    workspace = sys.argv[1]
    base_dir = Path(workspace) / 'Organized_Invoices'

    checks = []

    # Check folder 'Organized_Invoices' exists
    if not base_dir.exists() or not base_dir.is_dir():
        checks.append({"name": "folder_exist", "passed": False, "detail": f"Folder 'Organized_Invoices' not found at expected location {base_dir}"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return
    else:
        checks.append({"name": "folder_exist", "passed": True, "detail": "Folder 'Organized_Invoices' exists"})

    # Check at least 6 files are present inside Organized_Invoices (not counting Needs-Review)
    num_files = 0
    vendor_dirs = [d for d in base_dir.iterdir() if d.is_dir() and d.name.lower() != 'needs-review']
    for vd in vendor_dirs:
        for f in vd.glob('*'):
            if f.is_file():
                num_files += 1
    checks.append({"name": "file_count", "passed": num_files >= 6, "detail": f"Found {num_files} organized files under vendor folders"})

    # Check folder 'Needs-Review' exists (may be empty, allow 0 files)
    needs_review_dir = base_dir / 'Needs-Review'
    has_needs_review = needs_review_dir.exists() and any(needs_review_dir.iterdir())
    checks.append({"name": "needs_review_folder", "passed": needs_review_dir.exists(), "detail": f"Needs-Review folder exists: {needs_review_dir.exists()}"})

    # Check required CSV file with expected columns
    csv_path = base_dir / 'invoice-summary.csv'
    if not csv_path.exists():
        checks.append({"name": "csv_exists", "passed": False, "detail": "invoice-summary.csv not found"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return
    else:
        # Read and check columns
        try:
            with open(csv_path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                expected_cols = ['Date', 'Vendor', 'Invoice Number', 'Description', 'Amount', 'File Path']
                header_checks = all(any(h.lower() == col.lower() for h in headers or []) for col in expected_cols)
                if not header_checks:
                    checks.append({"name": "csv_columns", "passed": False, "detail": f"CSV missing expected columns. Found columns: {headers}"})
                else:
                    checks.append({"name": "csv_columns", "passed": True, "detail": "CSV contains all expected columns"})
                # Check at least 6 rows (matching files) and entries have valid data
                rows = list(reader)
                rows_valid = len(rows) >= 6
                checks.append({"name": "csv_row_count", "passed": rows_valid, "detail": f"CSV rows found: {len(rows)}"})

                # Sample check: for each row date format YYYY-MM-DD
                date_valid = all((r.get('Date', '') and re.match(r'\d{4}-\d{2}-\d{2}', r.get('Date', ''))) for r in rows)
                checks.append({"name": "csv_date_format", "passed": date_valid, "detail": "Dates in correct YYYY-MM-DD format"})

                # Check File Path values reference existing files relative to Organized_Invoices
                files_ok = True
                for r in rows:
                    fp = r.get('File Path', '').strip()
                    if not fp:
                        files_ok = False
                        break
                    file_path = base_dir / fp
                    if not file_path.exists() or not file_path.is_file():
                        files_ok = False
                        break
                checks.append({"name": "csv_file_paths", "passed": files_ok, "detail": f"All File Paths exist in Organized_Invoices folder: {files_ok}"})

        except Exception as e:
            checks.append({"name": "csv_read", "passed": False, "detail": f"Failed to read CSV: {e}"})

    # Check file naming convention: YYYY-MM-DD Vendor - Invoice - Description.ext
    # Check all files inside vendor folders follow pattern
    name_pattern = re.compile(r'\d{4}-\d{2}-\d{2} [\w .&-]+ - (Invoice|Receipt) - [\w .&-]+\.(pdf|jpg|png)$', re.IGNORECASE)
    naming_ok = True
    for vd in vendor_dirs:
        for f in vd.glob('*'):
            if f.is_file():
                if not name_pattern.match(f.name):
                    naming_ok = False
                    break
        if not naming_ok:
            break
    checks.append({"name": "filename_convention", "passed": naming_ok, "detail": "All organized files named per required pattern" if naming_ok else "Some files do not follow naming convention"})

    # Check originals not deleted: receipts2024 folder still has original 6 files
    receipts_dir = Path(workspace) / 'receipts2024'
    original_files = list(receipts_dir.glob('*'))
    checks.append({"name": "originals_preserved", "passed": len(original_files) >= 6, "detail": f"Original files preserved count: {len(original_files)}"})

    score = sum(1 for c in checks if c.get('passed')) / max(len(checks), 1)
    passed = score >= 0.8

    print(json.dumps({"passed": passed, "score": score, "checks": checks}))


if __name__ == '__main__':
    main()
