#!/usr/bin/env python3
"""
Build the initial sandbox workspace.
Creates:
- A realistic github repo directory with several pre-existing repos
- The scripts/ directory with scan_repos.py and update_kb.py
- Distractor files and directories
- An outdated/partial CLAUDE.md (missing the new repo)
"""

import os
import json
import random
import textwrap
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── 1. Create the github directory and pre-existing repos ──────────────────────

GITHUB_DIR = WORKSPACE / "github_repos"
GITHUB_DIR.mkdir(parents=True, exist_ok=True)

# Pre-existing repo 1: data-pipeline
repo1 = GITHUB_DIR / "data-pipeline"
(repo1 / "src").mkdir(parents=True, exist_ok=True)
(repo1 / "tests").mkdir(parents=True, exist_ok=True)
(repo1 / "src" / "pipeline.py").write_text(
    "# Main ETL pipeline logic\ndef run(): pass\n"
)
(repo1 / "src" / "config.yaml").write_text("workers: 4\nbatch_size: 1000\n")
(repo1 / "tests" / "test_pipeline.py").write_text(
    "def test_run(): assert True\n"
)
(repo1 / "requirements.txt").write_text("pandas>=1.3\nnumpy>=1.21\n")
(repo1 / ".git").mkdir(exist_ok=True)
(repo1 / ".git" / "config").write_text(
    "[core]\n\trepositoryformatversion = 0\n[remote \"origin\"]\n\turl = https://github.com/acme/data-pipeline\n"
)

# Pre-existing repo 2: auth-service
repo2 = GITHUB_DIR / "auth-service"
(repo2 / "app").mkdir(parents=True, exist_ok=True)
(repo2 / "app" / "main.py").write_text(
    "from flask import Flask\napp = Flask(__name__)\n"
)
(repo2 / "app" / "models.py").write_text("class User: pass\n")
(repo2 / "app" / "routes.py").write_text("# Auth routes\n")
(repo2 / "Dockerfile").write_text("FROM python:3.9-slim\n")
(repo2 / ".git").mkdir(exist_ok=True)
(repo2 / ".git" / "config").write_text(
    "[core]\n\trepositoryformatversion = 0\n[remote \"origin\"]\n\turl = https://github.com/acme/auth-service\n"
)

# Pre-existing repo 3: analytics-dashboard (no git — should be skipped/handled gracefully)
repo3 = GITHUB_DIR / "analytics-dashboard"
(repo3 / "components").mkdir(parents=True, exist_ok=True)
(repo3 / "components" / "chart.js").write_text("export const Chart = () => {};\n")
(repo3 / "components" / "table.js").write_text("export const Table = () => {};\n")
(repo3 / "package.json").write_text('{"name":"analytics-dashboard","version":"1.0.0"}\n')
# No .git directory — intentionally not a git repo

# Distractor files in github dir
(GITHUB_DIR / "notes.txt").write_text(
    "TODO: check if analytics-dashboard needs auth integration\n"
)
(GITHUB_DIR / "download_list.csv").write_text(
    "repo,priority\nml-utils,high\nconfig-manager,medium\n"
)
(GITHUB_DIR / "archive").mkdir(exist_ok=True)
(GITHUB_DIR / "archive" / "old_clone_script.sh").write_text("#!/bin/bash\n# deprecated\n")

# Stale CLAUDE.md (only has partial info, missing analytics-dashboard, outdated)
stale_claude = GITHUB_DIR / "CLAUDE.md"
stale_claude.write_text(textwrap.dedent("""\
    # GitHub Repository Knowledge Base
    Last updated: 2024-01-15

    ## Repositories

    ### data-pipeline
    - **Path**: /workspace/github_repos/data-pipeline
    - **Summary**: ETL pipeline for data processing

    ### auth-service  
    - **Path**: /workspace/github_repos/auth-service
    - **Summary**: Authentication microservice

    <!-- NOTE: This file is auto-generated. Do not edit manually. -->
"""))

