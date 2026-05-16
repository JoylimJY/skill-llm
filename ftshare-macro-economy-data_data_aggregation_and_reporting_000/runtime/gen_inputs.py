import os
import json
import random
import textwrap
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "skills/FTShare-macro-economy-data/sub-skills/economic-china-gdp-quarterly",
    "skills/FTShare-macro-economy-data/sub-skills/economic-china-cpi-monthly",
    "skills/FTShare-macro-economy-data/sub-skills/economic-china-pmi-monthly",
    "skills/FTShare-macro-economy-data/sub-skills/economic-china-money-supply-monthly",
    "skills/FTShare-macro-economy-data/sub-skills/economic-china-ppi-monthly",
    "skills/FTShare-macro-economy-data/sub-skills/economic-china-lpr-monthly",
    "skills/FTShare-macro-economy-data/sub-skills/economic-china-customs-trade-monthly",
    "skills/FTShare-macro-economy-data/sub-skills/economic-china-fixed-asset-investment-monthly",
    "skills/FTShare-macro-economy-data/sub-skills/economic-china-reserve-ratio-monthly",
    "skills/FTShare-macro-economy-data/sub-skills/economic-china-forex-gold-monthly",
    "skills/FTShare-macro-economy-data/sub-skills/economic-china-retail-sales-monthly",
    "skills/FTShare-macro-economy-data/sub-skills/economic-china-fiscal-revenue-monthly",
    "skills/FTShare-macro-economy-data/sub-skills/economic-china-tax-revenue-monthly",
    "skills/FTShare-macro-economy-data/sub-skills/economic-china-credit-loans-monthly",
    "skills/FTShare-macro-economy-data/sub-skills/economic-china-industrial-added-value-monthly",
    "skills/FTShare-macro-economy-data/sub-skills/economic-us-economic-by-type",
    "reports/drafts",
    "reports/archive",
    "data/raw/china",
    "data/raw/us",
    "data/processed",
    "config",
    "logs",
    "scripts/helpers",
    "tmp",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── SKILL.md (main entry point) ───────────────────────────────────────────────
