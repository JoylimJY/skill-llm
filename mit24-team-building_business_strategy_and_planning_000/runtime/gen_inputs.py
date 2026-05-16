import os
import random
import json

random.seed(42)

WORKSPACE = "/workspace"

# Directory structure
dirs = [
    "workspace/project_alpha",
    "workspace/project_alpha/market_research",
    "workspace/project_alpha/financial_models",
    "workspace/project_alpha/competitor_analysis",
    "workspace/project_alpha/technical_specs",
    "workspace/project_alpha/legal",
    "workspace/project_alpha/team_bios",
    "workspace/archive",
    "workspace/archive/phase1_ideation",
    "workspace/archive/phase2_market",
    "workspace/archive/phase3_business_model",
    "workspace/archive/phase4_strategy",
    "workspace/templates",
    "workspace/templates/generic",
    "workspace/investor_materials",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# --- Distractor files ---

# 1. Market research notes (distractor)
with open("workspace/project_alpha/market_research/market_size_notes.txt", "w") as f:
    f.write("""法律科技市场调研笔记（2024年1月）
============================
中国小型律所市场规模：约32万家律所，85%为50人以下小所
主要痛点：合同审查耗时（平均2-4小时/份），人力成本高
现有方案：传统人工审查，部分使用通用文档工具
竞品：法大大（电子签）、威科先行（大所为主）
目标客户：10-50人规模律所，月均合同审查量50-200份
""")

# 2. Competitor analysis (distractor)
with open("workspace/project_alpha/competitor_analysis/competitor_matrix.csv", "w") as f:
    f.write("""竞品名称,目标客户,价格,核心功能,弱点
法大大,所有律所,按量计费,电子签名,无AI审查
威科先行,大型律所,高端定价,知识库检索,价格过高
ChatDoc,个人用户,免费/低价,通用文档问答,法律专业性不足
LegalMind,外资律所,SaaS订阅,合规检查,不适配中国法规
""")

# 3. Financial model (distractor)
with open("workspace/project_alpha/financial_models/unit_economics.json", "w") as f:
    json.dump({
        "target_customer": "10-50人律所",
        "monthly_price": 2980,
        "annual_price": 29800,
        "CAC_estimate": 3500,
        "LTV_estimate": 89400,
        "payback_period_months": 1.2,
        "gross_margin_pct": 78
    }, f, ensure_ascii=False, indent=2)

# 4. Technical spec stub (distractor)
with open("workspace/project_alpha/technical_specs/tech_stack_draft.md", "w") as f:
    f.write("""# 技术栈初步规划

## 后端
- Python / FastAPI
- PostgreSQL + Redis
- LLM: GPT-4 API / 本地微调模型（待定）

## 前端
- React + Ant Design Pro
- 支持Web和钉钉小程序

## AI核心模块
- 合同条款提取：基于NER微调
- 风险识别：分类模型 + RAG
- 修改建议：LLM Chain

## 部署
- 阿里云ECS + OSS
- 私有化部署选项（大客户需求）

## 注意事项
本文档为草稿，正式技术规格待确定
""")

# 5. Legal entity notes (distractor)
with open("workspace/project_alpha/legal/company_registration_notes.txt", "w") as f:
    f.write("""公司注册事项备忘
- 主体：有限责任公司
- 注册地：上海浦东新区
- 注册资本：100万元（认缴）
- 股东：待定
- 经营范围：软件开发、人工智能技术服务
- 所需文件：身份证、章程、地址证明
- 预计时间：2-3周
- 联系律师：张律师 138-xxxx-xxxx
""")

# 6. Team bios (distractors - incomplete)
with open("workspace/project_alpha/team_bios/founder_bio.txt", "w") as f:
    f.write("""创始人简介（草稿）
姓名：李明
背景：前某头部律所合伙人，执业15年
特长：商务谈判、行业资源、客户关系
痛点理解：深度了解律所运营痛点
注：技术背景薄弱，需要技术合伙人
""")

with open("workspace/project_alpha/team_bios/tech_lead_candidate.txt", "w") as f:
    f.write("""技术候选人背景
姓名：王磊
背景：前阿里云NLP工程师，8年经验
特长：大模型微调、系统架构
薪资期望：高
股权期望：10-15%
注：面试反馈良好，但需确认创业意愿
""")

# 7. Archive files (distractors from previous phases)
with open("workspace/archive/phase1_ideation/problem_statement.txt", "w") as f:
    f.write("""核心痛点（步骤3产出）
目标客户：10-50人规模律所的主任/合伙人
核心痛点：合同审查效率低，新手律师错误率高，客户投诉风险
痛点量化：每份合同人工审查平均耗时3小时，月均审查50份 = 150小时/月/律师
痛点紧迫性：高（直接影响客户满意度和律所声誉）
""")

with open("workspace/archive/phase2_market/beachhead_segment.txt", "w") as f:
    f.write("""滩头市场定义（步骤6产出）
目标：上海地区10-30人商事律所
规模：约2,800家
触达渠道：律师协会、律所管理软件厂商
初期目标：12个月内签约50家
""")

with open("workspace/archive/phase3_business_model/pricing_strategy.txt", "w") as f:
    f.write("""定价策略（步骤11产出）
模式：SaaS订阅 + 按量计费混合
基础套餐：2,980元/月（含500次审查）
专业套餐：5,980元/月（含2000次审查）
企业套餐：定制
定价依据：客户愿付价值调研中位数3,200元/月
竞品参考：威科先行18,000元+/年（功能冗余）
""")

with open("workspace/archive/phase4_strategy/assumption_validation.txt", "w") as f:
    f.write("""假设验证结果（步骤18产出）
验证结论：商业可行性初步确认
关键数据：
- 访谈律所：28家
- 愿意付费比例：64%（18/28）
- 平均意愿付费：3,100元/月
- 主要顾虑：数据安全（72%）、准确率（85%）、合规性（61%）
下一步：开发MVBP，进行付费验证
""")

with open("workspace/archive/phase4_strategy/purchase_decision_criteria.txt", "w") as f:
    f.write("""客户购买决策标准（步骤14产出）
决策者：律所主任/管理合伙人
决策标准（按重要性排序）：
1. 合同审查准确率 ≥90%
2. 数据安全（私有化部署或国内合规云）
3. 易用性（不需要培训即可上手）
4. 价格在预算范围内（<5000元/月）
5. 与现有工作流集成
决策周期：1-3个月
""")

# 8. Templates (distractors)
with open("workspace/templates/generic/business_plan_template.md", "w") as f:
    f.write("""# 商业计划书模板（通用版）
## 1. 执行摘要
## 2. 市场分析
## 3. 产品/服务
## 4. 商业模式
## 5. 营销策略
## 6. 团队
## 7. 财务预测
注：这是通用模板，不代表最终输出格式
""")

# 9. Investor materials (distractor)
with open("workspace/investor_materials/pitch_deck_outline.txt", "w") as f:
    f.write("""融资路演大纲（草稿）
- 市场机会：300亿法律科技市场
- 产品：AI合同审查SaaS
- 商业模式：订阅制
- 团队：待完善
- 融资需求：300万天使轮
- 估值逻辑：待定
注意：投资人反馈需要更完整的团队和产品验证材料
""")

with open("workspace/investor_materials/investor_qa_notes.txt", "w") as f:
    f.write("""投资人问答记录（某天使投资人会面）
Q: 你们的MVBP是什么？何时能上线？
A: 还在规划中...（投资人不满意）
Q: 团队有哪些核心成员？各自职责？
A: 目前就创始人一人+技术候选人（投资人要求尽快确认团队）
Q: 如何向第一批客户演示？
A: 暂无系统性方案（需要改进）
结论：需要在下次会议前准备完整的产品验证报告
""")

# 10. A deliberately incomplete/wrong previous attempt (distractor)
with open("workspace/project_alpha/previous_attempt_mvbp_draft.txt", "w") as f:
    f.write("""【注意：这是一份被否定的草稿，请勿直接使用】

旧版MVP功能列表（错误版本）：
1. 用户注册/登录
2. 合同上传
3. AI全文审查（合规性检查）
4. 风险条款标注（高/中/低）
5. 修改建议生成
6. 对比审查（上传两份合同对比）
7. 批量处理（同时处理多份合同）
8. 团队协作（多用户共享项目）
9. 审查报告导出（PDF/Word）
10. 历史记录查询

问题：功能太多，无法在合理时间内完成，且混淆了MVP和MVBP的概念。
投资人评价：范围过大，缺乏验证商业模式的聚焦。
""")

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk("workspace"):
    for file in files:
        print(f"  {os.path.join(root, file)}")