import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Directory structure with distractors ──────────────────────────────────────
dirs = [
    "skills/FTShare-fund-data/sub-skills/fund-basicinfo-single-fund",
    "skills/FTShare-fund-data/sub-skills/fund-cal-return-single-fund-specific-period",
    "skills/FTShare-fund-data/sub-skills/fund-nav-single-fund-paginated",
    "skills/FTShare-fund-data/sub-skills/fund-overview-all-funds-paginated",
    "skills/FTShare-fund-data/sub-skills/fund-support-symbols-all-funds-paginated",
    "research/quarterly_reports/2024Q1",
    "research/quarterly_reports/2024Q2",
    "research/data_cache",
    "config",
    "logs",
    "tools/deprecated",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── SKILL.md (entry point) ─────────────────────────────────────────────────────
skill_md = """\
---
name: FTShare-fund-data
description: 基金数据技能集（market.ft.tech）。覆盖基金基本信息、净值历史、累计收益率、基金概览列表、支持基金标的列表。用户询问基金详情、基金净值、基金收益、基金列表时使用。
---

# FT 基金数据 Skills

本 skill 是 `FTShare-fund-data` 的**统一路由入口**。

根据用户问题，从下方「能力总览」或「询问方式与子 skill 对应表」匹配对应子 skill，然后通过 `run.py` 执行并解析响应。

> 所有接口均以 `https://market.ft.tech` 为基础域名。

---

## 调用方式（唯一规则）

`run.py` 与本文件（`SKILL.md`）位于同一目录。执行时：

1. 取本文件的绝对路径，将末尾 `/SKILL.md` 替换为 `/run.py`，得到 `<RUN_PY>` 。
2. 调用：`python <RUN_PY> <子skill名> [参数...]`

```bash
# 示例（<RUN_PY> 为实际绝对路径）
python <RUN_PY> fund-basicinfo-single-fund --institution-code 000001
python <RUN_PY> fund-cal-return-single-fund-specific-period --institution-code 159619 --cal-type 1Y
python <RUN_PY> fund-nav-single-fund-paginated --institution-code 000001 --page 1 --page-size 50
python <RUN_PY> fund-overview-all-funds-paginated --page 1 --page-size 20
python <RUN_PY> fund-support-symbols-all-funds-paginated --page 1 --page-size 20
```

> `run.py` 内部通过 `__file__` 自定位，无须在意执行时的工作目录。

---

## 基金 — 询问方式与子 skill 对应表

| 询问方式（用户常说的词） | 子 skill |
|------------------------|----------|
| **基金基本信息**、某只**基金详情**、**基金管理人/基金经理**、**基金类型/投资目标** | `fund-basicinfo-single-fund` |
| **基金累计收益率**、**近1年/近3个月收益**、**YTD 收益**、**基金收益曲线** | `fund-cal-return-single-fund-specific-period` |
| **基金净值**、**单位净值/累计净值**、**日增长率**、**基金净值历史** | `fund-nav-single-fund-paginated` |
| **基金概览**、**所有基金信息**、**基金列表概况** | `fund-overview-all-funds-paginated` |
| **支持的基金列表**、**基金代码清单**、**所有基金标的** | `fund-support-symbols-all-funds-paginated` |

---

## 能力总览

- **`fund-basicinfo-single-fund`**：查询指定基金基础信息（名称、管理人、经理、类型、投资目标等）。必填：`--institution-code`（6 位基金代码）。若用户仅给基金名称，先通过 `fund-support-symbols-all-funds-paginated` 或 `fund-overview-all-funds-paginated` 映射代码再查。
- **`fund-cal-return-single-fund-specific-period`**：查询指定基金在指定区间的累计收益率时间序列。必填：`--institution-code`、`--cal-type`（1M/3M/6M/1Y/3Y/5Y/YTD）。建议先完成名称到代码映射后再调用。
- **`fund-nav-single-fund-paginated`**：查询指定基金净值历史（分页）。必填：`--institution-code`；可选：`--page`、`--page-size`。建议先完成名称到代码映射后再调用。
- **`fund-overview-all-funds-paginated`**：查询所有基金概览信息（分页）。可选：`--page`、`--page-size`。
- **`fund-support-symbols-all-funds-paginated`**：查询所有支持基金的标的列表（分页）。可选：`--page`、`--page-size`。

---

## 使用流程

1. **记录本文件绝对路径**，将 `/SKILL.md` 替换为 `/run.py` 得到 `<RUN_PY>`。
2. **理解用户意图**，从「询问方式与子 skill 对应表」或「能力总览」匹配子 skill 名称。
3. **若用户给的是基金名称而非代码**：先调用 `fund-support-symbols-all-funds-paginated` 或 `fund-overview-all-funds-paginated` 获取候选，确定 6 位 `institution-code`。
4. （可选）读取 `sub-skills/<子skill名>/SKILL.md` 了解接口与参数。
5. **执行**：`python <RUN_PY> <子skill名> [参数...]`，获取 JSON 输出。
6. **解析并输出**：以表格或要点形式展示给用户；若候选不唯一，先让用户确认再查询指标。
"""
(workspace / "skills/FTShare-fund-data/SKILL.md").write_text(skill_md, encoding="utf-8")

# ── run.py ─────────────────────────────────────────────────────────────────────
run_py = """\
#!/usr/bin/env python3
\"\"\"Unified entry point for FTShare-fund-data skill.\"\"\"
import sys
import os
import subprocess
from pathlib import Path

SKILL_DIR = Path(__file__).parent
SUB_SKILLS_DIR = SKILL_DIR / "sub-skills"

def main():
    if len(sys.argv) < 2:
        print("Usage: python run.py <sub-skill-name> [args...]")
        sys.exit(1)
    sub_skill = sys.argv[1]
    args = sys.argv[2:]
    script = SUB_SKILLS_DIR / sub_skill / "run.py"
    if not script.exists():
        print(f"ERROR: sub-skill '{sub_skill}' not found at {script}")
        sys.exit(1)
    result = subprocess.run(
        [sys.executable, str(script)] + args,
        capture_output=False
    )
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
"""
(workspace / "skills/FTShare-fund-data/run.py").write_text(run_py, encoding="utf-8")

# ── Mock data definitions ──────────────────────────────────────────────────────
# Page 1 funds (10 funds) - target funds are on page 2
page1_symbols = [
    {"institution_code": "000001", "fund_name": "华夏成长混合"},
    {"institution_code": "000002", "fund_name": "华夏股票"},
    {"institution_code": "000003", "fund_name": "中信稳健成长"},
    {"institution_code": "000004", "fund_name": "南方稳健成长二号"},
    {"institution_code": "000005", "fund_name": "嘉实增长混合"},
    {"institution_code": "000006", "fund_name": "广发稳健增长混合"},
    {"institution_code": "000007", "fund_name": "博时价值增长"},
    {"institution_code": "000008", "fund_name": "鹏华行业成长"},
    {"institution_code": "000009", "fund_name": "大成价值增长"},
    {"institution_code": "000010", "fund_name": "融通新蓝筹"},
]
# Page 2 funds (include our two target funds)
page2_symbols = [
    {"institution_code": "159619", "fund_name": "华泰柏瑞中证A500ETF"},
    {"institution_code": "110022", "fund_name": "易方达消费行业股票"},
    {"institution_code": "001938", "fund_name": "中欧时代先锋股票A"},
    {"institution_code": "519674", "fund_name": "银河创新成长混合"},
    {"institution_code": "001714", "fund_name": "广发多因子混合"},
    {"institution_code": "000691", "fund_name": "工银瑞信新金融股票A"},
    {"institution_code": "001643", "fund_name": "汇丰晋信智造先锋股票A"},
    {"institution_code": "003376", "fund_name": "易方达瑞恒混合A"},
    {"institution_code": "004997", "fund_name": "天弘中证食品饮料ETF联接A"},
    {"institution_code": "005827", "fund_name": "易方达蓝筹精选混合"},
]

# Basic info for target funds
basicinfo_159619 = {
    "code": "159619",
    "name": "华泰柏瑞中证A500ETF",
    "fund_type": "股票型ETF",
    "manager_company": "华泰柏瑞基金管理有限公司",
    "fund_manager": "柳军",
    "investment_objective": "紧密跟踪中证A500指数，追求跟踪偏差和跟踪误差的最小化。",
    "establishment_date": "2023-10-16",
    "total_asset": "5820000000",
}
basicinfo_110022 = {
    "code": "110022",
    "name": "易方达消费行业股票",
    "fund_type": "股票型",
    "manager_company": "易方达基金管理有限公司",
    "fund_manager": "萧楠",
    "investment_objective": "重点投资于消费行业的上市公司股票，力争实现基金资产的长期增值。",
    "establishment_date": "2010-08-20",
    "total_asset": "42500000000",
}

# Return data for 1Y and 3M
returns_159619_1Y = [
    {"date": "2023-11-01", "return_rate": -0.023},
    {"date": "2023-12-01", "return_rate": 0.012},
    {"date": "2024-01-01", "return_rate": -0.045},
    {"date": "2024-02-01", "return_rate": 0.067},
    {"date": "2024-03-01", "return_rate": 0.031},
    {"date": "2024-04-01", "return_rate": -0.018},
    {"date": "2024-05-01", "return_rate": 0.025},
    {"date": "2024-06-01", "return_rate": -0.009},
    {"date": "2024-07-01", "return_rate": 0.041},
    {"date": "2024-08-01", "return_rate": -0.033},
    {"date": "2024-09-01", "return_rate": 0.092},
    {"date": "2024-10-01", "return_rate": 0.015},
]
returns_159619_3M = [
    {"date": "2024-08-01", "return_rate": -0.033},
    {"date": "2024-09-01", "return_rate": 0.092},
    {"date": "2024-10-01", "return_rate": 0.015},
]
returns_110022_1Y = [
    {"date": "2023-11-01", "return_rate": 0.031},
    {"date": "2023-12-01", "return_rate": -0.015},
    {"date": "2024-01-01", "return_rate": -0.062},
    {"date": "2024-02-01", "return_rate": 0.044},
    {"date": "2024-03-01", "return_rate": -0.021},
    {"date": "2024-04-01", "return_rate": 0.008},
    {"date": "2024-05-01", "return_rate": 0.019},
    {"date": "2024-06-01", "return_rate": -0.037},
    {"date": "2024-07-01", "return_rate": 0.055},
    {"date": "2024-08-01", "return_rate": -0.028},
    {"date": "2024-09-01", "return_rate": 0.073},
    {"date": "2024-10-01", "return_rate": 0.022},
]
returns_110022_3M = [
    {"date": "2024-08-01", "return_rate": -0.028},
    {"date": "2024-09-01", "return_rate": 0.073},
    {"date": "2024-10-01", "return_rate": 0.022},
]

# Save mock data as JSON files for the mock server to serve
mock_data = {
    "symbols_page1": {
        "total": 20, "page": 1, "page_size": 10,
        "data": page1_symbols
    },
    "symbols_page2": {
        "total": 20, "page": 2, "page_size": 10,
        "data": page2_symbols
    },
    "basicinfo_159619": basicinfo_159619,
    "basicinfo_110022": basicinfo_110022,
    "returns_159619_1Y": {"institution_code": "159619", "cal_type": "1Y", "data": returns_159619_1Y},
    "returns_159619_3M": {"institution_code": "159619", "cal_type": "3M", "data": returns_159619_3M},
    "returns_110022_1Y": {"institution_code": "110022", "cal_type": "1Y", "data": returns_110022_1Y},
    "returns_110022_3M": {"institution_code": "110022", "cal_type": "3M", "data": returns_110022_3M},
}

mock_data_dir = workspace / "config/mock_data"
mock_data_dir.mkdir(parents=True, exist_ok=True)
for key, val in mock_data.items():
    (mock_data_dir / f"{key}.json").write_text(json.dumps(val, ensure_ascii=False, indent=2), encoding="utf-8")

# ── Sub-skill: fund-support-symbols-all-funds-paginated ────────────────────────
symbols_run = """\
#!/usr/bin/env python3
import sys, requests, json, os

BASE_URL = os.environ.get("FT_BASE_URL", "https://market.ft.tech")

def main():
    page = 1
    page_size = 10
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--page" and i+1 < len(args):
            page = int(args[i+1]); i += 2
        elif args[i] == "--page-size" and i+1 < len(args):
            page_size = int(args[i+1]); i += 2
        else:
            i += 1
    url = f"{BASE_URL}/api/fund/support-symbols"
    resp = requests.get(url, params={"page": page, "page_size": page_size}, timeout=10)
    print(json.dumps(resp.json(), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
"""
(workspace / "skills/FTShare-fund-data/sub-skills/fund-support-symbols-all-funds-paginated/run.py").write_text(symbols_run, encoding="utf-8")

# ── Sub-skill: fund-basicinfo-single-fund ─────────────────────────────────────
basicinfo_run = """\
#!/usr/bin/env python3
import sys, requests, json, os

BASE_URL = os.environ.get("FT_BASE_URL", "https://market.ft.tech")

def main():
    institution_code = None
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--institution-code" and i+1 < len(args):
            institution_code = args[i+1]; i += 2
        else:
            i += 1
    if not institution_code:
        print("ERROR: --institution-code required"); sys.exit(1)
    url = f"{BASE_URL}/api/fund/basicinfo/{institution_code}"
    resp = requests.get(url, timeout=10)
    print(json.dumps(resp.json(), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
"""
(workspace / "skills/FTShare-fund-data/sub-skills/fund-basicinfo-single-fund/run.py").write_text(basicinfo_run, encoding="utf-8")

# ── Sub-skill: fund-cal-return-single-fund-specific-period ────────────────────
calreturn_run = """\
#!/usr/bin/env python3
import sys, requests, json, os

BASE_URL = os.environ.get("FT_BASE_URL", "https://market.ft.tech")

VALID_CAL_TYPES = {"1M", "3M", "6M", "1Y", "3Y", "5Y", "YTD"}

def main():
    institution_code = None
    cal_type = None
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--institution-code" and i+1 < len(args):
            institution_code = args[i+1]; i += 2
        elif args[i] == "--cal-type" and i+1 < len(args):
            cal_type = args[i+1]; i += 2
        else:
            i += 1
    if not institution_code:
        print("ERROR: --institution-code required"); sys.exit(1)
    if not cal_type or cal_type not in VALID_CAL_TYPES:
        print(f"ERROR: --cal-type must be one of {VALID_CAL_TYPES}"); sys.exit(1)
    url = f"{BASE_URL}/api/fund/cal-return/{institution_code}"
    resp = requests.get(url, params={"cal_type": cal_type}, timeout=10)
    print(json.dumps(resp.json(), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
"""
(workspace / "skills/FTShare-fund-data/sub-skills/fund-cal-return-single-fund-specific-period/run.py").write_text(calreturn_run, encoding="utf-8")

# ── Sub-skill: fund-nav-single-fund-paginated ─────────────────────────────────
nav_run = """\
#!/usr/bin/env python3
import sys, requests, json, os

BASE_URL = os.environ.get("FT_BASE_URL", "https://market.ft.tech")

def main():
    institution_code = None
    page = 1
    page_size = 20
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--institution-code" and i+1 < len(args):
            institution_code = args[i+1]; i += 2
        elif args[i] == "--page" and i+1 < len(args):
            page = int(args[i+1]); i += 2
        elif args[i] == "--page-size" and i+1 < len(args):
            page_size = int(args[i+1]); i += 2
        else:
            i += 1
    if not institution_code:
        print("ERROR: --institution-code required"); sys.exit(1)
    url = f"{BASE_URL}/api/fund/nav/{institution_code}"
    resp = requests.get(url, params={"page": page, "page_size": page_size}, timeout=10)
    print(json.dumps(resp.json(), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
"""
(workspace / "skills/FTShare-fund-data/sub-skills/fund-nav-single-fund-paginated/run.py").write_text(nav_run, encoding="utf-8")

# ── Sub-skill: fund-overview-all-funds-paginated ──────────────────────────────
overview_run = """\
#!/usr/bin/env python3
import sys, requests, json, os

BASE_URL = os.environ.get("FT_BASE_URL", "https://market.ft.tech")

def main():
    page = 1
    page_size = 20
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--page" and i+1 < len(args):
            page = int(args[i+1]); i += 2
        elif args[i] == "--page-size" and i+1 < len(args):
            page_size = int(args[i+1]); i += 2
        else:
            i += 1
    url = f"{BASE_URL}/api/fund/overview"
    resp = requests.get(url, params={"page": page, "page_size": page_size}, timeout=10)
    print(json.dumps(resp.json(), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
"""
(workspace / "skills/FTShare-fund-data/sub-skills/fund-overview-all-funds-paginated/run.py").write_text(overview_run, encoding="utf-8")

# ── mock server script ─────────────────────────────────────────────────────────
mock_server = r"""
#!/usr/bin/env python3
\"\"\"Local mock server for FT market API.\"\"\"
from flask import Flask, jsonify, request
import json
from pathlib import Path

app = Flask(__name__)
DATA_DIR = Path("/workspace/config/mock_data")

def load(name):
    return json.loads((DATA_DIR / f"{name}.json").read_text())

@app.route("/api/fund/support-symbols")
def support_symbols():
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 10))
    if page == 1:
        return jsonify(load("symbols_page1"))
    elif page == 2:
        return jsonify(load("symbols_page2"))
    else:
        return jsonify({"total": 20, "page": page, "page_size": page_size, "data": []})

@app.route("/api/fund/basicinfo/<code>")
def basicinfo(code):
    key = f"basicinfo_{code}"
    try:
        return jsonify(load(key))
    except FileNotFoundError:
        return jsonify({"error": "not found"}), 404

@app.route("/api/fund/cal-return/<code>")
def cal_return(code):
    cal_type = request.args.get("cal_type", "1Y")
    key = f"returns_{code}_{cal_type}"
    try:
        return jsonify(load(key))
    except FileNotFoundError:
        return jsonify({"error": "not found"}), 404

@app.route("/api/fund/nav/<code>")
def nav(code):
    return jsonify({"institution_code": code, "page": 1, "data": []})

@app.route("/api/fund/overview")
def overview():
    page = int(request.args.get("page", 1))
    if page == 1:
        return jsonify(load("symbols_page1"))
    elif page == 2:
        return jsonify(load("symbols_page2"))
    return jsonify({"total": 20, "page": page, "data": []})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=18080, debug=False)
"""
(workspace / "config/mock_server.py").write_text(mock_server, encoding="utf-8")

# ── Distractor files ───────────────────────────────────────────────────────────
(workspace / "research/quarterly_reports/2024Q1/report_draft.txt").write_text(
    "Draft Q1 report - incomplete. DO NOT USE.\nFund performance TBD.", encoding="utf-8")
(workspace / "research/quarterly_reports/2024Q2/raw_data.csv").write_text(
    "fund_code,return_1y\n159619,???\n110022,???\nData not populated.", encoding="utf-8")
(workspace / "research/data_cache/stale_returns.json").write_text(
    json.dumps({"note": "STALE DATA - DO NOT USE", "159619": {"1Y": 0.999}}), encoding="utf-8")
(workspace / "logs/api_errors.log").write_text(
    "2024-10-01 ERROR: timeout on market.ft.tech\n2024-10-02 ERROR: 503 service unavailable\n",
    encoding="utf-8")
(workspace / "tools/deprecated/old_fund_fetcher.py").write_text(
    "# DEPRECATED - use run.py instead\nimport requests\nprint('This script is no longer supported')",
    encoding="utf-8")
(workspace / "config/base_config.yaml").write_text(
    "base_url: https://market.ft.tech\nversion: v1\nretry: 3\n", encoding="utf-8")
(workspace / "research/data_cache/fund_codes_guess.txt").write_text(
    "Possible codes:\n159619 or 159620?\n110022 confirmed?\nNeeds verification!", encoding="utf-8")

print("Workspace setup complete.")
print(f"Workspace: {workspace}")