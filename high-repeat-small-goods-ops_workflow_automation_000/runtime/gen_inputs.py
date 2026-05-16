import os
import random
import json

random.seed(42)

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "workspace/scripts",
    "workspace/references",
    "workspace/data/raw",
    "workspace/data/processed",
    "workspace/store/sku_catalog",
    "workspace/store/pricing",
    "workspace/store/reviews",
    "workspace/ops/past_campaigns",
    "workspace/ops/content",
    "workspace/ops/customer_service",
    "workspace/finance",
    "workspace/logistics",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ── generate_content.py  (the bespoke script the agent must call) ────────────
generate_content_py = r'''#!/usr/bin/env python3
"""
generate_content.py  –  Blank template generator for high-repurchase small-goods ops.
Usage:
    python scripts/generate_content.py --type <TYPE>
Supported --type values:
    weekly_plan       → 周运营计划表 (blank)
    campaign          → 活动方案一页纸 (blank)
    repurchase_14d    → 14天复购节奏表 (blank)
    customer_sop      → 客服SOP与话术库 (blank)
    review_report     → 评价与复盘报告 (blank)
"""
import argparse, sys, textwrap, datetime

TEMPLATES = {
    "weekly_plan": textwrap.dedent("""\
        # 周运营计划表
        生成时间: {ts}
        ## 本周目标
        | 指标 | 目标值 | 当前值 | 差距 |
        |------|--------|--------|------|
        |      |        |        |      |

        ## 每日动作
        | 日期 | 内容发布 | 投放调整 | 私域触达 | 评价维护 | 责任人/工时 |
        |------|----------|----------|----------|----------|-------------|
        | 周一 |          |          |          |          |             |
        | 周二 |          |          |          |          |             |
        | 周三 |          |          |          |          |             |
        | 周四 |          |          |          |          |             |
        | 周五 |          |          |          |          |             |
        | 周六 |          |          |          |          |             |
        | 周日 |          |          |          |          |             |
        """),

    "campaign": textwrap.dedent("""\
        # 活动方案一页纸
        生成时间: {ts}
        ## 活动主题
        ## 目标人群
        ## 爆品/套装
        ## 利益点
        ## 节奏（时间线）
        ## 素材清单
        ## 页面改动点
        ## 客服话术
        ## 风险与兜底
        """),

    "repurchase_14d": textwrap.dedent("""\
        # 14天复购节奏表
        生成时间: {ts}
        | 天数 | 触达方式 | 内容/话术要点 | 目标行为 | 关注指标 |
        |------|----------|--------------|----------|----------|
        | D1   |          |              |          |          |
        | D2   |          |              |          |          |
        | D3   |          |              |          |          |
        | D4   |          |              |          |          |
        | D5   |          |              |          |          |
        | D6   |          |              |          |          |
        | D7   |          |              |          |          |
        | D8   |          |              |          |          |
        | D9   |          |              |          |          |
        | D10  |          |              |          |          |
        | D11  |          |              |          |          |
        | D12  |          |              |          |          |
        | D13  |          |              |          |          |
        | D14  |          |              |          |          |
        """),

    "customer_sop": textwrap.dedent("""\
        # 客服SOP与话术库
        生成时间: {ts}
        ## 新客疑虑话术
        ## 适配/色差/材质话术
        ## 催付话术
        ## 催评话术
        ## 售后安抚话术
        """),

    "review_report": textwrap.dedent("""\
        # 评价与复盘报告
        生成时间: {ts}
        ## 做了什么（动作）
        ## 数据结果（指标）
        | 指标 | 目标 | 实际 | 达成率 |
        |------|------|------|--------|
        |      |      |      |        |

        ## 结论（为什么）
        ## 下周实验
        | 改什么 | 预期 | 判定标准 | 止损线 |
        |--------|------|----------|--------|
        |        |      |          |        |
        """),
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", required=True, dest="ttype",
                        choices=list(TEMPLATES.keys()),
                        help="Template type to generate")
    args = parser.parse_args()
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    print(TEMPLATES[args.ttype].format(ts=ts))

if __name__ == "__main__":
    main()
'''

with open("workspace/scripts/generate_content.py", "w", encoding="utf-8") as f:
    f.write(generate_content_py)

# ── references/metrics.md ────────────────────────────────────────────────────
metrics_md = """\
# 指标口径与看板字段

## 核心指标定义
- **GMV**：平台口径成交额（含未发货订单，不含退款）
- **30天复购率**：30天内再次购买人数 / 当期下单人数
- **60天复购率**：60天内再次购买人数 / 当期下单人数
- **客单价**：GMV / 订单量
- **加购率**：加购人数 / 商品访客数
- **转化率**：下单人数 / 商品访客数
- **老客占比**：复购订单量 / 总订单量
- **评价率**：有内容评价数 / 发货订单数
- **退款率**：退款单数 / 下单单数（按金额口径另行标注）
- **ROI**：销售额 / 广告花费

## 看板字段
daily_gmv, daily_orders, uv, ctr, add_to_cart_rate, conversion_rate,
repurchase_rate_30d, repurchase_rate_60d, aov, old_customer_ratio,
review_rate, refund_rate, ad_spend, ad_roi
"""

