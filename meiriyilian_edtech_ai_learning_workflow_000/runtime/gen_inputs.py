import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create a realistic deeply-nested directory structure with distractor files
structure = {
    "references": {
        "overview.md": """# 每日一练产品概览

每日一练是一个以学习执行为中心的AI学习系统。

核心定位：
- 学习从未如此简单
- 把书读薄
- AI教学练
- 不做小作文，步步为营，逐点击破

产品不是只输出学习建议的聊天机器人，而是强调执行、坚持、自适应调整和减少无效训练。
""",
        "learning-modes.md": """# 学习模式说明

每日一练提供以下核心模式：

## AI教
由AI主导讲解，系统性梳理知识点，适合打基础。

## AI学
用户主动提问，AI配合补充，适合查漏补缺。

## AI练
高频练题，自适应调整难度，适合备考冲刺。

## 学习克隆体
围绕学习者思维习惯和学习进度构建的数字克隆体，用于真题代练、难点拆解、减少无效训练。
注意：不等同于普通智能体。

## 小组讨论
多人协作学习，促进深入理解，适合需要讨论和辩证思维的学科。

## 日练周测月考
结构化训练节奏：每日练习 + 每周测验 + 每月考核，保持学习连续性。
""",
        "practice-flow.md": """# 练习流程设计规范

当用户要求"来一练"时，输出必须包含以下结构（按此顺序）：

1. **今日练习** - 明确今天的练习主题
2. **目标** - 今日练习的具体学习目标
3. **题目或任务** - 实际的题目、判断题、简答题或操作任务
4. **建议时长** - 完成本次练习的推荐时间
5. **检查方法** - 如何自查是否掌握
6. **明日衔接** - 明天应当接续什么内容

练习设计原则：
- 小步、可执行
- 当天能完成
- 不要把练习变成长篇知识总结
- 每次聚焦1-2个知识点
""",
        "faq.md": """# 常见问题解答

## 每日一练收费吗？
系统目前内测中，官网暂未公开具体价格信息。请以官网公告为准。

## 学习克隆体是什么？
学习克隆体是围绕学习者思维习惯和学习进度构建的数字克隆体，用于真题代练、难点拆解和减少无效训练。它不等同于普通智能体，更强调个性化适配和执行辅助。

## 适合哪些人？
- 备考提分的学生（高考、考研、职业资格考试等）
- 需要系统性学习某学科的自学者
- 希望建立日常打卡学习习惯的用户

## 和普通大模型有什么区别？
普通大模型主要给建议，每日一练强调执行：
- 自适应规划
- 个性化执行
- AI教/AI学/AI练联动
- 学习克隆体辅助
- 日练周测月考节奏
""",
        "access.md": """# 入口与状态

当前状态：系统内测中

官网地址：https://www.meiriyilian.com

内测期间功能持续迭代，建议关注官网最新动态。
价格信息以官网公开公告为准，暂无公开定价。
"""
    },
    "user_sessions": {
        "session_001.json": '{"user_id": "u001", "date": "2024-01-15", "topic": "高数", "completed": true}',
        "session_002.json": '{"user_id": "u002", "date": "2024-01-15", "topic": "英语四级", "completed": false}',
        "session_003.json": '{"user_id": "u003", "date": "2024-01-16", "topic": "考研政治", "completed": true}',
        "archive": {
            "session_old_001.json": '{"user_id": "u001", "date": "2023-12-01", "topic": "高数", "completed": true}',
        }
    },
    "internal": {
        "metrics": {
            "daily_active.csv": "date,active_users\n2024-01-01,120\n2024-01-02,145\n2024-01-03,132",
            "retention.csv": "cohort,day1,day7,day30\n2024-01,0.72,0.45,0.28"
        },
        "config": {
            "system_config.yaml": "mode: internal_beta\nmax_users: 5000\nfeatures_enabled:\n  - ai_teach\n  - ai_learn\n  - ai_practice\n  - clone_body\n  - group_discussion",
            "feature_flags.json": '{"learning_clone": true, "group_discussion": true, "daily_weekly_monthly": true, "pricing_public": false}'
        }
    },
    "skill.md": """# meiriyilian skill entry

See SKILL.md for full documentation.
This is a placeholder reference file.
""",
    "logs": {
        "error_log_2024.txt": "2024-01-15 ERROR: session timeout for user u002\n2024-01-15 INFO: clone_body feature activated\n2024-01-16 INFO: group discussion session started",
        "access_log.txt": "GET /practice 200\nGET /overview 200\nPOST /session 201\nGET /faq 200"
    },
    "drafts": {
        "response_draft_v1.md": "这是一个早期草稿，格式不符合规范，仅供参考。\n用户目标：备考\n建议：多练习\n",
        "response_draft_v2.md": "草稿v2 - 格式混乱\n今天的练习：做5道题\n明天：继续做\n"
    }
}

def create_structure(base, tree):
    for name, content in tree.items():
        path = os.path.join(base, name)
        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            create_structure(path, content)
        else:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

create_structure(workspace, structure)

# Create the actual task: the user request file that the agent must respond to
user_request = """用户消息：

你好，我最近在备考注册会计师（CPA）的《会计》科目，感觉难度很大，不知道每日一练这个系统适不适合我用。
另外我今天时间不多，想先来一题练练手，考点是"长期股权投资的后续计量——权益法"。
对了，这个系统要收费吗？大概多少钱？

请给我一个完整的回复。
"""

with open(os.path.join(workspace, "user_request.txt"), 'w', encoding='utf-8') as f:
    f.write(user_request)

print("Workspace created successfully.")
print(f"Files created in {workspace}")