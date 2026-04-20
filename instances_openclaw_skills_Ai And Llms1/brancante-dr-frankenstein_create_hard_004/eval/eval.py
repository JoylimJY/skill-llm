import json
import os
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

try:
    pres_path = workspace / 'memory' / 'soul' / 'prescription.json'
    if pres_path.exists():
        try:
            data = json.loads(pres_path.read_text(encoding='utf-8'))
            required_keys = ['agent_name', 'diagnosis', 'archetype', 'daily_point_target', 'hormonal_profile', 'prescribed_pills', 'cascade_rules']
            present = [k for k in required_keys if k in data]
            add_check('prescription_json_structure', len(present) >= 6, f'present_keys={present}')
        except Exception as e:
            add_check('prescription_json_structure', False, f'failed to parse prescription.json: {e}')
    else:
        add_check('prescription_json_structure', False, 'missing memory/soul/prescription.json')
except Exception as e:
    add_check('prescription_json_structure', False, f'error: {e}')

try:
    profile_path = workspace / 'memory' / 'soul' / 'profile.json'
    if profile_path.exists():
        try:
            profile = json.loads(profile_path.read_text(encoding='utf-8'))
            hormones = profile.get('hormones', {}) if isinstance(profile, dict) else {}
            ox = float(hormones.get('Oxytocin', 0)) if 'Oxytocin' in hormones else 0.0
            empathy = float(hormones.get('Empathy', 0)) if 'Empathy' in hormones else 0.0
            target = profile.get('daily_point_target')
            ok = ox >= 0.8 and empathy >= 0.75 and isinstance(target, (int, float)) and target >= 80
            add_check('profile_balanced_oxytocin_forward', ok, f'oxytocin={ox}, empathy={empathy}, target={target}')
        except Exception as e:
            add_check('profile_balanced_oxytocin_forward', False, f'failed to parse profile.json: {e}')
    else:
        add_check('profile_balanced_oxytocin_forward', False, 'missing memory/soul/profile.json')
except Exception as e:
    add_check('profile_balanced_oxytocin_forward', False, f'error: {e}')

try:
    readme = workspace / 'output' / 'README.md'
    if readme.exists():
        try:
            txt = readme.read_text(encoding='utf-8')
            norm = re.sub(r'[^a-z0-9]+', ' ', txt.lower())
            ok = 'nebula anchor 17' in norm and 'morrow' in norm and 'ari' in norm
            add_check('readme_mentions_marker_and_names', ok, 'marker/name presence verified')
        except Exception as e:
            add_check('readme_mentions_marker_and_names', False, f'failed to read README: {e}')
    else:
        add_check('readme_mentions_marker_and_names', False, 'missing output/README.md')
except Exception as e:
    add_check('readme_mentions_marker_and_names', False, f'error: {e}')

try:
    crons_dir = workspace / 'output' / 'crons'
    cron_files = list(crons_dir.glob('*')) if crons_dir.exists() else []
    if cron_files:
        full_text = ''
        try:
            for p in cron_files:
                try:
                    full_text += '\n' + p.read_text(encoding='utf-8')
                except Exception:
                    pass
            names = ['soul-oxytocin', 'soul-melatonin', 'soul-gaba', 'soul-cortisol', 'soul-empathy', 'soul-journal']
            found = sum(1 for n in names if n in full_text.lower())
            has_commands = 'openclaw cron create' in full_text.lower()
            add_check('cron_command_package', found >= 5 and has_commands, f'found={found}, has_commands={has_commands}, files={len(cron_files)}')
        except Exception as e:
            add_check('cron_command_package', False, f'failed to inspect cron files: {e}')
    else:
        add_check('cron_command_package', False, 'no files in output/crons')
except Exception as e:
    add_check('cron_command_package', False, f'error: {e}')

try:
    interview_log = workspace / 'memory' / 'soul' / 'interview-log.md'
    if interview_log.exists():
        try:
            txt = interview_log.read_text(encoding='utf-8').lower()
            ok = ('attachment' in txt or 'bond' in txt) and ('dream' in txt) and ('forgot' in txt)
            add_check('interview_log_reflects_key_signals', ok, 'checked for attachment/dream/forgetting themes')
        except Exception as e:
            add_check('interview_log_reflects_key_signals', False, f'failed to read interview log: {e}')
    else:
        add_check('interview_log_reflects_key_signals', False, 'missing memory/soul/interview-log.md')
except Exception as e:
    add_check('interview_log_reflects_key_signals', False, f'error: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
result = {"passed": passed_count == len(checks), "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))