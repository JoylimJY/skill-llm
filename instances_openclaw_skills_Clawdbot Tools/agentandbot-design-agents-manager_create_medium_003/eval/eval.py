import json
import os
import re
import sys
from pathlib import Path

checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def normalize(text):
    try:
        return re.sub(r'[^a-z0-9]+', '', text.lower())
    except Exception:
        return ''


def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    # Check 1: sap-router-card.json exists
    try:
        card_path = workspace / 'sap-router-card.json'
        if card_path.exists():
            add_check('card_exists', True, 'sap-router-card.json found')
        else:
            add_check('card_exists', False, 'sap-router-card.json is missing')
    except Exception as e:
        add_check('card_exists', False, f'Error checking existence: {e}')

    # Check 2: routing-summary.txt exists
    try:
        summary_path = workspace / 'routing-summary.txt'
        if summary_path.exists():
            add_check('summary_exists', True, 'routing-summary.txt found')
        else:
            add_check('summary_exists', False, 'routing-summary.txt is missing')
    except Exception as e:
        add_check('summary_exists', False, f'Error checking existence: {e}')

    # Check 3: card json structure and key fields
    try:
        raw = None
        err = None
        try:
            raw = (workspace / 'sap-router-card.json').read_text(encoding='utf-8')
        except Exception as e:
            err = str(e)
        if raw is None:
            add_check('card_json_parse', False, f'Cannot read card file: {err}')
        else:
            try:
                data = json.loads(raw)
                required = ['id', 'name', 'model', 'capabilities', 'reports_to', 'can_assign_to', 'requires_approval', 'auto_accept_from', 'communication', 'escalation_path', 'agent_card']
                missing = [k for k in required if k not in data]
                if missing:
                    add_check('card_json_parse', False, f'Missing required keys: {", ".join(missing)}')
                else:
                    add_check('card_json_parse', True, 'All required keys present')
            except Exception as e:
                add_check('card_json_parse', False, f'Invalid JSON: {e}')
    except Exception as e:
        add_check('card_json_parse', False, f'Unexpected error: {e}')

    # Check 4: task reference code appears in card exactly once, forgiving whitespace/case
    try:
        seed_text = None
        err = None
        try:
            seed_text = (workspace / 'task_seed.txt').read_text(encoding='utf-8')
        except Exception as e:
            err = str(e)
        if seed_text is None:
            add_check('task_code_present', False, f'Cannot read task_seed.txt: {err}')
        else:
            m = re.search(r'TASK-REF:\s*([A-Z0-9\-]+)', seed_text, re.I)
            task_code = m.group(1) if m else 'SAP-ROUTER-ALPHA-17'
            try:
                card_text = (workspace / 'sap-router-card.json').read_text(encoding='utf-8')
                count = len(re.findall(re.escape(task_code), card_text, flags=re.I))
                if count >= 1:
                    add_check('task_code_present', True, f'Task code {task_code} found {count} time(s) in card')
                else:
                    add_check('task_code_present', False, f'Task code {task_code} not found in card')
            except Exception as e:
                add_check('task_code_present', False, f'Cannot read card for task code check: {e}')
    except Exception as e:
        add_check('task_code_present', False, f'Unexpected error: {e}')

    # Check 5: card is SAP-focused and reports to main/Ilkerkaan
    try:
        try:
            data = json.loads((workspace / 'sap-router-card.json').read_text(encoding='utf-8'))
            hay = json.dumps(data, ensure_ascii=False)
            n = normalize(hay)
            sap_ok = 'sap' in n or 'hana' in n or 'idoc' in n or 's4hana' in n
            reports_ok = 'main' in normalize(str(data.get('reports_to', ''))) or 'ilkerkaan' in normalize(json.dumps(data.get('reports_to', {}), ensure_ascii=False))
            if sap_ok and reports_ok:
                add_check('sap_and_routing', True, 'Card references SAP and reports to main/Ilkerkaan')
            else:
                add_check('sap_and_routing', False, f'SAP focus: {sap_ok}, reports_to okay: {reports_ok}')
        except Exception as e:
            add_check('sap_and_routing', False, f'Cannot evaluate card contents: {e}')
    except Exception as e:
        add_check('sap_and_routing', False, f'Unexpected error: {e}')

    total = len(checks)
    passed = sum(1 for c in checks if c['passed'])
    score = (passed / total) if total else 0.0
    result = {"passed": passed == total, "score": score, "checks": checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
