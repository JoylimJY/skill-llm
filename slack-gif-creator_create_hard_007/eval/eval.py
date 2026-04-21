#!/usr/bin/env python3
import sys
import os
import json
from PIL import Image
import glob

def evaluate_workspace(workspace_path):
    checks = []
    
    # Find the output GIF file
    gif_files = glob.glob(os.path.join(workspace_path, '*.gif'))
    target_file = None
    
    # Look for heart_bounce.gif specifically or any gif file
    for gif_file in gif_files:
        if 'heart_bounce.gif' in os.path.basename(gif_file):
            target_file = gif_file
            break
    
    if not target_file and gif_files:
        target_file = gif_files[0]  # Use any gif file found
    
    # Check 1: GIF file exists
    if target_file and os.path.exists(target_file):
        checks.append({"name": "gif_file_exists", "passed": True, "detail": f"Found GIF file: {os.path.basename(target_file)}"})
    else:
        checks.append({"name": "gif_file_exists", "passed": False, "detail": "No GIF file found"})
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}
    
    try:
        with Image.open(target_file) as img:
            # Check 2: Correct dimensions (128x128)
            width, height = img.size
            if width == 128 and height == 128:
                checks.append({"name": "correct_dimensions", "passed": True, "detail": f"Dimensions are {width}x{height}"})
            else:
                checks.append({"name": "correct_dimensions", "passed": False, "detail": f"Dimensions are {width}x{height}, expected 128x128"})
            
            # Check 3: Is animated (has multiple frames)
            frame_count = 0
            try:
                while True:
                    img.seek(frame_count)
                    frame_count += 1
            except EOFError:
                pass
            
            if frame_count >= 20:  # Should be around 24 frames
                checks.append({"name": "adequate_frames", "passed": True, "detail": f"Has {frame_count} frames"})
            else:
                checks.append({"name": "adequate_frames", "passed": False, "detail": f"Has only {frame_count} frames, expected around 24"})
            
            # Check 4: Frame duration indicates reasonable FPS (around 12 FPS = ~83ms per frame)
            img.seek(0)
            duration = img.info.get('duration', 0)
            if 70 <= duration <= 120:  # Allow some tolerance around 83ms
                checks.append({"name": "correct_fps", "passed": True, "detail": f"Frame duration is {duration}ms (good FPS)"})
            else:
                checks.append({"name": "correct_fps", "passed": False, "detail": f"Frame duration is {duration}ms, expected around 83ms for 12 FPS"})
            
            # Check 5: Contains heart-like shapes (look for red/pink colors and curved shapes)
            img.seek(0)
            frame = img.convert('RGB')
            pixels = list(frame.getdata())
            
            # Count red/pink pixels (heart colors)
            red_pink_count = 0
            for r, g, b in pixels:
                if r > 150 and (r > g * 1.2) and (r > b * 1.2):  # Reddish pixels
                    red_pink_count += 1
            
            red_pink_ratio = red_pink_count / len(pixels)
            if red_pink_ratio > 0.05:  # At least 5% red/pink pixels
                checks.append({"name": "heart_colors", "passed": True, "detail": f"Contains {red_pink_ratio*100:.1f}% red/pink pixels"})
            else:
                checks.append({"name": "heart_colors", "passed": False, "detail": f"Only {red_pink_ratio*100:.1f}% red/pink pixels, expected more for a heart"})
            
            # Check 6: Animation shows size variation (bouncing/pulsing effect)
            sizes = []
            for frame_idx in range(min(frame_count, 10)):  # Check first 10 frames
                try:
                    img.seek(frame_idx)
                    frame = img.convert('RGB')
                    pixels = list(frame.getdata())
                    
                    # Count non-background pixels as a proxy for size
                    non_bg_count = 0
                    for r, g, b in pixels:
                        if not (200 <= r <= 255 and 200 <= g <= 255 and 200 <= b <= 255):  # Not light background
                            non_bg_count += 1
                    sizes.append(non_bg_count)
                except:
                    break
            
            if len(sizes) >= 5:
                size_variation = max(sizes) - min(sizes)
                avg_size = sum(sizes) / len(sizes)
                variation_ratio = size_variation / avg_size if avg_size > 0 else 0
                
                if variation_ratio > 0.2:  # At least 20% size variation
                    checks.append({"name": "size_animation", "passed": True, "detail": f"Shows {variation_ratio*100:.1f}% size variation across frames"})
                else:
                    checks.append({"name": "size_animation", "passed": False, "detail": f"Only {variation_ratio*100:.1f}% size variation, expected more for bouncing/pulsing"})
            else:
                checks.append({"name": "size_animation", "passed": False, "detail": "Could not analyze size variation across frames"})
            
            # Check 7: File size is reasonable for Slack (under 1MB, preferably much smaller)
            file_size = os.path.getsize(target_file)
            if file_size < 500000:  # Under 500KB
                checks.append({"name": "file_size", "passed": True, "detail": f"File size is {file_size} bytes (good for Slack)"})
            elif file_size < 1000000:  # Under 1MB but not optimal
                checks.append({"name": "file_size", "passed": True, "detail": f"File size is {file_size} bytes (acceptable for Slack)"})
            else:
                checks.append({"name": "file_size", "passed": False, "detail": f"File size is {file_size} bytes (too large for Slack)"})
                
    except Exception as e:
        checks.append({"name": "gif_analysis", "passed": False, "detail": f"Error analyzing GIF: {str(e)}"})
    
    # Calculate final score
    passed_count = sum(1 for check in checks if check['passed'])
    total_count = len(checks)
    score = passed_count / total_count if total_count > 0 else 0.0
    
    return {
        "passed": score >= 0.8,  # Pass if at least 80% of checks pass
        "score": score,
        "checks": checks
    }

if __name__ == '__main__':
    workspace_path = sys.argv[1]
    result = evaluate_workspace(workspace_path)
    print(json.dumps(result))