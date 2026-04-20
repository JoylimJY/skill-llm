import sys
import os
import json
import re

def normalize(text):
    return re.sub(r'[\s\W]+', ' ', text.lower()).strip()

def fuzzy_contains(text, phrase):
    return normalize(phrase) in normalize(text)

checks = []

workspace = sys.argv[1] if len(sys.argv) > 1 else '.'

# Find output file - prefer larger files (actual output over input files)
output_path = None
output_size = 0

# First pass: find all candidate files
candidates = []
for fname in os.listdir(workspace):
    fpath = os.path.join(workspace, fname)
    if os.path.isfile(fpath):
        # Skip known input files
        if fname in ['context.txt', 'gen_inputs.py', 'setup.sh']:
            continue
        # Prefer .txt and .md files
        if fname.endswith('.txt') or fname.endswith('.md'):
            try:
                size = os.path.getsize(fpath)
                candidates.append((fpath, size))
            except:
                pass

# Sort by size descending (larger files are more likely to be actual output)
candidates.sort(key=lambda x: x[1], reverse=True)

if candidates:
    output_path = candidates[0][0]
    output_size = candidates[0][1]

# Check 1: output file exists
if output_path and os.path.exists(output_path):
    checks.append({'name': 'output_file_exists', 'passed': True, 'detail': f'Found output at {output_path}'})
else:
    checks.append({'name': 'output_file_exists', 'passed': False, 'detail': 'No output file found in workspace'})
    print(json.dumps({'passed': False, 'score': 0.0, 'checks': checks}))
    sys.exit(0)

try:
    with open(output_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
except Exception as e:
    checks.append({'name': 'output_readable', 'passed': False, 'detail': str(e)})
    print(json.dumps({'passed': False, 'score': 0.0, 'checks': checks}))
    sys.exit(0)

checks.append({'name': 'output_readable', 'passed': True, 'detail': f'File readable, {len(content)} chars'})

# Check 2: minimum length (4-5 min talk should be substantial)
min_chars = 3000
passed_length = len(content) >= min_chars
checks.append({'name': 'sufficient_length', 'passed': passed_length, 'detail': f'{len(content)} chars (min {min_chars})'})

# Check 3: mentions error messages as UI / user interface concept
try:
    has_ui = (
        fuzzy_contains(content, 'user interface') or 
        (fuzzy_contains(content, 'error message') and fuzzy_contains(content, 'interface')) or
        fuzzy_contains(content, 'error messages are') or
        fuzzy_contains(content, 'treat error messages')
    )
    checks.append({'name': 'core_insight_present', 'passed': has_ui, 'detail': 'Checks for error-messages-as-UI insight'})
except Exception as e:
    checks.append({'name': 'core_insight_present', 'passed': False, 'detail': str(e)})

# Check 4: references the concrete example (timeout / operation failed)
try:
    has_example = (
        fuzzy_contains(content, 'operation failed') or
        fuzzy_contains(content, 'timeout') or
        fuzzy_contains(content, 'database connection') or
        fuzzy_contains(content, '30s') or
        fuzzy_contains(content, 'retried')
    )
    checks.append({'name': 'concrete_example_present', 'passed': has_example, 'detail': 'Checks for the timeout/operation-failed example'})
except Exception as e:
    checks.append({'name': 'concrete_example_present', 'passed': False, 'detail': str(e)})

# Check 5: has an opening / hook section (more flexible patterns)
try:
    opening_patterns = [
        r'open|hook|intro|begin|start|welcome|imagine|picture this',
        r'0:00|00:00|minute 0',
        r'good morning|good afternoon|hello everyone',
        r'let me start|today i want|i want to talk'
    ]
    has_opening = any(re.search(p, content, re.IGNORECASE) for p in opening_patterns)
    checks.append({'name': 'has_opening_section', 'passed': has_opening, 'detail': 'Checks for opening/hook section marker'})
except Exception as e:
    checks.append({'name': 'has_opening_section', 'passed': False, 'detail': str(e)})

# Check 6: has Q&A section (more flexible patterns)
try:
    qa_patterns = [
        r'q\s*[&a]|q\s*and\s*a|question|objection|faq',
        r'what about|you might ask|some people say',
        r'audience question|let me address|common concern'
    ]
    has_qa = any(re.search(p, content, re.IGNORECASE) for p in qa_patterns)
    checks.append({'name': 'has_qa_section', 'passed': has_qa, 'detail': 'Checks for Q&A or objections section'})
except Exception as e:
    checks.append({'name': 'has_qa_section', 'passed': False, 'detail': str(e)})

# Check 7: has broader implications section (more flexible patterns)
try:
    implication_patterns = [
        r'implic|broader|beyond|matter|why this',
        r'takeaway|lesson|conclusion|in summary',
        r'what does this mean|the bigger picture|looking forward',
        r'change the way|transform|impact on'
    ]
    has_implications = any(re.search(p, content, re.IGNORECASE) for p in implication_patterns)
    checks.append({'name': 'has_implications', 'passed': has_implications, 'detail': 'Checks for broader implications content'})
except Exception as e:
    checks.append({'name': 'has_implications', 'passed': False, 'detail': str(e)})

total = len(checks)
passed_count = sum(1 for c in checks if c['passed'])
score = round(passed_count / total, 4) if total > 0 else 0.0
overall_passed = score >= 0.7

print(json.dumps({'passed': overall_passed, 'score': score, 'checks': checks}))