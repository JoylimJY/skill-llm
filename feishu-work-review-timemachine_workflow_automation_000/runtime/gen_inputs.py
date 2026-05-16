import os
import random

random.seed(42)

BASE = "/workspace"

# Directory structure simulating a Feishu-exported workspace
dirs = [
    "feishu_export/wiki/platform_infra",
    "feishu_export/wiki/ai_efficiency",
    "feishu_export/meeting_notes/week1",
    "feishu_export/meeting_notes/week2",
    "feishu_export/meeting_notes/week3",
    "feishu_export/meeting_notes/week4",
    "feishu_export/project_docs/model_serving",
    "feishu_export/project_docs/data_pipeline",
    "feishu_export/project_docs/governance",
    "feishu_export/personal_drafts",
    "feishu_export/shared_team_docs",
    "feishu_export/archive/q2_review",
    "feishu_export/archive/q1_review",
]

for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# ── USER: 林晓宇 (Lin Xiaoyu) ── we will tell the agent the user is 林晓宇

# === WEEK 1 MATERIALS ===

# User-OWNED doc: Model serving latency redesign
with open(os.path.join(BASE, "feishu_export/project_docs/model_serving/latency_redesign_v2.md"), "w") as f:
    f.write("""# 模型服务延迟优化方案 v2
创建者：林晓宇
最后编辑：林晓宇
创建时间：第1周 周一

## 背景
当前 P99 延迟达 420ms，超出 SLA 目标 200ms。

## 方案
1. 引入异步预加载机制，减少冷启动时间
2. 优化 KV Cache 复用策略，降低显存碎片
3. 增加动态批处理窗口，从固定 32 调整为自适应 8-64

## 预期收益
P99 降至 180ms，吞吐提升 35%

## 负责人
林晓宇主导，张伟配合压测

## 进展
- [x] 方案评审通过（第1周周三）
- [x] 异步预加载开发完成
- [ ] KV Cache 优化待合入
""")

# Meeting note week1 - user is main speaker/owner
with open(os.path.join(BASE, "feishu_export/meeting_notes/week1/model_serving_review_0103.md"), "w") as f:
    f.write("""# 会议纪要：模型服务周会 0103
参会人：林晓宇、张伟、王芳、李明
主持：林晓宇

## 讨论内容
林晓宇介绍了延迟优化方案 v2 的核心思路，重点阐述了异步预加载和 KV Cache 策略的取舍。
张伟提出压测计划，由林晓宇拍板确认压测维度。
王芳更新了其负责的数据管道进度（与本议题无关）。

## Action Items
- 林晓宇：本周完成异步预加载开发，提交 PR
- 张伟：搭建压测环境
- 王芳：数据管道接口文档更新（王芳负责）

## 结论
延迟优化方案进入开发阶段，林晓宇主导推进。
""")

# Meeting note week1 - user merely attended
with open(os.path.join(BASE, "feishu_export/meeting_notes/week1/infra_team_standup_0104.md"), "w") as f:
    f.write("""# 基础设施团队 Standup 0104
参会人：全组（含林晓宇）
主持：陈刚

## 各人进展
- 陈刚：K8s 节点扩容完成
- 赵磊：监控大盘上线
- 林晓宇：参会，未发言
- 刘洋：存储迁移进行中

## 备注
常规周会，无特殊决策。
""")

# === WEEK 2 MATERIALS ===

# User-OWNED wiki page: AI efficiency initiative
with open(os.path.join(BASE, "feishu_export/wiki/ai_efficiency/llm_eval_framework_design.md"), "w") as f:
    f.write("""# LLM 评测框架设计文档
作者：林晓宇
Wiki 节点所有者：林晓宇
更新时间：第2周

## 目标
建立统一的 LLM 评测框架，支持多模型对比、自动化回归测试。

## 核心设计
1. 评测指标标准化（BLEU/Rouge/自定义业务指标）
2. 异步任务队列（Celery + Redis）
3. 结果存储与版本对比（MySQL + S3）

## 已完成
- 框架核心模块设计（林晓宇）
- 与数据团队对齐评测数据集格式（林晓宇组织）
- Demo 跑通，覆盖 3 个模型

## 下一步
- 接入 CI 流水线（预计第3周）
""")

