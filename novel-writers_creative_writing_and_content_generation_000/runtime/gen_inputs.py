import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Create a realistic, messy project directory with distractor files ---

dirs = [
    "project_alpha/drafts",
    "project_alpha/outline",
    "project_alpha/character_notes",
    "project_beta/research",
    "project_beta/worldbuilding",
    "archive/old_drafts",
    "archive/rejected_ideas",
    "tools/templates",
    "tools/checklists",
    "editor_feedback",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files: old drafts, notes, rejected content, editor memos

distractor_files = {
    "project_alpha/drafts/draft_v1.txt": """第一章草稿（废弃）
李明走进便利店，买了一瓶矿泉水。他今年28岁，是一名普通的快递员。
这一天，他的生活将发生翻天覆地的变化。
（注：此版本节奏太慢，已废弃）""",

    "project_alpha/drafts/draft_v2_REJECTED.txt": """【废弃草稿 v2】
开篇：宇宙飞船在星际战场穿梭，激光炮轰鸣……
编辑反馈：太空歌剧风格，不符合平台要求。场景必须落地都市。""",

    "project_alpha/outline/main_outline_INCOMPLETE.md": """# 主线大纲（未完成）

## 故事背景
时间：近未来
地点：某一线城市

## 主角
姓名：待定
职业：待定
能力：待定

## 第一章
???

（注：策划案尚未完成，等待创作团队填写）""",

    "project_alpha/character_notes/brainstorm.txt": """角色头脑风暴（碎片想法）

想法A：外卖小哥+隐形能力？太老套了
想法B：保安大叔+预知未来？还行
想法C：程序员+量子纠缠？太硬科幻了
想法D：快递员+时间暂停？可以考虑

配角：最好有点意思，不要工具人
（以上仅为草稿，无最终结论）""",

    "project_beta/research/urban_scifi_market_2024.txt": """都市科幻市场调研报告（节选）

番茄小说平台数据显示：
- 都市科幻品类月活读者：2.3亿
- 用户留存关键：前3章爽点密度
- 黄金字数区间：单章2000-2500字
- 最受欢迎人设：反差萌主角

（数据来源：内部报告，仅供参考）""",

    "project_beta/worldbuilding/sci_fi_concepts_DUMP.txt": """科幻概念备忘（杂乱无章）

量子纠缠、虫洞、基因编辑、纳米机器人、意识上传、
时间悖论、平行宇宙、反物质、暗物质……

注意：不要写太硬科幻！量子力学推导、专业方程式绝对不行。
要落地：地铁时空裂缝？小区基因诊所？写字楼传送门？""",

    "archive/old_drafts/story_2022_abandoned.txt": """【2022年废弃稿】
题目：《我在异界当修仙者》
这是一个修仙故事……（与当前项目无关，存档备查）""",

    "archive/rejected_ideas/pure_fantasy_pitch.txt": """被编辑否定的提案：
纯奇幻世界观，没有都市背景。
反馈：不符合平台定位，须有都市烟火气。""",

    "tools/templates/generic_novel_template.txt": """通用小说模板（非番茄平台专用）

第X章：[章节名]
[正文内容]
——全文完——

（警告：此模板不符合任何特定平台规范，仅作通用参考）""",

    "tools/checklists/editor_review_checklist.txt": """编辑审稿清单（通用版）

□ 字数是否达标
□ 情节是否流畅
□ 人物是否立体
□ 对话是否自然
□ 结尾是否有力

（此清单为通用版，具体平台有具体要求）""",

    "editor_feedback/feedback_round1.txt": """编辑反馈意见（第一轮）

总体问题：
1. 开篇节奏太慢，读者会流失
2. 主角没有反差感，太平庸
3. 配角像背景板，没有存在感
4. 幽默元素不足，全篇太严肃
5. 每章结尾没有钩子，读者不会追更

请创作团队根据平台风格规范修改。""",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# --- The actual task brief (deliberately vague, no technical hints) ---

task_brief = """# 创作任务委托书

## 项目：《都市异能》系列 - 第一章创作

**委托方：** 番茄小说平台编辑部  
**日期：** 2024年

---

## 背景说明

我们正在启动一个新的都市科幻系列。编辑部需要创作团队提供一个完整的角色方案和开篇第一章。

## 交付要求

请基于以下素材创建两个文件：

### 文件1：角色设定稿（character_profile.md）
为本故事提供主角和至少一名配角的完整人设。

**主角基础信息（已确定）：**
- 姓名：陈默
- 年龄：26岁
- 职业：某互联网公司的普通IT运维工程师（外包）
- 背景：大专学历，月薪8000，租住在城中村，每天挤地铁上班

**科幻设定（已确定）：**
- 陈默某天上班途中，地铁发生了一次神秘的"设备故障"，事后他发现自己获得了"系统诊断"能力：能看到任何机械/电子设备的运行状态、故障原因、甚至预测故障时间，数据以半透明UI的形式叠加在他视野中。

**需要创作团队补充：**
- 主角完整人设（性格、日常习惯、内心世界）
- 至少1名配角（同事、邻居、或其他）的完整设定，配角必须有自己独特的科幻相关设定

### 文件2：开篇第一章（chapter_01.md）
撰写正式的第一章内容。

第一章必须包含完整的结构化信息，并展示主角的能力觉醒过程。
"""

with open(os.path.join(workspace, "task_brief.md"), "w", encoding="utf-8") as f:
    f.write(task_brief)

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk(workspace):
    level = root.replace(workspace, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}{os.path.basename(root)}/')
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f'{subindent}{file}')