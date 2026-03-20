#!/usr/bin/env python3
import json
import sys
import subprocess
from pathlib import Path
import re

def run_eval(workspace_path):
    checks = []
    workspace = Path(workspace_path)
    
    # Load expected content markers
    marker_file = workspace / 'expected_content.json'
    if not marker_file.exists():
        return {"passed": False, "score": 0.0, "checks": [{"name": "marker_file", "passed": False, "detail": "Missing expected_content.json"}]}
    
    with open(marker_file) as f:
        expected = json.load(f)
    
    # Check if output presentation exists
    pptx_files = list(workspace.glob('*.pptx'))
    if not pptx_files:
        checks.append({"name": "output_exists", "passed": False, "detail": "No .pptx file found"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    output_file = pptx_files[0]
    checks.append({"name": "output_exists", "passed": True, "detail": f"Found {output_file.name}"})
    
    # Extract text content using markitdown
    try:
        result = subprocess.run([sys.executable, '-m', 'markitdown', str(output_file)], 
                              capture_output=True, text=True, cwd=workspace)
        if result.returncode != 0:
            checks.append({"name": "text_extraction", "passed": False, "detail": f"markitdown failed: {result.stderr}"})
            return {"passed": False, "score": 0.0, "checks": checks}
        
        content = result.stdout.lower()
        checks.append({"name": "text_extraction", "passed": True, "detail": "Successfully extracted text content"})
        
    except Exception as e:
        checks.append({"name": "text_extraction", "passed": False, "detail": f"Exception: {str(e)}"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    # Check for company name and quarter
    company_found = expected['company_name'].lower() in content
    checks.append({"name": "company_name", "passed": company_found, "detail": f"Company name {'found' if company_found else 'missing'}"})
    
    quarter_found = expected['quarter'].lower() in content
    checks.append({"name": "quarter", "passed": quarter_found, "detail": f"Quarter {'found' if quarter_found else 'missing'}"})
    
    # Check for key financial metrics
    revenue_found = str(expected['revenue_growth']) in content and 'revenue' in content
    checks.append({"name": "revenue_metric", "passed": revenue_found, "detail": f"Revenue growth metric {'found' if revenue_found else 'missing'}"})
    
    churn_found = str(expected['churn_rate']) in content and 'churn' in content
    checks.append({"name": "churn_metric", "passed": churn_found, "detail": f"Churn rate metric {'found' if churn_found else 'missing'}"})
    
    customers_found = str(expected['new_customers']) in content and 'customer' in content
    checks.append({"name": "customer_metric", "passed": customers_found, "detail": f"Customer acquisition metric {'found' if customers_found else 'missing'}"})
    
    # Check for team members
    team_count = sum(1 for member in expected['team_members'] if any(name.lower() in content for name in member.split(' - ')[0].split()))
    team_found = team_count >= 2
    checks.append({"name": "team_members", "passed": team_found, "detail": f"Found {team_count}/3 team members"})
    
    # Check for testimonial customers  
    testimonial_count = sum(1 for customer in expected['testimonial_customers'] if customer.lower() in content)
    testimonials_found = testimonial_count >= 2
    checks.append({"name": "testimonials", "passed": testimonials_found, "detail": f"Found {testimonial_count}/3 customer testimonials"})
    
    # Check for roadmap features
    roadmap_count = sum(1 for feature in expected['roadmap_features'] if any(word.lower() in content for word in feature.split()))
    roadmap_found = roadmap_count >= 3
    checks.append({"name": "roadmap_features", "passed": roadmap_found, "detail": f"Found {roadmap_count}/4 roadmap features"})
    
    # Count slides by checking slide markers in markitdown output
    slide_markers = len(re.findall(r'slide \d+', content, re.IGNORECASE))
    adequate_slides = slide_markers >= 7  # Should have at least 7-8 slides
    checks.append({"name": "slide_count", "passed": adequate_slides, "detail": f"Found {slide_markers} slides (need >=7)"})
    
    # Check for visual elements (images should be referenced)
    has_images = 'image' in content or 'photo' in content or len(list(workspace.glob('*.png'))) > 0
    checks.append({"name": "visual_elements", "passed": has_images, "detail": f"Visual elements {'found' if has_images else 'missing'}"})
    
    # Check that it's not just bullet points - look for varied content structure
    has_variety = any(keyword in content for keyword in ['chart', 'table', 'timeline', 'matrix', 'dashboard'])
    checks.append({"name": "layout_variety", "passed": has_variety, "detail": f"Layout variety {'found' if has_variety else 'missing'}"})
    
    # Calculate score
    passed_checks = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_checks / total_checks
    overall_passed = score >= 0.8  # Need 80% of checks to pass
    
    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "usage", "passed": False, "detail": "Usage: eval_script.py <workspace_path>"}]}))
        sys.exit(1)
    
    result = run_eval(sys.argv[1])
    print(json.dumps(result, indent=2))