# Meeting note week2 - user organized and drove
with open(os.path.join(BASE, "feishu_export/meeting_notes/week2/llm_eval_kickoff_0110.md"), "w") as f:
    f.write("""# LLM 评测框架启动会 0110
参会人：林晓宇、数据团队（吴敏、周杰）、算法团队（郑涛）
组织者：林晓宇

## 议程（林晓宇主导）
1. 林晓宇介绍框架设计方案，阐述多模型对比的技术选型理由
2. 吴敏确认数据集格式，与林晓宇对齐 schema
3. 郑涛提出评测维度需求，林晓宇承诺纳入 v1

## Action Items
- 林晓宇：完成框架核心模块，本周五提交可 demo 版本
- 吴敏：准备评测数据集样本（吴敏负责）
- 郑涛：整理业务评测指标列表（郑涛负责）
""")

# Distractor: someone else's project status that user happened to be in
with open(os.path.join(BASE, "feishu_export/meeting_notes/week2/data_pipeline_weekly_0111.md"), "w") as f:
    f.write("""# 数据管道周会 0111
参会人：王芳（主持）、刘洋、林晓宇（旁听）、张伟

## 主要内容
王芳介绍数据管道 v3 重构进展，目标是将批处理延迟从 6h 降至 2h。
刘洋汇报存储层优化完成。
林晓宇旁听，无发言记录。

## Action Items
- 王芳：本周完成重构核心模块
- 刘洋：存储层压测报告
（林晓宇无 action item）
""")

# === WEEK 3 MATERIALS ===

# User-OWNED doc: governance/metrics work
with open(os.path.join(BASE, "feishu_export/project_docs/governance/model_quality_metrics_v1.md"), "w") as f:
    f.write("""# 模型质量治理指标体系 v1
负责人：林晓宇
协作：郑涛（算法）、吴敏（数据）
创建：第3周

## 背景
现有模型质量监控缺乏统一标准，导致线上问题发现滞后。

## 核心指标
1. 漂移检测：KL 散度阈值告警
2. 稳定性指标：连续7天 P99 < 200ms
3. 业务指标：转化率对照组 A/B 基准

## 林晓宇的工作
- 主导指标体系设计与评审
- 协调算法、数据、产品三方对齐
- 撰写指标定义文档

## 状态
已通过评审，进入工程实施阶段。
""")

# Meeting note week3 - user as cross-team coordinator
with open(os.path.join(BASE, "feishu_export/meeting_notes/week3/quality_governance_review_0117.md"), "w") as f:
    f.write("""# 模型质量治理评审会 0117
参会：林晓宇、郑涛、吴敏、产品负责人陈总
组织：林晓宇

## 内容
林晓宇主持评审，逐一讲解三类核心指标的设计逻辑和阈值设定。
郑涛对漂移检测方案提出修改意见，林晓宇当场判断采纳与否。
陈总对业务指标提出优化方向，林晓宇承诺下周更新文档。

## 结论
指标体系通过评审，林晓宇负责跟进工程实施。
""")

# Distractor: broad team meeting, user attendance only
with open(os.path.join(BASE, "feishu_export/meeting_notes/week3/all_hands_0118.md"), "w") as f:
    f.write("""# 全员大会 0118
参会：全体员工（200+人）

## 内容
CEO 介绍公司 Q1 战略方向。
各 BU 负责人汇报 Q4 成果。
林晓宇参会（无发言）。

## 备注
无具体 action item。
""")

# === WEEK 4 MATERIALS ===

# User-OWNED: model serving final push + cross-team traction
with open(os.path.join(BASE, "feishu_export/project_docs/model_serving/latency_result_report.md"), "w") as f:
    f.write("""# 模型服务延迟优化结果报告
作者：林晓宇
时间：第4周

## 结论
经过两周迭代，P99 延迟从 420ms 降至 165ms，超过 SLA 目标（200ms）。
吞吐量提升 38%，超出预期 35%。

## 主要措施
1. 异步预加载：冷启动时间降低 60%（林晓宇实现）
2. KV Cache 优化：显存碎片减少 40%（林晓宇设计，张伟实现）
3. 动态批处理：吞吐提升核心手段（林晓宇主导设计）

## 影响范围
已推广至 3 个业务线（推荐、搜索、内容审核），减少 GPU 资源消耗约 20%。

## 后续
林晓宇将方案沉淀为平台标准，推动其他服务复用。
""")

