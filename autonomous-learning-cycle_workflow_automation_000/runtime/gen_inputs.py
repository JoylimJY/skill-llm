import os
import json
import random

random.seed(42)

workspace = "/workspace"

# Create the core skill directory structure (as-installed, but INCOMPLETE/misconfigured)
skill_dir = os.path.join(workspace, "skills", "autonomous-learning-cycle")
os.makedirs(skill_dir, exist_ok=True)

# Create engines directory with stub JS files (they exist but configs are wrong/missing)
engines_dir = os.path.join(skill_dir, "engines")
os.makedirs(engines_dir, exist_ok=True)

engine_files = [
    "evolution-engine.js",
    "extractor.js",
    "confidence.js",
    "skill-creator.js",
    "reflection.js",
    "learning-direction.js",
]
for ef in engine_files:
    with open(os.path.join(engines_dir, ef), "w") as f:
        f.write(f"// {ef} - engine stub\nconsole.log('Engine: {ef}');\n")

# Create handlers directory
handlers_dir = os.path.join(skill_dir, "handlers")
os.makedirs(handlers_dir, exist_ok=True)
for hf in ["session-start.js", "file-generated.js"]:
    with open(os.path.join(handlers_dir, hf), "w") as f:
        f.write(f"// {hf} - handler stub\n")

# Create a BROKEN/INCOMPLETE configs directory - this is what agent must fix
configs_dir = os.path.join(skill_dir, "configs")
os.makedirs(configs_dir, exist_ok=True)

# Write a WRONG confidence config (wrong field names, wrong structure, wrong values)
broken_confidence = {
    "weights": {
        "base": 0.5,        # WRONG: should be "baseScore"
        "success": 0.3,     # WRONG: should be "successRate"
        "usage": 0.15,      # WRONG: should be "usageBonus"
        "decay": 0.05,      # WRONG: should be "timeDecay"
        # MISSING: "qualityBonus"
    },
    "thresholds": {
        "high": 0.9,        # WRONG value per task spec (should be 0.8 per best practices)
        "medium": 0.5,      # WRONG: should be 0.4
        # MISSING: "low"
    },
    "decay": {
        "halfLife": 30,     # WRONG: should be "daysToHalf"
        # MISSING: "minDecay"
    }
}
with open(os.path.join(configs_dir, "confidence-config.json"), "w") as f:
    json.dump(broken_confidence, f, indent=2)

# Write a WRONG cron config (wrong schedules, missing jobs)
broken_cron = {
    "jobs": [
        {
            "name": "evolution-loop",           # WRONG: should be "自主进化循环"
            "schedule": "0 */17 * * *",         # WRONG: should be "*/17 * * * *"
            "command": "node engines/evolution-engine.js start"  # WRONG: should be "run"
        },
        {
            "name": "daily-reflection",         # WRONG: should be "每日反思"
            "schedule": "0 22 * * *",           # WRONG: should be "0 23 * * *"
            "command": "node engines/reflection.js daily"        # This one is correct
        }
        # MISSING: weekly reflection job
        # MISSING: learning direction job
    ]
}
with open(os.path.join(configs_dir, "cron-jobs.json"), "w") as f:
    json.dump(broken_cron, f, indent=2)

# Create docs directory with stub docs
docs_dir = os.path.join(skill_dir, "docs")
os.makedirs(docs_dir, exist_ok=True)
for doc in ["INSTALL.md", "USAGE.md", "ARCHITECTURE.md"]:
    with open(os.path.join(docs_dir, doc), "w") as f:
        f.write(f"# {doc}\n\nDocumentation placeholder.\n")

# Create init.js, setup-cron.js, start.js stubs
for js in ["init.js", "setup-cron.js", "start.js"]:
    with open(os.path.join(skill_dir, js), "w") as f:
        f.write(f"// {js} - initialization stub\nconsole.log('Running {js}');\n")

# Create distractor files and directories to make the workspace realistic and noisy
distractor_dirs = [
    "projects/alpha/src",
    "projects/alpha/tests",
    "projects/beta/lib",
    "logs/2026-03",
    "logs/2026-04",
    "memory/old-sessions",
    "tmp/cache",
    "archive/v0.9",
    "archive/v0.8/configs",
    ".config/system",
]
for d in distractor_dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = {
    "projects/alpha/src/main.js": "// main application\nconsole.log('app running');\n",
    "projects/alpha/tests/test_main.js": "// tests\ndescribe('main', () => {});\n",
    "projects/beta/lib/utils.js": "// utility functions\nmodule.exports = {};\n",
    "logs/2026-03/system.log": "2026-03-01 INFO System started\n2026-03-02 WARN High memory\n",
    "logs/2026-04/error.log": "2026-04-01 ERROR Connection timeout\n",
    "memory/old-sessions/session-001.json": json.dumps({"session": "001", "tasks": [], "date": "2026-03-01"}),
    "tmp/cache/temp_data.bin": "binary_placeholder_data_xyz\n",
    "archive/v0.9/README.md": "# v0.9 Archive\nOld version, deprecated.\n",
    "archive/v0.8/configs/old-confidence.json": json.dumps({"version": "0.8", "threshold": 0.6}),
    ".config/system/env.conf": "NODE_ENV=production\nDEBUG=false\n",
    "projects/alpha/package.json": json.dumps({"name": "alpha", "version": "1.0.0", "dependencies": {}}),
}
for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# Create a partial tasks directory (exists but no queue.json yet)
tasks_dir = os.path.join(workspace, "tasks")
os.makedirs(tasks_dir, exist_ok=True)
# Put a corrupted/old tasks file to distract
with open(os.path.join(tasks_dir, "completed.json"), "w") as f:
    json.dump({"tasks": [{"id": "t001", "status": "completed", "name": "old task"}]}, f, indent=2)

# Create memory directory structure (partial - reflections dir missing)
memory_dir = os.path.join(workspace, "memory")
os.makedirs(memory_dir, exist_ok=True)
with open(os.path.join(memory_dir, "patterns.json"), "w") as f:
    json.dump({"patterns": []}, f, indent=2)

print("Workspace initialized with broken configs and distractor files.")
print(f"Skill dir: {skill_dir}")
print(f"Configs dir: {configs_dir}")