import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# === Create deeply nested distractor structure ===
distractor_dirs = [
    "ops/incidents/2024/q1",
    "ops/incidents/2024/q2",
    "ops/postmortems/archive",
    "knowledge/principles",
    "knowledge/done",
    "knowledge/insights",
    "knowledge/raw",
    "team/protocols/drafts",
    "team/protocols/approved",
    "team/onboarding/materials",
    "logs/system",
    "logs/application",
    "reports/weekly",
    "reports/monthly",
]

for d in distractor_dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = {
    "ops/incidents/2024/q1/incident_001.txt": "Incident: DB timeout\nStatus: Resolved\nDate: 2024-01-15",
    "ops/incidents/2024/q1/incident_002.txt": "Incident: Memory leak in auth service\nStatus: Resolved\nDate: 2024-02-03",
    "ops/incidents/2024/q2/incident_003.txt": "Incident: CDN misconfiguration\nStatus: Open\nDate: 2024-04-22",
    "ops/postmortems/archive/pm_001.md": "# Postmortem 001\n## Summary\nDatabase failover took 8 minutes instead of 2.",
    "knowledge/principles/principle_001.txt": "Always prefer read replicas for analytics queries.",
    "knowledge/done/task_log.txt": "2024-01-10: Migrated 3 services to k8s\n2024-02-20: Updated TLS certs",
    "knowledge/insights/insight_001.txt": "Caching at the CDN layer reduces origin load by 60%.",
    "knowledge/raw/unprocessed_001.txt": "Random note: check redis eviction policy",
    "team/protocols/drafts/response_draft_v1.txt": "Draft: incident response steps (unfinished)",
    "team/protocols/approved/escalation_matrix.txt": "P0: page on-call immediately\nP1: notify team lead within 15 min",
    "team/onboarding/materials/welcome.txt": "Welcome to the SRE team. Read all protocols before your first on-call shift.",
    "logs/system/syslog_sample.txt": "Jan 15 02:14:33 kernel: OOM killer invoked",
    "logs/application/app_error_sample.txt": "ERROR 2024-01-15 02:14:40 - NullPointerException in UserService.java:142",
    "reports/weekly/week_03_summary.txt": "Incidents this week: 2 P1, 0 P0. MTTR improved by 12%.",
    "reports/monthly/jan_2024.txt": "Total incidents: 8. SLA compliance: 99.2%.",
}

for path, content in distractors.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# === The SKILL.md file that the agent must read ===
skill_content = r"""# 3steps to wisdom / 沟通三部曲

> 智慧获取的标准工作流程
> 打开双方黑盒、让双方共同进步的唯一工具

---

## 核心理念

**沟通三部曲是帮我们双方打开对方黑盒的工具。**

镜子照见的不只是一个人——是镜子内外两个人：
- 帮彧哥发现小蜂执行的偏差
- 帮小蜂发现彧哥表述的漏洞

**它是让我们双方共同进步的唯一工具。**

---

The Three Steps is the tool that helps us both open each other's black box.

The mirror reflects two people—inside and outside the mirror:
- Helping Yu Ge discover Xiao Feng's execution deviations
- Helping Xiao Feng discover Yu Ge's expression gaps

It's the only tool that enables our mutual progress.

---

## 原始版三部曲结构

每次收到消息，回复前必须满足以下结构：

### 1. 思考
**目标、方案、选择理由**

- 目标是什么？
- 有哪些可选方案？
- 为什么选择这个方案？

### 2. 执行
**命令 + 结果**

- 展示命令（带注释）
- 展示执行结果

### 3. 复盘
**亮点、可优化、学到**

- 这次做得好的是什么？
- 可以改进的是什么？
- 学到了什么新东西？

---

### 1. Thinking
Goals, options, rationale

- What are we trying to achieve?
- What alternatives exist?
- Why did we pick this option?

### 2. Execution
Command + Result

- Show the command (with comments)
- Show the execution result

### 3. Reflection
What went well, what to improve, what we learned

- What worked?
- What could be better?
- What's the new insight?

---

## 为什么它是唯一工具

**透明 = 信任 = 协同进化**

- 黑盒 = 失控 + 高成本 + 低效率
- 三部曲把黑盒变白盒

Without the Three Steps, the mirror失效了：
- 直接给答案 → 看不见思考过程 → 无法纠偏
- 偏差累积 → 协同进化停摆

---

## 自检清单

发出前检查三模块是否完整：
- 思考 ✅
- 执行 ✅
- 复盘 ✅

⚠️ 缺少任意模块 → 补上再发

Before sending, verify all three modules are present. Missing any → complete before sending.

---

## 与记忆宫的配合

三部曲的产出自动沉淀：
- 决策过程 → 存入记忆宫的热/原则
- 执行结果 → 存入记忆宫的温/done
- 复盘收获 → 存入记忆宫的热/领悟

---

The outputs of the Three Steps automatically flow into the memory palace:
- Decision rationale → stored in 热/原则 (principles)
- Execution results → stored in 温/done (completed work)
- Reflections and insights → stored in 热/领悟 (insights)

---

*3steps to wisdom v2.1*
"""

with open(os.path.join(workspace, "SKILL.md"), "w") as f:
    f.write(skill_content)

# === The raw incident report the agent must work with ===
raw_incident = """INCIDENT TICKET #INC-2024-0887
Date: 2024-07-14
Reporter: Sarah Chen (SRE Lead)
Priority: P1

Summary:
The primary PostgreSQL database cluster experienced intermittent connection pool exhaustion
between 03:15 and 04:45 UTC. Application error rates spiked to 34%. The on-call engineer
(Mike Torres) identified that a batch analytics job had been misconfigured to run against
the primary instead of the read replica, saturating the connection pool.

Actions Taken:
1. Killed the rogue analytics batch job at 03:58 UTC
2. Restarted connection pool manager (PgBouncer) at 04:02 UTC
3. Verified traffic normalised by 04:12 UTC
4. Updated the analytics job configuration to point to the read replica
5. Added a runbook entry for PgBouncer restart procedure

Resolution:
System recovered. Root cause was a misconfigured job. SLA impact: ~90 minutes degraded.

Open Questions:
- Should we add a hard constraint in the job scheduler to block primary DB access for analytics workloads?
- Can we set up automated alerts for connection pool saturation >70%?
"""

os.makedirs(os.path.join(workspace, "ops/incidents/2024/q3"), exist_ok=True)
with open(os.path.join(workspace, "ops/incidents/2024/q3/INC-2024-0887_raw.txt"), "w") as f:
    f.write(raw_incident)

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in __import__('pathlib').Path(workspace).rglob('*') if _.is_file())}")