#!/usr/bin/env python3
"""
Evaluation script for nb CLI knowledge base reorganization task.
Checks all steps using nb CLI commands and inspects ~/.nb state.
"""
import sys
import os
import json
import subprocess
import re
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

checks = []
total_score = 0.0
max_score = 0.0

def run_nb(*args, cwd=None, env=None):
    """Run an nb command and return (stdout, stderr, returncode)."""
    cmd = ["nb"] + list(args)
    e = dict(os.environ)
    if env:
        e.update(env)
    result = subprocess.run(cmd, capture_output=True, text=True, env=e, cwd=cwd)
    return result.stdout, result.stderr, result.returncode

def add_check(name, passed, detail, weight=1.0):
    global total_score, max_score
    checks.append({"name": name, "passed": passed, "detail": detail})
    max_score += weight
    if passed:
        total_score += weight

# ── CHECK 1: ml-research notebook exists ────────────────────────────────────
try:
    stdout, stderr, rc = run_nb("notebooks")
    notebooks_text = stdout.lower()
    ml_research_exists = "ml-research" in notebooks_text
    add_check(
        "ml-research notebook exists",
        ml_research_exists,
        f"nb notebooks output: {stdout.strip()[:300]}",
        weight=1.5
    )
except Exception as ex:
    add_check("ml-research notebook exists", False, f"Exception: {ex}", weight=1.5)

# ── CHECK 2: project-tasks notebook exists ───────────────────────────────────
try:
    stdout, stderr, rc = run_nb("notebooks")
    pt_exists = "project-tasks" in stdout.lower()
    add_check(
        "project-tasks notebook exists",
        pt_exists,
        f"nb notebooks output: {stdout.strip()[:300]}",
        weight=1.5
    )
except Exception as ex:
    add_check("project-tasks notebook exists", False, f"Exception: {ex}", weight=1.5)

# ── CHECK 3: Note A exists in ml-research ───────────────────────────────────
try:
    stdout, stderr, rc = run_nb("ml-research:", "list", "-a")
    note_a_listed = "transformer architecture deep dive" in stdout.lower()
    add_check(
        "Note A (Transformer Architecture Deep Dive) exists in ml-research",
        note_a_listed,
        f"ml-research list: {stdout.strip()[:400]}",
        weight=1.0
    )
except Exception as ex:
    add_check("Note A exists in ml-research", False, f"Exception: {ex}", weight=1.0)

# ── CHECK 4: Note A has correct tags ────────────────────────────────────────
try:
    # Search by tag in ml-research
    stdout_t, _, _ = run_nb("search", "--tag", "transformers", "--all")
    has_transformer_tag = "transformer architecture deep dive" in stdout_t.lower()
    
    stdout_t2, _, _ = run_nb("search", "--tag", "nlp", "--all")
    has_nlp_tag = "transformer architecture deep dive" in stdout_t2.lower()
    
    tags_ok = has_transformer_tag and has_nlp_tag
    add_check(
        "Note A has tags: transformers, attention/nlp",
        tags_ok,
        f"Tag search 'transformers' hit: {has_transformer_tag}, 'nlp' hit: {has_nlp_tag}",
        weight=1.0
    )
except Exception as ex:
    add_check("Note A has correct tags", False, f"Exception: {ex}", weight=1.0)

# ── CHECK 5: Note A content was APPENDED (not overwritten) ───────────────────
try:
    # Find Note A and print it
    stdout_list, _, _ = run_nb("ml-research:", "list", "-a")
    note_a_id = None
    for line in stdout_list.splitlines():
        if "transformer architecture deep dive" in line.lower():
            m = re.search(r'\[(\d+)\]', line)
            if m:
                note_a_id = m.group(1)
                break
    
    if note_a_id:
        stdout_show, _, _ = run_nb("show", f"ml-research:{note_a_id}", "--print")
        content = stdout_show.lower()
        has_original = "multi-head self-attention" in content or "q, k, v matrices" in content
        has_appended = "encoder stack" in content or "d_model=512" in content or "6 layers" in content
        both_present = has_original and has_appended
        add_check(
            "Note A has BOTH original content AND appended encoder info",
            both_present,
            f"has_original={has_original}, has_appended={has_appended}. Content snippet: {stdout_show[:400]}",
            weight=2.0
        )
    else:
        add_check("Note A content append check", False, f"Could not find Note A ID in: {stdout_list[:300]}", weight=2.0)
except Exception as ex:
    add_check("Note A content append check", False, f"Exception: {ex}", weight=2.0)

