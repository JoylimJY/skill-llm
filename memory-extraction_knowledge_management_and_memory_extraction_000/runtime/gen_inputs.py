import os
import json
import random

random.seed(42)

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "memory",
    "logs/sessions",
    "logs/errors",
    "config",
    "docs/api",
    "docs/internal",
    "tests/unit",
    "tests/integration",
    "data/raw",
    "data/processed",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractor_files = {
    "config/settings.yaml": "debug: false\nlog_level: INFO\nmax_memory_entries: 500\n",
    "config/agent_config.json": json.dumps({"model": "gpt-4o", "temperature": 0.7, "max_tokens": 2048}, indent=2),
    "docs/api/endpoints.md": "# API Endpoints\n## POST /chat\n## GET /memory\n## DELETE /memory/{id}\n",
    "docs/internal/architecture.md": "# Architecture\nThe system uses a layered approach.\n## Layer 1: Ingestion\n## Layer 2: Processing\n## Layer 3: Storage\n",
    "logs/errors/error_2024_01.log": "[ERROR] 2024-01-15 Connection timeout\n[ERROR] 2024-01-16 Parse failure\n",
    "logs/sessions/session_old_001.jsonl": '{"role":"user","content":"hello"}\n{"role":"assistant","content":"hi"}\n',
    "tests/unit/test_parser.py": "import pytest\ndef test_placeholder():\n    assert True\n",
    "tests/integration/test_memory.py": "import pytest\ndef test_memory_placeholder():\n    assert True\n",
    "data/raw/legacy_export.csv": "id,name,type\n1,Alice,user\n2,ProjectX,project\n",
    "data/processed/cleaned_entities.json": json.dumps([{"id": 1, "label": "Alice"}, {"id": 2, "label": "ProjectX"}], indent=2),
    "memory/.gitkeep": "",
}
for path, content in distractor_files.items():
    with open(path, "w") as f:
        f.write(content)

# ── the KnowledgeGraphManager script (the real skill implementation) ──────────
kg_manager_code = '''
import json
import os
from pathlib import Path
from datetime import datetime

STORAGE_PATH = Path("memory/knowledge-graph.jsonl")
VIEW_PATH = Path("memory/KNOWLEDGE_GRAPH.md")

class KnowledgeGraphManager:
    def __init__(self):
        self.entities = {}   # name -> {name, entityType, observations: []}
        self.relations = []  # [{from, to, relationType}]
        self._load()

    def _load(self):
        if not STORAGE_PATH.exists():
            return
        with open(STORAGE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                if record.get("type") == "entity":
                    e = record["data"]
                    self.entities[e["name"]] = e
                elif record.get("type") == "relation":
                    self.relations.append(record["data"])

    def _save(self):
        STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(STORAGE_PATH, "w", encoding="utf-8") as f:
            for e in self.entities.values():
                f.write(json.dumps({"type": "entity", "data": e}, ensure_ascii=False) + "\\n")
            for r in self.relations:
                f.write(json.dumps({"type": "relation", "data": r}, ensure_ascii=False) + "\\n")

    def create_entities(self, entities):
        for e in entities:
            name = e["name"]
            if name not in self.entities:
                self.entities[name] = {
                    "name": name,
                    "entityType": e.get("entityType", "unknown"),
                    "observations": list(e.get("observations", []))
                }
            else:
                # merge observations
                existing = set(self.entities[name]["observations"])
                for obs in e.get("observations", []):
                    if obs not in existing:
                        self.entities[name]["observations"].append(obs)
        self._save()

    def create_relations(self, relations):
        existing = {(r["from"], r["to"], r["relationType"]) for r in self.relations}
        for r in relations:
            key = (r["from"], r["to"], r["relationType"])
            if key not in existing:
                self.relations.append(r)
                existing.add(key)
        self._save()

    def add_observations(self, observations):
        for item in observations:
            name = item["entityName"]
            if name not in self.entities:
                raise ValueError(f"Entity not found: {name}")
            existing = set(self.entities[name]["observations"])
            for content in item["contents"]:
                if content not in existing:
                    self.entities[name]["observations"].append(content)
                    existing.add(content)
        self._save()

    def search_nodes(self, query):
        results = []
        q = query.lower()
        for e in self.entities.values():
            if q in e["name"].lower() or any(q in o.lower() for o in e["observations"]):
                results.append(e)
        return results

    def read_graph(self):
        return {"entities": list(self.entities.values()), "relations": self.relations}

    def export_markdown(self):
        lines = ["# Knowledge Graph\\n"]
        lines.append("## Entities\\n")
        for e in self.entities.values():
            lines.append(f"### {e[\'name\']} ({e[\'entityType\']})")
            for obs in e["observations"]:
                lines.append(f"- {obs}")
            lines.append("")
        lines.append("## Relations\\n")
        for r in self.relations:
            lines.append(f"- {r[\'from\']} --[{r[\'relationType\']}]--> {r[\'to\']}")
        lines.append("")
        content = "\\n".join(lines)
        VIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(VIEW_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        return content
'''

with open("scripts/knowledge_graph_manager.py", "w", encoding="utf-8") as f:
    f.write(kg_manager_code)

