#!/usr/bin/env python3
import sys
import os
import subprocess
import tempfile
import json
from pathlib import Path

def check_task_completion(workspace_dir):
    checks = []
    score = 0.0
    
    workspace = Path(workspace_dir)
    
    # Look for the merged/final document
    possible_names = ['merged_contract.docx', 'final_contract.docx', 'contract_final.docx', 'contract_merged.docx']
    final_doc = None
    for name in possible_names:
        if (workspace / name).exists():
            final_doc = workspace / name
            break
    
    if not final_doc:
        # Look for any .docx file that might be the result
        docx_files = list(workspace.glob('*.docx'))
        input_files = {'contract_v1_sarah.docx', 'contract_v2_mike.docx', 'contract_v3_legal.docx', 'contract_v4_temp.docx'}
        output_files = [f for f in docx_files if f.name not in input_files]
        if output_files:
            final_doc = output_files[0]  # Take the first non-input file
    
    if not final_doc:
        checks.append({"name": "output_file_exists", "passed": False, "detail": "No output document found"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "output_file_exists", "passed": True, "detail": f"Found output document: {final_doc.name}"})
    score += 0.1
    
    try:
        # Unpack the final document to analyze
        temp_dir = tempfile.mkdtemp()
        subprocess.run(['python', '/app/scripts/office/unpack.py', str(final_doc), temp_dir], 
                      check=True, capture_output=True)
        
        # Read the document XML
        doc_xml_path = Path(temp_dir) / 'word' / 'document.xml'
        if not doc_xml_path.exists():
            checks.append({"name": "document_readable", "passed": False, "detail": "Could not read document XML"})
            return {"passed": False, "score": score, "checks": checks}
        
        with open(doc_xml_path, 'r', encoding='utf-8') as f:
            doc_content = f.read()
        
        checks.append({"name": "document_readable", "passed": True, "detail": "Successfully read document content"})
        score += 0.1
        
        # Check Sarah Chen's changes were accepted (should see final text, no tracked changes from her)
        sarah_accepted = True
        if 'consulting services' not in doc_content:
            sarah_accepted = False
        if 'twelve) months' not in doc_content or 'twelve (12) months' not in doc_content:
            sarah_accepted = False
        if 'thirty (30) days' not in doc_content:
            sarah_accepted = False
            
        checks.append({"name": "sarah_changes_accepted", "passed": sarah_accepted, 
                      "detail": "Sarah Chen's changes should be accepted and visible in final text"})
        if sarah_accepted:
            score += 0.15
        
        # Check Mike Rodriguez's changes were accepted
        mike_accepted = True
        if '60 days written notice' not in doc_content:
            mike_accepted = False
        if 'Delaware state law' not in doc_content:
            mike_accepted = False
            
        checks.append({"name": "mike_changes_accepted", "passed": mike_accepted,
                      "detail": "Mike Rodriguez's changes should be accepted and visible in final text"})
        if mike_accepted:
            score += 0.15
        
        # Check temp_reviewer changes were rejected (original text should remain)
        temp_rejected = True
        if 'Temporary Service Agreement' in doc_content:
            temp_rejected = False
        if 'start date' in doc_content and 'effective date' not in doc_content:
            temp_rejected = False
        if 'Service Agreement' not in doc_content:  # Original should be there
            temp_rejected = False
            
        checks.append({"name": "temp_changes_rejected", "passed": temp_rejected,
                      "detail": "temp_reviewer changes should be rejected, original text should remain"})
        if temp_rejected:
            score += 0.15
        
        # Check Legal Team deletions were accepted but insertions rejected
        legal_correct = True
        # Deletion should be accepted - 'binding arbitration' should be gone
        if 'binding arbitration' in doc_content:
            legal_correct = False
        # Insertions should be rejected - these phrases shouldn't appear
        if 'Additional termination fees may apply' in doc_content:
            legal_correct = False
        if 'subject to confidentiality clauses' in doc_content:
            legal_correct = False
            
        checks.append({"name": "legal_changes_partial", "passed": legal_correct,
                      "detail": "Legal Team deletions accepted, insertions rejected"})
        if legal_correct:
            score += 0.15
        
        # Check for comments on Legal Team insertion paragraphs
        comments_xml_path = Path(temp_dir) / 'word' / 'comments.xml'
        has_comments = False
        comment_explains_rejection = False
        
        if comments_xml_path.exists():
            with open(comments_xml_path, 'r', encoding='utf-8') as f:
                comments_content = f.read()
            has_comments = '<w:comment' in comments_content
            # Look for explanation about rejection
            if 'reject' in comments_content.lower() or 'legal' in comments_content.lower():
                comment_explains_rejection = True
        
        checks.append({"name": "comments_added", "passed": comment_explains_rejection,
                      "detail": "Comments should explain why Legal Team insertions were rejected"})
        if comment_explains_rejection:
            score += 0.1
        
        # Check for Review Summary section
        has_review_summary = 'Review Summary' in doc_content
        checks.append({"name": "review_summary_section", "passed": has_review_summary,
                      "detail": "Should contain a 'Review Summary' section"})
        if has_review_summary:
            score += 0.1
        
        # Check for table with reviewer statistics
        has_table = '<w:tbl>' in doc_content
        has_reviewer_stats = False
        if has_table:
            # Look for reviewer names in table context
            if 'Sarah Chen' in doc_content and 'Mike Rodriguez' in doc_content and 'Legal Team' in doc_content:
                has_reviewer_stats = True
        
        checks.append({"name": "reviewer_statistics_table", "passed": has_reviewer_stats,
                      "detail": "Should contain table showing accepted/rejected changes per reviewer"})
        if has_reviewer_stats:
            score += 0.1
        
        # Clean up
        subprocess.run(['rm', '-rf', temp_dir], check=True)
        
    except Exception as e:
        checks.append({"name": "analysis_error", "passed": False, "detail": f"Error analyzing document: {str(e)}"})
        return {"passed": False, "score": score, "checks": checks}
    
    passed = score >= 0.7  # Need at least 70% to pass
    return {"passed": passed, "score": score, "checks": checks}

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "usage", "passed": False, "detail": "Usage: eval_script.py <workspace_dir>"}]}))
        sys.exit(1)
    
    result = check_task_completion(sys.argv[1])
    print(json.dumps(result))