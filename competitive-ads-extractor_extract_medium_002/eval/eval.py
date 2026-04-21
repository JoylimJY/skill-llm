import sys
import os
import json
import re

def case_insensitive_contains(text, keywords):
    text = text.lower()
    for kw in keywords:
        if kw.lower() in text:
            return True
    return False

def check_markdown_sections(content, required_sections):
    results = {}
    content_lower = content.lower()
    for sec in required_sections:
        found = re.search(r'#+\s*' + re.escape(sec.lower()), content_lower)
        results[sec] = bool(found)
    return results

def extract_bullet_points(content, section):
    # Simple heuristic: find section heading, then collect bullet points under it
    lines = content.splitlines()
    section_lower = section.lower()
    bullets = []
    inside_section = False
    for line in lines:
        if re.match(r'#', line) and section_lower in line.lower():
            inside_section = True
            continue
        if inside_section:
            if re.match(r'#', line):  # next section
                break
            if re.match(r'\s*[-*]\s+', line):
                bullets.append(line.strip())
    return bullets

def evaluate_analysis_md(path):
    try:
        with open(path, encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, f'Cannot read analysis file: {e}'
    
    required_sections = ["problems highlighted", "use cases targeted", "value propositions promoted", "common creative patterns"]
    section_checks = check_markdown_sections(content, required_sections)

    # Check at least 1 bullet point per section
    bullet_checks = {}
    for sec in required_sections:
        bullets = extract_bullet_points(content, sec)
        bullet_checks[sec] = len(bullets) >= 1

    all_sections_present = all(section_checks.values())
    all_have_bullets = all(bullet_checks.values())

    passed = all_sections_present and all_have_bullets

    details = []
    for sec in required_sections:
        details.append({
            "name": f'Section "{sec}" present',
            "passed": section_checks.get(sec, False),
            "detail": f'Section {sec} found: {section_checks.get(sec)}'
        })
        details.append({
            "name": f'Contains bullet points in "{sec}"',
            "passed": bullet_checks.get(sec, False),
            "detail": f'Bullet points present: {bullet_checks.get(sec)}'
        })

    return passed, details

def check_screenshots(folder):
    png_files = [f for f in os.listdir(folder) if f.lower().endswith('.png')]
    if len(png_files) < 3:
        return False, f'Found only {len(png_files)} PNG screenshot files, expected at least 3.'
    # Optionally verify file sizes > 0
    for fname in png_files:
        fpath = os.path.join(folder, fname)
        if os.path.getsize(fpath) < 100:
            return False, f'File {fname} is suspiciously small.'
    return True, f'Found {len(png_files)} PNG screenshot files.'

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "argument check", "passed": False, "detail": "Expected workspace path argument."}]}))
        return

    workspace = sys.argv[1]
    base_folder = os.path.join(workspace, "competitor-ads", "acme-software")

    checks = []

    # Check screenshots
    passed_screenshots, detail_screenshots = check_screenshots(base_folder)
    checks.append({
        "name": "Screenshots saved as PNG in competitor-ads/acme-software",
        "passed": passed_screenshots,
        "detail": detail_screenshots
    })

    # Find analysis.md (case insensitive) - flexible file discovery
    analysis_files = [f for f in os.listdir(base_folder) if f.lower() == 'analysis.md']
    if not analysis_files:
        # try files containing 'analysis' and '.md'
        analysis_files = [f for f in os.listdir(base_folder) if 'analysis' in f.lower() and f.lower().endswith('.md')]
    if not analysis_files:
        checks.append({
            "name": "Analysis report presence",
            "passed": False,
            "detail": "No analysis markdown file found in competitor-ads/acme-software"
        })
    else:
        # Evaluate all found and take best
        best_score = 0
        best_checks = None
        best_passed = False
        for af in analysis_files:
            af_path = os.path.join(base_folder, af)
            passed_md, details_md = evaluate_analysis_md(af_path)
            score = sum(1 for c in details_md if c['passed']) / len(details_md) if details_md else 0
            if score > best_score:
                best_score = score
                best_checks = details_md
                best_passed = passed_md
        checks.append({
            "name": f"Analysis report content correctness ({len(analysis_files)} file(s) checked)",
            "passed": best_passed,
            "detail": f"Best score {best_score:.2f} from analysis files"
        })
        checks.extend(best_checks if best_checks else [])

    score = sum(1 for c in checks if c['passed']) / len(checks) if checks else 0.0
    passed_overall = score == 1.0

    result = {
        "passed": passed_overall,
        "score": score,
        "checks": checks
    }

    print(json.dumps(result))

if __name__ == "__main__":
    main()
