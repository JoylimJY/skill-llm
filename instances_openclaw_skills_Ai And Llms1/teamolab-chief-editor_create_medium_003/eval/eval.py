from pathlib import Path
import json
import re
import sys

workspace = Path(sys.argv[1])
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

# Check output exists
try:
    output_path = workspace / 'output.txt'
    exists = output_path.exists()
    add_check('output_exists', exists, 'output.txt found' if exists else 'output.txt is missing')
except Exception as e:
    add_check('output_exists', False, f'Error checking output file: {e}')
    output_path = None

content = ''
if output_path is not None:
    try:
        content = output_path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        add_check('output_readable', False, f'Could not read output.txt: {e}')
    else:
        add_check('output_readable', True, 'output.txt could be read')

# Check English-ish structure and references at end
try:
    text = content.strip()
    has_heading = bool(re.search(r'(?im)^\s*(title|summary|overview|editorial brief|article)\b', text))
    add_check('contains_heading', has_heading, 'Found a likely heading' if has_heading else 'No clear heading detected')
except Exception as e:
    add_check('contains_heading', False, f'Heading check failed: {e}')

try:
    lower = content.lower()
    ref_pos = lower.rfind('references')
    end_pos = len(lower)
    has_refs = ref_pos != -1
    refs_at_end = has_refs and (end_pos - ref_pos) < max(300, int(0.25 * max(1, end_pos)))
    add_check('references_section_at_end', refs_at_end, 'References appears near the end' if refs_at_end else 'References section missing or not at end')
except Exception as e:
    add_check('references_section_at_end', False, f'References placement check failed: {e}')

# Check markers from input files are likely reflected/handled indirectly via content quality cues
required_markers = [
    'editorial-core-2025',
    'structure-check-8842',
    'pdf-anchor-551'
]
try:
    norm = re.sub(r'[^a-z0-9]+', ' ', content.lower())
    marker_matches = 0
    for marker in required_markers:
        mnorm = re.sub(r'[^a-z0-9]+', ' ', marker.lower())
        if mnorm in norm:
            marker_matches += 1
    passed = marker_matches >= 1
    add_check('marker_usage', passed, f'{marker_matches} marker(s) found in output; at least one expected')
except Exception as e:
    add_check('marker_usage', False, f'Marker check failed: {e}')

# Check that URL(s) from inputs are represented in references or body
try:
    urls = [
        'example.com/editorial-guide',
        'example.org/style-manual',
        'example.net/research-note'
    ]
    lowered = content.lower()
    url_hits = sum(1 for u in urls if u.lower() in lowered)
    add_check('url_inclusion', url_hits >= 1, f'{url_hits} url(s) found in output')
except Exception as e:
    add_check('url_inclusion', False, f'URL inclusion check failed: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
result = {
    'passed': passed_count == len(checks),
    'score': score,
    'checks': checks,
}
print(json.dumps(result, ensure_ascii=False))
