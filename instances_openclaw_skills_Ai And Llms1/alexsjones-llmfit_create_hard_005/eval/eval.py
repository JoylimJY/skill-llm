import json
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, e

try:
    output_path = workspace / 'output.json'
    if not output_path.exists():
        add_check('output_exists', False, 'output.json is missing')
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        sys.exit(0)

    try:
        data = json.loads(output_path.read_text(encoding='utf-8'))
    except Exception as e:
        add_check('valid_json', False, f'Could not parse output.json: {e}')
        data = None

    if isinstance(data, dict):
        # Use fuzzy matching for keys - allow variations
        required_keys = {'summary', 'recommendations', 'config'}
        actual_keys = set(data.keys())
        # Check if all required keys are present (case-insensitive)
        keys_match = all(any(k.lower() == req.lower() for k in actual_keys) for req in required_keys)
        add_check('has_required_keys', keys_match, f'keys={list(data.keys())}')

        summary = data.get('summary', {})
        recs = data.get('recommendations', [])
        config = data.get('config', {})

        try:
            summary_text = json.dumps(summary).lower()
            # Fuzzy match for Apple M2 Max
            has_m2 = re.search(r'apple\s*m2\s*max', summary_text, re.IGNORECASE) is not None
            add_check('mentions_apple_m2_max', has_m2, summary_text[:200])
        except Exception as e:
            add_check('mentions_apple_m2_max', False, f'error: {e}')

        try:
            # Fuzzy match for unified memory
            has_unified = re.search(r'unified\s*memory', json.dumps(summary).lower(), re.IGNORECASE) is not None
            add_check('mentions_unified_memory', has_unified, 'summary inspected')
        except Exception as e:
            add_check('mentions_unified_memory', False, f'error: {e}')

        try:
            add_check('recommendation_count', isinstance(recs, list) and len(recs) >= 2, f'count={len(recs) if isinstance(recs, list) else "n/a"}')
        except Exception as e:
            add_check('recommendation_count', False, f'error: {e}')

        try:
            joined = ' '.join(json.dumps(r).lower() for r in recs if isinstance(r, dict))
            # Fuzzy match for Qwen2.5-Coder
            has_coding = re.search(r'qwen2\.5.*coder.*7b', joined, re.IGNORECASE) is not None
            add_check('contains_coding_model', has_coding, joined[:300])
        except Exception as e:
            add_check('contains_coding_model', False, f'error: {e}')

        try:
            # Fuzzy match for Llama 3.1 8B
            has_chat = re.search(r'llama.*3\.1.*8b', json.dumps(recs).lower(), re.IGNORECASE) is not None
            add_check('contains_chat_model', has_chat, 'recommendations inspected')
        except Exception as e:
            add_check('contains_chat_model', False, f'error: {e}')

        try:
            ollama = config.get('ollama', {}) if isinstance(config, dict) else {}
            # Check that ollama config has some reasonable keys
            ollama_keys = set(ollama.keys()) if isinstance(ollama, dict) else set()
            has_ollama = len(ollama_keys) >= 2 or 'notes' in ollama_keys
            add_check('ollama_tag_mapping', has_ollama, json.dumps(ollama)[:200])
        except Exception as e:
            add_check('ollama_tag_mapping', False, f'error: {e}')

        try:
            lmstudio = config.get('lmstudio', {}) if isinstance(config, dict) else {}
            # Check for actual LM Studio configuration parameters
            lmstudio_keys = set(lmstudio.keys()) if isinstance(lmstudio, dict) else set()
            lmstudio_text = json.dumps(lmstudio).lower()
            # Look for common LM Studio config keys or values
            has_lmstudio = (
                len(lmstudio_keys) >= 2 or
                re.search(r'(device|gpu_layers|context_size|context_length|flash_attention|main_gpu)', lmstudio_text, re.IGNORECASE) is not None
            )
            add_check('lmstudio_mapping', has_lmstudio, json.dumps(lmstudio)[:200])
        except Exception as e:
            add_check('lmstudio_mapping', False, f'error: {e}')
    else:
        add_check('has_required_keys', False, 'output.json is not a JSON object')

except Exception as e:
    add_check('eval_runtime', False, f'Unexpected evaluator error: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
passed = all(c['passed'] for c in checks) if checks else False
print(json.dumps({"passed": passed, "score": score, "checks": checks}))