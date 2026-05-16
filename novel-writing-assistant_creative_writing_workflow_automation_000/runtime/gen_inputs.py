import os
import json
import random

random.seed(42)

# Create directory structure
dirs = [
    "/workspace/project_xianxia",
    "/workspace/project_xianxia/drafts",
    "/workspace/project_xianxia/drafts/raw_notes",
    "/workspace/project_xianxia/drafts/outlines",
    "/workspace/project_xianxia/references",
    "/workspace/project_xianxia/references/market_data",
    "/workspace/project_xianxia/references/tropes",
    "/workspace/project_xianxia/assets",
    "/workspace/project_xianxia/assets/character_sketches",
    "/workspace/project_xianxia/assets/world_maps",
    "/workspace/project_xianxia/archive",
    "/workspace/project_xianxia/archive/old_versions",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# Distractor files - messy raw notes
raw_notes = [
    ("/workspace/project_xianxia/drafts/raw_notes/idea_dump.txt", """
主角叫什么好？李云？陈长生？
金手指：古老传承？还是系统？
反派要有深度 不能太蠢
世界叫做 九天大陆？
修炼等级要清晰
第一章要有冲突
女主角要有个性 不能花瓶
"""),
    ("/workspace/project_xianxia/drafts/raw_notes/character_scratch.txt", """
主角：平民出身，天才资质被封印
父母早逝，由叔叔抚养
性格：外冷内热，护短
金手指方向：可能是残卷？
配角甲：同门师兄 嫉妒主角
配角乙：女主 神秘身份
"""),
    ("/workspace/project_xianxia/drafts/raw_notes/world_scratch.txt", """
修炼等级（草稿）：
炼体 -> 聚气 -> 筑基 -> 金丹 -> 元婴 -> 化神
宗门：天剑宗 最强
国家：大炎王朝 封建制度
禁忌：不可逆天改命
货币：灵石
"""),
    ("/workspace/project_xianxia/drafts/outlines/rough_outline_v1.txt", """
第一章：主角被废，受辱
第二章：获得传承，觉醒
第三章：报仇雪恨（太快了？）
第N章：宗门试炼
结局：成为最强
"""),
    ("/workspace/project_xianxia/drafts/outlines/rough_outline_v2.txt", """
修改版大纲
开头要有钩子
前十章建立世界
中期要有感情线
反派要在第15章出现
高潮：宗门大比
"""),
    ("/workspace/project_xianxia/references/market_data/popular_tags_2024.json", json.dumps({
        "top_tags": ["仙侠", "玄幻", "系统流", "天才", "废材逆袭"],
        "avg_chapter_length": 2500,
        "daily_update_target": 3000,
        "popular_openings": ["开局被废", "重生归来", "获得系统"]
    }, ensure_ascii=False, indent=2)),
    ("/workspace/project_xianxia/references/market_data/competitor_analysis.txt", """
竞品分析：
《斗破苍穹》- 废材逆袭 强化丹药体系
《完美世界》- 宏大世界观 硬实力提升
《大主宰》- 情感线丰富 修炼体系清晰

差异化：
我们的故事要更注重人物深度
减少战斗流水账
增加世界观细节
"""),
    ("/workspace/project_xianxia/references/tropes/xianxia_tropes.txt", """
仙侠常见套路：
1. 废材流 - 主角初期被看不起
2. 师傅加持 - 获得高人指点
3. 秘境寻宝 - 发现上古遗迹
4. 宗门大比 - 展示实力
5. 女主红颜 - 情感线
要避免：过度使用这些套路，要有新意
"""),
    ("/workspace/project_xianxia/assets/character_sketches/protagonist_visual.txt", """
主角外貌描述（视觉参考）：
- 年龄约17岁，眉清目秀
- 修炼后气质沉稳
- 常着白色修士服
- 眼神：深邃，偶有锋芒
注意：视觉风格偏向传统仙侠
"""),
    ("/workspace/project_xianxia/assets/world_maps/continent_sketch.txt", """
九天大陆地图草图：
北部：冰雪极域（强者修炼地）
中部：大炎王朝（主要故事发生地）
东部：妖兽森林（危险区域）
西部：沙漠神秘区域（待定）
南部：海洋（未来发展地图）
天剑宗位置：中部山脉
"""),
    ("/workspace/project_xianxia/archive/old_versions/protagonist_v0.txt", """
旧版主角设定（废弃）：
名字：李天 
出身：王侯之家
金手指：系统
问题：太平庸，读者反馈不好
废弃原因：缺乏独特性
"""),
    ("/workspace/project_xianxia/archive/old_versions/chapter1_v0.txt", """
第一章 废材（旧版）
李天站在宗门广场上，心中充满了愤恨。
他是废材，所有人都这么说。
但他知道，终有一天，他会让所有人后悔。
[废弃 - 太平淡，开头没有钩子]
"""),
]

for filepath, content in raw_notes:
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

# Create the main brief/commission file - this is the KEY INPUT the agent must process
commission_brief = """
# 小说创作委托书

## 项目信息
- 项目代号：天剑传说
- 题材：仙侠
- 目标读者：喜欢爽点的上班族
- 核心卖点：废材逆袭 + 古老传承（非系统流）
- 期望字数：100万字
- 更新频率：日更

## 已确定设定

### 主角基础信息
- 姓名：沈云
- 年龄：17岁（少年设定）
- 出身：普通农民家庭，父母在他5岁时意外身亡
- 特殊背景：出生时灵根被人恶意封印，被认定为废材
- 金手指：获得上古剑修老祖的残魂传承（有代价：每次使用会消耗寿元）
- 核心性格：外表冷漠实则重情重义，护短
- 最大优点：意志力极强，逆境愈战愈勇
- 致命缺点：过于自负，不善求助

### 世界观关键信息
- 世界名：九天大陆
- 修炼体系：炼体→聚气→筑基→金丹→元婴→化神→渡劫→飞升（共8级）
- 主要势力：天剑宗（第一大宗门）、大炎王朝（皇权）、妖族（外部威胁）
- 故事起点：天剑宗外门弟子选拔

### 关键配角需求
需要以下四类配角：
1. 重要盟友角色（1个）
2. 主要对手角色（1个）  
3. 暧昧对象/感情线角色（1个）
4. 功能性角色-导师类（1个）

### 第一章要求
- 场景：天剑宗外门弟子选拔大会
- 核心事件：沈云在公众场合被测灵根，结果显示"废材"，受到众人嘲讽，随后触发传承觉醒
- 情感线：从屈辱到觉醒的内心转变
- 章节标题：《第一章 废材的觉醒》
- 文风偏好：简洁明快，高对话比例，强悬念结尾

## 需要输出的文件

请根据以上委托信息，生成以下三个文件，存放在 /workspace/project_xianxia/drafts/ 目录下：

1. `character_profiles.md` - 完整的人物档案文件
2. `chapter_01.md` - 第一章完整正文
3. `consistency_report.md` - 针对第一章正文的一致性审核报告

"""

with open("/workspace/project_xianxia/commission_brief.md", 'w', encoding='utf-8') as f:
    f.write(commission_brief)

# Create a partial/incomplete character template to show what format is expected but intentionally missing key sections
incomplete_template = """
# 人物档案模板（参考，不完整）

## 主角
- 姓名：
- 基本信息：
- 性格：（这里有更多内容但文件损坏了）

[文件损坏 - 请参考创作规范重新生成完整档案]
"""

with open("/workspace/project_xianxia/assets/character_sketches/TEMPLATE_BROKEN.md", 'w', encoding='utf-8') as f:
    f.write(incomplete_template)

print("Workspace initialized successfully.")
print("Key input file: /workspace/project_xianxia/commission_brief.md")