import sys
import os
from PIL import Image

def check_gif_properties(workspace_path):
    checks = []
    gif_path = os.path.join(workspace_path, 'bouncing_ball.gif')
    
    # Check if file exists
    file_exists = os.path.exists(gif_path)
    checks.append({
        'name': 'file_exists',
        'passed': file_exists,
        'detail': f'bouncing_ball.gif exists: {file_exists}'
    })
    
    if not file_exists:
        return checks
    
    try:
        # Open and analyze the GIF
        with Image.open(gif_path) as img:
            # Check if it's animated
            is_animated = hasattr(img, 'is_animated') and img.is_animated
            checks.append({
                'name': 'is_animated',
                'passed': is_animated,
                'detail': f'GIF is animated: {is_animated}'
            })
            
            # Check dimensions (should be 128x128 for emoji)
            width, height = img.size
            correct_dimensions = width == 128 and height == 128
            checks.append({
                'name': 'correct_dimensions',
                'passed': correct_dimensions,
                'detail': f'Dimensions are {width}x{height}, expected 128x128: {correct_dimensions}'
            })
            
            # Check number of frames (should have multiple for animation)
            frame_count = 0
            try:
                while True:
                    img.seek(frame_count)
                    frame_count += 1
            except EOFError:
                pass
            
            has_multiple_frames = frame_count > 1
            checks.append({
                'name': 'multiple_frames',
                'passed': has_multiple_frames,
                'detail': f'Has {frame_count} frames, multiple frames: {has_multiple_frames}'
            })
            
            # Check duration (should be under 3 seconds)
            try:
                total_duration = 0
                img.seek(0)
                for i in range(frame_count):
                    img.seek(i)
                    duration = img.info.get('duration', 100)  # default 100ms if not specified
                    total_duration += duration
                
                total_duration_seconds = total_duration / 1000.0
                duration_ok = total_duration_seconds <= 3.0
                checks.append({
                    'name': 'duration_under_3_seconds',
                    'passed': duration_ok,
                    'detail': f'Total duration: {total_duration_seconds:.2f}s, under 3s: {duration_ok}'
                })
            except Exception as e:
                checks.append({
                    'name': 'duration_under_3_seconds',
                    'passed': False,
                    'detail': f'Could not check duration: {str(e)}'
                })
            
            # Check file size (reasonable for Slack)
            file_size = os.path.getsize(gif_path)
            size_reasonable = file_size < 1024 * 1024  # Under 1MB
            checks.append({
                'name': 'reasonable_file_size',
                'passed': size_reasonable,
                'detail': f'File size: {file_size} bytes, under 1MB: {size_reasonable}'
            })
            
    except Exception as e:
        checks.append({
            'name': 'gif_readable',
            'passed': False,
            'detail': f'Could not read GIF file: {str(e)}'
        })
    
    return checks

def main():
    workspace_path = sys.argv[1] if len(sys.argv) > 1 else '.'
    checks = check_gif_properties(workspace_path)
    
    score = sum(1 for c in checks if c['passed']) / len(checks)
    passed = score >= 0.8  # Allow some tolerance for minor issues
    
    result = {
        'passed': passed,
        'score': score,
        'checks': checks
    }
    
    print(result)

if __name__ == '__main__':
    main()