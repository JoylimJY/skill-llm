import os
import stat
import random
import datetime
from pathlib import Path

random.seed(42)

# ── Base workspace ──────────────────────────────────────────────────────────
workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── Simulate the OpenClaw installation tree ─────────────────────────────────
openclaw_root = Path.home() / ".openclaw" / "workspace"
agents_dir    = openclaw_root / "agents"
skills_dir    = openclaw_root / "skills"
agents_dir.mkdir(parents=True, exist_ok=True)
skills_dir.mkdir(parents=True, exist_ok=True)

# ── Pre-existing skills (referenced in the task) ────────────────────────────
existing_skills = [
    "etl-monitor",
    "alert-router",
    "pipeline-health",
    "data-quality-check",
    "slack-notifier",
]

for skill_name in existing_skills:
    skill_path = skills_dir / skill_name
    skill_path.mkdir(exist_ok=True)
    # Each skill has a SKILL.md
    skill_md = skill_path / "SKILL.md"
    skill_md.write_text(f"""---
name: {skill_name}
description: Skill for {skill_name.replace('-', ' ')}
version: 1.0.0
author: platform-team
created_at: 2025-01-10
execution:
  type: shell
  command: ./tools/{skill_name}.sh
  arguments: "$@"
---

## 使用说明
This skill handles {skill_name.replace('-', ' ')} operations.
""", encoding="utf-8")

# ── Pre-existing agent (distractor: different name, different structure) ────
old_agent = agents_dir / "legacy-ops-agent"
old_agent.mkdir(exist_ok=True)
(old_agent / "SOUL.md").write_text("""---
name: legacy-ops-agent
description: Old operations agent
created_at: 2024-06-01
---

## Duties
- Handle legacy systems
""", encoding="utf-8")
(old_agent / "README.md").write_text("# Legacy Ops Agent\nDo not use.\n", encoding="utf-8")

# ── Distractor files in workspace to raise difficulty ───────────────────────
distractors = [
    ("config/openclaw.toml",         "[gateway]\nport = 8080\nlog_level = info\n"),
    ("config/db.yaml",               "host: localhost\nport: 5432\nname: openclaw\n"),
    ("logs/gateway.log",             "2026-03-17 00:01:22 INFO  Gateway started\n2026-03-17 00:01:23 INFO  Loaded 3 agents\n"),
    ("logs/etl-monitor.log",         "2026-03-17 02:00:00 ERROR Pipeline 'sales-etl' failed: timeout\n"),
    ("scripts/deploy.sh",            "#!/bin/bash\necho 'deploying...'\n"),
    ("scripts/health-check.sh",      "#!/bin/bash\ncurl -s http://localhost:8080/health\n"),
    ("docs/architecture.md",         "# Architecture\nOpenClaw uses an agent-skill model.\n"),
    ("docs/faq.md",                  "# FAQ\nQ: How do I restart the gateway?\nA: Run `openclaw gateway restart`\n"),
    ("tmp/scratch.txt",              "pipeline-watcher candidate names:\n- etl-guardian\n- data-watcher-agent\n- pipeline-monitor\n"),
    ("tmp/old-soul-draft.md",        "Draft SOUL file — incomplete, DO NOT USE\nname: pipeline-watcher\n"),
    ("notes/team-notes.txt",         "Meeting notes 2026-03-16:\n- Need new agent for ETL monitoring\n- Skills: etl-monitor, alert-router, pipeline-health\n"),
    ("notes/requirements.txt",       "Agent must:\n1. Monitor daily ETL jobs\n2. Route alerts via Slack\n3. Check data quality hourly\n4. Auto-recover stalled pipelines\n5. Send summary reports at 06:00\n"),
]

for rel_path, content in distractors:
    full_path = workspace / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")

# ── tools/create-agent.sh  ── the real script from SKILL.md ─────────────────
tools_dir = workspace / "tools"
tools_dir.mkdir(exist_ok=True)

create_agent_sh = tools_dir / "create-agent.sh"
create_agent_sh.write_text(r"""#!/bin/bash
# create-agent.sh  – OpenClaw agent scaffolder
# Usage: create-agent.sh <agent_name> <description> <duties_csv> <skills_csv> <run_rules>

set -euo pipefail

AGENT_NAME="${1:-}"
DESCRIPTION="${2:-}"
DUTIES_CSV="${3:-}"
SKILLS_CSV="${4:-}"
RUN_RULES="${5:-}"

if [[ -z "$AGENT_NAME" ]]; then
    echo "Usage: $0 <agent_name> <description> <duties_csv> <skills_csv> <run_rules>" >&2
    exit 1
fi

OPENCLAW_HOME="${HOME}/.openclaw/workspace"
AGENT_DIR="${OPENCLAW_HOME}/agents/${AGENT_NAME}"
SKILLS_DIR="${OPENCLAW_HOME}/skills"

mkdir -p "${AGENT_DIR}/skills"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Build bullet points for duties
DUTIES_MD=""
IFS=',' read -ra DUTIES <<< "$DUTIES_CSV"
for duty in "${DUTIES[@]}"; do
    duty=$(echo "$duty" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    DUTIES_MD+="- ${duty}"$'\n'
done

# Build skill list
SKILLS_MD=""
IFS=',' read -ra SKILLS <<< "$SKILLS_CSV"
for skill in "${SKILLS[@]}"; do
    skill=$(echo "$skill" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    SKILLS_MD+="- ${skill}"$'\n'
    # Create symlink if skill directory exists
    if [[ -d "${SKILLS_DIR}/${skill}" ]]; then
        ln -sfn "${SKILLS_DIR}/${skill}" "${AGENT_DIR}/skills/${skill}"
    fi
done

cat > "${AGENT_DIR}/SOUL.md" <<SOUL
---
name: ${AGENT_NAME}
description: ${DESCRIPTION}
created_at: ${TIMESTAMP}
---

## 职责
${DUTIES_MD}
## 可用 Skill
${SKILLS_MD}
## 运行规则
${RUN_RULES}

## 使用示例
@${AGENT_NAME} [你的指令]
SOUL

cat > "${AGENT_DIR}/README.md" <<README
# ${AGENT_NAME}

${DESCRIPTION}

## 使用方式
\`\`\`
@${AGENT_NAME} [你的指令]
\`\`\`

## 关联 Skill
${SKILLS_MD}

请执行 \`openclaw gateway restart\` 使新 Agent 生效。
README

echo "✅ Agent \"${AGENT_NAME}\" 创建成功！"
echo "配置文件：${AGENT_DIR}/SOUL.md"
echo "关联 Skill：${SKILLS_CSV}"
echo "使用方式：@${AGENT_NAME} [你的指令]"
echo "请执行 openclaw gateway restart 使新 Agent 生效。"
""", encoding="utf-8")

create_agent_sh.chmod(create_agent_sh.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

print("Workspace generated successfully.")
print(f"Skills available: {existing_skills}")
print(f"Agents dir: {agents_dir}")
print(f"Workspace: {workspace}")