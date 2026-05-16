import os
import random

random.seed(42)

workspace = "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "raw_materials",
    "raw_materials/regulatory",
    "raw_materials/social",
    "archive/2023/q4",
    "archive/2024/q1",
    "templates",
    "references",
    "assets",
    "published/biotech",
    "published/finance",
    "drafts/abandoned",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── SKILL.md ─────────────────────────────────────────────────────────────────
skill_md = """\
---
name: news-writing
description: 新闻素材收集、整理、写作、排版与校对的完整工作流。用于用户需要生成新闻稿、快讯、深度稿、企业新闻、活动报道，或需要对现有新闻内容进行事实核实、结构优化、标题导语改写、版式统一与发布前审校时。
---

# News Writing

按以下流程执行，确保内容可发布、可追溯、可复核。

## 1) 明确任务约束

先确认并记录：
- 新闻类型：快讯 / 通稿 / 深度稿 / 采访稿 / 活动报道
- 发布渠道：网站、公众号、邮件、内刊、社媒
- 目标读者：行业、地区、专业程度
- 输出要求：字数、语气、发布时间、是否需要中英双语

缺少约束时，先用保守默认：中性客观语气、标准新闻结构、便于二次排版的 Markdown。

## 2) 收集并整理素材

先建立"素材清单"再写作，素材至少包含：
- 原始来源：公告、采访记录、会议纪要、监管文件、统计数据
- 二级来源：权威媒体、机构网站、公开数据库
- 背景信息：时间线、关键人物/机构、历史对比数据

用表格整理素材，字段固定为：
- `编号` `事实陈述` `来源链接/出处` `时间` `地点` `可核实状态` `备注`

需要完整规范时，读取 [references/fact-check.md](references/fact-check.md)。

## 3) 写作前核实

仅把"已核实"事实写入正文；未核实内容放入"待确认列表"。

执行最小核实标准：
- 关键事实至少双来源交叉验证（原始来源优先）
- 时间、地名、人名、头衔、数字逐项核对
- 引述必须标注来源与语境，不改写原意
- 争议点显式标注"尚无独立证实"

## 4) 生成新闻正文

默认采用"倒金字塔结构"：
- 标题：结果导向，不堆砌形容词
- 导语：一句话交代 `谁-何时-何地-发生了什么-影响`
- 主体：按重要性递减展开，补充背景和数据
- 结尾：后续安排、官方回应或可执行信息

可直接基于模板产出：
- [assets/news-article-template.md](assets/news-article-template.md)

需要更多标题、导语、段落节奏规则时，读取 [references/writing-style.md](references/writing-style.md)。

## 5) 排版与可读性优化

在不改变事实前提下统一格式：
- 单段表达单一信息点
- 数字统一单位与格式（货币、百分比、同比/环比）
- 引用、数据、时间线使用小标题或列表分隔
- 保持"可扫描结构"：标题、小标题、短段、必要列表

## 6) 审校与发布前检查

发布前执行终检并输出两部分：
- `最终稿`
- `核实记录`（来源与未确认项）

终检清单：
- 事实准确：无未标注推测
- 逻辑完整：导语与正文一致
- 法律与合规：不含诽谤、隐私泄露、未经证实指控
- 语言质量：无错别字、病句、歧义指代
- 版式统一：标题层级、标点、空格、日期格式一致

## 输出格式

默认输出为以下三段：
1. `新闻正文`
2. `事实核验摘要`
3. `待补充信息`（如果为空，写"无"）
"""

with open(os.path.join(workspace, "SKILL.md"), "w", encoding="utf-8") as f:
    f.write(skill_md)

