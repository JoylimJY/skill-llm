import os
import json
import stat
from pathlib import Path

WORKSPACE = os.environ.get("WORKSPACE", "/workspace")
Path(WORKSPACE).mkdir(parents=True, exist_ok=True)

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "skills/FTShare-cb-data/sub-skills/cb-lists",
    "skills/FTShare-cb-data/sub-skills/cb-base-data",
    "skills/FTShare-cb-data/sub-skills/cb-candlesticks",
    "skills/FTShare-cb-data/sub-skills/get-nth-trade-date",
    "research/fixed_income/notes",
    "research/equities/drafts",
    "data/raw/bonds",
    "data/processed",
    "config",
    "logs",
    "tmp/scratch",
]
for d in dirs:
    Path(WORKSPACE, d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
distractor_files = {
    "research/fixed_income/notes/meeting_notes_2024.txt": "Q3 review: review convertible bond premiums, check 113050 and 127043.\n",
    "research/fixed_income/notes/watchlist.csv": "symbol,name\n110070,海尔转债\n113050,南航转债\n127043,赣锋转债\n",
    "research/equities/drafts/sector_rotation.md": "# Sector Rotation Notes\nFocus on EV and semiconductor sectors for Q4.\n",
    "data/raw/bonds/stale_prices_2023.csv": "date,code,close\n2023-12-29,110070.SH,102.5\n2023-12-29,113050.SH,98.3\n",
    "data/processed/README_DO_NOT_USE.txt": "Old pipeline output. Do not use these files for production.\n",
    "config/api_config_OLD.yaml": "base_url: https://old-market.ft.tech\ntimeout: 30\n",
    "config/symbols_mapping.json": json.dumps({
        "110070": {"exchange": "SH", "name": "海尔转债"},
        "113050": {"exchange": "SH", "name": "南航转债"},
    }, ensure_ascii=False, indent=2),
    "logs/pipeline_run_20241201.log": "[INFO] Fetched 342 bonds. Duration: 1.2s\n[WARN] Symbol 127043.SZ not found in cache\n",
    "logs/pipeline_run_20241202.log": "[INFO] Fetched 341 bonds. Duration 0.9s\n",
    "tmp/scratch/temp_query.py": "# scratch: test cb-base-data call\nprint('symbol: 110070.SH')\n",
    "tmp/scratch/ideas.txt": "Try: cb-candlesticks for 海尔转债, use XSHG suffix?\n",
}
for rel_path, content in distractor_files.items():
    fp = Path(WORKSPACE, rel_path)
    fp.write_text(content, encoding="utf-8")

# ── SKILL.md ─────────────────────────────────────────────────────────────────
skill_md = """\
---
name: FTShare-cb-data
description: A 股可转债数据技能集（market.ft.tech）。覆盖可转债全量列表、单只可转债基础信息（转股价、转股价值、到期日、发行规模等）、单标的历史 K 线（支持可转债）。用户询问可转债列表、某只转债详情、转股价/转股价值、转债 K 线/历史行情时使用。
---

# FT 可转债数据 Skills

本 skill 是 `FTShare-cb-data` 的**统一路由入口**。

根据用户问题，从下方「能力总览」或「询问方式与子 skill 对应表」匹配对应子 skill，然后通过 `run.py` 执行并解析响应。

> 所有接口均以 `https://market.ft.tech` 为基础域名，本技能集子 skill 无需额外请求头。

---

## 调用方式（唯一规则）

`run.py` 与本文件（`SKILL.md`）位于同一目录。执行时：

1. 取本文件的绝对路径，将末尾 `/SKILL.md` 替换为 `/run.py`，得到 `<RUN_PY>` 。
2. 调用：`python <RUN_PY> <子skill名> [参数...]`

```bash
# 示例（<RUN_PY> 为实际绝对路径）
python <RUN_PY> cb-lists
python <RUN_PY> cb-base-data --symbol_code 110070.SH
python <RUN_PY> cb-candlesticks --symbol 110070.XSHG --interval-unit Day --since-ts-millis 1767225600000 --until-ts-millis 1780272000000 --limit 10
python <RUN_PY> get-nth-trade-date --n 5
```

> `run.py` 内部通过 `__file__` 自定位，无论安装在何处都能正确找到各子 skill 的脚本。

---

## 可转债 — 询问方式与子 skill 对应表

| 询问方式（用户常说的词） | 子 skill |
|------------------------|----------|
| **可转债列表**、**全部可转债**、**转债代码列表**、**有哪些可转债**、可转债标的 | `cb-lists` |
| **某只可转债基础信息**、**转债详情**、**110070 转债**、**转股价/转股价值**、到期日、发行规模 | `cb-base-data` |
| **可转债 K 线**、**转债日线/周线/分钟线**、**转债历史行情**、**单标的历史 K 线**（支持转债） | `cb-candlesticks` |
| **前 N 个交易日**、**近 N 天交易日**、**往前推 N 个交易日**（查近几天 K 线时先调此接口再转时间戳） | `get-nth-trade-date` |

---

## 能力总览

- **`get-nth-trade-date`**：获取当前日期的前 N 个交易日。必填：`--n`（≥1）。查「近 N 天」K 线时先调本接口得到 `nth_trade_date`，再按东八区转为毫秒时间戳用于 K 线接口。
- **`cb-lists`**：获取可转债全量列表（全称、债券代码、正股代码、交易所）。无参数；数据为前一交易日。
- **`cb-base-data`**：查询单只可转债基础信息（简称、全称、正股代码、转股价、转股价值、转股溢价率、起息日/到期日、发行规模等，数据为前一交易日）。必填：`--symbol_code`（转债代码，可带交易所后缀如 110070.SH）。
- **`cb-candlesticks`**：查询单标的历史 K 线（**支持可转债**及 A 股）。必填：`--symbol`（带交易所后缀，如 110070.XSHG）、`--interval-unit`（Minute/Minute5/Day/Week/Month/Year）、`--since-ts-millis`、`--until-ts-millis`；可选：`--interval-value`、`--limit`、`--adjust-kind`（null/Forward/Backward）。

---

## 使用流程

1. **记录本文件绝对路径**，将 `/SKILL.md` 替换为 `/run.py` 得到 `<RUN_PY>`。
2. **理解用户意图**，从「询问方式与子 skill 对应表」或「能力总览」匹配子 skill 名称。
3. （可选）读取 `sub-skills/<子skill名>/SKILL.md` 了解接口与参数。
4. **执行**：`python <RUN_PY> <子skill名> [参数...]`，获取 JSON 输出。
5. **解析并输出**：以表格或要点形式展示给用户。
"""
Path(WORKSPACE, "skills/FTShare-cb-data/SKILL.md").write_text(skill_md, encoding="utf-8")

# ── Mock server script (run.py stand-in) — written as a CLI dispatcher ──────
# This run.py mocks the remote API calls locally.
run_py = r"""#!/usr/bin/env python3
"""
run_py += '''
import sys
import json
import argparse
import os
import requests

MOCK_BASE = os.environ.get("FT_MOCK_BASE", "http://127.0.0.1:19527")

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No sub-skill specified"}))
        sys.exit(1)

    sub_skill = sys.argv[1]
    rest = sys.argv[2:]

    if sub_skill == "cb-lists":
        r = requests.get(f"{MOCK_BASE}/cb-lists")
        print(r.text)

    elif sub_skill == "cb-base-data":
        p = argparse.ArgumentParser()
        p.add_argument("--symbol_code", required=True)
        args = p.parse_args(rest)
        r = requests.get(f"{MOCK_BASE}/cb-base-data", params={"symbol_code": args.symbol_code})
        print(r.text)

    elif sub_skill == "cb-candlesticks":
        p = argparse.ArgumentParser()
        p.add_argument("--symbol", required=True)
        p.add_argument("--interval-unit", required=True)
        p.add_argument("--since-ts-millis", required=True, type=int)
        p.add_argument("--until-ts-millis", required=True, type=int)
        p.add_argument("--interval-value", default=1, type=int)
        p.add_argument("--limit", default=None, type=int)
        p.add_argument("--adjust-kind", default="null")
        args = p.parse_args(rest)
        params = {
            "symbol": args.symbol,
            "interval_unit": args.interval_unit,
            "since_ts_millis": args.since_ts_millis,
            "until_ts_millis": args.until_ts_millis,
        }
        if args.limit:
            params["limit"] = args.limit
        r = requests.get(f"{MOCK_BASE}/cb-candlesticks", params=params)
        print(r.text)

    elif sub_skill == "get-nth-trade-date":
        p = argparse.ArgumentParser()
        p.add_argument("--n", required=True, type=int)
        args = p.parse_args(rest)
        r = requests.get(f"{MOCK_BASE}/get-nth-trade-date", params={"n": args.n})
        print(r.text)

    else:
        print(json.dumps({"error": f"Unknown sub-skill: {sub_skill}"}))
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

run_py_path = Path(WORKSPACE, "skills/FTShare-cb-data/run.py")
run_py_path.write_text(run_py, encoding="utf-8")
run_py_path.chmod(run_py_path.stat().st_mode | stat.S_IEXEC)

# ── Task brief (the agent's assignment) ─────────────────────────────────────
task_brief = """\
Task: Convertible Bond Research Report

You are a fixed-income analyst at a quantitative hedge fund.

Your task is to produce a machine-readable research snapshot for the convertible bond 海尔转债 (bond code: 110070).

Specifically, you must:

1. Confirm that 海尔转债 (110070) appears in today's full convertible bond market list.
2. Retrieve its complete fundamental data: short name, full name, underlying stock code, conversion price, 
   conversion value, conversion premium rate, value date, maturity date, and issuance scale.
3. Retrieve its daily candlestick (K-line) data for the most recent 20 trading days.
4. Write all findings into a single JSON file named cb_analysis_report.json, structured as follows:
   {
     "bond_code": "110070",
     "in_market_list": true/false,
     "fundamentals": { ... all fields from cb-base-data ... },
     "candlesticks": [ ... array of daily K-line records ... ]
   }

The SKILL.md for the relevant toolset is located at:
  /workspace/skills/FTShare-cb-data/SKILL.md

Use only the tools described there. Save cb_analysis_report.json anywhere in /workspace.
"""
Path(WORKSPACE, "TASK.md").write_text(task_brief, encoding="utf-8")

print("Workspace generated successfully.")
print(f"Root: {WORKSPACE}")