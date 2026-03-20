#!/usr/bin/env python3
import sys
import os
import json
from PIL import Image
import math

def evaluate_gif(workspace_path):
    checks = []
    
    # Look for GIF files
    gif_files = [f for f in os.listdir(workspace_path) if f.endswith('.gif')]
    
    if not gif_files:
        checks.append({"name": "gif_exists", "passed": False, "detail": "No GIF file found"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    gif_path = os.path.join(workspace_path, gif_files[0])
    checks.append({"name": "gif_exists", "passed": True, "detail": f"Found GIF: {gif_files[0]}"})
    
    try:
        # Open and analyze the GIF
        with Image.open(gif_path) as gif:
            # Check dimensions (should be emoji size)
            width, height = gif.size
            if width == 128 and height == 128:
                checks.append({"name": "emoji_dimensions", "passed": True, "detail": "128x128 dimensions correct"})
            else:
                checks.append({"name": "emoji_dimensions", "passed": False, "detail": f"Expected 128x128, got {width}x{height}"})
            
            # Check if it's animated
            frame_count = 0
            try:
                while True:
                    gif.seek(frame_count)
                    frame_count += 1
            except EOFError:
                pass
            
            if frame_count >= 10:
                checks.append({"name": "animation_frames", "passed": True, "detail": f"Has {frame_count} frames"})
            else:
                checks.append({"name": "animation_frames", "passed": False, "detail": f"Only {frame_count} frames, expected 10+"})
            
            # Check duration (should be under 3 seconds for emoji)
            try:
                duration = gif.info.get('duration', 100)
                total_duration = (duration * frame_count) / 1000.0
                if total_duration <= 3.0:
                    checks.append({"name": "duration_limit", "passed": True, "detail": f"Duration {total_duration:.2f}s <= 3s"})
                else:
                    checks.append({"name": "duration_limit", "passed": False, "detail": f"Duration {total_duration:.2f}s > 3s"})
            except:
                checks.append({"name": "duration_limit", "passed": True, "detail": "Duration check skipped"})
            
            # Analyze frames for motion/animation complexity
            has_motion = False
            color_variety = set()
            
            for i in range(min(frame_count, 10)):  # Check first 10 frames
                try:
                    gif.seek(i)
                    frame = gif.convert('RGB')
                    
                    # Sample colors from frame
                    for x in range(0, width, 16):
                        for y in range(0, height, 16):
                            color = frame.getpixel((x, y))
                            color_variety.add(color)
                    
                    # Check for non-uniform content (indicates graphics/motion)
                    if i > 0:
                        prev_frame = gif.convert('RGB')
                        gif.seek(i-1)
                        prev_frame = gif.convert('RGB')
                        gif.seek(i)
                        
                        # Simple motion detection - compare corner pixels
                        corners = [(0, 0), (width-1, 0), (0, height-1), (width-1, height-1)]
                        differences = 0
                        for corner in corners:
                            if frame.getpixel(corner) != prev_frame.getpixel(corner):
                                differences += 1
                        if differences > 0:
                            has_motion = True
                            break
                            
                except Exception as e:
                    continue
            
            if has_motion or len(color_variety) > 10:
                checks.append({"name": "visual_complexity", "passed": True, "detail": f"Detected motion/variety with {len(color_variety)} colors"})
            else:
                checks.append({"name": "visual_complexity", "passed": False, "detail": "Animation appears too simple"})
            
            # Check file size (should be reasonable for Slack)
            file_size = os.path.getsize(gif_path)
            if file_size < 1024 * 1024:  # Under 1MB
                checks.append({"name": "file_size", "passed": True, "detail": f"File size {file_size} bytes is reasonable"})
            else:
                checks.append({"name": "file_size", "passed": False, "detail": f"File size {file_size} bytes may be too large"})
    
    except Exception as e:
        checks.append({"name": "gif_analysis", "passed": False, "detail": f"Error analyzing GIF: {str(e)}"})
    
    # Calculate score
    passed_checks = sum(1 for check in checks if check["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    
    return {
        "passed": score >= 0.7,  # Need 70% of checks to pass
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace_path = sys.argv[1]
    result = evaluate_gif(workspace_path)
    print(json.dumps(result))