import json
import os
import sys
import re
from datetime import datetime, timedelta

def check_growth_report(workspace_dir):
    checks = []
    
    # Check 1: Growth report file exists
    report_path = os.path.join(workspace_dir, 'growth_report.md')
    report_exists = os.path.exists(report_path)
    checks.append({
        'name': 'growth_report_file_exists',
        'passed': report_exists,
        'detail': f'Growth report file exists at {report_path}' if report_exists else 'Growth report file missing'
    })
    
    # Check 2: Summary JSON file exists
    summary_path = os.path.join(workspace_dir, 'summary.json')
    summary_exists = os.path.exists(summary_path)
    checks.append({
        'name': 'summary_json_exists',
        'passed': summary_exists,
        'detail': f'Summary JSON file exists at {summary_path}' if summary_exists else 'Summary JSON file missing'
    })
    
    if not report_exists:
        # If main report doesn't exist, check if it might be in a different location
        for file in os.listdir(workspace_dir):
            if file.endswith('.md') and 'report' in file.lower():
                report_path = os.path.join(workspace_dir, file)
                report_exists = True
                break
    
    report_content = ''
    if report_exists:
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                report_content = f.read().lower()
        except Exception as e:
            checks.append({
                'name': 'report_file_readable',
                'passed': False,
                'detail': f'Could not read report file: {str(e)}'
            })
            report_content = ''
    
    # Check 3: Report contains work summary section
    has_work_summary = any(phrase in report_content for phrase in [
        'work summary', 'summary of work', 'recent work', 'work overview'
    ])
    checks.append({
        'name': 'contains_work_summary',
        'passed': has_work_summary,
        'detail': 'Report contains work summary section' if has_work_summary else 'Missing work summary section'
    })
    
    # Check 4: Report identifies TypeScript improvement area
    typescript_mentioned = any(term in report_content for term in [
        'typescript', 'type safety', 'type guard', 'optional field', 'auth config'
    ])
    checks.append({
        'name': 'identifies_typescript_issues',
        'passed': typescript_mentioned,
        'detail': 'Report identifies TypeScript/type safety issues' if typescript_mentioned else 'Missing TypeScript improvement area'
    })
    
    # Check 5: Report identifies security/data handling issues
    security_mentioned = any(term in report_content for term in [
        'security', 'sensitive data', 'auth token', 'api key', 'console.log', 'data leak'
    ])
    checks.append({
        'name': 'identifies_security_issues',
        'passed': security_mentioned,
        'detail': 'Report identifies security/data handling concerns' if security_mentioned else 'Missing security improvement area'
    })
    
    # Check 6: Report mentions UI/component architecture
    ui_mentioned = any(term in report_content for term in [
        'component', 'ui', 'responsive', 'overflow', 'marketplace', 'layout'
    ])
    checks.append({
        'name': 'identifies_ui_issues',
        'passed': ui_mentioned,
        'detail': 'Report identifies UI/component architecture issues' if ui_mentioned else 'Missing UI/component improvement area'
    })
    
    # Check 7: Report contains improvement areas section
    has_improvement_areas = any(phrase in report_content for phrase in [
        'improvement area', 'areas for improvement', 'skill gap', 'recommendation'
    ])
    checks.append({
        'name': 'contains_improvement_areas',
        'passed': has_improvement_areas,
        'detail': 'Report contains improvement areas section' if has_improvement_areas else 'Missing improvement areas section'
    })
    
    # Check 8: Report contains strengths section
    has_strengths = any(phrase in report_content for phrase in [
        'strength', 'doing well', 'good practice', 'positive'
    ])
    checks.append({
        'name': 'contains_strengths',
        'passed': has_strengths,
        'detail': 'Report contains strengths section' if has_strengths else 'Missing strengths section'
    })
    
    # Check 9: Report contains action items
    has_actions = any(phrase in report_content for phrase in [
        'action item', 'next step', 'priority', 'todo', 'focus on'
    ])
    checks.append({
        'name': 'contains_action_items',
        'passed': has_actions,
        'detail': 'Report contains action items' if has_actions else 'Missing action items section'
    })
    
    # Check 10: Report contains learning resources
    has_resources = any(phrase in report_content for phrase in [
        'learning resource', 'article', 'hackernews', 'link', 'study'
    ])
    checks.append({
        'name': 'contains_learning_resources',
        'passed': has_resources,
        'detail': 'Report contains learning resources' if has_resources else 'Missing learning resources section'
    })
    
    # Check 11: Summary JSON is valid and contains required fields
    summary_valid = False
    summary_detail = 'Summary JSON file missing'
    
    if summary_exists:
        try:
            with open(summary_path, 'r', encoding='utf-8') as f:
                summary_data = json.load(f)
            
            required_fields = ['work_summary', 'improvement_areas', 'strengths', 'action_items']
            has_all_fields = all(field in summary_data for field in required_fields)
            
            if has_all_fields:
                # Check that arrays contain actual content
                improvement_areas_populated = isinstance(summary_data.get('improvement_areas'), list) and len(summary_data['improvement_areas']) > 0
                strengths_populated = isinstance(summary_data.get('strengths'), list) and len(summary_data['strengths']) > 0
                action_items_populated = isinstance(summary_data.get('action_items'), list) and len(summary_data['action_items']) > 0
                work_summary_populated = isinstance(summary_data.get('work_summary'), str) and len(summary_data['work_summary'].strip()) > 0
                
                summary_valid = improvement_areas_populated and strengths_populated and action_items_populated and work_summary_populated
                summary_detail = 'Summary JSON is valid and properly populated' if summary_valid else 'Summary JSON has required fields but some are empty or invalid types'
            else:
                missing_fields = [field for field in required_fields if field not in summary_data]
                summary_detail = f'Summary JSON missing required fields: {missing_fields}'
                
        except json.JSONDecodeError as e:
            summary_detail = f'Summary JSON is not valid JSON: {str(e)}'
        except Exception as e:
            summary_detail = f'Error reading summary JSON: {str(e)}'
    
    checks.append({
        'name': 'summary_json_valid',
        'passed': summary_valid,
        'detail': summary_detail
    })
    
    # Check 12: Report shows evidence from chat history
    has_evidence = any(phrase in report_content for phrase in [
        'observed', 'noticed', 'chat history', 'recent work', 'your work shows', 'evidence'
    ])
    checks.append({
        'name': 'contains_evidence_based_analysis',
        'passed': has_evidence,
        'detail': 'Report contains evidence-based analysis from chat history' if has_evidence else 'Report lacks evidence-based analysis'
    })
    
    return checks

def main():
    if len(sys.argv) != 2:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'args', 'passed': False, 'detail': 'Expected workspace directory argument'}]}))
        return
    
    workspace_dir = sys.argv[1]
    
    if not os.path.exists(workspace_dir):
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'workspace', 'passed': False, 'detail': 'Workspace directory does not exist'}]}))
        return
    
    checks = check_growth_report(workspace_dir)
    
    # Calculate score as ratio of passed checks
    passed_count = sum(1 for check in checks if check['passed'])
    total_count = len(checks)
    score = passed_count / total_count if total_count > 0 else 0.0
    
    # Overall pass if score is high enough (80% threshold for this complex task)
    overall_passed = score >= 0.8
    
    result = {
        'passed': overall_passed,
        'score': score,
        'checks': checks
    }
    
    print(json.dumps(result))

if __name__ == '__main__':
    main()