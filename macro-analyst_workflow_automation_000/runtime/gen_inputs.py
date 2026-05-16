import os
import json
import random
import textwrap
from pathlib import Path

random.seed(42)

# ── top-level workspace layout ──────────────────────────────────────────────
base = Path("/workspace")

# ── skills/akshare-finance/scripts/  (the macro_data.py & earnings.py live here)
scripts_dir = base / "skills" / "akshare-finance" / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

# ── workspace-trading/skills/trading-quant/scripts/  (quant.py lives here)
quant_dir = base / "workspace-trading" / "skills" / "trading-quant" / "scripts"
quant_dir.mkdir(parents=True, exist_ok=True)

# ── distractor directories & files ──────────────────────────────────────────
distractors = [
    base / "skills" / "akshare-finance" / "data" / "cache" / "gdp_raw.csv",
    base / "skills" / "akshare-finance" / "data" / "cache" / "cpi_raw.csv",
    base / "skills" / "akshare-finance" / "config" / "settings.yaml",
    base / "workspace-trading" / "skills" / "trading-quant" / "config" / "quant_config.json",
    base / "workspace-trading" / "data" / "historical" / "index_returns.csv",
    base / "workspace-trading" / "data" / "historical" / "sector_weights.csv",
    base / "reports" / "archive" / "2024_q1_macro.txt",
    base / "reports" / "archive" / "2024_q2_macro.txt",
    base / "reports" / "templates" / "old_template.json",
    base / "logs" / "agent_run_20250101.log",
    base / "logs" / "agent_run_20250201.log",
    base / "tmp" / "scratch.py",
]
for p in distractors:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"# distractor file: {p.name}\n# auto-generated, not relevant\n")

# ── SKILL.md (entry point) ──────────────────────────────────────────────────
skill_md = base / "skills" / "akshare-finance" / "SKILL.md"
skill_md.parent.mkdir(parents=True, exist_ok=True)
skill_md.write_text(textwrap.dedent("""\
---
name: macro-analyst
description: 宏观经济分析工具集 - 基于AKShare的GDP/CPI/PMI/利率/汇率数据
keywords:
  - 宏观
  - GDP
  - CPI
  - PMI
  - 利率
  - 汇率
---

# Macro Analyst — 宏观经济分析

## 数据获取

### 中国宏观
```bash
PYTHON=python3.12
SCRIPT=skills/akshare-finance/scripts/macro_data.py

# GDP (季度)
$PYTHON $SCRIPT gdp

# CPI (月度)
$PYTHON $SCRIPT cpi

# PMI (月度)
$PYTHON $SCRIPT pmi

# M2货币供应 (月度)
$PYTHON $SCRIPT m2
```

### 个股财报 (行业聚合分析用)
```bash
$PYTHON skills/akshare-finance/scripts/earnings.py report 600519
$PYTHON skills/akshare-finance/scripts/earnings.py earnings
$PYTHON skills/akshare-finance/scripts/earnings.py industry
```

### 全球市场
```bash
# 全球市场概览 (via quant.py)
$PYTHON workspace-trading/skills/trading-quant/scripts/quant.py global_overview
```

### 汇率
```python
# 使用 akshare 直接调用
import akshare as ak
ak.currency_boc_sina()  # 中国银行汇率
```

## 分析框架

### 宏观日报流程
1. 获取 global_overview → 全球市场概况
2. 获取 GDP/CPI/PMI → 经济趋势判断
3. 检查 earnings → 季度业绩预告趋势
4. 综合分析 → 宏观展望

### 宏观周报流程
1. 本周全球市场回顾 (global_overview)
2. 宏观数据对比 (GDP/CPI/PMI 趋势)
3. 行业轮动分析 (industry)
4. 下周展望与风险提示

## 与其他 Agent 的协作
- 个股深度分析 → 交给 trading
- AI 行业趋势 → 交给 ainews
- Macro 关注: 政策影响、经济周期、行业估值
"""))

# ── macro_data.py ────────────────────────────────────────────────────────────
macro_data_py = scripts_dir / "macro_data.py"
macro_data_py.write_text(textwrap.dedent("""\
#!/usr/bin/env python3.12
\"\"\"Macro data fetcher using AKShare.\"\"\"
import sys
import json
import akshare as ak
import pandas as pd

def get_gdp():
    try:
        df = ak.macro_china_gdp()
        if df is None or df.empty:
            raise ValueError("empty")
        recent = df.tail(4)
        rows = recent.to_dict(orient="records")
        result = {"indicator": "GDP", "unit": "亿元", "frequency": "季度", "recent": rows}
    except Exception as e:
        result = {"indicator": "GDP", "unit": "亿元", "frequency": "季度",
                  "recent": [{"季度": "2024Q3", "国内生产总值-绝对值": 314000, "note": "mock"}]}
    print(json.dumps(result, ensure_ascii=False, default=str))

def get_cpi():
    try:
        df = ak.macro_china_cpi_monthly()
        if df is None or df.empty:
            raise ValueError("empty")
        recent = df.tail(6)
        rows = recent.to_dict(orient="records")
        result = {"indicator": "CPI", "unit": "%", "frequency": "月度", "recent": rows}
    except Exception as e:
        result = {"indicator": "CPI", "unit": "%", "frequency": "月度",
                  "recent": [{"月份": "2024-10", "全国-同比": 0.3, "note": "mock"}]}
    print(json.dumps(result, ensure_ascii=False, default=str))

def get_pmi():
    try:
        df = ak.macro_china_pmi_yearly()
        if df is None or df.empty:
            raise ValueError("empty")
        recent = df.tail(6)
        rows = recent.to_dict(orient="records")
        result = {"indicator": "PMI", "unit": "指数", "frequency": "月度", "recent": rows}
    except Exception as e:
        result = {"indicator": "PMI", "unit": "指数", "frequency": "月度",
                  "recent": [{"月份": "2024-10", "制造业-指数": 50.1, "note": "mock"}]}
    print(json.dumps(result, ensure_ascii=False, default=str))

def get_m2():
    try:
        df = ak.macro_china_money_supply()
        if df is None or df.empty:
            raise ValueError("empty")
        recent = df.tail(6)
        rows = recent.to_dict(orient="records")
        result = {"indicator": "M2", "unit": "亿元", "frequency": "月度", "recent": rows}
    except Exception as e:
        result = {"indicator": "M2", "unit": "亿元", "frequency": "月度",
                  "recent": [{"月份": "2024-10", "M2-数量": 3100000, "note": "mock"}]}
    print(json.dumps(result, ensure_ascii=False, default=str))

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "gdp":
        get_gdp()
    elif cmd == "cpi":
        get_cpi()
    elif cmd == "pmi":
        get_pmi()
    elif cmd == "m2":
        get_m2()
    else:
        print(json.dumps({"error": f"unknown command: {cmd}"}))
        sys.exit(1)
"""))
macro_data_py.chmod(0o755)

