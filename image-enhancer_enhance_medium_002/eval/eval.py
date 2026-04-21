import sys
import os
import json
from PIL import Image
import glob

def evaluate_enhancement(workspace_dir):
    os.chdir(workspace_dir)
    checks = []
    
    # Expected original files
    original_files = ['screenshot1.png', 'documentation_screenshot.png', 'web_interface.png']
    expected_enhanced = ['screenshot1-enhanced.png', 'documentation_screenshot-enhanced.png', 'web_interface-enhanced.png']
    
    # Check 1: Original files preserved
    originals_preserved = True
    for orig_file in original_files:
        if not os.path.exists(orig_file):
            originals_preserved = False
            break
    
    checks.append({
        'name': 'original_files_preserved',
        'passed': originals_preserved,
        'detail': f'Original PNG files preserved: {originals_preserved}'
    })
    
    # Check 2: Enhanced files created with correct naming
    enhanced_created = True
    enhanced_found = []
    
    for enhanced_file in expected_enhanced:
        if os.path.exists(enhanced_file):
            enhanced_found.append(enhanced_file)
        else:
            enhanced_created = False
    
    # Also check for any files with -enhanced pattern
    enhanced_pattern_files = glob.glob('*-enhanced.png')
    if len(enhanced_pattern_files) >= 3:
        enhanced_created = True
        enhanced_found = enhanced_pattern_files[:3]
    
    checks.append({
        'name': 'enhanced_files_created',
        'passed': enhanced_created,
        'detail': f'Enhanced files created: {len(enhanced_found)}/3 expected'
    })
    
    # Check 3: Enhanced images have different (usually larger) dimensions or file sizes
    dimension_improvements = 0
    size_improvements = 0
    
    if enhanced_created:
        for i, orig_file in enumerate(original_files):
            if os.path.exists(orig_file):
                # Find corresponding enhanced file
                enhanced_file = None
                base_name = orig_file.replace('.png', '')
                
                # Try exact expected name first
                expected_enhanced_name = f'{base_name}-enhanced.png'
                if os.path.exists(expected_enhanced_name):
                    enhanced_file = expected_enhanced_name
                else:
                    # Find any enhanced file that might correspond
                    for ef in enhanced_pattern_files:
                        if base_name in ef.lower() or any(part in ef.lower() for part in base_name.lower().split('_')):
                            enhanced_file = ef
                            break
                
                if enhanced_file and os.path.exists(enhanced_file):
                    try:
                        orig_img = Image.open(orig_file)
                        enhanced_img = Image.open(enhanced_file)
                        
                        orig_pixels = orig_img.size[0] * orig_img.size[1]
                        enhanced_pixels = enhanced_img.size[0] * enhanced_img.size[1]
                        
                        if enhanced_pixels >= orig_pixels:
                            dimension_improvements += 1
                        
                        orig_size = os.path.getsize(orig_file)
                        enhanced_size = os.path.getsize(enhanced_file)
                        
                        # Size might increase due to enhancement or decrease due to optimization
                        # Just check that file exists and is reasonable size
                        if enhanced_size > 1000:  # At least 1KB
                            size_improvements += 1
                            
                    except Exception as e:
                        pass
    
    dimension_check_passed = dimension_improvements >= 2  # At least 2 out of 3
    size_check_passed = size_improvements >= 2
    
    checks.append({
        'name': 'image_quality_improved',
        'passed': dimension_check_passed or size_check_passed,
        'detail': f'Images show signs of enhancement: {dimension_improvements} dimension improvements, {size_improvements} valid enhanced files'
    })
    
    # Check 4: Enhancement report created
    report_files = glob.glob('*report*.md') + glob.glob('*enhancement*.md') + glob.glob('*summary*.md')
    report_exists = len(report_files) > 0
    
    report_content_valid = False
    if report_exists:
        for report_file in report_files:
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                
                # Check for key content indicators
                has_dimensions = any(keyword in content for keyword in ['dimension', 'resolution', 'size', 'width', 'height'])
                has_filenames = any(filename.replace('.png', '').lower() in content for filename in original_files)
                has_enhanced_mention = any(keyword in content for keyword in ['enhanced', 'processed', 'improved'])
                
                if has_dimensions and (has_filenames or has_enhanced_mention):
                    report_content_valid = True
                    break
                    
            except Exception as e:
                pass
    
    checks.append({
        'name': 'report_created',
        'passed': report_exists,
        'detail': f'Enhancement report file created: {report_exists}'
    })
    
    checks.append({
        'name': 'report_content_valid',
        'passed': report_content_valid,
        'detail': f'Report contains expected content (dimensions, filenames): {report_content_valid}'
    })
    
    # Calculate score
    passed_checks = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_checks / total_checks
    overall_passed = score >= 0.8  # Allow some tolerance
    
    return {
        'passed': overall_passed,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    result = evaluate_enhancement(sys.argv[1])
    print(json.dumps(result))