import sys
import os
from PIL import Image, ImageSequence
import json

def main(workspace_dir):
    checks = []
    score = 0.0
    
    # Check if marker file exists (confirms gen_inputs ran)
    marker_path = os.path.join(workspace_dir, 'task_marker.txt')
    if os.path.exists(marker_path):
        with open(marker_path, 'r') as f:
            if 'slack-gif-bouncing-star-task-v1.2.3' in f.read():
                checks.append({'name': 'setup_verified', 'passed': True, 'detail': 'Task setup confirmed'})
            else:
                checks.append({'name': 'setup_verified', 'passed': False, 'detail': 'Invalid marker content'})
    else:
        checks.append({'name': 'setup_verified', 'passed': False, 'detail': 'Setup marker missing'})
    
    # Look for GIF files
    gif_files = [f for f in os.listdir(workspace_dir) if f.lower().endswith('.gif')]
    
    if not gif_files:
        checks.append({'name': 'gif_exists', 'passed': False, 'detail': 'No GIF file found'})
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': checks}))
        return
    
    checks.append({'name': 'gif_exists', 'passed': True, 'detail': f'Found {len(gif_files)} GIF file(s)'})
    score += 0.2
    
    # Check the main GIF (use first one found)
    gif_path = os.path.join(workspace_dir, gif_files[0])
    
    try:
        with Image.open(gif_path) as img:
            # Check dimensions (should be 128x128)
            if img.size == (128, 128):
                checks.append({'name': 'dimensions_correct', 'passed': True, 'detail': 'Dimensions are 128x128'})
                score += 0.2
            else:
                checks.append({'name': 'dimensions_correct', 'passed': False, 'detail': f'Dimensions are {img.size}, expected (128, 128)'})
            
            # Check if it's animated
            frame_count = 0
            for frame in ImageSequence.Iterator(img):
                frame_count += 1
            
            if frame_count > 1:
                checks.append({'name': 'is_animated', 'passed': True, 'detail': f'GIF has {frame_count} frames'})
                score += 0.2
            else:
                checks.append({'name': 'is_animated', 'passed': False, 'detail': 'GIF is not animated'})
            
            # Check duration (should be under 2 seconds)
            try:
                duration_ms = img.info.get('duration', 100) * frame_count
                duration_s = duration_ms / 1000.0
                if duration_s <= 2.0:
                    checks.append({'name': 'duration_check', 'passed': True, 'detail': f'Duration is {duration_s:.2f}s (under 2s)'})
                    score += 0.2
                else:
                    checks.append({'name': 'duration_check', 'passed': False, 'detail': f'Duration is {duration_s:.2f}s (over 2s limit)'})
            except:
                checks.append({'name': 'duration_check', 'passed': False, 'detail': 'Could not determine duration'})
            
            # Check for color variation (bouncing star should change colors)
            colors_found = set()
            frame_num = 0
            for frame in ImageSequence.Iterator(img):
                frame = frame.convert('RGB')
                # Sample some pixels to find non-background colors
                for x in range(0, 128, 16):
                    for y in range(0, 128, 16):
                        color = frame.getpixel((x, y))
                        if color != (240, 248, 255):  # Not background color
                            colors_found.add(color)
                frame_num += 1
                if frame_num >= 10:  # Don't check every frame for performance
                    break
            
            if len(colors_found) >= 3:
                checks.append({'name': 'color_variation', 'passed': True, 'detail': f'Found {len(colors_found)} different colors'})
                score += 0.2
            else:
                checks.append({'name': 'color_variation', 'passed': False, 'detail': f'Only found {len(colors_found)} colors, expected multiple for color-changing effect'})
            
            # Check file size (should be reasonable for Slack)
            file_size_kb = os.path.getsize(gif_path) / 1024
            if file_size_kb <= 500:  # Reasonable limit for Slack emoji
                checks.append({'name': 'file_size_check', 'passed': True, 'detail': f'File size is {file_size_kb:.1f}KB (reasonable for Slack)'})
                score += 0.2
            else:
                checks.append({'name': 'file_size_check', 'passed': False, 'detail': f'File size is {file_size_kb:.1f}KB (may be too large for Slack)'})
            
    except Exception as e:
        checks.append({'name': 'gif_analysis', 'passed': False, 'detail': f'Error analyzing GIF: {str(e)}'})
    
    passed = score >= 0.8  # Need 4 out of 6 main checks to pass
    print(json.dumps({'passed': passed, 'score': score, 'checks': checks}))

if __name__ == '__main__':
    main(sys.argv[1])