import os
import random
import json

random.seed(42)

workspace = "/workspace"

# Create a realistic deeply nested directory structure for a web novel company
dirs = [
    "projects/xuan_huan/draft",
    "projects/xuan_huan/reviews",
    "projects/yan_qing/draft",
    "projects/yan_qing/reviews",
    "projects/xuanhuan_mix/concepts",
    "templates/old_format",
    "templates/rejected",
    "resources/character_banks",
    "resources/world_building",
    "archive/2022/completed",
    "archive/2023/completed",
    "archive/2023/abandoned",
    "staff/editor_notes",
    "staff/writer_guidelines",
    "marketing/synopses",
    "marketing/covers",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files - old, partial, or irrelevant documents
distractor_files = {
    "projects/xuan_huan/draft/chapter1_rough.txt": """第一章 天才少年
    林峰睁开眼睛，发现自己置身于一片茫茫星空之中……
    （草稿，待修改）""",

    "projects/xuan_huan/reviews/editor_feedback_v1.txt": """编辑意见：
    人物动机不够清晰，主角开挂太快，读者无法代入。
    建议加强铺垫，增加反派背景故事。""",

    "projects/yan_qing/draft/synopsis_rough.txt": """女主：白浅浅，22岁，普通白领
    男主：顾霆烨，28岁，总裁
    （剧情：霸道总裁爱上我，待完善）""",

    "templates/old_format/novel_template_v1.md": """# 小说模板 V1 (已废弃)
    
    ## 角色
    - 主角：
    - 配角：
    
    ## 情节
    - 开始：
    - 发展：
    - 结束：
    
    注意：此模板已被新格式取代，请勿使用。""",

    "templates/rejected/incomplete_framework.md": """# 悬疑推理框架（未完成）

    ## 人物
    主角：陈侦探
    
    ## 剧情
    第一案：消失的证人
    
    （此文件因格式不符合标准被拒绝）""",

    "resources/character_banks/common_names.txt": "\n".join([
        "林峰、白浅浅、顾霆烨、叶辰、苏瑶", 
        "陈宇、李梦、王浩、张晓、刘洋",
        "赵天、孙悦、周杰、吴婷、郑伟"
    ]),

    "resources/world_building/magic_systems.txt": """常见修仙体系：
    1. 炼气期 → 筑基期 → 金丹期 → 元婴期 → 化神期
    2. 斗气等级：学徒 → 斗者 → 斗师 → 大斗师
    3. 武者境界：后天 → 先天 → 宗师 → 武王 → 武帝""",

    "archive/2022/completed/dragon_slayer_final.md": """# 屠龙传说 - 最终版
    
    已于2022年完结，全本180万字。
    本书版权已售出，请勿二次使用任何设定。""",

    "archive/2023/abandoned/city_power_abandoned.txt": """项目《都市异能觉醒》已于2023年9月终止。
    原因：市场同质化严重，读者反馈差。
    相关素材可用于参考但不可直接复用。""",

    "archive/2023/completed/school_romance_review.txt": """《校园初恋》项目总结
    完结时间：2023年12月
    总字数：60万
    读者评分：8.2/10
    主要成功因素：人物刻画真实，情感节奏把控得当。""",

    "staff/editor_notes/formatting_complaints.txt": """编辑部备忘录（2024年1月）：
    
    近期提交的框架文件存在以下问题：
    1. 缺少人物关系表格
    2. 结局只写了一两个，不够多样化
    3. 剧情节点描述过于简略
    4. 没有按照标准章节编号格式
    
    请所有写手重新阅读创作规范后再提交。""",

    "staff/writer_guidelines/genre_tips.txt": """各类型写作提示（简版）：
    
    玄幻修仙：注重境界成长线和宗门斗争
    都市异能：现实感要强，异能设定要有规则
    言情：情感节奏最重要，不要虐过头
    悬疑推理：线索要前后呼应，不能开上帝视角""",

    "marketing/synopses/pending_review.txt": """待审核项目列表（2024年Q1）：
    
    1. 《星际商队》- 科幻 - 作者：张文
    2. 《剑破苍穹》- 玄幻 - 作者：李明
    3. 《都市之巅》- 都市异能 - 作者：王芳
    4. 《回到盛唐》- 历史穿越 - 作者：陈刚
    
    上述项目均需完整创作框架后方可进入立项评审。""",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# Create a project brief that gives the agent its task context
project_brief = {
    "project_id": "2024-Q1-007",
    "genre": "悬疑推理",
    "secondary_genre": "都市异能",
    "title_working": "第七感侦探",
    "requester": "李编辑",
    "date": "2024-03-15",
    "notes": "需要完整的创作框架，包括所有人物、关系图、剧情节点和多版本结局。主角需要有特殊能力（读取残留情绪），反派为连环杀手组织。双主角设定。情感基调：紧张悬疑中带有情感线。",
    "target_readers": "18-35岁都市年轻读者",
    "length": "长篇",
    "deadline": "2024-03-20"
}

with open(os.path.join(workspace, "projects/xuanhuan_mix/concepts/project_brief_007.json"), "w", encoding="utf-8") as f:
    json.dump(project_brief, f, ensure_ascii=False, indent=2)

print("Workspace initialized with distractor files and project brief.")
print(f"Project brief written to: projects/xuanhuan_mix/concepts/project_brief_007.json")