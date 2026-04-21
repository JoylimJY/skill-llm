import sys
import os
import json

def evaluate(workspace_dir):
    checks = []

    # Check 1: bundle.html exists
    bundle_path = os.path.join(workspace_dir, 'counter-app', 'bundle.html')
    bundle_exists = os.path.isfile(bundle_path)
    checks.append({
        'name': 'bundle.html exists at counter-app/bundle.html',
        'passed': bundle_exists,
        'detail': f'File found at {bundle_path}' if bundle_exists else f'File not found at {bundle_path}'
    })

    if not bundle_exists:
        # Try to find bundle.html anywhere in workspace
        for root, dirs, files in os.walk(workspace_dir):
            for fname in files:
                if fname == 'bundle.html':
                    bundle_path = os.path.join(root, fname)
                    bundle_exists = True
                    checks[-1]['passed'] = True
                    checks[-1]['detail'] = f'Found bundle.html at {bundle_path}'
                    break
            if bundle_exists:
                break

    content = ''
    if bundle_exists:
        try:
            with open(bundle_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception as e:
            content = ''

    # Check 2: bundle.html is non-trivial size (at least 10KB)
    file_size = len(content)
    size_ok = file_size >= 10000
    checks.append({
        'name': 'bundle.html has substantial content (>=10KB)',
        'passed': size_ok,
        'detail': f'File size: {file_size} bytes'
    })

    # Check 3: Contains HTML structure
    content_lower = content.lower()
    has_html = '<html' in content_lower or '<!doctype html' in content_lower
    checks.append({
        'name': 'bundle.html contains valid HTML structure',
        'passed': has_html,
        'detail': 'Found <html> or <!DOCTYPE html> tag' if has_html else 'No HTML structure found'
    })

    # Check 4: Contains React/JavaScript bundle
    has_js = '<script' in content_lower
    checks.append({
        'name': 'bundle.html contains inlined JavaScript',
        'passed': has_js,
        'detail': 'Found <script> tag' if has_js else 'No <script> tag found'
    })

    # Check 5: Source App.tsx mentions 'Count:' pattern
    app_tsx_path = os.path.join(workspace_dir, 'counter-app', 'src', 'App.tsx')
    app_tsx_exists = os.path.isfile(app_tsx_path)
    app_tsx_content = ''
    if app_tsx_exists:
        try:
            with open(app_tsx_path, 'r', encoding='utf-8', errors='replace') as f:
                app_tsx_content = f.read()
        except:
            pass

    has_count_display = 'count:' in app_tsx_content.lower() or 'count' in app_tsx_content.lower()
    checks.append({
        'name': 'App.tsx contains counter display logic',
        'passed': has_count_display,
        'detail': 'Found count-related code in App.tsx' if has_count_display else 'No count-related code found in App.tsx'
    })

    # Check 6: Source App.tsx contains Increment button
    has_increment = 'increment' in app_tsx_content.lower()
    checks.append({
        'name': 'App.tsx contains Increment button',
        'passed': has_increment,
        'detail': 'Found Increment in App.tsx' if has_increment else 'No Increment button found in App.tsx'
    })

    # Check 7: Source App.tsx contains Decrement button
    has_decrement = 'decrement' in app_tsx_content.lower()
    checks.append({
        'name': 'App.tsx contains Decrement button',
        'passed': has_decrement,
        'detail': 'Found Decrement in App.tsx' if has_decrement else 'No Decrement button found in App.tsx'
    })

    # Check 8: Source App.tsx contains Reset button
    has_reset = 'reset' in app_tsx_content.lower()
    checks.append({
        'name': 'App.tsx contains Reset button',
        'passed': has_reset,
        'detail': 'Found Reset in App.tsx' if has_reset else 'No Reset button found in App.tsx'
    })

    # Check 9: Source App.tsx imports Button from shadcn/ui
    has_button_import = "from '@/components/ui/button'" in app_tsx_content or 'from "@/components/ui/button"' in app_tsx_content
    checks.append({
        'name': "App.tsx imports Button from '@/components/ui/button'",
        'passed': has_button_import,
        'detail': 'Found Button import from shadcn/ui' if has_button_import else 'No shadcn/ui Button import found'
    })

    # Check 10: bundle.html contains 'Count' text (after bundling the counter UI)
    has_count_in_bundle = 'count' in content_lower
    checks.append({
        'name': 'bundle.html contains counter-related content',
        'passed': has_count_in_bundle,
        'detail': 'Found count-related text in bundle.html' if has_count_in_bundle else 'No count-related text found in bundle.html'
    })

    num_passed = sum(1 for c in checks if c['passed'])
    score = num_passed / len(checks)
    passed = score >= 0.8

    return {
        'passed': passed,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.'
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))