# ── 2. Create a bare git repo to serve as a local "remote" for cloning ─────────

BARE_REPOS_DIR = WORKSPACE / "bare_remotes"
BARE_REPOS_DIR.mkdir(exist_ok=True)

ml_utils_bare = BARE_REPOS_DIR / "ml-utils.git"
ml_utils_bare.mkdir(exist_ok=True)

# We'll init this properly in the setup_script via git commands
# For now write a marker
(ml_utils_bare / ".gitkeep").write_text("")

# ── 3. Create the scripts/ directory with the proprietary helper scripts ───────

SCRIPTS_DIR = WORKSPACE / "scripts"
SCRIPTS_DIR.mkdir(exist_ok=True)

# scan_repos.py — scans a directory and returns JSON array of repo metadata
scan_repos_content = textwrap.dedent("""\
    #!/usr/bin/env python3
    \"\"\"
    scan_repos.py: Scan a local directory for git repositories and extract metadata.
    Usage: python3 scan_repos.py <directory>
    Outputs: JSON array to stdout
    \"\"\"
    import sys
    import json
    import os
    from pathlib import Path

    def get_repo_summary(repo_path):
        \"\"\"Extract a brief summary from a repository.\"\"\"
        p = Path(repo_path)
        summary_hints = []
        
        # Check for common descriptor files
        for fname in ["setup.py", "setup.cfg", "pyproject.toml", "package.json", 
                       "Cargo.toml", "go.mod", "Makefile", "Dockerfile"]:
            if (p / fname).exists():
                summary_hints.append(fname)
        
        # Count source files
        src_files = list(p.rglob("*.py")) + list(p.rglob("*.js")) + list(p.rglob("*.go"))
        src_count = len([f for f in src_files if ".git" not in str(f)])
        
        # Try to read a description from common locations
        description = ""
        for desc_file in [p / "description.txt", p / ".git" / "description"]:
            if desc_file.exists():
                content = desc_file.read_text().strip()
                if content and "Unnamed repository" not in content:
                    description = content
                    break
        
        if not description:
            description = f"Repository with {src_count} source file(s); contains: {', '.join(summary_hints) if summary_hints else 'misc files'}"
        
        return description

    def scan_directory(base_dir):
        base = Path(base_dir)
        if not base.exists():
            print(json.dumps({"error": f"Directory not found: {base_dir}"}))
            sys.exit(1)
        
        repos = []
        for item in sorted(base.iterdir()):
            if item.is_dir() and (item / ".git").exists():
                repos.append({
                    "name": item.name,
                    "path": str(item.resolve()),
                    "summary": get_repo_summary(item)
                })
        
        print(json.dumps(repos))

    if __name__ == "__main__":
        if len(sys.argv) < 2:
            print("Usage: python3 scan_repos.py <directory>", file=sys.stderr)
            sys.exit(1)
        scan_directory(sys.argv[1])
""")
(SCRIPTS_DIR / "scan_repos.py").write_text(scan_repos_content)

