import json, os, re
from pathlib import Path

workspace = Path(__import__('sys').argv[1]) if len(__import__('sys').argv) > 1 else Path('.')
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})

try:
    files = list(workspace.glob('*'))
except Exception as e:
    files = []
    add_check('workspace_access', False, f'Could not access workspace: {e}')

# Helper function for case-insensitive fuzzy filename matching
def find_file_by_pattern(patterns):
    """Find a file matching any of the given patterns (case-insensitive)"""
    for f in workspace.glob('*'):
        if f.is_file():
            fname_lower = f.name.lower()
            for pattern in patterns:
                if pattern.lower() in fname_lower or fname_lower in pattern.lower():
                    return f
    return None

# Check 1: required output files exist (case-insensitive, flexible naming)
try:
    backlog_patterns = ['backlog_refined', 'backlog_refinement', 'backlog-refined', 'backlog-refinement']
    sprint_patterns = ['sprint_plan', 'sprintplan', 'sprint-plan', 'sprint plan']
    velocity_patterns = ['velocity_summary', 'velocitysummary', 'velocity-summary', 'velocity summary']
    
    backlog_file = find_file_by_pattern(backlog_patterns)
    sprint_file = find_file_by_pattern(sprint_patterns)
    velocity_file = find_file_by_pattern(velocity_patterns)
    
    missing = []
    if not backlog_file: missing.append('backlog_refined.md (or similar)')
    if not sprint_file: missing.append('sprint_plan.md (or similar)')
    if not velocity_file: missing.append('velocity_summary.md (or similar)')
    
    add_check('required_files_exist', len(missing) == 0, 'Missing: ' + ', '.join(missing) if missing else 'All required files found.')
except Exception as e:
    add_check('required_files_exist', False, f'Error checking files: {e}')

# Load input data safely
backlog = {}
try:
    bp = workspace / 'backlog.json'
    backlog = json.loads(bp.read_text(encoding='utf-8')) if bp.exists() else {}
except Exception as e:
    add_check('input_backlog_readable', False, f'Could not read backlog.json: {e}')

try:
    notes = (workspace / 'notes.txt').read_text(encoding='utf-8', errors='replace') if (workspace / 'notes.txt').exists() else ''
except Exception as e:
    notes = ''
    add_check('input_notes_readable', False, f'Could not read notes.txt: {e}')

# Helper functions

def norm(s):
    try:
        return re.sub(r'[^a-z0-9]+', ' ', str(s).lower()).strip()
    except Exception:
        return ''

def contains_fuzzy(text, phrase):
    try:
        return norm(phrase) in norm(text)
    except Exception:
        return False

# Check 2: refined backlog contains sorted top items and markers
try:
    backlog_file = find_file_by_pattern(['backlog_refined', 'backlog_refinement', 'backlog-refined', 'backlog-refinement'])
    text = backlog_file.read_text(encoding='utf-8', errors='replace') if backlog_file else ''
    top_ids = ['US-101', 'US-102', 'US-106', 'US-109']
    found_ids = sum(1 for i in top_ids if contains_fuzzy(text, i))
    markers = ['MARKER-FILTER-PERSIST', 'MARKER-EXPORT-CSV', 'MARKER-DASH-SEARCH', 'MARKER-EXPORT-ERROR']
    found_markers = sum(1 for m in markers if contains_fuzzy(text, m))
    add_check('backlog_refined_content', found_ids >= 4 and found_markers >= 4, f'Found {found_ids}/4 top IDs and {found_markers}/4 markers.')
except Exception as e:
    add_check('backlog_refined_content', False, f'Error reading backlog refined file: {e}')

