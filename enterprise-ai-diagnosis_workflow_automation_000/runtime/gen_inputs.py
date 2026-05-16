import os
import random

random.seed(42)

WORKSPACE = "/workspace"

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "company_data/finance",
    "company_data/operations",
    "company_data/hr",
    "company_data/it",
    "legacy_docs/2023",
    "legacy_docs/2024",
    "references",
    "meeting_notes",
    "contracts",
    "templates",
    "reports/drafts",
    "reports/final",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────

# 1. org chart (distractor)
with open(os.path.join(WORKSPACE, "company_data/hr/org_chart_2024.txt"), "w") as f:
    f.write("""顺达物流集团 组织架构图 (2024年)
总经理: 王建国
├── 运营部  (45人)  部门经理: 李明
│   ├── 仓储组 (20人)
│   ├── 配送组 (18人)
│   └── 调度组 (7人)
├── 销售部  (25人)  部门经理: 张华
│   ├── 大客户组 (10人)
│   ├── 区域销售组 (12人)
│   └── 客服组 (3人)
├── 财务部  (12人)  部门经理: 陈丽
│   ├── 会计组 (6人)
│   ├── 审计组 (3人)
│   └── 税务组 (3人)
├── IT部    (8人)   部门经理: 刘强
│   ├── 系统维护组 (4人)
│   └── 数据组 (4人)
├── HR部    (10人)  部门经理: 赵芳
│   ├── 招聘组 (4人)
│   ├── 培训组 (3人)
│   └── 薪酬组 (3人)
├── 市场部  (8人)   部门经理: 孙磊
└── 法务部  (12人)  部门经理: 周梅

总员工数: 120人
""")

# 2. salary/cost data
with open(os.path.join(WORKSPACE, "company_data/finance/salary_costs_2024.txt"), "w") as f:
    f.write("""顺达物流 人力成本数据 (2024年度)
========================================
部门          人数   平均月薪(元)   年度人力成本(万元)
运营部         45     8,500         459
销售部         25     9,200         276
财务部         12     11,000        158.4
IT部            8     15,000        144
HR部           10     8,000         96
市场部          8     10,000        96
法务部         12     13,000        187.2

合计          120               1,416.6 万元/年

备注:
- 以上包含五险一金(约30%系数已计入)
- 年终奖平均1.5个月薪资
- 2024年人力成本同比增长8.3%
""")

# 3. operations inefficiency report (key input data)
with open(os.path.join(WORKSPACE, "company_data/operations/process_pain_points.txt"), "w") as f:
    f.write("""运营痛点调研报告 - 2024年Q4
====================================
1. 仓储管理:
   - 盘点准确率: 91% (行业标准: 99.5%)
   - 每月盘点耗时: 约240人时
   - 货物损耗率: 1.8% (行业标准: 0.3%)

2. 配送调度:
   - 路线规划纯人工，每天约需4小时
   - 司机空驶率: 23% (行业优秀: <10%)
   - 客户投诉率: 3.2%/月

3. 客户服务:
   - 人工处理查询咨询: 平均每天350次
   - 客服人员3人，平均响应时间: 12分钟
   - 重复性问题占比: 68%

4. 财务对账:
   - 每月对账耗时: 约160人时
   - 人工错误率: 2.1%
   - 发票处理积压: 平均3个工作日

5. 招聘与培训:
   - 司机年流失率: 35%
   - 新员工培训周期: 3周
   - 简历筛选: 每月约200份，人工处理

6. 市场与销售:
   - 客户报价响应时间: 平均1.2天
   - 销售预测准确率: 62%
   - 竞品监控: 无系统化工具
""")

# 4. IT infrastructure (distractor but useful)
with open(os.path.join(WORKSPACE, "company_data/it/current_systems.txt"), "w") as f:
    f.write("""IT系统现状清单
====================
ERP系统: 用友U8 (2018年部署，部分模块未使用)
WMS系统: 自研仓储系统 (2020年，功能较基础)
TMS系统: 无 (调度完全依赖Excel+电话)
CRM系统: 销售易基础版
OA系统: 钉钉 (全员使用)
财务软件: 金蝶K3
BI工具: 无 (报表依赖Excel手工制作)
AI工具: 无
云服务: 阿里云基础版 (仅用于邮件和官网)

IT预算: 年度约50万元
IT人员: 8人 (4人系统运维, 4人数据分析)
数字化成熟度: 初级 (约2/5)
""")

# 5. previous broken/incomplete diagnosis attempt (distractor - incomplete and wrong format)
with open(os.path.join(WORKSPACE, "reports/drafts/old_ai_assessment_INCOMPLETE.txt"), "w") as f:
    f.write("""【草稿-未完成-请勿使用】
AI评估尝试 - 2024年11月
------------------------------
仓储: 可以用AI? 也许
配送: 路线优化听说有软件
客服: 聊天机器人？

ROI: 不知道怎么算，先跳过

TODO: 找顾问帮忙做
状态: 放弃
""")

