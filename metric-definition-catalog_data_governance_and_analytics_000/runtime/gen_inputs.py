import os
import json
import random

random.seed(42)

BASE = "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "skill-metric-definition-catalog/scripts",
    "skill-metric-definition-catalog/resources",
    "skill-metric-definition-catalog/examples",
    "skill-metric-definition-catalog/tests",
    "data/raw/biz_unit_A",
    "data/raw/biz_unit_B",
    "data/raw/legacy_finance",
    "data/staging",
    "data/archive/2022",
    "data/archive/2023",
    "docs/governance",
    "docs/meeting_notes",
    "reports/q1",
    "reports/q2",
    "config",
    "tmp",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

def write(path, content):
    with open(os.path.join(BASE, path), "w", encoding="utf-8") as f:
        f.write(content)

# ── Distractor files ─────────────────────────────────────────────────────────
write("config/pipeline.yaml", "version: 2\nstages:\n  - extract\n  - transform\n  - load\n")
write("config/db_conn.cfg", "[postgres]\nhost=localhost\nport=5432\ndbname=analytics\n")
write("docs/governance/data_owner_registry.csv",
      "metric_name,owner,team\nGMV,alice@corp.com,growth\nCVR,bob@corp.com,product\nrefund_rate,carol@corp.com,finance\n")
write("docs/meeting_notes/2024-03-kickoff.txt",
      "Attendees: Alice, Bob, Carol\nAction items:\n- Consolidate metric definitions post-merger\n- Resolve GMV conflict between biz units\n")
write("docs/meeting_notes/2024-04-followup.txt",
      "Still pending: refund_rate formula alignment between Finance and Ops teams.\n")
write("reports/q1/summary.txt", "Q1 GMV: 120M (using BizUnit-A definition)\nQ1 CVR: 3.2%\n")
write("reports/q2/summary.txt", "Q2 GMV: 135M (using legacy Finance definition — NOTE: different base!)\n")
write("data/archive/2022/metric_snapshot.json",
      json.dumps({"GMV": {"formula": "sum(order_amount)", "note": "pre-merger"}, "CVR": {"formula": "orders/sessions"}}, indent=2))
write("data/archive/2023/metric_snapshot.json",
      json.dumps({"GMV": {"formula": "sum(paid_amount) where status='completed'", "note": "post-deduction"}, "CVR": {"formula": "unique_buyers/unique_visitors"}}, indent=2))
write("data/staging/.gitkeep", "")
write("tmp/scratch.txt", "TODO: figure out which GMV definition to use for board deck\n")
write("reports/q1/raw_export.csv", "date,metric,value\n2024-01-01,GMV,40000000\n2024-01-01,CVR,0.031\n")

# ── MESSY RAW INPUTS — the actual problem files ──────────────────────────────

# BizUnit A definitions (e-commerce focus)
write("data/raw/biz_unit_A/metrics_draft_v3.txt", """\
## BizUnit-A 指标草稿 v3 (电商事业部)

【GMV - 成交总额】
定义: 所有已提交订单的商品金额总和，含未支付、已取消订单。
公式: GMV = SUM(order_item_price * quantity) for all order_status IN ('submitted','paid','shipped','cancelled')
归属团队: 增长团队
统计周期: 日/周/月
注意事项: 含预售未付款订单

【CVR - 转化率】
定义: 访问后产生购买行为的用户占比
公式: CVR = 去重购买用户数 / 去重访客数
归属团队: 产品团队
分母口径: 以session维度去重访客

【退款率】
定义: 退款金额占GMV的比例  ← 注意：依赖GMV口径!
公式: 退款率 = SUM(refund_amount) / GMV_A  (使用本部门GMV定义)
归属团队: 客服团队
例外: 仅含成功退款，拒绝退款不计入
""")

# BizUnit B definitions (fintech / payment focus)
write("data/raw/biz_unit_B/indicator_list_final.md", """\
# BizUnit-B 核心指标清单（金融支付部）FINAL

## 1. GMV（交易总额）
**口径**: 仅统计支付成功且交易状态为completed的订单
**计算公式**: GMV = SUM(paid_amount) WHERE transaction_status = 'completed'
**负责人**: 数据中台
**统计口径说明**: 不含退款中订单、不含预授权未扣款订单
**更新频率**: T+1

## 2. 转化率 (Conversion Rate)
**口径**: 独立设备产生支付行为的比率
**计算公式**: CVR = COUNT(DISTINCT device_id WITH payment) / COUNT(DISTINCT device_id)
**负责人**: 产品分析
**备注**: 分母为设备维度，非用户维度

## 3. 退款率
**口径**: 退款笔数占成功交易笔数比例（金额无关）
**计算公式**: 退款率 = COUNT(refund_transactions) / COUNT(completed_transactions)
**负责人**: 风控团队
**注**: 按笔数算，不按金额

## 4. 客单价 (AOV)
**口径**: 成功交易的平均金额
**计算公式**: AOV = SUM(paid_amount) / COUNT(completed_transactions)
**负责人**: 数据中台
""")

# Legacy finance team — partial, missing fields
write("data/raw/legacy_finance/finance_kpi_partial.csv", """\
指标名称,计算方式,备注,归属,例外情况
GMV,所有付款记录金额之和,包含B2B批发订单,财务团队,剔除内部测试账号交易
毛利率,"(收入-成本)/收入 * 100%",按月汇总,财务团队,
NPS,,待补充,客户成功团队,
LTV,,待补充,增长团队,
退款率,退款金额/当月GMV,使用财务口径GMV（含B2B）,财务团队,含争议中订单
""")

# A conflicting note from the analytics working group
write("docs/governance/analytics_wg_conflict_log.txt", """\
=== 指标冲突记录 ===
记录时间: 2024-05-10

1. GMV: 三个部门存在三种不同口径
   - A部门: 含取消订单
   - B部门: 仅completed
   - 财务: 含B2B批发
   结论: 未对齐，待讨论

2. CVR: 分母口径不一致
   - A部门: session去重访客
   - B部门: device_id
   结论: 需要统一，暂无决议

3. 退款率: 计算基数不同
   - A部门: 金额/GMV_A
   - B部门: 笔数/completed_transactions
   - 财务: 金额/GMV_Finance
   结论: 三套口径均在用，高风险指标

4. AOV: 仅B部门有定义，A和财务未维护
   结论: 待确认A和财务是否适用

5. NPS/LTV: 无任何部门有完整公式
   结论: 待补充
""")

# The agent must produce this file:
# skill-metric-definition-catalog/ already has the skill infrastructure
# The agent needs to consolidate the above into a catalog

# Write the agent task manifest (describes what to do — business framing only)
write("data/raw/TASK_BRIEF.txt", """\
任务背景:
我们公司在今年完成了与支付部门的合并，目前电商事业部（BizUnit-A）、金融支付部（BizUnit-B）
和财务团队各自维护着一套指标定义，导致每次出报告时数字对不上。

请帮我把散落在 data/raw/ 下各部门文件中的所有指标定义整理成一份统一的指标目录文档。
重点关注 GMV、CVR（转化率）、退款率、AOV、NPS、LTV 这六个指标。

输出文件命名为 metric_catalog.md，放在 data/staging/ 目录下。
""")

print("Workspace generated successfully.")
print("Key input files:")
print("  data/raw/biz_unit_A/metrics_draft_v3.txt")
print("  data/raw/biz_unit_B/indicator_list_final.md")
print("  data/raw/legacy_finance/finance_kpi_partial.csv")
print("  data/raw/TASK_BRIEF.txt")