skill_md_content = textwrap.dedent("""\
---
name: FTShare-macro-economy-data
description: 中国与美国宏观经济指标技能集（market.ft.tech）。中国：GDP、LPR、PMI、PPI、CPI、财政收入、信贷、外储、社零、税收、M0/M1/M2、进出口、工业增加值、存准率、固投等 15 项月度/季度；美国：按 type 查询 ISM、非农、贸易帐、失业率、PPI/CPI、新屋/成屋、耐用品、咨商会信心、GDP 年率、联邦基金利率等 16 类。用户问中国/美国经济数据时使用。
---

# FT 宏观经济数据 Skills（中国 + 美国）

本 skill 是 `FTShare-macro-economy-data` 的**统一路由入口**，覆盖**中国经济**与**美国经济**指标。

根据用户问题，从下方「能力总览」或「提示词表」匹配对应子 skill，然后通过 `run.py` 执行并解析响应。

> 所有接口均以 `https://market.ft.tech` 为基础域名，使用 HTTP GET。

---

## 调用方式（唯一规则）

`run.py` 与本文件（`SKILL.md`）位于同一目录。执行时：

1. 取本文件的绝对路径，将末尾 `/SKILL.md` 替换为 `/run.py`，得到 `<RUN_PY>`。
2. **中国经济**（15 项）：`python <RUN_PY> <子skill名>`（无额外参数）。
3. **美国经济**（1 项，按 type）：`python <RUN_PY> economic-us-economic-by-type --type <type值>`。

```bash
# 示例（<RUN_PY> 为实际绝对路径）
python <RUN_PY> economic-china-gdp-quarterly
python <RUN_PY> economic-china-pmi-monthly
python <RUN_PY> economic-china-cpi-monthly
python <RUN_PY> economic-us-economic-by-type --type nonfarm-payroll
python <RUN_PY> economic-us-economic-by-type --type cpi-mom
```

> `run.py` 内部通过 `__file__` 自定位，无须关心安装路径。

---

## 能力总览与提示词表

### 中国经济 — 提示词与子 skill 对应表

| 提示词（用户常说的词） | 子 skill |
|------------------------|----------|
| **GDP**、国内生产总值、三次产业 | `economic-china-gdp-quarterly` |
| 财政收入、财政月度 | `economic-china-fiscal-revenue-monthly` |
| **LPR**、贷款市场报价利率、房贷利率、1年期/5年期 | `economic-china-lpr-monthly` |
| **PMI**、采购经理人指数、制造业/非制造业PMI | `economic-china-pmi-monthly` |
| **PPI**、工业品出厂价格指数、生产者价格指数 | `economic-china-ppi-monthly` |
| 信贷、**新增信贷**、新增人民币贷款、贷款增量 | `economic-china-credit-loans-monthly` |
| 外汇储备、黄金储备、**外储** | `economic-china-forex-gold-monthly` |
| 社会消费品零售总额、**社零**、零售总额、消费零售 | `economic-china-retail-sales-monthly` |
| 全国税收收入、税收收入、税收月度 | `economic-china-tax-revenue-monthly` |
| **CPI**、居民消费价格指数、消费价格指数、城市/农村CPI | `economic-china-cpi-monthly` |
| **M0、M1、M2**、货币供应量、广义货币、狭义货币 | `economic-china-money-supply-monthly` |
| 海关进出口、**进出口、外贸**、出口、进口 | `economic-china-customs-trade-monthly` |
| 工业增加值、工业增长 | `economic-china-industrial-added-value-monthly` |
| 存款准备金率、**存准率、RRR**、准备金率 | `economic-china-reserve-ratio-monthly` |
| 城镇固定资产投资、**固投**、固定资产投资 | `economic-china-fixed-asset-investment-monthly` |

### 美国经济 — 提示词与 type 对应表

子 skill 固定为 `economic-us-economic-by-type`，执行：`python <RUN_PY> economic-us-economic-by-type --type <type值>`。

| 提示词（用户常说的词） | type 值 |
|------------------------|---------|
| 美国 **ISM 制造业**、美国制造业PMI | `ism-manufacturing` |
| 美国 **ISM 非制造业**、美国服务业PMI | `ism-non-manufacturing` |
| 美国**非农**、非农就业、非农人数 | `nonfarm-payroll` |
| 美国**贸易帐**、贸易赤字/盈余 | `trade-balance` |
| 美国**失业率** | `unemployment-rate` |
| 美国 **PPI**、生产者物价月率 | `ppi-mom` |
| 美国 **CPI 月率**、消费者物价月率 | `cpi-mom` |
| 美国 **CPI 年率**、消费者物价年率 | `cpi-yoy` |
| 美国**核心 CPI 月率** | `core-cpi-mom` |
| 美国**核心 CPI 年率** | `core-cpi-yoy` |
| 美国**新屋开工** | `housing-starts` |
| 美国**成屋销售** | `existing-home-sales` |
| 美国**耐用品订单**、耐用品订单月率 | `durable-goods-orders-mom` |
| 美国**咨商会信心指数**、消费者信心 | `cb-consumer-confidence` |
| 美国 **GDP 年率**、GDP 初值、季度GDP | `gdp-yoy-preliminary` |
| 美国**联邦基金利率**、美联储利率、利率决议上限 | `fed-funds-rate-upper` |

---

## 子 skill 列表（路径说明）

所有子 skill 位于本包 `sub-skills/<子skill名>/`，接口详情见各子 skill 的 `SKILL.md`。

**中国经济（15 项）**

- `economic-china-gdp-quarterly`
- `economic-china-fiscal-revenue-monthly`
- `economic-china-lpr-monthly`
- `economic-china-pmi-monthly`
- `economic-china-ppi-monthly`
- `economic-china-credit-loans-monthly`
- `economic-china-forex-gold-monthly`
- `economic-china-retail-sales-monthly`
- `economic-china-tax-revenue-monthly`
- `economic-china-cpi-monthly`
- `economic-china-money-supply-monthly`
- `economic-china-customs-trade-monthly`
- `economic-china-industrial-added-value-monthly`
- `economic-china-reserve-ratio-monthly`
- `economic-china-fixed-asset-investment-monthly`

**美国经济（1 项，按 type 区分 16 类）**

- `economic-us-economic-by-type`

---

## 使用流程

1. **记录本文件绝对路径**，将 `/SKILL.md` 替换为 `/run.py` 得到 `<RUN_PY>`。
2. **理解用户意图**，从「中国经济 — 提示词与子 skill 对应表」或「美国经济 — 提示词与 type 对应表」匹配子 skill 及（美国）`--type`。
3. （可选）读取 `sub-skills/<子skill名>/SKILL.md` 了解接口与参数。
4. **执行**：中国 `python <RUN_PY> <子skill名>`；美国 `python <RUN_PY> economic-us-economic-by-type --type <type值>`。
5. **解析并输出**：以表格或要点形式展示给用户。
""")

