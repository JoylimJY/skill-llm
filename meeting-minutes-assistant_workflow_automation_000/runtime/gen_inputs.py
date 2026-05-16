import os
import random

random.seed(42)

base = "/workspace"

# --- Directory structure with distractor files ---
dirs = [
    "scripts",
    "archive/2023/Q2",
    "archive/2023/Q3",
    "archive/2024/Q1",
    "templates",
    "reports/weekly",
    "reports/monthly",
    "config",
    "logs",
    "assets/images",
    "assets/docs",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# --- Distractor files ---
distractors = {
    "archive/2023/Q2/meeting_20230601.txt": "Q2会议记录（旧版）\n张三、李四参会。讨论了市场策略。",
    "archive/2023/Q3/minutes_draft.md": "# 草稿\n这是一个未完成的纪要草稿。",
    "archive/2024/Q1/q1_summary.txt": "Q1总结：完成了产品路线图规划，待Q2跟进。",
    "templates/meeting_template.md": "# 会议纪要模板\n## 基本信息\n## 议程\n## 待办",
    "reports/weekly/week42.md": "## 本周进展\n- 完成了用户调研\n- 启动了AB测试",
    "reports/monthly/oct_report.md": "## 十月月报\n收入环比增长12%。",
    "config/app_config.yaml": "app:\n  name: meeting-assistant\n  version: 1.0.0\n  debug: false",
    "config/channels.json": '{"channels": ["wecom", "feishu", "ddingtalk"]}',
    "logs/push_history.log": "2024-10-01 10:00:00 [INFO] Pushed to wecom\n2024-10-02 11:30:00 [INFO] Pushed to feishu",
    "assets/docs/onboarding.md": "# 入职指引\n欢迎加入团队！请阅读以下文档。",
    "assets/docs/style_guide.md": "# 文档规范\n所有文档使用Markdown格式。",
    "reports/weekly/week43_notes.txt": "注意：本周会议记录尚未整理。请跟进。",
}

for rel_path, content in distractors.items():
    full_path = os.path.join(base, rel_path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# --- The actual messy raw meeting notes the agent must process ---
raw_notes = """
产品团队Q3规划会议 - 2024年10月15日

参与人员: 王磊（产品负责人）、陈晓（技术负责人）、刘芳（设计师）、赵强（运营）、林默（记录）

开场: 王磊主持，提到本次会议主要讨论Q3遗留问题和Q4规划

话题1: 用户增长
王磊说上个季度用户增长不达预期，只达成了70%目标。需要深入分析原因。
陈晓认为是因为注册流程太复杂，用户流失在注册第三步。
刘芳说她已经有了新的注册流程设计稿，下周可以提交给陈晓评审。
决定: 简化注册流程，目标是将注册完成率从40%提升到65%。
行动项: 刘芳在10月22日之前提交新注册流程设计稿给陈晓审核。

话题2: 新功能规划
赵强提出用户反馈最多的是缺少数据导出功能。
陈晓说开发数据导出功能大概需要两周时间。
王磊表示这个功能优先级很高，要排在Q4第一个迭代。
决定: Q4第一个迭代（10月28日开始）优先开发数据导出功能。
行动项: 陈晓需要在10月20日前给出数据导出功能的技术方案。
行动项: 赵强负责收集用户对导出格式的偏好（CSV/Excel），截止10月18日。

话题3: 运营活动
赵强汇报了上季度两次运营活动效果一般，用户参与度低。
刘芳建议改进活动页面的视觉设计。
王磊说要重新评估活动策略，引入更多激励机制。
决定: 下季度运营活动引入积分奖励机制。
行动项: 赵强制定新的积分奖励方案，截止11月1日。
行动项: 刘芳设计积分活动页面，截止11月8日。

其他事项:
- 下次会议安排在10月29日，同样由王磊主持
- 所有行动项负责人需要在各自截止日期前同步进展

散会。
"""

with open(os.path.join(base, "q3_planning_raw_notes.txt"), "w", encoding="utf-8") as f:
    f.write(raw_notes)

print("Workspace generated successfully.")
print(f"Raw notes file: {os.path.join(base, 'q3_planning_raw_notes.txt')}")