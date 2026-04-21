import os
import sys
import json
import re
from pathlib import Path

def evaluate_task(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    
    # Check 1: Design philosophy markdown file exists
    philosophy_files = list(workspace.glob('*.md'))
    philosophy_exists = len(philosophy_files) > 0
    checks.append({
        'name': 'design_philosophy_file_exists',
        'passed': philosophy_exists,
        'detail': f'Found {len(philosophy_files)} .md files' if philosophy_exists else 'No .md files found'
    })
    
    # Check 2: PDF output file exists
    pdf_files = list(workspace.glob('*.pdf'))
    pdf_exists = len(pdf_files) > 0
    checks.append({
        'name': 'pdf_output_exists',
        'passed': pdf_exists,
        'detail': f'Found {len(pdf_files)} PDF files' if pdf_exists else 'No PDF files found'
    })
    
    # Check 3: Analyze philosophy content quality
    philosophy_quality = False
    philosophy_detail = 'No philosophy content found'
    if philosophy_files:
        for phil_file in philosophy_files:
            try:
                content = phil_file.read_text(encoding='utf-8').lower()
                # Look for design philosophy indicators
                design_terms = ['visual', 'form', 'color', 'composition', 'space', 'aesthetic', 'design', 'philosophy']
                craft_terms = ['craftsman', 'expert', 'meticulou', 'precision', 'master']
                
                design_score = sum(1 for term in design_terms if term in content)
                craft_score = sum(1 for term in craft_terms if term in content)
                word_count = len(content.split())
                
                if design_score >= 4 and craft_score >= 1 and word_count >= 200:
                    philosophy_quality = True
                    philosophy_detail = f'Quality philosophy with {design_score} design terms, {craft_score} craftsmanship terms, {word_count} words'
                    break
                else:
                    philosophy_detail = f'Philosophy needs improvement: {design_score} design terms, {craft_score} craft terms, {word_count} words'
            except Exception as e:
                philosophy_detail = f'Error reading philosophy: {str(e)}'
    
    checks.append({
        'name': 'philosophy_content_quality',
        'passed': philosophy_quality,
        'detail': philosophy_detail
    })
    
    # Check 4: PDF file size indicates substantial visual content
    pdf_substantial = False
    pdf_detail = 'No PDF to analyze'
    if pdf_files:
        for pdf_file in pdf_files:
            try:
                file_size = pdf_file.stat().st_size
                if file_size > 10000:  # At least 10KB suggests visual content
                    pdf_substantial = True
                    pdf_detail = f'PDF file size {file_size} bytes indicates visual content'
                    break
                else:
                    pdf_detail = f'PDF file size {file_size} bytes too small for visual design'
            except Exception as e:
                pdf_detail = f'Error analyzing PDF: {str(e)}'
    
    checks.append({
        'name': 'pdf_substantial_content',
        'passed': pdf_substantial,
        'detail': pdf_detail
    })
    
    # Check 5: Algorithmic nature theme relevance in philosophy
    theme_relevance = False
    theme_detail = 'Theme not found'
    if philosophy_files:
        for phil_file in philosophy_files:
            try:
                content = phil_file.read_text(encoding='utf-8').lower()
                theme_keywords = ['algorithm', 'computational', 'organic', 'nature', 'growth', 'pattern', 'digital', 'natural', 'process', 'system']
                theme_matches = sum(1 for keyword in theme_keywords if keyword in content)
                
                if theme_matches >= 3:
                    theme_relevance = True
                    theme_detail = f'Found {theme_matches} theme-relevant terms'
                    break
                else:
                    theme_detail = f'Only {theme_matches} theme-relevant terms found'
            except Exception as e:
                theme_detail = f'Error checking theme: {str(e)}'
    
    checks.append({
        'name': 'algorithmic_nature_theme',
        'passed': theme_relevance,
        'detail': theme_detail
    })
    
    # Calculate score and overall pass
    score = sum(1 for c in checks if c['passed']) / len(checks)
    passed = score >= 0.8
    
    return {
        'passed': passed,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    result = evaluate_task(sys.argv[1])
    print(json.dumps(result))