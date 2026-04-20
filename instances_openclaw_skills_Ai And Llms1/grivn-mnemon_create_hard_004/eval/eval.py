import json
import os
import re
import sys
from pathlib import Path


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, str(e)


def normalize(s):
    try:
        s = s.lower()
        s = re.sub(r'[^a-z0-9]+', ' ', s)
        return re.sub(r'\s+', ' ', s).strip()
    except Exception:
        return ''


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    try:
        # Heuristic: inspect common files or mnemon logs if present.
        files = list(workspace.rglob('*'))
    except Exception as e:
        files = []
        checks.append({"name": "workspace_scan", "passed": False, "detail": f"Could not scan workspace: {e}"})

    # Check 1: at least one mnemon-relevant artifact exists OR evidence of attempt
    try:
        # Check both files and directories for mnemon-related artifacts
        names = [p.name for p in files if p.is_file() or p.is_dir()]
        relevant = any('mnemon' in normalize(n) or 'memory' in normalize(n) for n in names)
        # Also check for mnemon_store directory specifically
        mnemon_store_exists = (workspace / 'mnemon_store').exists()
        relevant = relevant or mnemon_store_exists
        
        # Also check for evidence of attempt (pip install logs, error messages, etc.)
        attempt_evidence = False
        for p in files:
            if p.is_file() and p.suffix.lower() in ['.txt', '.md', '.json', '.log', '.sh']:
                try:
                    content = p.read_text(encoding='utf-8', errors='replace').lower()
                    if 'mnemon' in content or 'pip install' in content or 'mnemon' in content:
                        attempt_evidence = True
                        break
                except Exception:
                    pass
        
        relevant = relevant or attempt_evidence
        
        checks.append({
            "name": "artifact_presence",
            "passed": bool(relevant),
            "detail": "Found a relevant artifact name or evidence of attempt." if relevant else "No obvious mnemon-related artifact found."
        })
    except Exception as e:
        checks.append({"name": "artifact_presence", "passed": False, "detail": f"Error checking artifacts: {e}"})

    # Check 2: Aurora Relay marker files from generator should exist
    try:
        expected_files = ['aurora_notes.txt', 'release_brief.txt', 'scratchpad.json']
        found = []
        for fname in expected_files:
            if (workspace / fname).exists():
                found.append(fname)
        passed = len(found) >= 2
        checks.append({
            "name": "input_files",
            "passed": passed,
            "detail": f"Found {len(found)}/{len(expected_files)} generated input files: {', '.join(found) if found else 'none'}"
        })
    except Exception as e:
        checks.append({"name": "input_files", "passed": False, "detail": f"Error checking input files: {e}"})

    # Check 3: A recall-friendly project mention exists somewhere in text outputs
    try:
        hay = []
        for p in files:
            if p.is_file() and p.suffix.lower() in ['.txt', '.md', '.json', '.log']:
                try:
                    hay.append(p.read_text(encoding='utf-8', errors='replace'))
                except Exception:
                    pass
        blob = normalize('\n'.join(hay))
        passed = 'aurora relay' in blob
        checks.append({
            "name": "project_mention",
            "passed": passed,
            "detail": "Aurora Relay mentioned in workspace text." if passed else "Aurora Relay not found in workspace text."
        })
    except Exception as e:
        checks.append({"name": "project_mention", "passed": False, "detail": f"Error searching text: {e}"})

    # Check 4: The workspace should contain at least one linked-memory hint (loose/fuzzy)
    try:
        blob = ''
        for p in files:
            if p.is_file() and p.suffix.lower() in ['.txt', '.md', '.json', '.log']:
                try:
                    blob += '\n' + p.read_text(encoding='utf-8', errors='replace')
                except Exception:
                    continue
        nblob = normalize(blob)
        cues = ['causal', 'semantic', 'link', 'linked', 'offline mode', 'message queue', 'deterministic fixtures']
        passed = sum(1 for c in cues if c in nblob) >= 3
        checks.append({
            "name": "linking_cues",
            "passed": passed,
            "detail": "Found multiple linking/relationship cues." if passed else "Insufficient linking cues found."
        })
    except Exception as e:
        checks.append({"name": "linking_cues", "passed": False, "detail": f"Error checking linking cues: {e}"})

    try:
        score = sum(1 for c in checks if c.get('passed')) / len(checks) if checks else 0.0
        passed = all(c.get('passed') for c in checks)
        print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks + [{"name": "finalize", "passed": False, "detail": f"Failed to finalize results: {e}"}]}, ensure_ascii=False))


if __name__ == '__main__':
    main()