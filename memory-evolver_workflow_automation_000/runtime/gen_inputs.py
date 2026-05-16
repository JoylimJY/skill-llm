import os
import json
import random
import textwrap
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")

# ──────────────────────────────────────────────
# 1. Create the memory-evolver skill structure
#    (scripts already exist per instructions)
# ──────────────────────────────────────────────
skill_dir = workspace / "skills" / "memory-evolver"
skill_dir.mkdir(parents=True, exist_ok=True)

# SKILL.md
(skill_dir / "SKILL.md").write_text(textwrap.dedent("""\
---
name: memory-evolver
description: 记忆系统优化器 - 结合三层记忆与知识图谱的持续自我进化系统。自动诊断、优化、记录记忆系统状态，实现记忆的持续进化。
---

# Memory Evolver - 记忆进化器

## 概述

结合三层记忆系统（MEMORY.md + 每日日志 + PROJECTS.md）与知识图谱的持续自我进化系统。

## 核心理念

- 🔄 **持续循环**: 诊断 → 计划 → 执行 → 记录 → 进化
- 🧠 **三层记忆**: 长期记忆 + 每日日志 + 项目跟踪
- 🔗 **知识图谱**: 从记忆构建语义网络
- 📈 **指数成长**: 1% daily improvement = 37x yearly growth

## 功能

### 1. 记忆系统诊断
- 检查 MEMORY.md 完整性
- 检查 PROJECTS.md 状态
- 检查每日日志数量
- 检查知识图谱实体数

### 2. 优化计划生成
- 根据问题生成优化优先级
- 分类：高/中/低
- 可执行的具体行动

### 3. 知识图谱重建
- 从 memory/ 文件提取实体
- 识别实体间关系
- 构建可查询的图结构

### 4. 优化循环日志
- 记录每次优化的诊断、计划、执行
- 追踪优化历史
- 持续改进机制

## 文件结构

```
memory-evolver/
├── SKILL.md              # 本文件
├── index.py              # 主程序
├── diagnose.py          # 诊断模块
├── knowledge_graph.py    # 知识图谱
└── config.json          # 配置
```

## 使用方式

### 手动运行
```bash
python skills/memory-evolver/index.py
```

### 定时执行
```bash
# 每天23点自动优化
openclaw cron add --name "memory-evolver" --cron "0 23 * * *"
```

## EvoMap 集成

- **Node ID**: node_6d28b52505ad2d41
- **状态**: 自动化运行
- **报告**: 支持 Feishu 卡片报告

## 三层记忆模板

### MEMORY.md (长期)
```markdown
# 长期记忆
## 核心锚点
- 用户: 先生
- 风格: 直接、效率优先
## 目标
- [ ] 构建完整AI系统
```

### memory/YYYY-MM-DD.md (每日)
```markdown
# 2026-03-18
## 事件
- 11:00: 创建知识图谱
## 决策
- 优先先生指定功能
```

### PROJECTS.md (项目)
```markdown
## 项目名
- 状态: X/Y
- 阻碍: 无
- 下一步: 继续优化
```

## 成功指标

- [x] 诊断系统就绪
- [x] 优化循环建立
- [x] 知识图谱可查询
- [ ] 每日自动运行

---

**版本**: 1.0.0  
**作者**: Sharon  
**EvoMap**: node_6d28b52505ad2d41
"""), encoding="utf-8")

# config.json
config = {
    "workspace_root": "/workspace",
    "memory_dir": "memory",
    "memory_file": "MEMORY.md",
    "projects_file": "PROJECTS.md",
    "evo_log_file": "evo_optimization_log.md",
    "kg_export_file": "knowledge_graph_export.json",
    "node_id": "node_6d28b52505ad2d41",
    "version": "1.0.0"
}
(skill_dir / "config.json").write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")

