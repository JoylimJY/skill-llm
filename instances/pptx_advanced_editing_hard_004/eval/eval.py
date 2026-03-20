#!/usr/bin/env python3
import sys
import json
import subprocess
from pathlib import Path
import pandas as pd
from xml.etree import ElementTree as ET
import zipfile
import re

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "Expected workspace directory argument"}]}))
        return
    
    workspace_dir = Path(sys.argv[1])
    checks = []
    total_score = 0.0
    max_score = 100.0
    
    # Find output presentation file
    pptx_files = list(workspace_dir.glob('*.pptx'))
    output_files = [f for f in pptx_files if f.name not in ['corporate_template.pptx']]
    
    if not output_files:
        checks.append({"name": "output_exists", "passed": False, "detail": "No output .pptx file found (excluding template)"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return
    
    output_file = output_files[0]
    checks.append({"name": "output_exists", "passed": True, "detail": f"Found output file: {output_file.name}"})
    total_score += 10
    
    # Extract text content for marker verification
    try:
        result = subprocess.run(['python', '-m', 'markitdown', str(output_file)], 
                              capture_output=True, text=True, cwd=workspace_dir)
        if result.returncode != 0:
            checks.append({"name": "text_extraction", "passed": False, "detail": f"Failed to extract text: {result.stderr}"})
            print(json.dumps({"passed": False, "score": total_score/max_score, "checks": checks}))
            return
        
        text_content = result.stdout.lower()
        checks.append({"name": "text_extraction", "passed": True, "detail": "Successfully extracted text content"})
        total_score += 10
        
    except Exception as e:
        checks.append({"name": "text_extraction", "passed": False, "detail": f"Error extracting text: {str(e)}"})
        print(json.dumps({"passed": False, "score": total_score/max_score, "checks": checks}))
        return
    
    # Check for content integration from all source files
    content_checks = [
        ("company_overview", "company_marker_12345", "Company overview content from overview.txt"),
        ("team_profiles", "dr. sarah chen", "Team member information from team_profiles.json"),
        ("market_analysis", "market_marker_98765", "Market analysis from market_research.docx"),
        ("financial_data", "financial_marker_67890", "Financial data from quarterly_data.csv")
    ]
    
    content_score = 0
    for check_name, marker, description in content_checks:
        if marker in text_content:
            checks.append({"name": check_name, "passed": True, "detail": f"Found {description}"})
            content_score += 15
        else:
            checks.append({"name": check_name, "passed": False, "detail": f"Missing {description}"})
    
    total_score += content_score
    
    # Check that placeholder content was removed
    placeholder_markers = [
        "template_marker_11111",
        "placeholder_marker_22222", 
        "section_marker_33333",
        "chart_marker_44444",
        "xxxx company presentation xxxx"
    ]
    
    placeholder_removed = True
    for marker in placeholder_markers:
        if marker in text_content:
            placeholder_removed = False
            break
    
    if placeholder_removed:
        checks.append({"name": "placeholders_removed", "passed": True, "detail": "All template placeholders were removed"})
        total_score += 10
    else:
        checks.append({"name": "placeholders_removed", "passed": False, "detail": "Some template placeholder content remains"})
    
    # Check slide count (should have multiple slides for a complete pitch deck)
    try:
        with zipfile.ZipFile(output_file, 'r') as zip_file:
            presentation_xml = zip_file.read('ppt/presentation.xml').decode('utf-8')
            slide_count = presentation_xml.count('<p:sldId')
            
        if slide_count >= 8:  # Expecting at least 8 slides for a complete pitch deck
            checks.append({"name": "slide_count", "passed": True, "detail": f"Presentation has {slide_count} slides"})
            total_score += 15
        else:
            checks.append({"name": "slide_count", "passed": False, "detail": f"Only {slide_count} slides - expected at least 8 for complete pitch deck"})
            
    except Exception as e:
        checks.append({"name": "slide_count", "passed": False, "detail": f"Could not verify slide count: {str(e)}"})
    
    # Check for brand color usage (forest green #2C5F2D)
    try:
        with zipfile.ZipFile(output_file, 'r') as zip_file:
            color_found = False
            # Check various slide files for the brand color
            for file_name in zip_file.namelist():
                if file_name.startswith('ppt/slides/slide') and file_name.endswith('.xml'):
                    content = zip_file.read(file_name).decode('utf-8')
                    # Look for hex color values (various formats)
                    if '2C5F2D' in content.upper() or '2c5f2d' in content.lower():
                        color_found = True
                        break
                        
        if color_found:
            checks.append({"name": "brand_colors", "passed": True, "detail": "Brand colors (forest green) found in presentation"})
            total_score += 10
        else:
            checks.append({"name": "brand_colors", "passed": False, "detail": "Brand colors not detected - may be using default template colors"})
            
    except Exception as e:
        checks.append({"name": "brand_colors", "passed": False, "detail": f"Could not verify brand colors: {str(e)}"})
    
    # Check for required slide types/content
    required_content = [
        ("funding", ["15m", "series a"], "Funding ask slide"),
        ("team", ["ceo", "cto"], "Team introduction slide"), 
        ("financial", ["revenue", "quarter"], "Financial projections slide"),
        ("competitive", ["tesla", "competitor"], "Competitive analysis slide")
    ]
    
    for content_type, keywords, description in required_content:
        found = any(keyword in text_content for keyword in keywords)
        if found:
            checks.append({"name": f"content_{content_type}", "passed": True, "detail": f"Found {description}"})
            total_score += 5
        else:
            checks.append({"name": f"content_{content_type}", "passed": False, "detail": f"Missing {description}"})
    
    # Final validation
    final_score = min(total_score / max_score, 1.0)
    passed = final_score >= 0.7  # Need 70% to pass
    
    result = {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()