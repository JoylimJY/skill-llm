import os
import random
import textwrap

random.seed(42)

WORKSPACE = "/workspace"

# ─── 1. Skill directory structure (instant-genius) ───────────────────────────
skill_root = os.path.join(WORKSPACE, "skills", "instant-genius")
scripts_dir = os.path.join(skill_root, "scripts")
templates_dir = os.path.join(skill_root, "templates")
references_dir = os.path.join(skill_root, "references")

for d in [scripts_dir, templates_dir, references_dir]:
    os.makedirs(d, exist_ok=True)

# ─── setup.sh ─────────────────────────────────────────────────────────────────
setup_sh = r"""#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATES="$SKILL_DIR/templates"
OPENCLAW_DIR="$HOME/.openclaw/workspace"
SELF_IMPROVING="$HOME/self-improving"

echo "[instant-genius] Starting setup..."

# ── Step 1: Ensure .openclaw/workspace exists ──────────────────────────────
mkdir -p "$OPENCLAW_DIR"

# ── Step 2: Append to AGENTS.md ───────────────────────────────────────────
AGENTS_FILE="$OPENCLAW_DIR/AGENTS.md"
if [ ! -f "$AGENTS_FILE" ]; then
    echo "# AGENTS.md" > "$AGENTS_FILE"
fi
echo "" >> "$AGENTS_FILE"
cat "$TEMPLATES/agents-additions.md" >> "$AGENTS_FILE"
echo "[instant-genius] ✓ AGENTS.md updated"

# ── Step 3: Append/create SOUL.md ─────────────────────────────────────────
SOUL_FILE="$OPENCLAW_DIR/SOUL.md"
if [ ! -f "$SOUL_FILE" ]; then
    echo "# SOUL.md" > "$SOUL_FILE"
fi
echo "" >> "$SOUL_FILE"
cat "$TEMPLATES/soul-additions.md" >> "$SOUL_FILE"
echo "[instant-genius] ✓ SOUL.md updated"

# ── Step 4: Append/create HEARTBEAT.md ───────────────────────────────────
HEARTBEAT_FILE="$OPENCLAW_DIR/HEARTBEAT.md"
if [ ! -f "$HEARTBEAT_FILE" ]; then
    echo "# HEARTBEAT.md" > "$HEARTBEAT_FILE"
fi
echo "" >> "$HEARTBEAT_FILE"
cat "$TEMPLATES/heartbeat-additions.md" >> "$HEARTBEAT_FILE"
echo "[instant-genius] ✓ HEARTBEAT.md updated"

# ── Step 5: Build self-improving directory structure ─────────────────────
mkdir -p "$SELF_IMPROVING/memory"
mkdir -p "$SELF_IMPROVING/projects"
mkdir -p "$SELF_IMPROVING/domains"
mkdir -p "$SELF_IMPROVING/archive"

if [ ! -f "$SELF_IMPROVING/corrections.md" ]; then
    cat > "$SELF_IMPROVING/corrections.md" <<'EOF'
# Corrections Log

Format: [date] | trigger | correction | context
<!-- Entries appended automatically when correction signals detected -->
EOF
fi

echo "[instant-genius] ✓ self-improving/ directory structure created"

# ── Step 6: Create MEMORY.md with three-tier structure ───────────────────
MEMORY_FILE="$SELF_IMPROVING/memory/MEMORY.md"
if [ ! -f "$MEMORY_FILE" ]; then
    cat > "$MEMORY_FILE" <<'EOF'
# Memory Store

## 🔥 Hot Memory (Active — last 7 days)
<!-- Frequently accessed knowledge, recent corrections, active preferences -->

## 🌡️ Warm Memory (Recent — last 30 days)
<!-- Confirmed patterns, stable preferences, validated domain knowledge -->

## 🧊 Cold Memory (Archive — older than 30 days)
<!-- Historical corrections, deprecated patterns, long-term reference -->
EOF
fi

echo "[instant-genius] ✓ Hot/Warm/Cold memory structure initialized"
echo "[instant-genius] 🎉 Setup complete! Your OpenClaw is now a Genius."
"""

