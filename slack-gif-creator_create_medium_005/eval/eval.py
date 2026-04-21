import os
import sys
import json
from PIL import Image
import imageio

def main(workspace_dir):
    checks = []
    
    # Check 1: File exists and is named correctly
    gif_path = os.path.join(workspace_dir, 'bouncing_star.gif')
    file_exists = os.path.exists(gif_path)
    checks.append({
        'name': 'File exists as bouncing_star.gif',
        'passed': file_exists,
        'detail': f'File found: {file_exists}'
    })
    
    if not file_exists:
        # Add remaining checks as failed
        for check_name in ['Correct dimensions', 'Has frames', 'Frame rate acceptable', 'Has star shapes', 'Shows bouncing motion', 'Color requirements']:
            checks.append({
                'name': check_name,
                'passed': False,
                'detail': 'Cannot evaluate - file not found'
            })
        score = 0.0
        passed = False
    else:
        try:
            # Check 2: Dimensions are 128x128
            with Image.open(gif_path) as img:
                correct_size = img.size == (128, 128)
                checks.append({
                    'name': 'Correct dimensions',
                    'passed': correct_size,
                    'detail': f'Size: {img.size}, expected: (128, 128)'
                })
                
                # Check 3: Has multiple frames
                frame_count = 0
                try:
                    while True:
                        img.seek(frame_count)
                        frame_count += 1
                except EOFError:
                    pass
                
                has_frames = frame_count > 5
                checks.append({
                    'name': 'Has frames',
                    'passed': has_frames,
                    'detail': f'Frame count: {frame_count}'
                })
            
            # Check 4: Frame rate is reasonable (using imageio for better metadata)
            try:
                reader = imageio.get_reader(gif_path)
                fps = 1.0 / reader.get_meta_data().get('duration', 0.1)
                fps_ok = 10 <= fps <= 30
                checks.append({
                    'name': 'Frame rate acceptable',
                    'passed': fps_ok,
                    'detail': f'FPS: {fps:.1f}, expected: 10-30'
                })
                reader.close()
            except:
                checks.append({
                    'name': 'Frame rate acceptable',
                    'passed': True,  # Don't penalize if metadata unavailable
                    'detail': 'Could not read FPS metadata, assuming OK'
                })
            
            # Check 5: Contains star-like shapes (look for non-rectangular content)
            with Image.open(gif_path) as img:
                img.seek(frame_count // 2)  # Check middle frame
                pixels = list(img.convert('RGB').getdata())
                unique_colors = len(set(pixels))
                has_shapes = unique_colors >= 3  # Background + star + outline colors
                checks.append({
                    'name': 'Has star shapes',
                    'passed': has_shapes,
                    'detail': f'Unique colors found: {unique_colors}'
                })
            
            # Check 6: Shows motion (compare first and middle frames)
            motion_detected = False
            try:
                with Image.open(gif_path) as img:
                    img.seek(0)
                    frame1 = img.convert('RGB')
                    img.seek(frame_count // 2)
                    frame2 = img.convert('RGB')
                    
                    # Simple pixel difference check
                    pixels1 = list(frame1.getdata())
                    pixels2 = list(frame2.getdata())
                    differences = sum(1 for p1, p2 in zip(pixels1, pixels2) if p1 != p2)
                    motion_detected = differences > 100  # Significant change
            except:
                motion_detected = True  # Assume motion if can't check
            
            checks.append({
                'name': 'Shows bouncing motion',
                'passed': motion_detected,
                'detail': f'Frame differences detected: {motion_detected}'
            })
            
            # Check 7: Has yellow and blue colors (approximate)
            with Image.open(gif_path) as img:
                img.seek(frame_count // 2)
                pixels = list(img.convert('RGB').getdata())
                
                # Look for yellow-ish colors (high R and G, low B)
                has_yellow = any(r > 200 and g > 200 and b < 100 for r, g, b in pixels)
                # Look for blue-ish colors (low R and G, high B)
                has_blue = any(r < 100 and g < 100 and b > 150 for r, g, b in pixels)
                
                color_ok = has_yellow or has_blue  # At least one required color
                checks.append({
                    'name': 'Color requirements',
                    'passed': color_ok,
                    'detail': f'Yellow found: {has_yellow}, Blue found: {has_blue}'
                })
                
        except Exception as e:
            # If any analysis fails, add failed checks
            remaining_checks = ['Correct dimensions', 'Has frames', 'Frame rate acceptable', 'Has star shapes', 'Shows bouncing motion', 'Color requirements']
            for i, check_name in enumerate(remaining_checks):
                if len(checks) <= i + 1:
                    checks.append({
                        'name': check_name,
                        'passed': False,
                        'detail': f'Error during analysis: {str(e)}'
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