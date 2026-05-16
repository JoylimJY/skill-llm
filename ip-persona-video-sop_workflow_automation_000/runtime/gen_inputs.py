import os
import json
import random

random.seed(42)

BASE = "/workspace"

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "project_tcm_ip/phase1_research/competitor_analysis",
    "project_tcm_ip/phase1_research/industry_reports",
    "project_tcm_ip/phase1_research/customer_insights",
    "project_tcm_ip/phase2_interview/audio_backups",
    "project_tcm_ip/phase2_interview/raw_notes",
    "project_tcm_ip/phase3_script",
    "project_tcm_ip/phase4_shooting/equipment_checklist",
    "project_tcm_ip/phase4_shooting/location_scouting",
    "project_tcm_ip/phase6_editing/footage_log",
    "project_tcm_ip/phase7_publish/platform_specs",
    "internal_templates",
    "archive/old_projects/client_A",
    "archive/old_projects/client_B",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────

# Competitor analysis (distractor)
with open(os.path.join(BASE, "project_tcm_ip/phase1_research/competitor_analysis/top_accounts.csv"), "w", encoding="utf-8") as f:
    f.write("账号名称,平台,粉丝数,主要内容,变现方式\n")
    f.write("中医张大夫,抖音,120万,健康科普,课程+带货\n")
    f.write("本草堂李医生,小红书,45万,养生食谱,会员社群\n")
    f.write("国医传承王老师,视频号,22万,经络讲解,线下工作坊\n")
    f.write("艾灸调理师陈姐,抖音,88万,体质调理,私信咨询\n")

with open(os.path.join(BASE, "project_tcm_ip/phase1_research/competitor_analysis/hit_content_analysis.txt"), "w", encoding="utf-8") as f:
    f.write("爆款内容拆解报告\n\n")
    f.write("1. 《为什么现代人越补越虚》- 播放量 1200万\n")
    f.write("   形式：口播+动画字幕\n   叙事：痛点切入→原理讲解→解决方案\n")
    f.write("2. 《我用这个方法帮300个失眠患者》- 播放量 890万\n")
    f.write("   形式：documentary风格\n   叙事：案例故事→方法揭秘→情感共鸣\n")
    f.write("3. 《从西医到中医，我经历了什么》- 播放量 650万\n")
    f.write("   形式：坐谈口播\n   叙事：逆袭故事→价值观输出\n")

# Industry report (distractor)
with open(os.path.join(BASE, "project_tcm_ip/phase1_research/industry_reports/tcm_market_2024.txt"), "w", encoding="utf-8") as f:
    f.write("中医健康行业分析报告 2024\n\n")
    f.write("行业规模：2023年中医服务市场规模达4200亿元，同比增长18%\n")
    f.write("主要赛道：体质调理、针灸推拿、中药养生、经络疏通\n")
    f.write("用户画像：25-45岁女性为主，注重预防性健康管理\n")
    f.write("痛点：正规中医资源稀缺，信任建立成本高\n")
    f.write("机会点：线上知识付费+线下诊所结合模式\n")

# Customer insights (distractor)
with open(os.path.join(BASE, "project_tcm_ip/phase1_research/customer_insights/comment_analysis.json"), "w", encoding="utf-8") as f:
    json.dump({
        "top_questions": [
            "湿气重怎么调理？",
            "月经不调能用中医治吗？",
            "艾灸和针灸哪个更适合我？",
            "自学中医靠谱吗？",
            "网上买的中药安全吗？"
        ],
        "resonance_topics": ["亚健康", "失眠", "体质差", "西医治不好的病"],
        "unmet_needs": ["可信赖的在线问诊", "系统性的自我调理课程"]
    }, f, ensure_ascii=False, indent=2)

# Equipment checklist (distractor)
with open(os.path.join(BASE, "project_tcm_ip/phase4_shooting/equipment_checklist/gear_list.md"), "w", encoding="utf-8") as f:
    f.write("# 拍摄器材清单\n\n")
    f.write("- [ ] Pocket 3 相机 x2\n")
    f.write("- [ ] 补光灯（面光）x1\n")
    f.write("- [ ] 补光灯（背光）x1\n")
    f.write("- [ ] 收声麦（领夹式）x2\n")
    f.write("- [ ] 备用电池 x4\n")
    f.write("- [ ] 存储卡 128G x4\n")

# Location scouting (distractor)
with open(os.path.join(BASE, "project_tcm_ip/phase4_shooting/location_scouting/locations.txt"), "w", encoding="utf-8") as f:
    f.write("备选拍摄场景\n\n")
    f.write("A. 诊所内：中药柜背景，暖黄灯光，有绿植\n")
    f.write("B. 书房：医书+茶具，安静，自然采光充足\n")
    f.write("C. 户外：公园/茶园，需便携反光板\n")
    f.write("首选：A方案（IP最放松）\n")