# ── Raw source 1: Official Press Release (mostly reliable, some typos) ───────
press_release = """\
【新闻稿 - 仅供参考，待最终确认】

发布单位：星弧生物科技有限公司（StarArc Biotech Co., Ltd.）
发布时间：2024年11月14日
联系人：媒体关系部  media@stararc-bio.cn

标题：星弧生物宣布 SAB-2201 三期临床试验达到主要终点

正文草稿：

星弧生物科技有限公司（以下简称"星弧生物"）今日宣布，其核心管线产品 SAB-2201（用于治疗
晚期非小细胞肺癌的口服靶向药）已在一项纳入 847 名患者的全球多中心三期临床试验（SOLAR-3
研究）中达到主要终点。

主要终点数据：
- 无进展生存期（PFS）中位数：SAB-2201 组 11.3 个月，安慰剂组 5.6 个月
- 疾病进展或死亡风险降低：52%（HR=0.48，95% CI：0.38–0.61，P<0.0001）
- 客观缓解率（ORR）：43.7%（安慰剂组 8.1%）

试验在中国、美国、德国、日本四国 62 家研究中心开展，主要研究者为上海肿瘤医院肿瘤内科
主任李明远教授（Prof. Li Mingyuan）。

公司CEO 王刚表示："SOLAR-3 的结果代表了晚期非小细胞肺癌治疗的重大突破，我们将尽快向
国家药品监督管理局（NMPA）和美国 FDA 提交上市申请。"

注意：上述数据为初步统计结果，完整数据将在2024年12月美国临床肿瘤学会（ASCO）年会上公布。
"""
with open(os.path.join(workspace, "raw_materials/press_release_draft.txt"), "w", encoding="utf-8") as f:
    f.write(press_release)

# ── Raw source 2: Internal meeting notes (contradictory numbers, informal) ───
meeting_notes = """\
会议纪要 - 内部传阅，不对外
日期：2024-11-13  星期三  下午3点
参与人员：王刚（CEO）、张晓燕（CFO）、Dr. Helen Wu（CMO）、法务李强

议题：SOLAR-3 数据读出 & 发布策略

要点记录（速记，非正式）：
1. Helen汇报：主要终点PFS达到，HR=0.48，P值很显著，统计团队昨晚确认的
2. 患者数：招募了847，完成随访的大概是831，脱落16人原因待整理
3. 王刚问ORR：Helen说SAB-2201组ORR是43.7%，但有个医生私下说可能高达50%+，
   这个数字还没有在正式统计中出现，不能用
4. 关于安全性：有3例严重不良反应（SAE）可能与药物相关，正在调查，
   法务李强说在数据正式确认前绝对不能对外说任何事
5. 竞争对手 PharmaNova 的同类产品 PN-4400 在二期失败的消息昨天刚出来，
   但没有官方来源，只是圈内传言，待核实
6. 上市申请：计划2025年Q1向NMPA提交，FDA时间线未定
7. ASCO演讲：李明远教授会在12月的ASCO口头报告这个数据（待确认摘要号）
8. 股价：今天盘前涨了18%（注：这只是传言，没有确认来源）

行动项：媒体稿由公关部起草，11月14日发出
"""
with open(os.path.join(workspace, "raw_materials/internal_meeting_notes_20241113.txt"), "w", encoding="utf-8") as f:
    f.write(meeting_notes)

# ── Raw source 3: Regulatory filing snippet ───────────────────────────────────
reg_filing = """\
国家药品监督管理局 — 临床试验登记与信息公示平台
登记号：CTR20221847
试验名称：SAB-2201治疗EGFR突变型晚期非小细胞肺癌的随机、双盲、安慰剂对照多中心III期临床试验
（SOLAR-3研究）
申办方：星弧生物科技有限公司
主要研究者：李明远（上海市肿瘤医院）
适应症：EGFR突变型晚期非小细胞肺癌（NSCLC）
试验状态：已完成随访 — 等待数据锁定
计划入组：850例  实际入组：847例
一级终点：无进展生存期（PFS）
二级终点：总生存期（OS）、客观缓解率（ORR）、安全性

登记日期：2022年06月01日
预计完成日期：2024年11月
研究中心数量：62个（中国、美国、德国、日本）
"""
with open(os.path.join(workspace, "raw_materials/regulatory/nmpa_trial_registry_CTR20221847.txt"), "w", encoding="utf-8") as f:
    f.write(reg_filing)

# ── Raw source 4: Social media post (unverified rumors) ──────────────────────
social_post = """\
[微博截图文字记录 - 2024-11-14 09:47]
用户 @biotech_insider_CN（非认证账号）：

爆料！星弧SAB-2201三期数据出来了！据说ORR超过50%！
股价明天会大涨，消息人士称FDA审批绿色通道已经确定？！
另外据说竞争对手PharmaNova的PN-4400已经彻底凉了！
大家快上车！ #SAB2201 #星弧生物 #生物医药

[转发 2341次，点赞 8921次]

---
注：此帖子未经核实，发布者为匿名账号，所有数字和说法均无官方来源支撑。
"""
with open(os.path.join(workspace, "raw_materials/social/weibo_post_20241114.txt"), "w", encoding="utf-8") as f:
    f.write(social_post)

