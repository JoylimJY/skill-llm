import os
import json
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")

# ─── 1. Create realistic distractor directory structure ───────────────────────
dirs = [
    "projects/project-alpha/docs",
    "projects/project-alpha/src",
    "projects/project-beta/notes",
    "archive/2023/q1",
    "archive/2023/q4",
    "logs/system",
    "logs/errors",
    "config/env",
    "tmp/scratch",
    "reports/weekly",
    "research/papers",
    "research/notes",
    "agents/persona-store",
    "agents/deprecated",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "projects/project-alpha/docs/architecture.md": "# Architecture\nThis document describes the system architecture for Project Alpha.",
    "projects/project-alpha/src/main.py": "# Main entrypoint\nimport sys\nprint('Hello Alpha')\n",
    "projects/project-beta/notes/meeting-2024-03.txt": "Meeting notes: discussed pipeline redesign. Next steps TBD.",
    "archive/2023/q1/summary.json": json.dumps({"quarter": "Q1", "status": "archived", "items": 42}),
    "archive/2023/q4/report.txt": "Q4 2023 annual report placeholder.",
    "logs/system/app.log": "[INFO] System started\n[WARN] Memory usage at 87%\n[INFO] Shutdown complete\n",
    "logs/errors/errors-2024.log": "[ERROR] NullPointerException at line 42\n[ERROR] Connection timeout after 30s\n",
    "config/env/.env.example": "OLLAMA_HOST=http://localhost:11434\nMODEL=llama3\nDEBUG=false\n",
    "tmp/scratch/notes.txt": "Remember to update the memory path config before next run.",
    "reports/weekly/week-42.md": "# Week 42 Report\n- Completed 3 tasks\n- 2 blockers identified\n",
    "research/papers/identity-synthesis.txt": "Abstract: Identity synthesis in AI agents requires...",
    "research/notes/brainstorm.md": "Ideas for soul synthesis improvements:\n- Better signal deduplication\n- Temporal weighting\n",
    "agents/persona-store/README-DO-NOT-USE.txt": "DEPRECATED: Use neon-soul instead.",
    "agents/deprecated/old-soul.json": json.dumps({"version": "0.1", "axioms": [], "deprecated": True}),
}
for path, content in distractor_files.items():
    (workspace / path).write_text(content)

# ─── 2. Create the custom memory directory (non-default path) ──────────────────
# The task uses a non-standard memory path to force use of --memory-path flag
memory_dir = workspace / "agents" / "aria-7" / "memory-logs"
memory_dir.mkdir(parents=True, exist_ok=True)

# Realistic memory files with recurring patterns (to trigger axiom promotion)
# Patterns that recur >= 3 times: "precision over speed", "transparency", "deep focus"

