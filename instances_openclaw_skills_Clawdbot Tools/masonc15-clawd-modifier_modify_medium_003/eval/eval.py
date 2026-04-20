import json
import os
import re
import sys
from pathlib import Path


def norm(s):
    try:
        s = str(s)
    except Exception:
        return ""
    s = s.lower()
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"[^a-z0-9_\-./]", "", s)
    return s


def safe_read(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return None, str(e)


workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []

# Check 1: task marker exists and contains expected deterministic markers
passed = False
try:
    marker_path = workspace / "task_marker.json"
    if marker_path.exists():
        data = json.loads(marker_path.read_text(encoding="utf-8", errors="replace"))
        task_id_ok = norm(data.get("task_id", "")) == norm("clawd_modify_medium_001")
        seed_ok = data.get("seed") == 1337
        markers = " ".join(map(str, data.get("markers", [])))
        markers_ok = all(m in markers for m in ["CLAWD_MARKER_ALPHA", "CLAWD_MARKER_BETA", "CLAWD_MARKER_GAMMA"])
        passed = task_id_ok and seed_ok and markers_ok
        detail = f"task_id_ok={task_id_ok}, seed_ok={seed_ok}, markers_ok={markers_ok}"
    else:
        detail = "task_marker.json is missing"
except Exception as e:
    detail = f"error reading task_marker.json: {e}"
checks.append({"name": "generated marker file", "passed": passed, "detail": detail})

# Check 2: reference notes exist and include markers
passed = False
try:
    notes_path = workspace / "reference_notes.txt"
    if notes_path.exists():
        text = notes_path.read_text(encoding="utf-8", errors="replace")
        text_n = norm(text)
        passed = all(norm(m) in text_n for m in ["CLAWD_MARKER_ALPHA", "CLAWD_MARKER_BETA", "CLAWD_MARKER_GAMMA"])
        detail = "markers present" if passed else "one or more markers missing"
    else:
        detail = "reference_notes.txt is missing"
except Exception as e:
    detail = f"error reading reference_notes.txt: {e}"
checks.append({"name": "reference notes markers", "passed": passed, "detail": detail})

# Check 3: modified mascot SVG exists with winter theme (ocean blue, both arms, preserved prompt icon)
passed = False
try:
    svg_files = [p for p in workspace.iterdir() if p.suffix.lower() == '.svg']
    if svg_files:
        # Find the winter-themed SVG (should have ocean blue color)
        winter_svg = None
        for svg_file in svg_files:
            content = svg_file.read_text(encoding="utf-8", errors="replace")
            # Check for ocean blue color (various formats)
            if re.search(r'#006994|#0077be|#008080|oceanblue|ocean.*blue', content, re.IGNORECASE):
                winter_svg = svg_file
                break
        
        if winter_svg:
            content = winter_svg.read_text(encoding="utf-8", errors="replace")
            content_lower = content.lower()
            
            # Check for ocean blue color
            has_blue = bool(re.search(r'#006994|#0077be|#008080|oceanblue|ocean.*blue', content, re.IGNORECASE))
            
            # Check for both arms - look for arm-related elements with ocean blue color
            # Arms can be represented by ellipse, path, rect, or circle elements
            arm_patterns = [
                r'<ellipse[^>]*fill="#006994"[^>]*>',
                r'<ellipse[^>]*fill="#0077be"[^>]*>',
                r'<ellipse[^>]*fill="#008080"[^>]*>',
                r'<path[^>]*fill="#006994"[^>]*>',
                r'<path[^>]*stroke="#006994"[^>]*>',
                r'<rect[^>]*fill="#006994"[^>]*>',
                r'<circle[^>]*fill="#006994"[^>]*>',
            ]
            arm_count = 0
            for pattern in arm_patterns:
                arm_count += len(re.findall(pattern, content, re.IGNORECASE))
            has_both_arms = arm_count >= 2
            
            # Check for preserved three-line prompt icon
            # Look for three horizontal lines (can be line, rect, or path elements)
            # Use flexible matching to handle different coordinate systems and transform groups
            line_elements = len(re.findall(r'<line[^>]*>', content, re.IGNORECASE))
            rect_lines = len(re.findall(r'<rect[^>]*>', content, re.IGNORECASE))
            has_prompt_icon = line_elements >= 3 or rect_lines >= 3
            
            passed = has_blue and has_both_arms and has_prompt_icon
            detail = f"has_blue={has_blue}, has_both_arms={has_both_arms}, has_prompt_icon={has_prompt_icon}"
        else:
            detail = "no winter-themed SVG found (missing ocean blue color)"
    else:
        detail = "no SVG files found in workspace"
except Exception as e:
    detail = f"error reading SVG files: {e}"
checks.append({"name": "modified mascot SVG", "passed": passed, "detail": detail})

# Check 4: backup file exists (flexible naming)
passed = False
try:
    files = [p.name for p in workspace.iterdir() if p.is_file()]
    # Look for backup-like files with flexible naming
    backup_patterns = ["backup", "bak", "orig", "original", "_backup", ".bak"]
    backup_like = [f for f in files if any(p in norm(f) for p in backup_patterns)]
    passed = len(backup_like) > 0
    detail = f"backup_candidates={backup_like[:5]}" if passed else "no backup-like file found"
except Exception as e:
    detail = f"error scanning workspace: {e}"
checks.append({"name": "backup artifact", "passed": passed, "detail": detail})

score = 0.0
try:
    score = sum(1 for c in checks if c.get("passed")) / float(len(checks) or 1)
except Exception:
    score = 0.0

result = {
    "passed": all(c.get("passed") for c in checks),
    "score": score,
    "checks": checks,
}
print(json.dumps(result, ensure_ascii=False))