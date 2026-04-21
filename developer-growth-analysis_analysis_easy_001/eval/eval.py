import sys
import os
import json
import re

def evaluate_growth_report(workspace_dir):
    checks = []
    
    # Check if growth_report.md exists
    report_path = os.path.join(workspace_dir, 'growth_report.md')
    if not os.path.exists(report_path):
        checks.append({"name": "Report File Exists", "passed": False, "detail": "growth_report.md not found"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "Report File Exists", "passed": True, "detail": "growth_report.md found"})
    
    # Read the report content
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read().lower()
    
    # Check for required sections
    has_title = any(marker in content for marker in ['developer growth report', 'growth report', 'development report'])
    checks.append({"name": "Has Report Title", "passed": has_title, "detail": "Found report title" if has_title else "Missing report title"})
    
    has_work_summary = any(marker in content for marker in ['work summary', 'summary', 'overview'])
    checks.append({"name": "Has Work Summary", "passed": has_work_summary, "detail": "Found work summary section" if has_work_summary else "Missing work summary section"})
    
    has_improvement_areas = any(marker in content for marker in ['improvement areas', 'improvement', 'areas for improvement', 'growth areas'])
    checks.append({"name": "Has Improvement Areas", "passed": has_improvement_areas, "detail": "Found improvement areas section" if has_improvement_areas else "Missing improvement areas section"})
    
    has_strengths = any(marker in content for marker in ['strengths', 'strengths observed', 'what you do well'])
    checks.append({"name": "Has Strengths Section", "passed": has_strengths, "detail": "Found strengths section" if has_strengths else "Missing strengths section"})
    
    has_action_items = any(marker in content for marker in ['action items', 'action', 'next steps', 'recommendations'])
    checks.append({"name": "Has Action Items", "passed": has_action_items, "detail": "Found action items section" if has_action_items else "Missing action items section"})
    
    has_learning_resources = any(marker in content for marker in ['learning resources', 'resources', 'curated', 'articles'])
    checks.append({"name": "Has Learning Resources", "passed": has_learning_resources, "detail": "Found learning resources section" if has_learning_resources else "Missing learning resources section"})
    
    # Check for evidence of analysis based on mock data
    mentions_technologies = any(tech in content for tech in ['typescript', 'react', 'javascript', 'css', 'sql', 'database'])
    checks.append({"name": "Analyzes Technologies", "passed": mentions_technologies, "detail": "Found technology analysis" if mentions_technologies else "Missing technology analysis"})
    
    mentions_projects = any(proj in content for proj in ['ecommerce', 'backend', 'frontend', 'portfolio', 'analytics', 'service'])
    checks.append({"name": "Analyzes Projects", "passed": mentions_projects, "detail": "Found project analysis" if mentions_projects else "Missing project analysis"})
    
    # Check report structure and formatting
    has_markdown_headers = bool(re.search(r'#{1,6}\s+', content))
    checks.append({"name": "Uses Markdown Headers", "passed": has_markdown_headers, "detail": "Found markdown headers" if has_markdown_headers else "Missing markdown headers"})
    
    # Calculate score
    passed_checks = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_checks / total_checks
    overall_passed = score >= 0.7  # Allow for some flexibility
    
    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1]
    result = evaluate_growth_report(workspace_dir)
    print(json.dumps(result))