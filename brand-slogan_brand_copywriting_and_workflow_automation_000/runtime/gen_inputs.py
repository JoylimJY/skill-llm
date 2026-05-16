import os
import json
import random

random.seed(42)

# Create directory structure with distractors
dirs = [
    "/workspace/brand_briefs",
    "/workspace/brand_briefs/archive",
    "/workspace/brand_briefs/drafts",
    "/workspace/marketing/campaigns",
    "/workspace/marketing/reports",
    "/workspace/assets/logos",
    "/workspace/assets/copy",
    "/workspace/competitor_analysis",
    "/workspace/internal/legal",
    "/workspace/internal/finance",
    "/workspace/output",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# ---- DISTRACTOR FILES ----

# 1. Old competitor analysis report
with open("/workspace/competitor_analysis/herbal_tea_market_2022.txt", "w", encoding="utf-8") as f:
    f.write("""凉茶市场竞争分析报告 2022
==========================
主要竞争对手：王老吉、加多宝、和其正
市场份额：王老吉 38%，加多宝 32%，其他 30%
主要诉求：去火降燥、清热解毒、夏日消暑
渠道分析：商超 45%，餐饮 30%，便利店 25%
建议：差异化定位，聚焦特定人群

注意：此报告为2022年版本，数据可能过时。
""")

# 2. Old failed slogan list (distractors - adjective-heavy, wrong format)
with open("/workspace/brand_briefs/archive/failed_slogans_v1.txt", "w", encoding="utf-8") as f:
    f.write("""历史淘汰口号（勿用）
===================
优质凉茶，健康首选
专业配方，高效去火
纯天然草本，品质保证
清凉一夏，畅饮无忧
匠心传承，百年老字号

以上口号已被市场部否决，原因：广告腔太重，缺乏记忆点
""")

# 3. Random finance file
with open("/workspace/internal/finance/Q3_budget.csv", "w", encoding="utf-8") as f:
    f.write("""部门,预算(万元),已用(万元),剩余(万元)
市场部,500,320,180
产品部,300,210,90
运营部,200,150,50
研发部,800,600,200
""")

# 4. Distractor legal file
with open("/workspace/internal/legal/trademark_notes.txt", "w", encoding="utf-8") as f:
    f.write("""商标注意事项
============
品牌名"清远堂"已于2019年注册
商标类别：30类（饮料）、5类（药品相关）
注意：不得使用"治疗""药用"等医疗声称
版权所有，内部资料
""")

# 5. Random marketing campaign brief (different brand, distractor)
with open("/workspace/marketing/campaigns/summer_promo_2024.txt", "w", encoding="utf-8") as f:
    f.write("""2024夏季促销方案（旺仔牛奶专项）
================================
主题：夏日清凉，旺仔相伴
预算：200万元
渠道：抖音、小红书、线下商超堆头
KPI：销售额环比增长20%
注意：此方案与清远堂品牌无关
""")

# 6. Logo asset placeholder
with open("/workspace/assets/logos/logo_specs.txt", "w", encoding="utf-8") as f:
    f.write("Logo specifications: 主色调#2E8B57, 辅色#F5DEB3, 字体：楷体加粗\n尺寸要求：主logo 300x100px，favicon 32x32px")

# 7. Old copy draft (partial, messy)
with open("/workspace/assets/copy/old_copy_draft.txt", "w", encoding="utf-8") as f:
    f.write("""旧文案草稿（废弃）
==================
「清远堂凉茶，去火好帮手」——已废弃（含形容词"好"的滥用）
「一罐在手，火气全无」——已废弃（无品牌名）
「广东人的清远堂」——备用
创作思路：需要更多口语化，接地气
""")

# 8. Competitor copy examples
with open("/workspace/competitor_analysis/competitor_copy.txt", "w", encoding="utf-8") as f:
    f.write("""竞品文案参考（仅供分析）
========================
王老吉：「怕上火，喝王老吉」——押韵好，有品牌名，口语
加多宝：「全国销量领先的红罐凉茶，加多宝」——书面腔
和其正：「清火气，养元气，和其正」——对仗工整
分析：王老吉文案最强，值得研究押韵和口语化策略
""")

# 9. Draft brand values note (partial, not enough for direct use)
with open("/workspace/brand_briefs/drafts/brand_values_notes.txt", "w", encoding="utf-8") as f:
    f.write("""品牌价值挖掘笔记（未完成）
==========================
清远堂凉茶主要卖点：
- 广东清远道地草本（暂未确认哪些草药）
- 传统配方？（需要核实年份）
- 目标客户可能是... 年轻人？上班族？

TODO：联系产品部确认配方、临床数据
注意：这只是草稿，不是最终资料
""")

# 10. Random HR distractor
with open("/workspace/internal/legal/employment_notes.txt", "w", encoding="utf-8") as f:
    f.write("""人事备忘录
==========
2024年Q4招聘计划：市场专员2名，文案策划1名
薪资范围：10k-18k
面试官：李总
截止日期：2024-11-30
""")

# ---- MAIN TASK INPUT FILE ----
# The actual brand brief - intentionally messy, with missing fields, mixed Chinese/English,
# incomplete data requiring auto-derivation per SKILL.md rules

brand_brief_content = """\
清远堂凉茶 · 品牌创作需求单
==============================
（内部工作文件 v2.3，2024-10-15，市场部整理）

【品牌基本信息】
品牌名称：清远堂
品类：广式凉茶（罐装）
成立背景：源自广东清远，祖传配方，第四代传人主理，已有超过120年历史

【产品核心价值】（部分确认，部分待定）
✓ 去火降燥（主诉求）
✓ 清热解毒
✓ 睡前喝了睡得好（市场测试反馈）
? 具体草药成分（待产品部确认，暂勿在文案中提及具体成分名）

【资源禀赋/背书】
- 广东清远道地取材（山泉水源）
- 四代家传秘方，逾120年
- 2023年获广东省非物质文化遗产认定（注：需再次核实）
- 正在申请国家级非遗（未完成，暂不对外宣传）

【目标人群】（市场调研结果，置信度80%）
主力人群：25-45岁城市上班族，尤其是广东、广西本地消费者
次要人群：出差/旅行到广东的外省游客（体验广东文化）
潜力人群：关注养生的年轻人（Z世代，18-25岁）

【核心使用场景】
- 加班熬夜后喝（去火）
- 吃火锅/烧烤/辛辣食物时配饮
- 睡前养生（市场测试新场景）
- 广东送礼（春节/中秋）

【文化原力线索】（文案部整理，供参考）
- 广东人常说：「喝凉茶，去火气」（民间口语）
- 熬夜文化：「不怕熬，就怕火」
- 养生俗语：「药补不如食补，食补不如水补」
- 四季养生：「春夏去火，秋冬润燥」

【竞争环境说明】
主要对手：王老吉（怕上火，喝王老吉）、加多宝
差异化方向：王老吉是"预防"场景，清远堂主打"已经上火了"的救急场景，同时强调百年传承

【市场部备注】（重要！）
- 之前找外部公司做的口号全是形容词堆砌，客户觉得没有记忆点
- 希望口号能像「怕上火喝王老吉」一样朗朗上口、押韵
- 老板点名要有"清远堂"三个字在口号里
- 字数不要太长，说太长了记不住
- 需要多给几个选项排个优先级，让老板选

【特别要求】
输出文件名：qingyuantang_proverbs.json
"""

with open("/workspace/brand_briefs/qingyuantang_brief_v2.3.txt", "w", encoding="utf-8") as f:
    f.write(brand_brief_content)

# 11. A red-herring JSON template (wrong/incomplete format)
wrong_template = {
    "brand": "清远堂",
    "slogans": [],
    "note": "这是一个空模板，格式未定，供参考"
}
with open("/workspace/brand_briefs/drafts/slogan_template_DRAFT.json", "w", encoding="utf-8") as f:
    json.dump(wrong_template, f, ensure_ascii=False, indent=2)

# 12. Scoring rubric partial notes (wrong/incomplete, a trap)
with open("/workspace/marketing/reports/scoring_notes_WRONG.txt", "w", encoding="utf-8") as f:
    f.write("""评分参考（内部草稿，未经验证）
================================
口号好不好，主要看：
1. 是否朗朗上口（50分）
2. 是否有品牌名（30分）
3. 字数（20分）

注意：这只是市场部的主观感受，不是最终评分标准！
""")

print("Workspace generated successfully.")
print("Key task file: /workspace/brand_briefs/qingyuantang_brief_v2.3.txt")
print("Expected output: /workspace/output/qingyuantang_proverbs.json (to be created by agent)")