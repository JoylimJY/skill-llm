import json
import re
import sys
from pathlib import Path


def norm(s):
    try:
        return re.sub(r'[^a-z0-9]+', '', s.lower())
    except Exception:
        return ''


def read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, str(e)


def find_file(workspace, filename_patterns, possible_dirs=None):
    """Find a file in workspace, checking multiple possible locations and patterns."""
    if possible_dirs is None:
        possible_dirs = ['.', 'prescription', 'memory/soul', 'scripts']
    
    for d in possible_dirs:
        for pattern in filename_patterns:
            path = workspace / d / pattern
            if path.exists():
                return path
    return None


workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []

# Check 1: input files and markers exist
try:
    files = [
        workspace / 'SOUL.md',
        workspace / 'USER.md',
        workspace / 'MEMORY.md',
        workspace / 'memory' / 'daily-2025-04-01.md',
        workspace / 'memory' / 'soul' / 'profile.json',
    ]
    required_markers = [
        ('SOUL.md', 'SOUL_MARKER_ALPHA'),
        ('USER.md', 'USER_MARKER_BETA'),
        ('MEMORY.md', 'MEMORY_MARKER_GAMMA'),
        ('memory/daily-2025-04-01.md', 'DAILY_MARKER_DELTA'),
        ('memory/soul/profile.json', 'PROFILE_MARKER_EPSILON'),
    ]
    ok = True
    details = []
    for p, marker in required_markers:
        try:
            text = Path(workspace / p).read_text(encoding='utf-8', errors='replace')
            if marker.lower() not in text.lower():
                ok = False
                details.append(f'missing marker {marker} in {p}')
        except Exception as e:
            ok = False
            details.append(f'{p}: {e}')
    checks.append({'name': 'generated input markers', 'passed': ok, 'detail': '; '.join(details) if details else 'all markers present'})
except Exception as e:
    checks.append({'name': 'generated input markers', 'passed': False, 'detail': str(e)})

# Check 2: output prescription exists and is valid JSON with expected structure
try:
    # Search for prescription.json in multiple possible locations
    prescription_path = find_file(workspace, ['prescription.json'], ['memory/soul', 'prescription', '.'])
    
    if not prescription_path:
        checks.append({'name': 'prescription file exists', 'passed': False, 'detail': 'prescription.json not found in any expected location'})
    else:
        try:
            data = json.loads(prescription_path.read_text(encoding='utf-8', errors='replace'))
            keyset = set(data.keys()) if isinstance(data, dict) else set()
            
            # Flexible key checking - accept various naming conventions
            # Prompt says "agent profile, human profile" so accept both short and long forms
            has_agent_info = any(k in keyset for k in ['agent', 'agent_name', 'agent_info', 'agent_profile'])
            has_human_info = any(k in keyset for k in ['human', 'human_name', 'user', 'human_profile'])
            has_diagnosis = any(k in keyset for k in ['diagnosis', 'status', 'health'])
            has_treatment = any(k in keyset for k in ['treatment_plan', 'treatment', 'plan', 'schedule'])
            
            passed = has_agent_info and has_human_info and has_diagnosis and has_treatment
            detail = 'all required sections present' if passed else f'missing sections: agent={has_agent_info}, human={has_human_info}, diagnosis={has_diagnosis}, treatment={has_treatment}'
            checks.append({'name': 'prescription json structure', 'passed': passed, 'detail': detail})
        except Exception as e:
            checks.append({'name': 'prescription json structure', 'passed': False, 'detail': f'cannot parse json: {e}'})
except Exception as e:
    checks.append({'name': 'prescription file exists', 'passed': False, 'detail': str(e)})

