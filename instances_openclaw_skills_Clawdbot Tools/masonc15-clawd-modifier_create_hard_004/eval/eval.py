import json
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1])
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


def safe_read_text(path):
    try:
        return Path(path).read_text(errors='replace')
    except Exception as e:
        return None, str(e)

# Check 1: task marker file exists and contains expected marker
try:
    marker_path = workspace / 'task_markers.json'
    if not marker_path.exists():
        add_check('marker_file_exists', False, 'task_markers.json is missing')
    else:
        data = json.loads(marker_path.read_text())
        marker_ok = 'clawd-blue-hat-arms-001' in str(data).lower()
        add_check('marker_file_exists', marker_ok, f"marker content keys={list(data.keys()) if isinstance(data, dict) else 'non-dict'}")
except Exception as e:
    add_check('marker_file_exists', False, f'Error reading marker file: {e}')

# Check 2: modified cli.js exists (flexible matching)
cli_path = None
cli_candidates = list(workspace.rglob('cli.js')) + list(workspace.rglob('cli.*.js'))
if cli_candidates:
    cli_path = cli_candidates[0]

if not cli_path or not cli_path.exists():
    add_check('cli_exists', False, 'No cli.js found in workspace')
    cli_text = None
else:
    try:
        cli_text = cli_path.read_text(errors='replace')
        add_check('cli_exists', True, f'Found {cli_path.name}')
    except Exception as e:
        cli_text = None
        add_check('cli_exists', False, f'Could not read cli.js: {e}')

# Check 3: color updated to blue in both rgb and ansi forms (flexible matching)
try:
    if not cli_text:
        add_check('color_updated', False, 'cli.js unavailable for inspection')
    else:
        t = cli_text.lower()
        # Flexible RGB matching - allow variations in spacing and quotes
        rgb_pattern = r'rgb\s*\(\s*100\s*,\s*149\s*,\s*237\s*\)'
        rgb_ok = bool(re.search(rgb_pattern, t, re.IGNORECASE))
        # Flexible ANSI matching
        ansi_pattern = r'ansi\s*:\s*bluebright'
        ansi_ok = bool(re.search(ansi_pattern, t, re.IGNORECASE))
        add_check('color_updated', rgb_ok and ansi_ok, f'rgb_ok={rgb_ok}, ansi_ok={ansi_ok}')
except Exception as e:
    add_check('color_updated', False, f'Error checking colors: {e}')

# Check 4: small Clawd includes arms and hat (flexible ASCII art detection)
try:
    if not cli_text:
        add_check('small_clawd_theme', False, 'cli.js unavailable for small art inspection')
    else:
        # Look for hat patterns - horizontal lines at top of character art (ASCII or Unicode)
        # Accept underscores, dashes, or Unicode box-drawing characters
        has_hat = bool(re.search(r'[_-]{3,}|[─━═▀▄]{3,}|[┌╭▲]{1,}', cli_text))
        # Look for arm patterns - diagonal or vertical lines suggesting limbs
        # Accept standard ASCII slashes/pipes or Unicode box-drawing
        has_arms = bool(re.search(r'[\/\\|]{2,}|[╱╲┌┐▌▐]{2,}', cli_text))
        has_clawd = bool(re.search(r'clawd|claud|claud', cli_text, re.IGNORECASE))
        add_check('small_clawd_theme', has_hat and has_arms and has_clawd, f'hat={has_hat}, arms={has_arms}, clawd_ref={has_clawd}')
except Exception as e:
    add_check('small_clawd_theme', False, f'Error checking small art: {e}')

# Check 5: loading-screen or large art appears modified (flexible detection)
try:
    if not cli_text:
        add_check('large_clawd_theme', False, 'cli.js unavailable for large art inspection')
    else:
        # Look for loading screen indicators or large ASCII art blocks
        loading_indicators = ['loading', 'spinner', 'progress', '█', '░', '▓']
        found_any = any(ind in cli_text.lower() for ind in loading_indicators)
        add_check('large_clawd_theme', found_any, f'found_loading_indicator={found_any}')
except Exception as e:
    add_check('large_clawd_theme', False, f'Error checking large art: {e}')

# Check 6: backup exists somewhere in workspace (flexible matching)
try:
    backup_patterns = ['backup', '.bak', '.orig', '.old', '.backup']
    backups = []
    for p in workspace.rglob('*'):
        if p.is_file():
            name_lower = p.name.lower()
            if any(pattern in name_lower for pattern in backup_patterns):
                backups.append(p)
    add_check('backup_created', len(backups) > 0, f'backups_found={[p.name for p in backups[:5]]}')
except Exception as e:
    add_check('backup_created', False, f'Error searching backups: {e}')

# Score calculation
passed_count = sum(1 for c in checks if c['passed'])
total_count = len(checks)
score = passed_count / total_count if total_count else 0.0
passed = passed_count == total_count

print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))