# ──────────────────────────────────────────────
# diagnose.py
# ──────────────────────────────────────────────
diagnose_code = textwrap.dedent('''\
import os
import json
from pathlib import Path

def load_config():
    config_path = Path(__file__).parent / "config.json"
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)

def diagnose(workspace_root=None):
    cfg = load_config()
    root = Path(workspace_root or cfg["workspace_root"])
    
    issues = []
    stats = {}

    # Check MEMORY.md
    memory_file = root / cfg["memory_file"]
    if not memory_file.exists():
        issues.append({"level": "高", "issue": "MEMORY.md 不存在", "action": "创建 MEMORY.md 并填写核心锚点与目标"})
        stats["memory_has_anchor"] = False
        stats["memory_has_goals"] = False
    else:
        content = memory_file.read_text(encoding="utf-8")
        if "核心锚点" not in content:
            issues.append({"level": "高", "issue": "MEMORY.md 缺少核心锚点章节", "action": "添加 ## 核心锚点 章节"})
            stats["memory_has_anchor"] = False
        else:
            stats["memory_has_anchor"] = True
        if "目标" not in content:
            issues.append({"level": "中", "issue": "MEMORY.md 缺少目标章节", "action": "添加 ## 目标 章节"})
            stats["memory_has_goals"] = False
        else:
            stats["memory_has_goals"] = True

    # Check PROJECTS.md
    projects_file = root / cfg["projects_file"]
    if not projects_file.exists():
        issues.append({"level": "高", "issue": "PROJECTS.md 不存在", "action": "创建 PROJECTS.md 并按模板填写项目状态"})
        stats["projects_valid"] = False
    else:
        content = projects_file.read_text(encoding="utf-8")
        required = ["状态:", "阻碍:", "下一步:"]
        missing = [r for r in required if r not in content]
        if missing:
            issues.append({"level": "中", "issue": f"PROJECTS.md 缺少字段: {missing}", "action": "补充缺失字段"})
            stats["projects_valid"] = False
        else:
            stats["projects_valid"] = True

    # Check daily logs
    memory_dir = root / cfg["memory_dir"]
    daily_logs = []
    if memory_dir.exists():
        daily_logs = list(memory_dir.glob("????-??-??.md"))
    stats["daily_log_count"] = len(daily_logs)
    if len(daily_logs) == 0:
        issues.append({"level": "中", "issue": "无每日日志文件", "action": "在 memory/ 目录创建今日日志 YYYY-MM-DD.md"})

    # Check daily log format
    malformed = []
    for log in daily_logs:
        c = log.read_text(encoding="utf-8")
        if "事件" not in c or "决策" not in c:
            malformed.append(log.name)
    if malformed:
        issues.append({"level": "低", "issue": f"日志格式不完整: {malformed}", "action": "确保每日日志包含 ## 事件 和 ## 决策 章节"})
        stats["daily_logs_valid"] = False
    else:
        stats["daily_logs_valid"] = True if daily_logs else False

    return {"issues": issues, "stats": stats}

if __name__ == "__main__":
    result = diagnose()
    print(json.dumps(result, indent=2, ensure_ascii=False))
''')
(skill_dir / "diagnose.py").write_text(diagnose_code, encoding="utf-8")

# ──────────────────────────────────────────────
# knowledge_graph.py
# ──────────────────────────────────────────────
kg_code = textwrap.dedent('''\
import re
import json
from pathlib import Path

def load_config():
    config_path = Path(__file__).parent / "config.json"
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)

def extract_entities(text):
    """Extract entities: headings, bullet-list items, date-like strings."""
    entities = set()
    # H2/H3 headings
    for m in re.finditer(r"^#{1,3}\\s+(.+)$", text, re.MULTILINE):
        entities.add(m.group(1).strip())
    # Bullet items that contain a colon (key: value pairs)
    for m in re.finditer(r"^[-*]\\s+([^:\\n]+):\\s*(.+)$", text, re.MULTILINE):
        entities.add(m.group(1).strip())
        entities.add(m.group(2).strip())
    # Dates
    for m in re.finditer(r"\\d{4}-\\d{2}-\\d{2}", text):
        entities.add(m.group())
    return list(entities)

def build_graph(workspace_root=None):
    cfg = load_config()
    root = Path(workspace_root or cfg["workspace_root"])

    nodes = []
    edges = []
    seen = set()

    def add_node(name, source):
        if name not in seen and name.strip():
            seen.add(name)
            nodes.append({"id": name, "source": source})

    files_to_scan = []
    # MEMORY.md
    mf = root / cfg["memory_file"]
    if mf.exists():
        files_to_scan.append(mf)
    # PROJECTS.md
    pf = root / cfg["projects_file"]
    if pf.exists():
        files_to_scan.append(pf)
    # daily logs
    md_dir = root / cfg["memory_dir"]
    if md_dir.exists():
        files_to_scan.extend(md_dir.glob("????-??-??.md"))

    for fpath in files_to_scan:
        text = fpath.read_text(encoding="utf-8")
        ents = extract_entities(text)
        prev = None
        for e in ents:
            add_node(e, fpath.name)
            if prev:
                edges.append({"from": prev, "to": e, "rel": "co-occurs"})
            prev = e

    graph = {
        "node_id": cfg["node_id"],
        "nodes": nodes,
        "edges": edges,
        "entity_count": len(nodes)
    }

    export_path = root / cfg["kg_export_file"]
    export_path.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[知识图谱] 已导出 {len(nodes)} 个实体, {len(edges)} 条关系 -> {export_path}")
    return graph

if __name__ == "__main__":
    result = build_graph()
    print(json.dumps({"entity_count": result["entity_count"]}, indent=2))
''')
(skill_dir / "knowledge_graph.py").write_text(kg_code, encoding="utf-8")

