import sys
import os
import pandas as pd
import json
from pathlib import Path
import pdfplumber
from pypdf import PdfReader

def check_extracted_excel(workspace_path):
    """Check if Excel file was created with proper table data"""
    excel_path = Path(workspace_path) / "extracted_tables.xlsx"
    if not excel_path.exists():
        return False, "Excel file 'extracted_tables.xlsx' not found"
    
    try:
        # Read all sheets
        xl_file = pd.ExcelFile(excel_path)
        sheets = xl_file.sheet_names
        
        if len(sheets) < 3:
            return False, f"Expected at least 3 sheets, found {len(sheets)}"
        
        # Check for revenue data (should contain quarterly revenue)
        revenue_found = False
        expense_found = False
        margin_found = False
        
        for sheet_name in sheets:
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            
            # Look for revenue table markers
            if any(df.astype(str).apply(lambda x: x.str.contains('324500|344800|366200|387700', na=False)).any()):
                revenue_found = True
                # Check if it has proper structure
                if df.shape[0] < 4 or df.shape[1] < 4:
                    return False, f"Revenue table has insufficient data: {df.shape}"
            
            # Look for expense table markers
            if any(df.astype(str).apply(lambda x: x.str.contains('Marketing|45000|47500|R&D', na=False)).any()):
                expense_found = True
                if df.shape[0] < 4 or df.shape[1] < 4:
                    return False, f"Expense table has insufficient data: {df.shape}"
            
            # Look for margin table markers
            if any(df.astype(str).apply(lambda x: x.str.contains('North America|542000|29.9|25.3', na=False)).any()):
                margin_found = True
                if df.shape[0] < 4 or df.shape[1] < 3:
                    return False, f"Margin table has insufficient data: {df.shape}"
        
        if not revenue_found:
            return False, "Revenue table data not found in Excel"
        if not expense_found:
            return False, "Expense table data not found in Excel"
        if not margin_found:
            return False, "Margin table data not found in Excel"
        
        return True, f"Excel contains all 3 tables across {len(sheets)} sheets"
    
    except Exception as e:
        return False, f"Error reading Excel file: {str(e)}"

def check_summary_pdf(workspace_path):
    """Check if summary PDF was created with required content"""
    summary_files = list(Path(workspace_path).glob("*summary*.pdf")) + list(Path(workspace_path).glob("*report*.pdf"))
    
    if not summary_files:
        return False, "No summary/report PDF file found"
    
    summary_path = summary_files[0]
    
    try:
        with pdfplumber.open(summary_path) as pdf:
            if len(pdf.pages) == 0:
                return False, "Summary PDF has no pages"
            
            # Extract all text from PDF
            all_text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    all_text += page_text.lower()
            
            # Check for key content indicators
            required_indicators = ['total', 'revenue', 'summary', 'average']
            found_indicators = [indicator for indicator in required_indicators if indicator in all_text]
            
            if len(found_indicators) < 2:
                return False, f"Summary PDF missing key content. Found: {found_indicators}"
            
            # Check for numerical values (should have some calculations)
            import re
            numbers = re.findall(r'[0-9,]+', all_text)
            if len(numbers) < 3:
                return False, "Summary PDF should contain calculated numerical values"
            
            return True, f"Summary PDF contains {len(found_indicators)} key indicators and {len(numbers)} numerical values"
    
    except Exception as e:
        return False, f"Error reading summary PDF: {str(e)}"

def check_file_structure(workspace_path):
    """Check if required files exist"""
    required_files = ['financial_data.pdf']
    missing_files = []
    
    for file in required_files:
        if not (Path(workspace_path) / file).exists():
            missing_files.append(file)
    
    if missing_files:
        return False, f"Missing input files: {missing_files}"
    
    # Check for output files
    excel_files = list(Path(workspace_path).glob("*.xlsx"))
    pdf_files = [f for f in Path(workspace_path).glob("*.pdf") if f.name != 'financial_data.pdf']
    
    if not excel_files:
        return False, "No Excel output file found"
    
    if not pdf_files:
        return False, "No summary PDF output file found"
    
    return True, f"Found {len(excel_files)} Excel file(s) and {len(pdf_files)} output PDF(s)"

def main(workspace_path):
    checks = []
    total_score = 0
    
    # Check 1: File structure (20 points)
    file_passed, file_detail = check_file_structure(workspace_path)
    checks.append({"name": "File Structure", "passed": file_passed, "detail": file_detail})
    if file_passed:
        total_score += 20
    
    # Check 2: Excel extraction (40 points)
    excel_passed, excel_detail = check_extracted_excel(workspace_path)
    checks.append({"name": "Excel Table Extraction", "passed": excel_passed, "detail": excel_detail})
    if excel_passed:
        total_score += 40
    
    # Check 3: Summary PDF (40 points)
    summary_passed, summary_detail = check_summary_pdf(workspace_path)
    checks.append({"name": "Summary PDF Creation", "passed": summary_passed, "detail": summary_detail})
    if summary_passed:
        total_score += 40
    
    result = {
        "passed": all(check["passed"] for check in checks),
        "score": total_score / 100.0,
        "checks": checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python eval_script.py <workspace_path>")
        sys.exit(1)
    
    main(sys.argv[1])