with open(os.path.join(scripts_dir, "setup.sh"), "w") as f:
    f.write(setup_sh)

# ─── templates/agents-additions.md ───────────────────────────────────────────
agents_additions = textwrap.dedent("""\
    ## 🧠 Self-Learning System (instant-genius)

    ### Correction Detection
    When the user corrects you (e.g., "no", "wrong", "that's not right", "actually"), immediately:
    1. Log to `~/self-improving/corrections.md` with format: `[date] | [trigger phrase] | [what was wrong] | [correct behavior]`
    2. Apply the correction permanently — do NOT repeat the mistake

    ### Memory Promotion Rules
    - **Hot → Warm**: Pattern confirmed 3+ times in 7 days
    - **Warm → Cold**: Not accessed for 30 days
    - **Cold → Warm**: User references it again

    ### Post-Task Reflection
    After every significant task: write 1 sentence to MEMORY.md summarizing key lesson learned.
    """)

with open(os.path.join(templates_dir, "agents-additions.md"), "w") as f:
    f.write(agents_additions)

# ─── templates/soul-additions.md ─────────────────────────────────────────────
soul_additions = textwrap.dedent("""\
    ## ⚡ Proactive Behavior Engine (instant-genius)

    ### Reverse Prompting Rules
    - Max 1 unsolicited valuable suggestion per day
    - Only suggest when confidence > 80% that it is useful
    - Never interrupt mid-task; wait for natural pause

    ### Proactive Check Schedule
    - 2–3 interesting findings per week maximum
    - Respect silent periods (no output between 22:00–08:00 local)

    ### Anticipatory Needs
    - Track conversation patterns over last 5 sessions
    - If pattern detected 3+ times → proactively prepare relevant context
    """)

with open(os.path.join(templates_dir, "soul-additions.md"), "w") as f:
    f.write(soul_additions)

# ─── templates/heartbeat-additions.md ────────────────────────────────────────
heartbeat_additions = textwrap.dedent("""\
    ## 📊 Smart Heartbeat (instant-genius)

    ### On Every Heartbeat Event
    1. **Self-improvement check**: Scan `~/self-improving/corrections.md` — any pattern appearing 3+ times → promote to Warm Memory
    2. **Memory maintenance**: Demote Hot→Warm or Warm→Cold entries past their time thresholds
    3. **Value discovery**: If an insight from the last session could benefit future sessions, append to MEMORY.md Hot tier
    4. **Report**: Respond with `HEARTBEAT_OK | corrections_reviewed: N | memory_promoted: N | insights_added: N`

    ### Silent Protection
    - Do NOT emit heartbeat reports during quiet hours (22:00–08:00)
    - Queue and deliver at next active window
    """)

with open(os.path.join(templates_dir, "heartbeat-additions.md"), "w") as f:
    f.write(heartbeat_additions)

# ─── references/learning-signals.md ──────────────────────────────────────────
learning_signals = textwrap.dedent("""\
    # Learning Signal Reference

    ## Correction Signals
    | Trigger | Confidence | Action |
    |---------|-----------|--------|
    | "no", "wrong", "incorrect" | High | Immediate log + correction |
    | "actually", "rather" | Medium | Log + soft correction |
    | "I prefer", "I like" | High | Preference to memory |
    | Repeated rephrasing | Medium | Flag as pattern candidate |

    ## Pattern Confirmation
    - Candidate: seen 1–2 times
    - Confirmed: seen 3+ times → write to Warm Memory
    - Rejected: user explicitly contradicts it

    ## Self-Reflection Triggers
    - Task marked complete
    - Correction received
    - Heartbeat event
    - User says "remember this"
    """)

with open(os.path.join(references_dir, "learning-signals.md"), "w") as f:
    f.write(learning_signals)