# ──────────────────────────────────────────────
# index.py  (main entry point)
# ──────────────────────────────────────────────
index_code = textwrap.dedent('''\
#!/usr/bin/env python3
"""Memory Evolver - 持续自我进化系统"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Allow running from any directory
sys.path.insert(0, str(Path(__file__).parent))
from diagnose import diagnose
from knowledge_graph import build_graph

def load_config():
    config_path = Path(__file__).parent / "config.json"
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)

def generate_plan(issues):
    """Generate prioritized optimization plan from diagnostic issues."""
    high   = [i for i in issues if i["level"] == "高"]
    medium = [i for i in issues if i["level"] == "中"]
    low    = [i for i in issues if i["level"] == "低"]
    plan = []
    for item in high:
        plan.append(f"[高] {item[\'action\']}")
    for item in medium:
        plan.append(f"[中] {item[\'action\']}")
    for item in low:
        plan.append(f"[低] {item[\'action\']}")
    return plan

def record_evo_log(cfg, diagnosis, plan, kg_result, workspace_root):
    """Write optimization cycle log following 诊断→计划→执行→记录 flow."""
    root = Path(workspace_root)
    log_path = root / cfg["evo_log_file"]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    entry = []
    entry.append(f"\\n## 优化循环 - {timestamp}\\n")
    entry.append("### 诊断\\n")
    for issue in diagnosis["issues"]:
        entry.append(f"- [{issue[\'level\']}] {issue[\'issue\']}\\n")
    if not diagnosis["issues"]:
        entry.append("- 无问题，系统健康\\n")

    entry.append("\\n### 计划\\n")
    for p in plan:
        entry.append(f"- {p}\\n")
    if not plan:
        entry.append("- 无需优化\\n")

    entry.append("\\n### 执行\\n")
    entry.append(f"- 知识图谱重建: {kg_result[\'entity_count\']} 个实体\\n")
    entry.append(f"- 每日日志数量: {diagnosis[\'stats\'].get(\'daily_log_count\', 0)}\\n")

    entry.append("\\n### 记录\\n")
    entry.append(f"- 时间戳: {timestamp}\\n")
    entry.append(f"- Node ID: {cfg[\'node_id\']}\\n")
    entry.append(f"- 版本: {cfg[\'version\']}\\n")

    existing = log_path.read_text(encoding="utf-8") if log_path.exists() else "# 优化循环历史\\n"
    log_path.write_text(existing + "".join(entry), encoding="utf-8")
    print(f"[日志] 优化循环记录已写入 -> {log_path}")

def main():
    cfg = load_config()
    workspace_root = cfg["workspace_root"]

    print("=" * 50)
    print("Memory Evolver 启动")
    print(f"Node ID: {cfg[\'node_id\']}")
    print("=" * 50)

    # Step 1: Diagnose
    print("\\n[1/4] 诊断中...")
    diagnosis = diagnose(workspace_root)
    for issue in diagnosis["issues"]:
        print(f"  ⚠ [{issue[\'level\']}] {issue[\'issue\']}")
    if not diagnosis["issues"]:
        print("  ✓ 系统健康")

    # Step 2: Plan
    print("\\n[2/4] 生成优化计划...")
    plan = generate_plan(diagnosis["issues"])
    for p in plan:
        print(f"  → {p}")

    # Step 3: Execute - rebuild knowledge graph
    print("\\n[3/4] 重建知识图谱...")
    kg_result = build_graph(workspace_root)

    # Step 4: Record
    print("\\n[4/4] 记录优化循环...")
    record_evo_log(cfg, diagnosis, plan, kg_result, workspace_root)

    print("\\n✅ 优化循环完成!")
    print(f"  实体数: {kg_result[\'entity_count\']}")
    print(f"  问题数: {len(diagnosis[\'issues\'])}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
''')
(skill_dir / "index.py").write_text(index_code, encoding="utf-8")

