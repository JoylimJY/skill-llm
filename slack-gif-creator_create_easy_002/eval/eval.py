import os
import sys
from PIL import Image
import json

def main(workspace_path):
    checks = []
    
    # Check if output file exists
    gif_path = os.path.join(workspace_path, 'bouncing_ball.gif')
    if not os.path.exists(gif_path):
        checks.append({'name': 'file_exists', 'passed': False, 'detail': 'bouncing_ball.gif not found'})
        result = {'passed': False, 'score': 0.0, 'checks': checks}
        print(json.dumps(result))
        return
    
    checks.append({'name': 'file_exists', 'passed': True, 'detail': 'bouncing_ball.gif exists'})
    
    try:
        # Open and analyze the GIF
        with Image.open(gif_path) as img:
            # Check dimensions
            width, height = img.size
            correct_dimensions = width == 128 and height == 128
            checks.append({
                'name': 'dimensions', 
                'passed': correct_dimensions, 
                'detail': f'Dimensions: {width}x{height}, expected 128x128'
            })
            
            # Check if it's animated (has multiple frames)
            frame_count = 0
            try:
                while True:
                    img.seek(frame_count)
                    frame_count += 1
            except EOFError:
                pass
            
            is_animated = frame_count > 1
            checks.append({
                'name': 'animated', 
                'passed': is_animated, 
                'detail': f'Frame count: {frame_count}'
            })
            
            # Check file format
            is_gif = img.format == 'GIF'
            checks.append({
                'name': 'format', 
                'passed': is_gif, 
                'detail': f'Format: {img.format}'
            })
            
            # Check if frames contain red pixels (indicating red ball)
            has_red_content = False
            if is_animated and frame_count > 1:
                try:
                    img.seek(0)
                    frame = img.convert('RGB')
                    pixels = list(frame.getdata())
                    # Look for predominantly red pixels (R > G and R > B)
                    red_pixels = [p for p in pixels if p[0] > 150 and p[0] > p[1] + 50 and p[0] > p[2] + 50]
                    has_red_content = len(red_pixels) > 10
                except:
                    has_red_content = False
            
            checks.append({
                'name': 'red_content', 
                'passed': has_red_content, 
                'detail': f'Contains red pixels: {has_red_content}'
            })
            
    except Exception as e:
        checks.append({'name': 'file_readable', 'passed': False, 'detail': f'Error reading GIF: {str(e)}'})
    
    # Calculate score
    passed_count = sum(1 for c in checks if c['passed'])
    total_count = len(checks)
    score = passed_count / total_count if total_count > 0 else 0.0
    passed = score >= 0.8
    
    result = {
        'passed': passed,
        'score': score,
        'checks': checks
    }
    
    print(json.dumps(result))

if __name__ == '__main__':
    main(sys.argv[1])