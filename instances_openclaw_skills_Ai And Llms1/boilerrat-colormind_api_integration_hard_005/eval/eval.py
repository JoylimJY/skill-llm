import sys
import os
import json
import re

def run_checks(workspace):
    checks = []

    # Check 1: palette_output.json exists
    json_path = os.path.join(workspace, 'palette_output.json')
    json_exists = os.path.isfile(json_path)
    checks.append({
        'name': 'palette_output.json exists',
        'passed': json_exists,
        'detail': 'File found' if json_exists else 'palette_output.json not found in workspace'
    })

    # Check 2: palette_output.json is valid JSON with 'result' key
    palette_data = None
    if json_exists:
        try:
            with open(json_path, 'r') as f:
                content = f.read().strip()
            palette_data = json.loads(content)
            has_result = 'result' in palette_data
            checks.append({
                'name': 'palette_output.json has result key',
                'passed': has_result,
                'detail': 'result key present' if has_result else f'Keys found: {list(palette_data.keys())}'
            })
        except Exception as e:
            checks.append({
                'name': 'palette_output.json has result key',
                'passed': False,
                'detail': f'Failed to parse JSON: {e}'
            })
    else:
        checks.append({
            'name': 'palette_output.json has result key',
            'passed': False,
            'detail': 'File missing, cannot check'
        })

    # Check 3: result contains exactly 5 colors
    if palette_data and 'result' in palette_data:
        try:
            result = palette_data['result']
            is_list = isinstance(result, list)
            has_five = is_list and len(result) == 5
            each_rgb = has_five and all(
                isinstance(c, list) and len(c) == 3 and all(isinstance(v, int) for v in c)
                for c in result
            )
            passed = has_five and each_rgb
            checks.append({
                'name': 'palette has 5 RGB colors',
                'passed': passed,
                'detail': f'Got {len(result) if is_list else "non-list"} colors' if not passed else '5 valid RGB triples found'
            })
        except Exception as e:
            checks.append({
                'name': 'palette has 5 RGB colors',
                'passed': False,
                'detail': f'Error checking result: {e}'
            })
    else:
        checks.append({
            'name': 'palette has 5 RGB colors',
            'passed': False,
            'detail': 'No result data to check'
        })

    # Check 4: first slot is approximately navy blue (0,31,63) - allow ±15 tolerance
    if palette_data and 'result' in palette_data:
        try:
            result = palette_data['result']
            if isinstance(result, list) and len(result) >= 1:
                first = result[0]
                target = [0, 31, 63]
                tolerance = 15
                close_enough = all(abs(first[i] - target[i]) <= tolerance for i in range(3))
                checks.append({
                    'name': 'first slot locked to navy blue ~(0,31,63)',
                    'passed': close_enough,
                    'detail': f'First color: {first}, target: {target}, tolerance: ±{tolerance}'
                })
            else:
                checks.append({
                    'name': 'first slot locked to navy blue ~(0,31,63)',
                    'passed': False,
                    'detail': 'result list too short or invalid'
                })
        except Exception as e:
            checks.append({
                'name': 'first slot locked to navy blue ~(0,31,63)',
                'passed': False,
                'detail': f'Error: {e}'
            })
    else:
        checks.append({
            'name': 'first slot locked to navy blue ~(0,31,63)',
            'passed': False,
            'detail': 'No result data'
        })

    # Check 5: last slot is approximately warm gold (255,200,87) - allow ±15 tolerance
    if palette_data and 'result' in palette_data:
        try:
            result = palette_data['result']
            if isinstance(result, list) and len(result) == 5:
                last = result[4]
                target = [255, 200, 87]
                tolerance = 15
                close_enough = all(abs(last[i] - target[i]) <= tolerance for i in range(3))
                checks.append({
                    'name': 'last slot locked to warm gold ~(255,200,87)',
                    'passed': close_enough,
                    'detail': f'Last color: {last}, target: {target}, tolerance: ±{tolerance}'
                })
            else:
                checks.append({
                    'name': 'last slot locked to warm gold ~(255,200,87)',
                    'passed': False,
                    'detail': 'result list too short or invalid'
                })
        except Exception as e:
            checks.append({
                'name': 'last slot locked to warm gold ~(255,200,87)',
                'passed': False,
                'detail': f'Error: {e}'
            })
    else:
        checks.append({
            'name': 'last slot locked to warm gold ~(255,200,87)',
            'passed': False,
            'detail': 'No result data'
        })

    # Check 6: palette_pretty.txt exists
    pretty_path = os.path.join(workspace, 'palette_pretty.txt')
    pretty_exists = os.path.isfile(pretty_path)
    checks.append({
        'name': 'palette_pretty.txt exists',
        'passed': pretty_exists,
        'detail': 'File found' if pretty_exists else 'palette_pretty.txt not found in workspace'
    })

    # Check 7: palette_pretty.txt contains hex color codes or RGB values
    if pretty_exists:
        try:
            with open(pretty_path, 'r', errors='replace') as f:
                pretty_content = f.read()
            hex_pattern = re.compile(r'#[0-9a-fA-F]{6}', re.IGNORECASE)
            rgb_pattern = re.compile(r'rgb\s*\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)', re.IGNORECASE)
            has_hex = bool(hex_pattern.search(pretty_content))
            has_rgb = bool(rgb_pattern.search(pretty_content))
            has_color_info = has_hex or has_rgb
            checks.append({
                'name': 'palette_pretty.txt contains color info (hex or RGB)',
                'passed': has_color_info,
                'detail': f'hex codes found: {has_hex}, rgb values found: {has_rgb}'
            })
        except Exception as e:
            checks.append({
                'name': 'palette_pretty.txt contains color info (hex or RGB)',
                'passed': False,
                'detail': f'Error reading file: {e}'
            })
    else:
        checks.append({
            'name': 'palette_pretty.txt contains color info (hex or RGB)',
            'passed': False,
            'detail': 'File missing'
        })

    total = len(checks)
    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / total if total > 0 else 0.0
    overall_passed = passed_count == total

    return {
        'passed': overall_passed,
        'score': round(score, 4),
        'checks': checks
    }

if __name__ == '__main__':
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.'
    try:
        result = run_checks(workspace)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({
            'passed': False,
            'score': 0.0,
            'checks': [{'name': 'eval_script_crash', 'passed': False, 'detail': str(e)}]
        }))
