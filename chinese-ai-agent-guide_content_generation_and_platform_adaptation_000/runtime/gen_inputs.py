import os
import random

random.seed(42)

# Create deeply nested workspace structure with distractor files
dirs = [
    "workspace/product/docs",
    "workspace/product/specs",
    "workspace/marketing/drafts",
    "workspace/marketing/archive",
    "workspace/marketing/templates",
    "workspace/ops/logs",
    "workspace/ops/configs",
    "workspace/user_feedback/raw",
    "workspace/user_feedback/processed",
    "workspace/social/scheduled",
    "workspace/social/published",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# Distractor files
distractors = {
    "workspace/product/docs/roadmap_2024.txt": "Q1: 发布测试版\nQ2: 付费功能上线\nQ3: iOS 端适配\nQ4: 海外版探索",
    "workspace/product/specs/tech_spec_v2.md": "# 技术规格\n## 后端\n- Python 3.11\n- FastAPI\n## 前端\n- React 18\n- TypeScript",
    "workspace/product/specs/api_schema.json": '{"version": "1.0", "endpoints": ["/chat", "/history", "/export"]}',
    "workspace/marketing/archive/old_campaign_jan.txt": "1月推广文案（已归档）\n用AI学习，效率翻倍。\n——市场团队",
    "workspace/marketing/templates/email_template.html": "<html><body><h1>{{title}}</h1><p>{{body}}</p></body></html>",
    "workspace/marketing/drafts/weibo_ideas.txt": "想法1: 用数据说话\n想法2: KOL合作\n想法3: 话题挑战赛",
    "workspace/ops/logs/deploy_20240601.log": "[INFO] Deploy started\n[INFO] Health check passed\n[INFO] Deploy complete",
    "workspace/ops/configs/nginx.conf": "server { listen 80; server_name example.com; }",
    "workspace/user_feedback/processed/batch_001.csv": "id,user,score\n1,张三,4\n2,李四,5\n3,王五,3",
    "workspace/social/published/xiaohongshu_march.txt": "（已发布3月笔记）",
    "workspace/social/scheduled/jike_queue.txt": "（待发布即刻内容列表）",
}
for path, content in distractors.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# THE REAL INPUTS

# 1. Raw product notes (messy, unstructured, internal-speak)
raw_notes = """产品更新说明（内部流转版）- 请勿直接外发

本次更新核心功能：
- 新增「错题本」功能：AI自动识别用户做错的题目并归档，每周生成复习计划
- 「对话式答疑」升级：现在支持连续追问，AI会记住上下文，不再鸡同鸭讲
- 学习报告可导出 PDF，家长可直接查看孩子进度
- 界面响应速度提升了大约40%，卡顿问题基本解决

用户痛点解决情况：
之前最大的吐槽是AI答完一道题就忘了刚才说了什么，现在修了。
另外导出报告是付费用户呼声最高的功能，终于上了。

适用人群：初高中生，备考党，家长监督型学习场景

注意：错题本功能目前仅支持数学和英语，其他科目Q3上线
"""
with open("workspace/product/docs/update_notes_v1.1_internal.txt", "w", encoding="utf-8") as f:
    f.write(raw_notes)

# 2. User feedback messages with implicit sentiment
feedback_messages = """=== 用户反馈原文（待回复）===

[反馈编号 F-2024-089]
用户名：备考小刘
内容：导出报告我试了，格式还行吧。

[反馈编号 F-2024-091]  
用户名：高三家长王阿姨
内容：先这样，我让孩子用两天再说。

"""
with open("workspace/user_feedback/raw/pending_replies_20240615.txt", "w", encoding="utf-8") as f:
    f.write(feedback_messages)

# 3. Task brief for the agent (the actual prompt context file)
task_brief = """任务说明
=========
社媒运营需要根据最新产品更新，输出以下内容：

1. 小红书笔记一篇
2. 即刻动态一条
3. 微信私域消息（分条版本）
4. 针对 F-2024-089 和 F-2024-091 两条用户反馈的回复草稿

原始素材见：
- workspace/product/docs/update_notes_v1.1_internal.txt
- workspace/user_feedback/raw/pending_replies_20240615.txt
"""
with open("workspace/marketing/drafts/social_task_brief.txt", "w", encoding="utf-8") as f:
    f.write(task_brief)

print("Workspace generated successfully.")