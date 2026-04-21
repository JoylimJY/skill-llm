import sys
import os
import json
import subprocess
import re

def main():
    workspace = sys.argv[1]
    checks = []

    # Check 1: create_presentation.js exists
    js_path = os.path.join(workspace, 'create_presentation.js')
    js_exists = os.path.isfile(js_path)
    checks.append({
        'name': 'create_presentation.js exists',
        'passed': js_exists,
        'detail': 'File create_presentation.js found' if js_exists else 'File create_presentation.js not found'
    })

    # Check 2: Run the JS script and produce the pptx
    pptx_path = os.path.join(workspace, 'climate_change.pptx')
    if js_exists:
        try:
            result = subprocess.run(
                ['node', 'create_presentation.js'],
                cwd=workspace,
                capture_output=True, text=True, timeout=60
            )
            run_ok = result.returncode == 0
            checks.append({
                'name': 'node create_presentation.js runs without error',
                'passed': run_ok,
                'detail': f'Exit code {result.returncode}. stderr: {result.stderr[:300]}' if not run_ok else 'Script ran successfully'
            })
        except Exception as e:
            checks.append({
                'name': 'node create_presentation.js runs without error',
                'passed': False,
                'detail': f'Exception: {str(e)}'
            })
    else:
        checks.append({
            'name': 'node create_presentation.js runs without error',
            'passed': False,
            'detail': 'Skipped - JS file not found'
        })

    # Check 3: climate_change.pptx exists
    pptx_exists = os.path.isfile(pptx_path)
    checks.append({
        'name': 'climate_change.pptx file exists',
        'passed': pptx_exists,
        'detail': 'climate_change.pptx found' if pptx_exists else 'climate_change.pptx not found'
    })

    if not pptx_exists:
        score = sum(1 for c in checks if c['passed']) / len(checks)
        print(json.dumps({'passed': score >= 0.8, 'score': score, 'checks': checks}))
        return

    # Extract text content using python-pptx
    try:
        from pptx import Presentation
        prs = Presentation(pptx_path)
        slides = list(prs.slides)
        all_text = []
        for slide in slides:
            slide_text = []
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for para in shape.text_frame.paragraphs:
                        t = para.text.strip()
                        if t:
                            slide_text.append(t)
            all_text.append(' '.join(slide_text))
        full_text = ' '.join(all_text).lower()

        # Check 4: Has exactly 5 slides
        slide_count = len(slides)
        checks.append({
            'name': 'Presentation has exactly 5 slides',
            'passed': slide_count == 5,
            'detail': f'Found {slide_count} slides (expected 5)'
        })

        # Check 5: Title slide contains expected title text
        title_text = all_text[0].lower() if len(all_text) > 0 else ''
        has_title = 'climate change' in title_text
        checks.append({
            'name': 'Slide 1 contains title text about climate change',
            'passed': has_title,
            'detail': f'Slide 1 text: {all_text[0][:200]}' if all_text else 'No text found'
        })

        # Check 6: Subtitle on title slide
        has_subtitle = 'action' in title_text or 'crisis' in title_text or 'future' in title_text or 'understanding' in title_text
        checks.append({
            'name': 'Slide 1 contains subtitle content',
            'passed': has_subtitle,
            'detail': f'Subtitle keywords found: {has_subtitle}'
        })

        # Check 7: Statistics slide
        stats_text = all_text[1].lower() if len(all_text) > 1 else ''
        has_stats_title = any(k in stats_text for k in ['numbers', 'statistics', 'stats', 'data', 'figures', 'facts', 'lie'])
        checks.append({
            'name': 'Slide 2 (statistics) has appropriate title',
            'passed': has_stats_title,
            'detail': f'Slide 2 text: {all_text[1][:200]}' if len(all_text) > 1 else 'No slide 2'
        })

        # Check 8: Causes slide contains bullet content
        causes_text = all_text[2].lower() if len(all_text) > 2 else ''
        cause_keywords = ['fossil', 'deforest', 'agriculture', 'industry', 'emission', 'coal', 'gas', 'oil', 'transport', 'livestock', 'methane', 'carbon']
        causes_found = sum(1 for k in cause_keywords if k in causes_text)
        checks.append({
            'name': 'Slide 3 (causes) contains at least 2 cause-related keywords',
            'passed': causes_found >= 2,
            'detail': f'Found {causes_found} cause keywords in: {all_text[2][:200]}' if len(all_text) > 2 else 'No slide 3'
        })

        # Check 9: Root Causes title
        has_causes_title = any(k in causes_text for k in ['cause', 'root', 'driver', 'source', 'factor'])
        checks.append({
            'name': 'Slide 3 has a title related to causes',
            'passed': has_causes_title,
            'detail': f'Title keywords found: {has_causes_title}'
        })

        # Check 10: Solutions slide has 'renewable'
        solutions_text = all_text[3].lower() if len(all_text) > 3 else ''
        has_renewable = 'renewable' in solutions_text
        checks.append({
            'name': 'Slide 4 (solutions) contains the word renewable',
            'passed': has_renewable,
            'detail': f'Renewable found: {has_renewable}. Slide text: {all_text[3][:200]}' if len(all_text) > 3 else 'No slide 4'
        })

        # Check 11: Solutions title
        has_solutions_title = any(k in solutions_text for k in ['solution', 'path', 'forward', 'action', 'fix', 'address', 'tackle', 'strategy'])
        checks.append({
            'name': 'Slide 4 has a title related to solutions or path forward',
            'passed': has_solutions_title,
            'detail': f'Solution title keywords found: {has_solutions_title}'
        })

        # Check 12: Call to action slide contains 'future'
        cta_text = all_text[4].lower() if len(all_text) > 4 else ''
        has_future = 'future' in cta_text
        checks.append({
            'name': 'Slide 5 (call to action) contains the word future',
            'passed': has_future,
            'detail': f'Future found: {has_future}. Slide text: {all_text[4][:200]}' if len(all_text) > 4 else 'No slide 5'
        })

        # Check 13: Call to action title
        has_cta_title = any(k in cta_text for k in ['act', 'now', 'action', 'change', 'together', 'start', 'begin', 'take', 'join'])
        checks.append({
            'name': 'Slide 5 has a call-to-action title',
            'passed': has_cta_title,
            'detail': f'CTA keywords found: {has_cta_title}'
        })

        # Check 14: JS file uses LAYOUT_16x9
        with open(js_path, 'r') as f:
            js_content = f.read()
        has_layout = 'LAYOUT_16x9' in js_content
        checks.append({
            'name': 'JS script uses LAYOUT_16x9',
            'passed': has_layout,
            'detail': 'LAYOUT_16x9 found in script' if has_layout else 'LAYOUT_16x9 not found in script'
        })

        # Check 15: JS file does not use # in hex colors (spot check)
        hash_color_pattern = re.compile(r'color:\s*["\']#[0-9a-fA-F]', re.IGNORECASE)
        has_hash_colors = bool(hash_color_pattern.search(js_content))
        checks.append({
            'name': 'JS script does not use # prefix in hex color strings',
            'passed': not has_hash_colors,
            'detail': 'No # prefix in colors detected' if not has_hash_colors else 'Found # prefix in hex color strings (causes file corruption)'
        })

        # Check 16: Dark background color used (1E2761 or similar dark hex mentioned in JS)
        dark_bg_pattern = re.compile(r'1[Ee]2761|1e2761|background.*color|color.*background', re.IGNORECASE)
        has_dark_bg = bool(re.search(r'1[Ee]2761|1e2761', js_content))
        checks.append({
            'name': 'JS script uses the specified dark background color 1E2761',
            'passed': has_dark_bg,
            'detail': '1E2761 found in script' if has_dark_bg else '1E2761 not found in script'
        })

    except Exception as e:
        checks.append({
            'name': 'PPTX content analysis',
            'passed': False,
            'detail': f'Error analyzing PPTX: {str(e)}'
        })

    score = sum(1 for c in checks if c['passed']) / len(checks)
    result = {
        'passed': score >= 0.8,
        'score': round(score, 4),
        'checks': checks
    }
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
