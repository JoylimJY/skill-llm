import os
import stat
import textwrap
from pathlib import Path

# --- Deterministic workspace setup ---
WORKSPACE = Path("/workspace")
HOME = Path("/root")

# ---- Create realistic distractor directory tree ----
distractor_dirs = [
    WORKSPACE / "projects" / "alpha" / "src",
    WORKSPACE / "projects" / "alpha" / "tests",
    WORKSPACE / "projects" / "beta" / "docs",
    WORKSPACE / "logs" / "2024" / "january",
    WORKSPACE / "logs" / "2024" / "february",
    WORKSPACE / "config" / "envs",
    WORKSPACE / "config" / "secrets",
    WORKSPACE / "data" / "raw",
    WORKSPACE / "data" / "processed",
    WORKSPACE / "tmp" / "cache",
]
for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    WORKSPACE / "projects" / "alpha" / "src" / "main.py": "# main application entry\nprint('hello')\n",
    WORKSPACE / "projects" / "alpha" / "src" / "utils.py": "def helper(): pass\n",
    WORKSPACE / "projects" / "alpha" / "tests" / "test_main.py": "import pytest\ndef test_dummy(): assert True\n",
    WORKSPACE / "projects" / "beta" / "docs" / "architecture.md": "# Architecture\nThis project uses microservices.\n",
    WORKSPACE / "logs" / "2024" / "january" / "app.log": "[INFO] 2024-01-01 system started\n[ERROR] 2024-01-05 connection refused\n",
    WORKSPACE / "logs" / "2024" / "february" / "app.log": "[INFO] 2024-02-01 system started\n",
    WORKSPACE / "config" / "envs" / "dev.env": "DB_HOST=localhost\nDB_PORT=5432\n",
    WORKSPACE / "config" / "envs" / "prod.env": "DB_HOST=prod-db\nDB_PORT=5432\n",
    WORKSPACE / "config" / "secrets" / ".gitignore": "*.key\n*.pem\n",
    WORKSPACE / "data" / "raw" / "dataset_2024.csv": "id,value\n1,100\n2,200\n3,300\n",
    WORKSPACE / "data" / "processed" / "summary.json": '{"total": 600, "count": 3}\n',
    WORKSPACE / "tmp" / "cache" / "session.tmp": "session_id=abc123\n",
}
for fpath, content in distractor_files.items():
    fpath.write_text(content)

# ---- Create the skill scripts directory structure ----
skill_dir = HOME / ".agents" / "skills" / "notes-skill" / "scripts"
skill_dir.mkdir(parents=True, exist_ok=True)

# ---- Write init.py ----
init_py = skill_dir / "init.py"
init_py.write_text(textwrap.dedent("""\
    #!/usr/bin/env python3
    \"\"\"Initialize the notes database.\"\"\"
    import sqlite3
    from pathlib import Path

    DB_DIR = Path.home() / ".openclaw" / "workspace" / "notes"
    DB_PATH = DB_DIR / "notes.db"
    BACKUP_DIR = DB_DIR / "backups"

    def init():
        DB_DIR.mkdir(parents=True, exist_ok=True)
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        cur.executescript(\"\"\"
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                archived INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT (datetime('now', 'localtime'))
            );
            CREATE INDEX IF NOT EXISTS idx_notes_created ON notes(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_notes_archived ON notes(archived);
        \"\"\")
        conn.commit()
        conn.close()
        print(f"Initialized notes DB at {DB_PATH}")

    if __name__ == "__main__":
        init()
"""))

# ---- Write backup.py ----
backup_py = skill_dir / "backup.py"
backup_py.write_text(textwrap.dedent("""\
    #!/usr/bin/env python3
    \"\"\"Backup the notes database, keeping N most recent backups.\"\"\"
    import sys
    import shutil
    from pathlib import Path
    from datetime import datetime

    DB_DIR = Path.home() / ".openclaw" / "workspace" / "notes"
    DB_PATH = DB_DIR / "notes.db"
    BACKUP_DIR = DB_DIR / "backups"

    def backup(keep=7):
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        if not DB_PATH.exists():
            print("ERROR: notes.db not found. Run init.py first.", file=sys.stderr)
            sys.exit(1)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = BACKUP_DIR / f"notes_{timestamp}.db"
        shutil.copy2(str(DB_PATH), str(dest))
        print(f"Backup created: {dest}")
        # Prune old backups
        backups = sorted(BACKUP_DIR.glob("notes_*.db"), key=lambda p: p.stat().st_mtime)
        while len(backups) > keep:
            oldest = backups.pop(0)
            oldest.unlink()
            print(f"Removed old backup: {oldest}")
        print(f"Backup complete. Keeping {keep} most recent backups.")

    if __name__ == "__main__":
        keep = int(sys.argv[1]) if len(sys.argv) > 1 else 7
        backup(keep)
"""))

# Make scripts executable
init_py.chmod(init_py.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP)
backup_py.chmod(backup_py.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP)

# ---- Create the task instruction file for the agent ----
# This is the "messy raw notes" the agent must process
raw_notes_file = WORKSPACE / "raw_notes_inbox.txt"
raw_notes_file.write_text(textwrap.dedent("""\
    NOTE 1:
    今天研究了radom forest算法 发现特征重要性排名里面 age字段排在最高 但是模型在测试集上accuarcy只有0.62感觉欠拟合了 可能要加特征或者调参

    NOTE 2:
    组会上讨论了新数据集采集方案。计划下周开始采集 样本量目标1000个 每个样本需要记录时间地点天气温度湿度五个维度

    NOTE 3:
    跑实验时候发现cuda out of memeory报错 解决方法是把batch_size从128降到32 然后用梯度累积gradients accumlation steps=4来等效大batch

    ARCHIVE THESE IDs: 2, 4

    NOTE 4:
    python虚拟环境踩坑：用conda create -n myenv python=3.9之后pip install的包有时候会装到全局环境而不是虚拟环境里面 原因是PATH没更新 要先conda activate myenv再装

    BACKUP RETENTION: 3
"""))

print("Workspace setup complete.")
print(f"Skill scripts created at: {skill_dir}")
print(f"Raw notes inbox: {raw_notes_file}")