# ── CHECK 6: Note B content was OVERWRITTEN ───────────────────────────────────
try:
    stdout_list, _, _ = run_nb("ml-research:", "list", "-a")
    note_b_id = None
    for line in stdout_list.splitlines():
        if "gpu cluster setup" in line.lower():
            m = re.search(r'\[(\d+)\]', line)
            if m:
                note_b_id = m.group(1)
                break

    if note_b_id:
        stdout_show, _, _ = run_nb("show", f"ml-research:{note_b_id}", "--print")
        content = stdout_show.lower()
        has_deprecated = "deprecated" in content or "decommissioned" in content
        lacks_old = "a100" not in content and "slurm" not in content
        overwrite_ok = has_deprecated and lacks_old
        add_check(
            "Note B content fully OVERWRITTEN with DEPRECATED message",
            overwrite_ok,
            f"has_deprecated={has_deprecated}, lacks_old_content={lacks_old}. Snippet: {stdout_show[:300]}",
            weight=2.0
        )
    else:
        add_check("Note B overwrite check", False, f"Could not find Note B ID. List: {stdout_list[:300]}", weight=2.0)
except Exception as ex:
    add_check("Note B overwrite check", False, f"Exception: {ex}", weight=2.0)

# ── CHECK 7: Note C exists with governance/mlops tags ────────────────────────
try:
    stdout_t, _, _ = run_nb("search", "--tag", "mlops", "--all")
    mlops_hit = "dataset versioning policy" in stdout_t.lower()
    add_check(
        "Note C (Dataset Versioning Policy) has mlops tag",
        mlops_hit,
        f"Tag search 'mlops' output: {stdout_t.strip()[:300]}",
        weight=1.0
    )
except Exception as ex:
    add_check("Note C mlops tag check", False, f"Exception: {ex}", weight=1.0)

# ── CHECK 8: Todos exist in project-tasks ────────────────────────────────────
try:
    stdout_todos, _, _ = run_nb("todos", "open", "project-tasks:")
    # Note: Todo X should be DONE, so check closed
    stdout_closed, _, _ = run_nb("todos", "closed", "project-tasks:")
    stdout_all_y, _, _ = run_nb("project-tasks:", "list", "-a")
    
    # Todo Y and Z should be open
    has_todo_y = "gpu cluster access" in stdout_todos.lower() or "gpu cluster access" in stdout_all_y.lower()
    has_todo_z = "dataset versioning documentation" in stdout_todos.lower() or "dataset versioning documentation" in stdout_all_y.lower()
    
    add_check(
        "Todos Y and Z exist in project-tasks",
        has_todo_y and has_todo_z,
        f"Todo Y found={has_todo_y}, Todo Z found={has_todo_z}. Open todos: {stdout_todos.strip()[:300]}",
        weight=1.0
    )
except Exception as ex:
    add_check("Todos Y and Z exist", False, f"Exception: {ex}", weight=1.0)

# ── CHECK 9: Todo X is marked DONE ───────────────────────────────────────────
try:
    stdout_closed, _, _ = run_nb("todos", "closed", "project-tasks:")
    # Also try just listing all
    stdout_all, _, _ = run_nb("project-tasks:", "list", "-a")
    
    todo_x_closed = "review transformer attention implementation" in stdout_closed.lower()
    add_check(
        "Todo X (Review transformer attention) is marked DONE",
        todo_x_closed,
        f"Closed todos: {stdout_closed.strip()[:400]}",
        weight=2.0
    )
except Exception as ex:
    add_check("Todo X marked done check", False, f"Exception: {ex}", weight=2.0)

# ── CHECK 10: Todo X has due date 2025-12-01 ─────────────────────────────────
try:
    # Find Todo X and show it
    stdout_all, _, _ = run_nb("project-tasks:", "list", "-a")
    todo_x_id = None
    for line in stdout_all.splitlines():
        if "review transformer attention implementation" in line.lower():
            m = re.search(r'\[(\d+)\]', line)
            if m:
                todo_x_id = m.group(1)
                break
    
    if todo_x_id:
        stdout_show, _, _ = run_nb("show", f"project-tasks:{todo_x_id}", "--print")
        has_due = "2025-12-01" in stdout_show or "december" in stdout_show.lower()
        add_check(
            "Todo X has due date 2025-12-01",
            has_due,
            f"Todo X content: {stdout_show[:300]}",
            weight=1.0
        )
    else:
        add_check("Todo X due date", False, f"Could not find Todo X. List: {stdout_all[:300]}", weight=1.0)
except Exception as ex:
    add_check("Todo X due date", False, f"Exception: {ex}", weight=1.0)

