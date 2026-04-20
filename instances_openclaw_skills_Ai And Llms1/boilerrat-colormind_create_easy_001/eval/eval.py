import json
import os
import re
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []

def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

# Helper to extract palette colors from various JSON structures
def extract_palette_colors(data):
    """Extract list of colors from various possible JSON structures."""
    if not isinstance(data, dict):
        return None
    
    # Try common keys for palette data
    palette_keys = ['palette', 'colors', 'hex_palette', 'rgb_palette', 'color_palette', 'palette_colors']
    
    for key in palette_keys:
        if key in data:
            val = data[key]
            if isinstance(val, list) and len(val) >= 1:
                return val
    
    # Try to find any list that looks like colors (hex strings or RGB arrays)
    for key, val in data.items():
        if isinstance(val, list) and len(val) >= 1:
            first = val[0]
            # Check if it's hex colors
            if isinstance(first, str) and re.match(r'^#[0-9A-Fa-f]{6}$', first):
                return val
            # Check if it's RGB arrays
            if isinstance(first, list) and len(first) == 3:
                return val
    
    return None

# Check 1: palette.json exists and is valid JSON with expected structure
try:
    palette_path = workspace / 'palette.json'
    if not palette_path.exists():
        add_check('palette_json_exists', False, 'palette.json is missing')
    else:
        try:
            data = json.loads(palette_path.read_text(encoding='utf-8'))
            colors = extract_palette_colors(data)
            if colors and len(colors) == 5:
                add_check('palette_json_exists', True, 'palette.json exists and contains a 5-color palette')
            elif colors and len(colors) >= 4:
                # Accept slightly flexible length
                add_check('palette_json_exists', True, f'palette.json exists with {len(colors)} colors')
            else:
                add_check('palette_json_exists', False, 'palette.json is present but does not contain a valid palette list')
        except Exception as e:
            add_check('palette_json_exists', False, f'palette.json could not be parsed as JSON: {e}')
except Exception as e:
    add_check('palette_json_exists', False, f'Unexpected error while checking palette.json: {e}')

# Check 2: first color is locked near the requested brand blue
try:
    palette_path = workspace / 'palette.json'
    if not palette_path.exists():
        add_check('locked_color', False, 'palette.json is missing')
    else:
        try:
            data = json.loads(palette_path.read_text(encoding='utf-8'))
            colors = extract_palette_colors(data)
            ok = False
            detail = 'first color not found'
            
            if colors and len(colors) >= 1:
                first = colors[0]
                target = [0, 122, 255]
                
                # Handle hex format
                if isinstance(first, str) and re.match(r'^#[0-9A-Fa-f]{6}$', first):
                    hex_val = first[1:]
                    rgb = [int(hex_val[i:i+2], 16) for i in (0, 2, 4)]
                    diffs = [abs(rgb[i] - target[i]) for i in range(3)]
                    ok = sum(diffs) <= 30
                    detail = f'first color={first} (rgb={rgb}), target={target}, diffs={diffs}'
                
                # Handle RGB array format
                elif isinstance(first, list) and len(first) == 3:
                    diffs = [abs(int(first[i]) - target[i]) for i in range(3)]
                    ok = sum(diffs) <= 30
                    detail = f'first color={first}, target={target}, diffs={diffs}'
                
                # Handle dict format with rgb/hex keys
                elif isinstance(first, dict):
                    if 'rgb' in first and isinstance(first['rgb'], list) and len(first['rgb']) == 3:
                        diffs = [abs(int(first['rgb'][i]) - target[i]) for i in range(3)]
                        ok = sum(diffs) <= 30
                        detail = f'first color={first["rgb"]}, target={target}, diffs={diffs}'
                    elif 'hex' in first and isinstance(first['hex'], str):
                        hex_val = first['hex'][1:]
                        rgb = [int(hex_val[i:i+2], 16) for i in (0, 2, 4)]
                        diffs = [abs(rgb[i] - target[i]) for i in range(3)]
                        ok = sum(diffs) <= 30
                        detail = f'first color={first["hex"]} (rgb={rgb}), target={target}, diffs={diffs}'
            
            add_check('locked_color', ok, detail)
        except Exception as e:
            add_check('locked_color', False, f'Could not inspect palette colors: {e}')
except Exception as e:
    add_check('locked_color', False, f'Unexpected error while checking locked color: {e}')

# Check 3: summary file exists and mentions both hex and RGB
try:
    summary_path = workspace / 'palette_summary.md'
    if not summary_path.exists():
        add_check('summary_file', False, 'palette_summary.md is missing')
    else:
        try:
            text = summary_path.read_text(encoding='utf-8')
            text_lower = text.lower()
            has_hex = 'hex' in text_lower or re.search(r'#[0-9A-Fa-f]{6}', text)
            has_rgb = 'rgb' in text_lower or re.search(r'rgb\s*\(', text_lower)
            add_check('summary_file', has_hex and has_rgb, f'contains_hex={has_hex}, contains_rgb={has_rgb}')
        except Exception as e:
            add_check('summary_file', False, f'Could not read summary file: {e}')
except Exception as e:
    add_check('summary_file', False, f'Unexpected error while checking summary file: {e}')

# Check 4: marker input file exists
try:
    marker_path = workspace / 'task_marker.txt'
    if not marker_path.exists():
        add_check('marker_file', False, 'task_marker.txt is missing')
    else:
        try:
            text = marker_path.read_text(encoding='utf-8')
            add_check('marker_file', 'COLORMIND_TASK_MARKER' in text, 'marker content found' if 'COLORMIND_TASK_MARKER' in text else 'marker content missing')
        except Exception as e:
            add_check('marker_file', False, f'Could not read marker file: {e}')
except Exception as e:
    add_check('marker_file', False, f'Unexpected error while checking marker file: {e}')

passed = all(c['passed'] for c in checks) if checks else False
score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
print(json.dumps({'passed': passed, 'score': score, 'checks': checks}))