# Old project archives (distractors)
with open(os.path.join(BASE, "archive/old_projects/client_A/script_v3_final_FINAL.md"), "w", encoding="utf-8") as f:
    f.write("# 旧项目脚本（健身教练IP）\n\n这是一个已完成的项目存档，与当前任务无关。\n")

with open(os.path.join(BASE, "archive/old_projects/client_B/persona_tags.txt"), "w", encoding="utf-8") as f:
    f.write("标签：职场妈妈/逆袭创业/真实感/接地气/有温度\n")

# Internal templates (distractors - intentionally wrong/old format)
with open(os.path.join(BASE, "internal_templates/old_script_template_v1.docx.txt"), "w", encoding="utf-8") as f:
    f.write("旧版脚本模板（v1，已废弃）\n请使用最新SOP流程。\n")

with open(os.path.join(BASE, "internal_templates/interview_guide_draft.txt"), "w", encoding="utf-8") as f:
    f.write("访谈参考问题（草稿）\n1. 你为什么选择这个行业？\n2. 遇到过什么困难？\n3. 你的核心理念是什么？\n")

# Footage log (distractor)
with open(os.path.join(BASE, "project_tcm_ip/phase6_editing/footage_log/raw_clips.csv"), "w", encoding="utf-8") as f:
    f.write("clip_id,duration,content,status\n")
    f.write("001,00:03:22,开场自我介绍,待剪辑\n")
    f.write("002,00:07:15,童年故事段落,待剪辑\n")
    f.write("003,00:05:44,转折点故事,待剪辑\n")

# Platform specs (distractor)
with open(os.path.join(BASE, "project_tcm_ip/phase7_publish/platform_specs/ratio_guide.txt"), "w", encoding="utf-8") as f:
    f.write("各平台视频规格\n抖音：9:16竖屏，1080x1920\n小红书：3:4或9:16\n视频号：3:4\n")

# ── CORE INPUT FILES ─────────────────────────────────────────────────────────

# Interview transcript - Growth story (messy, verbose, raw)
growth_interview = """访谈记录 - 成长故事部分
受访人：林晓薇（中医师，32岁）
采访日期：2026-03-10
采访人：陈操盘

【注意：以下为现场速记，未经整理，包含口语、停顿、重复】

陈：你是什么时候开始接触中医的？

林：哎，这个说来话长哦。我从小身体就不好，经常生病，小时候我妈就带我去看中医。那个老大夫——我现在还记得他的样子，白胡子，慢悠悠的——他就把脉，然后跟我妈说，这孩子脾胃虚，要从根上调。那时候我大概七八岁吧。然后他给我开了一副汤药，苦死了（笑）。但是喝了三个月，真的好多了。那时候就觉得，哇，这东西好神奇。

陈：后来你去学西医了对吗？

林：对对对。因为家里人觉得中医不够"科学"，我爸妈希望我学西医，说以后找工作稳定。我就乖乖去学了。在医院实习的时候……那是我人生中最难受的一段时间。我记得有个病人，慢性疲劳综合征，各种检查全部正常，西医真的没有什么好的方案，就说你注意休息。但你看他的眼睛，那种绝望——我心里真的很难受，觉得自己帮不上忙。那时候就一直在想，如果用中医的思路来看这个人……

陈：那你是怎么转回中医的？

林：转折点是2018年。我自己病了，压力太大，失眠、焦虑、月经也乱了。去看了好几个西医，说没问题，给我开了安眠药。我不想吃那个药。就去找了一个老师——我恩师，程老师——他一把脉，说你这是肝气郁结，心脾两虚。就开了七帖药，加上推荐我练八段锦。一个月不到，整个人就好了。我当时就在诊室里哭了，真的。就觉得——用了我后来常说的一句话——"身体有它自己的语言，中医是唯一听得懂的。"

陈：那后来创业是怎么决定的？

林：2020年，疫情期间，我就开始在网上分享一些养生知识，没想到很多人来问我。后来就开了个小工作室。一开始真的很难，就我一个人，没有资金，家人也不理解，觉得开诊所才叫正经事。我记得第一个月，就来了三个客户（笑）。但我没放弃，因为我相信，每个普通人都应该有机会了解自己的身体，不应该只有有钱有资源的人才能得到好的健康管理。这个信念一直支撑着我。

陈：现在做到什么阶段了？

林：现在工作室有稳定的300多个学员，在线课程也有两万多人购买了。去年营收大概在150到200万之间吧。但我觉得这不是最重要的，最重要的是我的学员真的在改变。有个阿姨，失眠20年，跟了我的课3个月，现在能睡着了，她给我发语音，哭着说谢谢……那个时候我才觉得，对，这就是我应该做的事。

陈：你觉得你和别的中医IP最大的不同是什么？

林：我不卖玄学，我讲逻辑。中医不是迷信，是有完整理论体系的。我一直说，"中医的智慧，现代人用得上。"另外就是，我愿意讲我自己的故事，包括我的弯路，我的低谷，这些我都不藏着掖着。我觉得真实才能打动人。

陈：有没有让你特别崩溃的时刻？

林：有。2021年，有个学员在网上发帖子说我的课程效果不好，还说我是骗子。那段时间真的很黑暗，质疑自己，要不要放弃。我老公那时候说了一句话，他说，你要相信你服务过的那200个人，不是那一个人。那句话把我拉回来了。然后我就想，不管怎样，"只要我真的在帮人，时间会证明一切。"

陈：你现在最想传递给学员的是什么？

林：就是——你的身体比你想象中更有智慧，你只需要学会和它对话。这其实也就是"身体有它自己的语言，中医是唯一听得懂的。"（笑）我好像老在说这句话。

【速记结束，共约90分钟访谈，此为节选核心段落】
"""