skill_root = workspace / "skills/FTShare-macro-economy-data"
(skill_root / "SKILL.md").write_text(skill_md_content, encoding="utf-8")

# ── Mock run.py that returns realistic fake data ──────────────────────────────
run_py_content = textwrap.dedent("""\
#!/usr/bin/env python3
\"\"\"Mock run.py – simulates market.ft.tech responses for sandbox evaluation.\"\"\"

import sys
import json
import argparse

MOCK_DATA = {
    "economic-china-cpi-monthly": {
        "code": 200,
        "data": [
            {"date": "2024-03", "value": 0.1, "yoy": -1.0, "unit": "%"},
            {"date": "2024-02", "value": 1.0, "yoy": 0.7, "unit": "%"},
            {"date": "2024-01", "value": 0.3, "yoy": -0.8, "unit": "%"},
        ]
    },
    "economic-china-pmi-monthly": {
        "code": 200,
        "data": [
            {"date": "2024-03", "manufacturing": 50.8, "non_manufacturing": 53.0, "unit": "index"},
            {"date": "2024-02", "manufacturing": 49.1, "non_manufacturing": 51.6, "unit": "index"},
            {"date": "2024-01", "manufacturing": 49.2, "non_manufacturing": 50.7, "unit": "index"},
        ]
    },
    "economic-china-money-supply-monthly": {
        "code": 200,
        "data": [
            {"date": "2024-03", "m0": 11.7, "m1": 8.7, "m2": 308.7, "unit": "trillion_cny"},
            {"date": "2024-02", "m0": 11.2, "m1": 8.2, "m2": 299.6, "unit": "trillion_cny"},
            {"date": "2024-01", "m0": 11.4, "m1": 8.5, "m2": 317.6, "unit": "trillion_cny"},
        ]
    },
    "economic-china-customs-trade-monthly": {
        "code": 200,
        "data": [
            {"date": "2024-03", "exports": 279.7, "imports": 220.8, "balance": 58.9, "unit": "billion_usd"},
            {"date": "2024-02", "exports": 188.8, "imports": 162.8, "balance": 26.0, "unit": "billion_usd"},
            {"date": "2024-01", "exports": 256.8, "imports": 213.0, "balance": 43.8, "unit": "billion_usd"},
        ]
    },
    "economic-china-lpr-monthly": {
        "code": 200,
        "data": [
            {"date": "2024-03", "lpr_1y": 3.45, "lpr_5y": 3.95, "unit": "%"},
            {"date": "2024-02", "lpr_1y": 3.45, "lpr_5y": 3.95, "unit": "%"},
            {"date": "2024-01", "lpr_1y": 3.45, "lpr_5y": 4.20, "unit": "%"},
        ]
    },
    "economic-us-cpi-mom": {
        "code": 200,
        "data": [
            {"date": "2024-03", "value": 0.4, "unit": "%"},
        ]
    },
}

US_MOCK = {
    "cpi-mom": {
        "code": 200,
        "data": [
            {"date": "2024-03", "value": 0.4, "unit": "%"},
            {"date": "2024-02", "value": 0.4, "unit": "%"},
            {"date": "2024-01", "value": 0.3, "unit": "%"},
        ]
    },
    "nonfarm-payroll": {
        "code": 200,
        "data": [
            {"date": "2024-03", "value": 303, "unit": "thousand"},
            {"date": "2024-02", "value": 275, "unit": "thousand"},
            {"date": "2024-01", "value": 256, "unit": "thousand"},
        ]
    },
    "unemployment-rate": {
        "code": 200,
        "data": [
            {"date": "2024-03", "value": 3.8, "unit": "%"},
            {"date": "2024-02", "value": 3.9, "unit": "%"},
            {"date": "2024-01", "value": 3.7, "unit": "%"},
        ]
    },
    "fed-funds-rate-upper": {
        "code": 200,
        "data": [
            {"date": "2024-03", "value": 5.50, "unit": "%"},
            {"date": "2024-02", "value": 5.50, "unit": "%"},
            {"date": "2024-01", "value": 5.50, "unit": "%"},
        ]
    },
    "core-cpi-yoy": {
        "code": 200,
        "data": [
            {"date": "2024-03", "value": 3.8, "unit": "%"},
            {"date": "2024-02", "value": 3.8, "unit": "%"},
            {"date": "2024-01", "value": 3.9, "unit": "%"},
        ]
    },
    "ism-manufacturing": {
        "code": 200,
        "data": [
            {"date": "2024-03", "value": 50.3, "unit": "index"},
            {"date": "2024-02", "value": 47.8, "unit": "index"},
            {"date": "2024-01", "value": 49.1, "unit": "index"},
        ]
    },
}

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"code": 400, "error": "No sub-skill specified"}))
        sys.exit(1)

    sub_skill = sys.argv[1]

    if sub_skill == "economic-us-economic-by-type":
        parser = argparse.ArgumentParser()
        parser.add_argument("sub_skill")
        parser.add_argument("--type", required=True, dest="type_val")
        args = parser.parse_args()
        result = US_MOCK.get(args.type_val, {"code": 404, "error": f"Unknown type: {args.type_val}"})
    else:
        result = MOCK_DATA.get(sub_skill, {"code": 404, "error": f"Unknown sub-skill: {sub_skill}"})

    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
""")

