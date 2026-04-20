import json
import os
import re
import sys
from pathlib import Path


def safe_read(path: Path):
    try:
        return path.read_text(encoding='utf-8'), None
    except Exception as e:
        return None, str(e)


def normalize(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '', text.lower())


def main():
    workspace = Path(sys.argv[1])
    # Check both workspace root and output subdirectory for generated files
    search_paths = [workspace / 'output', workspace]
    
    checks = []
    marker = 'NORTHSTAR-LAUNCH-2025'
    expected_files = [
        'README.md',
        'release-notes.md',
        'launch-manifest.json',
    ]

    # Find where files actually exist
    file_paths = {}
    for filename in expected_files:
        for search_path in search_paths:
            full_path = search_path / filename
            if full_path.exists():
                file_paths[filename] = full_path
                break
        if filename not in file_paths:
            file_paths[filename] = None

    for filename in expected_files:
        path = file_paths.get(filename)
        if path is None or not path.exists():
            checks.append({'name': f'{filename} exists', 'passed': False, 'detail': 'file is missing'})
            continue
        content, err = safe_read(path)
        if err:
            checks.append({'name': f'{filename} readable', 'passed': False, 'detail': err})
            continue
        has_marker = marker.lower() in content.lower()
        checks.append({'name': f'{filename} contains marker', 'passed': bool(has_marker), 'detail': 'marker found' if has_marker else 'marker not found'})

    manifest_path = file_paths.get('launch-manifest.json')
    manifest_ok = False
    manifest_detail = 'manifest not checked'
    try:
        if manifest_path and manifest_path.exists():
            data = json.loads(manifest_path.read_text(encoding='utf-8'))
            project_ok = 'northstar' in normalize(str(data.get('project', '')))
            assets = data.get('assets', None)
            # Accept assets as either a non-empty list OR a non-empty dict (nested structure)
            if isinstance(assets, list):
                assets_ok = len(assets) > 0
            elif isinstance(assets, dict):
                assets_ok = len(assets) > 0
            else:
                assets_ok = False
            # Fix: normalize both sides of the marker comparison
            marker_value = str(data.get('marker', ''))
            marker_normalized = normalize(marker_value)
            marker_expected_normalized = normalize(marker)
            marker_ok = marker_expected_normalized in marker_normalized or marker_normalized in marker_expected_normalized
            manifest_ok = project_ok and assets_ok and marker_ok
            manifest_detail = f"project_ok={project_ok}, assets_ok={assets_ok}, marker_ok={marker_ok}"
        else:
            manifest_detail = 'manifest file not found'
    except Exception as e:
        manifest_detail = str(e)
    checks.append({'name': 'launch-manifest.json structure', 'passed': manifest_ok, 'detail': manifest_detail})

    readme_path = file_paths.get('README.md')
    readme_ok = False
    readme_detail = 'README not checked'
    try:
        if readme_path and readme_path.exists():
            text = readme_path.read_text(encoding='utf-8')
            words_ok = len(text.split()) >= 80
            title_ok = 'northstar studio' in text.lower()
            readme_ok = words_ok and title_ok and marker.lower() in text.lower()
            readme_detail = f'words_ok={words_ok}, title_ok={title_ok}'
        else:
            readme_detail = 'README file not found'
    except Exception as e:
        readme_detail = str(e)
    checks.append({'name': 'README.md content quality', 'passed': readme_ok, 'detail': readme_detail})

    total = len(checks)
    passed = sum(1 for c in checks if c['passed'])
    result = {
        'passed': passed == total,
        'score': float(passed) / float(total) if total else 0.0,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()