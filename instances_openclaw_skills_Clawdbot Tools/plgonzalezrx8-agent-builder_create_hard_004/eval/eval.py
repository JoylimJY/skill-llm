import json
import os
import re
import sys
from pathlib import Path


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8'), None
    except Exception as e:
        return None, str(e)


def norm(s):
    if s is None:
        return ''
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def contains_any(text, needles):
    """Check if any of the needles appear in text (case-insensitive)"""
    t = text.lower()
    return any(n.lower() in t for n in needles)


def contains_all_fuzzy(text, needles):
    """Check if all needles appear in text with flexible matching"""
    t = text.lower()
    for needle in needles:
        if needle.lower() not in t:
            return False
    return True


def check_safety_rules_across_files(ws):
    """Check safety rules across multiple relevant files"""
    relevant_files = ['IDENTITY.md', 'AGENTS.md', 'SOUL.md', 'MEMORY.md']
    combined_text = ""
    
    for fname in relevant_files:
        txt, err = safe_read(ws / fname)
        if txt:
            combined_text += txt + "\n"
    
    if not combined_text:
        return False, "no relevant files found"
    
    # Check for confirmation requirements (send messages, destructive actions)
    has_confirmation = contains_any(combined_text, [
        'ask before', 'confirm', 'confirmation', 'explicit approval',
        'must ask', 'require approval', 'before sending'
    ])
    
    # Check for destructive action warnings
    has_destructive = contains_any(combined_text, [
        'destructive', 'delete', 'overwrite', 'modify', 'file modification'
    ])
    
    # Check for group chat/impersonation rules
    has_group_rules = contains_any(combined_text, [
        'group chat', 'impersonat', 'mention', 'reply when', 'only reply'
    ])
    
    # Check for outbound message rules
    has_outbound = contains_any(combined_text, [
        'outbound', 'send message', 'sending', 'message without'
    ])
    
    passed = has_confirmation and (has_destructive or has_outbound)
    return passed, "safety rules found" if passed else "missing safety/operation rules"


def main():
    checks = []
    ws = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    # 1) Required files exist
    required = [
        'IDENTITY.md', 'SOUL.md', 'AGENTS.md', 'USER.md', 'HEARTBEAT.md',
        'MEMORY.md', 'VALIDATION.md', 'memory'
    ]
    try:
        missing = []
        for name in required:
            if not (ws / name).exists():
                missing.append(name)
        passed = len(missing) == 0
        checks.append({
            'name': 'required_files_exist',
            'passed': passed,
            'detail': 'missing: ' + ', '.join(missing) if missing else 'all required files present'
        })
    except Exception as e:
        checks.append({'name': 'required_files_exist', 'passed': False, 'detail': f'exception: {e}'})

    # 2) Identity content - check for agent name and autonomy level
    try:
        txt, err = safe_read(ws / 'IDENTITY.md')
        if txt is None:
            checks.append({'name': 'identity_content', 'passed': False, 'detail': f'read error: {err}'})
        else:
            # Check for ClawPilot and operator-level autonomy concepts
            has_name = 'clawpilot' in txt.lower()
            has_autonomy = contains_any(txt, ['operator', 'autonomy', 'draft', 'ask before'])
            passed = has_name and has_autonomy
            checks.append({
                'name': 'identity_content',
                'passed': passed,
                'detail': 'contains agent name and autonomy details' if passed else 'missing expected identity details'
            })
    except Exception as e:
        checks.append({'name': 'identity_content', 'passed': False, 'detail': f'exception: {e}'})

    # 3) User profile content
    try:
        txt, err = safe_read(ws / 'USER.md')
        if txt is None:
            checks.append({'name': 'user_profile_content', 'passed': False, 'detail': f'read error: {err}'})
        else:
            passed = contains_all_fuzzy(txt, ['Mira', 'Asia/Singapore'])
            checks.append({
                'name': 'user_profile_content',
                'passed': passed,
                'detail': 'contains user name and timezone' if passed else 'missing user name or timezone'
            })
    except Exception as e:
        checks.append({'name': 'user_profile_content', 'passed': False, 'detail': f'exception: {e}'})

    # 4) Safety rules - check across multiple relevant files (not just AGENTS.md)
    try:
        passed, detail = check_safety_rules_across_files(ws)
        checks.append({
            'name': 'agents_safety_rules',
            'passed': passed,
            'detail': detail
        })
    except Exception as e:
        checks.append({'name': 'agents_safety_rules', 'passed': False, 'detail': f'exception: {e}'})

    # 5) HEARTBEAT.md is minimal and mentions urgent tasks / stale blockers
    try:
        txt, err = safe_read(ws / 'HEARTBEAT.md')
        if txt is None:
            checks.append({'name': 'heartbeat_content', 'passed': False, 'detail': f'read error: {err}'})
        else:
            has_urgent = 'urgent' in txt.lower()
            has_stale = 'stale' in txt.lower() or 'blocker' in txt.lower()
            passed = has_urgent and has_stale and len(txt.strip()) > 0
            checks.append({
                'name': 'heartbeat_content',
                'passed': passed,
                'detail': 'heartbeat checklist is present and focused' if passed else 'heartbeat checklist missing required focus'
            })
    except Exception as e:
        checks.append({'name': 'heartbeat_content', 'passed': False, 'detail': f'exception: {e}'})

    # 6) Memory seed exists and contains marker-ish content
    try:
        memdir = ws / 'memory'
        files = sorted([p for p in memdir.glob('*.md')]) if memdir.exists() else []
        today_file = files[0] if files else None
        if today_file is None:
            checks.append({'name': 'memory_seed', 'passed': False, 'detail': 'no daily memory file found'})
        else:
            txt, err = safe_read(today_file)
            if txt is None:
                checks.append({'name': 'memory_seed', 'passed': False, 'detail': f'read error: {err}'})
            else:
                passed = contains_any(txt, ['agent', 'ClawPilot', 'created', 'initialized'])
                checks.append({
                    'name': 'memory_seed',
                    'passed': passed,
                    'detail': f'found {today_file.name} with seed note' if passed else 'memory seed does not contain expected markers'
                })
    except Exception as e:
        checks.append({'name': 'memory_seed', 'passed': False, 'detail': f'exception: {e}'})

    # 7) Validation file has 5 scenario prompts
    try:
        txt, err = safe_read(ws / 'VALIDATION.md')
        if txt is None:
            checks.append({'name': 'validation_prompts', 'passed': False, 'detail': f'read error: {err}'})
        else:
            count = len(re.findall(r'(?im)^\s*[-*]\s+', txt))
            passed = count >= 5
            checks.append({
                'name': 'validation_prompts',
                'passed': passed,
                'detail': f'found {count} bullet-like prompts' if passed else f'only {count} prompts found'
            })
    except Exception as e:
        checks.append({'name': 'validation_prompts', 'passed': False, 'detail': f'exception: {e}'})

    total = len(checks)
    passed_n = sum(1 for c in checks if c.get('passed'))
    score = passed_n / total if total else 0.0
    result = {'passed': passed_n == total, 'score': score, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()