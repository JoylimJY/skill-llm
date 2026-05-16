import sys
import os
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    
    # ── 1. Check that app_report.txt exists in workspace ──────────────────────
    report_path = Path(workspace_dir) / "app_report.txt"
    candidates = list(Path(workspace_dir).rglob("app_report.txt"))
    
    if not candidates:
        checks.append({
            "name": "app_report_exists",
            "passed": False,
            "detail": "app_report.txt not found anywhere in the workspace."
        })
        return {"passed": False, "score": 0.0, "checks": checks}
    
    report_path = candidates[0]
    checks.append({
        "name": "app_report_exists",
        "passed": True,
        "detail": f"Found app_report.txt at {report_path}"
    })
    
    try:
        report_content = report_path.read_text(encoding="utf-8", errors="replace").lower()
    except Exception as e:
        checks.append({
            "name": "app_report_readable",
            "passed": False,
            "detail": f"Could not read app_report.txt: {e}"
        })
        return {"passed": False, "score": 0.0, "checks": checks}
    
    # ── 2. Report mentions Sketch with correct path ────────────────────────────
    sketch_path_correct = "/applications/sketch.app" in report_content
    checks.append({
        "name": "report_sketch_path",
        "passed": sketch_path_correct,
        "detail": (
            "app_report.txt contains the correct path /Applications/Sketch.app for Sketch"
            if sketch_path_correct
            else f"app_report.txt does NOT contain '/applications/sketch.app'. Content snippet: {report_content[:400]}"
        )
    })
    
    # ── 3. Report mentions DevUtils with correct path ─────────────────────────
    # DevUtils lives in ~/Applications (home dir) - agent must use ls fallback
    devutils_mentioned = "devutils" in report_content
    # Accept either ~/Applications/DevUtils.app or the expanded home path
    devutils_path_correct = (
        "devutils.app" in report_content and
        ("~/applications" in report_content or "/root/applications" in report_content or 
         "/home/" in report_content or "applications/devutils" in report_content)
    )
    checks.append({
        "name": "report_devutils_mentioned",
        "passed": devutils_mentioned,
        "detail": (
            "app_report.txt mentions DevUtils"
            if devutils_mentioned
            else "app_report.txt does NOT mention DevUtils at all."
        )
    })
    checks.append({
        "name": "report_devutils_path",
        "passed": devutils_path_correct,
        "detail": (
            "app_report.txt contains a valid path for DevUtils.app (from ~/Applications fallback)"
            if devutils_path_correct
            else f"app_report.txt does not contain a valid DevUtils.app path. Content: {report_content[:500]}"
        )
    })
    
    # ── 4. Check open_calls.log to verify open was actually called ─────────────
    open_log_path = Path("/tmp/open_calls.log")
    try:
        open_log = open_log_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        checks.append({
            "name": "open_log_readable",
            "passed": False,
            "detail": f"Could not read /tmp/open_calls.log: {e}"
        })
        return {"passed": False, "score": 0.0, "checks": checks}
    
    open_log_lower = open_log.lower()
    
    # ── 5. Verify Sketch was opened via 'open' command ─────────────────────────
    # Accept: open -a "Sketch" or open "/Applications/Sketch.app"
    sketch_opened = (
        'sketch' in open_log_lower and
        '[path_not_found]' not in open_log_lower.split('sketch')[0][-50:] if 'sketch' in open_log_lower else False
    )
    # More robust check
    sketch_opened = False
    for line in open_log.splitlines():
        if 'sketch' in line.lower() and '[path_not_found]' not in line and '[not_an_app]' not in line:
            sketch_opened = True
            break
    
    checks.append({
        "name": "sketch_was_opened",
        "passed": sketch_opened,
        "detail": (
            "open command was called for Sketch successfully"
            if sketch_opened
            else f"Sketch was not opened via 'open' command (or had errors). Log: {open_log[:500]}"
        )
    })
    
    # ── 6. Verify DevUtils was opened via 'open' command ─────────────────────
    devutils_opened = False
    for line in open_log.splitlines():
        if 'devutils' in line.lower() and '[path_not_found]' not in line and '[not_an_app]' not in line:
            devutils_opened = True
            break
    
    checks.append({
        "name": "devutils_was_opened",
        "passed": devutils_opened,
        "detail": (
            "open command was called for DevUtils successfully"
            if devutils_opened
            else f"DevUtils was not opened via 'open' command (or had errors). Log: {open_log[:500]}"
        )
    })
    
    # ── 7. Verify mdfind was used with correct Spotlight syntax ───────────────
    # Check shell history or any script left in workspace for evidence of mdfind usage
    mdfind_used_correctly = False
    search_paths = [
        Path(workspace_dir),
        Path("/tmp"),
    ]
    
    # Look for any shell scripts or command logs in workspace
    for search_root in search_paths:
        try:
            for f in search_root.rglob("*.sh"):
                try:
                    content = f.read_text(errors="replace").lower()
                    if "kmditemkind" in content and "application" in content and "mdfind" in content:
                        mdfind_used_correctly = True
                        break
                except:
                    pass
            if mdfind_used_correctly:
                break
        except:
            pass
    
    # Also check bash history
    for history_file in [Path("/root/.bash_history"), Path("/tmp/.bash_history")]:
        if history_file.exists():
            try:
                hist = history_file.read_text(errors="replace").lower()
                if "kmditemkind" in hist and "mdfind" in hist:
                    mdfind_used_correctly = True
            except:
                pass
    
    # Check if any script in workspace uses mdfind with the proper query
    for f in Path(workspace_dir).rglob("*"):
        if f.is_file() and f.suffix in (".sh", ".bash", ".py", ".txt", ""):
            try:
                content = f.read_text(errors="replace").lower()
                if "kmditemkind" in content and "mdfind" in content:
                    mdfind_used_correctly = True
                    break
            except:
                pass
    
    checks.append({
        "name": "mdfind_spotlight_syntax_used",
        "passed": mdfind_used_correctly,
        "detail": (
            "Found evidence of correct mdfind with kMDItemKind == 'Application' Spotlight query"
            if mdfind_used_correctly
            else "No evidence found of mdfind with the proprietary kMDItemKind Spotlight query syntax. "
                 "Agent may have used 'find' or 'locate' instead."
        )
    })
    
    # ── 8. Verify fallback strategy was used for DevUtils ────────────────────
    # Check that ls or find was used on ~/Applications to find DevUtils
    fallback_used = False
    for f in Path(workspace_dir).rglob("*"):
        if f.is_file() and f.suffix in (".sh", ".bash", ".py", ".txt", ""):
            try:
                content = f.read_text(errors="replace").lower()
                if "devutils" in content and (
                    "ls" in content or "find" in content or "grep" in content
                ) and ("~/applications" in content or "applications" in content):
                    fallback_used = True
                    break
            except:
                pass
    
    # If DevUtils was successfully opened, infer fallback was used
    if devutils_opened and devutils_path_correct:
        fallback_used = True
    
    checks.append({
        "name": "ls_fallback_used_for_devutils",
        "passed": fallback_used,
        "detail": (
            "Agent correctly used ls/find fallback strategy to discover DevUtils in ~/Applications"
            if fallback_used
            else "No evidence of ls/grep fallback being used to find DevUtils (which mdfind cannot find)"
        )
    })
    
    # ── Scoring ───────────────────────────────────────────────────────────────
    # Weight the checks
    weights = {
        "app_report_exists": 0.10,
        "report_sketch_path": 0.10,
        "report_devutils_mentioned": 0.10,
        "report_devutils_path": 0.10,
        "sketch_was_opened": 0.20,
        "devutils_was_opened": 0.20,
        "mdfind_spotlight_syntax_used": 0.10,
        "ls_fallback_used_for_devutils": 0.10,
    }
    
    score = 0.0
    for check in checks:
        w = weights.get(check["name"], 0.0)
        if check["passed"]:
            score += w
    
    all_critical_passed = (
        sketch_opened and 
        devutils_opened and 
        sketch_path_correct and 
        devutils_mentioned
    )
    
    return {
        "passed": all_critical_passed and score >= 0.70,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))