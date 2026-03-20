import sys
import os
from pypdf import PdfReader
import json

def check_task_completion(workspace_dir):
    checks = []
    passed = True
    score = 0.0
    
    # Change to workspace directory
    os.chdir(workspace_dir)
    
    # Check 1: annual_summary.pdf exists and has correct page count
    try:
        if os.path.exists('annual_summary.pdf'):
            reader = PdfReader('annual_summary.pdf')
            page_count = len(reader.pages)
            expected_pages = 4 + 3 + 5  # Q1(4) + Q2(3) + Q3(5) = 12 pages
            if page_count == expected_pages:
                checks.append({"name": "annual_summary_pages", "passed": True, "detail": f"Correct page count: {page_count}"})
                score += 0.3
            else:
                checks.append({"name": "annual_summary_pages", "passed": False, "detail": f"Expected {expected_pages} pages, got {page_count}"})
                passed = False
        else:
            checks.append({"name": "annual_summary_exists", "passed": False, "detail": "annual_summary.pdf not found"})
            passed = False
    except Exception as e:
        checks.append({"name": "annual_summary_read", "passed": False, "detail": f"Error reading annual_summary.pdf: {str(e)}"})
        passed = False
    
    # Check 2: executive_summaries.pdf exists and has 3 pages (one from each report)
    try:
        if os.path.exists('executive_summaries.pdf'):
            reader = PdfReader('executive_summaries.pdf')
            page_count = len(reader.pages)
            if page_count == 3:
                checks.append({"name": "executive_summaries_pages", "passed": True, "detail": "Correct 3 executive summary pages"})
                score += 0.25
                
                # Check if executive summary content is present
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                
                exec_markers = ['EXEC_SUMMARY_MARKER_Q1', 'EXEC_SUMMARY_MARKER_Q2', 'EXEC_SUMMARY_MARKER_Q3']
                markers_found = sum(1 for marker in exec_markers if marker in text)
                if markers_found == 3:
                    checks.append({"name": "executive_content", "passed": True, "detail": "All executive summary markers found"})
                    score += 0.25
                else:
                    checks.append({"name": "executive_content", "passed": False, "detail": f"Only found {markers_found}/3 executive summary markers"})
                    passed = False
            else:
                checks.append({"name": "executive_summaries_pages", "passed": False, "detail": f"Expected 3 pages, got {page_count}"})
                passed = False
        else:
            checks.append({"name": "executive_summaries_exists", "passed": False, "detail": "executive_summaries.pdf not found"})
            passed = False
    except Exception as e:
        checks.append({"name": "executive_summaries_read", "passed": False, "detail": f"Error reading executive_summaries.pdf: {str(e)}"})
        passed = False
    
    # Check 3: report_metadata.txt exists and contains required information
    try:
        if os.path.exists('report_metadata.txt'):
            with open('report_metadata.txt', 'r') as f:
                metadata_content = f.read()
            
            # Check for page count mention
            if '12' in metadata_content or 'twelve' in metadata_content.lower():
                checks.append({"name": "metadata_page_count", "passed": True, "detail": "Total page count mentioned"})
                score += 0.1
            else:
                checks.append({"name": "metadata_page_count", "passed": False, "detail": "Total page count not found in metadata"})
                passed = False
            
            # Check for title markers from each report
            title_markers = ['TITLE_MARKER: Q1', 'TITLE_MARKER: Q2', 'TITLE_MARKER: Q3']
            titles_found = sum(1 for marker in title_markers if marker in metadata_content)
            if titles_found == 3:
                checks.append({"name": "metadata_titles", "passed": True, "detail": "All quarterly report titles found"})
                score += 0.1
            else:
                checks.append({"name": "metadata_titles", "passed": False, "detail": f"Only found {titles_found}/3 report titles"})
                passed = False
        else:
            checks.append({"name": "metadata_exists", "passed": False, "detail": "report_metadata.txt not found"})
            passed = False
    except Exception as e:
        checks.append({"name": "metadata_read", "passed": False, "detail": f"Error reading report_metadata.txt: {str(e)}"})
        passed = False
    
    return {"passed": passed, "score": score, "checks": checks}

if __name__ == "__main__":
    workspace_dir = sys.argv[1]
    result = check_task_completion(workspace_dir)
    print(json.dumps(result, indent=2))