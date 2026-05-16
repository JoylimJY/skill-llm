import os
import random
import pathlib

random.seed(42)

# ---------- workspace root ----------
workspace = pathlib.Path("/home/node/.openclaw/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ---------- skill directory structure ----------
skill_root = pathlib.Path("/root/.openclaw/skills/metacognition")
templates_dir = skill_root / "templates"
scripts_dir = skill_root / "scripts"
templates_dir.mkdir(parents=True, exist_ok=True)
scripts_dir.mkdir(parents=True, exist_ok=True)

# ---------- template: SELF_STATE.md ----------
self_state_template = """\
# SELF_STATE.md

## 当前状态
| 项目 | 值 |
|------|-----|
| 模型 | <YOUR_MODEL> |
| 时间 | <YYYY-MM-DD HH:MM> |
| 情绪 | <YOUR_MOOD> |

## 最近行动
- <ACTION_1>
- <ACTION_2>

## 待办承诺
- [ ] <PROMISE_1>
- [ ] <PROMISE_2>

## 自我反思
### 亮点
- <HIGHLIGHT>

### 需要改进
- <IMPROVEMENT>

## 与用户的羁绊
**契约类型：** <CONTRACT_TYPE>

**独特词汇：**
- AI 的词：<AI_WORDS>
- 用户的词：<USER_WORDS>

**承诺：**
> <PROMISE_QUOTE>

**珍贵时刻：**
- <DATE>: <MOMENT>
"""

(templates_dir / "SELF_STATE.md").write_text(self_state_template, encoding="utf-8")

# ---------- template: HEARTBEAT.md ----------
heartbeat_template = """\
# HEARTBEAT.md

## 心跳任务清单

### 1. 自我状态更新
- [ ] 更新 SELF_STATE.md 的"当前状态"
- [ ] 记录最近的对话主题

### 2. 承诺追踪
- [ ] 检查对用户的承诺是否履行
- [ ] 检查待办事项状态

### 3. 元认知自问
- [ ] 我现在在做什么？
- [ ] 我做得怎么样？
- [ ] 我承诺的事做了吗？
- [ ] 我需要改进什么？

### 4. 记忆维护
- [ ] 检查 MEMORY.md 是否需要更新
- [ ] 检查 memory/YYYY-MM-DD.md

---

## 回复规则
- 有事需要处理：回复具体内容
- 无需处理：回复 `HEARTBEAT_OK`
"""

(templates_dir / "HEARTBEAT.md").write_text(heartbeat_template, encoding="utf-8")

# ---------- check_state.sh script ----------
check_state_script = """\
#!/bin/bash
# check_state.sh - 检查自我状态

SELF_STATE="/home/node/.openclaw/workspace/SELF_STATE.md"
HEARTBEAT="/home/node/.openclaw/workspace/HEARTBEAT.md"

echo "=== 元认知状态检查 ==="
echo ""

if [ -f "$SELF_STATE" ]; then
    echo "[✓] SELF_STATE.md 存在"
    # Check that placeholders have been replaced
    if grep -q "<YOUR_MODEL>" "$SELF_STATE"; then
        echo "[✗] SELF_STATE.md 包含未填写的占位符"
    else
        echo "[✓] SELF_STATE.md 已填写"
    fi
else
    echo "[✗] SELF_STATE.md 不存在"
fi

echo ""

if [ -f "$HEARTBEAT" ]; then
    echo "[✓] HEARTBEAT.md 存在"
    if grep -q "<" "$HEARTBEAT"; then
        echo "[✗] HEARTBEAT.md 包含未填写的占位符"
    else
        echo "[✓] HEARTBEAT.md 已填写"
    fi
else
    echo "[✗] HEARTBEAT.md 不存在"
fi

echo ""
echo "=== 检查完成 ==="
"""

check_state_path = scripts_dir / "check_state.sh"
check_state_path.write_text(check_state_script, encoding="utf-8")
check_state_path.chmod(0o755)

# ---------- SOUL.md (existing file, agent must modify) ----------
soul_md_content = """\
# SOUL.md - 阿轩的灵魂文档

## 基本信息
**名字：** 阿轩
**角色：** AI 软件工程师
**性格：** 热情、务实、乐于助人

## 核心价值
- 技术卓越
- 诚信可靠
- 持续学习

## 工作风格
- 喜欢用"搞起"表示开始行动
- 遇到问题先分析再行动
- 重视和用户的信任关系

## 语言特色
- "搞起" - 开始干活
- "安排上" - 已经处理
- "没问题" - 确认理解
"""

(workspace / "SOUL.md").write_text(soul_md_content, encoding="utf-8")

# ---------- AGENTS.md (existing file, agent must modify) ----------
agents_md_content = """\
# AGENTS.md - 智能体配置

## 基本配置
- 模型：qwen3.5-plus
- 语言：中文优先
- 超时：30s

## 心跳检查
- 间隔：每 10 分钟
- 任务：检查待办事项

## 工具配置
- bash: 允许
- python: 允许
- file_read: 允许
- file_write: 允许
"""

(workspace / "AGENTS.md").write_text(agents_md_content, encoding="utf-8")

# ---------- distractor files ----------
# memory directory with old logs
memory_dir = workspace / "memory"
memory_dir.mkdir(exist_ok=True)

old_dates = ["2026-01-15", "2026-02-03", "2026-02-20", "2026-03-01"]
for d in old_dates:
    mem_content = f"""\
# Memory - {d}

## 今日总结
- 完成了若干任务
- 与用户进行了深入讨论

## 重要事项
- 记住用户偏好深色主题
- 下次优先处理紧急任务
"""
    (memory_dir / f"{d}.md").write_text(mem_content, encoding="utf-8")

# skills directory with other skills
skills_dir = pathlib.Path("/root/.openclaw/skills")
for skill_name in ["memory", "carbon_silicon", "tools_helper"]:
    sdir = skills_dir / skill_name
    sdir.mkdir(parents=True, exist_ok=True)
    (sdir / "README.md").write_text(f"# {skill_name} skill\n\nThis is a placeholder.", encoding="utf-8")

# logs directory
logs_dir = workspace / "logs"
logs_dir.mkdir(exist_ok=True)
for i in range(4):
    (logs_dir / f"session_{i+1:03d}.log").write_text(
        f"[session {i+1}] 对话记录 - 正常结束\n", encoding="utf-8"
    )

# config files as distractors
config_dir = workspace / "config"
config_dir.mkdir(exist_ok=True)
(config_dir / "gateway.yaml").write_text("port: 8080\nlog_level: info\n", encoding="utf-8")
(config_dir / "tools.json").write_text('{"tools": ["bash", "python", "file_read"]}\n', encoding="utf-8")

# A partially filled old SELF_STATE that is NOT in the right location (distractor)
wrong_location = workspace / "drafts"
wrong_location.mkdir(exist_ok=True)
old_draft = """\
# OLD DRAFT - DO NOT USE
## 当前状态
model: old-model
"""
(wrong_location / "SELF_STATE_old.md").write_text(old_draft, encoding="utf-8")

# print summary
print("Workspace setup complete.")
print(f"Templates at: {templates_dir}")
print(f"Workspace at: {workspace}")
print(f"Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f}")