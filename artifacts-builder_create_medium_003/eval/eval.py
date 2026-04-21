import sys
import os
import json
import re

def find_files(dir_path, suffixes):
    result = []
    for root, _, files in os.walk(dir_path):
        for fname in files:
            if any(fname.lower().endswith(s) for s in suffixes):
                result.append(os.path.join(root, fname))
    return result

def read_text_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return ""

# Check 1: bundle.html exists in root and is non-empty
# Check 2: bundle.html contains inlined JS and CSS (basic heuristic)
# Check 3: In src/App.tsx has routing with at least 3 routes: Home, Profile, Settings
# Check 4: Home page has Card component usage and state-managed list + add button
# Check 5: Profile page has react-hook-form usage with zod validation
# Check 6: Settings page has Accordion with >=2 AccordionItems
# Check 7: Tailwind config avoids purple gradients, no 'inter' font used in src/index.css


def evaluate(workspace):
    checks = []

    # 1. Check bundle.html
    bundle_path = os.path.join(workspace, 'multi-route-artifact', 'bundle.html')
    if not os.path.isfile(bundle_path):
        # fallback: search bundle.html anywhere
        bundle_candidates = find_files(os.path.join(workspace, 'multi-route-artifact'), ['bundle.html'])
        bundle_path = bundle_candidates[0] if bundle_candidates else None
    if bundle_path and os.path.getsize(bundle_path) > 1024:
        bundle_ok = True
        bundle_content = read_text_file(bundle_path).lower()
    else:
        bundle_ok = False
        bundle_content = ""

    checks.append({
        "name": "bundle.html presence and size",
        "passed": bundle_ok,
        "detail": "bundle.html found and larger than 1kb" if bundle_ok else "bundle.html missing or empty"
    })

    # 2. bundle.html contains inlined JS and CSS (basic check for <style> and <script> tags)
    if bundle_ok:
        has_style = '<style' in bundle_content
        has_script = '<script' in bundle_content
        inline_assets_ok = has_style and has_script
    else:
        inline_assets_ok = False

    checks.append({
        "name": "bundle.html has inlined JS and CSS",
        "passed": inline_assets_ok,
        "detail": "found <style> and <script> tags in bundle.html" if inline_assets_ok else "missing <style> or <script> tags"
    })

    # 3. Check src/App.tsx for routing of Home, Profile, Settings
    app_path = os.path.join(workspace, 'multi-route-artifact', 'src', 'App.tsx')
    app_text = read_text_file(app_path).lower()

    route_checks = []
    # look for 'route' and each path
    for route in ['"/"', '"/profile"', '"/settings"', '/profile', '/settings']:
        route_checks.append(route in app_text)

    routes_ok = all(route_checks)

    checks.append({
        "name": "React Router routes for Home, Profile, Settings",
        "passed": routes_ok,
        "detail": "all 3 routes found in src/App.tsx" if routes_ok else "some routes missing"
    })

    # 4. Home page with Card component, state list of at least 3 items, add button
    # Heuristic: look for 'useState' and 'card' and 'addItem'
    # Read raw text to properly detect React components (must be uppercase)
    app_text_raw = read_text_file(app_path)
    state_ok = ('useState' in app_text_raw)
    card_ok = ('<Card' in app_text_raw)  # React components are PascalCase
    additem_ok = ('addItem' in app_text_raw)

    home_ok = state_ok and card_ok and additem_ok

    checks.append({
        "name": "Home page has Card component with stateful list and add button",
        "passed": home_ok,
        "detail": "state, Card, and addItem function detected in src/App.tsx" if home_ok else "missing state or Card component or add button"
    })

    # 5. Profile page has react-hook-form usage with zod validation
    # look for 'useForm', 'zod', 'zodResolver'
    profile_ok = all(k in app_text for k in ['useform', 'zod', 'zodresolver'])
    # also form field names
    profile_ok = profile_ok and ('username' in app_text) and ('email' in app_text)

    checks.append({
        "name": "Profile page uses react-hook-form with zod validation",
        "passed": profile_ok,
        "detail": "useForm and zod validation found with username and email fields" if profile_ok else "missing form or validation setup"
    })

    # 6. Settings page has Accordion with >=2 AccordionItems
    # check for AccordionItem components count at least 2
    accordion_items = len(re.findall(r'AccordionItem', app_text, re.IGNORECASE))
    accordion_ok = accordion_items >= 2

    checks.append({
        "name": "Settings page has Accordion with at least 2 collapsible items",
        "passed": accordion_ok,
        "detail": f'Found {accordion_items} AccordionItem components' if accordion_ok else 'Less than 2 AccordionItem components found'
    })

    # 7. Tailwind config constraints
    tailwind_path = os.path.join(workspace, 'multi-route-artifact', 'tailwind.config.js')
    tailwind_text = read_text_file(tailwind_path).lower()
    index_css_path = os.path.join(workspace, 'multi-route-artifact', 'src', 'index.css')
    index_css_text = read_text_file(index_css_path).lower()

    # Check no 'purple' or 'gradient' keywords in tailwind config
    no_purple_gradient = ('purple' not in tailwind_text) and ('gradient' not in tailwind_text)

    # Check index.css does not contain 'inter' font
    no_inter_font = ('inter' not in index_css_text)

    # Check index.css does not have centered layouts (look for 'text-center', 'items-center', 'justify-center')
    no_centered = not any(k in index_css_text for k in ['text-center', 'items-center', 'justify-center'])

    tailwind_ok = no_purple_gradient and no_inter_font and no_centered

    detail_msg = "No purple gradients, no Inter font, and no centered layout found." if tailwind_ok else "Found disallowed styles: "
    if not no_purple_gradient:
        detail_msg += " purple gradients present."
    if not no_inter_font:
        detail_msg += " Inter font found."
    if not no_centered:
        detail_msg += " Centered layouts detected."

    checks.append({
        "name": "Tailwind config and index.css follow style guidelines",
        "passed": tailwind_ok,
        "detail": detail_msg
    })

    # Calculate final score
    passed_count = sum(1 for c in checks if c.get('passed'))
    total = len(checks)
    score = passed_count / total if total > 0 else 0.0

    passed = score == 1.0

    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }

    print(json.dumps(result))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Argument error", "passed": False, "detail": "Expected workspace directory as argument"}]}))
        sys.exit(1)
    workspace = sys.argv[1]
    evaluate(workspace)
