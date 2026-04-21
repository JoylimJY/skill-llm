import sys
import os
import json
from pathlib import Path

def evaluate_task(workspace_dir):
    workspace_path = Path(workspace_dir)
    checks = []
    
    # Check for design philosophy file
    philosophy_files = list(workspace_path.glob('*.md'))
    philosophy_found = False
    philosophy_content = ''
    
    for md_file in philosophy_files:
        if md_file.name.lower() in ['design_philosophy.md', 'philosophy.md'] or 'philosophy' in md_file.name.lower():
            philosophy_found = True
            try:
                philosophy_content = md_file.read_text(encoding='utf-8', errors='ignore').lower()
                break
            except:
                pass
    
    checks.append({
        'name': 'Design Philosophy File',
        'passed': philosophy_found,
        'detail': f'Found philosophy file: {philosophy_found}'
    })
    
    # Check philosophy content quality
    philosophy_quality = False
    if philosophy_content:
        quality_indicators = [
            any(word in philosophy_content for word in ['visual', 'space', 'form', 'composition']),
            any(word in philosophy_content for word in ['color', 'material', 'aesthetic', 'design']),
            any(word in philosophy_content for word in ['craftsmanship', 'meticulously', 'expert', 'master']),
            len(philosophy_content.split()) > 200  # Substantial content
        ]
        philosophy_quality = sum(quality_indicators) >= 3
    
    checks.append({
        'name': 'Philosophy Content Quality',
        'passed': philosophy_quality,
        'detail': f'Philosophy contains design principles and craftsmanship emphasis: {philosophy_quality}'
    })
    
    # Check for PNG output file
    png_files = list(workspace_path.glob('*.png'))
    png_found = False
    target_png = None
    
    for png_file in png_files:
        if 'liminal' in png_file.name.lower() or png_file.name.lower() == 'liminal_poster.png':
            png_found = True
            target_png = png_file
            break
    
    # If specific file not found, check for any substantial PNG
    if not png_found and png_files:
        for png_file in png_files:
            try:
                file_size = png_file.stat().st_size
                if file_size > 10000:  # At least 10KB for a meaningful image
                    png_found = True
                    target_png = png_file
                    break
            except:
                pass
    
    checks.append({
        'name': 'PNG Output File',
        'passed': png_found,
        'detail': f'Found PNG file: {png_found}'
    })
    
    # Check PNG file size (should be substantial for a quality poster)
    png_size_adequate = False
    if target_png:
        try:
            file_size = target_png.stat().st_size
            png_size_adequate = file_size > 50000  # At least 50KB for quality
        except:
            pass
    
    checks.append({
        'name': 'PNG File Size',
        'passed': png_size_adequate,
        'detail': f'PNG file has adequate size for poster: {png_size_adequate}'
    })
    
    # Check for liminal theme connection
    liminal_connection = False
    all_content = philosophy_content
    
    # Also check if there are any text files that might contain theme discussion
    for txt_file in workspace_path.glob('*.txt'):
        try:
            txt_content = txt_file.read_text(encoding='utf-8', errors='ignore').lower()
            all_content += ' ' + txt_content
        except:
            pass
    
    liminal_indicators = [
        'liminal' in all_content,
        any(word in all_content for word in ['threshold', 'transition', 'between']),
        any(word in all_content for word in ['space', 'empty', 'vacant']),
        any(word in all_content for word in ['uncanny', 'strange', 'familiar'])
    ]
    liminal_connection = sum(liminal_indicators) >= 2
    
    checks.append({
        'name': 'Liminal Theme Connection',
        'passed': liminal_connection,
        'detail': f'Content shows connection to liminal spaces theme: {liminal_connection}'
    })
    
    # Check for sophistication markers in philosophy
    sophistication = False
    if philosophy_content:
        sophistication_markers = [
            any(word in philosophy_content for word in ['museum', 'gallery', 'exhibition']),
            any(word in philosophy_content for word in ['minimalist', 'geometric', 'abstract']),
            any(word in philosophy_content for word in ['typography', 'composition', 'hierarchy']),
            len([w for w in philosophy_content.split() if len(w) > 8]) > 20  # Complex vocabulary
        ]
        sophistication = sum(sophistication_markers) >= 2
    
    checks.append({
        'name': 'Sophisticated Design Approach',
        'passed': sophistication,
        'detail': f'Philosophy demonstrates sophisticated design thinking: {sophistication}'
    })
    
    # Calculate final score
    passed_checks = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_checks / total_checks
    overall_passed = score >= 0.8
    
    result = {
        'passed': overall_passed,
        'score': score,
        'checks': checks
    }
    
    print(json.dumps(result, indent=2))
    return result

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: eval_script.py <workspace_directory>')
        sys.exit(1)
    
    workspace_dir = sys.argv[1]
    evaluate_task(workspace_dir)