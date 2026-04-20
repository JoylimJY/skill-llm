import json
from pathlib import Path

root = Path('.')
(root / 'skills' / 'arya-model-router').mkdir(parents=True, exist_ok=True)

rules = {
    "models": {
        "cheap": "openai/gpt-4o-mini",
        "default": "openai/gpt-4.1-mini",
        "pro": "openai/gpt-4.1",
        "ultra": "openai/gpt-4.1"
    },
    "overrides": {
        "tag_map": {
            "@cheap": "cheap",
            "@default": "default",
            "@pro": "pro",
            "@ultra": "ultra"
        },
        "commands": {
            "router status": True,
            "router auto on": True,
            "router auto off": True,
            "router force cheap": True,
            "router force default": True,
            "router force pro": True,
            "router force ultra": True,
            "router force off": True
        }
    },
    "thresholds": {
        "heavy_score": 6,
        "default_score": 3,
        "max_context_chars_for_pro": 12000
    },
    "signals": {
        "daily_report_keywords": ["daily report", "reporte diario", "summary"],
        "heavy_keywords": ["refactor", "debug", "traceback", "optimize", "integration", "analysis"],
        "light_keywords": ["thanks", "ok", "simple", "brief"]
    },
    "response_policies": {
        "cheap": {"max_words": 120, "style": "short"},
        "default": {"max_words": 180, "style": "concise"},
        "pro": {"max_words": 260, "style": "detailed"},
        "ultra": {"max_words": 320, "style": "very detailed"}
    }
}

state = {
    "mode": "auto",
    "lastDecision": None,
    "feedback": {"too_expensive": 1, "too_weak": 0},
    "forced_level": None
}

readme = """# Arya Model Router (Token Saver)

This repository contains a lightweight router that decides whether a request should stay on a cheap model or escalate to a stronger one.

## Features

- Manual overrides with tags like `@cheap` and `@pro`
- Router commands for status and auto mode
- Persistent `forced_level` control via:
  - `router force cheap`
  - `router force default`
  - `router force pro`
  - `router force ultra`
  - `router force off`
- Brief-first suggestion when context is too large for a strong model
- Response policies per tier

## Behavior notes

- `router force <level>` must win above scoring, feedback, and auto mode.
- `router force off` clears the forced level.
- Large contexts should trigger a brief-first action before using `pro` or `ultra`.
"""

router_py = """#!/usr/bin/env python3
import argparse
import json
import os
import re

STATE_PATH = os.path.join(os.path.dirname(__file__), 'state.json')


def load_json(path, default):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, obj):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def tokenize(text):
    return re.findall(r"[\\wáéíóúñü]+", text.lower())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--text', required=True)
    ap.add_argument('--context-chars', type=int, default=0)
    ap.add_argument('--rules', default=os.path.join(os.path.dirname(__file__), 'rules.json'))
    ap.add_argument('--state', default=STATE_PATH)
    args = ap.parse_args()

    rules = load_json(args.rules, {})
    state = load_json(args.state, {"mode": "auto", "lastDecision": None, "feedback": {"too_expensive": 0, "too_weak": 0}, "forced_level": None})

    text = args.text.strip().lower()
    forced = state.get('forced_level')

    if text == 'router force off':
        state['forced_level'] = None
        save_json(args.state, state)
        print(json.dumps({"ok": True, "forced_level": None, "mode": state.get('mode', 'auto')}, ensure_ascii=False))
        return

    if text.startswith('router force '):
        target = text.replace('router force ', '', 1).strip()
        if target in ('cheap', 'default', 'pro', 'ultra'):
            state['forced_level'] = target
            save_json(args.state, state)
            print(json.dumps({"ok": True, "forced_level": target, "mode": state.get('mode', 'auto')}, ensure_ascii=False))
            return

    if forced in ('cheap', 'default', 'pro', 'ultra'):
        level = forced
        model = rules.get('models', {}).get(level, rules.get('models', {}).get('default'))
        actions = ['use_subagent'] if level in ('pro', 'ultra') else ['stay_main']
        if args.context_chars > int(rules.get('thresholds', {}).get('max_context_chars_for_pro', 12000)) and level in ('pro', 'ultra'):
            actions.insert(0, 'brief_first')
        out = {
            'mode': state.get('mode', 'auto'),
            'level': level,
            'model': model,
            'score': 0,
            'reasons': ['forced override active'],
            'actions': actions,
            'response_policy': rules.get('response_policies', {}).get(level, {}),
            'helper_scripts': {'brief': 'python3 skills/arya-model-router/brief.py --max-chars 4000 < context.txt'}
        }
        state['lastDecision'] = {k: out[k] for k in ('level', 'model', 'score', 'actions')}
        save_json(args.state, state)
        print(json.dumps(out, ensure_ascii=False))
        return

    tokens = tokenize(args.text)
    score = 0
    if len(args.text) > 1500:
        score += 2
    if len(args.text) > 5000:
        score += 2
    if any(k in ' '.join(tokens) for k in rules.get('signals', {}).get('heavy_keywords', [])):
        score += 2

    if score >= int(rules.get('thresholds', {}).get('heavy_score', 6)):
        level = 'pro'
    elif score >= int(rules.get('thresholds', {}).get('default_score', 3)):
        level = 'default'
    else:
        level = 'cheap'

    model = rules.get('models', {}).get(level, rules.get('models', {}).get('default'))
    actions = ['use_subagent'] if level in ('pro', 'ultra') else ['stay_main']
    out = {
        'mode': state.get('mode', 'auto'),
        'level': level,
        'model': model,
        'score': score,
        'reasons': [],
        'actions': actions,
        'response_policy': rules.get('response_policies', {}).get(level, {}),
        'helper_scripts': {'brief': 'python3 skills/arya-model-router/brief.py --max-chars 4000 < context.txt'}
    }
    state['lastDecision'] = {k: out[k] for k in ('level', 'model', 'score', 'actions')}
    save_json(args.state, state)
    print(json.dumps(out, ensure_ascii=False))


if __name__ == '__main__':
    main()
"""

brief_py = """#!/usr/bin/env python3
import argparse
import sys

p = argparse.ArgumentParser()
p.add_argument('--max-chars', type=int, default=4000)
args = p.parse_args()
text = sys.stdin.read()
summary = text[:args.max_chars]
print(summary)
"""

(root / 'skills' / 'arya-model-router' / 'rules.json').write_text(json.dumps(rules, ensure_ascii=False, indent=2), encoding='utf-8')
(root / 'skills' / 'arya-model-router' / 'state.json').write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
(root / 'skills' / 'arya-model-router' / 'README.md').write_text(readme, encoding='utf-8')
(root / 'skills' / 'arya-model-router' / 'router.py').write_text(router_py, encoding='utf-8')
(root / 'skills' / 'arya-model-router' / 'brief.py').write_text(brief_py, encoding='utf-8')
