import sys
import os
import json
from PIL import Image
import cv2
import numpy as np

def main(workspace_dir):
    checks = []
    
    # Check if enhanced file exists
    enhanced_path = os.path.join(workspace_dir, 'enhanced_screenshot.png')
    enhanced_exists = os.path.exists(enhanced_path)
    checks.append({
        'name': 'enhanced_file_exists',
        'passed': enhanced_exists,
        'detail': f'Enhanced file exists: {enhanced_exists}'
    })
    
    # Check if original file is preserved
    original_path = os.path.join(workspace_dir, 'input_screenshot.png')
    original_preserved = os.path.exists(original_path)
    checks.append({
        'name': 'original_file_preserved',
        'passed': original_preserved,
        'detail': f'Original file preserved: {original_preserved}'
    })
    
    if enhanced_exists and original_preserved:
        try:
            # Load both images
            original = cv2.imread(original_path)
            enhanced = cv2.imread(enhanced_path)
            
            if original is not None and enhanced is not None:
                # Check if enhanced image has different properties (indicating processing)
                original_gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
                enhanced_gray = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)
                
                # Calculate image sharpness using Laplacian variance
                original_sharpness = cv2.Laplacian(original_gray, cv2.CV_64F).var()
                enhanced_sharpness = cv2.Laplacian(enhanced_gray, cv2.CV_64F).var()
                
                sharpness_improved = bool(enhanced_sharpness > original_sharpness * 1.1)
                checks.append({
                    'name': 'sharpness_improved',
                    'passed': sharpness_improved,
                    'detail': f'Sharpness improved: {sharpness_improved} (original: {original_sharpness:.2f}, enhanced: {enhanced_sharpness:.2f})'
                })
                
                # Check if image dimensions are maintained or improved
                orig_h, orig_w = original.shape[:2]
                enh_h, enh_w = enhanced.shape[:2]
                dimensions_maintained = bool(enh_h >= orig_h and enh_w >= orig_w)
                checks.append({
                    'name': 'dimensions_maintained',
                    'passed': dimensions_maintained,
                    'detail': f'Dimensions maintained or improved: {dimensions_maintained} (original: {orig_w}x{orig_h}, enhanced: {enh_w}x{enh_h})'
                })
                
                # Check if the enhanced image is different from original
                images_different = bool(not np.array_equal(original, enhanced))
                checks.append({
                    'name': 'image_processed',
                    'passed': images_different,
                    'detail': f'Image was processed (different from original): {images_different}'
                })
            else:
                checks.append({
                    'name': 'images_readable',
                    'passed': False,
                    'detail': 'Could not read one or both image files'
                })
        except Exception as e:
            checks.append({
                'name': 'image_analysis',
                'passed': False,
                'detail': f'Error analyzing images: {str(e)}'
            })
    
    # Calculate score and overall pass
    score = sum(1 for c in checks if c['passed']) / len(checks)
    passed = score >= 0.8
    
    result = {
        'passed': passed,
        'score': score,
        'checks': checks
    }
    
    print(json.dumps(result))

if __name__ == '__main__':
    main(sys.argv[1])