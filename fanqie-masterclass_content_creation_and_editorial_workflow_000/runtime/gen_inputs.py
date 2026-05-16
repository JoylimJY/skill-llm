import os
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

# --- Directory structure with distractors ---
dirs = [
    "workspace/drafts/chapter1",
    "workspace/drafts/chapter2",
    "workspace/drafts/archive",
    "workspace/references",
    "workspace/notes/research",
    "workspace/notes/ideas",
    "workspace/output",
    "workspace/tools/scripts",
    "workspace/tools/templates",
    "workspace/review/pending",
    "workspace/review/done",
]
for d in dirs:
    os.makedirs(os.path.join("/", d), exist_ok=True)

# --- Distractor files ---
distractors = {
    "workspace/drafts/chapter1/draft_v1.txt": "第一章草稿：主角是一个普通上班族，某天发现公司老板是自己的前男友……",
    "workspace/drafts/chapter1/draft_v2.txt": "修改版：加强冲突，第一段改为倒叙手法。",
    "workspace/drafts/chapter2/outline_raw.txt": "大纲：1-开端 2-矛盾 3-高潮 4-结局\n角色：女主林晓晓，男主陆霆烨",
    "workspace/drafts/archive/old_title_list.txt": "备用标题（废弃）：\n离婚协议签了，前夫跪地求我回头\n婆婆叫我卷铺盖，我卷走了她儿子\n",
    "workspace/references/platform_notes.txt": "番茄平台注意事项：日更2000字，完读率要超过70%，避免宫斗元素。",
    "workspace/references/competitor_analysis.txt": "竞品分析：七猫、掌阅、起点对比，番茄以免费+广告为主，用户粘性高。",
    "workspace/notes/research/reader_survey.txt": "读者调研数据（虚构）：25-35岁女性占比最高，偏好都市爽文，完读率与第一段强度正相关。",
    "workspace/notes/ideas/raw_seeds.txt": "脑洞种子（未处理）：\n- 外卖员送餐送到了自己的葬礼现场\n- 保洁阿姨发现总裁的秘密\n- 闪婚对象是自己的债主",
    "workspace/notes/ideas/genre_map.txt": "题材地图：都市/甜宠/虐恋/悬疑/逆袭/系统文",
    "workspace/tools/scripts/word_count.sh": "#!/bin/bash\nwc -w $1",
    "workspace/tools/templates/basic_outline.txt": "【基础大纲模板】\n主人公：\n目标：\n障碍：\n行动：\n结果：\n转折：\n高潮：\n结局：",
    "workspace/review/pending/submission_001.txt": "待审稿件001：《总裁的隐婚甜妻》第一章……（内容省略）",
    "workspace/review/done/feedback_001.txt": "审稿意见001：标题吸引力不足，导语节奏慢，建议修改第一段。",
}

for path, content in distractors.items():
    with open(os.path.join("/", path), "w", encoding="utf-8") as f:
        f.write(content)

# --- THE ACTUAL TASK INPUT ---
# A raw story seed + bad title + AI-flavored passage that the agent must process

task_input = {
    "task_id": "fanqie_audit_001",
    "description": "请对以下内容进行全面的质量审核与改写，并将结果保存为 audit_report.json",
    "raw_story_seed": "一个在婚礼现场被当众羞辱的新娘，发现新郎是个替身，真正的新郎其实是个卧底警察，整场婚礼是个圈套。",
    "bad_title": "婚礼上发生了一件奇怪的事情让我很震惊",
    "ai_flavored_passage": (
        "林晓雨感到非常愤怒。因为她意识到眼前这个男人并不是她真正的未婚夫。"
        "为了弄清楚事情的真相，她决定冷静下来，试图通过观察细节来找到线索。"
        "所以她深吸一口气，努力让自己保持镇定。"
        "她的内心充满了复杂的情绪，既有愤怒，也有悲伤，还有一丝难以言说的恐惧。"
        "她非常坚定地走向那个陌生的男人，因为她知道今天必须得到一个答案。"
        "这场婚礼从一开始就充满了令人窒息的压迫感，所有人的目光都聚焦在她的身上，让她感到窒息和无助。"
    )
}

with open("/workspace/task_input.json", "w", encoding="utf-8") as f:
    json.dump(task_input, f, ensure_ascii=False, indent=2)

print("Workspace initialized. Task input written to /workspace/task_input.json")
print("Agent must produce: /workspace/output/audit_report.json")