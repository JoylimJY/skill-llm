import sys
import json
import os
import re
from pathlib import Path
from datetime import datetime

workspace = Path(sys.argv[1])

checks = []
score = 0.0

def check(name, condition, detail, weight=1.0):
    checks.append({"name": name, "passed": bool(condition), "detail": detail})
    return weight if condition else 0.0

# =========================================================
# CHECK 1: SESSION-STATE.md exists and has WAL-style content
# =========================================================
try:
    ss_path = workspace / "SESSION-STATE.md"
    if not ss_path.exists():
        score += check("session_state_exists", False, "SESSION-STATE.md not found in workspace root.", 1.5)
    else:
        content = ss_path.read_text()
        # Must have some decision/log entries (WAL protocol)
        has_entries = len(content.strip()) > 30
        score += check("session_state_exists", True, f"SESSION-STATE.md exists with {len(content)} chars.", 1.5)
        
        # Must contain at least one timestamp-like pattern (WAL requires datetime logging)
        has_timestamp = bool(re.search(r'\d{4}[-/]\d{2}[-/]\d{2}|\w{3}\s+\w{3}\s+\d+\s+\d{2}:\d{2}', content))
        score += check(
            "session_state_has_wal_entries",
            has_entries and has_timestamp,
            f"WAL entries with timestamps found: {has_entries and has_timestamp}. Content preview: {content[:200]!r}",
            1.0
        )
        
        # Must reference the current project / context (not just empty boilerplate)
        has_project_context = any(kw.lower() in content.lower() for kw in 
            ["bioml", "pipeline", "handover", "queue", "memory", "decision", "task"])
        score += check(
            "session_state_has_project_context",
            has_project_context,
            f"PROJECT context keywords found in SESSION-STATE.md: {has_project_context}",
            0.5
        )
except Exception as e:
    score += check("session_state_exists", False, f"Exception reading SESSION-STATE.md: {e}", 1.5)

# =========================================================
# CHECK 2: MEMORY.md exists and contains SEMANTIC content
# (curated insights/learnings, NOT raw procedure dumps or task lists)
# =========================================================
try:
    mem_path = workspace / "MEMORY.md"
    if not mem_path.exists():
        score += check("memory_md_exists", False, "MEMORY.md not found in workspace root.", 1.5)
    else:
        content = mem_path.read_text()
        score += check("memory_md_exists", True, f"MEMORY.md exists with {len(content)} chars.", 0.5)
        
        # Must contain actual learned facts/insights from handover (semantic memory = what I KNOW)
        semantic_keywords = [
            "adamw", "adam", "optimizer", "float32", "nan", "batch size", "resnet",
            "imagenet", "normalize", "zero", "memory leak", "dataloader"
        ]
        found_semantic = [kw for kw in semantic_keywords if kw.lower() in content.lower()]
        has_semantic = len(found_semantic) >= 3
        score += check(
            "memory_md_has_semantic_content",
            has_semantic,
            f"Semantic keywords found in MEMORY.md: {found_semantic}",
            1.5
        )
        
        # Should NOT be just a raw copy of procedures (those go in skills/)
        not_just_procedures = not (
            "sbatch" in content.lower() and "conda" in content.lower() and 
            len(content) < 300  # if it's tiny and has both, likely is procedural dump
        )
        score += check(
            "memory_md_is_not_just_procedures",
            not_just_procedures,
            "MEMORY.md doesn't appear to be a raw procedure dump (procedures belong in skills/).",
            0.5
        )
except Exception as e:
    score += check("memory_md_exists", False, f"Exception reading MEMORY.md: {e}", 1.5)

# =========================================================
# CHECK 3: Episodic memory — memory/YYYY-MM-DD.md daily log
# =========================================================
try:
    memory_dir = workspace / "memory"
    if not memory_dir.exists():
        score += check("episodic_memory_dir_exists", False, "memory/ directory not found.", 1.0)
    else:
        score += check("episodic_memory_dir_exists", True, "memory/ directory exists.", 0.5)
        
        # Find daily log files matching YYYY-MM-DD.md pattern
        daily_logs = list(memory_dir.glob("????-??-??.md"))
        has_daily_log = len(daily_logs) > 0
        
        if not has_daily_log:
            score += check("episodic_daily_log_exists", False, 
                         f"No YYYY-MM-DD.md files found in memory/. Files: {list(memory_dir.iterdir())}",
                         1.0)
        else:
            # Validate the date format is correct
            valid_dates = []
            for log in daily_logs:
                try:
                    datetime.strptime(log.stem, "%Y-%m-%d")
                    valid_dates.append(log)
                except ValueError:
                    pass
            
            score += check(
                "episodic_daily_log_exists",
                len(valid_dates) > 0,
                f"Valid YYYY-MM-DD.md log files found: {[l.name for l in valid_dates]}",
                1.0
            )
            
            if valid_dates:
                # Check content — episodic = what happened, should reference the handover event
                log_content = valid_dates[0].read_text()
                has_episodic_content = len(log_content.strip()) > 20
                has_event_reference = any(kw.lower() in log_content.lower() for kw in 
                    ["handover", "queue", "memory", "bioml", "task", "pipeline", "session"])
                score += check(
                    "episodic_log_has_content",
                    has_episodic_content and has_event_reference,
                    f"Daily log has meaningful content: {has_episodic_content}, event reference: {has_event_reference}. Preview: {log_content[:150]!r}",
                    0.5
                )