# ── the messy onboarding conversation transcript ──────────────────────────────
# This is the "raw, messy input" the agent must process.
# It is intentionally unstructured, contains colloquialisms and implicit facts.
transcript = """
=== USER ONBOARDING SESSION TRANSCRIPT ===
Session ID: ONB-2024-0317-A
Timestamp: 2024-03-17 10:22:05

[User]: 你好！我叫李明，我是一名后端工程师，目前在上海工作。
[Assistant]: 你好，李明！很高兴认识你。请问有什么我可以帮你的？
[User]: 我最近在做一个叫"DataFlow"的数据管道项目，主要用Python和Apache Kafka来处理流数据。
[Assistant]: 听起来很有意思！DataFlow 是做什么用的？
[User]: 就是把各种数据源接进来，实时处理后推送出去。我打算把它部署到腾讯云上。
[Assistant]: 明白了。你对界面风格有什么偏好吗？
[User]: 我喜欢简洁的深色主题，另外我的工作语言主要是中文，代码注释也习惯用中文写。
[Assistant]: 好的，我记下来了。你目前团队里有几个人一起做 DataFlow？
[User]: 就我一个人，兼职做的。我的邮箱是liming@example.com，时区是Asia/Shanghai。
[Assistant]: 了解。除了 Python 和 Kafka，你还用到哪些技术？
[User]: 还用了 Redis 做缓存，另外我有飞书的 API 集成技能，之前做过飞书机器人。
[Assistant]: 好的，这些我都会记录下来，下次对话直接给你个性化建议。

=== END OF TRANSCRIPT ===
"""

with open("data/raw/onboarding_transcript.txt", "w", encoding="utf-8") as f:
    f.write(transcript)

# ── SKILL.md ──────────────────────────────────────────────────────────────────
skill_md = open("SKILL.md", "w", encoding="utf-8") if not os.path.exists("SKILL.md") else None

skill_content = """# 记忆提取 Skill

自动从对话中提取 Entity/Relation/Observation 并更新知识图谱。

## 功能

1. **实体提取** - 从对话中识别用户、项目、技能、偏好等实体
2. **关系提取** - 识别实体之间的关系
3. **观察提取** - 提取原子化事实作为观察
4. **自动更新** - 写入知识图谱存储

## 使用方法

### 手动调用

```python
from scripts.knowledge_graph_manager import KnowledgeGraphManager

manager = KnowledgeGraphManager()

# 创建实体
manager.create_entities([
    {'name': '新项目', 'entityType': 'project', 'observations': ['描述']}
])

# 创建关系
manager.create_relations([
    {'from': '用户', 'to': '新项目', 'relationType': 'owns'}
])

# 添加观察
manager.add_observations([
    {'entityName': '用户', 'contents': ['新偏好']}
])
```

### 自动提取规则

Agent 在对话中应主动识别以下信息并写入记忆：

#### 实体类型

| entityType | 识别信号 | 示例 |
|------------|----------|------|
| `user` | "我是"、"我的" | "我叫张三" → 创建用户实体 |
| `project` | "项目"、"做个"、"创建" | "做个看板" → 创建项目实体 |
| `skill` | "技能"、"能力" | "我有飞书技能" → 创建技能实体 |
| `tool` | "用"、"使用" | "用 yfinance" → 创建工具实体 |
| `preference` | "喜欢"、"偏好"、"想" | "喜欢深色风格" → 创建偏好实体 |
| `location` | "在"、"位于" | "在北京" → 创建地点实体 |
| `event` | "今天"、"时间点" | "2026-03-06 初次对话" → 创建事件实体 |

#### 关系类型

| relationType | 识别信号 | 示例 |
|--------------|----------|------|
| `owns` | "我的"、"我做的" | 用户 owns 项目 |
| `uses` | "用"、"使用" | 项目 uses 工具 |
| `prefers` | "喜欢"、"偏好" | 用户 prefers 偏好 |
| `located_at` | "在"、"位于" | 用户 located_at 地点 |
| `named` | "叫"、"命名" | 用户 named Agent |
| `created_on` | "创建时间" | 项目 created_on 时间 |
| `deployed_to` | "部署到" | 项目 deployed_to 平台 |

#### 观察提取

观察应该是**原子化事实**：
- 一条观察 = 一个事实
- 简洁、具体、可验证

**示例**：
- ✅ "时区：Asia/Shanghai"
- ✅ "邮箱：user@example.com"
- ❌ "用户信息包括时区和邮箱"（不是原子化）

## 记忆更新流程

```
对话开始
    ↓
读取知识图谱 (search_nodes / read_graph)
    ↓
对话进行中
    ↓
识别新信息 → 提取 Entity/Relation/Observation
    ↓
写入知识图谱 (create_entities / create_relations / add_observations)
    ↓
对话结束
    ↓
导出 Markdown 视图
```

## System Prompt 集成

在 Agent 的 System Prompt 中添加：

```
## 记忆管理

每次对话开始时：
1. 说 "正在回忆..." 并从知识图谱检索相关信息
2. 将知识图谱称为 "记忆"

对话过程中：
主动识别并记录以下类型的信息：
- Basic Identity: 年龄、性别、位置、职业、教育
- Behaviors: 兴趣、习惯
- Preferences: 交流风格、语言偏好
- Goals: 目标、期望
- Relationships: 人际关系（3 度以内）

发现新信息时：
1. 创建实体（用户、项目、技能、工具、偏好、地点、事件）
2. 创建关系（owns, uses, prefers, located_at, named 等）
3. 添加观察（原子化事实）
```

## 文件位置

- 管理器: `scripts/knowledge_graph_manager.py`
- 存储: `memory/knowledge-graph.jsonl`
- 视图: `memory/KNOWLEDGE_GRAPH.md`

---

*基于 MCP Memory Server 设计*
"""

with open("SKILL.md", "w", encoding="utf-8") as f:
    f.write(skill_content)

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk("."):
    # skip .git
    dirs_list[:] = [d for d in dirs_list if d != ".git"]
    for file in files:
        print(f"  {os.path.join(root, file)}")