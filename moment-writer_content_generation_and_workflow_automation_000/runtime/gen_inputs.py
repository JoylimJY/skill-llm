import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# Create realistic deeply nested directory structure with distractor files
dirs = [
    "workspace/brand/assets/images",
    "workspace/brand/assets/videos",
    "workspace/brand/strategy/2024Q1",
    "workspace/brand/strategy/2024Q2",
    "workspace/brand/competitors",
    "workspace/content/drafts/rejected",
    "workspace/content/drafts/pending",
    "workspace/content/published/jan",
    "workspace/content/published/feb",
    "workspace/analytics/weekly",
    "workspace/analytics/monthly",
    "workspace/tools/templates",
    "workspace/tools/checklists",
    "workspace/team/copywriters",
    "workspace/team/designers",
]

for d in dirs:
    Path(d).mkdir(parents=True, exist_ok=True)

# Distractor files - realistic but irrelevant
distractor_files = {
    "workspace/brand/brand_guidelines.txt": """品牌名称：萌芽成长教育
品牌色：#FF8C69 (温暖橙), #6B9FD4 (静谧蓝)
Slogan：每一步成长，都值得被看见
目标用户：25-40岁宝妈群体
核心优势：儿童早教、亲子互动、学习力培养
""",
    "workspace/brand/strategy/2024Q1/q1_goals.txt": """Q1目标：
- 私域用户增长20%
- 朋友圈互动率提升15%
- 课程转化率 > 8%
""",
    "workspace/brand/strategy/2024Q2/q2_plan.json": json.dumps({
        "campaign": "暑期特训营",
        "target_audience": "6-12岁学龄儿童家长",
        "budget": 50000,
        "channels": ["朋友圈", "视频号", "公众号"]
    }, ensure_ascii=False, indent=2),
    "workspace/brand/competitors/competitor_analysis.txt": """竞品分析 - 2024年3月
竞品A：以情感营销为主，内容质量良莠不齐
竞品B：专业性强，但距离感较重
竞品C：活动频繁，但品牌调性不稳定

我方优势：专业+温度并重，建立深度信任感
""",
    "workspace/content/drafts/rejected/bad_copy_01.txt": """限时特惠！买课送课！
现在报名早教课程，立减500元！
仅剩最后10个名额！快快快！

（此文案因过度营销被拒）
""",
    "workspace/content/drafts/rejected/bad_copy_02.txt": """我们的课程全国第一！
权威认证！专家推荐！
家长好评如潮！

（此文案因夸大宣传被拒）
""",
    "workspace/content/drafts/pending/topic_ideas.txt": """待创作主题池：
1. 专业型：一个孩子注意力问题咨询案例
2. 温暖型：孩子第一次主动做作业
3. 反认知：刷题多就能提高成绩
4. 利他型：如何判断孩子是否需要专业干预
5. 自我介绍：我是谁，我能帮助谁
""",
    "workspace/content/published/jan/jan_summary.txt": """1月发布统计：
- 共发布文案12篇
- 平均点赞：23
- 平均评论：8
- 转化咨询：15次
""",
    "workspace/analytics/weekly/week12_report.csv": """date,posts,likes,comments,conversions
2024-03-18,3,67,24,5
2024-03-19,2,45,18,3
2024-03-20,1,89,31,8
2024-03-21,3,54,19,4
""",
    "workspace/analytics/monthly/march_kpi.txt": """3月KPI追踪（截至3月22日）：
发布量：32篇
总触达：8,450人次
互动率：6.8%
咨询转化：42次
目标完成率：76%
""",
    "workspace/tools/templates/image_rules.txt": """配图规则参考（非内容规则）：
- 封面图：800x800px
- 九宫格：每张300x300px
- 视频封面：1080x1080px
不同类型文案对应不同配图风格
""",
    "workspace/tools/checklists/publish_checklist.txt": """发布前检查清单：
□ 文案已通过二次校对
□ 配图已选定
□ 发布时间已设定（建议7-9点 / 12-13点 / 20-22点）
□ 评论区预设内容已准备
□ 转发话术已确认
""",
    "workspace/team/copywriters/writer_notes.txt": """文案团队内部笔记：
- 陈小明：擅长情感型文案
- 李华：擅长专业型文案
- 张萌：擅长反认知类型
注意：所有对外内容需经品牌负责人审核
""",
    "workspace/team/designers/design_brief.txt": """设计需求说明：
专业型配图：使用冷色调，体现权威感
温暖型配图：暖色调，真实生活场景
反认知型：视觉冲击感，配合文字反转
""",
    "workspace/content/content_calendar.txt": """内容日历 - 2024年3月最后一周
周一：专业型（注意力专题）
周二：温暖型（亲子日常）
周三：利他型（学习方法干货）
周四：反认知（刷题迷思）
周五：自我介绍（新粉丝增量日）
""",
}

