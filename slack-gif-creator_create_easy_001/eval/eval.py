#!/usr/bin/env python3
import sys
import os
import json
from PIL import Image
import imageio

def check_gif_creation(workspace_dir):
    checks = []
    
    # Check 1: File exists with correct name
    gif_path = os.path.join(workspace_dir, 'thumbs_pulse.gif')
    file_exists = os.path.exists(gif_path)
    checks.append({
        'name': 'File Creation',
        'passed': file_exists,
        'detail': f'thumbs_pulse.gif exists: {file_exists}'
    })
    
    if not file_exists:
        # If file doesn't exist, add placeholder checks
        checks.extend([
            {'name': 'File Size', 'passed': False, 'detail': 'File not found'},
            {'name': 'Dimensions', 'passed': False, 'detail': 'File not found'},
            {'name': 'Animation Frames', 'passed': False, 'detail': 'File not found'},
            {'name': 'Duration', 'passed': False, 'detail': 'File not found'}
        ])
        return checks
    
    try:
        # Check 2: File size (should be under 64KB for emoji)
        file_size = os.path.getsize(gif_path)
        size_ok = file_size <= 65536  # 64KB
        checks.append({
            'name': 'File Size',
            'passed': size_ok,
            'detail': f'Size: {file_size} bytes (limit: 65536)'
        })
        
        # Check 3: Dimensions (should be 128x128 or reasonable emoji size)
        with Image.open(gif_path) as img:
            width, height = img.size
            dims_ok = (width == 128 and height == 128) or (64 <= width <= 256 and 64 <= height <= 256)
            checks.append({
                'name': 'Dimensions',
                'passed': dims_ok,
                'detail': f'Dimensions: {width}x{height}'
            })
        
        # Check 4: Animation frames (should have multiple frames for animation)
        frames = imageio.mimread(gif_path)
        frame_count = len(frames)
        frames_ok = frame_count >= 5  # At least 5 frames for animation
        checks.append({
            'name': 'Animation Frames',
            'passed': frames_ok,
            'detail': f'Frame count: {frame_count}'
        })
        
        # Check 5: Duration (should be short for emoji, typically 1-3 seconds)
        # Estimate duration based on frame count and typical fps
        estimated_duration = frame_count / 10.0  # Assume ~10fps typical
        duration_ok = 0.5 <= estimated_duration <= 5.0  # Reasonable range
        checks.append({
            'name': 'Duration',
            'passed': duration_ok,
            'detail': f'Estimated duration: {estimated_duration:.1f}s'
        })
        
    except Exception as e:
        # If we can't analyze the file, it's likely corrupted
        checks.extend([
            {'name': 'File Size', 'passed': False, 'detail': f'Error reading file: {e}'},
            {'name': 'Dimensions', 'passed': False, 'detail': f'Error reading file: {e}'},
            {'name': 'Animation Frames', 'passed': False, 'detail': f'Error reading file: {e}'},
            {'name': 'Duration', 'passed': False, 'detail': f'Error reading file: {e}'}
        ])
    
    return checks

def main():
    if len(sys.argv) != 2:
        print(json.dumps({'error': 'Usage: eval_script.py <workspace_dir>'}))
        sys.exit(1)
    
    workspace_dir = sys.argv[1]
    checks = check_gif_creation(workspace_dir)
    
    # Calculate score as ratio of passed checks
    passed_count = sum(1 for c in checks if c['passed'])
    total_count = len(checks)
    score = passed_count / total_count if total_count > 0 else 0.0
    
    result = {
        'passed': score == 1.0,
        'score': score,
        'checks': checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()