import sys
import os
import json

def main():
    workspace = sys.argv[1]
    checks = []

    # Check 1: screenshot.png exists
    screenshot_path = None
    for fname in os.listdir(workspace):
        if fname.lower().endswith('.png') and 'screenshot' in fname.lower():
            screenshot_path = os.path.join(workspace, fname)
            break

    if screenshot_path is None:
        checks.append({'name': 'screenshot_file_exists', 'passed': False, 'detail': 'No screenshot PNG file found in workspace'})
        score = 0.0
        result = {'passed': False, 'score': score, 'checks': checks}
        print(json.dumps(result))
        return

    checks.append({'name': 'screenshot_file_exists', 'passed': True, 'detail': f'Found screenshot file: {os.path.basename(screenshot_path)}'})

    # Check 2: File is a valid PNG
    try:
        from PIL import Image
        img = Image.open(screenshot_path)
        img.verify()
        checks.append({'name': 'valid_png_format', 'passed': True, 'detail': 'File is a valid PNG image'})
    except Exception as e:
        checks.append({'name': 'valid_png_format', 'passed': False, 'detail': f'File is not a valid PNG: {e}'})
        score = sum(1 for c in checks if c['passed']) / len(checks)
        result = {'passed': score >= 0.8, 'score': score, 'checks': checks}
        print(json.dumps(result))
        return

    # Check 3: Screenshot has reasonable dimensions (not tiny)
    try:
        from PIL import Image
        img = Image.open(screenshot_path)
        width, height = img.size
        reasonable = width >= 400 and height >= 200
        checks.append({
            'name': 'reasonable_dimensions',
            'passed': reasonable,
            'detail': f'Image dimensions: {width}x{height} px' + ('' if reasonable else ' (too small)')
        })
    except Exception as e:
        checks.append({'name': 'reasonable_dimensions', 'passed': False, 'detail': f'Could not read dimensions: {e}'})

    # Check 4: Screenshot is not completely white or blank (has some content)
    try:
        from PIL import Image
        import statistics
        img = Image.open(screenshot_path).convert('RGB')
        pixels = list(img.getdata())
        # Sample some pixels; if all are white (255,255,255), it's blank
        r_vals = [p[0] for p in pixels[::100]]
        g_vals = [p[1] for p in pixels[::100]]
        b_vals = [p[2] for p in pixels[::100]]
        # Check that there is variance (not a blank white/single-color image)
        all_white = all(r == 255 and g == 255 and b == 255 for r, g, b in zip(r_vals, g_vals, b_vals))
        has_content = not all_white
        checks.append({
            'name': 'screenshot_has_content',
            'passed': has_content,
            'detail': 'Screenshot contains non-white pixels (content detected)' if has_content else 'Screenshot appears blank or all-white'
        })
    except Exception as e:
        checks.append({'name': 'screenshot_has_content', 'passed': False, 'detail': f'Could not analyze pixel content: {e}'})

    score = sum(1 for c in checks if c['passed']) / len(checks)
    passed = score == 1.0
    result = {'passed': passed, 'score': score, 'checks': checks}
    print(json.dumps(result))

if __name__ == '__main__':
    main()
