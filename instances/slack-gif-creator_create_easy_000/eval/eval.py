import sys
import os
from PIL import Image
import json

def eval_bouncing_ball(workspace_dir):
    checks = []
    score = 0.0
    
    # Check if GIF file exists
    gif_files = [f for f in os.listdir(workspace_dir) if f.endswith('.gif')]
    if not gif_files:
        checks.append({"name": "gif_exists", "passed": False, "detail": "No GIF file found"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    gif_path = os.path.join(workspace_dir, gif_files[0])
    checks.append({"name": "gif_exists", "passed": True, "detail": f"Found GIF: {gif_files[0]}"})
    score += 0.2
    
    try:
        # Open and analyze the GIF
        gif = Image.open(gif_path)
        
        # Check dimensions (should be emoji size ~128x128)
        width, height = gif.size
        is_emoji_size = 100 <= width <= 200 and 100 <= height <= 200
        checks.append({"name": "emoji_dimensions", "passed": is_emoji_size, 
                      "detail": f"Dimensions: {width}x{height} (expected ~128x128)"})
        if is_emoji_size:
            score += 0.2
        
        # Check if it's animated (has multiple frames)
        frame_count = 0
        try:
            while True:
                gif.seek(frame_count)
                frame_count += 1
        except EOFError:
            pass
        
        is_animated = frame_count > 1
        checks.append({"name": "is_animated", "passed": is_animated,
                      "detail": f"Frame count: {frame_count}"})
        if is_animated:
            score += 0.2
        
        # Check reasonable frame count (5-50 frames typical for bouncing)
        reasonable_frames = 5 <= frame_count <= 50
        checks.append({"name": "reasonable_frame_count", "passed": reasonable_frames,
                      "detail": f"Frame count {frame_count} is reasonable"})
        if reasonable_frames:
            score += 0.2
        
        # Check file size (should be reasonable for Slack)
        file_size = os.path.getsize(gif_path)
        size_ok = file_size < 5 * 1024 * 1024  # Less than 5MB
        checks.append({"name": "file_size_ok", "passed": size_ok,
                      "detail": f"File size: {file_size} bytes"})
        if size_ok:
            score += 0.2
        
        # Check if there's motion by comparing first and middle frames
        if frame_count > 2:
            gif.seek(0)
            first_frame = gif.convert('RGB')
            gif.seek(frame_count // 2)
            middle_frame = gif.convert('RGB')
            
            # Simple difference check
            pixels_first = list(first_frame.getdata())
            pixels_middle = list(middle_frame.getdata())
            
            different_pixels = sum(1 for p1, p2 in zip(pixels_first, pixels_middle) if p1 != p2)
            has_motion = different_pixels > (width * height * 0.1)  # At least 10% different
            
            checks.append({"name": "has_motion", "passed": has_motion,
                          "detail": f"Different pixels between frames: {different_pixels}"})
            if has_motion:
                score += 0.2
        
    except Exception as e:
        checks.append({"name": "gif_analysis", "passed": False, "detail": f"Error analyzing GIF: {str(e)}"})
        return {"passed": False, "score": score, "checks": checks}
    
    passed = score >= 0.6  # Need at least 60% to pass
    return {"passed": passed, "score": score, "checks": checks}

if __name__ == '__main__':
    result = eval_bouncing_ball(sys.argv[1])
    print(json.dumps(result))