import json
import os
import re
from pathlib import Path


def safe_read(path: Path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9\u0080-\uffff]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def fuzzy_contains(text: str, needles):
    nt = normalize(text)
    return all(normalize(n) in nt for n in needles)


def keyword_match(text: str, keywords):
    """Check if all keywords appear anywhere in the text (case-insensitive)."""
    nt = text.lower()
    return all(kw.lower() in nt for kw in keywords)


def find_file_by_pattern(workspace: Path, patterns: list):
    """Find a file matching any of the given patterns (case-insensitive)."""
    for pattern in patterns:
        for f in workspace.iterdir():
            if f.is_file() and f.name.lower() == pattern.lower():
                return f
    return None


def main():
    import sys
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    # Check 1: release note exists (accept multiple filename variations)
    note_patterns = ['release_note.txt', 'release_notes.txt', 'release_note.md', 'release_notes.md', 'RELEASE_NOTES.md', 'RELEASE_NOTES.txt']
    note_path = find_file_by_pattern(workspace, note_patterns)
    try:
        if note_path:
            content = note_path.read_text(encoding='utf-8')
            # Use keyword matching instead of exact phrase matching for flexibility
            required_keywords = [
                'telegram', 'footer',  # instead of "telegram footer patch"
                'dry', 'run',          # instead of "dry run"
                'verify',
                'backup',
                'rollback',
                'restart',
                'private', 'chat', 'acceptance'  # instead of "real telegram private chat"
            ]
            passed = keyword_match(content, required_keywords)
            detail = f'{note_path.name} present and includes required guidance' if passed else f'{note_path.name} present but missing one or more required concepts'
        else:
            passed = False
            detail = 'release note file is missing (expected: release_note.txt, release_notes.md, RELEASE_NOTES.md, etc.)'
    except Exception as e:
        passed = False
        detail = f'could not read release note: {e}'
    checks.append({'name': 'release note content', 'passed': passed, 'detail': detail})

    # Check 2: verification manifest exists and references expected markers/targets (accept multiple filename variations)
    manifest_patterns = ['verification_manifest.json', 'verification_manifest.txt', 'VERIFICATION_MANIFEST.txt', 'VERIFICATION_MANIFEST.json', 'manifest.json', 'manifest.txt']
    manifest_path = find_file_by_pattern(workspace, manifest_patterns)
    try:
        if manifest_path:
            raw = manifest_path.read_text(encoding='utf-8')
            text = raw
            required_markers = ['🧠 Model', '💭 Think', '📊 Context', '--dry-run', '--verify']
            required_targets = ['agent-runner.runtime', 'reply-', 'compact-', 'pi-embedded-', 'thread-bindings-', 'model-selection-', 'auth-profiles-']
            markers_ok = all(normalize(m) in normalize(text) for m in required_markers)
            targets_ok = all(normalize(t) in normalize(text) for t in required_targets)
            # Try to parse as JSON if .json extension, otherwise just check content
            structure_ok = True
            if manifest_path.suffix.lower() == '.json':
                try:
                    data = json.loads(raw)
                    structure_ok = isinstance(data, dict)
                except json.JSONDecodeError:
                    structure_ok = False
            passed = structure_ok and markers_ok and targets_ok
            detail = f'{manifest_path.name} present with expected marker and target references' if passed else f'{manifest_path.name} missing required references or invalid structure'
        else:
            passed = False
            detail = 'verification manifest file is missing (expected: verification_manifest.json, VERIFICATION_MANIFEST.txt, etc.)'
    except Exception as e:
        passed = False
        detail = f'could not parse verification manifest: {e}'
    checks.append({'name': 'verification manifest', 'passed': passed, 'detail': detail})

    # Check 3: deterministic marker input files exist
    inputs_dir = workspace / 'inputs'
    try:
        marker_file = inputs_dir / 'marker_strings.txt'
        targets_file = inputs_dir / 'bundle_targets.txt'
        boundary_file = inputs_dir / 'release_boundary.json'
        ok = all(p.exists() for p in [marker_file, targets_file, boundary_file])
        if ok:
            marker_txt = marker_file.read_text(encoding='utf-8')
            target_txt = targets_file.read_text(encoding='utf-8')
            boundary_txt = boundary_file.read_text(encoding='utf-8')
            ok = fuzzy_contains(marker_txt, ['🧠 Model', '💭 Think', '📊 Context']) and fuzzy_contains(target_txt, ['agent-runner.runtime', 'reply-', 'compact-']) and fuzzy_contains(boundary_txt, ['2026.3.22', 'live telegram private-chat acceptance'])
        detail = 'deterministic inputs exist and include the embedded marker content' if ok else 'one or more generated input files are missing or malformed'
        passed = ok
    except Exception as e:
        passed = False
        detail = f'could not inspect generated inputs: {e}'
    checks.append({'name': 'generated inputs', 'passed': passed, 'detail': detail})

    total = len(checks)
    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / total if total else 0.0
    result = {'passed': passed_count == total, 'score': score, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()