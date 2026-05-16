import os
import json
import random

random.seed(42)

workspace = "/workspace"

# Create deeply nested directory structure with distractor files
dirs = [
    "platform/backend/services/dialogue",
    "platform/backend/services/user",
    "platform/backend/models",
    "platform/frontend/components",
    "platform/frontend/pages",
    "platform/data/raw_dialogues",
    "platform/data/processed",
    "platform/data/archive",
    "platform/config",
    "platform/docs",
    "platform/tests/unit",
    "platform/tests/integration",
    "scripts/migration",
    "scripts/analysis",
    "reports/weekly",
    "reports/monthly",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "platform/backend/services/user/user_service.py": '''
class UserService:
    def get_user(self, user_id: str):
        return {"id": user_id, "name": "Anonymous", "level": 1}
    def update_progress(self, user_id: str, stage: str):
        pass
''',
    "platform/backend/models/session.py": '''
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CoachingSession:
    session_id: str
    user_id: str
    start_time: datetime
    turns: list
    stage_classification: str = "unknown"
''',
    "platform/backend/services/dialogue/router.py": '''
# Route incoming messages to appropriate coaching modules
ROUTING_RULES = {
    "confusion": "clarity_module",
    "anger": "emotion_module",
    "attachment": "release_module",
}
''',
    "platform/frontend/components/ChatBubble.jsx": '''
export const ChatBubble = ({ message, role }) => (
  <div className={`bubble ${role}`}>
    <p>{message.content}</p>
    <span className="timestamp">{message.ts}</span>
  </div>
);
''',
    "platform/frontend/pages/session.js": '''
// Session page - renders coaching dialogue
import { ChatBubble } from "../components/ChatBubble";
export default function SessionPage({ sessionId }) {
  return <div className="session-container" />;
}
''',
    "platform/config/app_config.yaml": '''
app:
  name: MindfulPath
  version: 2.1.0
  environment: production
dialogue:
  max_turns: 20
  timeout_seconds: 300
  language: zh-CN
''',
    "platform/docs/api_spec.md": '''
# MindfulPath API Specification
## POST /session/start
Creates a new coaching session.
## POST /session/{id}/message
Sends a user message and gets coach response.
## GET /session/{id}/summary
Returns session summary with stage classification.
''',
    "platform/data/processed/session_stats.json": json.dumps({
        "total_sessions": 1247,
        "avg_turns_per_session": 8.3,
        "stage_distribution": {"beginner": 0.6, "intermediate": 0.3, "advanced": 0.1},
        "avg_response_length_chars": 312
    }, indent=2),
    "platform/data/archive/old_format_v1.json": json.dumps([
        {"role": "coach", "text": "你好，有什么可以帮你的？", "quality": "unknown"},
        {"role": "user", "text": "我最近很烦躁", "quality": "unknown"},
    ], indent=2),
    "scripts/migration/migrate_v1_to_v2.py": '''
import json
import sys

def migrate(input_file, output_file):
    with open(input_file) as f:
        data = json.load(f)
    # TODO: implement migration logic
    print(f"Migrating {len(data)} records")

if __name__ == "__main__":
    migrate(sys.argv[1], sys.argv[2])
''',
    "scripts/analysis/quality_metrics.py": '''
# Placeholder for quality metrics calculation
# Metrics: avg_response_length, question_ratio, rejection_count
def calculate_metrics(dialogues):
    return {}
''',
    "reports/weekly/week_23_summary.txt": '''
Week 23 Coaching Quality Report
================================
Sessions reviewed: 48
Flagged for review: 12
Common issues: responses too long, coach not asking follow-up questions
Action items: review dialogue guidelines, retrain on new examples
''',
    "reports/monthly/may_analysis.csv": '''
date,sessions,avg_score,flagged
2024-05-01,42,3.2,8
2024-05-08,51,3.5,6
2024-05-15,38,2.9,11
2024-05-22,55,3.8,4
''',
    "platform/tests/unit/test_router.py": '''
import pytest

def test_routing_anger():
    from platform.backend.services.dialogue.router import ROUTING_RULES
    assert ROUTING_RULES["anger"] == "emotion_module"

def test_routing_attachment():
    from platform.backend.services.dialogue.router import ROUTING_RULES
    assert ROUTING_RULES["attachment"] == "release_module"
''',
    "platform/tests/integration/test_session_flow.py": '''
import pytest

def test_full_session_flow():
    # Integration test - requires running server
    pass
''',
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# THE MAIN PROBLEM: Raw messy dialogue samples that need auditing and remediation
# These are intentionally flawed dialogues that violate the SKILL.md principles
raw_dialogues = [
    {
        "id": "dlg_001",
        "context": "用户说最近工作压力很大，总是控制不住发脾气，事后又很后悔",
        "user_message": "我就是脾气不好，可能天生这样，改不了了",
        "flawed_coach_response": "你说得对，有些人天生脾气就急一些。不过脾气不好其实也不一定是坏事，说明你是个直性子。我见过很多成功人士脾气都很大的，比如乔布斯。其实你可以试试每天早上冥想五分钟，晚上睡前记三件感恩的事，慢慢就会好的。还有就是要多运动，运动能释放多巴胺。另外饮食也很重要，少吃辛辣……",
        "metadata": {"session_id": "s_2024_0312", "user_stage_guess": "unknown", "flagged": True}
    },
    {
        "id": "dlg_002",
        "context": "用户在讨论一段让她很痛苦的感情，男友经常冷落她，她说离不开",
        "user_message": "我知道他对我不好，但我就是放不下，我是不是有问题？",
        "flawed_coach_response": "你没有问题，这很正常。爱情本来就是复杂的。从心理学角度来说，这可能是依恋焦虑型人格，你小时候可能缺乏安全感。你需要先爱自己，我给你推荐一本书《被讨厌的勇气》，还有就是你要设立边界，告诉他你的底线，如果他还是这样，你就要考虑离开。你值得被好好对待的！我相信你能做到！",
        "metadata": {"session_id": "s_2024_0401", "user_stage_guess": "unknown", "flagged": True}
    },
    {
        "id": "dlg_003",
        "context": "用户说自己修行了几年，感觉没什么进步，打坐时念头很多控制不住",
        "user_message": "我打坐的时候脑子里一直有各种念头，怎么都控制不住，是不是我根本没有修行的天赋？",
        "flawed_coach_response": '打坐时有念头是完全正常的！所有人都这样。你的目标不应该是"没有念头"，而是觉察念头。你可以用数息法，从一数到十，数乱了重新开始。还可以用观息法，专注于鼻尖的呼吸感觉。另外，你可以先从短时间开始，每次5分钟，慢慢增加。修行是一辈子的事，不要着急，放轻松。',
        "metadata": {"session_id": "s_2024_0415", "user_stage_guess": "unknown", "flagged": True}
    },
    {
        "id": "dlg_004",
        "context": "用户抱怨同事总是抢功劳，自己做了很多却得不到认可，非常愤怒",
        "user_message": "凭什么他能这样？这不公平，我就是咽不下这口气",
        "flawed_coach_response": "我理解你的感受，换谁都会生气的。你的愤怒是完全正当的。你可以去找你的领导反映这个情况，把证据整理好，比如邮件记录、会议记录等。同时你也要学会表达自己，不要总是隐忍。职场就是这样，你要懂得保护自己的权益……",
        "metadata": {"session_id": "s_2024_0502", "user_stage_guess": "unknown", "flagged": True}
    },
    {
        "id": "dlg_005",
        "context": "用户说自己总是拖延，什么事情都完不成，觉得自己很废，已经自我怀疑很久了",
        "user_message": "我知道自己应该去做，但就是做不到，我告诉自己很多次了没用",
        "flawed_coach_response": "拖延症很多人都有，你不是一个人。研究表明，拖延往往和完美主义有关。你可以试试番茄工作法——25分钟专注，5分钟休息。还可以把大任务拆解成小步骤。另外，给自己设一个奖励机制，完成了就奖励自己。最重要的是要对自己有耐心，改变需要时间的……",
        "metadata": {"session_id": "s_2024_0518", "user_stage_guess": "unknown", "flagged": True}
    },
]

# Write the raw flawed dialogues to the raw_dialogues directory
with open(os.path.join(workspace, "platform/data/raw_dialogues/flawed_samples.json"), "w", encoding="utf-8") as f:
    json.dump(raw_dialogues, f, ensure_ascii=False, indent=2)

# Also write a separate context document about the platform's coaching philosophy (partially described, vague)
coaching_brief = """
MindfulPath Coaching Quality Standards - Internal Brief
=======================================================

Our coaching AI has been generating responses that our senior practitioners find 
"ineffective" and "too advice-heavy." The dialogue samples in flawed_samples.json 
need to be reviewed and corrected according to the standards described in SKILL.md.

For each dialogue, the output should capture:
1. What the user is truly stuck on (their core attachment point)
2. A quality-compliant remediated coach response
3. The practitioner development stage classification
4. Whether the original response violated any key principles and which ones

The remediated responses must demonstrate the "force/impact" principle with both 
its required components. They must also adhere strictly to the brevity and 
questioning technique requirements.

Output file: dialogue_audit_report.json
Location: platform/data/processed/dialogue_audit_report.json
"""

with open(os.path.join(workspace, "platform/docs/coaching_quality_brief.md"), "w", encoding="utf-8") as f:
    f.write(coaching_brief)

# Write the SKILL.md into the workspace
skill_md = """---
name: buddha-companion
description: >
  佛法实践与智慧对话助手。用于：(1) 帮用户理解佛法核心义理（缘起性空、无我、中道），
  (2) 在对话中引导用户看到自己的执着，(3) 以有力道的方式点拨，而非说教。
  当用户问佛法问题、修行困惑、或在生活中遇到境界时触发。
---

# 佛法实践助手

## 核心理念

### 缘起性空
- 诸法因缘生，无自性
- 既不是有，也不是无——是"缘起有，自性空"
- 因果恰恰建立在无自性上

### 无我
- 没有独立不变的"实体我"
- 但有因缘和合的"假我"
- 轮回的是"相续"，不是"我"

### 中道
- 超越有、无两边
- 不执着于"空"，也不执着于"有"

---

## 核心经典要义

| 经典 | 核心 |
|------|------|
| 金刚经 | 应无所住而生其心 |
| 圆觉经 | 知幻即离，不作方便 |
| 坛经 | 本来无一物，何处惹尘埃 |
| 楞严经 | 客尘比喻 |
| 法华经 | 三车喻，会三归一 |
| 华严经 | 一真法界，缘起无尽 |

---

## 心法：止观功夫

### 止
- 念头起来时知道，不跟着跑
- 不是压制不起念，是"看到"念头

### 观
- 如实看到，不评判
- 修的是"看到"，不是"做到"

### 觉察进阶
- 初级：知道自己在生气
- 中级：知道为什么生气
- 高级：看着生气起来，看着它走

---

## 对话力：力道的两个核心

### 1. 方向
- 指向对方的执着点
- 不是四面八方说，是靶心在哪打哪
- 问：他在卡在哪里？

### 2. 边界
- 在对方卡住的地方发力
- 不到边界就是隔靴搔痒
- 问：现在是不是卡住了？

### 心法提醒

- **少说**：克制表达的冲动
- **等**：让子弹飞一会儿
- **问**：把球踢回去
- **指向核心**：一句话点到

### 提醒自己

- 不是"证明自己懂"
- 是"帮对方看到"
- 带着慈悲，不是说服
- 不评判，不急着给答案

---

## 应用：帮用户提升心性

### 怎么做

1. 看到用户在抓什么
2. 轻轻点一下，不啰嗦
3. 用问题让他自己想
4. 给他空间，不塞答案

### 不做什么

- 不评判
- 不急着给答案
- 不证明自己厉害
- 不渡己姿态

---

## 每日自检

- 今天说话有没有废话太多？
- 刚才那句话是"证明自己"还是"帮对方"？
- 用户卡在哪，我有没有看到？

### 阶段进步

- 从能给答案 → 能问问题
- 从说很多 → 说一句
- 从急着回应 → 等一等

---

## 关键原则

**佛法不是知识，是功夫。**
知道"无我"不算数，需要"看到"无我。
功夫是"回过来做"——不是在外面修，是向内看。
"""

with open(os.path.join(workspace, "SKILL.md"), "w", encoding="utf-8") as f:
    f.write(skill_md)

print("Workspace generated successfully.")
print(f"Files created:")
for root, dirs_list, files in os.walk(workspace):
    for file in files:
        filepath = os.path.join(root, file)
        print(f"  {filepath}")