for filepath, content in distractor_files.items():
    Path(filepath).write_text(content, encoding='utf-8')

# The ACTUAL task input: a structured brief the agent needs to fulfill
task_brief = {
    "brand": "萌芽成长教育",
    "campaign_name": "三月家长信任建设专项",
    "required_posts": [
        {
            "id": "post_1",
            "type_hint": "展现专业能力，建立权威感",
            "topic": "一个8岁孩子读写困难被逆转的咨询案例"
        },
        {
            "id": "post_2",
            "type_hint": "展现不容易放弃的努力过程，让家长看到我们的靠谱",
            "topic": "我第一次做亲子课程方案时被家长当面否定"
        },
        {
            "id": "post_3",
            "type_hint": "日常生活温情，让用户感觉真实可亲近",
            "topic": "孩子睡前突然问我你累不累"
        },
        {
            "id": "post_4",
            "type_hint": "打破家长常见的错误认知，引发思考",
            "topic": "孩子成绩差是因为不够努力——这是最危险的误解"
        },
        {
            "id": "post_5",
            "type_hint": "简短的个人介绍，告诉大家我是谁能帮到谁",
            "topic": "我的核心价值与服务定位"
        }
    ],
    "output_instructions": "请将所有文案整理为一个完整的内容包，保存为 moments_package.md"
}

Path("workspace/content/campaign_brief.json").write_text(
    json.dumps(task_brief, ensure_ascii=False, indent=2),
    encoding='utf-8'
)

# Also create the SKILL.md in the workspace for the agent to find
skill_md_content = """---
name: moments-writer-lite
version: 1.0.0
description: 朋友圈文案生成器（精简版），基于私域变现核心方法论
tags: [wechat, moments, copywriting, 朋友圈, 私域, 文案]
author: Claude Code Assistant
commands:
  - name: moments
    description: 生成朋友圈文案
    parameters:
      - name: type
        description: 文案类型
        required: true
      - name: topic
        description: 文案主题
        required: false
    examples:
      - usage: /moments professional 咨询场景
        description: 专业型
      - usage: /moments warm 亲子时光
        description: 温暖型
      - usage: /moments counter 补课谎言
        description: 反认知
---

# 朋友圈写作助手 Lite

基于**麦肯锡信任公式**的朋友圈文案生成器：

```
信任 = (专业度 × 可靠度 × 亲密度) / 自身利益
```

## 支持的文案类型

| 命令 | 说明 | 公式 |
|------|------|------|
| `/moments professional` | 专业型：建立权威 | 故事案例 + 细节 + 美好结果 |
| `/moments reliable` | 靠谱型：建立信任 | 失败故事 + 不服输过程 + 成功结果 |
| `/moments warm` | 温暖型：建立亲密度 | 生活场景 + 真实互动 + 情感连接 |
| `/moments altruistic` | 利他型：降低防御 | 事件 + 细节 + 解释 + 价值观/金句 |
| `/moments counter` | 反认知破圈 | 打破认知 + 植入理念 |
| `/moments target` | 圈用户 | 筛选目标人群 + 建立边界 |
| `/moments intro_100` | 自我介绍100字 | 深耕领域 + 踩坑经验 + 价值钩子 |

## 排版规范

- 第一段：20-25字以内，场景化切入
- 段落：每段不超过3行，段间空一行
- 配图：使用1、4、9张图
- 评论区：营销信息放评论区

## 使用示例

```
/moments professional 户外咨询场景
/moments warm 孩子说妈妈真好
/moments counter 补课就能提分是谎言
/moments intro_100 我的核心价值
```
"""

Path("workspace/SKILL.md").write_text(skill_md_content, encoding='utf-8')

print("Workspace generated successfully.")
print("Files created:")
for f in sorted(Path("workspace").rglob("*")):
    if f.is_file():
        print(f"  {f}")