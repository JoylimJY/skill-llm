import os
import json
import random

random.seed(42)

BASE = "/workspace"

# Create realistic deeply nested distractor structure
dirs = [
    "project/archive/2023/q4",
    "project/archive/2024/q1",
    "project/archive/2024/q2",
    "project/drafts/pending",
    "project/drafts/rejected",
    "project/assets/images",
    "project/assets/audio",
    "project/analytics/raw",
    "project/analytics/processed",
    "project/templates",
    "project/meetings/notes",
    "project/source_materials",
]

for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# --- DISTRACTOR FILES ---

# Old content drafts (distractor)
with open(os.path.join(BASE, "project/archive/2023/q4/draft_food_safety.txt"), "w", encoding="utf-8") as f:
    f.write("2023年食品安全专题草稿\n这是一个关于食品安全的旧稿，已归档。\n内容包括餐厅检查结果、消费者投诉数据等。\n")

with open(os.path.join(BASE, "project/archive/2024/q1/weibo_hotspot_log.txt"), "w", encoding="utf-8") as f:
    f.write("2024Q1热点追踪记录\n#外卖骑手# #劳动权益# #平台经济#\n话题热度数据（仅供参考）：...\n")

with open(os.path.join(BASE, "project/archive/2024/q2/interview_template.docx.txt"), "w", encoding="utf-8") as f:
    f.write("采访提纲模板（通用版）\n1. 请介绍一下您的基本情况\n2. ...\n")

# Rejected drafts (distractor)
with open(os.path.join(BASE, "project/drafts/rejected/platform_report_v1.txt"), "w", encoding="utf-8") as f:
    f.write("平台报告初稿（已被否定）\n这份报告因数据不足被驳回，请勿使用。\n")

with open(os.path.join(BASE, "project/drafts/pending/content_ideas_brainstorm.txt"), "w", encoding="utf-8") as f:
    f.write("头脑风暴：\n- 外卖骑手专题\n- 平台算法与骑手收入\n- 骑手意外伤害保障\n待定，尚未立项。\n")

# Asset placeholders (distractor)
with open(os.path.join(BASE, "project/assets/images/cover_design_notes.txt"), "w", encoding="utf-8") as f:
    f.write("封面设计备注：使用骑手骑行的实拍图，背景色建议橙色系，与美团/饿了么品牌色呼应。\n")

with open(os.path.join(BASE, "project/assets/audio/voiceover_script_old.txt"), "w", encoding="utf-8") as f:
    f.write("旧版配音脚本（2023版）\n开场白：每天有数百万骑手穿梭在城市的大街小巷……\n（此版本已过时）\n")

# Meeting notes (distractor)
with open(os.path.join(BASE, "project/meetings/notes/editorial_meeting_20240601.txt"), "w", encoding="utf-8") as f:
    f.write("编辑会议纪要 2024-06-01\n议题：外卖骑手劳动权益专题策划\n决议：由内容团队本周完成素材采集，下周启动多平台分发。\n负责人：待定\n")

with open(os.path.join(BASE, "project/meetings/notes/analytics_review_20240605.txt"), "w", encoding="utf-8") as f:
    f.write("数据复盘会议纪要 2024-06-05\n上期内容数据整体偏低，需分析原因。\n行动项：重新审视标题策略，改善互动率。\n")

# Templates (distractor)
with open(os.path.join(BASE, "project/templates/wechat_article_template.txt"), "w", encoding="utf-8") as f:
    f.write("微信公众号文章排版模板\n[标题]\n[副标题]\n[正文]\n[互动引导]\n[作者信息]\n")

with open(os.path.join(BASE, "project/templates/douyin_script_template.txt"), "w", encoding="utf-8") as f:
    f.write("抖音脚本模板\n时长：60秒\n[画面描述]\n[配音文字]\n[字幕]\n")

# Analytics raw data (distractor, incomplete/wrong format)
with open(os.path.join(BASE, "project/analytics/raw/old_metrics_dump.csv"), "w", encoding="utf-8") as f:
    f.write("date,platform,reads,likes\n2024-01-01,wechat,5000,200\n2024-01-02,weibo,8000,150\n")

# --- ACTUAL INPUT FILES THE AGENT MUST PROCESS ---

