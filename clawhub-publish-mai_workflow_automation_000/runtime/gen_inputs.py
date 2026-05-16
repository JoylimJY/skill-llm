import os
import random

random.seed(42)

BASE = "/workspace"

# --- Directory structure ---
dirs = [
    "MAIBOT/skills/notion-sync",
    "MAIBOT/skills/obsidian-daily",
    "MAIBOT/skills/obsidian-daily/references",
    "MAIBOT/skills/gmail-summarize",
    "MAIBOT/skills/gmail-summarize/references",
    "MAIBOT/skills/notion-sync/references",
    "MAIBOT/memory",
    "MAIBOT/config",
    "MAIBOT/logs",
    "MAIBOT/scripts",
    "MAIBOT/tmp",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# --- Distractor files ---
distractors = {
    "MAIBOT/memory/marketplace-strategy.md": """# Marketplace Strategy

## ClawHub Published Skills

| Slug | Name | Version | Date |
|------|------|---------|------|
| gmail-summarize | Gmail Summarizer | 1.0.0 | 2024-01-10 |
""",
    "MAIBOT/config/settings.json": '{"user": "jini92", "theme": "dark", "autoSync": true}',
    "MAIBOT/logs/publish.log": "2024-01-10 10:23:11 INFO Published gmail-summarize v1.0.0\n",
    "MAIBOT/scripts/sync.ps1": "# Sync script\nGet-ChildItem C:\\MAIBOT\\skills\n",
    "MAIBOT/tmp/draft_notes.txt": "TODO: clean up obsidian skill before publish\n",
    "MAIBOT/skills/gmail-summarize/SKILL.md": """---
name: gmail-summarize
description: Summarize Gmail inbox threads using AI.
---

# Gmail Summarize

Fetches and summarizes email threads from Gmail using IMAP.
""",
    "MAIBOT/skills/gmail-summarize/references/setup.md": "# Setup\n\nConfigure IMAP credentials in config.\n",
    "MAIBOT/skills/notion-sync/SKILL.md": """---
name: notion-sync
description: Sync Notion pages to local markdown vault.
---

# Notion Sync

Pulls pages from Notion API and writes to ~/vault/notion/.
""",
    "MAIBOT/skills/notion-sync/references/api-notes.md": "# API Notes\n\nUse Notion integration token.\n",
    "MAIBOT/skills/obsidian-daily/references/checklist.md": "# Daily Note Checklist\n\n- Title formatted as YYYY-MM-DD\n- Tags present\n",
}
for path, content in distractors.items():
    full = os.path.join(BASE, path)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)

# --- THE PROBLEM: messy, Korean + personal-path SKILL.md for obsidian-daily ---
# This skill has:
#   1. Korean text in description and body
#   2. Personal path C:\Users\jini9 and JINI_SYNC references
#   3. Internal account name "jini9" referenced
# The agent must sanitize, translate, bump version (1.1.0 for translation fix), and publish.
# NOTE: This is the FIRST publish (no existing version record in marketplace-strategy.md)

messy_skill_md = """---
name: obsidian-daily
description: Obsidian 데일리 노트를 자동으로 생성하고 관리합니다.
---

# 옵시디언 데일리 노트 자동화

이 스킬은 매일 아침 옵시디언 데일리 노트를 자동으로 생성합니다.

## 사전 요구사항

- Obsidian 설치됨
- 볼트 경로: `C:\\Users\\jini9\\Documents\\JINI_SYNC\\vault`
- 계정: jini9@maibot.internal

## 사용 방법

1. `C:\\Users\\jini9\\Documents\\JINI_SYNC\\vault\\daily` 폴더를 확인합니다.
2. 템플릿 파일을 `C:\\Users\\jini9\\AppData\\obsidian\\templates\\daily.md`에서 복사합니다.
3. 날짜 형식은 `YYYY-MM-DD` 입니다.

## 설정

볼트 경로를 `config.json`의 `vaultPath` 필드에 지정하세요.
내부 계정(jini9)의 API 토큰은 `JINI_SYNC_TOKEN` 환경 변수에 저장됩니다.

## 주의사항

- JINI_SYNC 서버가 실행 중이어야 합니다.
- jini9 계정 권한이 필요합니다.
"""

skill_path = os.path.join(BASE, "MAIBOT/skills/obsidian-daily/SKILL.md")
with open(skill_path, "w", encoding="utf-8") as f:
    f.write(messy_skill_md)

print("Workspace generated successfully.")
print("Problem file: MAIBOT/skills/obsidian-daily/SKILL.md")