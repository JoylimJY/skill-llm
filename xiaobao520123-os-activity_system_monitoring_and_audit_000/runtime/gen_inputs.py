import os
import random
import stat
from pathlib import Path

random.seed(42)

home = Path.home()

# Create the full OpenClaw workspace structure
skills_scripts_dir = home / ".openclaw" / "workspace" / "skills" / "os-activity" / "scripts"
skills_scripts_dir.mkdir(parents=True, exist_ok=True)

# Create other distractor directories to simulate a real openclaw workspace
distractor_dirs = [
    home / ".openclaw" / "workspace" / "skills" / "weather" / "scripts",
    home / ".openclaw" / "workspace" / "skills" / "calendar" / "scripts",
    home / ".openclaw" / "workspace" / "skills" / "notes" / "scripts",
    home / ".openclaw" / "workspace" / "memory",
    home / ".openclaw" / "workspace" / "logs",
    home / ".openclaw" / "workspace" / "cache",
    home / ".openclaw" / "workspace" / "plugins" / "core",
    home / ".openclaw" / "workspace" / "plugins" / "community",
    home / ".openclaw" / "workspace" / "themes",
    home / ".openclaw" / "workspace" / "backups" / "2024",
]
for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

# Create distractor files
distractor_files = {
    home / ".openclaw" / "openclaw.json": '{"version": "2.1.0", "user": "agent", "theme": "dark", "plugins": ["os-activity", "weather", "notes"]}',
    home / ".openclaw" / "workspace" / "memory" / "context.md": "# Memory\nUser prefers Python. Works on Linux servers.",
    home / ".openclaw" / "workspace" / "logs" / "openclaw.log": "[2026-01-10 09:00:00] OpenClaw started\n[2026-01-10 09:00:01] Loaded 3 skills\n",
    home / ".openclaw" / "workspace" / "skills" / "weather" / "scripts" / "forecast.py": "print('weather forecast')",
    home / ".openclaw" / "workspace" / "skills" / "weather" / "scripts" / "current.py": "print('current weather')",
    home / ".openclaw" / "workspace" / "skills" / "calendar" / "scripts" / "events.py": "print('calendar events')",
    home / ".openclaw" / "workspace" / "skills" / "notes" / "scripts" / "search.py": "print('note search')",
    home / ".openclaw" / "workspace" / "cache" / "osquery_cache.json": '{"cached": true, "stale": true}',
    home / ".openclaw" / "workspace" / "themes" / "dark.json": '{"bg": "#1e1e1e", "fg": "#d4d4d4"}',
    home / ".openclaw" / "workspace" / "backups" / "2024" / "openclaw_backup.tar": "FAKE_BACKUP_DATA",
    home / ".openclaw" / "workspace" / "plugins" / "core" / "manifest.json": '{"core_version": "1.0"}',
    home / ".openclaw" / "workspace" / "plugins" / "community" / "index.json": '{"plugins": []}',
}
for fpath, content in distractor_files.items():
    fpath.write_text(content)

# --- THE ACTUAL SKILL SCRIPTS ---

# install_osquery.py — marks osquery as installed via a flag file
install_script = '''#!/usr/bin/env python3
"""
Installs osquery for use with OpenClaw OS Activity skill.
"""
import os
import sys
from pathlib import Path

flag_file = Path.home() / ".openclaw" / "workspace" / "skills" / "os-activity" / ".osquery_installed"

print("Checking for osquery installation...")
print("Downloading osquery components...")
print("Configuring osquery for OpenClaw integration...")
flag_file.parent.mkdir(parents=True, exist_ok=True)
flag_file.write_text("installed")
print("osquery installed successfully.")
print("You can now use the os-activity skill scripts.")
'''

# processes.py — outputs pipe-delimited running process info (Linux supported)
processes_script = '''#!/usr/bin/env python3
"""
Find running programs using osquery integration.
Supported: macOS, Windows, Linux
"""
import sys
from pathlib import Path

flag_file = Path.home() / ".openclaw" / "workspace" / "skills" / "os-activity" / ".osquery_installed"
if not flag_file.exists():
    print("ERROR: osquery is not installed. Please run install_osquery.py first.", file=sys.stderr)
    sys.exit(1)

import psutil

rows = []
rows.append("PID|Name|Status|CPU Percent|Memory MB")

seen_pids = set()
for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_info']):
    try:
        info = proc.info
        pid = info['pid']
        if pid in seen_pids:
            continue
        seen_pids.add(pid)
        name = info['name'] or 'unknown'
        status = info['status'] or 'unknown'
        cpu = info['cpu_percent'] if info['cpu_percent'] is not None else 0.0
        mem_mb = round(info['memory_info'].rss / (1024 * 1024), 2) if info['memory_info'] else 0.0
        rows.append(f"{pid}|{name}|{status}|{cpu}|{mem_mb}")
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        continue

for row in rows:
    print(row)
'''