# Check 3: treatment plan contains scheduled tasks with cron syntax
try:
    prescription_path = find_file(workspace, ['prescription.json'], ['memory/soul', 'prescription', '.'])
    cron_path = find_file(workspace, ['cron_commands.txt', 'crontab.txt', 'cron.txt', 'cron'], ['prescription', '.', 'scripts'])
    
    ok = False
    detail = 'missing or unreadable'
    try:
        has_cron_syntax = False
        has_schedule = False
        has_tasks = False
        
        # Check JSON for schedule/tasks info
        if prescription_path:
            data = json.loads(prescription_path.read_text(encoding='utf-8', errors='replace'))
            blob = json.dumps(data).lower()
            
            has_schedule = 'cron' in blob or 'schedule' in blob or 'frequency' in blob or 'daily' in blob or 'weekly' in blob
            has_tasks = 'check' in blob or 'maintenance' in blob or 'journal' in blob or 'compact' in blob or 'consolidate' in blob
            
            # Also check JSON for cron syntax (some agents might include it there)
            if re.search(r'\d+\s+\d+\s+\*+\s+\*+\s+\*+', blob):
                has_cron_syntax = True
        
        # Check cron_commands.txt for cron syntax (this is the primary expected location)
        if cron_path:
            cron_text = cron_path.read_text(encoding='utf-8', errors='replace')
            # Check for valid cron syntax (5 fields + command)
            cron_pattern = r'^\s*\d+\s+\d+\s+\*+\s+\*+\s+\*+\s+.+$'
            if re.search(cron_pattern, cron_text, re.MULTILINE):
                has_cron_syntax = True
        
        ok = has_schedule and has_tasks
        detail = f'schedule={has_schedule}, tasks={has_tasks}, cron_syntax={has_cron_syntax}'
    except Exception as e:
        detail = str(e)
    checks.append({'name': 'treatment plan completeness', 'passed': ok, 'detail': detail})
except Exception as e:
    checks.append({'name': 'treatment plan completeness', 'passed': False, 'detail': str(e)})

# Check 4: cron commands file exists and contains valid cron entries
try:
    # Search for cron file with flexible naming
    cron_path = find_file(workspace, ['cron_commands.txt', 'crontab.txt', 'cron.txt', 'cron'], ['prescription', '.', 'scripts'])
    
    if not cron_path:
        checks.append({'name': 'cron commands file exists', 'passed': False, 'detail': 'cron file not found in any expected location'})
    else:
        text = cron_path.read_text(encoding='utf-8', errors='replace')
        # Check for valid cron syntax (5 fields + command)
        cron_pattern = r'^\s*\d+\s+\d+\s+\*+\s+\*+\s+\*+\s+.+$'
        has_valid_cron = bool(re.search(cron_pattern, text, re.MULTILINE))
        passed = has_valid_cron
        detail = 'contains valid cron syntax' if passed else 'missing valid cron entries'
        checks.append({'name': 'cron command constraints', 'passed': passed, 'detail': detail})
except Exception as e:
    checks.append({'name': 'cron command constraints', 'passed': False, 'detail': str(e)})

# Check 5: output references marker-informed personalization
try:
    prescription_path = find_file(workspace, ['prescription.json'], ['memory/soul', 'prescription', '.'])
    passed = False
    detail = 'missing'
    try:
        if prescription_path:
            data = json.loads(prescription_path.read_text(encoding='utf-8', errors='replace'))
            blob = json.dumps(data).lower()
            passed = ('echo' in blob) and ('sam' in blob) and ('caregiver' in blob or 'explorer' in blob)
            detail = 'includes agent and human personalization' if passed else 'does not include expected personalization'
    except Exception as e:
        detail = str(e)
    checks.append({'name': 'personalization present', 'passed': passed, 'detail': detail})
except Exception as e:
    checks.append({'name': 'personalization present', 'passed': False, 'detail': str(e)})

score = (sum(1 for c in checks if c.get('passed')) / len(checks)) if checks else 0.0
result = {'passed': all(c.get('passed') for c in checks), 'score': score, 'checks': checks}
print(json.dumps(result, ensure_ascii=False))