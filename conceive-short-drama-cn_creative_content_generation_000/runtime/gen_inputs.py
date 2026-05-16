import os
import random

random.seed(42)

# Build a realistic, deeply nested workspace simulating a short-drama production company's folder

base = "/workspace"

dirs = [
    "projects/drama_series_A/scripts",
    "projects/drama_series_A/assets",
    "projects/drama_series_A/archive",
    "projects/drama_series_B/drafts",
    "projects/drama_series_B/review",
    "projects/drama_series_C/brainstorm",
    "admin/contracts",
    "admin/schedules",
    "marketing/campaigns",
    "marketing/social_media",
    "resources/references",
    "resources/templates",
    "tools/scripts",
    "output/pending",
]

for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# --- Distractor files ---

distractor_files = {
    "projects/drama_series_A/scripts/episode_01_draft.txt": (
        "第一集草稿\n\n这是一个关于创业青年的故事，男主从小镇来到大城市打拼...\n"
        "（此版本已废弃，请勿使用）\n"
    ),
    "projects/drama_series_A/scripts/episode_02_notes.txt": (
        "Episode 2 Notes:\n- 增加家庭冲突\n- 女主出场需要更自然\n- 结局修改为开放式\n"
    ),
    "projects/drama_series_A/assets/music_list.csv": (
        "track_id,name,duration\n001,奋斗的青春,3:45\n002,归途,4:12\n003,无名英雄,2:58\n"
    ),
    "projects/drama_series_A/archive/old_outline_v1.txt": (
        "旧版大纲（v1.0，已弃用）\n\n男主角自学编程，创业，公司上市，迎娶白富美...\n"
        "注：此套路太老，导演已否决。\n"
    ),
    "projects/drama_series_B/drafts/concept_note.md": (
        "# 系列B概念笔记\n\n主题：传统工艺复兴\n风格：温情现实主义\n目标观众：25-40岁女性\n"
    ),
    "projects/drama_series_B/review/feedback_round1.txt": (
        "审阅意见：\n1. 节奏偏慢，需要在第二幕增加更多冲突\n2. 人物动机不够充分\n3. 结局太过突兀\n"
    ),
    "projects/drama_series_C/brainstorm/random_ideas.txt": (
        "随机创意池：\n- 一个修鞋匠发现顾客是失散多年的亲人\n- 外卖骑手意外发现邻居是通缉犯\n"
        "- 清洁工在豪宅发现秘密\n- 村里最穷的孩子赢得国际数学奖\n"
    ),
    "admin/contracts/production_contract_template.txt": (
        "制作合同模板\n\n甲方：___\n乙方：___\n项目名称：___\n制作周期：___天\n"
    ),
    "admin/schedules/q4_production_plan.csv": (
        "week,project,milestone\n1,Series_A,脚本定稿\n2,Series_B,拍摄启动\n3,Series_C,剪辑完成\n4,All,上线审核\n"
    ),
    "marketing/campaigns/launch_plan_nov.txt": (
        "11月上线计划\n\n系列A：11月5日上线\n系列B：11月12日上线\n推广渠道：抖音、快手、B站\n"
    ),
    "marketing/social_media/hashtag_research.txt": (
        "热门话题标签研究：\n#短剧推荐 #逆袭人生 #感人故事 #励志短片\n播放量分析：逆袭类内容平均完播率62%\n"
    ),
    "resources/references/plot_cliches_to_avoid.txt": (
        "常见老套情节清单（禁用）：\n1. 主角自学编程然后创业上市\n"
        "2. 救下老人→老人是富豪→获得投资\n3. 灰姑娘被总裁看上一夜逆袭\n"
        "4. 车祸失忆再相遇\n5. 孤儿发现自己是皇族后裔\n"
    ),
    "resources/templates/script_format_guide.txt": (
        "剧本格式规范\n\n场景号 INT/EXT 地点 - 时间\n\n人物名\n台词内容\n\n（动作描述）\n"
        "注：此为正式剧本格式，剧情大纲阶段不适用。\n"
    ),
    "tools/scripts/auto_formatter.py": (
        "# 自动格式化工具（开发中，暂不可用）\n"
        "def format_script(text):\n    pass  # TODO\n"
    ),
    "output/pending/placeholder.txt": (
        "此目录用于存放待审核的输出文件。\n当前无待审核内容。\n"
    ),
}

for path, content in distractor_files.items():
    full_path = os.path.join(base, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# --- THE ACTUAL TASK INPUT ---
# A "creative brief" file with the one-sentence inspiration seed
# Deliberately embedded in a non-obvious location with some surrounding noise

creative_brief_content = """\
=====================================
创意简报 - 紧急任务
项目编号：PRJ-2024-0891
提交人：李制片
日期：2024-11-15
优先级：高
=====================================

背景说明：
本周五前需要完成以下剧情大纲供导演审阅。
请剧情策划师按照公司标准流程输出完整大纲。
输出文件命名：story_outline.txt

-------------------------------------
本次创作灵感（一句话）：
-------------------------------------

一个聋哑花艺师，用一束花改变了整栋楼邻居的命运

-------------------------------------
特别备注：
- 不得出现任何台词或对白，全程用叙述方式呈现
- 剧情必须正能量，无负面暴力内容
- 结构清晰，有起伏有高潮
- 周五18:00前提交output/pending/目录
=====================================
"""

brief_path = os.path.join(base, "projects/drama_series_C/brainstorm/creative_brief_PRJ0891.txt")
with open(brief_path, "w", encoding="utf-8") as f:
    f.write(creative_brief_content)

print("Workspace generated successfully.")
print(f"Task input file: {brief_path}")
print(f"Total distractor files: {len(distractor_files)}")