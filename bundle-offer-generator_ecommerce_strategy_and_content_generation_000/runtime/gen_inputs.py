import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Deep directory structure with distractor files ---
dirs = [
    "workspace/references",
    "workspace/data/products",
    "workspace/data/customers",
    "workspace/data/inventory",
    "workspace/internal/pricing",
    "workspace/internal/campaigns/2024",
    "workspace/internal/campaigns/2023",
    "workspace/reports/q1",
    "workspace/reports/q2",
    "workspace/assets/images",
    "workspace/assets/copy",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# --- SKILL.md (the agent must use this) ---
skill_md = """\
---
name: bundle-offer-generator
description: Generate ecommerce bundle ideas using product mix, margin logic, and customer intent. Use when teams want stronger offer packaging without random discounting.
---

# Bundle Offer Generator

bundle 不是把几个产品硬绑在一起，而是把购买理由组合得更强。

## 解决的问题

很多 bundle 做不起来，通常是因为：
- 只是打折，没有更清楚的购买逻辑；
- 组合虽然便宜，但用户不知道为什么要一起买；
- AOV 上去了，利润却掉得太多；
- 套餐层级不清楚，反而增加选择负担。

这个 skill 的目标是：
**基于商品关系、利润空间和用户场景，生成更好卖的 bundle 方案。**

## 何时使用

- 想拉高 AOV；
- 有多个关联商品，但不知道如何组合；
- 促销期想推出更有结构的套餐而不是单纯降价。

## 输入要求

- 商品列表与价格
- 毛利空间
- 商品搭配关系 / 使用顺序
- 目标客群和购买场景
- 可选：折扣边界、库存限制、平台限制

## 工作流

1. 找出自然搭配组合。
2. 设计基础款 / 进阶款 / 高价值款层级。
3. 检查 margin 和折扣空间。
4. 输出可销售的命名和定位建议。

## 输出格式

1. Bundle 方案列表
2. 定价逻辑
3. Margin 风险提示
4. 建议使用场景

## 质量标准

- 组合要有明确购买逻辑。
- 不只是"便宜了多少"，还要说明为什么一起买。
- 不能牺牲太多 margin。
- 输出要可直接用于商品页或活动页。

## 资源

参考 `references/output-template.md`。
"""
with open("workspace/SKILL.md", "w", encoding="utf-8") as f:
    f.write(skill_md)

# --- references/output-template.md ---
output_template = """\
# Bundle Output Template

## 1. Bundle 方案列表

### [基础款] <Bundle Name>
- 包含商品：<product list>
- 原价合计：<sum>
- Bundle 售价：<price>
- 折扣幅度：<discount %>
- 购买理由：<why buy together — NOT just price saving>

### [进阶款] <Bundle Name>
- 包含商品：<product list>
- 原价合计：<sum>
- Bundle 售价：<price>
- 折扣幅度：<discount %>
- 购买理由：<why buy together>

### [高价值款] <Bundle Name>
- 包含商品：<product list>
- 原价合计：<sum>
- Bundle 售价：<price>
- 折扣幅度：<discount %>
- 购买理由：<why buy together>

## 2. 定价逻辑

<Explain the pricing rationale — which products anchor value, how discount is distributed>

## 3. Margin 风险提示

<For each bundle: estimated blended margin, flag if margin is at risk, suggest mitigation>

## 4. 建议使用场景

<Which customer segment, which purchase moment, which channel this bundle works best for>
"""
with open("workspace/references/output-template.md", "w", encoding="utf-8") as f:
    f.write(output_template)

# --- Core input: product catalog with messy, realistic data ---
product_catalog = """\
# TrailPeak Outdoor Gear — Product Catalog (Internal)
# Last updated: 2024-03-12
# NOTE: Some margins are estimated. Finance to confirm Q2.

Product ID | Name                        | Retail Price (USD) | COGS (USD) | Gross Margin % | Category       | Pairing Notes
-----------|-----------------------------|-------------------|------------|----------------|----------------|-------------------------------
TP-001     | TrailPeak 3-Season Tent 2P  | 189.00            | 132.30     | 30%            | Shelter        | Always bought with sleeping bags; first-time campers need full kit
TP-002     | UltraLight Sleeping Bag -5C | 129.00            | 71.00      | 45%            | Sleep          | Pairs with tent and sleeping pad
TP-003     | Self-Inflating Sleeping Pad | 59.00             | 23.60      | 60%            | Sleep          | Almost always bought with sleeping bag
TP-004     | Headlamp Pro 400lm          | 34.00             | 10.20      | 70%            | Lighting       | Impulse add-on; high margin
TP-005     | Camp Kitchen Kit (4-piece)  | 49.00             | 24.50      | 50%            | Cooking        | Bought by families and car campers
TP-006     | Trekking Poles (pair)       | 45.00             | 22.50      | 50%            | Accessories    | Pairs with tent for trail hikers
TP-007     | Water Filter Straw          | 29.00             | 8.70       | 70%            | Water/Safety   | Safety purchase, high attach rate with tents
TP-008     | First Aid Kit Outdoor 50pc  | 22.00             | 7.70       | 65%            | Safety         | Low AOV but very high margin; always good add-on
TP-009     | Compression Stuff Sack Set  | 18.00             | 5.40       | 70%            | Accessories    | Pairs with sleeping bag to reduce pack volume
TP-010     | TrailPeak Rain Jacket       | 119.00            | 83.30      | 30%            | Apparel        | Weekend warriors, pairs with tent/poles
TP-011     | Portable Solar Charger 10W  | 55.00             | 27.50      | 50%            | Electronics    | Multi-day trip segment; pairs with headlamp
TP-012     | Bear Canister 700cu         | 75.00             | 37.50      | 50%            | Safety/Storage | Required in some parks; pairs with cooking kit
"""
with open("workspace/data/products/catalog.txt", "w", encoding="utf-8") as f:
    f.write(product_catalog)

# --- Customer segment brief ---
customer_brief = """\
# Customer Segments — TrailPeak 2024

## Segment A: First-Time Campers
- Age: 25–38
- Purchase trigger: Planning first overnight trip
- Pain point: Don't know what gear they need; overwhelmed by choices
- AOV target: $250–$350
- Platform: Website + Instagram ads
- Notes: Highly responsive to "complete kit" messaging; need reassurance

## Segment B: Weekend Warriors
- Age: 30–50
- Purchase trigger: Upgrading existing gear for shoulder season
- Pain point: Want better performance without replacing everything
- AOV target: $150–$250
- Platform: Email campaigns + loyalty program
- Notes: Know gear well; respond to value + performance narrative

## Segment C: Multi-Day Thru-Hikers
- Age: 28–45
- Purchase trigger: Preparing for 5+ day backcountry trips
- Pain point: Weight savings and redundancy; safety is critical
- AOV target: $350+
- Platform: Direct/organic search, gear review sites
- Notes: Will pay premium; skeptical of bundles unless clearly purposeful
"""
with open("workspace/data/customers/segments.txt", "w", encoding="utf-8") as f:
    f.write(customer_brief)

# --- Discount policy (messy internal doc) ---
discount_policy = """\
INTERNAL MEMO — Pricing & Promotions
Date: 2024-01-08
From: Finance

Bundle discount ceiling: 12% off retail sum (blended)
- Exception: if bundle blended margin stays above 40%, up to 15% is okay
- Hard floor: NO bundle can have blended margin below 35%
- Rain Jacket (TP-010) and Tent (TP-001) CANNOT be discounted more than 8% individually due to MAP policy with supplier
- Accessories (TP-004, TP-007, TP-008, TP-009) can absorb deeper discount to protect anchor margin
- Stock note: Bear Canister (TP-012) is currently overstocked (300 units); push in bundles if margin holds

Approved bundle window: Summer Campaign (June–August 2024)
"""
with open("workspace/internal/pricing/discount_policy.txt", "w", encoding="utf-8") as f:
    f.write(discount_policy)

# --- Distractor files (not relevant, just noise) ---
with open("workspace/internal/campaigns/2024/q2_plan_draft.txt", "w") as f:
    f.write("Q2 campaign plan — TBD. Waiting on product team sign-off.\nBudget: $45k digital, $10k influencer.\n")

with open("workspace/internal/campaigns/2023/black_friday_results.csv", "w") as f:
    f.write("campaign,revenue,units,aov\nBF2023_Tent,142000,751,189\nBF2023_Accessories,38000,1520,25\n")

with open("workspace/data/inventory/stock_levels.json", "w") as f:
    json.dump({
        "TP-001": 450, "TP-002": 312, "TP-003": 287,
        "TP-004": 980, "TP-005": 145, "TP-006": 201,
        "TP-007": 673, "TP-008": 540, "TP-009": 410,
        "TP-010": 98,  "TP-011": 167, "TP-012": 300
    }, f, indent=2)

with open("workspace/reports/q1/revenue_summary.txt", "w") as f:
    f.write("Q1 2024 Revenue: $1.24M\nTop SKU: TP-001 (Tent) — 41% of revenue\nLow performer: TP-009 (Stuff Sack) — 1.2% attach rate\n")

with open("workspace/reports/q2/targets.txt", "w") as f:
    f.write("Q2 AOV target: +18% YoY\nBundle attach rate target: 22% of orders\n")

with open("workspace/assets/copy/taglines.txt", "w") as f:
    f.write("Taglines brainstorm:\n- 'Your first night under the stars'\n- 'Go further. Sleep better.'\n- 'Built for the trail, not the parking lot.'\n")

with open("workspace/assets/images/placeholder.txt", "w") as f:
    f.write("Images pending from design team. Jira ticket: DES-2041\n")

with open("workspace/data/customers/churn_analysis.txt", "w") as f:
    f.write("Churn analysis: 68% of one-time buyers never returned. Primary reason: unclear product ecosystem.\n")

with open("workspace/data/products/discontinued.txt", "w") as f:
    f.write("Discontinued SKUs (do not include in any new offers):\nTP-OLD-003 — 1P Bivy Tent (returned too many)\nTP-OLD-007 — Gas Canister (hazmat shipping restrictions)\n")

print("Workspace initialized successfully.")