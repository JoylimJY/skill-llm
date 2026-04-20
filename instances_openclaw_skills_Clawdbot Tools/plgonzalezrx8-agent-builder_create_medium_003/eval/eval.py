import json
import re
from pathlib import Path
import sys


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8'), None
    except Exception as e:
        return None, str(e)


def fuzzy_contains(text, needles):
    if text is None:
        return False
    norm = re.sub(r'[^a-z0-9]+', ' ', text.lower())
    return all(re.sub(r'[^a-z0-9]+', ' ', n.lower()).strip() in norm for n in needles)


def main():
    checks = []
    ws = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    expected_files = [
        'IDENTITY.md', 'SOUL.md', 'AGENTS.md', 'USER.md', 'HEARTBEAT.md', 'MEMORY.md'
    ]
    for fname in expected_files:
        try:
            p = ws / fname
            ok = p.exists() and p.is_file()
            detail = 'exists' if ok else 'missing'
        except Exception as e:
            ok = False
            detail = f'error: {e}'
        checks.append({'name': f'file_{fname}', 'passed': ok, 'detail': detail})

    try:
        identity, err = safe_read(ws / 'IDENTITY.md')
        ok = fuzzy_contains(identity, ['OpsLighthouse', 'AI assistant']) if identity else False
        checks.append({'name': 'identity_content', 'passed': ok, 'detail': 'contains expected agent identity' if ok else f'bad or unreadable: {err}'})
    except Exception as e:
        checks.append({'name': 'identity_content', 'passed': False, 'detail': f'error: {e}'})

    try:
        soul, err = safe_read(ws / 'SOUL.md')
        # Use fuzzy matching for tone and policy keywords to handle variations like "Ask-Before-Destructive"
        ok = bool(soul) and fuzzy_contains(soul, ['professional', 'calm', 'concise', 'ask', 'before', 'destructive'])
        checks.append({'name': 'soul_policy', 'passed': ok, 'detail': 'persona and boundary language present' if ok else f'missing or malformed: {err}'})
    except Exception as e:
        checks.append({'name': 'soul_policy', 'passed': False, 'detail': f'error: {e}'})

    try:
        agents, err = safe_read(ws / 'AGENTS.md')
        # Use fuzzy matching for agent rules to allow flexible phrasing
        ok = bool(agents) and fuzzy_contains(agents, ['stop', 'cli', 'error', 'group', 'chat', 'delegation', 'ask', 'before', 'sending', 'outbound'])
        checks.append({'name': 'agents_rules', 'passed': ok, 'detail': 'operating rules present' if ok else f'missing rules: {err}'})
    except Exception as e:
        checks.append({'name': 'agents_rules', 'passed': False, 'detail': f'error: {e}'})

    try:
        user, err = safe_read(ws / 'USER.md')
        ok = bool(user) and fuzzy_contains(user, ['Team Lead', 'UTC'])
        checks.append({'name': 'user_profile', 'passed': ok, 'detail': 'user profile configured' if ok else f'missing or malformed: {err}'})
    except Exception as e:
        checks.append({'name': 'user_profile', 'passed': False, 'detail': f'missing or malformed: {err}'})

    try:
        heartbeat, err = safe_read(ws / 'HEARTBEAT.md')
        ok = bool(heartbeat) and 'daily ops triage' in heartbeat.lower()
        checks.append({'name': 'heartbeat_tiny', 'passed': ok, 'detail': 'heartbeat checklist includes ops triage' if ok else f'missing or malformed: {err}'})
    except Exception as e:
        checks.append({'name': 'heartbeat_tiny', 'passed': False, 'detail': f'missing or malformed: {err}'})

    try:
        memory, err = safe_read(ws / 'MEMORY.md')
        ok = bool(memory) and all(k in memory.lower() for k in ['telegram', 'discord', 'not the user'])
        checks.append({'name': 'memory_curated', 'passed': ok, 'detail': 'memory file includes durable guidance' if ok else f'missing or malformed: {err}'})
    except Exception as e:
        checks.append({'name': 'memory_curated', 'passed': False, 'detail': f'missing or malformed: {err}'})

    try:
        # Fuzzy match for seed memory - accept any date-based filename in memory directory
        memory_dir = ws / 'memory'
        seed_found = False
        if memory_dir.exists():
            for f in memory_dir.glob('*.md'):
                content = f.read_text(encoding='utf-8').lower()
                if 'marker: agent created' in content or 'agent created' in content or 'initialization' in content:
                    seed_found = True
                    break
        checks.append({'name': 'seed_memory_entry', 'passed': seed_found, 'detail': 'seed entry present' if seed_found else 'seed entry missing or marker absent'})
    except Exception as e:
        checks.append({'name': 'seed_memory_entry', 'passed': False, 'detail': f'error: {e}'})

    try:
        total = len(checks)
        passed_n = sum(1 for c in checks if c['passed'])
        score = passed_n / total if total else 0.0
        passed = passed_n == total
        print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))
    except Exception:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': checks}, ensure_ascii=False))


if __name__ == '__main__':
    main()