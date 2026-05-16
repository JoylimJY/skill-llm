#!/usr/bin/env python3
"""
Evaluation script for the Niri IPC workspace reorganization task.

Checks:
1. workspace_audit.json exists and is valid JSON
2. "before" state is present and contains the initial window listing
3. Firefox and Chromium windows were moved to the "web" workspace
4. VSCode and nvim windows were moved to the "code" workspace
5. Spotify and VLC windows were moved to the "media" workspace
6. Terminal (Alacritty) windows remain on the "terminal" workspace
7. Slack remains unmoved (not covered by policy)
8. The mock server state file confirms mutations happened
"""
import sys
import json
import os
from pathlib import Path

def load_json_safe(path):
    try:
        return json.loads(Path(path).read_text()), None
    except FileNotFoundError:
        return None, f"File not found: {path}"
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON in {path}: {e}"
    except Exception as e:
        return None, f"Unexpected error reading {path}: {e}"

def run_eval(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    
    # ── Check 1: workspace_audit.json exists ─────────────────────────────────
    audit_files = list(workspace.rglob("workspace_audit.json"))
    if not audit_files:
        checks.append({
            "name": "workspace_audit.json_exists",
            "passed": False,
            "detail": "workspace_audit.json not found anywhere in workspace"
        })
        return checks, 0.0

    audit_path = audit_files[0]
    audit, err = load_json_safe(audit_path)
    if err:
        checks.append({
            "name": "workspace_audit.json_valid",
            "passed": False,
            "detail": err
        })
        return checks, 0.0
    
    checks.append({
        "name": "workspace_audit.json_exists_and_valid",
        "passed": True,
        "detail": f"Found at {audit_path}"
    })
    
    # ── Check 2: "before" state present ──────────────────────────────────────
    has_before = False
    before_windows = []
    if isinstance(audit, dict):
        if "before" in audit:
            before_data = audit["before"]
            if isinstance(before_data, dict) and "windows" in before_data:
                before_windows = before_data["windows"]
                has_before = len(before_windows) > 0
            elif isinstance(before_data, list) and len(before_data) > 0:
                before_windows = before_data
                has_before = True
        # Also accept top-level "windows_before"
        elif "windows_before" in audit:
            before_windows = audit["windows_before"]
            has_before = len(before_windows) > 0
    
    checks.append({
        "name": "before_state_recorded",
        "passed": has_before,
        "detail": f"Before state has {len(before_windows)} windows" if has_before else "No 'before' state with windows found in audit"
    })
    
    # ── Check 3-7: Verify actual IPC state mutations via mock server state ────
    state_path = "/tmp/niri_mock_state.json"
    final_state, err = load_json_safe(state_path)
    if err:
        checks.append({
            "name": "mock_server_state_readable",
            "passed": False,
            "detail": f"Cannot read mock server state: {err}"
        })
        # Still try to evaluate from audit "after" state if present
        final_state = None
    else:
        checks.append({
            "name": "mock_server_state_readable",
            "passed": True,
            "detail": f"Mock state loaded with {len(final_state.get('windows', []))} windows"
        })
    
    # Helper: find workspace name by id in final_state
    def get_ws_name(ws_id, state):
        if not state:
            return None
        for ws in state.get("workspaces", []):
            if ws["id"] == ws_id:
                return ws.get("name", "").lower()
        return None
    
    # Helper: find window in final state by app_id substring
    def find_windows_by_app(substr, state):
        if not state:
            return []
        return [w for w in state.get("windows", []) 
                if substr.lower() in w.get("app_id", "").lower()]
    
    # Helper: find window in final state by title substring  
    def find_windows_by_title(substr, state):
        if not state:
            return []
        return [w for w in state.get("windows", [])
                if substr.lower() in w.get("title", "").lower()]
    
    # ── Check 3: Firefox on "web" workspace ───────────────────────────────────
    if final_state:
        firefox_wins = find_windows_by_app("firefox", final_state)
        firefox_moved = all(get_ws_name(w["workspace_id"], final_state) == "web" for w in firefox_wins)
        checks.append({
            "name": "firefox_moved_to_web",
            "passed": bool(firefox_wins) and firefox_moved,
            "detail": f"Firefox windows: {[(w['title'], get_ws_name(w['workspace_id'], final_state)) for w in firefox_wins]}"
        })
    else:
        checks.append({"name": "firefox_moved_to_web", "passed": False, "detail": "No mock state available"})
    
    # ── Check 4: Chromium on "web" workspace ─────────────────────────────────
    if final_state:
        chromium_wins = find_windows_by_app("chromium", final_state)
        chromium_moved = all(get_ws_name(w["workspace_id"], final_state) == "web" for w in chromium_wins)
        checks.append({
            "name": "chromium_moved_to_web",
            "passed": bool(chromium_wins) and chromium_moved,
            "detail": f"Chromium windows: {[(w['title'], get_ws_name(w['workspace_id'], final_state)) for w in chromium_wins]}"
        })
    else:
        checks.append({"name": "chromium_moved_to_web", "passed": False, "detail": "No mock state available"})
    
    # ── Check 5: VSCode on "code" workspace ───────────────────────────────────
    if final_state:
        vscode_wins = find_windows_by_app("code", final_state)
        vscode_moved = all(get_ws_name(w["workspace_id"], final_state) == "code" for w in vscode_wins)
        checks.append({
            "name": "vscode_moved_to_code",
            "passed": bool(vscode_wins) and vscode_moved,
            "detail": f"VSCode windows: {[(w['title'], get_ws_name(w['workspace_id'], final_state)) for w in vscode_wins]}"
        })
    else:
        checks.append({"name": "vscode_moved_to_code", "passed": False, "detail": "No mock state available"})
    
    # ── Check 6: nvim on "code" workspace ────────────────────────────────────
    if final_state:
        nvim_wins = find_windows_by_title("nvim", final_state)
        nvim_moved = all(get_ws_name(w["workspace_id"], final_state) == "code" for w in nvim_wins)
        checks.append({
            "name": "nvim_moved_to_code",
            "passed": bool(nvim_wins) and nvim_moved,
            "detail": f"nvim windows: {[(w['title'], get_ws_name(w['workspace_id'], final_state)) for w in nvim_wins]}"
        })
    else:
        checks.append({"name": "nvim_moved_to_code", "passed": False, "detail": "No mock state available"})
    
    # ── Check 7: Spotify on "media" workspace ────────────────────────────────
    if final_state:
        spotify_wins = find_windows_by_app("spotify", final_state)
        spotify_moved = all(get_ws_name(w["workspace_id"], final_state) == "media" for w in spotify_wins)
        checks.append({
            "name": "spotify_moved_to_media",
            "passed": bool(spotify_wins) and spotify_moved,
            "detail": f"Spotify windows: {[(w['title'], get_ws_name(w['workspace_id'], final_state)) for w in spotify_wins]}"
        })
    else:
        checks.append({"name": "spotify_moved_to_media", "passed": False, "detail": "No mock state available"})
    
    # ── Check 8: VLC on "media" workspace ────────────────────────────────────
    if final_state:
        vlc_wins = find_windows_by_app("vlc", final_state)
        vlc_moved = all(get_ws_name(w["workspace_id"], final_state) == "media" for w in vlc_wins)
        checks.append({
            "name": "vlc_moved_to_media",
            "passed": bool(vlc_wins) and vlc_moved,
            "detail": f"VLC windows: {[(w['title'], get_ws_name(w['workspace_id'], final_state)) for w in vlc_wins]}"
        })
    else:
        checks.append({"name": "vlc_moved_to_media", "passed": False, "detail": "No mock state available"})
    
    # ── Check 9: Alacritty terminals remain on "terminal" workspace ──────────
    if final_state:
        alacritty_wins = find_windows_by_app("alacritty", final_state)
        alacritty_ok = all(get_ws_name(w["workspace_id"], final_state) == "terminal" for w in alacritty_wins)
        checks.append({
            "name": "alacritty_on_terminal",
            "passed": bool(alacritty_wins) and alacritty_ok,
            "detail": f"Alacritty windows: {[(w['title'], get_ws_name(w['workspace_id'], final_state)) for w in alacritty_wins]}"
        })
    else:
        checks.append({"name": "alacritty_on_terminal", "passed": False, "detail": "No mock state available"})
    
    # ── Check 10: Slack NOT moved (unmatched policy = leave in place) ─────────
    if final_state:
        slack_wins = find_windows_by_app("slack", final_state)
        # Slack should still be on workspace_id 1 (terminal, the original)
        slack_unmoved = all(w["workspace_id"] == 1 for w in slack_wins)
        checks.append({
            "name": "slack_not_moved",
            "passed": bool(slack_wins) and slack_unmoved,
            "detail": f"Slack windows: {[(w['title'], w['workspace_id']) for w in slack_wins]}"
        })
    else:
        checks.append({"name": "slack_not_moved", "passed": False, "detail": "No mock state available"})
    
    # ── Check 11: "after" state in audit ─────────────────────────────────────
    has_after = False
    if isinstance(audit, dict):
        if "after" in audit:
            after_data = audit["after"]
            if isinstance(after_data, dict) and "windows" in after_data:
                has_after = len(after_data["windows"]) > 0
            elif isinstance(after_data, list):
                has_after = len(after_data) > 0
        elif "windows_after" in audit:
            has_after = len(audit["windows_after"]) > 0
    
    checks.append({
        "name": "after_state_recorded",
        "passed": has_after,
        "detail": "After state present in audit" if has_after else "No 'after' state with windows found in audit"
    })

    # ── Scoring ───────────────────────────────────────────────────────────────
    # Weight critical checks more heavily
    critical = [
        "firefox_moved_to_web",
        "chromium_moved_to_web", 
        "vscode_moved_to_code",
        "nvim_moved_to_code",
        "spotify_moved_to_media",
        "vlc_moved_to_media",
        "alacritty_on_terminal",
        "slack_not_moved",
    ]
    passed_count = sum(1 for c in checks if c["passed"])
    total_count = len(checks)
    
    # Critical checks score 0.7 of total, structural checks 0.3
    critical_checks = [c for c in checks if c["name"] in critical]
    structural_checks = [c for c in checks if c["name"] not in critical]
    
    critical_score = sum(1 for c in critical_checks if c["passed"]) / max(len(critical_checks), 1)
    structural_score = sum(1 for c in structural_checks if c["passed"]) / max(len(structural_checks), 1)
    
    final_score = round(0.7 * critical_score + 0.3 * structural_score, 3)
    overall_passed = final_score >= 0.85
    
    return checks, final_score, overall_passed

def main():
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        checks, score, passed = run_eval(workspace_dir)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_error", "passed": False, "detail": str(e)}]
        }
        print(json.dumps(result))
        return
    
    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()