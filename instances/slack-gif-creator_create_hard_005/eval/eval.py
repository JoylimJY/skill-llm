import sys
import os
import json
from PIL import Image, ImageSequence
import imageio.v2 as imageio
import numpy as np

def evaluate_gif(workspace_path):
    checks = []
    
    # Check if requirements file exists
    req_file = os.path.join(workspace_path, 'task_requirements.json')
    if not os.path.exists(req_file):
        return {'passed': False, 'score': 0.0, 'checks': [{'name': 'requirements_file', 'passed': False, 'detail': 'Task requirements file missing'}]}
    
    with open(req_file, 'r') as f:
        requirements = json.load(f)
    
    # Look for GIF files
    gif_files = [f for f in os.listdir(workspace_path) if f.lower().endswith('.gif')]
    
    if not gif_files:
        checks.append({'name': 'gif_exists', 'passed': False, 'detail': 'No GIF file found'})
        return {'passed': False, 'score': 0.0, 'checks': checks}
    
    gif_path = os.path.join(workspace_path, gif_files[0])
    checks.append({'name': 'gif_exists', 'passed': True, 'detail': f'Found GIF: {gif_files[0]}'})
    
    try:
        # Load and analyze the GIF
        with Image.open(gif_path) as img:
            frames = []
            durations = []
            
            for frame in ImageSequence.Iterator(img):
                frames.append(np.array(frame.convert('RGB')))
                durations.append(frame.info.get('duration', 100))
            
            num_frames = len(frames)
            width, height = img.size
            total_duration = sum(durations) / 1000.0  # Convert to seconds
            
            # Check dimensions (should be emoji-sized)
            correct_size = (width == 128 and height == 128)
            checks.append({'name': 'emoji_dimensions', 'passed': correct_size, 'detail': f'Size: {width}x{height}, expected: 128x128'})
            
            # Check duration
            duration_ok = total_duration <= 2.7  # Allow slight margin
            checks.append({'name': 'duration_limit', 'passed': duration_ok, 'detail': f'Duration: {total_duration:.2f}s, limit: 2.5s'})
            
            # Check minimum frame count (should have enough frames for complex animation)
            min_frames = num_frames >= 15
            checks.append({'name': 'sufficient_frames', 'passed': min_frames, 'detail': f'Frames: {num_frames}, minimum expected: 15'})
            
            # Analyze for star-like shapes by looking for bright regions
            star_detected = False
            color_variety = False
            motion_detected = False
            
            # Check for bright regions (stars) and color changes
            frame_brightnesses = []
            frame_colors = []
            centroids = []
            
            for i, frame in enumerate(frames):
                # Find bright regions
                gray = np.mean(frame, axis=2)
                bright_threshold = np.mean(gray) + np.std(gray)
                bright_mask = gray > bright_threshold
                
                if np.sum(bright_mask) > 50:  # Sufficient bright pixels
                    star_detected = True
                    
                    # Calculate centroid of bright regions
                    y_coords, x_coords = np.where(bright_mask)
                    if len(y_coords) > 0:
                        centroid_y = np.mean(y_coords)
                        centroid_x = np.mean(x_coords)
                        centroids.append((centroid_x, centroid_y))
                
                # Track color variety
                mean_color = np.mean(frame.reshape(-1, 3), axis=0)
                frame_colors.append(mean_color)
                frame_brightnesses.append(np.mean(frame))
            
            checks.append({'name': 'star_detection', 'passed': star_detected, 'detail': f'Bright star-like regions detected: {star_detected}'})
            
            # Check for color variation (cycling colors)
            if len(frame_colors) > 1:
                color_changes = np.std(frame_colors, axis=0)
                color_variety = np.mean(color_changes) > 10  # Reasonable color variation
            
            checks.append({'name': 'color_cycling', 'passed': color_variety, 'detail': f'Color variation detected: {color_variety}'})
            
            # Check for motion (position changes)
            if len(centroids) > 3:
                distances = []
                for i in range(1, len(centroids)):
                    dist = np.sqrt((centroids[i][0] - centroids[i-1][0])**2 + (centroids[i][1] - centroids[i-1][1])**2)
                    distances.append(dist)
                
                motion_detected = len([d for d in distances if d > 2]) > 2  # Multiple significant movements
            
            checks.append({'name': 'motion_animation', 'passed': motion_detected, 'detail': f'Motion detected: {motion_detected}'})
            
            # Check file size (should be optimized)
            file_size = os.path.getsize(gif_path)
            size_ok = file_size < 500000  # 500KB limit for well-optimized emoji
            checks.append({'name': 'file_size_optimization', 'passed': size_ok, 'detail': f'File size: {file_size} bytes, should be under 500KB'})
            
    except Exception as e:
        checks.append({'name': 'gif_analysis', 'passed': False, 'detail': f'Error analyzing GIF: {str(e)}'})
        return {'passed': False, 'score': 0.0, 'checks': checks}
    
    # Calculate score
    passed_checks = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    
    # Must pass critical checks to be considered successful
    critical_checks = ['gif_exists', 'emoji_dimensions', 'star_detection', 'motion_animation']
    critical_passed = all(any(check['name'] == crit and check['passed'] for check in checks) for crit in critical_checks)
    
    return {
        'passed': critical_passed and score >= 0.7,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    workspace_path = sys.argv[1] if len(sys.argv) > 1 else '.'
    result = evaluate_gif(workspace_path)
    print(json.dumps(result, indent=2))