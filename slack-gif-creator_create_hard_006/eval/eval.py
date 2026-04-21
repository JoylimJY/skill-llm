import os
import sys
import json
from PIL import Image
import math

def evaluate_bouncing_star_gif(workspace_dir):
    checks = []
    
    # Check if the GIF file exists
    gif_path = os.path.join(workspace_dir, 'bouncing_star.gif')
    if not os.path.exists(gif_path):
        checks.append({"name": "File Exists", "passed": False, "detail": "bouncing_star.gif not found"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "File Exists", "passed": True, "detail": "bouncing_star.gif found"})
    
    try:
        with Image.open(gif_path) as gif:
            # Check dimensions
            width, height = gif.size
            dimension_correct = width == 128 and height == 128
            checks.append({"name": "Dimensions", "passed": dimension_correct, "detail": f"Size: {width}x{height}, expected 128x128"})
            
            # Check if it's animated
            frame_count = 0
            try:
                while True:
                    gif.seek(frame_count)
                    frame_count += 1
            except EOFError:
                pass
            
            is_animated = frame_count > 1
            checks.append({"name": "Is Animated", "passed": is_animated, "detail": f"Found {frame_count} frames"})
            
            # Check duration (approximately 2.5 seconds at 15 FPS = ~37-38 frames)
            expected_frames = int(2.5 * 15)
            duration_tolerance = 5  # Allow some variance
            duration_correct = abs(frame_count - expected_frames) <= duration_tolerance
            checks.append({"name": "Duration", "passed": duration_correct, "detail": f"Frame count: {frame_count}, expected ~{expected_frames}"})
            
            # Analyze frames for bounce and spin behavior
            if frame_count > 5:
                gif.seek(0)
                first_frame = gif.convert('RGB')
                
                # Check for gradient background (sample top and bottom)
                top_color = first_frame.getpixel((64, 10))
                bottom_color = first_frame.getpixel((64, 118))
                
                # Top should be more blue, bottom should be whiter
                top_blue_dominant = top_color[2] > max(top_color[0], top_color[1]) * 0.8
                bottom_light = sum(bottom_color) > 600  # Sum of RGB should be high for white-ish
                gradient_present = top_blue_dominant and bottom_light
                checks.append({"name": "Gradient Background", "passed": gradient_present, "detail": f"Top color: {top_color}, Bottom color: {bottom_color}"})
                
                # Sample multiple frames to check for star presence and motion
                star_found_frames = 0
                golden_pixels_found = 0
                
                for frame_idx in [0, frame_count//4, frame_count//2, 3*frame_count//4, frame_count-1]:
                    try:
                        gif.seek(frame_idx)
                        frame = gif.convert('RGB')
                        
                        # Look for golden colors (yellow-ish pixels)
                        for y in range(20, 108, 8):  # Sample grid
                            for x in range(20, 108, 8):
                                pixel = frame.getpixel((x, y))
                                # Check for golden/yellow colors
                                if pixel[0] > 180 and pixel[1] > 180 and pixel[2] < 100:  # Golden yellow-ish
                                    golden_pixels_found += 1
                                    star_found_frames += 1
                                    break
                            if golden_pixels_found > 0:
                                break
                    except (EOFError, OSError):
                        continue
                
                star_present = star_found_frames >= 3
                checks.append({"name": "Star Presence", "passed": star_present, "detail": f"Golden pixels found in {star_found_frames} sampled frames"})
                
                # Check for motion by comparing frame differences
                motion_detected = False
                if frame_count > 2:
                    try:
                        gif.seek(0)
                        frame1 = gif.convert('RGB')
                        gif.seek(frame_count//2)
                        frame2 = gif.convert('RGB')
                        
                        # Count significantly different pixels
                        diff_pixels = 0
                        for y in range(0, 128, 4):
                            for x in range(0, 128, 4):
                                p1 = frame1.getpixel((x, y))
                                p2 = frame2.getpixel((x, y))
                                diff = sum(abs(a - b) for a, b in zip(p1, p2))
                                if diff > 50:
                                    diff_pixels += 1
                        
                        motion_detected = diff_pixels > 20
                    except (EOFError, OSError):
                        motion_detected = False
                
                checks.append({"name": "Animation Motion", "passed": motion_detected, "detail": f"Motion detected: {motion_detected}"})
            else:
                checks.append({"name": "Gradient Background", "passed": False, "detail": "Too few frames to analyze"})
                checks.append({"name": "Star Presence", "passed": False, "detail": "Too few frames to analyze"})
                checks.append({"name": "Animation Motion", "passed": False, "detail": "Too few frames to analyze"})
            
            # Check file size is reasonable for Slack
            file_size = os.path.getsize(gif_path)
            size_reasonable = file_size < 1024 * 1024  # Less than 1MB
            checks.append({"name": "File Size", "passed": size_reasonable, "detail": f"Size: {file_size} bytes"})
    
    except Exception as e:
        checks.append({"name": "GIF Analysis", "passed": False, "detail": f"Error analyzing GIF: {str(e)}"})
    
    # Calculate score
    passed_checks = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    overall_passed = score >= 0.8
    
    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == '__main__':
    workspace_dir = sys.argv[1]
    result = evaluate_bouncing_star_gif(workspace_dir)
    print(json.dumps(result))