# ── earnings.py ──────────────────────────────────────────────────────────────
earnings_py = scripts_dir / "earnings.py"
earnings_py.write_text(textwrap.dedent("""\
#!/usr/bin/env python3.12
\"\"\"Earnings and industry data fetcher.\"\"\"
import sys
import json
import akshare as ak
import pandas as pd

def get_report(code):
    try:
        df = ak.stock_financial_report_sina(stock=code, symbol="资产负债表")
        if df is None or df.empty:
            raise ValueError("empty")
        result = {"type": "report", "code": code, "rows": df.head(3).to_dict(orient="records")}
    except Exception as e:
        result = {"type": "report", "code": code,
                  "rows": [{"报告期": "2024-09-30", "资产总计": 500000000000, "note": "mock"}]}
    print(json.dumps(result, ensure_ascii=False, default=str))

def get_earnings():
    try:
        df = ak.stock_notice_report(symbol="预增")
        if df is None or df.empty:
            raise ValueError("empty")
        result = {"type": "earnings", "rows": df.head(5).to_dict(orient="records")}
    except Exception as e:
        result = {"type": "earnings",
                  "rows": [{"股票代码": "600519", "业绩类型": "预增", "涨幅": "30%", "note": "mock"}]}
    print(json.dumps(result, ensure_ascii=False, default=str))

def get_industry():
    try:
        df = ak.stock_sector_spot(symbol="行业板块")
        if df is None or df.empty:
            raise ValueError("empty")
        result = {"type": "industry", "rows": df.head(10).to_dict(orient="records")}
    except Exception as e:
        result = {"type": "industry",
                  "rows": [
                      {"板块名称": "新能源", "涨跌幅": "2.35%", "成交额": "450亿", "note": "mock"},
                      {"板块名称": "消费", "涨跌幅": "-0.82%", "成交额": "210亿", "note": "mock"},
                      {"板块名称": "科技", "涨跌幅": "1.10%", "成交额": "380亿", "note": "mock"},
                  ]}
    print(json.dumps(result, ensure_ascii=False, default=str))

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "report":
        code = sys.argv[2] if len(sys.argv) > 2 else "600519"
        get_report(code)
    elif cmd == "earnings":
        get_earnings()
    elif cmd == "industry":
        get_industry()
    else:
        print(json.dumps({"error": f"unknown command: {cmd}"}))
        sys.exit(1)
"""))
earnings_py.chmod(0o755)

# ── quant.py  (workspace-trading path) ───────────────────────────────────────
quant_py = quant_dir / "quant.py"
quant_py.write_text(textwrap.dedent("""\
#!/usr/bin/env python3.12
\"\"\"Quantitative tools including global market overview.\"\"\"
import sys
import json
import akshare as ak
import pandas as pd

def global_overview():
    try:
        df = ak.stock_us_spot_em()
        if df is None or df.empty:
            raise ValueError("empty")
        rows = df.head(5).to_dict(orient="records")
        result = {"type": "global_overview", "markets": rows}
    except Exception as e:
        result = {
            "type": "global_overview",
            "markets": [
                {"市场": "美国道琼斯", "最新价": 42500.0, "涨跌幅": "0.45%", "note": "mock"},
                {"市场": "纳斯达克", "最新价": 18800.0, "涨跌幅": "0.72%", "note": "mock"},
                {"市场": "欧洲斯托克50", "最新价": 4820.0, "涨跌幅": "-0.15%", "note": "mock"},
                {"市场": "日经225", "最新价": 38900.0, "涨跌幅": "1.02%", "note": "mock"},
                {"市场": "恒生指数", "最新价": 19400.0, "涨跌幅": "-0.33%", "note": "mock"},
            ]
        }
    print(json.dumps(result, ensure_ascii=False, default=str))

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "global_overview":
        global_overview()
    else:
        print(json.dumps({"error": f"unknown command: {cmd}"}))
        sys.exit(1)
"""))
quant_py.chmod(0o755)

# ── a stale/wrong template to confuse the agent ──────────────────────────────
wrong_template = base / "reports" / "templates" / "old_template.json"
wrong_template.parent.mkdir(parents=True, exist_ok=True)
wrong_template.write_text(json.dumps({
    "report_type": "daily",
    "sections": ["market_summary", "news_digest"],
    "note": "DEPRECATED — do not use for weekly reports"
}, ensure_ascii=False, indent=2))

print("Workspace generation complete.")