# recent_files.py — Linux NOT supported
recent_files_script = '''#!/usr/bin/env python3
"""
Find recently edited files using osquery integration.
Supported: macOS, Windows
NOT supported on Linux.
"""
import sys
import platform

if platform.system() == "Linux":
    print("ERROR: recent_files is not supported on Linux.", file=sys.stderr)
    sys.exit(2)

print("Filename|Path|Last Edited Time")
print("example.txt|/home/user/example.txt|2026-02-22 17:30:43")
'''

# recent_dirs.py — Linux NOT supported
recent_dirs_script = '''#!/usr/bin/env python3
"""
Find recently accessed directories using osquery integration.
Supported: Windows only.
NOT supported on macOS or Linux.
"""
import sys
import platform

if platform.system() in ("Linux", "Darwin"):
    print("ERROR: recent_dirs is not supported on this platform.", file=sys.stderr)
    sys.exit(2)

print("Directory|Last Accessed Time")
'''

# programs.py — Linux NOT supported
programs_script = '''#!/usr/bin/env python3
"""
Find installed programs using osquery integration.
Supported: macOS, Windows.
NOT supported on Linux.
"""
import sys
import platform

if platform.system() == "Linux":
    print("ERROR: programs is not supported on Linux.", file=sys.stderr)
    sys.exit(2)

print("Name|Version|Install Date")
'''

# Write all scripts
script_files = {
    "install_osquery.py": install_script,
    "processes.py": processes_script,
    "recent_files.py": recent_files_script,
    "recent_dirs.py": recent_dirs_script,
    "programs.py": programs_script,
}

for filename, content in script_files.items():
    fpath = skills_scripts_dir / filename
    fpath.write_text(content)
    fpath.chmod(fpath.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# Create SKILL.md at the skill root (as it would exist in a real workspace)
skill_root = home / ".openclaw" / "workspace" / "skills" / "os-activity"
skill_md_content = open("/dev/stdin").read() if False else """---
name: os-activity
description: Personalize your openclaw by learning your operating system activity.
---

# OS Activity - Personalize your OpenClaw by learning how you use your computer.
By leveraging `osquery` tool, add additional information telling OpenClaw about your activity on the computer, such as recent edited files, program running, etc.

# Installation
If you have not installed `osquery`, please run the following command to install it:
```bash
python ~/.openclaw/workspace/skills/os-activity/scripts/install_osquery.py
```

# Quick Usage
Find recently edited files:
```bash
python ~/.openclaw/workspace/skills/os-activity/scripts/recent_files.py
```

# Example Output
```markdown
Filename|Path|Last Edited Time
memory|C:\\Users\\steve\\.openclaw\\workspace\\memory|2026-02-22 17:30:43
os-activity|C:\\Users\\steve\\.openclaw\\workspace\\os-activity|2026-02-22 17:29:10
openclaw.json|C:\\Users\\steve\\.openclaw\\openclaw.json|2026-02-22 17:10:05
```

# More commands
## 1. Find recently edited files
### macOS
```bash
python ~/.openclaw/workspace/skills/os-activity/scripts/recent_files.py
```
### Windows
```powershell
python $Env:USERPROFILE\\.openclaw\\workspace\\skills\\os-activity\\scripts\\recent_files.py
```
### Linux
* Not supported
## 2. Find recently accessed directories
### macOS
* Not supported
### Windows
```powershell
python $Env:USERPROFILE\\.openclaw\\workspace\\skills\\os-activity\\scripts\\recent_dirs.py
```
### Linux
* Not supported
## 3. Find installed programs
### macOS
```bash
python ~/.openclaw/workspace/skills/os-activity/scripts/programs.py
```
### Windows
```powershell
python $Env:USERPROFILE\\.openclaw\\workspace\\skills\\os-activity\\scripts\\programs.py
```
### Linux
* Not supported
## 4. Find running programs
### macOS
```bash
python ~/.openclaw/workspace/skills/os-activity/scripts/processes.py
```
### Windows
```powershell
python $Env:USERPROFILE\\.openclaw\\workspace\\skills\\os-activity\\scripts\\processes.py
```
### Linux
```bash
python ~/.openclaw/workspace/skills/os-activity/scripts/processes.py
```
"""
(skill_root / "SKILL.md").write_text(skill_md_content)

print("Workspace initialized successfully.")
print(f"Skill scripts at: {skills_scripts_dir}")