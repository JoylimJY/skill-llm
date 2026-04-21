import sys
import os
import json
from PIL import Image
import glob

def check_enhancement_results(workspace_dir):
    os.chdir(workspace_dir)
    checks = []
    
    # Check 1: Screenshot image enhanced and upscaled
    screenshot_enhanced = False
    screenshot_dims_ok = False
    for file in glob.glob('*screenshot*enhanced*'):
        if os.path.exists(file):
            screenshot_enhanced = True
            try:
                with Image.open(file) as img:
                    width, height = img.size
                    if width >= 2560 and height >= 1440:
                        screenshot_dims_ok = True
            except Exception:
                pass
            break
    
    checks.append({
        'name': 'screenshot_enhanced_exists',
        'passed': screenshot_enhanced,
        'detail': f'Screenshot enhanced file exists: {screenshot_enhanced}'
    })
    
    checks.append({
        'name': 'screenshot_upscaled_correctly',
        'passed': screenshot_dims_ok,
        'detail': f'Screenshot upscaled to at least 2560x1440: {screenshot_dims_ok}'
    })
    
    # Check 2: Photo image enhanced (noise reduction)
    photo_enhanced = False
    for file in glob.glob('*photo*enhanced*'):
        if os.path.exists(file):
            photo_enhanced = True
            break
    
    checks.append({
        'name': 'photo_enhanced_exists',
        'passed': photo_enhanced,
        'detail': f'Photo enhanced file exists: {photo_enhanced}'
    })
    
    # Check 3: Logo converted to PNG format
    logo_png_created = False
    logo_format_correct = False
    for file in glob.glob('*logo*enhanced*'):
        if os.path.exists(file):
            logo_png_created = True
            if file.lower().endswith('.png'):
                logo_format_correct = True
            break
    
    checks.append({
        'name': 'logo_enhanced_exists',
        'passed': logo_png_created,
        'detail': f'Logo enhanced file exists: {logo_png_created}'
    })
    
    checks.append({
        'name': 'logo_png_format',
        'passed': logo_format_correct,
        'detail': f'Logo converted to PNG format: {logo_format_correct}'
    })
    
    # Check 4: Enhancement report exists
    report_exists = os.path.exists('enhancement_report.md')
    checks.append({
        'name': 'report_exists',
        'passed': report_exists,
        'detail': f'Enhancement report file exists: {report_exists}'
    })
    
    # Check 5: Report contains required information
    report_has_content = False
    if report_exists:
        try:
            with open('enhancement_report.md', 'r') as f:
                content = f.read().lower()
                if ('screenshot' in content and 'photo' in content and 
                    'logo' in content and 'dimensions' in content):
                    report_has_content = True
        except Exception:
            pass
    
    checks.append({
        'name': 'report_contains_details',
        'passed': report_has_content,
        'detail': f'Report contains image processing details: {report_has_content}'
    })
    
    # Check 6: Original files preserved
    originals_preserved = True
    expected_originals = ['app_screenshot.jpg', 'vacation_photo.png', 'company_logo.jpg', 'test_image.bmp']
    for orig_file in expected_originals:
        if not os.path.exists(orig_file):
            originals_preserved = False
            break
    
    checks.append({
        'name': 'originals_preserved',
        'passed': originals_preserved,
        'detail': f'Original files preserved: {originals_preserved}'
    })
    
    # Check 7: Enhanced files use correct naming convention
    naming_correct = True
    enhanced_files = glob.glob('*enhanced*')
    if len(enhanced_files) < 3:  # Should have at least 3 enhanced files
        naming_correct = False
    
    checks.append({
        'name': 'enhanced_file_naming',
        'passed': naming_correct,
        'detail': f'Enhanced files use correct naming convention: {naming_correct}'
    })
    
    # Calculate score
    score = sum(1 for c in checks if c['passed']) / len(checks)
    passed = score >= 0.8  # Allow some flexibility for hard task
    
    return {
        'passed': passed,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({'error': 'Usage: eval_script.py <workspace_dir>'}))
        sys.exit(1)
    
    result = check_enhancement_results(sys.argv[1])
    print(json.dumps(result))