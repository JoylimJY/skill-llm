import os
import random
import json
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ─── 1. Directory structure with distractor files ───────────────────────────

dirs = [
    "docs/architecture",
    "docs/legacy",
    "docs/meeting_notes",
    "src/core/agents",
    "src/core/plugins",
    "src/edge/firmware",
    "src/cloud/sync",
    "reports/q1_2024",
    "reports/templates",
    "infra/k8s",
    "infra/ci",
    "analysis/competitors",
    "analysis/drafts",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ─── 2. Distractor files ─────────────────────────────────────────────────────

(WORKSPACE / "docs/architecture/overview.md").write_text(
    "# NexusMFG Platform Overview\n\nNexusMFG is a smart manufacturing IoT platform...\n(draft - incomplete)\n"
)

(WORKSPACE / "docs/architecture/components.md").write_text(
    "## Components\n- Gateway Nodes\n- Cloud Orchestrator\n- Edge Runtime\n- Data Lake\n- ML Pipeline\n"
)

(WORKSPACE / "docs/legacy/old_evaluation.txt").write_text(
    "Previous eval used ISO 25010. Scores: Reliability 78%, Performance 82%, Maintainability 65%\n"
)

(WORKSPACE / "docs/meeting_notes/2024-03-15.md").write_text(
    "Meeting: Discussed migration from monolith to microservices. Key concern: edge node autonomy.\n"
)

(WORKSPACE / "docs/meeting_notes/2024-04-02.md").write_text(
    "Security audit pending. Hardware TPM integration under review. Privacy compliance needed.\n"
)

(WORKSPACE / "src/core/agents/task_router.py").write_text(
    "# TaskRouter - dispatches tasks to specialized agents\nclass TaskRouter:\n    def route(self, task):\n        pass\n"
)

(WORKSPACE / "src/core/plugins/plugin_registry.py").write_text(
    "# PluginRegistry - hot-reloadable skill modules\nclass PluginRegistry:\n    def load(self, path): pass\n    def unload(self, name): pass\n"
)

(WORKSPACE / "src/edge/firmware/node_agent.c").write_text(
    "// Edge node autonomous agent firmware\n// Supports local mesh networking\n// TODO: implement local ML inference\n"
)

(WORKSPACE / "src/cloud/sync/memory_sync.py").write_text(
    "# Cross-device memory synchronization module\n# Currently only syncs to cloud, not peer-to-peer\nclass MemorySync:\n    def push(self, data): pass\n"
)

(WORKSPACE / "reports/q1_2024/metrics.json").write_text(
    json.dumps({
        "uptime": "99.2%", "edge_nodes": 1240, "avg_latency_ms": 45,
        "skill_modules_active": 38, "ml_model_updates_per_week": 3
    }, indent=2)
)

(WORKSPACE / "reports/templates/eval_template.docx").write_text(
    "[Binary placeholder - not readable]\n"
)

(WORKSPACE / "infra/k8s/deployment.yaml").write_text(
    "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: nexusmfg-orchestrator\n"
)

(WORKSPACE / "infra/ci/pipeline.yml").write_text(
    "stages:\n  - build\n  - test\n  - deploy\n"
)

(WORKSPACE / "analysis/competitors/competitor_matrix.csv").write_text(
    "Vendor,EdgeAutonomy,SkillMarketplace,MemorySync,MultiModal\n"
    "SiemensEdge,High,Low,Medium,None\n"
    "PTC ThingWorx,Medium,Medium,Low,None\n"
    "AWS IoT Greengrass,Medium,High,Medium,None\n"
)

(WORKSPACE / "analysis/drafts/partial_notes.txt").write_text(
    "Rough notes:\n- NexusMFG edge nodes can run standalone but no formal skill plugin API yet\n"
    "- Memory layer is cloud-only as of v2.3\n"
    "- Agent-to-agent comms via MQTT pub/sub\n"
    "- No digital twin yet, roadmap item for Q3\n"
    "- TPM chips on gateway hardware but SDK not exposed\n"
    "- Skill inheritance not supported, copy-paste reuse only\n"
)

# ─── 3. The main project spec file (the input to analyze) ───────────────────

project_spec = """# NexusMFG 智能制造平台 — 项目技术规格说明书 v2.3

## 项目背景
NexusMFG 是一个面向重型制造业的工业物联网平台，部署于1200余家工厂，
管理超过120万个边缘节点（含PLC控制器、传感器网关、机械臂控制单元）。

## 架构组件

### 边缘层
- 每个工厂网关（Edge Gateway）运行轻量级 Agent Runtime v1.8
- 网关之间通过 ZigBee/LoRa 形成局域网状网络，支持断网运行最长72小时
- 边缘节点无法主动发现或加入其他节点的集群（需要手动配置）
- 无本地ML推理引擎，所有推理任务上传云端处理

### 技能/插件层
- 支持运行时热加载 .nxpkg 格式技能包（无需重启网关）
- 技能包通过 NexusMFG Marketplace 发布/订阅
- 技能继承机制：不支持，开发者只能复制粘贴已有技能代码
- 技能组合：支持通过可视化拖拽编排（低代码），但无无代码选项

### 记忆与数据层
- 所有设备状态和历史记忆统一存储于中央 Cloud Memory Hub
- 记忆同步协议：单向推送（Edge→Cloud），不支持 Edge 端本地持久化
- 无记忆压缩/蒸馏机制，原始数据全量存储（已产生存储瓶颈）
- 无跨用户知识共享机制（各工厂数据完全隔离）

### 协作与编排层
- Agent 之间通过 MQTT pub/sub 通信
- 任务分配由中央 Orchestrator 决定（非自动分解）
- 系统内置12类专家 Agent（焊接、质检、物流、能耗等），可相互调用
- Agent 间无意图对齐协议，任务描述需人工填写

### 感知层
- 仅支持结构化传感器数据（温度、压力、振动等数值流）
- 不支持图像、声音等非结构化输入
- 无3D环境建模或数字孪生功能（已列入Q3路线图）
- 设备可通过在线学习微调异常检测阈值（有限的持续学习能力）

### 安全层
- 每个 Agent 操作均写入不可篡改审计日志（含操作链路溯源）
- 所有敏感工厂数据（配方、参数）在边缘端加密，云端仅存哈希
- 硬件层：所有网关内置 TPM 2.0 芯片，但当前 SDK 未暴露 TPM API 给 Agent

### 自进化层
- Agent 根据历史操作频率和错误率自动调整任务优先级（有限自优化）
- 人机协作：操作员可通过反馈界面标注 Agent 决策，用于模型微调
- 尚无完整的 Agent 自主生成新技能的能力

## 已知技术债务
1. 记忆层存储成本失控（缺乏蒸馏）
2. 技能开发门槛高（缺乏继承机制）
3. 边缘节点自治能力受限（无自组织）
4. TPM 芯片利用率为零（信任链未打通）
"""

(WORKSPACE / "docs/architecture/nexusmfg_spec_v2.3.md").write_text(project_spec)

# ─── 4. SKILL.md (the methodology document the agent should use) ─────────────

skill_md = """---
name: openclaw-analysis
description: "用 OpenClaw 七大核心理念分析重大项目架构"
trigger: "分析|评估|审查|架构"
---

# OpenClaw 七大理念架构分析

用 OpenClaw 七大核心理念分析任何重大项目。

## 七大理念框架

### 1️⃣ Agent 无处不在（Ubiquitous Agents）
- 硬件即 Agent：每个设备是否都是独立 Agent 节点？
- 边缘自治网络：是否支持本地 Agent 集群自组织？
- Agent 市场机制：是否支持技能/Agent 的发布和订阅？

### 2️⃣ 技能即插件（Skill-as-Plugin）
- 动态技能热插拔：是否支持运行时动态加载/卸载技能？
- 技能组合编程：是否支持低代码/无代码组合新功能？
- 技能基因库：技能是否可继承、变异、重组？

### 3️⃣ 记忆即永续（Memory-as-Persistence）
- 跨设备记忆同步：是否所有设备共享同一记忆层？
- 记忆压缩与蒸馏：是否有记忆总结、提炼、遗忘机制？
- 集体记忆网络：是否支持跨用户知识共享？

### 4️⃣ 协作即本能（Collaboration-as-Instinct）
- Agent 意图对齐：Agent 之间是否能自动理解彼此目标？
- 动态任务编排：是否支持复杂任务自动分解和分配？
- 跨领域专家：是否有专家 Agent 相互调用？

### 5️⃣ 感知即语言（Perception-as-Language）
- 多模态统一编码：是否支持图像、声音、触觉统一处理？
- 物理世界数字孪生：是否实时构建3D环境模型？
- 持续学习感知：设备是否能持续学习用户习惯？

### 6️⃣ 安全即信任（Security-as-Trust）
- 可解释 AI 决策：每个 Agent 行为是否可追溯？
- 隐私优先架构：敏感数据是否本地处理？
- 硬件级信任链：是否有硬件级别的安全验证？

### 7️⃣ 进化即必然（Evolution-as-Inevitable）
- 自进化 Agent：是否能根据使用模式自我优化？
- 人机共生进化：是否支持人类和 AI 相互促进？

---

## 使用方法

告诉我你要分析的项目，我会用以上 7 大理念 21 个维度进行全面评估。

**示例：**
> "帮我用七大理念分析这个智能家居系统"
"""

(WORKSPACE / "SKILL.md").write_text(skill_md)

print("Workspace generated successfully.")
print(f"Files created: {len(list(WORKSPACE.rglob('*')))}")