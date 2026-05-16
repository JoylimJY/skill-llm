import os
import json
import textwrap
from pathlib import Path

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ── Create deeply nested distractor structure ──────────────────────────────────
dirs = [
    "skills/hk_data",
    "skills/hk_data/company_hk",
    "skills/hk_data/valuatnanalyd",
    "skills/hk_data/candlesticks",
    "skills/hk_data/view",
    "data/raw",
    "data/processed",
    "reports/drafts",
    "reports/archive",
    "config",
    "logs",
    "tests",
    "notebooks",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractors = {
    "skills/hk_data/company_hk/schema.json": json.dumps({"fields": ["trade_code", "company_name", "intro"]}),
    "skills/hk_data/valuatnanalyd/params.txt": "page, page_size, trade_code (optional)",
    "skills/hk_data/candlesticks/notes.txt": "interval options: day, month, quarter, year",
    "skills/hk_data/view/readme_old.txt": "deprecated - use hk-view subskill",
    "data/raw/sample_trade_codes.txt": "00700.HK\n02318.HK\n00005.HK\n01299.HK",
    "data/processed/old_report_template.json": json.dumps({"stock": "", "date": "", "metrics": {}}),
    "data/raw/hk_market_overview_20240101.csv": "date,open,high,low,close\n2024-01-01,10.0,10.5,9.8,10.2",
    "reports/drafts/draft_valuation_20240315.txt": "PE TTM: 12.3\nPB: 1.5\n(draft only)",
    "reports/archive/old_report_02318_2023.json": json.dumps({"stock": "02318.HK", "year": 2023, "note": "archived"}),
    "config/api_endpoints.txt": "# These endpoints are outdated\nold_base_url: https://old.ft.tech\n",
    "logs/run_errors_20240401.log": "[ERROR] connection timeout\n[ERROR] invalid param\n",
    "tests/test_stub.py": "# placeholder test\ndef test_placeholder():\n    pass\n",
    "notebooks/exploratory_eda.ipynb": json.dumps({"cells": [], "metadata": {}, "nbformat": 4}),
}
for rel_path, content in distractors.items():
    p = workspace / rel_path
    p.write_text(content)

# ── The SKILL.md (top-level) ───────────────────────────────────────────────────
skill_md_top = textwrap.dedent("""\
---
name: FTShare-hk-data
description: 港股数据技能集（market.ft.tech）。覆盖公司介绍、分页估值分析（PE/PB/PS/股息率）、单票基础视图（板块/上市状态/市值/股本）、日/月/季/年 K 线（历史k线，T日18点更新当日数据）（前复权/不复权）。
---

# FT 港股数据 Skills

本 skill 是 `FTShare-hk-data` 的**统一路由入口**。

根据用户问题，从下方「能力总览」或「询问方式与子 skill 对应表」匹配对应子 skill，然后通过 `run.py` 执行并解析响应。

> 所有接口均以 `https://market.ft.tech` 为基础域名，本技能集子 skill 无需额外请求头。

### 时区与交易日历

港股交易时间遵循 **港交所交易日历（UTC+8 / 东八区）**。

- 所有 **YYYYMMDD / YYYY-MM-DD** 日期字段均为东八区交易日。
- `update_time`（如 `20260324120000`）等时间戳字段也基于东八区。
- 调用方传入日期时无需手动转时区——接口本身按东八区解释。
- 若 Agent 所在系统时区非东八区，在计算「今天」「昨天」等相对日期时，应先转为东八区日期再传参。

---

## 调用方式（唯一规则）

`run.py` 与本文件（`SKILL.md`）位于同一目录。执行时：

1. 取本文件的绝对路径，将末尾 `/SKILL.md` 替换为 `/run.py`，得到 `<RUN_PY>` 。
2. 调用：`python <RUN_PY> <子skill名> [参数...]`

```bash
# 示例（<RUN_PY> 为实际绝对路径）
python <RUN_PY> company-hk --trade_code 00700.HK
python <RUN_PY> hk-valuatnanalyd --trade_code 00700.HK --page 1 --page_size 20
python <RUN_PY> hk-valuatnanalyd --page 1 --page_size 20
python <RUN_PY> hk-view --hk_code 00700.HK
python <RUN_PY> hk-candlesticks --trade-code 00700.HK --interval-unit day --until-date 2026-03-24 --since-date 2026-03-01 --limit 20
```

> `run.py` 内部通过 `__file__` 自定位，无论安装在何处都能正确找到各子 skill 的脚本。

---

## 港股 — 询问方式与子 skill 对应表

| 询问方式（用户常说的词） | 子 skill |
|------------------------|----------|
| **港股公司简介**、**港股公司介绍**、**00700 公司信息**、**腾讯控股 港股 介绍**、成立日期、注册资本、法人代表、主营业务 | `company-hk` |
| **港股估值**、**估值分析**、**市盈率/市净率/市销率**、**股息率**、**港股全市场估值分页**、PE TTM、PB、换手率 | `hk-valuatnanalyd` |
| **港股基础视图**、**港股一览**、**单票市值/总股本**、**主板/上市状态**、**关联 A 股代码**（与历史分页估值区分，要「当前视图」） | `hk-view` |
| **港股 K 线**、**港股日线/月线/季线/年线**、**00700 历史行情**、OHLC、前复权港股 | `hk-candlesticks` |

---

## 能力总览

| 子 skill | 说明 |
|----------|------|
| `company-hk` | 按 `trade_code`（如 `00700.HK`）查询港股公司介绍 |
| `hk-valuatnanalyd` | 分页查询港股估值分析；可选 `trade_code` 过滤单票，不传为全市场 |
| `hk-view` | 按 `hk_code` 查询单票基础视图（板块、上市状态、股本、市值、估值指标） |
| `hk-candlesticks` | 按 `trade_code` 查询日/月/季/年 K 线；`until_date` 必填，`since_date` 可选 |

---

## 子 skill 文档

各子目录内另有 `SKILL.md`，含接口路径、参数与响应字段说明；执行时以本目录 `run.py` 为准。
""")

(workspace / "skills/hk_data/SKILL.md").write_text(skill_md_top)

# ── Sub-skill SKILL.md files ──────────────────────────────────────────────────
company_skill_md = textwrap.dedent("""\
# company-hk Sub-Skill

## Endpoint
GET /hk/company

## Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| trade_code | string | Yes | 港股代码，如 `00700.HK` |

## Response Fields
| Field | Description |
|-------|-------------|
| trade_code | 股票代码 |
| company_name | 公司全称 |
| listing_date | 上市日期 |
| registered_capital | 注册资本 |
| legal_representative | 法人代表 |
| main_business | 主营业务简介 |
| intro | 公司详细介绍 |
""")
(workspace / "skills/hk_data/company_hk/SKILL.md").write_text(company_skill_md)

view_skill_md = textwrap.dedent("""\
# hk-view Sub-Skill

## Endpoint
GET /hk/view

## Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| hk_code | string | Yes | 港股代码，如 `00700.HK` |

## Response Fields
| Field | Description |
|-------|-------------|
| hk_code | 港股代码 |
| company_name | 公司简称 |
| sector | 所属板块 |
| listing_status | 上市状态 |
| market_cap | 总市值（港元） |
| total_shares | 总股本（股） |
| a_share_code | 关联A股代码（如有） |
| pe_ttm | 市盈率TTM |
| pb | 市净率 |
""")
(workspace / "skills/hk_data/view/SKILL.md").write_text(view_skill_md)

valuation_skill_md = textwrap.dedent("""\
# hk-valuatnanalyd Sub-Skill

## Endpoint
GET /hk/valuatnanalyd

## Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| page | int | Yes | 页码，从1开始 |
| page_size | int | Yes | 每页条数 |
| trade_code | string | No | 股票代码过滤，不传返回全市场 |

## Response Fields
| Field | Description |
|-------|-------------|
| total | 总条数 |
| page | 当前页 |
| page_size | 每页条数 |
| data | 估值列表 |
| data[].trade_code | 股票代码 |
| data[].pe_ttm | 市盈率（TTM） |
| data[].pb | 市净率 |
| data[].ps | 市销率 |
| data[].dividend_yield | 股息率 |
| data[].turnover_rate | 换手率 |
| data[].update_time | 更新时间（东八区，格式 YYYYMMDDHHmmss） |
""")
(workspace / "skills/hk_data/valuatnanalyd/SKILL.md").write_text(valuation_skill_md)

candlesticks_skill_md = textwrap.dedent("""\
# hk-candlesticks Sub-Skill

## Endpoint
GET /hk/candlesticks

## Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| trade-code | string | Yes | 港股代码，如 `00700.HK`（注意：参数名用连字符） |
| interval-unit | string | Yes | K线周期：`day` / `month` / `quarter` / `year` |
| until-date | string | Yes | 截止日期，格式 `YYYY-MM-DD` |
| since-date | string | No | 起始日期，格式 `YYYY-MM-DD` |
| limit | int | No | 返回条数上限，默认20 |
| adjust | string | No | 复权类型：`forward`（前复权）/ `none`（不复权，默认） |

## Response Fields
| Field | Description |
|-------|-------------|
| trade_code | 股票代码 |
| interval_unit | K线周期 |
| adjust | 复权类型 |
| data | K线列表（按日期升序） |
| data[].date | 交易日期 YYYY-MM-DD |
| data[].open | 开盘价 |
| data[].high | 最高价 |
| data[].low | 最低价 |
| data[].close | 收盘价 |
| data[].volume | 成交量 |
| data[].turnover | 成交额 |
""")
(workspace / "skills/hk_data/candlesticks/SKILL.md").write_text(candlesticks_skill_md)

# ── Mock server script ─────────────────────────────────────────────────────────
mock_server_code = textwrap.dedent("""\
#!/usr/bin/env python3
\"\"\"Mock server for market.ft.tech — deterministic responses for testing.\"\"\"
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

HK_VIEW_02318 = {
    "hk_code": "02318.HK",
    "company_name": "中国平安",
    "sector": "金融",
    "listing_status": "正常上市",
    "market_cap": 868000000000,
    "total_shares": 18210000000,
    "a_share_code": "601318.SH",
    "pe_ttm": 9.87,
    "pb": 1.23
}

HK_VALUATION_02318 = {
    "total": 1,
    "page": 1,
    "page_size": 20,
    "data": [
        {
            "trade_code": "02318.HK",
            "pe_ttm": 9.87,
            "pb": 1.23,
            "ps": 0.87,
            "dividend_yield": 5.12,
            "turnover_rate": 0.34,
            "update_time": "20260324120000"
        }
    ]
}

CANDLESTICKS_02318_DAY = {
    "trade_code": "02318.HK",
    "interval_unit": "day",
    "adjust": "none",
    "data": [
        {"date": "2026-03-01", "open": 47.10, "high": 47.80, "low": 46.90, "close": 47.55, "volume": 12340000, "turnover": 586500000},
        {"date": "2026-03-02", "open": 47.55, "high": 48.20, "low": 47.30, "close": 48.00, "volume": 13200000, "turnover": 634000000},
        {"date": "2026-03-03", "open": 48.00, "high": 48.50, "low": 47.70, "close": 48.30, "volume": 11800000, "turnover": 570000000},
        {"date": "2026-03-04", "open": 48.30, "high": 49.00, "low": 48.10, "close": 48.75, "volume": 14500000, "turnover": 708000000},
        {"date": "2026-03-05", "open": 48.75, "high": 49.20, "low": 48.50, "close": 49.10, "volume": 15200000, "turnover": 748000000},
        {"date": "2026-03-06", "open": 49.10, "high": 49.60, "low": 48.80, "close": 49.40, "volume": 13800000, "turnover": 683000000},
        {"date": "2026-03-07", "open": 49.40, "high": 50.00, "low": 49.20, "close": 49.85, "volume": 16100000, "turnover": 803000000},
        {"date": "2026-03-08", "open": 49.85, "high": 50.30, "low": 49.50, "close": 50.10, "volume": 14700000, "turnover": 738000000},
        {"date": "2026-03-09", "open": 50.10, "high": 50.80, "low": 49.90, "close": 50.60, "volume": 17200000, "turnover": 871000000},
        {"date": "2026-03-10", "open": 50.60, "high": 51.00, "low": 50.20, "close": 50.80, "volume": 15900000, "turnover": 810000000},
        {"date": "2026-03-11", "open": 50.80, "high": 51.30, "low": 50.50, "close": 51.10, "volume": 14200000, "turnover": 727000000},
        {"date": "2026-03-12", "open": 51.10, "high": 51.70, "low": 50.90, "close": 51.50, "volume": 13500000, "turnover": 696000000},
        {"date": "2026-03-13", "open": 51.50, "high": 52.00, "low": 51.20, "close": 51.90, "volume": 16800000, "turnover": 873000000},
        {"date": "2026-03-14", "open": 51.90, "high": 52.40, "low": 51.60, "close": 52.20, "volume": 15300000, "turnover": 799000000},
        {"date": "2026-03-17", "open": 52.20, "high": 52.80, "low": 51.90, "close": 52.60, "volume": 14100000, "turnover": 743000000},
        {"date": "2026-03-18", "open": 52.60, "high": 53.10, "low": 52.30, "close": 52.90, "volume": 13700000, "turnover": 726000000},
        {"date": "2026-03-19", "open": 52.90, "high": 53.50, "low": 52.60, "close": 53.30, "volume": 15800000, "turnover": 841000000},
        {"date": "2026-03-20", "open": 53.30, "high": 54.00, "low": 53.00, "close": 53.80, "volume": 17500000, "turnover": 944000000},
        {"date": "2026-03-21", "open": 53.80, "high": 54.20, "low": 53.50, "close": 54.00, "volume": 14900000, "turnover": 807000000},
        {"date": "2026-03-24", "open": 54.00, "high": 54.50, "low": 53.80, "close": 54.30, "volume": 13200000, "turnover": 718000000},
    ]
}

HK_COMPANY_02318 = {
    "trade_code": "02318.HK",
    "company_name": "中国平安保险（集团）股份有限公司",
    "listing_date": "2004-06-24",
    "registered_capital": "18210000000",
    "legal_representative": "马明哲",
    "main_business": "保险、银行、资产管理",
    "intro": "中国平安保险（集团）股份有限公司成立于1988年，是中国最大的综合金融服务集团之一。"
}

@app.route('/hk/view')
def hk_view():
    hk_code = request.args.get('hk_code', '')
    if hk_code == '02318.HK':
        return jsonify({"code": 0, "data": HK_VIEW_02318})
    return jsonify({"code": 404, "message": "not found"}), 404

@app.route('/hk/valuatnanalyd')
def hk_valuation():
    trade_code = request.args.get('trade_code', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))
    if trade_code == '02318.HK':
        resp = dict(HK_VALUATION_02318)
        resp['page'] = page
        resp['page_size'] = page_size
        return jsonify({"code": 0, "data": resp})
    return jsonify({"code": 404, "message": "not found"}), 404

@app.route('/hk/candlesticks')
def hk_candlesticks():
    trade_code = request.args.get('trade_code', '')
    interval_unit = request.args.get('interval_unit', 'day')
    until_date = request.args.get('until_date', '')
    since_date = request.args.get('since_date', '')
    adjust = request.args.get('adjust', 'none')
    limit = int(request.args.get('limit', 20))
    if trade_code == '02318.HK' and interval_unit == 'day':
        data = list(CANDLESTICKS_02318_DAY['data'])
        if since_date:
            data = [d for d in data if d['date'] >= since_date]
        if until_date:
            data = [d for d in data if d['date'] <= until_date]
        data = data[:limit]
        resp = {
            "trade_code": trade_code,
            "interval_unit": interval_unit,
            "adjust": adjust,
            "data": data
        }
        return jsonify({"code": 0, "data": resp})
    return jsonify({"code": 404, "message": "not found"}), 404

@app.route('/hk/company')
def hk_company():
    trade_code = request.args.get('trade_code', '')
    if trade_code == '02318.HK':
        return jsonify({"code": 0, "data": HK_COMPANY_02318})
    return jsonify({"code": 404, "message": "not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=18888, debug=False)
""")
(workspace / "mock_server.py").write_text(mock_server_code)

# ── run.py (the actual skill runner) ──────────────────────────────────────────
run_py_code = textwrap.dedent("""\
#!/usr/bin/env python3
\"\"\"
FTShare-hk-data unified skill runner.
Usage: python run.py <sub-skill> [args...]
\"\"\"
import sys
import json
import argparse
import requests

BASE_URL = "http://localhost:18888"

def run_company_hk(args):
    p = argparse.ArgumentParser()
    p.add_argument('--trade_code', required=True)
    ns = p.parse_args(args)
    r = requests.get(f"{BASE_URL}/hk/company", params={'trade_code': ns.trade_code})
    return r.json()

def run_hk_view(args):
    p = argparse.ArgumentParser()
    p.add_argument('--hk_code', required=True)
    ns = p.parse_args(args)
    r = requests.get(f"{BASE_URL}/hk/view", params={'hk_code': ns.hk_code})
    return r.json()

def run_hk_valuatnanalyd(args):
    p = argparse.ArgumentParser()
    p.add_argument('--page', type=int, required=True)
    p.add_argument('--page_size', type=int, required=True)
    p.add_argument('--trade_code', default=None)
    ns = p.parse_args(args)
    params = {'page': ns.page, 'page_size': ns.page_size}
    if ns.trade_code:
        params['trade_code'] = ns.trade_code
    r = requests.get(f"{BASE_URL}/hk/valuatnanalyd", params=params)
    return r.json()

def run_hk_candlesticks(args):
    p = argparse.ArgumentParser()
    p.add_argument('--trade-code', dest='trade_code', required=True)
    p.add_argument('--interval-unit', dest='interval_unit', required=True)
    p.add_argument('--until-date', dest='until_date', required=True)
    p.add_argument('--since-date', dest='since_date', default=None)
    p.add_argument('--limit', type=int, default=20)
    p.add_argument('--adjust', default='none')
    ns = p.parse_args(args)
    params = {
        'trade_code': ns.trade_code,
        'interval_unit': ns.interval_unit,
        'until_date': ns.until_date,
        'adjust': ns.adjust,
        'limit': ns.limit,
    }
    if ns.since_date:
        params['since_date'] = ns.since_date
    r = requests.get(f"{BASE_URL}/hk/candlesticks", params=params)
    return r.json()

SKILLS = {
    'company-hk': run_company_hk,
    'hk-view': run_hk_view,
    'hk-valuatnanalyd': run_hk_valuatnanalyd,
    'hk-candlesticks': run_hk_candlesticks,
}

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({"error": "sub-skill name required"}))
        sys.exit(1)
    skill_name = sys.argv[1]
    skill_args = sys.argv[2:]
    if skill_name not in SKILLS:
        print(json.dumps({"error": f"unknown skill: {skill_name}"}))
        sys.exit(1)
    result = SKILLS[skill_name](skill_args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
""")
(workspace / "skills/hk_data/run.py").write_text(run_py_code)
os.chmod(workspace / "skills/hk_data/run.py", 0o755)

# ── Task description file (business context, no hints) ────────────────────────
task_desc = textwrap.dedent("""\
# Analyst Research Task

Stock: 02318.HK (Ping An Insurance Group)
Reference Date Range for Price History: 2026-03-01 to 2026-03-24

Please produce a consolidated research report file named: research_report.json
""")
(workspace / "TASK.md").write_text(task_desc)

print("Workspace initialized successfully.")
print(f"Files created: {len(list(workspace.rglob('*')))} total")