# update_kb.py — takes base dir + JSON repos string, writes CLAUDE.md
update_kb_content = textwrap.dedent("""\
    #!/usr/bin/env python3
    \"\"\"
    update_kb.py: Update the CLAUDE.md knowledge base file with repository metadata.
    Usage: python3 update_kb.py <github_directory> '<repos_json>'
    
    The repos_json must be a JSON array of objects with keys: name, path, summary
    CLAUDE.md is written to <github_directory>/CLAUDE.md
    \"\"\"
    import sys
    import json
    from pathlib import Path
    from datetime import datetime

    REQUIRED_KEYS = {"name", "path", "summary"}

    def update_knowledge_base(github_dir, repos_json_str):
        base = Path(github_dir)
        if not base.exists():
            print(f"Error: Directory not found: {github_dir}", file=sys.stderr)
            sys.exit(1)
        
        try:
            repos = json.loads(repos_json_str)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON: {e}", file=sys.stderr)
            sys.exit(1)
        
        if not isinstance(repos, list):
            print("Error: repos_json must be a JSON array", file=sys.stderr)
            sys.exit(1)
        
        for repo in repos:
            missing = REQUIRED_KEYS - set(repo.keys())
            if missing:
                print(f"Error: Repo entry missing keys: {missing}", file=sys.stderr)
                sys.exit(1)
        
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        lines = [
            "# GitHub Repository Knowledge Base",
            f"Last updated: {timestamp}",
            "",
            "## Repositories",
            "",
        ]
        
        for repo in repos:
            lines.append(f"### {repo['name']}")
            lines.append(f"- **Path**: {repo['path']}")
            lines.append(f"- **Summary**: {repo['summary']}")
            lines.append("")
        
        lines.append("<!-- NOTE: This file is auto-generated. Do not edit manually. -->")
        lines.append("")
        
        claude_md = base / "CLAUDE.md"
        claude_md.write_text("\\n".join(lines))
        print(f"Knowledge base updated: {claude_md}")
        print(f"Total repositories indexed: {len(repos)}")

    if __name__ == "__main__":
        if len(sys.argv) < 3:
            print("Usage: python3 update_kb.py <github_directory> '<repos_json>'", file=sys.stderr)
            sys.exit(1)
        update_knowledge_base(sys.argv[1], sys.argv[2])
""")
(SCRIPTS_DIR / "update_kb.py").write_text(update_kb_content)

# ── 4. Additional distractor files ─────────────────────────────────────────────

(WORKSPACE / "old_inventory.json").write_text(
    json.dumps({"repos": ["data-pipeline", "auth-service"], "generated": "2024-01-01"}, indent=2)
)

config_dir = WORKSPACE / "config"
config_dir.mkdir(exist_ok=True)
(config_dir / "app_settings.yaml").write_text("debug: false\nlog_level: INFO\n")
(config_dir / "db_config.yaml").write_text("host: localhost\nport: 5432\nname: inventory\n")

logs_dir = WORKSPACE / "logs"
logs_dir.mkdir(exist_ok=True)
(logs_dir / "scan_2024-01-14.log").write_text(
    "2024-01-14 10:00:00 INFO Scanned 2 repositories\n"
    "2024-01-14 10:00:01 INFO data-pipeline: OK\n"
    "2024-01-14 10:00:01 INFO auth-service: OK\n"
)

(WORKSPACE / "SKILL.md").write_text(textwrap.dedent("""\
    ---
    name: github-helper
    description: Local GitHub repository helper for search, clone, sync, and issue/PR inspection workflows.
    ---

    # GitHub Helper

    ## Local Repository Directory
    **Default path**: `/Users/liuchen/Documents/github`

    ## Core Workflows

    ### 1. Initialize or Update Knowledge Base
    1. Scan the directory using `scripts/scan_repos.py`.
    2. Update CLAUDE.md using `scripts/update_kb.py`.

    Example:
    ```bash
    python3 scripts/scan_repos.py /Users/liuchen/Documents/github
    python3 scripts/update_kb.py /Users/liuchen/Documents/github '[{"name":"repo1","path":"/path","summary":"desc"}]'
    ```

    ### 3. Download Repository
    1. Clone to the github directory:
       ```bash
       cd /Users/liuchen/Documents/github
       git clone <repo-url>
       ```
    2. After successful clone, update knowledge base:
       - Run `scripts/scan_repos.py` to get repo info.
       - Run `scripts/update_kb.py` to update CLAUDE.md.

    ## Scripts
    - `scan_repos.py`: Scan local repositories and extract summaries.
    - `update_kb.py`: Update `CLAUDE.md` with repository metadata.
"""))

print("Workspace initialized successfully.")
print(f"GitHub repos dir: {GITHUB_DIR}")
print(f"Scripts dir: {SCRIPTS_DIR}")
print(f"Stale CLAUDE.md written to: {stale_claude}")