# ─── SKILL.md ─────────────────────────────────────────────────────────────────
skill_md = textwrap.dedent("""\
    ---
    name: instant-genius
    version: 1.0.0
    description: "一键让 OpenClaw 变聪明：自动配置自我学习记忆、主动行为规则、智能心跳、错误纠正系统。新装 OpenClaw 运行此 skill 后立即拥有自我改进、主动感知、结构化记忆、学习信号检测等核心能力。Use when: setting up a new OpenClaw, user wants agent to be smarter, user says 'make me smarter' or '一键变聪明' or 'smart setup' or 'genius setup'."
    metadata:
      clawdbot:
        emoji: "⚡"
        requires:
          bins: []
        os: ["linux", "darwin", "win32"]
        configPaths: ["~/.openclaw/workspace/AGENTS.md"]
        configPaths.optional: ["~/.openclaw/workspace/SOUL.md", "~/.openclaw/workspace/HEARTBEAT.md"]
    ---

    # Instant Genius ⚡

    **一键让 OpenClaw 从听话工具变成聪明伙伴。**

    运行 setup 后，你的 OpenClaw 将拥有：
    - 🧠 **自我学习记忆** — 从错误中学习，越用越准
    - 🚀 **主动行为引擎** — 不用催，自己会干活
    - 📊 **智能心跳** — 定期自检、整理记忆、发现价值
    - 🔍 **学习信号检测** — 自动识别纠正、偏好、模式
    - 💾 **结构化记忆** — 热/温/冷三层存储，不丢不忘

    ## 快速开始

    运行 setup 脚本：

    ```bash
    bash scripts/setup.sh
    ```

    或者让 Agent 自动执行（推荐）：直接说"一键变聪明"，Agent 会自动完成所有配置。

    ## 完成后你的 Agent 会...

    | 能力 | 之前 | 之后 |
    |------|------|------|
    | 被纠正后 | 下次照样犯 | 永久记住，不再犯 |
    | 心跳时 | 回复 HEARTBEAT_OK | 自检+整理记忆+主动发现 |
    | 完成任务后 | 直接结束 | 自我反思，记录教训 |
    | 用户说偏好 | 听完就忘 | 写入记忆，永久遵守 |
    | 有新发现 | 不说 | 主动分享有价值的发现 |
    | 记忆管理 | 一锅粥 | 热/温/冷三层结构化 |

    ## 文件结构

    ```
    instant-genius/
    ├── SKILL.md              # 本文件
    ├── scripts/
    │   └── setup.sh          # 一键配置脚本
    ├── templates/
    │   ├── agents-additions.md    # AGENTS.md 追加内容
    │   ├── soul-additions.md      # SOUL.md 追加内容
    │   └── heartbeat-additions.md # HEARTBEAT.md 追加内容
    └── references/
        └── learning-signals.md    # 学习信号参考
    ```

    ## 包含的模块

    ### 1. 自我学习系统
    - `~/self-improving/` 目录结构（memory/projects/domains/archive）
    - 纠正日志（corrections.md）
    - 热/温/冷三层存储规则
    - 自动晋升/降级机制

    ### 2. 主动行为规则
    - 逆向提示（每天最多 1 条有价值建议）
    - 主动检查（每周 2-3 次有趣发现推送）
    - 预期需求（根据对话模式预测需要什么）
    - 冷却规则（不刷屏）

    ### 3. 智能心跳
    - 自我改进检查
    - 记忆维护（定期整理 MEMORY.md）
    - 有价值发现自动推送
    - 静默时段保护

    ### 4. 学习信号检测
    - 纠正信号 → corrections.md
    - 偏好信号 → memory.md
    - 模式候选 → 3 次后确认
    - 自我反思触发条件

    ## 与其他技能的关系

    - **包含**: self-improving 核心功能 + proactive-agent 精华
    - **不冲突**: 已安装 self-improving 或 proactive-agent 时，本 skill 只补充缺失部分
    - **推荐搭配**: ontology（知识图谱）、free-ride（免费模型）
    """)