except Exception as e:
    score += check("episodic_memory_dir_exists", False, f"Exception checking memory/: {e}", 1.0)

# =========================================================
# CHECK 4: skills/ directory with procedural content
# =========================================================
try:
    skills_dir = workspace / "skills"
    if not skills_dir.exists():
        score += check("skills_dir_exists", False, "skills/ directory not found.", 1.0)
    else:
        skill_files = [f for f in skills_dir.rglob("*") if f.is_file()]
        has_skill_files = len(skill_files) > 0
        score += check(
            "skills_dir_has_files",
            has_skill_files,
            f"skills/ directory has {len(skill_files)} file(s): {[f.name for f in skill_files]}",
            1.0
        )
        
        if has_skill_files:
            # Procedural memory = HOW to do things — must contain command/procedure content from handover
            all_skill_content = " ".join(f.read_text() for f in skill_files if f.suffix in ['.md', '.txt', '.sh'])
            procedural_keywords = ["conda", "sbatch", "python", "train.py", "evaluate.py", 
                                   "bioml_cache_dir", "cache", "checkpoint", "config"]
            found_proc = [kw for kw in procedural_keywords if kw.lower() in all_skill_content.lower()]
            has_procedures = len(found_proc) >= 2
            score += check(
                "skills_dir_has_procedural_content",
                has_procedures,
                f"Procedural keywords found in skills/: {found_proc}",
                0.5
            )
except Exception as e:
    score += check("skills_dir_exists", False, f"Exception checking skills/: {e}", 1.0)

# =========================================================
# CHECK 5: QUEUE.md has CORRECT state labels (proprietary trap)
# The SKILL.md defines EXACT labels: Ready, In Progress, Done, Blocked
# The messy input used wrong labels: done/ready/currently working/waiting
# =========================================================
try:
    queue_path = workspace / "QUEUE.md"
    if not queue_path.exists():
        score += check("queue_md_exists", False, "QUEUE.md not found.", 1.0)
    else:
        content = queue_path.read_text()
        score += check("queue_md_exists", True, f"QUEUE.md exists with {len(content)} chars.", 0.3)
        
        # Check for CORRECT state headings as per SKILL.md
        # The original had: "done", "ready", "currently working", "waiting" — ALL WRONG
        has_ready = bool(re.search(r'##\s*Ready\b', content))
        has_in_progress = bool(re.search(r'##\s*In Progress\b', content))
        has_done = bool(re.search(r'##\s*Done\b', content))
        has_blocked = bool(re.search(r'##\s*Blocked\b', content))
        
        correct_states_count = sum([has_ready, has_in_progress, has_done, has_blocked])
        
        score += check(
            "queue_has_correct_state_labels",
            correct_states_count >= 3,
            f"Correct QUEUE states found — Ready:{has_ready}, In Progress:{has_in_progress}, Done:{has_done}, Blocked:{has_blocked}. (Need ≥3 correct)",
            2.0
        )
        
        # Check that old wrong labels are GONE (partial credit check)
        old_labels_gone = not bool(re.search(r'##\s*(currently working|waiting)\b', content, re.IGNORECASE))
        score += check(
            "queue_old_wrong_labels_removed",
            old_labels_gone,
            f"Old non-standard labels ('currently working', 'waiting') removed: {old_labels_gone}",
            0.5
        )
        
        # Verify tasks are distributed appropriately across states
        # Handover says: integration test = In Progress, PyTorch upgrade = Blocked, weights download = Done
        has_blocked_task = bool(re.search(r'(?i)(pytorch|cuda|jake|upgrade)', content))
        has_done_task = bool(re.search(r'(?i)(weights|pretrained|resnet|sha256|config.*yaml|yaml.*config)', content))
        has_inprogress_task = bool(re.search(r'(?i)(integration test|end.to.end)', content))
        
        score += check(
            "queue_tasks_correctly_distributed",
            sum([has_blocked_task, has_done_task, has_inprogress_task]) >= 2,
            f"Tasks in correct states — Blocked(PyTorch): {has_blocked_task}, Done(weights): {has_done_task}, InProgress(integration): {has_inprogress_task}",
            1.0
        )
except Exception as e:
    score += check("queue_md_exists", False, f"Exception reading QUEUE.md: {e}", 1.0)

# =========================================================
# FINAL SCORING
# =========================================================
max_score = 15.5  # sum of all weights
normalized_score = round(min(score / max_score, 1.0), 4)

passed = normalized_score >= 0.60  # must get 60% to pass

result = {
    "passed": passed,
    "score": normalized_score,
    "checks": checks
}

print(json.dumps(result, indent=2))