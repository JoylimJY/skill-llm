#!/usr/bin/env python3
import sys
import json
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

workspace = Path(sys.argv[1])
result = {"passed": False, "score": 0.0, "checks": []}

try:
    docx_file = workspace / 'report.docx'
    
    # Check 1: File exists
    check1 = {"name": "File exists", "passed": docx_file.exists(), "detail": "report.docx found" if docx_file.exists() else "report.docx not found"}
    result["checks"].append(check1)
    
    if not docx_file.exists():
        result["score"] = 0.0
        print(json.dumps(result))
        sys.exit(0)
    
    # Extract and parse document.xml
    with ZipFile(docx_file) as zf:
        doc_xml = zf.read('word/document.xml').decode('utf-8')
    
    # Check 2: Title exists
    check2 = {"name": "Title present", "passed": 'Quarterly Report' in doc_xml, "detail": "Title 'Quarterly Report' found" if 'Quarterly Report' in doc_xml else "Title not found"}
    result["checks"].append(check2)
    
    # Check 3: Subtitle exists
    check3 = {"name": "Subtitle present", "passed": 'Q1 2025' in doc_xml, "detail": "Subtitle 'Q1 2025' found" if 'Q1 2025' in doc_xml else "Subtitle not found"}
    result["checks"].append(check3)
    
    # Check 4: Body text exists
    check4 = {"name": "Body text present", "passed": 'key metrics' in doc_xml.lower(), "detail": "Body text found" if 'key metrics' in doc_xml.lower() else "Body text not found"}
    result["checks"].append(check4)
    
    # Check 5: Table content exists
    check5 = {"name": "Table content present", "passed": 'Revenue' in doc_xml and '1.2M' in doc_xml, "detail": "Table with Revenue and value found" if ('Revenue' in doc_xml and '1.2M' in doc_xml) else "Table content incomplete"}
    result["checks"].append(check5)
    
    # Check 6: Footer exists
    check6 = {"name": "Footer present", "passed": 'Page' in doc_xml, "detail": "Footer with page reference found" if 'Page' in doc_xml else "Footer not found"}
    result["checks"].append(check6)
    
    # Check 7: Valid DOCX structure
    check7 = {"name": "Valid DOCX structure", "passed": True, "detail": "DOCX file is valid ZIP archive"}
    result["checks"].append(check7)
    
    passed_count = sum(1 for c in result["checks"] if c["passed"])
    result["score"] = passed_count / len(result["checks"])
    result["passed"] = result["score"] >= 0.85
    
except Exception as e:
    result["checks"].append({"name": "Error", "passed": False, "detail": str(e)})
    result["score"] = 0.0
    result["passed"] = False

print(json.dumps(result))