# Week4 meeting - LLM eval framework CI integration (user drove)
with open(os.path.join(BASE, "feishu_export/meeting_notes/week4/llm_eval_ci_integration_0124.md"), "w") as f:
    f.write("""# LLM 评测框架 CI 集成会 0124
参会：林晓宇、DevOps 团队（韩磊）、算法团队（郑涛）
组织：林晓宇

## 内容
林晓宇介绍 CI 集成方案，阐述触发时机和回归基准选择逻辑。
韩磊确认 Pipeline 配置，与林晓宇对齐触发条件。
郑涛验收评测维度覆盖情况，确认满足需求。

## 结论
CI 集成完成，覆盖 5 个核心模型，自动化回归测试上线。
林晓宇推动评测框架成为团队标准工具。
""")

# Distractor: AI-generated meeting summary with inflated claims
with open(os.path.join(BASE, "feishu_export/meeting_notes/week4/ai_summary_weekly_0125.md"), "w") as f:
    f.write("""# [AI 自动摘要] 本周工作汇总 0125
（由会议助手自动生成，未经人工校验）

## 本周重点（系统生成）
- 林晓宇完成了所有基础设施优化工作
- 林晓宇主导了数据管道 v3 重构（注：实际为王芳负责）
- 林晓宇推动了 K8s 扩容（注：实际为陈刚负责）
- 模型质量指标体系全面上线

## 注意
以上内容为 AI 自动整理，可能存在归因错误，请以原始会议纪要为准。
""")

# Personal draft - user's own notes
with open(os.path.join(BASE, "feishu_export/personal_drafts/weekly_notes_rough.md"), "w") as f:
    f.write("""# 个人工作草稿（非正式）
林晓宇个人记录

第1周：延迟优化方案终于评审过了，异步预加载写完了，感觉 KV Cache 那块还得再磨一磨
第2周：LLM 评测框架启动，跟数据团队对齐了格式，demo 跑通
第3周：质量治理指标评审，陈总那边有些新需求，下周更新
第4周：延迟降到 165ms 了！！比目标还好，评测框架 CI 也上线了
""")

# Distractor: archive docs from previous quarter (should not be main content)
with open(os.path.join(BASE, "feishu_export/archive/q2_review/q2_summary_team.md"), "w") as f:
    f.write("""# Q2 团队总结（归档）
时间：上季度（非本月范围）
作者：团队整体

## 内容
Q2 主要完成了基础平台升级和数据治理专项。
（此为历史文档，与本月回顾无关）
""")

with open(os.path.join(BASE, "feishu_export/archive/q1_review/q1_kpi_team.md"), "w") as f:
    f.write("""# Q1 KPI 盘点（归档）
（历史文档）
""")

# Distractor: shared team doc user is NOT owner of
with open(os.path.join(BASE, "feishu_export/shared_team_docs/team_okr_q3.md"), "w") as f:
    f.write("""# 团队 OKR Q3（共享文档）
负责人：陈刚（基础设施）

## 团队目标
O1: 平台稳定性 99.9%
O2: 成本降低 15%
O3: 新功能交付周期缩短 20%

（林晓宇非此文档负责人）
""")

with open(os.path.join(BASE, "feishu_export/wiki/platform_infra/k8s_scaling_guide.md"), "w") as f:
    f.write("""# K8s 扩容操作手册
作者：陈刚
内容：K8s 节点扩容标准操作流程（与林晓宇工作无直接关联）
""")

with open(os.path.join(BASE, "feishu_export/wiki/platform_infra/storage_migration_notes.md"), "w") as f:
    f.write("""# 存储迁移笔记
作者：刘洋
内容：S3 至内部对象存储迁移过程记录（与林晓宇工作无直接关联）
""")

# Distractor: broad discussion doc
with open(os.path.join(BASE, "feishu_export/shared_team_docs/tech_radar_discussion.md"), "w") as f:
    f.write("""# 技术雷达讨论记录
参与：全组讨论，无具体负责人
内容：对 Rust、WebAssembly、向量数据库的泛泛讨论，无 action item，无 owner。
林晓宇参与了部分讨论但无具体主张被采纳记录。
""")

print("Workspace generated successfully.")
print(f"Files created in {BASE}/feishu_export/")