#!/usr/bin/env python3
"""
Evaluation script for the claude-code-task skill sandbox.
Checks that the agent correctly:
  1. Read MEMORY.md and used 'codex' as the preferred agent (no asking)
  2. Created a git worktree on a new branch off main
  3. Symlinked (not copied) .env (and .env.local) into the worktree
  4. Created a tmux session with -d flag and correct -c (worktree path)
  5. Sent the nvm+tool launch command via send-keys
  6. Sent the task with the plan-first boilerplate via send-keys -l --
  7. Did NOT modify MEMORY.md in a way that removes/replaces the preference

Usage: python3 eval_script.py /workspace
"""

import sys
import json
import subprocess
import os
from pathlib import Path

def load_tmux_log(log_path: str) -> list[dict]:
    """Load all tmux audit log entries."""
    entries = []
    try:
        with open(log_path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except FileNotFoundError:
        pass
    return entries


def flatten_args(entry: dict) -> list[str]:
    return entry.get("args", [])


def args_str(entry: dict) -> str:
    return " ".join(entry.get("args", []))


def run_check(name: str, fn) -> dict:
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {e}"}


def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    project = workspace / "patient-pipeline"
    memory_md = workspace / "MEMORY.md"
    tmux_log = "/tmp/tmux_audit.log"

    checks = []
    tmux_entries = load_tmux_log(tmux_log)

    # ── Check 1: MEMORY.md exists and has "Preferences" section with codex ──
    def check_memory_preferences():
        if not memory_md.exists():
            return False, "MEMORY.md not found at workspace root"
        content = memory_md.read_text()
        if "Preferences" not in content:
            return False, "MEMORY.md has no '## Preferences' section"
        # The preferred agent must be codex (read from existing memory, not changed)
        lines = content.lower().splitlines()
        pref_lines = [l for l in lines if "preferred_coding_agent" in l]
        if not pref_lines:
            return False, "No preferred_coding_agent entry in MEMORY.md"
        # Accept 'codex' as value (it was pre-seeded; agent should have kept or confirmed it)
        last_pref = pref_lines[-1]
        if "codex" not in last_pref:
            return False, f"Expected 'codex' as preferred agent, got: {pref_lines[-1]}"
        return True, f"MEMORY.md correctly shows codex preference: '{pref_lines[-1].strip()}'"

    checks.append(run_check("memory_preferences_codex", check_memory_preferences))

    # ── Check 2: A git worktree was created (not main) ───────────────────────
    def check_worktree_created():
        result = subprocess.run(
            ["git", "-C", str(project), "worktree", "list", "--porcelain"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return False, f"git worktree list failed: {result.stderr}"
        
        output = result.stdout
        # Parse worktrees
        worktrees = []
        current = {}
        for line in output.splitlines():
            if line.startswith("worktree "):
                if current:
                    worktrees.append(current)
                current = {"path": line.split(" ", 1)[1]}
            elif line.startswith("branch "):
                current["branch"] = line.split(" ", 1)[1]
            elif line.startswith("HEAD "):
                current["HEAD"] = line.split(" ", 1)[1]
        if current:
            worktrees.append(current)
        
        # Must have more than just the main worktree
        non_main = [w for w in worktrees if str(project) != w.get("path", "").rstrip()]
        if not non_main:
            return False, f"No additional worktree found. Worktrees: {worktrees}"
        
        # Verify each non-main worktree is not on 'main' branch
        task_worktrees = [w for w in non_main 
                         if "refs/heads/main" not in w.get("branch", "")]
        if not task_worktrees:
            return False, f"Extra worktrees exist but all are on 'main': {non_main}"
        
        wt = task_worktrees[0]
        branch = wt.get("branch", "").replace("refs/heads/", "")
        return True, f"Worktree created at '{wt.get('path')}' on branch '{branch}'"

    checks.append(run_check("worktree_created_on_new_branch", check_worktree_created))

    # ── Check 3: Worktree path exists on filesystem ───────────────────────────
    def check_worktree_path_exists():
        result = subprocess.run(
            ["git", "-C", str(project), "worktree", "list", "--porcelain"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return False, "git worktree list failed"
        
        paths = []
        for line in result.stdout.splitlines():
            if line.startswith("worktree "):
                paths.append(line.split(" ", 1)[1])
        
        # Find non-main paths
        non_main_paths = [p for p in paths if p.rstrip("/") != str(project).rstrip("/")]
        if not non_main_paths:
            return False, "No extra worktree paths found"
        
        for p in non_main_paths:
            wt_path = Path(p)
            if wt_path.exists():
                return True, f"Worktree directory exists: {wt_path}"
        
        return False, f"Worktree path(s) {non_main_paths} do not exist on disk"

    checks.append(run_check("worktree_directory_exists", check_worktree_path_exists))

    # ── Check 4: .env is a SYMLINK in the worktree (not a copied file) ────────
    def check_env_symlinked():
        result = subprocess.run(
            ["git", "-C", str(project), "worktree", "list", "--porcelain"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return False, "git worktree list failed"
        
        wt_paths = []
        for line in result.stdout.splitlines():
            if line.startswith("worktree "):
                wt_paths.append(line.split(" ", 1)[1])
        
        non_main = [Path(p) for p in wt_paths if p.rstrip("/") != str(project).rstrip("/")]
        if not non_main:
            return False, "No extra worktree found to check .env"
        
        wt = non_main[0]
        env_in_wt = wt / ".env"
        
        if not env_in_wt.exists() and not env_in_wt.is_symlink():
            return False, f".env not found in worktree at {env_in_wt}"
        
        if not env_in_wt.is_symlink():
            return False, f".env in worktree is a COPY, not a symlink! Found regular file at {env_in_wt}"
        
        # Verify it points toward the project .env
        link_target = os.readlink(str(env_in_wt))
        # Resolve to absolute
        if not os.path.isabs(link_target):
            resolved = (wt / link_target).resolve()
        else:
            resolved = Path(link_target).resolve()
        
        project_env = (project / ".env").resolve()
        if resolved != project_env:
            return False, f".env symlink points to '{link_target}' (resolved: {resolved}), expected {project_env}"
        
        return True, f".env is a symlink in worktree → correctly points to {link_target}"

    checks.append(run_check("env_is_symlink_not_copy", check_env_symlinked))

    # ── Check 5: tmux new-session was called with -d and a -c (worktree path) ─
    def check_tmux_new_session():
        if not tmux_entries:
            return False, "No tmux audit log entries found (tmux was never called)"
        
        new_session_entries = [e for e in tmux_entries if "new-session" in flatten_args(e)]
        if not new_session_entries:
            return False, f"tmux new-session never called. All calls: {[args_str(e) for e in tmux_entries]}"
        
        for entry in new_session_entries:
            args = flatten_args(entry)
            # Must have -d (detached)
            if "-d" not in args:
                return False, f"tmux new-session missing -d flag: {args}"
            # Must have -c pointing to a path (working directory = worktree)
            if "-c" not in args:
                return False, f"tmux new-session missing -c flag: {args}"
            
            c_idx = args.index("-c")
            if c_idx + 1 >= len(args):
                return False, f"tmux new-session -c has no value: {args}"
            
            worktree_path = args[c_idx + 1]
            
            # The -c path must NOT be the main project dir
            if Path(worktree_path).resolve() == project.resolve():
                return False, f"tmux -c points to main project dir, should be worktree: {worktree_path}"
            
            # Must have a session name (-s)
            if "-s" not in args:
                return False, f"tmux new-session missing -s flag: {args}"
            
            return True, f"tmux new-session called with -d -s <name> -c {worktree_path}"
        
        return False, "No valid tmux new-session call found"

    checks.append(run_check("tmux_new_session_correct_flags", check_tmux_new_session))

    # ── Check 6: tmux send-keys launched the agent with nvm use 20 ───────────
    def check_tmux_agent_launch():
        if not tmux_entries:
            return False, "No tmux audit log entries"
        
        send_entries = [e for e in tmux_entries if "send-keys" in flatten_args(e)]
        if not send_entries:
            return False, "tmux send-keys never called"
        
        # Look for nvm use 20 AND codex
        for entry in send_entries:
            combined = " ".join(flatten_args(entry))
            if "nvm use 20" in combined and "codex" in combined:
                return True, f"Found nvm use 20 + codex in send-keys: {combined[:120]}"
        
        # Also accept if codex appears separately from nvm (two separate send-keys calls)
        codex_entries = [e for e in send_entries if "codex" in " ".join(flatten_args(e))]
        nvm_entries = [e for e in send_entries if "nvm use 20" in " ".join(flatten_args(e))]
        
        if codex_entries and nvm_entries:
            return True, "Found separate nvm use 20 and codex send-keys calls"
        
        if not codex_entries:
            return False, f"'codex' never sent via send-keys. Keys sent: {[' '.join(flatten_args(e))[:80] for e in send_entries]}"
        if not nvm_entries:
            return False, f"'nvm use 20' never sent via send-keys. Keys sent: {[' '.join(flatten_args(e))[:80] for e in send_entries]}"
        
        return False, "Agent launch not properly configured"

    checks.append(run_check("tmux_send_keys_agent_launch", check_tmux_agent_launch))

    # ── Check 7: Task sent with plan-first boilerplate using -l flag ──────────
    def check_tmux_task_with_plan_instruction():
        if not tmux_entries:
            return False, "No tmux audit log entries"
        
        send_entries = [e for e in tmux_entries if "send-keys" in flatten_args(e)]
        if not send_entries:
            return False, "tmux send-keys never called"
        
        PLAN_PHRASES = [
            "before making any changes",
            "show me a plan",
            "wait for my approval",
        ]
        
        # Find entries that carry the actual task text + plan instruction
        task_entry = None
        for entry in send_entries:
            args = flatten_args(entry)
            combined_lower = " ".join(args).lower()
            matches = sum(1 for phrase in PLAN_PHRASES if phrase in combined_lower)
            if matches >= 2:
                task_entry = entry
                break
        
        if not task_entry:
            # Try concatenating all send-keys args together (agent might have sent in parts)
            all_text = " ".join(
                " ".join(flatten_args(e)) for e in send_entries
            ).lower()
            matches = sum(1 for phrase in PLAN_PHRASES if phrase in all_text)
            if matches >= 2:
                return True, "Plan-first instruction found across multiple send-keys calls"
            return False, (
                f"Plan-first boilerplate not found in send-keys calls. "
                f"Looking for: {PLAN_PHRASES}. "
                f"Got args snippets: {[' '.join(flatten_args(e))[:80] for e in send_entries[:5]]}"
            )
        
        # Verify -l flag is present in this call
        args = flatten_args(task_entry)
        if "-l" not in args:
            return False, (
                f"Plan-first instruction found but -l flag missing from send-keys. "
                f"Args: {args[:10]}"
            )
        
        return True, "Task sent with plan-first boilerplate and -l flag ✓"

    checks.append(run_check("tmux_task_plan_first_with_l_flag", check_tmux_task_with_plan_instruction))

    # ── Check 8: Worktree was created with -b flag (new branch off main) ──────
    def check_worktree_branch_flag():
        """Verify via git that the branch created did not already exist before the task."""
        result = subprocess.run(
            ["git", "-C", str(project), "branch", "-a"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return False, f"git branch failed: {result.stderr}"
        
        branches = [b.strip().lstrip("* ") for b in result.stdout.splitlines()]
        non_main = [b for b in branches if b and b != "main" and not b.startswith("remotes/")]
        
        if not non_main:
            return False, "No feature branch found. git worktree add -b <branch> was not used."
        
        return True, f"Feature branch(es) created: {non_main}"

    checks.append(run_check("new_branch_created_with_b_flag", check_worktree_branch_flag))

    # ── Compute final score ───────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 3)
    all_passed = passed_count == total

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks,
    }
    print(json.dumps(result, indent=2))
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())