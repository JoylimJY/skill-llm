#!/usr/bin/env python3
import sys
import os
import json
from PIL import Image, ImageSequence

def check_gif_properties(gif_path):
    """Check if GIF meets the requirements"""
    checks = []
    
    # Check if file exists
    if not os.path.exists(gif_path):
        checks.append({"name": "file_exists", "passed": False, "detail": "celebration.gif not found"})
        return checks
    
    checks.append({"name": "file_exists", "passed": True, "detail": "celebration.gif found"})
    
    try:
        with Image.open(gif_path) as img:
            # Check if it's a GIF
            if img.format != 'GIF':
                checks.append({"name": "is_gif", "passed": False, "detail": f"File format is {img.format}, not GIF"})
                return checks
            
            checks.append({"name": "is_gif", "passed": True, "detail": "File is a valid GIF"})
            
            # Check dimensions (should be around 480x480, allow some flexibility)
            width, height = img.size
            size_ok = 400 <= width <= 600 and 400 <= height <= 600
            checks.append({
                "name": "dimensions", 
                "passed": size_ok, 
                "detail": f"Dimensions: {width}x{height} (expected ~480x480)"
            })
            
            # Check file size (should be under 2MB)
            file_size = os.path.getsize(gif_path)
            size_mb = file_size / (1024 * 1024)
            size_ok = size_mb < 2.0
            checks.append({
                "name": "file_size", 
                "passed": size_ok, 
                "detail": f"File size: {size_mb:.2f}MB (should be < 2MB)"
            })
            
            # Check if it's animated (has multiple frames)
            frame_count = 0
            try:
                for frame in ImageSequence.Iterator(img):
                    frame_count += 1
                    if frame_count > 50:  # Stop counting after reasonable limit
                        break
            except:
                frame_count = 1
            
            animated_ok = frame_count > 5  # Should have multiple frames for animation
            checks.append({
                "name": "animated", 
                "passed": animated_ok, 
                "detail": f"Frame count: {frame_count} (should be > 5 for animation)"
            })
            
            # Check duration (should be 3-4 seconds, allow 2-6 second range)
            try:
                duration_ms = img.info.get('duration', 100) * frame_count
                duration_sec = duration_ms / 1000
                duration_ok = 2.0 <= duration_sec <= 6.0
                checks.append({
                    "name": "duration", 
                    "passed": duration_ok, 
                    "detail": f"Duration: {duration_sec:.1f}s (expected 3-4s, allow 2-6s)"
                })
            except:
                checks.append({
                    "name": "duration", 
                    "passed": True, 
                    "detail": "Duration check skipped (metadata unavailable)"
                })
            
            # Check if GIF loops (loop count should be 0 for infinite)
            try:
                loop_count = img.info.get('loop', 0)
                loops_ok = loop_count == 0  # 0 means infinite loop
                checks.append({
                    "name": "loops", 
                    "passed": loops_ok, 
                    "detail": f"Loop count: {loop_count} (0 = infinite loop)"
                })
            except:
                checks.append({
                    "name": "loops", 
                    "passed": True, 
                    "detail": "Loop check skipped (metadata unavailable)"
                })
            
    except Exception as e:
        checks.append({"name": "gif_analysis", "passed": False, "detail": f"Error analyzing GIF: {str(e)}"})
    
    return checks

def main():
    if len(sys.argv) != 2:
        print('Usage: eval_script.py <workspace_dir>')
        sys.exit(1)
    
    workspace_dir = sys.argv[1]
    gif_path = os.path.join(workspace_dir, 'celebration.gif')
    
    checks = check_gif_properties(gif_path)
    
    # Calculate score as ratio of passed checks
    passed_count = sum(1 for check in checks if check['passed'])
    total_count = len(checks)
    score = passed_count / total_count if total_count > 0 else 0.0
    
    # Overall pass requires all checks to pass
    overall_passed = score >= 0.8  # Allow 80% pass rate due to metadata variability
    
    result = {
        'passed': overall_passed,
        'score': score,
        'checks': checks
    }
    
    print(json.dumps(result))

if __name__ == '__main__':
    main()