# 1. Raw interview notes - messy, unstructured
raw_interview = """
【原始采访素材 - 外卖骑手劳动权益专题】
采访时间：2024年6月10日
采访对象：张伟（外卖骑手，从业3年），李敏（平台运营经理，匿名），陈法律（劳动法学者）

===张伟采访实录（口语化，未整理）===
记者：您每天大概跑多少单？
张伟：多的时候四五十单吧，少的时候也得二三十单。最近平台把底薪砍了，说是要"优化激励机制"，但实际上我们收入降了差不多20%。
记者：遇到过事故吗？
张伟：去年冬天滑倒过一次，胳膊骨折，在家歇了两个月。平台说我们是"合作关系"不是"雇佣关系"，不赔工伤。我自己买的那个什么"骑手保"，最后就赔了几百块钱，医药费好几千呢。
记者：现在的情况有改善吗？
张伟：听说今年开始要把我们纳入职业伤害保障了，但具体怎么弄还不清楚，反正就是盼着能有个保障。

===李敏采访实录（匿名，谨慎）===
记者：平台如何看待骑手的劳动关系问题？
李敏：这个……我们一直在配合相关部门的政策推进。平台确实有责任，我们也在积极探索。（后续不愿多谈）

===陈法律采访实录===
记者：从法律角度怎么看这个问题？
陈法律：新业态用工的劳动权益保障是全球性难题。在中国，2021年人社部等八部门联合发布了关于维护新就业形态劳动者劳动保障权益的指导意见，明确要求平台企业对不完全符合劳动关系情形的骑手，推进职业伤害保障试点。但落地效果参差不齐，监管力度还需加强。
记者：骑手们最核心的诉求是什么？
陈法律：三点：一是收入的稳定性与透明度，二是意外伤害的兜底保障，三是申诉渠道的畅通。

===补充数据===
- 全国外卖骑手规模约800万（来源：中国互联网协会2023年报）
- 2023年外卖行业市场规模突破1.2万亿元
- 某头部平台骑手平均月收入：约5500元（平台官方数据，骑手反映实际更低）
- 骑手工伤类纠纷案件：2023年同比增长34%

===记者手记===
骑手们夹在平台算法与城市需求之间，是数字经济高速发展背后容易被忽视的群体。这个选题具有很强的社会价值与传播潜力。
"""

with open(os.path.join(BASE, "project/source_materials/interview_raw_notes.txt"), "w", encoding="utf-8") as f:
    f.write(raw_interview)

# 2. Messy platform performance data for previous related articles (needs diagnosis)
performance_data = {
    "report_period": "2024-05-01 to 2024-05-31",
    "articles": [
        {
            "id": "ART001",
            "title": "震惊！外卖骑手月入过万竟是这个原因！",
            "platform": "wechat",
            "metrics": {
                "reads": 58200,
                "likes": 312,
                "comments": 45,
                "shares": 89,
                "avg_read_duration_seconds": 18,
                "estimated_full_read_rate_percent": 8.2
            },
            "content_type": "图文"
        },
        {
            "id": "ART002",
            "title": "外卖骑手调查报告（完整版）",
            "platform": "wechat",
            "metrics": {
                "reads": 12300,
                "likes": 1890,
                "comments": 567,
                "shares": 2340,
                "avg_read_duration_seconds": 312,
                "estimated_full_read_rate_percent": 71.4
            },
            "content_type": "深度图文"
        },
        {
            "id": "ART003",
            "title": "骑手维权这件事你必须知道",
            "platform": "douyin",
            "metrics": {
                "plays": 23400,
                "likes": 3200,
                "comments": 890,
                "shares": 1200,
                "completion_rate_percent": 12.3,
                "average_watch_seconds": 7.2,
                "video_duration_seconds": 58
            },
            "content_type": "短视频"
        },
        {
            "id": "ART004",
            "title": "三分钟了解外卖骑手困境",
            "platform": "douyin",
            "metrics": {
                "plays": 187600,
                "likes": 45200,
                "comments": 12300,
                "shares": 23400,
                "completion_rate_percent": 68.9,
                "average_watch_seconds": 152,
                "video_duration_seconds": 220
            },
            "content_type": "短视频"
        },
        {
            "id": "ART005",
            "title": "外卖平台最新政策解读#外卖骑手#劳动权益",
            "platform": "weibo",
            "metrics": {
                "reads": 342000,
                "likes": 2100,
                "comments": 1890,
                "shares": 8900,
                "repost_rate_percent": 2.6
            },
            "content_type": "图文"
        }
    ],
    "notes": "本期数据为上月存档，部分字段单位混乱，请核实后使用。"
}

with open(os.path.join(BASE, "project/analytics/raw/may_performance_data.json"), "w", encoding="utf-8") as f:
    json.dump(performance_data, f, ensure_ascii=False, indent=2)

# 3. A brief from the editor (the actual task trigger)
editor_brief = """
编辑部工作指令 - 外卖骑手劳动权益专题
下发时间：2024年6月12日
负责人：内容运营团队

【背景】
上述采访素材已采集完毕（见 interview_raw_notes.txt）。上月相关内容的数据分析报告（见 may_performance_data.json）也已整理完毕。

【任务要求】
请完成以下工作，输出文件名为 content_package.json：

1. 基于采访原始素材，按照我们全媒体运营规范，生成面向四个主要平台的内容适配方案：
   - 微信公众号
   - 微博
   - 抖音
   - 小红书

2. 对上月的五篇相关内容（may_performance_data.json）进行诊断分析，找出问题所在并给出改进建议。

3. 将以上所有内容整合到一个结构化的 JSON 文件中。

注意：内容适配必须真正体现各平台的差异化运营逻辑，不能"一键分发"做成一样的内容。数据诊断也需要有理有据。
"""

with open(os.path.join(BASE, "project/editor_brief.txt"), "w", encoding="utf-8") as f:
    f.write(editor_brief)

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk(BASE):
    for fname in files:
        fpath = os.path.join(root, fname)
        print(f"  {fpath}")