# ── Raw source 5: Financial data note ────────────────────────────────────────
financial_note = """\
星弧生物 — 投资者关系备忘（内部）
日期：2024-11-14

当日股价变动（A股，星弧生物，代码：688XXX）：
- 开盘涨幅：约 +17.8%（数据来自Bloomberg终端，已核实）
- 市值变化：新增约 42亿人民币

分析师观点（匿名引用，待授权后可公开）：
- 某券商分析师预测：若FDA快速通道申请成功，峰值销售额可达80亿美元
- 另一分析师警告：SAE数据尚未披露，存在不确定性

注：以上财务数据仅供内部使用，未经IR部门正式确认不得对外引用。
"""
with open(os.path.join(workspace, "raw_materials/investor_relations_note_20241114.txt"), "w", encoding="utf-8") as f:
    f.write(financial_note)

# ── Distractor files ──────────────────────────────────────────────────────────

# Old unrelated article
with open(os.path.join(workspace, "archive/2023/q4/pharma_market_overview_2023.md"), "w", encoding="utf-8") as f:
    f.write("# 2023年生物医药市场年度综述\n\n全球生物医药市场规模达到 1.48 万亿美元...\n（存档，仅供参考）\n")

# Abandoned draft
with open(os.path.join(workspace, "drafts/abandoned/draft_SAB2201_phase2_results.md"), "w", encoding="utf-8") as f:
    f.write("# SAB-2201 二期结果报道草稿（已废弃）\n\n此稿已作废，请勿参考。二期ORR数据已被三期取代。\n")

# Unrelated config
with open(os.path.join(workspace, "drafts/abandoned/cms_config.yaml"), "w", encoding="utf-8") as f:
    f.write("cms:\n  platform: wordpress\n  api_endpoint: http://internal-cms.stararc.local/api\n  timeout: 30\n")

# Old template (intentionally missing required fields to be a trap)
with open(os.path.join(workspace, "templates/old_news_template_v1.md"), "w", encoding="utf-8") as f:
    f.write("""\
# [标题]

**时间：** [日期]
**来源：** [单位]

## 正文
[内容]

## 来源说明
[来源]
""")

# Competitor analysis note
with open(os.path.join(workspace, "archive/2024/q1/competitor_pharmanove_analysis.txt"), "w", encoding="utf-8") as f:
    f.write("PharmaNova PN-4400 Phase II 结果分析（2024年Q1内部报告）\n\n尚无公开数据支撑，分析基于专利申请文件推断。\n（内部机密，请勿外传）\n")

# Style guide stub (referenced but empty - agent shouldn't need it for this task)
with open(os.path.join(workspace, "references/writing-style.md"), "w", encoding="utf-8") as f:
    f.write("# Writing Style Guide\n\n（待补充）\n")

# Fact-check reference stub
with open(os.path.join(workspace, "references/fact-check.md"), "w", encoding="utf-8") as f:
    f.write("# Fact Check Standards\n\n请遵循 SKILL.md 中的素材整理规范，使用规定字段格式。\n")

# Asset template (minimal, agent should follow SKILL.md structure not this)
with open(os.path.join(workspace, "assets/news-article-template.md"), "w", encoding="utf-8") as f:
    f.write("""\
# [标题]

[导语]

## 正文

[主体内容]

## 后续

[结尾信息]
""")

# Published examples (distractors)
with open(os.path.join(workspace, "published/biotech/2024_q1_gene_therapy_launch.md"), "w", encoding="utf-8") as f:
    f.write("# 某基因疗法获批上市\n\n2024年3月，XX公司宣布...\n")

with open(os.path.join(workspace, "published/finance/ipo_report_2024.md"), "w", encoding="utf-8") as f:
    f.write("# 生物医药IPO市场2024中期回顾\n\n上半年共有12家生物科技公司上市...\n")

# Log file distractor
with open(os.path.join(workspace, "raw_materials/data_pull_log.txt"), "w", encoding="utf-8") as f:
    f.write("2024-11-14 08:00:01 INFO  Bloomberg data pull started\n2024-11-14 08:00:45 INFO  Retrieved 1 record for 688XXX\n2024-11-14 08:00:46 INFO  Done.\n")

print("Workspace initialized successfully.")
print("Files created:")
for root, dirs_list, files in os.walk("/workspace"):
    for fname in files:
        print(f"  {os.path.join(root, fname)}")