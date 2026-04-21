#!/usr/bin/env python3
import sys
import os
import json
from PIL import Image

def check_rocket_launch_gif(workspace_dir):
    checks = []
    
    # Check 1: File exists and is named correctly
    gif_path = os.path.join(workspace_dir, 'rocket_launch.gif')
    file_exists = os.path.exists(gif_path)
    checks.append({
        'name': 'correct_filename',
        'passed': file_exists,
        'detail': f"File 'rocket_launch.gif' {'exists' if file_exists else 'not found'}"
    })
    
    if not file_exists:
        # Add remaining failed checks if file doesn't exist
        for check_name in ['file_size', 'dimensions', 'is_animated', 'has_multiple_frames']:
            checks.append({
                'name': check_name,
                'passed': False,
                'detail': 'Cannot check - file does not exist'
            })
        score = 0.0
        return {
            'passed': False,
            'score': score,
            'checks': checks
        }
    
    # Check 2: File size under 64KB (Slack emoji limit)
    file_size = os.path.getsize(gif_path)
    file_size_kb = file_size / 1024
    size_ok = file_size_kb <= 64
    checks.append({
        'name': 'file_size',
        'passed': size_ok,
        'detail': f"File size: {file_size_kb:.1f}KB ({'under' if size_ok else 'over'} 64KB limit)"
    })
    
    try:
        # Check 3: Dimensions are 128x128
        with Image.open(gif_path) as img:
            width, height = img.size
            dimensions_ok = width == 128 and height == 128
            checks.append({
                'name': 'dimensions',
                'passed': dimensions_ok,
                'detail': f"Dimensions: {width}x{height} ({'correct' if dimensions_ok else 'incorrect, should be 128x128'})"
            })
            
            # Check 4: Is animated GIF
            is_animated = getattr(img, 'is_animated', False)
            checks.append({
                'name': 'is_animated',
                'passed': is_animated,
                'detail': f"Animation: {'animated GIF' if is_animated else 'static image (should be animated)'}"
            })
            
            # Check 5: Has reasonable number of frames (at least 8 for a launch sequence)
            frame_count = 0
            if is_animated:
                try:
                    while True:
                        img.seek(frame_count)
                        frame_count += 1
                except EOFError:
                    pass
            
            has_enough_frames = frame_count >= 8
            checks.append({
                'name': 'has_multiple_frames',
                'passed': has_enough_frames,
                'detail': f"Frame count: {frame_count} frames ({'sufficient' if has_enough_frames else 'too few for launch sequence'})"
            })
            
    except Exception as e:
        # If we can't open the image, mark image-related checks as failed
        for check_name in ['dimensions', 'is_animated', 'has_multiple_frames']:
            checks.append({
                'name': check_name,
                'passed': False,
                'detail': f'Cannot check - error opening image: {str(e)}'
            })
    
    # Check 6: Look for validation output in any text files or stdout capture
    validation_found = False
    validation_detail = "No validation output found"
    
    # Look for any text files that might contain validation output
    for filename in os.listdir(workspace_dir):
        if filename.endswith('.txt') or filename.endswith('.log'):
            try:
                with open(os.path.join(workspace_dir, filename), 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    if any(keyword in content for keyword in ['slack', 'emoji', 'validation', '64kb', 'size', 'ready']):
                        validation_found = True
                        validation_detail = f"Validation output found in {filename}"
                        break
            except:
                pass
    
    checks.append({
        'name': 'validation_output',
        'passed': validation_found,
        'detail': validation_detail
    })
    
    # Calculate score
    passed_count = sum(1 for check in checks if check['passed'])
    total_count = len(checks)
    score = passed_count / total_count
    
    return {
        'passed': score >= 0.8,  # Allow passing if most checks pass
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: eval_script.py <workspace_dir>')
        sys.exit(1)
    
    workspace_dir = sys.argv[1]
    result = check_rocket_launch_gif(workspace_dir)
    print(json.dumps(result))