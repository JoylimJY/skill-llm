import os
import random
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# --- Directory structure ---
dirs = [
    "memory/tasks",
    "memory/archive",
    "memory/notes",
    "models/retraining",
    "models/evaluation",
    "data/raw",
    "data/processed",
    "scripts/pipeline",
    "scripts/monitoring",
    "logs/training",
    "logs/evaluation",
    "reports/weekly",
    "reports/monthly",
    "config",
    "notebooks",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractors = {
    "models/retraining/run_20240101.log": "Training run: loss=0.34, val_loss=0.38\nEpochs: 50\nStatus: complete",
    "models/retraining/run_20240215.log": "Training run: loss=0.29, val_loss=0.31\nEpochs: 50\nStatus: complete",
    "models/evaluation/metrics_q1.json": '{"precision": 0.87, "recall": 0.82, "f1": 0.845}',
    "models/evaluation/metrics_q2.json": '{"precision": 0.89, "recall": 0.85, "f1": 0.870}',
    "data/raw/dataset_v3.csv": "id,feature1,feature2,label\n1,0.5,1.2,1\n2,0.3,0.9,0\n3,1.1,2.3,1",
    "data/processed/train_split.csv": "id,feature1,feature2,label\n1,0.5,1.2,1",
    "data/processed/val_split.csv": "id,feature1,feature2,label\n2,0.3,0.9,0",
    "scripts/pipeline/retrain.py": "#!/usr/bin/env python3\n# Retraining pipeline\nprint('retraining...')",
    "scripts/pipeline/preprocess.py": "#!/usr/bin/env python3\n# Preprocessing\nprint('preprocessing...')",
    "scripts/monitoring/drift_detector.py": "#!/usr/bin/env python3\n# Drift detection\nprint('checking drift...')",
    "logs/training/2024-06-01.log": "[INFO] epoch 1/50 loss=0.55\n[INFO] epoch 50/50 loss=0.34",
    "logs/evaluation/2024-06-05.log": "[INFO] evaluation complete. F1=0.845",
    "reports/weekly/week_22.md": "# Week 22 Summary\n- Retrained model on new data\n- Validation F1 improved",
    "reports/monthly/june_2024.md": "# June 2024\n- 3 retraining cycles completed\n- Average F1: 0.86",
    "config/model_config.yaml": "model_type: xgboost\nmax_depth: 6\nlearning_rate: 0.1\nn_estimators: 200",
    "config/pipeline_config.yaml": "data_source: s3://ml-data/raw\noutput_path: models/\nschedule: weekly",
    "notebooks/eda_v2.ipynb": '{"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}',
    "memory/notes/team_standup_2024-06-03.md": "# Standup 2024-06-03\n- Model drift detected on feature2\n- Need to retrain before July",
    "memory/notes/team_standup_2024-06-10.md": "# Standup 2024-06-10\n- New labeled data batch ready\n- Pipeline scripts updated",
    "memory/archive/old_experiment_notes.md": "# Archived: Experiment Alpha\nTried LSTM approach, abandoned due to latency.",
}

for filepath, content in distractors.items():
    full_path = WORKSPACE / filepath
    full_path.write_text(content, encoding="utf-8")

# --- MEMORY.md: existing file with "待办提醒" section but no reference to the new plan yet ---
memory_md_content = """\
# MEMORY.md

## 关键上下文
- 团队正在推进 MLOps 自动化改造
- 模型重训频率：每4周一次
- 当前负责人：数据团队

## 待办提醒
- 数据漂移监控 → 见 memory/tasks/drift-monitor-plan.md
- 季度报告整理 → 截止 2024-07-15

## 近期记录
- 2024-06-10：新标注数据批次已就绪，共 12,000 条
- 2024-06-05：Q2 评估完成，F1=0.870
- 2024-05-28：发现 feature2 数据漂移，触发重训流程

## 长期背景
- 使用 XGBoost 作为主模型
- 数据来源：用户行为日志（每日更新）
- 部署环境：内网推理服务，SLA 要求 <50ms
"""
(WORKSPACE / "memory" / "MEMORY.md").write_text(memory_md_content, encoding="utf-8")

# --- CURRENT_STATE.md: existing file ---
current_state_content = """\
# CURRENT_STATE.md

## 今日日期
2024-06-17

## 今日目标
- 完成 feature2 的重训数据集准备
- 检查 pipeline 配置是否与新数据兼容

## 进行中的工作
- 模型重训计划（待启动）
- 数据质量监控持续运行中

## 最近决策
- 决定将重训窗口从4周缩短为3周（基于漂移分析）
- 新标注数据将在本周纳入训练集
"""
(WORKSPACE / "memory" / "CURRENT_STATE.md").write_text(current_state_content, encoding="utf-8")

# --- EXISTING plan file that has a stale/completed phase needing rollover ---
# This plan exists for "drift-monitor" and has a completed phase that needs archiving + new phase
drift_plan_content = """\
# 数据漂移监控计划

## 目标
持续监控生产模型的特征漂移，确保在漂移超出阈值前触发重训。

## 策略/原则
1. 每天检查漂移分数，阈值 > 0.15 时报警
2. 每周汇总漂移趋势，生成报告
3. 发现漂移立即通知数据团队
4. 不依赖人工判断，全自动触发
5. 保持监控脚本版本可追溯

---

## 当前阶段：基线建立（2024-06-03 - 2024-06-07）

### 阶段目标
采集7天基线数据，确定各特征的正常漂移范围，建立告警阈值。

### 具体任务
- [x] 部署 drift_detector.py 到生产环境
- [x] 采集 feature1、feature2、feature3 基线分布
- [x] 设定初始阈值：feature1=0.12, feature2=0.18, feature3=0.10
- [x] 验证告警通知链路（邮件 + Slack）
- [x] 输出基线报告 baseline_drift_report.md

### 复盘检查点（2024-06-07）
- 对比阶段目标，完成率多少？
- 哪些任务效果好/差？
- 下一阶段方向需要调整吗？

---

## 历史归档
（暂无）

---
*创建：2024-06-03*
*当前阶段截止：2024-06-07*
"""
(WORKSPACE / "memory" / "tasks" / "drift-monitor-plan.md").write_text(drift_plan_content, encoding="utf-8")

# --- A second unrelated plan file as distractor ---
other_plan_content = """\
# 季度报告自动化计划

## 目标
自动生成每季度的模型性能报告，减少人工整理时间。

## 策略/原则
1. 数据来源统一走数据仓库 API
2. 报告格式固定，不允许临时修改模板

---

## 当前阶段：模板设计（2024-06-10 - 2024-06-14）

### 阶段目标
确定报告模板结构，与团队对齐格式标准。

### 具体任务
- [x] 收集历史手工报告样本
- [ ] 设计 Jinja2 模板
- [ ] 与团队 review 模板草稿

### 复盘检查点（2024-06-14）
- 对比阶段目标，完成率多少？
- 哪些任务效果好/差？
- 下一阶段方向需要调整吗？

---

## 历史归档
（暂无）

---
*创建：2024-06-10*
*当前阶段截止：2024-06-14*
"""
(WORKSPACE / "memory" / "tasks" / "quarterly-report-plan.md").write_text(other_plan_content, encoding="utf-8")

print("Workspace generated successfully.")
print("Files created:")
for p in sorted(WORKSPACE.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(WORKSPACE)}")