#!/usr/bin/env python3

import sys
import os
from pathlib import Path
from PIL import Image
import json

def main():
    workspace = Path(sys.argv[1])
    checks = []
    
    # Check 1: File exists
    gif_path = workspace / 'thumbs_reaction.gif'
    if gif_path.exists():
        checks.append({"name": "File exists", "passed": True, "detail": "thumbs_reaction.gif found"})
    else:
        checks.append({"name": "File exists", "passed": False, "detail": "thumbs_reaction.gif not found"})
        # Early return if file doesn't exist
        result = {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }
        print(json.dumps(result))
        return
    
    try:
        # Check 2: File is a valid GIF
        img = Image.open(gif_path)
        if img.format == 'GIF':
            checks.append({"name": "Valid GIF format", "passed": True, "detail": "File is a valid GIF"})
        else:
            checks.append({"name": "Valid GIF format", "passed": False, "detail": f"File format is {img.format}, not GIF"})
    except Exception as e:
        checks.append({"name": "Valid GIF format", "passed": False, "detail": f"Error opening file: {str(e)}"})
        img = None
    
    # Check 3: Dimensions are 128x128
    if img:
        width, height = img.size
        if width == 128 and height == 128:
            checks.append({"name": "Correct dimensions", "passed": True, "detail": "Dimensions are 128x128"})
        else:
            checks.append({"name": "Correct dimensions", "passed": False, "detail": f"Dimensions are {width}x{height}, expected 128x128"})
    else:
        checks.append({"name": "Correct dimensions", "passed": False, "detail": "Could not check dimensions - invalid image"})
    
    # Check 4: File size under 64KB for Slack emoji
    file_size = gif_path.stat().st_size
    if file_size <= 65536:  # 64KB
        checks.append({"name": "Size under 64KB", "passed": True, "detail": f"File size is {file_size} bytes"})
    else:
        checks.append({"name": "Size under 64KB", "passed": False, "detail": f"File size is {file_size} bytes, exceeds 64KB limit"})
    
    # Check 5: GIF is animated (has multiple frames)
    if img:
        try:
            frame_count = img.n_frames
            if frame_count > 1:
                checks.append({"name": "Is animated", "passed": True, "detail": f"GIF has {frame_count} frames"})
            else:
                checks.append({"name": "Is animated", "passed": False, "detail": "GIF has only 1 frame - not animated"})
        except Exception as e:
            checks.append({"name": "Is animated", "passed": False, "detail": f"Could not check frame count: {str(e)}"})
    else:
        checks.append({"name": "Is animated", "passed": False, "detail": "Could not check animation - invalid image"})
    
    # Check 6: Reasonable frame count for emoji (not too many)
    if img:
        try:
            frame_count = img.n_frames
            if 5 <= frame_count <= 30:
                checks.append({"name": "Reasonable frame count", "passed": True, "detail": f"Frame count {frame_count} is reasonable for emoji"})
            else:
                checks.append({"name": "Reasonable frame count", "passed": False, "detail": f"Frame count {frame_count} may be too low or high for good emoji animation"})
        except Exception as e:
            checks.append({"name": "Reasonable frame count", "passed": False, "detail": f"Could not check frame count: {str(e)}"})
    else:
        checks.append({"name": "Reasonable frame count", "passed": False, "detail": "Could not check frame count - invalid image"})
    
    # Calculate score
    passed_count = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_count / total_checks if total_checks > 0 else 0.0
    
    result = {
        "passed": score >= 0.8,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result))

if __name__ == '__main__':
    main()