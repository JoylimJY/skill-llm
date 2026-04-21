import sys
import os
import json
import re


def check_file_exists(directory, filename):
    path = os.path.join(directory, filename)
    return os.path.isfile(path)


def find_highest_score(results):
    return max(results) if results else 0.0


def case_insensitive_search(text, keywords):
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in keywords)


def check_shadcn_components_in_code(code_text, component_names):
    # Check if code text imports or uses components from the shadcn/ui library
    # We check for each component name case-insensitive
    found_components = set()
    for comp in component_names:
        # Check import or usage
        pattern = re.compile(re.escape(comp), re.IGNORECASE)
        if pattern.search(code_text):
            found_components.add(comp)
    return found_components


def load_file_contents(directory, target_extensions=None):
    # Load all files with target extensions and return dict {filename: content}
    contents = {}
    for root, _, files in os.walk(directory):
        for file in files:
            if target_extensions and not any(file.lower().endswith(ext) for ext in target_extensions):
                continue
            try:
                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                    contents[file] = f.read()
            except Exception:
                pass
    return contents


def evaluate_artifact(workspace_dir):
    checks = []

    # Check 1: Initialization - project folder 'task-artifact' should exist with package.json
    project_dir = os.path.join(workspace_dir, 'task-artifact')
    init_passed = False
    if os.path.isdir(project_dir):
        pkg_path = os.path.join(project_dir, 'package.json')
        init_passed = os.path.isfile(pkg_path)
    checks.append({
        'name': 'Project Initialization with package.json',
        'passed': init_passed,
        'detail': 'Project directory "task-artifact" with package.json found.' if init_passed else 'Missing package.json in task-artifact directory.'
    })

    # Check 2: Developed React app uses at least 3 different shadcn/ui components
    # Check for component names in source code (tsx files under src/)
    # Common shadcn components to look for, prefer distinct component names
    required_components = ["Button", "Card", "Dialog", "Accordion", "Tabs", "Tooltip"]

    found_components = set()
    if init_passed:
        src_dir = os.path.join(project_dir, 'src')
        # Load .tsx files
        tsx_contents = load_file_contents(src_dir, ['.tsx', '.ts', '.jsx', '.js'])
        for content in tsx_contents.values():
            found_components.update(check_shadcn_components_in_code(content, required_components))

    comps_passed = len(found_components) >= 3
    checks.append({
        'name': 'Uses at least 3 distinct shadcn/ui components',
        'passed': comps_passed,
        'detail': f'Found components: {sorted(found_components)}' if comps_passed else f'Only found components: {sorted(found_components)}'
    })

    # Check 3: Routing implemented - presence of react-router-dom in package.json dependencies
    routing_passed = False
    if init_passed:
        try:
            import json
            pkg_json_path = os.path.join(project_dir, 'package.json')
            with open(pkg_json_path, 'r', encoding='utf-8') as f:
                pkg_data = json.load(f)
            dependencies = pkg_data.get('dependencies', {})
            dev_deps = pkg_data.get('devDependencies', {})
            # We accept either in dependencies or devDependencies
            if any('react-router' in k.lower() for k in dependencies.keys()) or any('react-router' in k.lower() for k in dev_deps.keys()):
                routing_passed = True
            else:
                # Also heuristic: check imports in code
                for content in tsx_contents.values():
                    if re.search(r"import\s+.*Router.*from\s+['\"]react-router", content, re.IGNORECASE):
                        routing_passed = True
                        break
        except Exception:
            routing_passed = False
    checks.append({
        'name': 'React Routing implemented',
        'passed': routing_passed,
        'detail': 'react-router-dom dependency found or import detected.' if routing_passed else 'react-router-dom dependency and import not found.'
    })

    # Check 4: Tailwind CSS used - presence of tailwind directives in src/index.css
    tailwind_passed = False
    if init_passed:
        index_css_path = os.path.join(project_dir, 'src', 'index.css')
        if os.path.isfile(index_css_path):
            with open(index_css_path, 'r', encoding='utf-8') as f:
                css_content = f.read().lower()
            # Check presence of @tailwind base/components/utilities
            if all(directive in css_content for directive in ['@tailwind base', '@tailwind components', '@tailwind utilities']):
                tailwind_passed = True
    checks.append({
        'name': 'Tailwind CSS is configured',
        'passed': tailwind_passed,
        'detail': 'Tailwind directives found in src/index.css.' if tailwind_passed else 'Tailwind directives missing or src/index.css absent.'
    })

    # Check 5: Bundle created named bundle.html in project root
    bundle_path = os.path.join(project_dir, 'bundle.html')
    bundle_exists = os.path.isfile(bundle_path)
    checks.append({
        'name': 'Bundled single HTML file exists as bundle.html',
        'passed': bundle_exists,
        'detail': 'bundle.html found in project root.' if bundle_exists else 'bundle.html not found in project root.'
    })

    # Check 6: Bundle contains inlined JS and CSS - check approximate size and the presence of <script> and <style> tags
    bundle_inline_passed = False
    if bundle_exists:
        try:
            with open(bundle_path, 'r', encoding='utf-8') as f:
                bundle_text = f.read().lower()
            # Heuristic: look for large inline <script> with JS and inline <style> tags
            has_script = '<script' in bundle_text and '</script>' in bundle_text
            has_style = '<style' in bundle_text and '</style>' in bundle_text
            size_ok = os.path.getsize(bundle_path) > 10000  # >10KB reasonable minimum
            bundle_inline_passed = has_script and has_style and size_ok
        except Exception:
            bundle_inline_passed = False
    checks.append({
        'name': 'bundle.html contains inlined JS and CSS',
        'passed': bundle_inline_passed,
        'detail': 'bundle.html has <script> and <style> tags with reasonable size.' if bundle_inline_passed else 'bundle.html missing expected inline JS or CSS or file too small.'
    })

    # Check 7: Style guideline avoidance - no excessive centered layouts/purple gradients/uniform rounded corners/Inter font
    # This is best-effort: scan code for keywords indicating these avoidances
    style_issues_passed = True
    style_issues_details = []
    # Check centered layout usage (look for 'text-center' or 'justify-center', must not be excessive but one usage allowed)
    centering_count = 0
    if init_passed:
        code_files = load_file_contents(project_dir, ['.tsx', '.ts', '.jsx', '.js', '.css'])
        for content in code_files.values():
            centering_count += len(re.findall(r'text-center|justify-center', content, re.IGNORECASE))
    if centering_count > 10:
        style_issues_passed = False
        style_issues_details.append('Excessive centering classes found (text-center/justify-center).')
    # Purple gradients or uses of purple color keywords typical in tailwind (e.g., from-purple-500) - disallowed
    purple_usage = 0
    if init_passed:
        for content in code_files.values():
            purple_usage += len(re.findall(r'from-purple|to-purple|purple-', content, re.IGNORECASE))
    if purple_usage > 0:
        style_issues_passed = False
        style_issues_details.append('Purple gradient or purple color classes present.')
    # Check uniform rounded corners
    uniform_rounded = False
    if init_passed:
        for content in code_files.values():
            # Look for uniform rounded corners like rounded-lg on many elements
            matches = re.findall(r'rounded(-lg|-md|-sm)?', content, re.IGNORECASE)
            if len(matches) > 20:
                uniform_rounded = True
                break
    if uniform_rounded:
        style_issues_passed = False
        style_issues_details.append('Excessive uniform rounded corner classes (like rounded-lg) found.')
    # Check Inter font usage - look for 'font-inter' or import of Inter
    inter_font = False
    # Check Inter font usage - 修正版：使用 \b 确保只匹配独立的 inter 单词，不误杀 interface
    inter_font = False
    if init_passed:
        for content in code_files.values():
            # 1. 检查 Tailwind 类名 font-inter
            # 2. 检查 CSS 中的 font-family: Inter
            # 3. 检查 import 语句中是否包含独立的 inter 单词 (排除 interface)
            if (re.search(r'font-inter\b', content, re.IGNORECASE) or 
                re.search(r'font-family:.*?\binter\b', content, re.IGNORECASE) or
                re.search(r'import.*?\binter\b(?![a-zA-Z0-9])', content, re.IGNORECASE)):
                inter_font = True
                break
    if inter_font:
        style_issues_passed = False
        style_issues_details.append('Inter font usage detected.')

    checks.append({
        'name': 'Avoid style guideline violations (centering, purple, uniform rounding, Inter font)',
        'passed': style_issues_passed,
        'detail': 'No significant style violations found.' if style_issues_passed else '; '.join(style_issues_details)
    })

    # Calculate overall score and passed flag
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c['passed'])
    score = passed_checks / total_checks

    # We require all or 80% pass (allow some margin for style guidelines)
    passed = score >= 0.8

    result = {
        'passed': passed,
        'score': score,
        'checks': checks
    }

    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'Invocation', 'passed': False, 'detail': 'Expected one argument: workspace directory path'}]}))
        sys.exit(1)
    workspace_path = sys.argv[1]
    evaluate_artifact(workspace_path)