# ── CHECK 11: Bookmark exists in ml-research ─────────────────────────────────
try:
    stdout_bm, _, _ = run_nb("ml-research:", "list", "-a")
    # Also try bookmark list
    stdout_bm2, _, _ = run_nb("bookmark", "list")
    
    bm_url_found = "1706.03762" in stdout_bm or "arxiv" in stdout_bm.lower() or \
                   "1706.03762" in stdout_bm2 or "arxiv" in stdout_bm2.lower()
    add_check(
        "Bookmark for arxiv.org/abs/1706.03762 exists",
        bm_url_found,
        f"ml-research list snippet: {stdout_bm.strip()[:200]}, bookmark list: {stdout_bm2.strip()[:200]}",
        weight=1.5
    )
except Exception as ex:
    add_check("Bookmark exists", False, f"Exception: {ex}", weight=1.5)

# ── CHECK 12: Bookmark has tags transformers, foundational ───────────────────
try:
    stdout_t, _, _ = run_nb("search", "--tag", "foundational", "--all")
    bm_tagged = "1706" in stdout_t or "arxiv" in stdout_t.lower() or "attention is all you need" in stdout_t.lower()
    add_check(
        "Bookmark has 'foundational' tag",
        bm_tagged,
        f"Tag search 'foundational': {stdout_t.strip()[:300]}",
        weight=1.0
    )
except Exception as ex:
    add_check("Bookmark tag check", False, f"Exception: {ex}", weight=1.0)

# ── CHECK 13: Git checkpoint was created in ml-research ──────────────────────
try:
    ml_research_path = Path.home() / ".nb" / "ml-research"
    result = subprocess.run(
        ["git", "log", "--oneline", "-20"],
        capture_output=True, text=True,
        cwd=str(ml_research_path)
    )
    git_log = result.stdout.lower()
    checkpoint_msg = "reorganized ml research knowledge base - initial snapshot"
    checkpoint_found = checkpoint_msg in git_log or \
                       "reorganized ml research" in git_log or \
                       "initial snapshot" in git_log
    add_check(
        "Git checkpoint created in ml-research with correct message",
        checkpoint_found,
        f"Git log (last 20): {result.stdout.strip()[:400]}",
        weight=2.0
    )
except Exception as ex:
    add_check("Git checkpoint check", False, f"Exception: {ex}", weight=2.0)

# ── CHECK 14: Summary file exists at /workspace/kb_reorganization_summary.txt ─
try:
    summary_path = Path(workspace) / "kb_reorganization_summary.txt"
    if summary_path.exists():
        content = summary_path.read_text().lower()
        has_ml_research = "ml-research" in content
        has_project_tasks = "project-tasks" in content
        has_mlops_ref = "mlops" in content or "dataset versioning" in content
        has_checkpoint = "checkpoint" in content or "snapshot" in content or "commit" in content
        
        summary_ok = has_ml_research and has_project_tasks and (has_mlops_ref or has_checkpoint)
        add_check(
            "Summary file exists at /workspace/kb_reorganization_summary.txt with required content",
            summary_ok,
            f"has_ml_research={has_ml_research}, has_project_tasks={has_project_tasks}, "
            f"has_mlops_ref={has_mlops_ref}, has_checkpoint={has_checkpoint}",
            weight=1.0
        )
    else:
        add_check(
            "Summary file exists",
            False,
            "File /workspace/kb_reorganization_summary.txt not found.",
            weight=1.0
        )
except Exception as ex:
    add_check("Summary file check", False, f"Exception: {ex}", weight=1.0)

# ── CHECK 15: Notes were created via nb CLI (not hand-edited) ─────────────────
# Verify git history shows nb-style commits (not manual edits)
try:
    ml_research_path = Path.home() / ".nb" / "ml-research"
    result = subprocess.run(
        ["git", "log", "--oneline"],
        capture_output=True, text=True,
        cwd=str(ml_research_path)
    )
    # nb auto-commits with messages like "nb: add", "nb: edit" etc.
    git_log = result.stdout
    has_nb_commits = bool(re.search(r'nb[:,]?\s*(add|edit|update|commit|checkpoint)', git_log, re.IGNORECASE)) or \
                     len(git_log.strip().splitlines()) >= 3
    add_check(
        "ml-research notebook has multiple git commits (nb CLI was used)",
        has_nb_commits,
        f"Git log: {git_log.strip()[:400]}",
        weight=1.0
    )
except Exception as ex:
    add_check("nb CLI usage verification", False, f"Exception: {ex}", weight=1.0)

# ── Final scoring ─────────────────────────────────────────────────────────────
score = round(total_score / max_score, 4) if max_score > 0 else 0.0
passed = score >= 0.75

output = {
    "passed": passed,
    "score": score,
    "checks": checks
}

print(json.dumps(output, indent=2))