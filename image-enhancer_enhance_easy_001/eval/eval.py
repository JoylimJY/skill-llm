import os
import sys
from PIL import Image
import json

def evaluate_image_enhancement(workspace_dir):
    checks = []
    
    # Check if original file exists
    input_path = os.path.join(workspace_dir, 'input_screenshot.png')
    checks.append({
        'name': 'original_file_exists',
        'passed': os.path.exists(input_path),
        'detail': f'Original file input_screenshot.png exists: {os.path.exists(input_path)}'
    })
    
    # Check if enhanced file was created
    enhanced_path = os.path.join(workspace_dir, 'enhanced_screenshot.png')
    enhanced_exists = os.path.exists(enhanced_path)
    checks.append({
        'name': 'enhanced_file_created',
        'passed': enhanced_exists,
        'detail': f'Enhanced file enhanced_screenshot.png created: {enhanced_exists}'
    })
    
    if enhanced_exists and os.path.exists(input_path):
        try:
            # Load both images
            original_img = Image.open(input_path)
            enhanced_img = Image.open(enhanced_path)
            
            # Check if resolution was improved (upscaled)
            orig_size = original_img.size
            enhanced_size = enhanced_img.size
            resolution_improved = (enhanced_size[0] >= orig_size[0] and enhanced_size[1] >= orig_size[1]) and (enhanced_size[0] > orig_size[0] or enhanced_size[1] > orig_size[1])
            
            checks.append({
                'name': 'resolution_upscaled',
                'passed': resolution_improved,
                'detail': f'Resolution improved from {orig_size} to {enhanced_size}: {resolution_improved}'
            })
            
            # Check file format is still PNG
            is_png = enhanced_img.format == 'PNG'
            checks.append({
                'name': 'correct_format',
                'passed': is_png,
                'detail': f'Enhanced image is PNG format: {is_png}'
            })
            
            # Check that enhancement was actually performed (file size or quality difference)
            orig_file_size = os.path.getsize(input_path)
            enhanced_file_size = os.path.getsize(enhanced_path)
            # Enhanced image should be different (usually larger due to upscaling)
            size_changed = abs(enhanced_file_size - orig_file_size) > 1000
            
            checks.append({
                'name': 'image_modified',
                'passed': size_changed,
                'detail': f'Image was modified (size changed from {orig_file_size} to {enhanced_file_size}): {size_changed}'
            })
            
        except Exception as e:
            checks.append({
                'name': 'image_processing_error',
                'passed': False,
                'detail': f'Error processing images: {str(e)}'
            })
    
    # Calculate final score
    passed_checks = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    
    return {
        'passed': score >= 0.8,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    result = evaluate_image_enhancement(workspace_dir)
    print(json.dumps(result))