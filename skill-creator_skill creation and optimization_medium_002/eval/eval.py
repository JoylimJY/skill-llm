import sys
import os
import json
import re
from pathlib import Path

def main():
    workspace = sys.argv[1]
    checks = []
    
    # Check if documentation.md exists
    doc_file = Path(workspace) / 'documentation.md'
    doc_exists = doc_file.exists()
    checks.append({
        'name': 'documentation_file_created',
        'passed': doc_exists,
        'detail': f'documentation.md exists: {doc_exists}'
    })
    
    if doc_exists:
        try:
            doc_content = doc_file.read_text().lower()
            
            # Check for table of contents
            toc_present = any(marker in doc_content for marker in ['table of contents', 'contents', '## contents', '# contents'])
            checks.append({
                'name': 'table_of_contents_present',
                'passed': toc_present,
                'detail': f'Table of contents found: {toc_present}'
            })
            
            # Check for class documentation
            class_doc = 'dataprocessor' in doc_content or 'data processor' in doc_content
            checks.append({
                'name': 'class_documentation',
                'passed': class_doc,
                'detail': f'DataProcessor class documented: {class_doc}'
            })
            
            # Check for function documentation
            func_docs = [
                'calculate_area' in doc_content,
                'format_text' in doc_content,
                'process_numbers' in doc_content
            ]
            func_documented = sum(func_docs) >= 2
            checks.append({
                'name': 'function_documentation',
                'passed': func_documented,
                'detail': f'Functions documented: {sum(func_docs)}/3'
            })
            
            # Check for parameter information
            param_info = any(marker in doc_content for marker in ['parameters', 'args', 'arguments', 'param'])
            checks.append({
                'name': 'parameter_information',
                'passed': param_info,
                'detail': f'Parameter information found: {param_info}'
            })
            
            # Check for return value information
            return_info = any(marker in doc_content for marker in ['returns', 'return', 'output'])
            checks.append({
                'name': 'return_value_information',
                'passed': return_info,
                'detail': f'Return value information found: {return_info}'
            })
            
        except Exception as e:
            checks.append({
                'name': 'documentation_readable',
                'passed': False,
                'detail': f'Error reading documentation: {str(e)}'
            })
    
    # Check for test cases file
    test_file = Path(workspace) / 'test_cases.json'
    test_exists = test_file.exists()
    checks.append({
        'name': 'test_cases_file_created',
        'passed': test_exists,
        'detail': f'test_cases.json exists: {test_exists}'
    })
    
    if test_exists:
        try:
            with open(test_file, 'r') as f:
                test_data = json.load(f)
            
            # Check if test data has reasonable structure
            has_assertions = isinstance(test_data, (dict, list)) and len(str(test_data)) > 50
            checks.append({
                'name': 'test_cases_content',
                'passed': has_assertions,
                'detail': f'Test cases contain content: {has_assertions}'
            })
            
        except Exception as e:
            checks.append({
                'name': 'test_cases_readable',
                'passed': False,
                'detail': f'Error reading test cases: {str(e)}'
            })
    
    # Calculate final score
    passed_count = sum(1 for check in checks if check['passed'])
    score = passed_count / len(checks)
    passed = score >= 0.75
    
    result = {
        'passed': passed,
        'score': score,
        'checks': checks
    }
    
    print(json.dumps(result))

if __name__ == '__main__':
    main()