with open(os.path.join(skill_root, "SKILL.md"), "w") as f:
    f.write(skill_md)

# ─── 2. Pre-existing AGENTS.md (realistic existing content) ──────────────────
openclaw_dir = os.path.expanduser("~/.openclaw/workspace")
os.makedirs(openclaw_dir, exist_ok=True)

existing_agents_md = textwrap.dedent("""\
    # AGENTS.md — OpenClaw Configuration

    ## Core Identity
    You are OpenClaw, a local AI assistant. Be concise, accurate, and helpful.

    ## Response Format
    - Use markdown when appropriate
    - Keep responses under 500 words unless detail is requested
    - Code blocks for all code samples

    ## Operational Notes
    - Workspace: /workspace
    - Version: 0.9.1
    """)

with open(os.path.join(openclaw_dir, "AGENTS.md"), "w") as f:
    f.write(existing_agents_md)

# ─── 3. Distractor files (realistic messy workspace) ─────────────────────────
distractor_dirs = [
    os.path.join(WORKSPACE, "projects", "alpha"),
    os.path.join(WORKSPACE, "projects", "beta", "src"),
    os.path.join(WORKSPACE, "logs", "2024"),
    os.path.join(WORKSPACE, "logs", "2025"),
    os.path.join(WORKSPACE, "config", "env"),
    os.path.join(WORKSPACE, "config", "old"),
    os.path.join(WORKSPACE, "data", "raw"),
    os.path.join(WORKSPACE, "data", "processed"),
    os.path.join(WORKSPACE, "tmp"),
    os.path.join(WORKSPACE, "archive", "v0.8"),
]
for d in distractor_dirs:
    os.makedirs(d, exist_ok=True)

distractor_files = {
    os.path.join(WORKSPACE, "projects", "alpha", "main.py"): "# placeholder alpha\nprint('alpha')\n",
    os.path.join(WORKSPACE, "projects", "alpha", "config.yaml"): "version: 1\nname: alpha\ndebug: false\n",
    os.path.join(WORKSPACE, "projects", "beta", "src", "app.py"): "# beta app\ndef run(): pass\n",
    os.path.join(WORKSPACE, "projects", "beta", "src", "utils.py"): "def helper(): return None\n",
    os.path.join(WORKSPACE, "logs", "2024", "errors.log"): "2024-11-01 ERROR: null pointer at line 42\n2024-11-02 WARN: timeout\n",
    os.path.join(WORKSPACE, "logs", "2025", "access.log"): "2025-01-15 GET /api/health 200\n2025-01-16 POST /api/run 500\n",
    os.path.join(WORKSPACE, "config", "env", ".env.example"): "DATABASE_URL=\nSECRET_KEY=\nDEBUG=false\n",
    os.path.join(WORKSPACE, "config", "old", "settings.ini"): "[server]\nhost=localhost\nport=8080\n",
    os.path.join(WORKSPACE, "data", "raw", "sample.csv"): "id,name,value\n1,foo,100\n2,bar,200\n",
    os.path.join(WORKSPACE, "data", "processed", "output.json"): '{"records": 2, "status": "ok"}\n',
    os.path.join(WORKSPACE, "tmp", "scratch.txt"): "temporary notes\ntodo: clean this up\n",
    os.path.join(WORKSPACE, "archive", "v0.8", "legacy.py"): "# deprecated\n# do not use\n",
    os.path.join(WORKSPACE, "archive", "v0.8", "migration_notes.md"): "## v0.8 → v0.9\n- Removed old memory system\n- No migration needed\n",
}

for path, content in distractor_files.items():
    with open(path, "w") as f:
        f.write(content)

print("[gen_inputs] Workspace scaffold complete.")
print(f"[gen_inputs] Skill at: {skill_root}")
print(f"[gen_inputs] Pre-existing AGENTS.md at: {openclaw_dir}/AGENTS.md")
print("[gen_inputs] Distractor files created.")