import json
import os
import re
import sys
from pathlib import Path


def norm(s):
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    checks = []

    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    # 1) sap-helper routing spec exists (handoff note with usage guidance)
    try:
        # Search for any file containing "sap-helper" in the name
        candidates = []
        for p in workspace.rglob('*'):
            if p.is_file() and 'sap-helper' in p.name.lower():
                candidates.append(p)
        
        found = None
        for c in candidates:
            if c.exists():
                found = c
                break
        
        if found is None:
            add_check("sap-helper spec exists", False, "Could not find sap-helper routing spec in expected locations.")
        else:
            txt = found.read_text(encoding='utf-8', errors='ignore')
            n = norm(txt)
            # Check for essential handoff content: usage guidance and escalation criteria
            ok = ('sap' in n) and (
                ('when to use' in n or 'delegate' in n or 'use' in n) and
                ('escalat' in n or 'approval' in n or 'human' in n)
            )
            add_check("sap-helper spec exists", ok, f"Found {found.name}; required routing markers {'present' if ok else 'missing'}.")
    except Exception as e:
        add_check("sap-helper spec exists", False, f"Error while checking spec: {e}")

    # 2) registry updated with sap-helper agent
    try:
        reg_path = workspace / 'references' / 'agent-registry.json'
        if not reg_path.exists():
            add_check("registry updated", False, "agent-registry.json is missing.")
        else:
            data = json.loads(reg_path.read_text(encoding='utf-8'))
            agents = data.get('agents', []) if isinstance(data, dict) else []
            
            # Find sap-helper agent
            sap_helper = None
            for a in agents:
                try:
                    if norm(a.get('id', '')) in ['saphelper', 'sap-helper'] or norm(a.get('name', '')) == 'saphelper':
                        sap_helper = a
                        break
                except Exception:
                    continue
            
            # Find main agent
            main_agent = None
            for a in agents:
                try:
                    if norm(a.get('id', '')) == 'main' or norm(a.get('name', '')) == 'clawdia':
                        main_agent = a
                        break
                except Exception:
                    continue
            
            if sap_helper is None:
                add_check("registry updated", False, "No sap-helper-like agent found in registry.")
            else:
                reports_to = sap_helper.get('reports_to', {}) if isinstance(sap_helper, dict) else {}
                req = sap_helper.get('requires_approval', None)
                ok = True
                detail_bits = []
                
                # Check sap-helper has proper id
                ok &= norm(sap_helper.get('id')) in {'saphelper', 'sap-helper'}
                detail_bits.append(f"id={sap_helper.get('id')}")
                
                # Check sap-helper reports to main agent
                ok &= isinstance(reports_to, dict) and reports_to.get('type') in {'agent', 'human'}
                detail_bits.append(f"reports_to={reports_to}")
                
                # Check requires_approval is set
                ok &= req in {True, False}
                detail_bits.append(f"requires_approval={req}")
                
                # Check main agent can assign to sap-helper
                if main_agent:
                    main_can_assign = main_agent.get('can_assign_to', [])
                    if isinstance(main_can_assign, list):
                        ok &= any(norm(x) in ['saphelper', 'sap-helper'] for x in main_can_assign)
                        detail_bits.append(f"main.can_assign_to={main_can_assign}")
                    else:
                        ok = False
                        detail_bits.append("main.can_assign_to is not a list")
                else:
                    ok = False
                    detail_bits.append("main agent not found")
                
                add_check("registry updated", ok, "; ".join(detail_bits))
    except Exception as e:
        add_check("registry updated", False, f"Error while parsing registry: {e}")

    # 3) handoff note exists with escalation guidance and marker
    try:
        # Search for any markdown file containing handoff/escalation content
        candidates = []
        for p in workspace.rglob('*'):
            if p.is_file() and p.suffix.lower() in {'.md', '.txt'}:
                candidates.append(p)
        
        found = None
        for c in candidates:
            if c.exists():
                txt = c.read_text(encoding='utf-8', errors='ignore')
                n = norm(txt)
                # Check for handoff-related content
                if ('handoff' in n or 'when to use' in n or 'escalat' in n) and 'sap' in n:
                    found = c
                    break
        
        if found is None:
            add_check("handoff note", False, "handoff note not found in expected locations.")
        else:
            txt = found.read_text(encoding='utf-8', errors='ignore')
            n = norm(txt)
            ok = ('sap' in n) and ('escalat' in n or 'human' in n or 'approval' in n)
            add_check("handoff note", ok, f"Found {found.name}; escalation guidance {'present' if ok else 'missing'}.")
    except Exception as e:
        add_check("handoff note", False, f"Error while checking handoff note: {e}")

    # 4) main agent delegation updated to include sap-helper somewhere in workspace text files
    try:
        hits = []
        for p in workspace.rglob('*'):
            if p.is_file() and p.suffix.lower() in {'.md', '.json', '.txt', '.yaml', '.yml'}:
                try:
                    txt = p.read_text(encoding='utf-8', errors='ignore')
                    if 'sap' in norm(txt) and ('helper' in norm(txt) or 'sap-helper' in txt.lower()):
                        hits.append(str(p.relative_to(workspace)))
                except Exception:
                    continue
        ok = len(hits) > 0
        add_check("delegation references", ok, f"Found SAP delegation references in: {', '.join(hits[:5]) if hits else 'none'}.")
    except Exception as e:
        add_check("delegation references", False, f"Error while scanning workspace: {e}")

    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / len(checks) if checks else 0.0
    result = {"passed": passed_count == len(checks), "score": score, "checks": checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()