# 6. contract sample (distractor)
with open(os.path.join(WORKSPACE, "contracts/client_contract_template_2024.txt"), "w") as f:
    f.write("""物流服务合同模板
甲方：___________（委托方）
乙方：顺达物流集团有限公司
服务内容：仓储、配送、供应链管理
服务期限：____年____月____日 至 ____年____月____日
合同金额：人民币 _________ 元整
付款方式：月结30天
违约条款：详见附件A
...(此处省略标准条款)
""")

# 7. meeting notes (distractor)
with open(os.path.join(WORKSPACE, "meeting_notes/board_meeting_2025_01.txt"), "w") as f:
    f.write("""董事会会议纪要 - 2025年1月15日
议题：年度战略规划
出席：王建国(总经理)、陈丽(财务总监)、李明(运营总监)

讨论要点：
1. 2024年营收：4,800万元 (同比+12%)
2. 净利润率：6.2% (行业平均：5.8%)
3. 主要挑战：人力成本上涨、竞争加剧、效率瓶颈
4. 战略重点：数字化转型、客户体验提升
5. 初步预算：数字化转型预算约 80万元/年

行动项：
- 请IT部评估AI工具可行性 (负责人: 刘强, 截止: 2月底)
- 联系AI咨询公司获取诊断报告 (负责人: 王建国)
""")

# 8. competitor analysis (distractor)
with open(os.path.join(WORKSPACE, "company_data/operations/competitor_snapshot.txt"), "w") as f:
    f.write("""竞争对手分析摘要 (2024年)
================================
竞争对手A (京东物流):
- 已部署AI路线优化，空驶率<8%
- 自动化仓库，盘点准确率99.8%
- 智能客服覆盖率85%

竞争对手B (顺丰):
- AI预测需求准确率89%
- 无人机试点项目

行业趋势：70%的头部物流企业已开始AI试点
我司风险：若不升级，2年内竞争力将显著下降
""")

# 9. HR training costs (distractor/input)
with open(os.path.join(WORKSPACE, "company_data/hr/training_budget_2024.txt"), "w") as f:
    f.write("""2024年培训预算明细
====================
新员工入职培训：12万元
技能提升培训：8万元
管理层培训：6万元
外部培训课程：5万元
合计：31万元/年

培训效率问题：
- 大量重复性培训内容
- 培训效果追踪困难
- 新司机培训成本：约3,000元/人
""")

# 10. partial financial projection (distractor)
with open(os.path.join(WORKSPACE, "company_data/finance/2025_budget_draft.txt"), "w") as f:
    f.write("""2025年度预算草案 (初稿)
=========================
营收目标：5,500万元 (+14.6%)
成本控制目标：降低5%
数字化投入预算：80万元
  - 硬件：20万元
  - 软件：30万元
  - 培训：15万元
  - 咨询：15万元

注：具体AI工具采购待诊断报告出炉后确定
""")

# 11. legacy doc (distractor)
with open(os.path.join(WORKSPACE, "legacy_docs/2023/it_audit_2023.txt"), "w") as f:
    f.write("""IT审计报告 2023年度
系统可用性：97.2%
数据备份状态：正常
安全漏洞：3个低危，已修复
主要问题：各系统数据孤岛严重，互通性差
建议：推进数据中台建设
""")

# 12. references case study placeholder (distractor)
with open(os.path.join(WORKSPACE, "references/case-studies.md"), "w") as f:
    f.write("""# 案例参考

## 案例1：某中型电商仓储企业
- 规模：180人
- AI应用：智能拣货 + 需求预测
- 实施周期：3个月
- ROI：14个月回本

## 案例2：区域配送公司
- 规模：80人
- AI应用：路线优化 + 智能客服
- 实施周期：6周
- ROI：8个月回本
""")

# 13. templates folder (distractor)
with open(os.path.join(WORKSPACE, "templates/report_template_OLD.txt"), "w") as f:
    f.write("""旧版报告模板 (已废弃，勿用)
标题：
摘要：
详情：
结论：
""")

# 14. Main company profile summary (key input)
with open(os.path.join(WORKSPACE, "company_data/company_profile.txt"), "w") as f:
    f.write("""顺达物流集团 - 企业概况
================================
企业名称：顺达物流集团有限公司
成立年份：2009年
总部：上海
员工规模：120人
主营业务：区域仓储物流、城市配送、供应链管理
年营收：约4,800万元 (2024年)
主要客户：快消品、电商、制造业客户约200家
地理覆盖：上海及长三角地区

数字化现状：
- ERP/WMS已部署，但数据利用率低
- 无AI工具使用经验
- IT团队具备基础数据处理能力

核心挑战：
- 人力成本持续上涨（年增8%+）
- 运营效率低于行业标准
- 客服压力大，响应慢
- 路线调度完全依赖人工经验

AI投入意愿：
- 总经理已批准探索AI转型
- 可用预算：年度约50-80万元
- 期望：12-18个月内看到可量化回报
""")

print("Workspace initialized successfully.")
print(f"Files created in {WORKSPACE}")