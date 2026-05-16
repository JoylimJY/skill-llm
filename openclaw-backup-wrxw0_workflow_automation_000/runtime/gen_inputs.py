import os
import json
import random
import hashlib
import tarfile
import io
import time
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

WORKSPACE = Path("/workspace")

# Create the ~/.claude directory structure
HOME = Path("/root")
CLAUDE_DIR = HOME / ".claude"

# Create directory structure
dirs = [
    CLAUDE_DIR / "skills" / "code-review",
    CLAUDE_DIR / "skills" / "code-review" / "supporting",
    CLAUDE_DIR / "skills" / "deploy-helper",
    CLAUDE_DIR / "skills" / "deploy-helper" / "templates",
    CLAUDE_DIR / "skills" / "doc-writer",
    CLAUDE_DIR / "commands",
    CLAUDE_DIR / "contexts",
    CLAUDE_DIR / "templates",
    CLAUDE_DIR / "mcp",
]

for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# Populate skills with SKILL.md files
skills_content = {
    "code-review": """---
name: code-review
description: Automated code review assistant
---
# Code Review Skill
Reviews code for quality, security, and best practices.
""",
    "deploy-helper": """---
name: deploy-helper
description: Deployment automation helper
---
# Deploy Helper Skill
Automates deployment workflows across environments.
""",
    "doc-writer": """---
name: doc-writer
description: Documentation generation tool
---
# Doc Writer Skill
Generates technical documentation from source code.
""",
}

for skill_name, content in skills_content.items():
    (CLAUDE_DIR / "skills" / skill_name / "SKILL.md").write_text(content)

# Supporting files in skills
(CLAUDE_DIR / "skills" / "code-review" / "supporting" / "rules.json").write_text(
    json.dumps({"max_line_length": 120, "enforce_types": True}, indent=2)
)
(CLAUDE_DIR / "skills" / "deploy-helper" / "templates" / "deploy.sh").write_text(
    "#!/bin/bash\necho 'Deploying...'\n"
)
(CLAUDE_DIR / "skills" / "deploy-helper" / "templates" / "rollback.sh").write_text(
    "#!/bin/bash\necho 'Rolling back...'\n"
)

# Commands
commands = {
    "review.md": "# /review\nTriggers code review on current file.\n",
    "deploy.md": "# /deploy\nInitiates deployment pipeline.\n",
    "summarize.md": "# /summarize\nSummarizes the current context.\n",
}
for cmd_name, content in commands.items():
    (CLAUDE_DIR / "commands" / cmd_name).write_text(content)

# Settings files
settings = {
    "model": "claude-opus-4",
    "theme": "dark",
    "auto_save": True,
    "max_tokens": 8192,
    "plugins": ["code-review", "deploy-helper"]
}
(CLAUDE_DIR / "settings.json").write_text(json.dumps(settings, indent=2))

settings_local = {
    "machine_id": "workstation-dev-42",
    "local_model_path": "/opt/models/local",
    "gpu_enabled": False
}
(CLAUDE_DIR / "settings.local.json").write_text(json.dumps(settings_local, indent=2))

# MCP config
(CLAUDE_DIR / "mcp").mkdir(exist_ok=True)
(CLAUDE_DIR / "mcp" / "servers.json").write_text(
    json.dumps({"servers": [{"name": "filesystem", "port": 3001}]}, indent=2)
)

# Contexts and templates (distractor files)
(CLAUDE_DIR / "contexts" / "project-alpha.ctx").write_text("Context for project alpha\n")
(CLAUDE_DIR / "contexts" / "debug-session.ctx").write_text("Debug session context\n")
(CLAUDE_DIR / "templates" / "pr-template.md").write_text("# PR Template\n## Description\n## Testing\n")
(CLAUDE_DIR / "templates" / "bug-report.md").write_text("# Bug Report\n## Steps to Reproduce\n")

# Create the backup directory with pre-existing OLD backups
BACKUP_DIR = HOME / "openclaw-backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# Generate 5 pre-existing "skills" type backups with fake timestamps (old ones)
# These simulate already-existing archives that need to be subject to cleanup
# We'll create them with varied timestamps, oldest first

def make_fake_tar_gz(path: Path, label: str):
    """Create a minimal valid tar.gz file."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w:gz') as tf:
        content = f"fake backup content: {label}\n".encode()
        info = tarfile.TarInfo(name=f"fake_{label}.txt")
        info.size = len(content)
        tf.addfile(info, io.BytesIO(content))
    buf.seek(0)
    path.write_bytes(buf.read())

# Old timestamps (simulate backups created on past days, older first)
old_timestamps = [
    "20250101_020000",
    "20250215_020000",
    "20250310_020000",
    "20250401_020000",
    "20250510_020000",
]

for ts in old_timestamps:
    backup_name = f"openclaw_skills_{ts}.tar.gz"
    backup_path = BACKUP_DIR / backup_name
    make_fake_tar_gz(backup_path, ts)
    
    # Generate sha256 for each existing backup
    sha256_hash = hashlib.sha256(backup_path.read_bytes()).hexdigest()
    (BACKUP_DIR / f"{backup_name}.sha256").write_text(
        f"{sha256_hash}  {backup_name}\n"
    )
    
    # Set file modification time to simulate age (oldest first)
    # Parse timestamp
    dt = datetime.strptime(ts, "%Y%m%d_%H%M%S")
    mtime = dt.timestamp()
    os.utime(backup_path, (mtime, mtime))

# Workspace also gets some distractor files
(WORKSPACE / "notes.txt").write_text("Meeting notes: discuss backup rotation policy\n")
(WORKSPACE / "todo.md").write_text("TODO: implement backup cleanup\n- Keep only last 3 backups\n")
(WORKSPACE / "config_draft.json").write_text(
    json.dumps({"retention": 3, "backup_type": "skills"}, indent=2)
)

# Create a distractor backup directory with wrong structure to mislead
wrong_dir = WORKSPACE / "backup_attempt"
wrong_dir.mkdir(exist_ok=True)
(wrong_dir / "README.txt").write_text("This is not the right place for backups\n")

print("Workspace generation complete.")
print(f"~/.claude structure created at {CLAUDE_DIR}")
print(f"Pre-existing backups created at {BACKUP_DIR}")
print(f"  - {len(old_timestamps)} old 'skills' type backups with sha256 files")