# Check 3: sprint plan has committed/stretch and capacity math (FIXED - more flexible phrases)
try:
    sprint_file = find_file_by_pattern(['sprint_plan', 'sprintplan', 'sprint-plan', 'sprint plan'])
    text = sprint_file.read_text(encoding='utf-8', errors='replace') if sprint_file else ''
    # More flexible phrase matching - accept variations
    capacity_phrases = ['sprint capacity', 'effective capacity', 'planned capacity', 'capacity']
    committed_phrases = ['committed', 'commitment']
    stretch_phrases = ['stretch', 'stretch items', 'stretch goals']
    goal_phrases = ['sprint goal', 'goal']
    
    has_capacity = any(contains_fuzzy(text, p) for p in capacity_phrases)
    has_committed = any(contains_fuzzy(text, p) for p in committed_phrases)
    has_stretch = any(contains_fuzzy(text, p) for p in stretch_phrases)
    has_goal = any(contains_fuzzy(text, p) for p in goal_phrases)
    
    phrase_hits = sum([has_capacity, has_committed, has_stretch, has_goal])
    has_capacity_number = bool(re.search(r'\b\d+\b', text))
    add_check('sprint_plan_structure', phrase_hits >= 4 and has_capacity_number, f'Phrase hits={phrase_hits}/4; capacity-like number present={has_capacity_number}.')
except Exception as e:
    add_check('sprint_plan_structure', False, f'Error reading sprint plan file: {e}')

# Check 4: velocity summary mentions calculated capacity and reliability (FIXED - more flexible)
try:
    velocity_file = find_file_by_pattern(['velocity_summary', 'velocitysummary', 'velocity-summary', 'velocity summary'])
    text = velocity_file.read_text(encoding='utf-8', errors='replace') if velocity_file else ''
    # Accept variations of required concepts
    velocity_terms = ['average velocity', 'historical velocity', 'velocity']
    availability_terms = ['availability factor', 'availability']
    capacity_terms = ['adjusted capacity', 'effective capacity', 'sprint capacity', 'planned capacity', 'capacity']
    reliability_terms = ['commitment reliability', 'commitment rate', 'reliability']
    
    hits = 0
    hits += 1 if any(contains_fuzzy(text, t) for t in velocity_terms) else 0
    hits += 1 if any(contains_fuzzy(text, t) for t in availability_terms) else 0
    hits += 1 if any(contains_fuzzy(text, t) for t in capacity_terms) else 0
    hits += 1 if any(contains_fuzzy(text, t) for t in reliability_terms) else 0
    
    add_check('velocity_summary_content', hits >= 3, f'Found {hits}/4 required concept categories.')
except Exception as e:
    add_check('velocity_summary_content', False, f'Error reading velocity summary file: {e}')

# Check 5: committed points should not exceed 85% of adjusted capacity (FIXED - extract from explicit totals)
try:
    sprint_file = find_file_by_pattern(['sprint_plan', 'sprintplan', 'sprint-plan', 'sprint plan'])
    text = sprint_file.read_text(encoding='utf-8', errors='replace') if sprint_file else ''
    
    # Calculate expected capacity from input
    av = int(backlog.get('average_velocity', 0) or 0)
    af = float(backlog.get('availability_factor', 0) or 0)
    capacity = av * af if av and af else 0
    threshold = capacity * 0.85 if capacity else None
    
    # Extract committed points from explicit totals in the sprint plan
    # Look for patterns like "Committed Items (25 points)" or "Committed Capacity: 25"
    committed = None
    match = re.search(r'committed\s*(?:items|capacity|work|total)?\s*[(:]?\s*(\d+)\s*(?:points)?', text, re.IGNORECASE)
    if match:
        committed = int(match.group(1))
    else:
        # Fallback: look for "X points" near "committed" within a reasonable distance
        match = re.search(r'committed.*?(\d+)\s*points', text, re.IGNORECASE)
        if match:
            committed = int(match.group(1))
    
    ok = True
    detail = 'Could not compute.'
    if threshold is not None and capacity > 0:
        if committed is not None:
            ok = committed <= threshold + 1.0
            detail = f'Committed={committed}, threshold≈{threshold:.1f}.'
        else:
            ok = False
            detail = 'Could not extract committed points from sprint plan.'
    else:
        ok = False
        detail = 'Insufficient data to verify committed capacity.'
    add_check('capacity_constraint', ok, detail)
except Exception as e:
    add_check('capacity_constraint', False, f'Error checking capacity: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
result = {"passed": passed_count == len(checks), "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))