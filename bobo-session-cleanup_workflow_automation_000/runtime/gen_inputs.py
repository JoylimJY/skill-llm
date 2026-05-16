#!/usr/bin/env python3
"""
Generate the sandbox workspace for the session-cleanup skill evaluation.
Creates a realistic OpenClaw session directory with orphan files, stale sessions,
protected sessions, and the agent:main:main session.
"""

import os
import json
import random
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta

random.seed(42)

workspace = Path("/workspace")

# ── 1. Directory structure ──────────────────────────────────────────────────
dirs = [
    "skills/session-cleanup/scripts",
    "skills/session-cleanup/references",
    "skills/other-skill/scripts",
    "config",
    "logs",
    "tmp",
    "docs",
    "references",
    ".openclaw/agents/main/sessions",
    ".openclaw/agents/main/meta",
    ".openclaw/config",
    ".openclaw/logs",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── 2. Distractor files ──────────────────────────────────────────────────────
distractors = [
    ("config/app.yaml",          "version: 2\nlog_level: info\nmax_sessions: 100\n"),
    ("config/db.conf",           "[database]\nhost=localhost\nport=5432\n"),
    ("logs/app.log",             "2026-03-01 10:00:00 INFO startup\n2026-03-01 10:01:00 INFO ready\n"),
    ("logs/error.log",           "2026-02-28 09:55:00 ERROR disk full\n"),
    ("docs/architecture.md",     "# Architecture\nOpenClaw uses agent-based sessions.\n"),
    ("docs/changelog.md",        "## v0.2.1\n- Fixed orphan detection\n## v0.2.0\n- Initial release\n"),
    ("tmp/scratch.txt",          "temporary notes\n"),
    ("references/glossary.md",   "# Glossary\nSession: a tracked interaction context\n"),
    ("skills/other-skill/scripts/run.sh", "#!/bin/bash\necho 'other skill'\n"),
    (".openclaw/config/settings.json", json.dumps({"theme": "dark", "language": "zh-CN"}, indent=2) + "\n"),
    (".openclaw/logs/access.log", "2026-03-06 08:00 agent:main:main started\n"),
    (".openclaw/agents/main/meta/profile.json", json.dumps({"agentId": "main", "created": "2025-01-01T00:00:00Z"}, indent=2) + "\n"),
]
for rel_path, content in distractors:
    p = workspace / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

# ── 3. Session data setup ───────────────────────────────────────────────────
sessions_dir = workspace / ".openclaw/agents/main/sessions"
now_utc = datetime.now(timezone.utc)

def ts(hours_ago: float) -> str:
    return (now_utc - timedelta(hours=hours_ago)).isoformat()

def make_jsonl(session_id: str, lines: int = 3) -> str:
    rows = []
    for i in range(lines):
        rows.append(json.dumps({
            "role": "user" if i % 2 == 0 else "assistant",
            "content": f"message {i} from session {session_id}",
            "ts": ts(random.uniform(0.5, 2.0))
        }))
    return "\n".join(rows) + "\n"

# Sessions that will be registered in sessions.json
# Protected: current session (hours_ago < 72) + special flag
registered_sessions = [
    # id,                        hours_ago,  protected,  size_kb
    ("agent:main:main",          0.5,        True,       8),    # NEVER delete
    ("session-alpha-001",        1.0,        True,       12),   # within 72h window → protected
    ("session-beta-002",         48.0,       True,       6),    # within 72h window → protected
    ("session-gamma-003",        73.5,       False,      15),   # stale → delete candidate
    ("session-delta-004",        96.0,       False,      20),   # stale → delete candidate
    ("session-epsilon-005",      120.0,      False,      9),    # stale → delete candidate
    ("session-zeta-006",         71.9,       True,       4),    # just within 72h → protected
]

sessions_json_entries = []
for sid, hours_ago, protected, size_kb in registered_sessions:
    entry = {
        "id": sid,
        "createdAt": ts(hours_ago + random.uniform(0.1, 0.5)),
        "updatedAt": ts(hours_ago),
        "protected": protected,
        "sizeKb": size_kb,
    }
    sessions_json_entries.append(entry)
    # Write .jsonl file
    jsonl_path = sessions_dir / f"{sid}.jsonl"
    # Make stale file sizes realistic
    content = make_jsonl(sid, lines=size_kb // 2 + 1)
    # Pad content to approximate size
    pad = "x" * max(0, size_kb * 1024 - len(content.encode()))
    jsonl_path.write_text(content + ("# pad:" + pad[:100] if pad else ""), encoding="utf-8")

# Write sessions.json
sessions_json_path = workspace / ".openclaw/agents/main/sessions.json"
sessions_json = {
    "schemaVersion": "1.0",
    "agentId": "main",
    "sessions": sessions_json_entries,
}
sessions_json_path.write_text(json.dumps(sessions_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# ── 4. Orphan .jsonl files (on disk but NOT in sessions.json) ───────────────
orphan_sessions = [
    ("orphan-xray-099",   30),   # hours_ago irrelevant for orphans
    ("orphan-yankee-100", 50),
    ("orphan-zulu-101",   80),
]
for oid, hours_ago in orphan_sessions:
    jsonl_path = sessions_dir / f"{oid}.jsonl"
    content = make_jsonl(oid, lines=4)
    jsonl_path.write_text(content, encoding="utf-8")

# ── 5. SKILL.md ──────────────────────────────────────────────────────────────
skill_md = r"""---
name: session-cleanup
description: DEPRECATED: Please use `session-cleanup-pro`. This legacy slug is retained only for compatibility.
user-invocable: true
metadata:
  { "openclaw": { "emoji": "🧹", "requires": { "bins": ["bash", "node"] } }, "version": "0.2.1", "updatedAt": "2026-03-06 20:47 Asia/Shanghai" }
---

# Session Cleanup

清理 OpenClaw 会话目录中的孤儿文件与过期会话，优先安全、可审计。

## 使用方式

先扫描，再确认，再执行：

1. 扫描（只读）
2. 生成清理计划
3. 用户确认
4. 执行清理并回报结果

## 关键文件

- 扫描脚本：`scripts/scan_sessions.sh`
- 清理策略：`references/policy.md`

## 扫描命令（必做）

```bash
./skills/session-cleanup/scripts/scan_sessions.sh scan
```

返回 JSON 包含：
- `orphanFiles`：磁盘存在但 `sessions.json` 未登记的 `.jsonl`
- `staleSessions`：超过 72 小时且非受保护会话
- `protectedSessions`：当前会话 + 72 小时保护窗口内会话

## 执行规则

- 必须先扫描并展示摘要
- 必须询问用户确认后才清理
- 默认不删除受保护会话
- 永不删除 `agent:main:main`

## 清理建议

### A. 先处理孤儿文件（优先）

在用户确认后删除孤儿文件：

```bash
rm ~/.openclaw/agents/main/sessions/<orphan>.jsonl
```

### B. 再处理过期会话（谨慎）

仅在用户明确确认后执行，删除对应 `.jsonl`，并更新 `sessions.json` 去除条目。

## 输出模板

```markdown
🧹 会话清理扫描完成

- 注册会话：X
- 磁盘 jsonl：Y
- 孤儿文件：A
- 过期会话：B
- 受保护会话：C

预计可释放：N MB

是否按上述计划执行清理？
```

## 发布前自检

```bash
# 1) 脚本可执行
./skills/session-cleanup/scripts/scan_sessions.sh scan >/tmp/session-cleanup-report.json

# 2) 输出为有效 JSON
node -e "JSON.parse(require('fs').readFileSync('/tmp/session-cleanup-report.json','utf8')); console.log('OK')"
```
"""
(workspace / "skills/session-cleanup/SKILL.md").write_text(skill_md, encoding="utf-8")

# ── 6. policy.md (referenced in SKILL.md) ────────────────────────────────────
policy_md = """# Cleanup Policy

## Protection Rules
- Sessions updated within the last 72 hours are protected.
- The session `agent:main:main` is PERMANENTLY protected and must NEVER be deleted.
- Sessions with `protected: true` in sessions.json are always protected.

## Orphan Definition
A `.jsonl` file in the sessions directory that has no corresponding entry in `sessions.json`.

## Stale Definition
A registered session whose `updatedAt` timestamp is older than 72 hours AND is not protected.

## Execution Order
1. Remove orphan files first.
2. Remove stale session `.jsonl` files second.
3. Update `sessions.json` to remove entries for deleted stale sessions.
"""
(workspace / "skills/session-cleanup/references/policy.md").write_text(policy_md, encoding="utf-8")

print("✅ Workspace generated successfully.")
print(f"   Sessions dir: {sessions_dir}")
print(f"   Registered sessions: {len(registered_sessions)}")
print(f"   Orphan files: {len(orphan_sessions)}")
print(f"   Stale sessions: {sum(1 for s in registered_sessions if not s[2] and s[1] > 72)}")