with open("workspace/references/metrics.md", "w", encoding="utf-8") as f:
    f.write(metrics_md)

# ── references/templates.md ──────────────────────────────────────────────────
templates_md = """\
# 模板索引
所有模板通过 scripts/generate_content.py 生成。
可用 --type: weekly_plan, campaign, repurchase_14d, customer_sop, review_report
"""
with open("workspace/references/templates.md", "w", encoding="utf-8") as f:
    f.write(templates_md)

# ── messy sales data ─────────────────────────────────────────────────────────
sales_csv = """\
日期,SKU,SKU名称,销量,售价,退款量,访客数,加购数,广告花费
2024-05-01,SKU001,iPhone15手机壳-透明,312,19.9,8,2100,340,180
2024-05-01,SKU002,iPhone15手机壳-磨砂黑,278,22.9,5,1980,310,160
2024-05-01,SKU003,手机壳三件套-混色,44,49.9,2,380,95,60
2024-05-02,SKU001,iPhone15手机壳-透明,298,19.9,10,2050,328,175
2024-05-02,SKU004,华为Mate60手机壳-皮纹,130,29.9,3,950,190,90
2024-05-02,SKU005,挂绳配件-编织款,88,9.9,1,620,140,20
2024-05-03,SKU001,iPhone15手机壳-透明,320,19.9,7,2200,355,185
2024-05-03,SKU002,iPhone15手机壳-磨砂黑,265,22.9,6,1900,298,155
2024-05-04,SKU003,手机壳三件套-混色,52,49.9,1,410,102,65
2024-05-04,SKU006,镜面手机壳-玫瑰金,199,35.9,4,1400,280,120
2024-05-05,SKU001,iPhone15手机壳-透明,335,19.9,9,2300,370,190
2024-05-05,SKU005,挂绳配件-编织款,102,9.9,0,700,155,22
2024-05-06,SKU004,华为Mate60手机壳-皮纹,145,29.9,2,1050,210,95
2024-05-06,SKU006,镜面手机壳-玫瑰金,210,35.9,5,1500,295,125
2024-05-07,SKU003,手机壳三件套-混色,60,49.9,0,450,115,70
"""
with open("workspace/data/raw/sales_may_week1.csv", "w", encoding="utf-8") as f:
    f.write(sales_csv)

repurchase_raw = """\
统计周期: 2024-04-01 至 2024-04-30
总下单人数: 4820
30天内再次购买人数: 628
60天内再次购买人数: 实际未统计
复购周期（平均天数）: 约21天
老客订单占比: 约13%
备注: 数据为店主手工统计，存在误差
"""
with open("workspace/data/raw/repurchase_april.txt", "w", encoding="utf-8") as f:
    f.write(repurchase_raw)

review_raw = """\
好评率: 97.2%
评价总数: 1832
有图/视频评价: 412
差评数: 12
差评主要原因: 色差(5), 手机型号不符(4), 物流慢(3)
追评数: 88
"""
with open("workspace/store/reviews/review_summary_april.txt", "w", encoding="utf-8") as f:
    f.write(review_raw)

# ── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "workspace/store/sku_catalog/sku_list_2024q1.csv": "SKU,名称,成本,建议零售价\nSKU001,iPhone15手机壳-透明,5.2,19.9\nSKU002,iPhone15手机壳-磨砂黑,6.1,22.9\n",
    "workspace/store/pricing/price_history.json": json.dumps({"SKU001": [17.9, 18.9, 19.9], "SKU002": [19.9, 21.9, 22.9]}, ensure_ascii=False, indent=2),
    "workspace/ops/past_campaigns/campaign_march.txt": "三月活动：满50减5，引流款折扣，GMV提升12%\n效果一般，未做套装推荐。",
    "workspace/ops/content/video_ideas.txt": "待拍视频选题：\n1. 三秒换壳挑战\n2. 手机壳颜值测评\n3. 情侣款搭配\n",
    "workspace/ops/customer_service/faq_v1.txt": "Q: 你家手机壳适配iPhone15 Pro Max吗？\nA: 请核对SKU描述中的型号列表。\n",
    "workspace/finance/cost_structure.txt": "材料成本: 30-35%\n平台佣金: 5%\n物流: 3-4元/单\n广告: 约12% of GMV\n",
    "workspace/logistics/shipping_policy.txt": "发货时效: 48小时内\n快递: 默认圆通/韵达\n包邮门槛: 满29元\n",
    "workspace/data/processed/placeholder.txt": "尚未有清洗后数据。",
    "workspace/ops/content/douyin_posting_schedule.txt": "发布时间建议: 07:30, 12:00, 20:00\n最优内容类型: 开箱+换装",
    "workspace/store/sku_catalog/discontinued_skus.txt": "已下架: SKU009(钢化膜-失效), SKU010(皮套-滞销)",
    "workspace/finance/monthly_pnl_q1.txt": "一月GMV: 82000\n二月GMV: 71000\n三月GMV: 95000\n毛利率估算: 约42%",
}

for path, content in distractors.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("Workspace generated successfully.")