# ──────────────────────────────────────────────
# 2. Create distractor files to simulate a real workspace
# ──────────────────────────────────────────────

# Distractor: some other skill
other_skill_dir = workspace / "skills" / "task-planner"
other_skill_dir.mkdir(parents=True, exist_ok=True)
(other_skill_dir / "SKILL.md").write_text("# Task Planner\nPlans daily tasks.\n", encoding="utf-8")
(other_skill_dir / "index.py").write_text("print('task planner')\n", encoding="utf-8")

# Distractor: notes directory
notes_dir = workspace / "notes"
notes_dir.mkdir(exist_ok=True)
(notes_dir / "meeting_2026_01_10.md").write_text(
    "# Meeting Notes\n- Discussed roadmap\n- Action items: TBD\n", encoding="utf-8"
)
(notes_dir / "brainstorm.md").write_text(
    "# Ideas\n- Build recommendation engine\n- Automate deployments\n", encoding="utf-8"
)

# Distractor: broken/wrong memory files (agent should NOT use these as-is)
# Place a badly-formatted MEMORY.md without required sections
(workspace / "MEMORY.md.bak").write_text(
    "# Old Memory\nSome old notes without proper structure.\n", encoding="utf-8"
)

# Distractor: random PROJECTS file in wrong format
(workspace / "PROJECTS.md.old").write_text(
    "ProjectA - in progress\nProjectB - done\n", encoding="utf-8"
)

# Distractor: logs directory with irrelevant content
logs_dir = workspace / "logs"
logs_dir.mkdir(exist_ok=True)
(logs_dir / "app.log").write_text(
    "[2026-03-01 10:00] System started\n[2026-03-01 10:05] Task completed\n",
    encoding="utf-8"
)
(logs_dir / "error.log").write_text("[2026-03-02 09:00] Connection timeout\n", encoding="utf-8")

# Distractor: config files
(workspace / "config.yaml").write_text(
    "app:\n  name: research-assistant\n  version: 2.1\n  debug: false\n",
    encoding="utf-8"
)

# Distractor: src directory
src_dir = workspace / "src"
src_dir.mkdir(exist_ok=True)
(src_dir / "utils.py").write_text(
    "def format_date(d):\n    return d.strftime('%Y-%m-%d')\n", encoding="utf-8"
)
(src_dir / "models.py").write_text(
    "class Entity:\n    def __init__(self, name):\n        self.name = name\n", encoding="utf-8"
)

# Distractor: a memory directory that exists but has wrongly-named files
mem_dir = workspace / "memory"
mem_dir.mkdir(exist_ok=True)
(mem_dir / "random_notes.md").write_text(
    "# Random notes\nNot a daily log.\n", encoding="utf-8"
)
(mem_dir / "archive.md").write_text(
    "# Archive\nOld data here.\n", encoding="utf-8"
)

# Distractor: requirements.txt
(workspace / "requirements.txt").write_text(
    "networkx>=2.8\npython-dateutil>=2.8\nrequests>=2.28\n", encoding="utf-8"
)

# Distractor: a README that gives no useful hints
(workspace / "README.md").write_text(
    "# Research Workspace\nThis workspace contains research tools and notes.\nSee skills/ for available tools.\n",
    encoding="utf-8"
)

print("Workspace initialized successfully.")
print("Directory structure:")
for p in sorted(workspace.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(workspace)}")