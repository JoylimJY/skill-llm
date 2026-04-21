import sys
import os
import re

def evaluate_growth_report(workspace_dir):
    checks = []
    
    # Check if growth_report.md exists
    report_path = os.path.join(workspace_dir, 'growth_report.md')
    if os.path.exists(report_path):
        checks.append({"name": "Report file exists", "passed": True, "detail": "growth_report.md found"})
        
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read().lower()
            
        # Check for key sections
        has_title = any(keyword in content for keyword in ['developer growth report', 'growth report', 'development report'])
        checks.append({"name": "Report title present", "passed": has_title, "detail": "Found report title" if has_title else "No report title found"})
        
        has_summary = any(keyword in content for keyword in ['work summary', 'summary', 'recent work'])
        checks.append({"name": "Work summary section", "passed": has_summary, "detail": "Found work summary" if has_summary else "No work summary found"})
        
        has_improvements = any(keyword in content for keyword in ['improvement', 'areas', 'growth', 'development'])
        checks.append({"name": "Improvement areas section", "passed": has_improvements, "detail": "Found improvement areas" if has_improvements else "No improvement areas found"})
        
        # Check for technology mentions from chat history
        has_typescript = 'typescript' in content
        checks.append({"name": "TypeScript mentioned", "passed": has_typescript, "detail": "TypeScript referenced in analysis" if has_typescript else "TypeScript not mentioned"})
        
        has_react = 'react' in content
        checks.append({"name": "React mentioned", "passed": has_react, "detail": "React referenced in analysis" if has_react else "React not mentioned"})
        
        # Check for analysis depth
        has_specific_recommendations = any(keyword in content for keyword in ['recommend', 'suggestion', 'should', 'practice'])
        checks.append({"name": "Specific recommendations", "passed": has_specific_recommendations, "detail": "Found recommendations" if has_specific_recommendations else "No specific recommendations found"})
        
        # Check for evidence-based analysis
        has_observed_patterns = any(keyword in content for keyword in ['observed', 'noticed', 'pattern', 'struggle'])
        checks.append({"name": "Evidence-based observations", "passed": has_observed_patterns, "detail": "Found evidence-based observations" if has_observed_patterns else "No evidence-based observations found"})
        
    else:
        checks.append({"name": "Report file exists", "passed": False, "detail": "growth_report.md not found"})
        # Add failing checks for missing file
        for check_name in ["Report title present", "Work summary section", "Improvement areas section", "TypeScript mentioned", "React mentioned", "Specific recommendations", "Evidence-based observations"]:
            checks.append({"name": check_name, "passed": False, "detail": "File not found"})
    
    # Calculate score
    passed_count = sum(1 for c in checks if c['passed'])
    total_count = len(checks)
    score = passed_count / total_count if total_count > 0 else 0.0
    
    return {
        "passed": score >= 0.8,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    result = evaluate_growth_report(workspace_dir)
    print(result)