(skill_root / "run.py").write_text(run_py_content, encoding="utf-8")

# ── Distractor files ──────────────────────────────────────────────────────────

# Stale/misleading notes in various places
(workspace / "data/raw/china/notes.txt").write_text(
    "CPI data last pulled 2023-11. Script: fetch_cpi.py --month 2023-11\n"
    "WARNING: format changed in 2024, old scripts may break.\n",
    encoding="utf-8",
)

(workspace / "data/raw/us/notes.txt").write_text(
    "US CPI endpoint: /api/us/cpi?type=mom  (deprecated, do not use)\n"
    "New endpoint requires --type flag.\n",
    encoding="utf-8",
)

(workspace / "config/api_config.json").write_text(
    json.dumps({
        "base_url": "https://market.ft.tech",
        "deprecated_endpoints": {
            "china_cpi": "/v1/china/cpi",
            "us_nonfarm": "/v1/us/nonfarm"
        },
        "note": "These endpoints are deprecated. Use run.py instead."
    }, indent=2),
    encoding="utf-8",
)

(workspace / "config/indicator_map_WRONG.json").write_text(
    json.dumps({
        "china": {
            "CPI": "economic-china-cpi",
            "PMI": "economic-china-pmi",
            "M2": "economic-china-m2-monthly"
        },
        "us": {
            "CPI": "economic-us-cpi-monthly",
            "nonfarm": "economic-us-nonfarm-monthly"
        },
        "_warning": "This file is OUTDATED and contains wrong sub-skill names. Do not use."
    }, indent=2),
    encoding="utf-8",
)

