import os
import json
import random
import textwrap
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ─── Directory skeleton (mimic a real openclaw install) ───────────────────────
dirs = [
    "scripts",
    "config",
    "references",
    "logs",
    ".openclaw/agency-agents/master-agent",
    ".openclaw/agency-agents/master-agent/memory",
    ".openclaw/agency-agents/master-agent/skills",
    ".openclaw/backups",
    "memory",
    "tmp",
    "docs/internal",
    "docs/archived",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ─── org-context.md (already filled → Phase 0 should be skipped) ─────────────
(workspace / "config/org-context.md").write_text(textwrap.dedent("""\
    # org-context.md — 组织背景预埋信息

    ## 公司信息
    - 公司：DataFlux Technology Co., Ltd.
    - 业务：实时数据管道监控与数据质量治理平台，服务金融和电商客户

    ## 现有 Agent 架构
    - master-agent: 主调度 Agent，统筹所有子 Agent

    ## 其他背景
    - 技术栈：Python, Spark, Kafka, dbt
    """))

# ─── openclaw.json — the live registry ───────────────────────────────────────
openclaw_cfg = {
    "version": "1.4.2",
    "agents": {
        "list": [
            {
                "agentId": "master-agent",
                "workspace": str(workspace / ".openclaw/agency-agents/master-agent"),
                "subagents": {
                    "allowAgents": []
                }
            }
        ]
    },
    "gateway": {
        "port": 7430,
        "logLevel": "info"
    }
}
(workspace / "openclaw.json").write_text(json.dumps(openclaw_cfg, indent=2, ensure_ascii=False))

# ─── Minimal SOUL.md for master-agent (distractor) ───────────────────────────
(workspace / ".openclaw/agency-agents/master-agent/SOUL.md").write_text(textwrap.dedent("""\
    # SOUL.md
    我是 Master，负责统筹协调所有子 Agent 的工作。
    我关注整体效率，确保各 Agent 协同运转。
    """))

(workspace / ".openclaw/agency-agents/master-agent/AGENTS.md").write_text(textwrap.dedent("""\
    # AGENTS.md
    ## 每次对话开始时
    1. 读 SOUL.md
    2. 读今日 memory 文件
    """))

(workspace / ".openclaw/agency-agents/master-agent/MEMORY.md").write_text(textwrap.dedent("""\
    # MEMORY.md
    ## 关于公司
    - 公司：DataFlux Technology Co., Ltd.
    - 业务：实时数据管道监控与数据质量治理平台
    """))

# ─── Distractor files ─────────────────────────────────────────────────────────
(workspace / "logs/gateway-2024-01-10.log").write_text(
    "[INFO] openclaw-gateway started on port 7430\n"
    "[INFO] Loaded agent: master-agent\n"
    "[INFO] Tool registration complete\n"
)

(workspace / "logs/gateway-2024-01-11.log").write_text(
    "[INFO] openclaw-gateway restarted\n"
    "[WARN] Agent data-checker not found in registry\n"
)

(workspace / "docs/internal/agent-naming-convention.md").write_text(textwrap.dedent("""\
    # Agent Naming Convention
    - Human agents: staff-<open_id_prefix>
    - Functional agents: <domain>-<role> (e.g., data-analyst, code-reviewer)
    - All lowercase, hyphens only
    """))

(workspace / "docs/internal/tool-registry.md").write_text(textwrap.dedent("""\
    # Available Tools
    - feishu_get_user
    - feishu_im_user_message
    - feishu_calendar_event
    - db_query_executor
    - pipeline_status_checker
    - alert_dispatcher
    - data_quality_reporter
    - schema_validator
    """))

(workspace / "docs/archived/old-agent-template.md").write_text(textwrap.dedent("""\
    # Old Template (DEPRECATED - do not use)
    This template predates the current workspace system.
    Use scripts/create_workspace.sh instead.
    """))

(workspace / "tmp/scratch.txt").write_text("temp workspace scratch\n")

(workspace / "memory/2024-01-10.md").write_text(textwrap.dedent("""\
    ## 2024-01-10
    - 讨论了数据质量 Agent 的需求
    - 确定需要能校验 schema、跑数据探查、产出质量报告
    - 父 Agent 确定为 master-agent
    """))

(workspace / "memory/2024-01-11.md").write_text(textwrap.dedent("""\
    ## 2024-01-11
    - 数据质量 Agent 将命名为 dq-sentinel
    - 需要工具权限: db_query_executor, pipeline_status_checker, data_quality_reporter, schema_validator
    - 不处理业务逻辑变更，只做检测和报告
    """))

(workspace / "MEMORY.md").write_text(textwrap.dedent("""\
    # MEMORY.md — Master Memory
    ## 组织背景
    - 公司：DataFlux Technology Co., Ltd.
    - 业务：实时数据管道监控与数据质量治理平台
    ## 近期任务
    - 正在规划 dq-sentinel Agent 的创建
    """))

# ─── Mock scripts (these "already exist in workspace" per skill) ──────────────

# create_workspace.sh
(workspace / "scripts/create_workspace.sh").write_text(textwrap.dedent("""\
    #!/usr/bin/env bash
    # Mock implementation of create_workspace.sh
    # Usage: bash scripts/create_workspace.sh <agentId> --type [human|functional]
    set -e

    AGENT_ID="$1"
    TYPE_FLAG=""
    TYPE_VALUE=""

    shift
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --type)
                TYPE_FLAG="--type"
                TYPE_VALUE="$2"
                shift 2
                ;;
            *)
                echo "Unknown argument: $1" >&2
                exit 1
                ;;
        esac
    done

    if [[ -z "$AGENT_ID" ]]; then
        echo "ERROR: agentId required" >&2
        exit 1
    fi

    if [[ "$TYPE_VALUE" != "human" && "$TYPE_VALUE" != "functional" ]]; then
        echo "ERROR: --type must be 'human' or 'functional'" >&2
        exit 1
    fi

    BASE="$HOME/.openclaw/agency-agents/$AGENT_ID"
    mkdir -p "$BASE/memory"

    if [[ "$TYPE_VALUE" == "human" ]]; then
        mkdir -p "$BASE/skills"
        echo "Created workspace for HUMAN agent: $BASE"
        echo "Files to create: IDENTITY.md, SOUL.md (skeleton), AGENTS.md, TOOLS.md, MEMORY.md, HEARTBEAT.md, BOOTSTRAP.md, USER.md"
        echo "Note: BOOTSTRAP.md and USER.md will be partially filled by bootstrap phase."
    else
        echo "Created workspace for FUNCTIONAL agent: $BASE"
        echo "Files to create: IDENTITY.md, SOUL.md (full), AGENTS.md, TOOLS.md, MEMORY.md, HEARTBEAT.md"
        echo "Note: No BOOTSTRAP.md or USER.md needed for functional agents."
    fi

    # Write sentinel file so eval can confirm script was called correctly
    echo "$TYPE_VALUE" > "$BASE/.workspace_type"
    echo "$AGENT_ID" > "$BASE/.agent_id"
    """))

# register_agent.py
(workspace / "scripts/register_agent.py").write_text(textwrap.dedent("""\
    #!/usr/bin/env python3
    \"\"\"Mock register_agent.py — records call args and modifies openclaw.json\"\"\"
    import argparse, json, shutil, sys, datetime
    from pathlib import Path

    def main():
        parser = argparse.ArgumentParser()
        parser.add_argument('--agent-id', required=True)
        parser.add_argument('--workspace', required=True)
        parser.add_argument('--parent-id', required=True)
        parser.add_argument('--also-allow', nargs='+', default=[])
        parser.add_argument('--agent-dir', default=None)
        parser.add_argument('--dry-run', action='store_true')
        args = parser.parse_args()

        cfg_path = Path('/workspace/openclaw.json')
        if not cfg_path.exists():
            print('ERROR: openclaw.json not found', file=sys.stderr)
            sys.exit(1)

        with open(cfg_path) as f:
            cfg = json.load(f)

        # Backup
        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup = Path(f'/workspace/.openclaw/backups/openclaw_{ts}.json')
        backup.parent.mkdir(parents=True, exist_ok=True)

        if args.dry_run:
            print(f'[DRY-RUN] Would register agent {args.agent_id}')
            print(f'  workspace: {args.workspace}')
            print(f'  parent: {args.parent_id}')
            print(f'  also-allow: {args.also_allow}')
            if args.agent_dir:
                print(f'  agent-dir: {args.agent_dir}')
            return

        shutil.copy(cfg_path, backup)
        print(f'Backup created: {backup}')

        # Build new agent entry
        new_agent = {
            "agentId": args.agent_id,
            "workspace": args.workspace,
            "subagents": {"allowAgents": []},
            "alsoAllow": args.also_allow
        }
        if args.agent_dir:
            new_agent["agentDir"] = args.agent_dir

        # Add to agents list
        cfg["agents"]["list"].append(new_agent)

        # Double-bind: add to parent's allowAgents
        parent_found = False
        for agent in cfg["agents"]["list"]:
            if agent["agentId"] == args.parent_id:
                agent["subagents"]["allowAgents"].append(args.agent_id)
                parent_found = True
                break

        if not parent_found:
            print(f'WARNING: parent agent {args.parent_id} not found — skipping double-bind', file=sys.stderr)

        # Validate (mock: always passes)
        print('Running: openclaw config validate')
        print('✅ Config validation passed')

        with open(cfg_path, 'w') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)

        print(f'✅ Agent {args.agent_id} registered successfully')

        # Record call metadata for eval
        call_record = {
            "agent_id": args.agent_id,
            "workspace": args.workspace,
            "parent_id": args.parent_id,
            "also_allow": args.also_allow,
            "agent_dir": args.agent_dir,
            "dry_run": args.dry_run
        }
        record_path = Path('/workspace/tmp/register_call.json')
        with open(record_path, 'w') as f:
            json.dump(call_record, f, indent=2)

        print(f'Call record saved: {record_path}')

    if __name__ == '__main__':
        main()
    """))

# verify_workspace.sh
(workspace / "scripts/verify_workspace.sh").write_text(textwrap.dedent("""\
    #!/usr/bin/env bash
    # Mock verify_workspace.sh
    # Usage: bash scripts/verify_workspace.sh <agentId> --type [human|functional]
    set -e

    AGENT_ID="$1"
    TYPE_VALUE=""

    shift
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --type)
                TYPE_VALUE="$2"
                shift 2
                ;;
            *) shift ;;
        esac
    done

    BASE="$HOME/.openclaw/agency-agents/$AGENT_ID"

    echo "=== Verifying workspace for $AGENT_ID (type: $TYPE_VALUE) ==="

    ERRORS=0
    check_file() {
        local f="$1"
        local name="$2"
        if [[ -f "$BASE/$f" ]] && [[ -s "$BASE/$f" ]]; then
            echo "  ✅ $name"
        else
            echo "  ❌ $name — missing or empty"
            ERRORS=$((ERRORS + 1))
        fi
    }

    check_file "IDENTITY.md" "IDENTITY.md"
    check_file "SOUL.md"     "SOUL.md"
    check_file "AGENTS.md"   "AGENTS.md"
    check_file "TOOLS.md"    "TOOLS.md"
    check_file "MEMORY.md"   "MEMORY.md"
    check_file "HEARTBEAT.md" "HEARTBEAT.md"

    if [[ "$TYPE_VALUE" == "human" ]]; then
        check_file "BOOTSTRAP.md" "BOOTSTRAP.md"
        check_file "USER.md"      "USER.md"
    fi

    if [[ $ERRORS -gt 0 ]]; then
        echo "=== ❌ Verification FAILED ($ERRORS errors) ==="
        exit 1
    fi

    echo "=== ✅ Workspace verification PASSED ==="

    # Record that verify was called with correct type
    echo "$TYPE_VALUE" > "$BASE/.verify_type_used"
    """))

# references (stubs — agent must synthesize from skill instructions)
(workspace / "references/file-formats.md").write_text(textwrap.dedent("""\
    # File Formats Reference
    ## TOOLS.md
    Each tool entry must contain:
    - 用途 (purpose)
    - 什么时候用 (when to use)
    - 什么时候不用 (when NOT to use) — more important than when to use

    Restricted tools must be listed separately with explicit authorization note.

    ## MEMORY.md
    - MEMORY.md = long-term stable knowledge
    - memory/<date>.md = daily event logs
    These must NEVER be conflated.
    """))

(workspace / "references/soul-writing-guide.md").write_text(textwrap.dedent("""\
    # SOUL.md Writing Guide
    ## For Functional Agents
    - Write professional judgment tendencies
    - Write quality standards this agent cares about
    - Write the agent's work obsession
    - Do NOT write communication style or personal preferences
    - Use first-person narrative, not rule sentences
    - No rule-style sentences (e.g., "You must...", "Always do...")
    - Rule sentences belong in AGENTS.md

    ## For Human Agents
    - Write communication style and tone
    - Write personality and personal preferences
    - Leave specific details for BOOTSTRAP phase
    """))

(workspace / "references/evolve-rules.md").write_text(textwrap.dedent("""\
    # Evolve Rules — Memory Growth
    ## 写入 AGENTS.md 的具体段落（逐字复制）

    ### 记忆规则
    ```
    ## 记忆规则
    ### 触发式写入
    - 每次对话结束前检查：有没有新的信息值得记录？
    - 判断标准：这个信息下次还会用到吗？
    - 写入位置：memory/<今日日期>.md

    ### Heartbeat 精炼
    - 每 3 天读最近 memory 文件，提炼稳定知识进 MEMORY.md
    - 过时内容直接删除，不保留
    ```
    """))

(workspace / "references/bootstrap-protocol.md").write_text(textwrap.dedent("""\
    # BOOTSTRAP Protocol
    ## Structure
    1. Execution declaration (run this file when it exists)
    2. Reference declaration (where to find format specs)
    3. Information slot map (what to collect)
    4. Information-to-file mapping (where each answer goes)
    5. Question protocol (first round rules + subsequent rounds + stop condition)
    6. Write execution steps
    7. Completion (send welcome message + delete this file)

    ## First step for employee agents
    Call feishu_get_user to get user's name for personalized opening.

    ## Key principle
    This file is ONLY for human/employee agents. Functional agents do NOT use BOOTSTRAP.md.
    """))

print("Workspace initialized successfully.")
print(f"openclaw.json: {(workspace / 'openclaw.json').read_text()[:200]}...")