with open(os.path.join(BASE, "project_tcm_ip/phase2_interview/raw_notes/interview_growth_story.txt"), "w", encoding="utf-8") as f:
    f.write(growth_interview)

# Interview transcript - Business/Product
business_interview = """访谈记录 - 事业与产品部分
受访人：林晓薇
采访日期：2026-03-11

陈：你现在的产品线是怎么设计的？

林：主要三块。第一是入门课，99块钱，教大家认识自己的体质，大概2万多人买了。第二是系统课，2980，三个月的体质调理课，有直播答疑，这个有300多个学员在学。第三是一对一咨询，8800一年，我亲自服务，就30个名额，现在基本满了。

陈：你觉得你的核心差异化是什么？

林：三个词：真实、系统、接地气。我不装，讲自己踩过的坑；我有体系，不是东一块西一块的碎片知识；我用普通人听得懂的话讲中医，不用那些听不懂的术语吓人。

陈：你服务的主要是什么样的人？

林：25到45岁的女性居多，白领、全职妈妈都有。她们的共同特点是——知道自己身体有问题，但不知道从哪里入手，对西医已经有点失望，但又不完全信任中医。我就是要帮这类人找到方向。

陈：你觉得目前产品有什么不足？

林：入门课太便宜了，性价比倒是高，但学员粘性不够，很多人买了不学。系统课其实还可以再涨价，内容值这个钱。一对一我觉得挺好的，就是太累（笑），一年30个人已经接近我的极限了。

陈：有什么想法但还没做的？

林：想出一本书，把我的调理体系整理出来。还想做线下工作坊，让学员体验真实的诊断过程。这两个是接下来1-2年要做的事。

【访谈结束】
"""

with open(os.path.join(BASE, "project_tcm_ip/phase2_interview/raw_notes/interview_business_product.txt"), "w", encoding="utf-8") as f:
    f.write(business_interview)

# A messy "previous attempt" at persona profile that is WRONG (wrong format, incomplete)
bad_attempt = {
    "client": "林晓薇",
    "notes": "中医师，做过西医，转型创业",
    "possible_tags": ["中医", "健康", "女性", "创业"],
    "some_topics": ["湿气调理", "失眠怎么办", "体质测试"],
    "status": "草稿，未完成"
}
with open(os.path.join(BASE, "project_tcm_ip/phase3_script/DRAFT_incomplete_profile.json"), "w", encoding="utf-8") as f:
    json.dump(bad_attempt, f, ensure_ascii=False, indent=2)

# A messy draft script that is WRONG (uses formal/written language, wrong structure)
bad_script_draft = """# 旧版脚本草稿（格式错误，已废弃）

本人具备深厚的中医理论基础及丰富的临床实践经验。
经过多年的学习与探索，本人成功建立了系统化的体质调理课程体系。
本人的核心价值观体现在对传统医学的传承与现代化应用方面。
目前，本人已服务学员逾两万人次，并持续获得广泛好评。

问题：
- 语言太书面化，不符合SOP要求
- 没有情绪曲线
- 没有金句
- 段落太长
"""
with open(os.path.join(BASE, "project_tcm_ip/phase3_script/DRAFT_wrong_language_style.md"), "w", encoding="utf-8") as f:
    f.write(bad_script_draft)

print("Workspace generated successfully.")
print(f"Files created in {BASE}")