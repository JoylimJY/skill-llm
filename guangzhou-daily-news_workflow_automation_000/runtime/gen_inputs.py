import os
import random
from pathlib import Path

random.seed(42)

home = Path("/home/agent")

# Create deeply nested distractor directory structure
dirs = [
    home / ".qclaw" / "skills" / "guangzhou-daily-news" / "scripts",
    home / ".qclaw" / "skills" / "guangzhou-daily-news" / "config",
    home / ".qclaw" / "skills" / "weather-forecast" / "scripts",
    home / ".qclaw" / "skills" / "stock-monitor" / "scripts",
    home / ".qclaw" / "config" / "cron",
    home / ".qclaw" / "logs",
    home / "News" / "archive",
    home / "workspace" / "projects" / "media",
    home / "workspace" / "tmp",
    home / ".local" / "share" / "applications",
]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    home / ".qclaw" / "skills" / "weather-forecast" / "scripts" / "fetch_weather.py":
        "# Weather fetch script\nimport requests\nprint('fetching weather...')\n",
    home / ".qclaw" / "skills" / "stock-monitor" / "scripts" / "monitor.py":
        "# Stock monitor\nimport time\nwhile True:\n    time.sleep(60)\n",
    home / ".qclaw" / "config" / "cron" / "tasks.json":
        '{"tasks": [{"name": "weather", "cron": "0 8 * * *"}, {"name": "news", "cron": "0 9 * * *"}]}\n',
    home / ".qclaw" / "logs" / "skill_runner.log":
        "[2026-03-23 09:00:01] INFO: Running guangzhou-daily-news\n[2026-03-23 09:00:05] ERROR: Connection timeout\n",
    home / "workspace" / "projects" / "media" / "notes.txt":
        "# Media monitoring project\nCheck gz-cmc.com for news updates daily.\n",
    home / "workspace" / "tmp" / "scratch.py":
        "# scratch file\nx = 1\n",
    home / "News" / "archive" / "old_news_2026-03-22.md":
        "# Old news - outdated format\n1. Some old story\n2. Another story\n",
    home / ".qclaw" / "skills" / "guangzhou-daily-news" / "config" / "settings.json":
        '{"version": "1.0.0", "push_enabled": false, "schedule": ["09:00", "18:00"]}\n',
    home / ".local" / "share" / "applications" / "openclaw.desktop":
        "[Desktop Entry]\nName=OpenClaw\nExec=openclaw\n",
    home / "workspace" / "projects" / "media" / "sources.csv":
        "source,url,priority\n广州日报,https://gz-cmc.com,high\n南方日报,https://nfdaily.cn,medium\n",
    home / ".qclaw" / "skills" / "guangzhou-daily-news" / "config" / "legacy_config.yaml":
        "# Legacy config - do not use\nbase_url: http://old.gz-cmc.com\nmax_items: 10\n",
}
for path, content in distractor_files.items():
    path.write_text(content, encoding="utf-8")

# Create a broken/incomplete previous attempt at fetch_news.py as a distractor
broken_script = home / ".qclaw" / "skills" / "guangzhou-daily-news" / "scripts" / "fetch_news.py.bak"
broken_script.write_text(
    """# BROKEN - incomplete attempt
import requests
# TODO: fix URL
BASE_URL = 'https://gz-cmc.com'
# This script is incomplete and does not work
""",
    encoding="utf-8"
)

print("Workspace generated successfully.")