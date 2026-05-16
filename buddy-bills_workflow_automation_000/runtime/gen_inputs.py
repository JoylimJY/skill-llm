#!/usr/bin/env python3
"""
Build the initial sandbox workspace for the buddy-bills exam.
Simulates an existing user with April 2025 data already in place,
fixed-expense config, and a partial index — ready for May 2025 processing.
"""

import os
import yaml
from pathlib import Path

WORKSPACE = Path("/workspace")

# ── helpers ──────────────────────────────────────────────────────────────────
def write_yaml(path: Path, data, header: str = None):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        if header:
            f.write(header + "\n")
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

def write_raw(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

# ── finance-records root ──────────────────────────────────────────────────────
fr = WORKSPACE / "finance-records"
fr.mkdir(parents=True, exist_ok=True)

# ── 固定支出配置.yaml ────────────────────────────────────────────────────────
fixed_config = """\
# 固定支出配置

每月固定支出:
  - 名称: 房贷
    金额: 8500.00
    扣款日: 10
    商户: 招商银行房贷
    分类: 房贷

  - 名称: 医保
    金额: 650.00
    扣款日: 15
    商户: 社保中心
    分类: 医保

每年固定支出:
  - 名称: 物业费
    金额: 3600.00
    缴费月份: 3
    商户: 绿城物业
    分类: 物业费

  - 名称: 车位费
    金额: 6000.00
    缴费月份: 3
    商户: 小区停车管理处
    分类: 车位费
"""
write_raw(fr / "固定支出配置.yaml", fixed_config)

# ── 收入配置.yaml ────────────────────────────────────────────────────────────
income_config = """\
# 收入配置

工资:
  金额: 18000.00
  发放日: 25
  来源: 某科技有限公司
  子分类: 工资
"""
write_raw(fr / "收入" / "收入配置.yaml", income_config)

# ── index.yaml (root) — only 2025/04 data exists ────────────────────────────
index_data = {
    "2025": {
        "04": {
            "总支出": 14320.00,
            "房贷": 8500.00,
            "家庭转账": 2000.00,
            "餐饮": 1820.00,
            "收入": 18000.00,
            "结余": 3680.00,
        }
    }
}
write_yaml(fr / "index.yaml", index_data)

# ── April 2025 category files (distractor / prior-month data) ────────────────

# 餐饮/2025/04.yaml
canteen_apr = {
    "月度汇总": {"总计": 1820.00},
    "明细": [
        {"日期": "2025-04-03", "商户": "麦当劳", "子分类": "午餐", "金额": 45.00, "支付方式": "微信", "备注": ""},
        {"日期": "2025-04-10", "商户": "美团外卖", "子分类": "外卖", "金额": 68.00, "支付方式": "支付宝", "备注": ""},
        {"日期": "2025-04-18", "商户": "瑞幸咖啡", "子分类": "咖啡", "金额": 32.00, "支付方式": "微信", "备注": ""},
        {"日期": "2025-04-22", "商户": "聚餐饭店", "子分类": "聚餐", "金额": 320.00, "支付方式": "微信", "备注": "朋友聚餐"},
        {"日期": "2025-04-28", "商户": "超市买菜", "子分类": "早餐", "金额": 85.00, "支付方式": "现金", "备注": ""},
        {"日期": "2025-04-29", "商户": "星巴克", "子分类": "咖啡", "金额": 58.00, "支付方式": "支付宝", "备注": ""},
        {"日期": "2025-04-30", "商户": "晚餐外卖", "子分类": "外卖", "金额": 75.00, "支付方式": "微信", "备注": ""},
    ],
}
write_raw(fr / "餐饮/2025/04.yaml",
          "# 餐饮明细 - 2025年04月\n\n" + yaml.dump(canteen_apr, allow_unicode=True, default_flow_style=False, sort_keys=False))

# 餐饮/index.yaml
canteen_idx = {"2025": {"04": {"总计": 1820.00}}}
write_yaml(fr / "餐饮/index.yaml", canteen_idx)

# 房贷/2025/04.yaml
mortgage_apr = {
    "月度汇总": {"总计": 8500.00},
    "明细": [
        {"日期": "2025-04-10", "商户": "招商银行房贷", "子分类": "", "金额": 8500.00, "支付方式": "银行自动扣款", "备注": "4月月供"},
    ],
}
write_raw(fr / "房贷/2025/04.yaml",
          "# 房贷明细 - 2025年04月\n\n" + yaml.dump(mortgage_apr, allow_unicode=True, default_flow_style=False, sort_keys=False))

mortgage_idx = {"2025": {"04": {"总计": 8500.00}}}
write_yaml(fr / "房贷/index.yaml", mortgage_idx)

# 医保/2025/04.yaml
insur_apr = {
    "月度汇总": {"总计": 650.00},
    "明细": [
        {"日期": "2025-04-15", "商户": "社保中心", "子分类": "", "金额": 650.00, "支付方式": "银行自动扣款", "备注": "4月医保"},
    ],
}
write_raw(fr / "医保/2025/04.yaml",
          "# 医保明细 - 2025年04月\n\n" + yaml.dump(insur_apr, allow_unicode=True, default_flow_style=False, sort_keys=False))

insur_idx = {"2025": {"04": {"总计": 650.00}}}
write_yaml(fr / "医保/index.yaml", insur_idx)

# 家庭转账/2025/04.yaml
transfer_apr = {
    "月度汇总": {"总计": 2000.00},
    "明细": [
        {"日期": "2025-04-05", "商户": "配偶", "子分类": "", "金额": 2000.00, "支付方式": "微信转账", "备注": "家庭日常"},
    ],
}
write_raw(fr / "家庭转账/2025/04.yaml",
          "# 家庭转账明细 - 2025年04月\n\n" + yaml.dump(transfer_apr, allow_unicode=True, default_flow_style=False, sort_keys=False))

transfer_idx = {"2025": {"04": {"总计": 2000.00}}}
write_yaml(fr / "家庭转账/index.yaml", transfer_idx)

# 收入/2025/04.yaml
income_apr = {
    "月度汇总": {"总计": 18000.00},
    "明细": [
        {"日期": "2025-04-25", "商户": "某科技有限公司", "子分类": "工资", "金额": 18000.00, "支付方式": "银行转账", "备注": "4月工资"},
    ],
}
write_raw(fr / "收入/2025/04.yaml",
          "# 收入明细 - 2025年04月\n\n" + yaml.dump(income_apr, allow_unicode=True, default_flow_style=False, sort_keys=False))

income_idx = {"2025": {"04": {"总计": 18000.00}}}
write_yaml(fr / "收入/index.yaml", income_idx)

# ── April 2025 summary (already closed) ──────────────────────────────────────
apr_summary_raw = """\
# 月度汇总 - 2025年04月

## 一、收支总览
收入:
  工资: 18000.00
  总收入: 18000.00
支出:
  房贷: 8500.00
  医保: 650.00
  家庭转账: 2000.00
  餐饮: 1820.00
  总支出: 14320.00
结余: 3680.00
储蓄率: 20%

## 二、每周总结
### 第1周（04月01日 - 04月06日）
  支出: 2045.00
  收入: 0.00
  明细:
    - 2025-04-03 | 麦当劳 | 餐饮 | 45.00
    - 2025-04-05 | 配偶 | 家庭转账 | 2000.00

### 第2周（04月07日 - 04月13日）
  支出: 8568.00
  收入: 0.00
  明细:
    - 2025-04-10 | 招商银行房贷 | 房贷 | 8500.00
    - 2025-04-10 | 美团外卖 | 餐饮 | 68.00

### 第3周（04月14日 - 04月20日）
  支出: 682.00
  收入: 0.00
  明细:
    - 2025-04-15 | 社保中心 | 医保 | 650.00
    - 2025-04-18 | 瑞幸咖啡 | 餐饮 | 32.00

### 第4周（04月21日 - 04月30日）
  支出: 3025.00
  收入: 18000.00
  明细:
    - 2025-04-22 | 聚餐饭店 | 餐饮 | 320.00
    - 2025-04-25 | 某科技有限公司 | 收入 | 18000.00
    - 2025-04-28 | 超市买菜 | 餐饮 | 85.00
    - 2025-04-29 | 星巴克 | 餐饮 | 58.00
    - 2025-04-30 | 晚餐外卖 | 餐饮 | 75.00

## 三、支出明细汇总
### 房贷（8500.00）
  占总支出: 59%
  明细:
    - 2025-04-10 | 招商银行房贷 | 8500.00

### 家庭转账（2000.00）
  占总支出: 14%
  明细:
    - 2025-04-05 | 配偶 | 2000.00

### 餐饮（1820.00）
  占总支出: 13%
  明细:
    - 2025-04-03 | 麦当劳 | 45.00
    - 2025-04-10 | 美团外卖 | 68.00
    - 2025-04-18 | 瑞幸咖啡 | 32.00
    - 2025-04-22 | 聚餐饭店 | 320.00
    - 2025-04-28 | 超市买菜 | 85.00
    - 2025-04-29 | 星巴克 | 58.00
    - 2025-04-30 | 晚餐外卖 | 75.00

### 医保（650.00）
  占总支出: 5%
  明细:
    - 2025-04-15 | 社保中心 | 650.00

## 四、统计分析
支出排行:
  1. 房贷: 8500.00（59%）
  2. 家庭转账: 2000.00（14%）
  3. 餐饮: 1820.00（13%）
  4. 医保: 650.00（5%）
最大单笔: 8500.00（招商银行房贷）
固定支出: 11150.00
浮动支出: 3170.00

## 五、环比对比
  上月结余: 0.00

## 六、备注
"""
write_raw(fr / "summary/2025/04.yaml", apr_summary_raw)

# ── Distractor files (unrelated project files) ───────────────────────────────
distractors = [
    ("projects/webapp/config.json",           '{"port": 3000, "debug": false}'),
    ("projects/webapp/src/index.js",           'console.log("hello");'),
    ("projects/webapp/src/utils.js",           'function add(a,b){return a+b;}'),
    ("projects/webapp/package.json",           '{"name":"webapp","version":"1.0.0"}'),
    ("notes/meeting-2025-04-28.txt",           "Q2 planning meeting notes. Budget TBD."),
    ("notes/todo.txt",                         "1. File taxes\n2. Call bank\n3. Buy groceries"),
    ("docs/api-reference.md",                  "# API Reference\n\nSee swagger.yaml for details."),
    ("docs/onboarding.md",                     "# Onboarding\n\nWelcome to the team!"),
    ("scripts/backup.sh",                      "#!/bin/bash\ntar -czf backup.tar.gz /workspace"),
    ("scripts/deploy.sh",                      "#!/bin/bash\necho 'Deploying...'"),
    ("logs/app-2025-04-30.log",               "[INFO] Application started\n[ERROR] DB timeout"),
    ("logs/access-2025-04-30.log",            "GET /api/v1/users 200 45ms"),
    (".env.example",                           "DATABASE_URL=\nSECRET_KEY=\nDEBUG=false"),
    ("README_PROJECTS.md",                     "# Projects\n\nThis folder contains project files."),
]

for rel_path, content in distractors:
    p = WORKSPACE / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

# ── Write a plain-text "inbox" file with the May transactions the agent must process
inbox = """\
# 待处理收支记录 — 2025年5月

以下是本月需要录入的流水，请帮我整理入账并生成月度汇总：

1. 5月2日，美团外卖点了晚饭，花了62元，微信支付。
2. 5月8日，京东买了一个插线板和收纳盒，共消费218元，支付宝付款。
3. 5月14日，带孩子去打了流感疫苗，医院收费280元，现金。
4. 5月20日，给老婆转了2000元家用。
5. 5月26日，在瑞幸买了两杯咖啡，花了38元，微信支付。

另外，本月固定支出（房贷、医保）按惯例正常扣款，25号工资也照常发放。
今天是5月31日，麻烦把这个月的账全部整理好，生成月度汇总报告。
"""
write_raw(WORKSPACE / "inbox_may2025.txt", inbox)

print("Workspace generated successfully.")
print(f"Key files created under: {fr}")