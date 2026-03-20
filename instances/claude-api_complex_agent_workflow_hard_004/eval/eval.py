#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path
import subprocess

def check_file_exists(filepath):
    """Check if a file exists and return details"""
    path = Path(filepath)
    if path.exists():
        return True, f"File exists: {filepath} ({path.stat().st_size} bytes)"
    else:
        return False, f"File missing: {filepath}"

def check_json_structure(filepath, required_keys):
    """Check if JSON file has required structure"""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            return False, f"Missing required keys: {missing_keys}"
        
        return True, f"JSON structure valid with keys: {list(data.keys())}"
    except Exception as e:
        return False, f"JSON parsing error: {str(e)}"

def check_pdf_exists(filepath):
    """Check if PDF file exists and has reasonable size"""
    path = Path(filepath)
    if not path.exists():
        return False, f"PDF file missing: {filepath}"
    
    size = path.stat().st_size
    if size < 1000:  # Less than 1KB is suspicious
        return False, f"PDF file too small: {size} bytes"
    
    return True, f"PDF file exists: {filepath} ({size} bytes)"

def check_investment_report_content(filepath):
    """Check if investment report has required analysis components"""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        checks = []
        
        # Check for sentiment analysis
        if 'sentiment_analysis' in data:
            if isinstance(data['sentiment_analysis'], dict) and 'overall_sentiment' in data['sentiment_analysis']:
                checks.append("✓ Sentiment analysis present")
            else:
                checks.append("✗ Sentiment analysis incomplete")
        else:
            checks.append("✗ Sentiment analysis missing")
        
        # Check for financial metrics
        if 'financial_metrics' in data or 'financial_analysis' in data:
            checks.append("✓ Financial analysis present")
        else:
            checks.append("✗ Financial analysis missing")
        
        # Check for recommendation
        rec_found = False
        for key in ['recommendation', 'investment_recommendation', 'conclusion']:
            if key in data:
                rec_data = data[key]
                if isinstance(rec_data, dict) and ('action' in rec_data or 'recommendation' in rec_data):
                    rec_found = True
                    break
        
        if rec_found:
            checks.append("✓ Investment recommendation present")
        else:
            checks.append("✗ Investment recommendation missing")
        
        # Check for confidence scores
        confidence_found = any('confidence' in str(data).lower() for _ in [1])
        if confidence_found:
            checks.append("✓ Confidence scores present")
        else:
            checks.append("✗ Confidence scores missing")
        
        return len([c for c in checks if c.startswith('✓')]) >= 3, "; ".join(checks)
    
    except Exception as e:
        return False, f"Error analyzing report content: {str(e)}"

def check_marker_preservation():
    """Check if original marker content is preserved in analysis"""
    markers_found = []
    
    # Check for evidence of processing original data
    files_to_check = ['investment_report.json']
    
    for filepath in files_to_check:
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                
                # Look for evidence that original data was processed
                if 'tesla' in content.lower() or 'TSLA' in content:
                    markers_found.append(f"Tesla data referenced in {filepath}")
                
                if any(term in content.lower() for term in ['q4', 'earnings', 'revenue', 'deliveries']):
                    markers_found.append(f"Financial data processed in {filepath}")
                
                if any(term in content.lower() for term in ['positive', 'negative', 'sentiment']):
                    markers_found.append(f"Sentiment analysis in {filepath}")
            
            except Exception:
                pass
    
    return len(markers_found) >= 2, f"Found: {'; '.join(markers_found)}"

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: eval_script.py <workspace_path>"}))
        sys.exit(1)
    
    workspace_path = sys.argv[1]
    os.chdir(workspace_path)
    
    checks = []
    
    # Check 1: Investment report JSON exists and has structure
    passed, detail = check_file_exists('investment_report.json')
    checks.append({"name": "investment_report_exists", "passed": passed, "detail": detail})
    
    if passed:
        required_keys = ['sentiment_analysis', 'financial_analysis', 'recommendation']
        # Be flexible with key names
        passed, detail = check_json_structure('investment_report.json', [])
        checks.append({"name": "investment_report_structure", "passed": passed, "detail": detail})
        
        # Check report content quality
        passed, detail = check_investment_report_content('investment_report.json')
        checks.append({"name": "investment_report_content", "passed": passed, "detail": detail})
    
    # Check 2: PDF report exists
    passed, detail = check_pdf_exists('market_analysis_report.pdf')
    checks.append({"name": "pdf_report_exists", "passed": passed, "detail": detail})
    
    # Check 3: Evidence of multi-tool usage (charts, analysis files)
    chart_files = list(Path('.').glob('*.png')) + list(Path('.').glob('*.jpg')) + list(Path('.').glob('charts/*.png'))
    if chart_files:
        checks.append({"name": "visualizations_created", "passed": True, "detail": f"Found {len(chart_files)} chart files"})
    else:
        checks.append({"name": "visualizations_created", "passed": False, "detail": "No chart/visualization files found"})
    
    # Check 4: Original data processing
    passed, detail = check_marker_preservation()
    checks.append({"name": "original_data_processed", "passed": passed, "detail": detail})
    
    # Check 5: Evidence of code execution (intermediate files, analysis outputs)
    analysis_files = [f for f in os.listdir('.') if f.endswith(('.json', '.csv', '.txt')) and f not in ['tesla_news.json', 'tesla_financials.json', 'tesla_stock_history.json', 'analysis_requirements.json']]
    if len(analysis_files) >= 2:
        checks.append({"name": "intermediate_analysis_files", "passed": True, "detail": f"Found analysis files: {', '.join(analysis_files[:3])}"})
    else:
        checks.append({"name": "intermediate_analysis_files", "passed": False, "detail": f"Only found {len(analysis_files)} analysis files"})
    
    # Calculate overall score
    passed_checks = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_checks / total_checks
    
    # Overall pass requires key deliverables + evidence of complex workflow
    overall_passed = (
        any(c['name'] == 'investment_report_exists' and c['passed'] for c in checks) and
        any(c['name'] == 'pdf_report_exists' and c['passed'] for c in checks) and
        any(c['name'] == 'investment_report_content' and c['passed'] for c in checks) and
        score >= 0.6
    )
    
    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()