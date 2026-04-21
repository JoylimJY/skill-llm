import os
import sys
import json
from PIL import Image
import glob

def check_image_enhancement(workspace_dir):
    checks = []
    
    # Check 1: Original files are preserved
    original_files = glob.glob(os.path.join(workspace_dir, '*.png'))
    original_pngs = [f for f in original_files if not f.endswith('-enhanced.png')]
    
    preserved_originals = len(original_pngs) >= 3
    checks.append({
        'name': 'Original files preserved',
        'passed': preserved_originals,
        'detail': f'Found {len(original_pngs)} original PNG files'
    })
    
    # Check 2: Enhanced files created with correct naming
    enhanced_files = glob.glob(os.path.join(workspace_dir, '*-enhanced.png'))
    correct_naming = len(enhanced_files) >= 3
    checks.append({
        'name': 'Enhanced files created with correct suffix',
        'passed': correct_naming,
        'detail': f'Found {len(enhanced_files)} enhanced files with "-enhanced" suffix'
    })
    
    # Check 3: Enhanced files have increased resolution
    upscaled_count = 0
    for enhanced_file in enhanced_files:
        try:
            with Image.open(enhanced_file) as img:
                width, height = img.size
                if width >= 2560 and height >= 1440:
                    upscaled_count += 1
                elif width >= 1920 or height >= 1080:  # Allow some flexibility
                    upscaled_count += 0.5
        except Exception:
            pass
    
    resolution_improved = upscaled_count >= 2
    checks.append({
        'name': 'Images upscaled to target resolution',
        'passed': resolution_improved,
        'detail': f'{upscaled_count} images meet or approach target resolution (2560x1440)'
    })
    
    # Check 4: Summary report exists
    report_files = []
    for pattern in ['*report*', '*summary*', '*.txt', '*.md']:
        report_files.extend(glob.glob(os.path.join(workspace_dir, pattern)))
    
    # Filter out image files
    report_files = [f for f in report_files if not f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    report_exists = len(report_files) > 0
    checks.append({
        'name': 'Summary report provided',
        'passed': report_exists,
        'detail': f'Found {len(report_files)} potential report files'
    })
    
    # Check 5: Report contains meaningful content
    report_has_content = False
    if report_files:
        for report_file in report_files:
            try:
                with open(report_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().lower()
                    keywords = ['enhanced', 'resolution', 'upscaled', 'improved', 'quality', 'screenshot']
                    if any(keyword in content for keyword in keywords) and len(content) > 50:
                        report_has_content = True
                        break
            except Exception:
                continue
    
    checks.append({
        'name': 'Report contains enhancement details',
        'passed': report_has_content,
        'detail': 'Report includes information about image improvements' if report_has_content else 'Report missing or lacks enhancement details'
    })
    
    # Calculate score
    passed_checks = sum(1 for check in checks if check['passed'])
    score = passed_checks / len(checks)
    overall_passed = score >= 0.8
    
    return {
        'passed': overall_passed,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    result = check_image_enhancement(workspace_dir)
    print(json.dumps(result))