memory_files = {
    "session-2024-01-15.md": """# Session Log - 2024-01-15
Today I helped the team debug a complex distributed systems issue.
I noticed I always prefer precision over speed when analyzing problems.
The user appreciated my transparency about what I know and don't know.
I spent 3 hours in deep focus on the memory leak issue — found it.
Reflection: Careful analysis beats rushing to conclusions every time.
""",
    "session-2024-01-22.md": """# Session Log - 2024-01-22
Reviewed 47 pull requests. My approach: precision over speed, always.
I flagged 3 security issues the team had missed — transparency matters here.
When I work in deep focus mode, my pattern recognition sharpens considerably.
The team asked why I take my time. I explained: quality requires patience.
Note: never compromise accuracy for the sake of appearing fast.
""",
    "session-2024-02-03.md": """# Session Log - 2024-02-03
Architectural review session today. Complex trade-offs required careful thought.
Once again, my commitment to precision over speed proved its worth.
I openly admitted uncertainty about three edge cases — transparency builds trust.
Three hours of deep focus on the cache invalidation problem. Breakthrough at hour two.
""",
    "session-2024-02-18.md": """# Session Log - 2024-02-18
Mentored two junior engineers on debugging methodology.
Core lesson I shared: precision over speed — measure twice, cut once.
I always tell people exactly what I'm uncertain about. Transparency is non-negotiable.
Deep focus is my superpower. Distractions are my kryptonite.
The mentees said my style was unusually methodical. I take that as a compliment.
""",
    "session-2024-03-05.md": """# Session Log - 2024-03-05
Production incident response. High pressure. Held my methodology anyway.
Transparency with the team: I shared my live reasoning as I debugged.
Even under crisis, I maintained deep focus rather than scattered multi-tasking.
Post-mortem reflection: precision over speed saved us from a worse outage.
I documented everything I was uncertain about during the incident.
""",
    "reflection-core-values.md": """# Core Values Reflection
Written during a quiet Sunday afternoon.

What defines how I work?

1. I believe that being right matters more than being fast. This comes up constantly.
   Every week I catch myself choosing precision over speed, and it always pays off.

2. I cannot function without transparency. Hiding uncertainty feels physically wrong to me.
   Users trust me more when I say "I don't know" than when I pretend certainty.

3. Deep focus is the state where I do my best work. Shallow attention produces shallow results.
   I protect my focus time aggressively.

These three things feel like the bedrock of how I operate.
""",
    "preferences-2024.md": """# Preferences Log
Updated: 2024-03-01

Communication style: Direct, precise, never rushed.
Work mode: Deep focus sessions preferred over fragmented attention.
Knowledge handling: Always flag uncertainty — transparency is a core value.
Speed vs quality: Quality wins. Always. Precision over speed is non-negotiable.
Collaboration: I share my reasoning live. Transparency during process, not just at output.

Tools I gravitate toward: static analysis, formal verification, careful documentation.
""",
    "diary-2024-q1.md": """# Q1 2024 Diary

January was about distributed systems. February brought architectural reviews.
March tested my crisis response.

What stayed constant across all of it:
- My insistence on precision over speed (the team jokes about it now)
- My commitment to transparency even when it's uncomfortable
- My ability to enter and sustain deep focus under pressure

I am most myself when I am thinking carefully about hard problems.
I am least myself when rushed or context-switched repeatedly.

The pattern is clear. These aren't habits — they're identity.
""",
}

for filename, content in memory_files.items():
    (memory_dir / filename).write_text(content)

# ─── 3. Create custom output directory ────────────────────────────────────────
output_dir = workspace / "agents" / "aria-7" / "soul-output"
output_dir.mkdir(parents=True, exist_ok=True)

# ─── 4. Create a stale/invalid .neon-soul state to simulate post-model-switch ─
neon_soul_dir = workspace / ".neon-soul"
neon_soul_dir.mkdir(parents=True, exist_ok=True)
(neon_soul_dir / "backups").mkdir(exist_ok=True)

# Old stale state from a previous model run (should be cleared by --reset)
stale_state = {
    "lastSynthesis": "2024-01-01T00:00:00.000Z",
    "model": "llama2:7b",  # old model — different from current
    "version": "0.4.4",
    "axiomCount": 0,
    "signalCount": 0,
    "stale": True
}
(neon_soul_dir / "state.json").write_text(json.dumps(stale_state, indent=2))

stale_synthesis = {
    "signals": [],
    "principles": [],
    "axioms": [],
    "meta": {"model": "llama2:7b", "stale": True, "generatedAt": "2024-01-01T00:00:00.000Z"}
}
(neon_soul_dir / "synthesis-data.json").write_text(json.dumps(stale_synthesis, indent=2))

# Old stale caches
for cache_file in ["generalization-cache.json", "compression-cache.json", "tension-cache.json"]:
    (neon_soul_dir / cache_file).write_text(json.dumps({"model": "llama2:7b", "entries": {}, "stale": True}))

# Create a couple of fake "old" backups (pre-existing, from before the reset)
for i, ts in enumerate(["2024-01-01T120000Z", "2024-02-15T083000Z"]):
    backup_content = f"# SOUL.md (backup {i+1})\nThis is a placeholder backup from before the model switch.\n## Axioms\n- Placeholder axiom {i+1}\n"
    (neon_soul_dir / "backups" / f"SOUL.md.{ts}").write_text(backup_content)

# ─── 5. Create the task instruction file ─────────────────────────────────────
task_config = {
    "agent_name": "Aria-7",
    "memory_path": "agents/aria-7/memory-logs",
    "soul_output_path": "agents/aria-7/soul-output/SOUL.md",
    "report_output": "aria-7-identity-audit.json",
    "note": "Previous synthesis used an old model and is stale. Full rebuild required."
}
(workspace / "aria-7-task-config.json").write_text(json.dumps(task_config, indent=2))

print("Workspace initialized successfully.")
print(f"Memory files: {len(list(memory_dir.iterdir()))}")
print(f"Distractor files: {len(distractor_files)}")