import sys
import os
import json
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches
from pptx.dml.color import RGBColor
import re

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def check_presentation_structure(pptx_path):
    """Check if presentation has required slides and structure"""
    try:
        prs = Presentation(pptx_path)
        slide_count = len(prs.slides)
        
        # Should have 12 slides as requested
        if slide_count < 10:
            return False, f"Expected at least 10 slides, found {slide_count}"
        
        # Check for required content keywords across slides
        required_keywords = ['TechFlow Dynamics', 'brand', 'color', 'typography', 'logo']
        found_keywords = set()
        
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, 'text') and shape.text:
                    text_lower = shape.text.lower()
                    for keyword in required_keywords:
                        if keyword.lower() in text_lower:
                            found_keywords.add(keyword)
        
        missing_keywords = set(required_keywords) - found_keywords
        if missing_keywords:
            return False, f"Missing required content keywords: {missing_keywords}"
        
        return True, f"Found {slide_count} slides with required content"
    except Exception as e:
        return False, f"Error reading presentation: {str(e)}"

def check_theme_application(pptx_path):
    """Check if a consistent theme has been applied"""
    try:
        prs = Presentation(pptx_path)
        
        # Check for consistent colors across slides
        colors_used = set()
        fonts_used = set()
        
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, 'text_frame'):
                    for paragraph in shape.text_frame.paragraphs:
                        for run in paragraph.runs:
                            if hasattr(run.font, 'name') and run.font.name:
                                fonts_used.add(run.font.name)
                            if hasattr(run.font, 'color') and run.font.color.rgb:
                                colors_used.add(str(run.font.color.rgb))
        
        # Should have limited, consistent color palette (max 6-8 colors)
        if len(colors_used) > 10:
            return False, f"Too many colors used ({len(colors_used)}), theme not consistently applied"
        
        # Should have consistent font usage (max 3-4 fonts)
        if len(fonts_used) > 5:
            return False, f"Too many fonts used ({len(fonts_used)}), theme not consistently applied"
        
        return True, f"Consistent theme applied with {len(colors_used)} colors and {len(fonts_used)} fonts"
    except Exception as e:
        return False, f"Error checking theme application: {str(e)}"

def check_custom_theme_creation(workspace_dir):
    """Check if a custom theme was created for TechFlow Dynamics"""
    themes_dir = Path(workspace_dir) / 'themes'
    
    # Look for new theme files beyond the original 3
    theme_files = list(themes_dir.glob('*.json')) if themes_dir.exists() else []
    
    if len(theme_files) <= 3:
        return False, "No custom theme appears to have been created"
    
    # Check if any new theme file contains tech/flow related naming or colors
    for theme_file in theme_files:
        if theme_file.name not in ['ocean_depths.json', 'tech_innovation.json', 'modern_minimalist.json']:
            try:
                with open(theme_file) as f:
                    theme_data = json.load(f)
                    theme_name = theme_data.get('name', '').lower()
                    if 'tech' in theme_name or 'flow' in theme_name or 'innovation' in theme_name or 'dynamic' in theme_name:
                        return True, f"Custom theme '{theme_data.get('name')}' created for TechFlow Dynamics"
            except:
                continue
    
    return True, "Custom theme creation attempted"

def check_brand_guide_completeness(pptx_path):
    """Check if the brand guide covers all requested sections"""
    try:
        prs = Presentation(pptx_path)
        
        required_sections = [
            'techflow dynamics',
            'company overview', 
            'brand essence',
            'color palette',
            'typography',
            'logo usage',
            'imagery',
            'tone of voice',
            'applications',
            'contact'
        ]
        
        all_text = ''
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, 'text') and shape.text:
                    all_text += shape.text.lower() + ' '
        
        found_sections = 0
        for section in required_sections:
            if section in all_text:
                found_sections += 1
        
        completeness_score = found_sections / len(required_sections)
        
        if completeness_score >= 0.7:
            return True, f"Brand guide covers {found_sections}/{len(required_sections)} required sections"
        else:
            return False, f"Brand guide incomplete: only {found_sections}/{len(required_sections)} sections found"
    
    except Exception as e:
        return False, f"Error checking brand guide completeness: {str(e)}"

def main():
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    workspace_path = Path(workspace_dir)
    
    checks = []
    total_score = 0
    max_score = 4
    
    # Find presentation file
    pptx_files = list(workspace_path.glob('*.pptx'))
    if not pptx_files:
        checks.append({
            'name': 'presentation_exists',
            'passed': False,
            'detail': 'No PowerPoint presentation file found'
        })
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': checks}))
        return
    
    pptx_path = pptx_files[0]
    
    # Check 1: Presentation structure and content
    passed, detail = check_presentation_structure(pptx_path)
    checks.append({
        'name': 'presentation_structure',
        'passed': passed,
        'detail': detail
    })
    if passed:
        total_score += 1
    
    # Check 2: Theme application
    passed, detail = check_theme_application(pptx_path)
    checks.append({
        'name': 'theme_application',
        'passed': passed,
        'detail': detail
    })
    if passed:
        total_score += 1
    
    # Check 3: Custom theme creation
    passed, detail = check_custom_theme_creation(workspace_dir)
    checks.append({
        'name': 'custom_theme_creation',
        'passed': passed,
        'detail': detail
    })
    if passed:
        total_score += 1
    
    # Check 4: Brand guide completeness
    passed, detail = check_brand_guide_completeness(pptx_path)
    checks.append({
        'name': 'brand_guide_completeness',
        'passed': passed,
        'detail': detail
    })
    if passed:
        total_score += 1
    
    final_score = total_score / max_score
    overall_passed = final_score >= 0.75
    
    print(json.dumps({
        'passed': overall_passed,
        'score': final_score,
        'checks': checks
    }))

if __name__ == '__main__':
    main()