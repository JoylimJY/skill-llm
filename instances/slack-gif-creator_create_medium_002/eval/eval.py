import sys
import os
from PIL import Image, ImageSequence
import json

def eval_gif(workspace_path):
    checks = []
    score = 0.0
    
    # Check for marker file
    marker_path = os.path.join(workspace_path, 'animation_requirements.txt')
    if not os.path.exists(marker_path):
        checks.append({"name": "marker_file", "passed": False, "detail": "Animation requirements file missing"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    with open(marker_path, 'r') as f:
        content = f.read()
        if 'TASK_MARKER_STAR_BOUNCE_SPIN' not in content:
            checks.append({"name": "marker_content", "passed": False, "detail": "Invalid marker content"})
            return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "marker_validation", "passed": True, "detail": "Marker file valid"})
    score += 0.1
    
    # Find GIF files
    gif_files = [f for f in os.listdir(workspace_path) if f.lower().endswith('.gif')]
    
    if not gif_files:
        checks.append({"name": "gif_exists", "passed": False, "detail": "No GIF file found"})
        return {"passed": False, "score": score, "checks": checks}
    
    checks.append({"name": "gif_exists", "passed": True, "detail": f"Found GIF: {gif_files[0]}"})
    score += 0.2
    
    # Analyze the GIF
    gif_path = os.path.join(workspace_path, gif_files[0])
    
    try:
        with Image.open(gif_path) as img:
            # Check if it's animated
            frame_count = 0
            durations = []
            
            for frame in ImageSequence.Iterator(img):
                frame_count += 1
                durations.append(frame.info.get('duration', 100))
            
            if frame_count < 5:
                checks.append({"name": "animation_frames", "passed": False, "detail": f"Only {frame_count} frames, needs more for smooth animation"})
            else:
                checks.append({"name": "animation_frames", "passed": True, "detail": f"{frame_count} frames detected"})
                score += 0.2
            
            # Check duration (should be under 2 seconds)
            total_duration_ms = sum(durations)
            total_duration_s = total_duration_ms / 1000.0
            
            if total_duration_s <= 2.0:
                checks.append({"name": "duration_check", "passed": True, "detail": f"Duration: {total_duration_s:.1f}s (under 2s requirement)"})
                score += 0.2
            else:
                checks.append({"name": "duration_check", "passed": False, "detail": f"Duration: {total_duration_s:.1f}s (exceeds 2s requirement)"})
            
            # Check dimensions (should be reasonable for emoji)
            width, height = img.size
            if width == height and 64 <= width <= 256:
                checks.append({"name": "dimensions", "passed": True, "detail": f"Square dimensions {width}x{height} suitable for emoji"})
                score += 0.2
            else:
                checks.append({"name": "dimensions", "passed": False, "detail": f"Dimensions {width}x{height} not ideal for emoji"})
            
            # Check for color variety (indicates colorful design)
            first_frame = img.convert('RGB')
            colors = first_frame.getcolors(maxcolors=256*256*256)
            unique_colors = len(colors) if colors else 0
            
            if unique_colors > 10:
                checks.append({"name": "colorful", "passed": True, "detail": f"{unique_colors} unique colors detected"})
                score += 0.1
            else:
                checks.append({"name": "colorful", "passed": False, "detail": f"Only {unique_colors} colors, needs more variety"})
            
    except Exception as e:
        checks.append({"name": "gif_analysis", "passed": False, "detail": f"Error analyzing GIF: {str(e)}"})
        return {"passed": False, "score": score, "checks": checks}
    
    # Final assessment
    passed = score >= 0.8
    
    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "usage", "passed": False, "detail": "Usage: eval_script.py <workspace_path>"}]}))
        sys.exit(1)
    
    result = eval_gif(sys.argv[1])
    print(json.dumps(result))