(workspace / "scripts/helpers/old_fetch.py").write_text(
    "# Deprecated helper - uses wrong API paths\n"
    "# DO NOT USE\n"
    "import requests\n"
    "def fetch_china_cpi():\n"
    "    return requests.get('https://market.ft.tech/v1/china/cpi').json()\n",
    encoding="utf-8",
)

(workspace / "scripts/helpers/us_indicators.py").write_text(
    "# Partial helper - missing --type param logic\n"
    "# use run.py directly\n"
    "INDICATORS = ['cpi', 'nonfarm', 'fed_rate', 'unemployment']\n",
    encoding="utf-8",
)

(workspace / "reports/drafts/template_v1.json").write_text(
    json.dumps({
        "report_date": "2024-Q1",
        "china": {},
        "us": {},
        "_note": "Template only - populate via data fetch scripts"
    }, indent=2),
    encoding="utf-8",
)

(workspace / "reports/archive/macro_report_2023Q4.json").write_text(
    json.dumps({
        "report_date": "2023-Q4",
        "china": {
            "cpi_latest": {"date": "2023-12", "yoy": -0.3},
            "pmi_latest": {"date": "2023-12", "manufacturing": 50.2}
        },
        "us": {
            "cpi_mom_latest": {"date": "2023-12", "value": 0.3},
            "nonfarm_latest": {"date": "2023-12", "value": 216}
        }
    }, indent=2),
    encoding="utf-8",
)

(workspace / "logs/fetch_log_2024-01.txt").write_text(
    "[2024-01-15] ERROR: economic-china-cpi - connection timeout\n"
    "[2024-01-15] ERROR: economic-us-economic-by-type --type cpi-mom - 503\n"
    "[2024-01-16] SUCCESS: all indicators fetched\n",
    encoding="utf-8",
)

(workspace / "tmp/scratch.txt").write_text(
    "TODO: automate monthly pull\n"
    "sub-skills to use: economic-china-cpi-monthly, economic-china-pmi-monthly\n"
    "US: need --type flag for each indicator\n",
    encoding="utf-8",
)

(workspace / "data/processed/last_run_meta.json").write_text(
    json.dumps({
        "last_successful_run": "2024-01-16T09:00:00Z",
        "indicators_fetched": 5,
        "errors": 0
    }, indent=2),
    encoding="utf-8",
)

# Sub-skill SKILL.md files (minimal, for reference)
sub_skill_docs = {
    "economic-china-cpi-monthly": "# China CPI Monthly\nReturns monthly CPI data.\nNo extra params needed.\n",
    "economic-china-pmi-monthly": "# China PMI Monthly\nReturns manufacturing & non-manufacturing PMI.\nNo extra params needed.\n",
    "economic-china-money-supply-monthly": "# China Money Supply Monthly\nReturns M0, M1, M2 data.\nNo extra params needed.\n",
    "economic-china-customs-trade-monthly": "# China Customs Trade Monthly\nReturns exports, imports, trade balance.\nNo extra params needed.\n",
    "economic-china-lpr-monthly": "# China LPR Monthly\nReturns 1Y and 5Y LPR rates.\nNo extra params needed.\n",
    "economic-us-economic-by-type": (
        "# US Economic By Type\n"
        "Requires --type parameter.\n"
        "Valid types: ism-manufacturing, ism-non-manufacturing, nonfarm-payroll,\n"
        "trade-balance, unemployment-rate, ppi-mom, cpi-mom, cpi-yoy,\n"
        "core-cpi-mom, core-cpi-yoy, housing-starts, existing-home-sales,\n"
        "durable-goods-orders-mom, cb-consumer-confidence,\n"
        "gdp-yoy-preliminary, fed-funds-rate-upper\n"
    ),
}

for skill_name, content in sub_skill_docs.items():
    path = workspace / f"skills/FTShare-macro-economy-data/sub-skills/{skill_name}/SKILL.md"
    path.write_text(content, encoding="utf-8")

print("Workspace initialized successfully.")
print(f"Skill root: {skill_root}")
print(f"run.py: {skill_root / 'run.py'}")