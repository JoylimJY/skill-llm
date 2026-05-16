import os
import random

random.seed(42)

# Create directory structure
dirs = [
    "/workspace",
    "/workspace/account_data",
    "/workspace/account_data/history",
    "/workspace/account_data/history/2024_q3",
    "/workspace/account_data/history/2024_q4",
    "/workspace/drafts",
    "/workspace/drafts/rejected",
    "/workspace/drafts/archived",
    "/workspace/resources",
    "/workspace/resources/images",
    "/workspace/resources/templates",
    "/workspace/notes",
    "/workspace/reports",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ── Main task inputs ──────────────────────────────────────────────────────────

# 1. Performance metrics CSV with bad numbers
metrics_csv = """\
metric_name,value,unit,period
impression_count,12400,次,2024-12-01至2024-12-07
click_rate,2.1,%,2024-12-01至2024-12-07
completion_rate,18,%,2024-12-01至2024-12-07
interaction_rate,0.3,%,2024-12-01至2024-12-07
new_followers,34,人,2024-12-01至2024-12-07
share_count,28,次,2024-12-01至2024-12-07
comment_count,19,条,2024-12-01至2024-12-07
like_count,87,次,2024-12-01至2024-12-07
"""
with open("/workspace/account_data/account_metrics.csv", "w", encoding="utf-8") as f:
    f.write(metrics_csv)

# 2. Content brief describing 3 article topics + 1 micro post topic
content_brief = """\
账号定位：个人理财与财务自由，面向25-40岁城市白领

=== 文章选题任务 ===

选题A（知识科普类）：
主题：为什么很多人存了10年钱反而越来越穷？
目标人群：月收入5000-15000元的工薪族
核心内容：通货膨胀侵蚀购买力、低风险低收益陷阱、理财误区分析
写作要求：需要用数据和案例说明，读者要有"原来如此"的顿悟感

选题B（情感故事类）：
主题：我身边一个普通工厂工人，靠每月500元理财，40岁提前退休的故事
目标人群：认为自己收入太低无法理财的普通人
核心内容：真实人物故事，从怀疑到改变的心理历程，具体操作方法
写作要求：有温度，有冲突，让读者觉得"我也能做到"

选题C（实用教程类）：
主题：工资发了当天应该怎么分配？手把手教你管理家庭收入
目标人群：刚工作或刚成家、没有理财习惯的年轻人
核心内容：具体分配比例和步骤，工具推荐，常见错误规避
写作要求：操作性强，步骤清晰，读者能照做

=== 微头条任务 ===

话题：月薪8000的人，为什么比月薪5000的人存款还少？
要求：讨论性强，能引发共鸣和评论
"""
with open("/workspace/content_brief.txt", "w", encoding="utf-8") as f:
    f.write(content_brief)

# ── Distractor files ──────────────────────────────────────────────────────────

# Old draft articles (messy, incomplete)
old_draft_1 = """\
震惊！这个理财方法让月薪3000的人实现财务自由！不转不是中国人！

【草稿未完成】
理财其实很简单，就是要...
（此处省略，待补充）
数据来源：某不知名网站2019年统计
注意：这篇可能有点夸张，先存着
"""
with open("/workspace/drafts/rejected/old_draft_finance_1.txt", "w", encoding="utf-8") as f:
    f.write(old_draft_1)

old_draft_2 = """\
必看！2024年最值得关注的10大理财产品（合法合规版）

内容框架：
1. 货币基金
2. 国债
3. 银行理财
4. 指数基金
... （未完成，数据需要更新）

注意事项：需要去掉"必看"这个词，平台会限流
"""
with open("/workspace/drafts/rejected/old_draft_finance_2.txt", "w", encoding="utf-8") as f:
    f.write(old_draft_2)

# Archived content plan
archived_plan = """\
2024年Q4内容计划（已归档）

11月：聚焦双11消费陷阱系列
12月：年终奖理财系列（未执行完）

备注：账号数据很差，前同事离职前说是标题和文章结构有问题，具体原因不清楚
账号近期展现量和点击率都不正常，需要全面诊断
"""
with open("/workspace/account_data/history/2024_q4/content_plan_q4.txt", "w", encoding="utf-8") as f:
    f.write(archived_plan)

# Historical weekly reports (distractors)
for week in range(1, 5):
    report_content = f"""\
第{week}周周报（2024年Q3）
展现量：{random.randint(8000, 20000)}
点击：{random.randint(200, 800)}
新增粉丝：{random.randint(10, 60)}
问题：内容质量参差不齐
"""
    with open(f"/workspace/account_data/history/2024_q3/week{week}_report.txt", "w", encoding="utf-8") as f:
        f.write(report_content)

# Image list (distractor)
image_list = """\
图片资源清单
finance_cover_1.jpg - 存钱罐图片
chart_inflation.png - 通货膨胀走势图
person_working.jpg - 办公室场景
coins_stacked.jpg - 硬币叠放
calculator_desk.jpg - 计算器桌面
"""
with open("/workspace/resources/images/image_list.txt", "w", encoding="utf-8") as f:
    f.write(image_list)

# Competitor analysis notes (distractor)
competitor_notes = """\
竞品分析笔记（粗略）
- 账号A：粉丝23万，主要发视频，更新很频繁
- 账号B：粉丝8万，图文为主，标题都很抓眼球
- 账号C：粉丝15万，专注基金话题

观察：他们的标题都比我们的短，而且经常用具体数字
"""
with open("/workspace/notes/competitor_analysis.txt", "w", encoding="utf-8") as f:
    f.write(competitor_notes)

# Template placeholder (distractor, incomplete)
template_placeholder = """\
【模板库 - 待完善】
这个文件夹用来存放标题模板和文章模板
目前为空，需要根据平台规则重新整理
"""
with open("/workspace/resources/templates/template_notes.txt", "w", encoding="utf-8") as f:
    f.write(template_placeholder)

# Keyword research (distractor)
keywords_file = """\
关键词研究（未整理）
理财,5800000
基金,3200000
股票,7100000
存钱,2100000
财务自由,1800000
工资,4500000
副业,3900000
投资,6200000
"""
with open("/workspace/resources/keyword_research.csv", "w", encoding="utf-8") as f:
    f.write(keywords_file)

# Brand voice notes (distractor)
brand_notes = """\
品牌调性备忘
- 不要太高冷，要接地气
- 数据要有出处
- 不要夸大收益
- 语气像在跟朋友说话
"""
with open("/workspace/notes/brand_voice.txt", "w", encoding="utf-8") as f:
    f.write(brand_notes)

# Empty reports directory with a placeholder
with open("/workspace/reports/.gitkeep", "w") as f:
    f.write("")

print("Workspace initialized successfully.")
print("Files created:")
for root, dirs_, files in os.walk("/workspace"):
    for fname in files:
        print(f"  {os.path.join(root, fname)}")