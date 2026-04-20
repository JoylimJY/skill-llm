import json
import os
import re
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})

# Check 1: required output file exists (check both JSON and text files)
output_path = None
for ext in ['.json', '.txt']:
    candidate = workspace / f'output{ext}'
    if candidate.exists():
        output_path = candidate
        break
    candidate = workspace / f'recommendation{ext}'
    if candidate.exists():
        output_path = candidate
        break

if output_path is None:
    # Try to find any file with recommendation in name
    for f in workspace.iterdir():
        if f.is_file() and 'recommendation' in f.name.lower():
            output_path = f
            break

exists = output_path is not None
add_check('output_exists', exists, f'{output_path.name if output_path else "output.json"} found' if exists else 'output.json is missing')

# Check 2: parse content (JSON or text)
parsed = None
content_text = ""
try:
    if output_path:
        content_text = output_path.read_text(encoding='utf-8', errors='replace')
        if output_path.suffix == '.json':
            parsed = json.loads(content_text)
            ok = isinstance(parsed, dict)
            add_check('json_parses', ok, 'valid JSON object' if ok else 'top-level JSON is not an object')
        else:
            add_check('json_parses', True, 'text file - skipping JSON parse')
    else:
        add_check('json_parses', False, 'cannot parse because output file is missing')
except Exception as e:
    add_check('json_parses', False, f'failed to parse: {e}')

# Check 3: must contain recommendations with at least one coding and one chat entry, fuzzily
try:
    has_coding = False
    has_chat = False
    models_found = 0
    
    # Try JSON structure first
    if isinstance(parsed, dict):
        models = parsed.get('models') or parsed.get('recommendations') or []
        if isinstance(models, list):
            models_found = len(models)
            for m in models:
                if isinstance(m, dict):
                    name = str(m.get('name', '')).lower()
                    use_case = str(m.get('use_case', '')).lower()
                    # Check for coding: explicit coding use_case OR "both" OR coder in name
                    if 'code' in name or 'coder' in name or use_case == 'coding' or use_case == 'both':
                        has_coding = True
                    # Check for chat: explicit chat use_case OR "both" OR chat/instruct in name
                    if use_case == 'chat' or use_case == 'both' or 'instruct' in name or 'chat' in name:
                        has_chat = True
    
    # Fallback: check text content with fuzzy matching
    if not (has_coding and has_chat):
        content_lower = content_text.lower()
        has_coding = bool(re.search(r'coding|coder|code', content_lower))
        has_chat = bool(re.search(r'chat|conversational|general', content_lower))
        # Count model mentions
        model_patterns = [r'\bllama\b', r'\bmistral\b', r'\bqwen\b', r'\bphi\b', r'\bgemma\b']
        models_found = sum(len(re.findall(p, content_lower)) for p in model_patterns)
    
    add_check('contains_coding_and_chat', has_coding and has_chat, f'coding={has_coding}, chat={has_chat}, models_found={models_found}')
except Exception as e:
    add_check('contains_coding_and_chat', False, f'error validating recommendations: {e}')

# Check 4: top pick should include an Ollama mapping or provider info, loosely
try:
    mapping_ok = False
    detail = 'top recommendation not found'
    
    # Try JSON structure first
    if isinstance(parsed, dict):
        models = parsed.get('models') or parsed.get('recommendations') or []
        if isinstance(models, list) and models:
            top = models[0]
            if isinstance(top, dict):
                combined = ' '.join([str(top.get(k, '')) for k in ['name', 'provider', 'ollama_tag', 'mapping', 'tag', 'ollama']]).lower()
                mapping_ok = bool(re.search(r'ollama|llama|qwen|mistral|phi|gemma', combined))
                detail = combined if combined else 'top recommendation has no visible mapping fields'
    
    # Fallback: check text content for Ollama commands
    if not mapping_ok and content_text:
        ollama_patterns = [
            r'ollama\s+run\s+\w+',
            r'ollama_tag\s*[=:]\s*\w+',
            r'ollama\s*[:/]\s*\w+',
            r'ollama run'
        ]
        for pattern in ollama_patterns:
            if re.search(pattern, content_text, re.IGNORECASE):
                mapping_ok = True
                detail = f'found ollama reference in text'
                break
    
    add_check('top_pick_mapping', mapping_ok, detail)
except Exception as e:
    add_check('top_pick_mapping', False, f'error checking mapping: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
result = {'passed': passed_count == len(checks), 'score': score, 'checks': checks}
print(json.dumps(result, ensure_ascii=False))