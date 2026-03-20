#!/usr/bin/env python3
import sys
import os
import json
from PIL import Image

def evaluate(workspace_dir):
    checks = []
    score = 0.0
    
    # Check if any GIF file exists
    gif_files = [f for f in os.listdir(workspace_dir) if f.lower().endswith('.gif')]
    
    if not gif_files:
        checks.append({"name": "gif_exists", "passed": False, "detail": "No GIF file found"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    gif_path = os.path.join(workspace_dir, gif_files[0])
    checks.append({"name": "gif_exists", "passed": True, "detail": f"Found GIF: {gif_files[0]}"})
    score += 0.2
    
    try:
        with Image.open(gif_path) as gif:
            # Check dimensions (should be 128x128)
            width, height = gif.size
            if width == 128 and height == 128:
                checks.append({"name": "dimensions", "passed": True, "detail": f"Correct dimensions: {width}x{height}"})
                score += 0.3
            else:
                checks.append({"name": "dimensions", "passed": False, "detail": f"Wrong dimensions: {width}x{height}, expected 128x128"})
            
            # Check if animated (has multiple frames)
            frame_count = 0
            try:
                while True:
                    gif.seek(frame_count)
                    frame_count += 1
            except EOFError:
                pass
            
            if frame_count > 1:
                checks.append({"name": "animated", "passed": True, "detail": f"Animated with {frame_count} frames"})
                score += 0.3
            else:
                checks.append({"name": "animated", "passed": False, "detail": "GIF is not animated (only 1 frame)"})
            
            # Check duration (should be under 3 seconds)
            if hasattr(gif, 'info') and 'duration' in gif.info:
                frame_duration = gif.info.get('duration', 100)  # default 100ms
                total_duration = (frame_count * frame_duration) / 1000.0  # convert to seconds
                if total_duration <= 3.0:
                    checks.append({"name": "duration", "passed": True, "detail": f"Duration: {total_duration:.2f}s (under 3s)"})
                    score += 0.2
                else:
                    checks.append({"name": "duration", "passed": False, "detail": f"Duration: {total_duration:.2f}s (over 3s limit)"})
            else:
                checks.append({"name": "duration", "passed": True, "detail": "Duration info not available, assuming compliant"})
                score += 0.1
    
    except Exception as e:
        checks.append({"name": "gif_valid", "passed": False, "detail": f"Error reading GIF: {str(e)}"})
        return {"passed": False, "score": score, "checks": checks}
    
    checks.append({"name": "gif_valid", "passed": True, "detail": "GIF file is valid and readable"})
    
    passed = score >= 0.8
    return {"passed": passed, "score": score, "checks": checks}

if __name__ == "__main__":
    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))