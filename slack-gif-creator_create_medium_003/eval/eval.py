#!/usr/bin/env python3
import os
import sys
import json
from PIL import Image

def main(workspace_dir):
    checks = []
    
    # Check 1: GIF file exists with correct name
    gif_path = os.path.join(workspace_dir, 'loading-success.gif')
    file_exists = os.path.exists(gif_path)
    checks.append({
        "name": "GIF file exists with correct filename",
        "passed": file_exists,
        "detail": f"Found loading-success.gif: {file_exists}"
    })
    
    if not file_exists:
        # If file doesn't exist, check for other GIF files
        gif_files = [f for f in os.listdir(workspace_dir) if f.endswith('.gif')]
        if gif_files:
            gif_path = os.path.join(workspace_dir, gif_files[0])
            checks[-1]["detail"] += f" (Found alternative: {gif_files[0]})"
    
    # Check 2: File size under 64KB (Slack emoji limit)
    size_valid = False
    file_size = 0
    if os.path.exists(gif_path):
        file_size = os.path.getsize(gif_path)
        size_valid = file_size <= 65536  # 64KB in bytes
    
    checks.append({
        "name": "File size under 64KB for Slack emoji",
        "passed": size_valid,
        "detail": f"File size: {file_size} bytes (limit: 65536)"
    })
    
    # Check 3: Image dimensions are appropriate (around 128x128)
    dimensions_valid = False
    width, height = 0, 0
    if os.path.exists(gif_path):
        try:
            with Image.open(gif_path) as img:
                width, height = img.size
                # Allow some flexibility in dimensions but prefer square format
                dimensions_valid = (100 <= width <= 150 and 100 <= height <= 150)
        except Exception as e:
            pass
    
    checks.append({
        "name": "Appropriate dimensions for emoji",
        "passed": dimensions_valid,
        "detail": f"Dimensions: {width}x{height} (expected around 128x128)"
    })
    
    # Check 4: GIF is actually animated (has multiple frames)
    is_animated = False
    frame_count = 0
    if os.path.exists(gif_path):
        try:
            with Image.open(gif_path) as img:
                frame_count = getattr(img, 'n_frames', 1)
                is_animated = frame_count > 1
        except Exception as e:
            pass
    
    checks.append({
        "name": "GIF is animated with multiple frames",
        "passed": is_animated,
        "detail": f"Frame count: {frame_count}"
    })
    
    # Check 5: Duration is reasonable (2-4 seconds for loading + success)
    duration_valid = False
    total_duration = 0
    if os.path.exists(gif_path) and is_animated:
        try:
            with Image.open(gif_path) as img:
                durations = []
                for i in range(frame_count):
                    img.seek(i)
                    duration = img.info.get('duration', 100)  # Default 100ms if not specified
                    durations.append(duration)
                total_duration = sum(durations) / 1000.0  # Convert to seconds
                duration_valid = 1.5 <= total_duration <= 4.0  # Allow some flexibility
        except Exception as e:
            pass
    
    checks.append({
        "name": "Animation duration is reasonable (1.5-4 seconds)",
        "passed": duration_valid,
        "detail": f"Total duration: {total_duration:.2f} seconds"
    })
    
    # Check 6: Frame rate is appropriate (8-15 fps for emoji)
    fps_valid = False
    calculated_fps = 0
    if total_duration > 0 and frame_count > 0:
        calculated_fps = frame_count / total_duration
        fps_valid = 8 <= calculated_fps <= 15
    
    checks.append({
        "name": "Frame rate is appropriate for emoji GIF",
        "passed": fps_valid,
        "detail": f"Calculated FPS: {calculated_fps:.1f} (expected 8-15)"
    })
    
    # Calculate score
    passed_count = sum(1 for check in checks if check['passed'])
    score = passed_count / len(checks)
    overall_passed = score >= 0.8  # Allow some tolerance
    
    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: eval_script.py <workspace_dir>")
        sys.exit(1)
    main(sys.argv[1])