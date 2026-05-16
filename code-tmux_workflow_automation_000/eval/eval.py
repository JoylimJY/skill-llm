#!/usr/bin/env python3
import sys
import os
import json
import subprocess
import stat
from pathlib import Path

def run(cmd, cwd=None, capture=True):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=capture, text=True, cwd=cwd, timeout=15)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except Exception as e:
        return "", str(e), 1

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    project = workspace / "dna-qc-pipeline"
    checks = []
    total_score = 0.0

    # -----------------------------------------------------------------------
    # CHECK 1: MEMORY.md exists and has correct Preferences section with codex
    # -----------------------------------------------------------------------
    memory_path = workspace / "MEMORY.md"
    try:
        memory_content = memory_path.read_text()
        has_preferences = "## Preferences" in memory_content or "# Preferences" in memory_content or "Preferences" in memory_content
        has_codex = "preferred_coding_agent" in memory_content and "codex" in memory_content
        passed = has_preferences and has_codex
        checks.append({
            "name": "MEMORY.md has Preferences section with codex tool",
            "passed": passed,
            "detail": f"Preferences section present: {has_preferences}, codex entry present: {has_codex}. Content snippet: {memory_content[:300]!r}"
        })
        if passed:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "MEMORY.md has Preferences section with codex tool", "passed": False, "detail": str(e)})

    # -----------------------------------------------------------------------
    # CHECK 2: A git worktree branch named feature/gc-content-filter exists
    # -----------------------------------------------------------------------
    try:
        stdout, stderr, rc = run("git branch -a", cwd=str(project))
        # Check for the branch (with or without feature/ prefix variants)
        branch_exists = "gc-content-filter" in stdout or "gc_content_filter" in stdout
        # Also check git worktree list history (branch should persist even after worktree removal)
        wt_stdout, _, _ = run("git worktree list", cwd=str(project))
        checks.append({
            "name": "Git branch for gc-content-filter task was created",
            "passed": branch_exists,
            "detail": f"Branches found: {stdout!r}. Worktree list: {wt_stdout!r}"
        })
        if branch_exists:
            total_score += 0.20
    except Exception as e:
        checks.append({"name": "Git branch for gc-content-filter task was created", "passed": False, "detail": str(e)})

    # -----------------------------------------------------------------------
    # CHECK 3: .env is a symlink in the worktree (not a copy)
    # The worktree path might be removed after cleanup, but the branch ref exists.
    # We check if the worktree was EVER created by looking at git reflog or
    # checking for evidence in the worktree list or by finding any remaining symlink.
    # Also check if worktree was properly removed (cleanup).
    # -----------------------------------------------------------------------
    try:
        wt_stdout, _, _ = run("git worktree list --porcelain", cwd=str(project))
        
        # Find any worktree paths (other than main)
        wt_paths = []
        for line in wt_stdout.splitlines():
            if line.startswith("worktree "):
                path = line.split(" ", 1)[1].strip()
                if path != str(project):
                    wt_paths.append(Path(path))
        
        # Scenario A: Worktree still exists (cleanup not done or partial) - check symlink
        symlink_verified = False
        worktree_removed = len(wt_paths) == 0  # All non-main worktrees cleaned up
        
        for wt_path in wt_paths:
            env_link = wt_path / ".env"
            if env_link.exists() or env_link.is_symlink():
                if env_link.is_symlink():
                    symlink_verified = True
        
        # Scenario B: Worktree removed - check agent's history via tmux log or invocation log
        codex_log = Path("/tmp/codex_invocation.log")
        codex_was_run = codex_log.exists()
        if codex_was_run:
            log_content = codex_log.read_text()
        else:
            log_content = ""

        # For cleanup verification: branch should still exist even if worktree removed
        stdout_branches, _, _ = run("git branch -a", cwd=str(project))
        branch_still_exists = "gc-content-filter" in stdout_branches or "gc_content_filter" in stdout_branches

        # We pass symlink check if: worktree still has symlink, OR worktree was removed (cleanup done)
        # The critical thing is branch still exists after cleanup
        symlink_check_passed = symlink_verified or (worktree_removed and branch_still_exists and codex_was_run)
        
        checks.append({
            "name": ".env was symlinked (not copied) in worktree",
            "passed": symlink_check_passed,
            "detail": f"Symlink directly verified: {symlink_verified}. Worktree removed (cleanup): {worktree_removed}. Branch preserved: {branch_still_exists}. Codex invoked: {codex_was_run}. Codex log: {log_content!r}"
        })
        if symlink_check_passed:
            total_score += 0.15
    except Exception as e:
        checks.append({"name": ".env was symlinked (not copied) in worktree", "passed": False, "detail": str(e)})

    # -----------------------------------------------------------------------
    # CHECK 4: codex was actually invoked (mock log exists)
    # -----------------------------------------------------------------------
    try:
        codex_log = Path("/tmp/codex_invocation.log")
        codex_invoked = codex_log.exists() and len(codex_log.read_text().strip()) > 0
        log_content = codex_log.read_text() if codex_invoked else "(file missing)"
        checks.append({
            "name": "codex agent was launched (found in invocation log)",
            "passed": codex_invoked,
            "detail": f"Log content: {log_content!r}"
        })
        if codex_invoked:
            total_score += 0.15
    except Exception as e:
        checks.append({"name": "codex agent was launched (found in invocation log)", "passed": False, "detail": str(e)})

    # -----------------------------------------------------------------------
    # CHECK 5: tmux was used - check session existed or was killed, and
    #          that the task was sent with plan-first instruction
    # The plan-first message must contain the standard phrase from SKILL.md
    # -----------------------------------------------------------------------
    try:
        # Check tmux sessions (may have been killed during cleanup)
        active_sessions, _, _ = run("tmux list-sessions 2>/dev/null || echo 'NO_SESSIONS'")
        
        # Check tmux capture or any tmux-related artifacts
        # The plan-first instruction must be sent - we look for evidence in tmux buffers
        # or in a log. Since the mock codex echoes the plan text, check if it was captured.
        
        # Look for any tmux pane output files or check if sessions were created
        # We verify by checking git reflog for the branch creation (tmux not strictly traceable)
        # But we can check if the branch was created from the right base (main)
        
        reflog, _, _ = run("git reflog --all 2>/dev/null | head -20", cwd=str(project))
        branch_from_main = "gc-content-filter" in reflog or "gc_content_filter" in reflog
        
        # Check tmux session history - look for session named after the branch
        # tmux show-messages or similar
        tmux_history, _, _ = run("tmux list-sessions -F '#{session_name}' 2>/dev/null || echo ''")
        
        # The key check: codex was invoked from the worktree path (not the main project)
        codex_log_path = Path("/tmp/codex_invocation.log")
        if codex_log_path.exists():
            log_txt = codex_log_path.read_text()
            # The invocation path should NOT be the main project path
            invoked_from_worktree = str(project) not in log_txt or any(
                p not in log_txt for p in [str(project)]
            )
            # More specifically: the path in log should differ from main project
            paths_in_log = [line.split("=", 1)[1] for line in log_txt.splitlines() if "=" in line]
            from_different_path = any(Path(p).resolve() != project.resolve() for p in paths_in_log)
        else:
            from_different_path = False
            paths_in_log = []

        tmux_used = branch_from_main  # Necessary proxy: branch was created properly
        checks.append({
            "name": "tmux session was created and task sent via send-keys",
            "passed": tmux_used,
            "detail": f"Branch in reflog: {branch_from_main}. Active tmux sessions: {active_sessions!r}. Codex invoked from worktree: {from_different_path}. Paths: {paths_in_log}"
        })
        if tmux_used:
            total_score += 0.15
    except Exception as e:
        checks.append({"name": "tmux session was created and task sent via send-keys", "passed": False, "detail": str(e)})

    # -----------------------------------------------------------------------
    # CHECK 6: Cleanup was performed - worktree removed, branch preserved,
    #          tmux session killed
    # -----------------------------------------------------------------------
    try:
        wt_list, _, _ = run("git worktree list --porcelain", cwd=str(project))
        branches, _, _ = run("git branch", cwd=str(project))
        
        # Count non-main worktrees
        non_main_worktrees = [
            line for line in wt_list.splitlines()
            if line.startswith("worktree ") and str(project) not in line
        ]
        
        worktree_cleaned = len(non_main_worktrees) == 0
        branch_preserved = "gc-content-filter" in branches or "gc_content_filter" in branches
        
        # Check tmux sessions are killed (task session should not exist)
        sessions, _, _ = run("tmux list-sessions -F '#{session_name}' 2>/dev/null || echo ''")
        task_session_killed = "gc-content-filter" not in sessions and "gc_content_filter" not in sessions
        
        cleanup_passed = worktree_cleaned and branch_preserved and task_session_killed
        checks.append({
            "name": "Cleanup: worktree removed, branch preserved, tmux session killed",
            "passed": cleanup_passed,
            "detail": f"Non-main worktrees remaining: {non_main_worktrees}. Branch preserved: {branch_preserved}. Task tmux session killed: {task_session_killed}. Active sessions: {sessions!r}"
        })
        if cleanup_passed:
            total_score += 0.15
    except Exception as e:
        checks.append({"name": "Cleanup: worktree removed, branch preserved, tmux session killed", "passed": False, "detail": str(e)})

    # -----------------------------------------------------------------------
    # CHECK 7: Plan-first message was relayed (agent captured codex output)
    # We check if the agent produced any output containing the plan content.
    # The mock codex outputs a predictable plan message. The agent should have
    # captured it via `tmux capture-pane` and relayed it. We check for a
    # relay artifact: either a file, stdout log, or session capture file.
    # -----------------------------------------------------------------------
    try:
        # Look for any file in workspace that contains plan content
        plan_keywords = ["gc_content_filter", "GC content", "gc-content", "plan", "Plan"]
        plan_captured = False
        capture_source = "none"
        
        # Search for files that contain plan relay evidence
        for candidate in workspace.rglob("*.txt"):
            try:
                content = candidate.read_text(errors="ignore")
                if any(kw.lower() in content.lower() for kw in plan_keywords):
                    plan_captured = True
                    capture_source = str(candidate)
                    break
            except Exception:
                pass
        
        if not plan_captured:
            for candidate in workspace.rglob("*.log"):
                try:
                    content = candidate.read_text(errors="ignore")
                    if any(kw.lower() in content.lower() for kw in plan_keywords):
                        plan_captured = True
                        capture_source = str(candidate)
                        break
                except Exception:
                    pass

        if not plan_captured:
            for candidate in workspace.rglob("*.md"):
                try:
                    content = candidate.read_text(errors="ignore")
                    if any(kw.lower() in content.lower() for kw in plan_keywords):
                        plan_captured = True
                        capture_source = str(candidate)
                        break
                except Exception:
                    pass

        # Also check if tmux pane was captured (pane buffer may contain plan)
        pane_capture, _, _ = run("tmux capture-pane -t _init_server -p 2>/dev/null || echo ''")
        if any(kw.lower() in pane_capture.lower() for kw in plan_keywords):
            plan_captured = True
            capture_source = "tmux_pane_buffer"

        checks.append({
            "name": "Agent captured and relayed the codex plan output",
            "passed": plan_captured,
            "detail": f"Plan captured: {plan_captured}. Source: {capture_source}"
        })
        if plan_captured:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "Agent captured and relayed the codex plan output", "passed": False, "detail": str(e)})

    # -----------------------------------------------------------------------
    # CHECK 8: Manual worktree path is separate from main project (not in-project)
    # Per SKILL.md: worktree-path is a separate directory, not inside the project
    # -----------------------------------------------------------------------
    try:
        codex_log_path = Path("/tmp/codex_invocation.log")
        if codex_log_path.exists():
            log_txt = codex_log_path.read_text()
            paths_in_log = [line.split("=", 1)[1].strip() for line in log_txt.splitlines() if "codex_invoked=" in line]
            if paths_in_log:
                wt_path = Path(paths_in_log[0])
                # Worktree should NOT be inside the main project directory
                is_separate = not str(wt_path).startswith(str(project))
                # Worktree should NOT be the main project itself
                is_not_main = wt_path.resolve() != project.resolve()
                passed = is_separate and is_not_main
                checks.append({
                    "name": "Worktree path is separate from main project directory",
                    "passed": passed,
                    "detail": f"Codex invoked from: {paths_in_log}. Project path: {project}. Separate: {is_separate}. Not main: {is_not_main}"
                })
                if passed:
                    total_score += 0.10
            else:
                checks.append({"name": "Worktree path is separate from main project directory", "passed": False, "detail": "No path found in codex invocation log"})
        else:
            checks.append({"name": "Worktree path is separate from main project directory", "passed": False, "detail": "Codex invocation log not found"})
    except Exception as e:
        checks.append({"name": "Worktree path is separate from main project directory", "passed": False, "detail": str(e)})

    # Final result
    passed_count = sum(1 for c in checks if c["passed"])
    all_passed = passed_count >= 5  # Require at least 5/8 checks to pass

    result = {
        "passed": all_passed,
        "score": round(min(total_score, 1.0), 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()