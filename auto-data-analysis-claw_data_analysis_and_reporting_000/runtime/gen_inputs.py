import os
import random
import json
import csv
import numpy as np
from pathlib import Path

random.seed(42)
np.random.seed(42)

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))

# --- Directory structure ---
dirs = [
    "data/raw", "data/processed", "data/archive",
    "scripts", "references", "reports",
    "config/templates", "config/old",
    "logs", "notebooks",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "logs/pipeline_run_2024Q3.log": "INFO 2024-09-01 Pipeline completed successfully.\nWARN 2024-09-02 Missing 3 records in region=North.\n",
    "config/old/kpi_v1.json": '{"kpis": [{"name": "revenue", "formula": "total(revenue)"}]}',  # wrong formula syntax
    "config/old/report_draft.json": '{"title": "Draft", "body": "placeholder"}',
    "notebooks/exploration_scratch.py": "# scratch\nimport pandas as pd\ndf = pd.read_csv('../data/raw/sales.csv')\nprint(df.head())\n",
    "data/archive/sales_2023Q4.csv": "date,store,revenue\n2023-10-01,Downtown,50000\n2023-11-01,Uptown,45000\n",
    "data/archive/README_old.txt": "This folder contains archived data from 2023. Do not modify.",
    "config/templates/generic_report.html": "<html><body><h1>{{title}}</h1></body></html>",
    "references/industry_benchmarks.txt": "Coffee industry avg gross margin: 65%\nTarget customer acquisition cost: $12\n",
    "logs/cleanup_notes.txt": "Removed 142 duplicate entries from Q2 data on 2024-07-15.\n",
    "data/processed/.gitkeep": "",
    "reports/.gitkeep": "",
}
for path, content in distractor_files.items():
    (WORKSPACE / path).write_text(content)

# --- Generate MESSY sales data CSV ---
stores = ["Downtown", "Uptown", "Airport", "Mall", "Suburb"]
products = ["Espresso", "Latte", "Cappuccino", "Cold Brew", "Matcha"]
months = [f"2024-{m:02d}-01" for m in range(1, 13)]

rows = []
order_id = 1000
for month in months:
    for store in stores:
        for product in products:
            # Normal records
            revenue = round(random.uniform(8000, 30000), 2)
            units = random.randint(200, 900)
            cost = round(revenue * random.uniform(0.28, 0.42), 2)
            gross_margin_pct = round((revenue - cost) / revenue * 100, 2)
            rows.append({
                "order_id": f"ORD-{order_id}",
                "date": month,
                "store": store,
                "product": product,
                "revenue": revenue,
                "units_sold": units,
                "cost": cost,
                "gross_margin_pct": gross_margin_pct,
                "region": "North" if store in ["Downtown", "Uptown"] else "South",
                "customer_segment": random.choice(["Regular", "Premium", "Occasional"]),
            })
            order_id += 1

# Inject messiness: nulls, blanks, outliers
# 1. Some revenue values set to None
for i in random.sample(range(len(rows)), 18):
    rows[i]["revenue"] = ""

# 2. Some gross_margin_pct set to None
for i in random.sample(range(len(rows)), 12):
    rows[i]["gross_margin_pct"] = ""

# 3. One fully-null store entry
rows.append({
    "order_id": "", "date": "", "store": "", "product": "",
    "revenue": "", "units_sold": "", "cost": "", "gross_margin_pct": "",
    "region": "", "customer_segment": ""
})

# 4. Outlier: one crazy high revenue
rows[5]["revenue"] = 9999999.99

# 5. Duplicate rows
rows.extend(rows[10:13])

# Shuffle
random.shuffle(rows)

fieldnames = ["order_id", "date", "store", "product", "revenue",
              "units_sold", "cost", "gross_margin_pct", "region", "customer_segment"]

sales_csv = WORKSPACE / "data/raw/coffee_sales_2024.csv"
with open(sales_csv, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated messy CSV with {len(rows)} rows at {sales_csv}")

# --- Write the actual working scripts ---

# scripts/analyze.py
analyze_script = r'''#!/usr/bin/env python3
"""Automated Data Analysis Tool"""
import argparse
import json
import sys
import pandas as pd
import numpy as np
from pathlib import Path


def load_data(filepath):
    p = Path(filepath)
    if p.suffix == ".csv":
        df = pd.read_csv(filepath)
    elif p.suffix in [".xlsx", ".xls"]:
        df = pd.read_excel(filepath)
    else:
        raise ValueError(f"Unsupported format: {p.suffix}")
    return df


def cmd_profile(args):
    df = load_data(args.file)
    print(f"=== Data Profile: {args.file} ===")
    print(f"Rows: {len(df)}, Columns: {len(df.columns)}")
    print(f"Columns: {list(df.columns)}")
    print("\nData Types:")
    print(df.dtypes.to_string())
    print("\nNull Value Rates:")
    null_rates = (df.isnull() | (df == "")).mean()
    print(null_rates.to_string())
    print("\nNumeric Summary:")
    print(df.describe().to_string())
    print("\nProfile complete.")


def cmd_clean(args):
    df = load_data(args.file)
    original_rows = len(df)

    # Replace empty strings with NaN
    df.replace("", np.nan, inplace=True)

    # Drop fully-null columns
    before_cols = set(df.columns)
    df.dropna(axis=1, how="all", inplace=True)
    dropped_cols = before_cols - set(df.columns)
    if dropped_cols:
        print(f"Dropped fully-null columns: {dropped_cols}")

    # Fill numeric columns with median
    num_cols = df.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        median_val = df[col].median()
        df[col].fillna(median_val, inplace=True)

    # Fill categorical columns with mode
    cat_cols = df.select_dtypes(exclude=[np.number]).columns
    for col in cat_cols:
        if df[col].isnull().any():
            mode_val = df[col].mode()
            if not mode_val.empty:
                df[col].fillna(mode_val[0], inplace=True)

    cleaned_rows = len(df)
    out_path = args.o if args.o else args.file.replace(".csv", "_cleaned.csv")
    df.to_csv(out_path, index=False)
    print(f"Clean complete. Original: {original_rows} rows -> Cleaned: {cleaned_rows} rows")
    print(f"Saved to: {out_path}")


def cmd_variance(args):
    df = load_data(args.file)
    df.replace("", np.nan, inplace=True)
    print(f"=== Variance Analysis: {args.value} by {args.period} ===")
    if args.group:
        grouped = df.groupby([args.period, args.group])[args.value].sum().reset_index()
        print(grouped.to_string(index=False))
    else:
        grouped = df.groupby(args.period)[args.value].sum().reset_index()
        grouped["pct_change"] = grouped[args.value].pct_change() * 100
        print(grouped.to_string(index=False))


def cmd_trend(args):
    df = load_data(args.file)
    df.replace("", np.nan, inplace=True)
    df[args.date] = pd.to_datetime(df[args.date], errors="coerce")
    df = df.dropna(subset=[args.date])
    df = df.set_index(args.date)
    freq = args.freq if args.freq else "M"
    trend = df[args.value].resample(freq).sum()
    print(f"=== Trend Analysis: {args.value} (freq={freq}) ===")
    print(trend.to_string())


def cmd_correlate(args):
    df = load_data(args.file)
    df.replace("", np.nan, inplace=True)
    cols = args.columns
    subset = df[cols].apply(pd.to_numeric, errors="coerce")
    corr = subset.corr()
    print(f"=== Correlation Matrix: {cols} ===")
    print(corr.to_string())


def cmd_kpi(args):
    df = load_data(args.file)
    df.replace("", np.nan, inplace=True)

    # Fill numeric with median for calculation
    num_cols = df.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        df[col].fillna(df[col].median(), inplace=True)

    with open(args.config) as f:
        config = json.load(f)

    results = {}
    import re
    for kpi in config["kpis"]:
        name = kpi["name"]
        formula = kpi["formula"]
        # Parse formula: func(column)
        match = re.match(r"(\w+)\((\w+)\)", formula)
        if not match:
            print(f"WARNING: Cannot parse formula '{formula}' for KPI '{name}'")
            results[name] = None
            continue
        func_name, col_name = match.group(1), match.group(2)
        if col_name not in df.columns:
            print(f"WARNING: Column '{col_name}' not found for KPI '{name}'")
            results[name] = None
            continue
        series = pd.to_numeric(df[col_name], errors="coerce")
        if func_name == "sum":
            val = series.sum()
        elif func_name == "mean":
            val = series.mean()
        elif func_name == "count":
            val = series.count()
        elif func_name == "max":
            val = series.max()
        elif func_name == "min":
            val = series.min()
        else:
            print(f"WARNING: Unknown function '{func_name}' for KPI '{name}'")
            val = None
        results[name] = round(float(val), 4) if val is not None else None
        print(f"KPI [{name}]: {results[name]}")

    out_path = args.o if hasattr(args, "o") and args.o else "kpi_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"KPI results saved to: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Data Analysis Tool")
    subparsers = parser.add_subparsers(dest="command")

    # profile
    p_profile = subparsers.add_parser("profile")
    p_profile.add_argument("file")

    # clean
    p_clean = subparsers.add_parser("clean")
    p_clean.add_argument("file")
    p_clean.add_argument("-o", default=None)

    # variance
    p_var = subparsers.add_parser("variance")
    p_var.add_argument("file")
    p_var.add_argument("--value", required=True)
    p_var.add_argument("--period", required=True)
    p_var.add_argument("--group", default=None)

    # trend
    p_trend = subparsers.add_parser("trend")
    p_trend.add_argument("file")
    p_trend.add_argument("--date", required=True)
    p_trend.add_argument("--value", required=True)
    p_trend.add_argument("--freq", default="M")

    # correlate
    p_corr = subparsers.add_parser("correlate")
    p_corr.add_argument("file")
    p_corr.add_argument("--columns", nargs="+", required=True)

    # kpi
    p_kpi = subparsers.add_parser("kpi")
    p_kpi.add_argument("file")
    p_kpi.add_argument("--config", required=True)
    p_kpi.add_argument("-o", default=None)

    args = parser.parse_args()

    cmd_map = {
        "profile": cmd_profile,
        "clean": cmd_clean,
        "variance": cmd_variance,
        "trend": cmd_trend,
        "correlate": cmd_correlate,
        "kpi": cmd_kpi,
    }

    if args.command in cmd_map:
        cmd_map[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
'''

(WORKSPACE / "scripts/analyze.py").write_text(analyze_script)

# scripts/report_generator.py
report_gen_script = r'''#!/usr/bin/env python3
"""Professional Report Generator"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime


def render_markdown(config):
    lines = []
    title = config.get("title", "Report")
    meta = config.get("metadata", {})
    period = meta.get("period", "")
    author = meta.get("author", "")
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines.append(f"# {title}")
    lines.append("")
    if period:
        lines.append(f"**分析周期**: {period}")
    if author:
        lines.append(f"**作者**: {author}")
    lines.append(f"**生成时间**: {generated}")
    lines.append("")
    lines.append("---")
    lines.append("")

    sections = config.get("sections", [])
    for section in sections:
        sec_title = section.get("title", "Section")
        content = section.get("content", "")
        insight = section.get("insight", "")

        lines.append(f"## {sec_title}")
        lines.append("")

        if isinstance(content, dict):
            # KPI table format
            lines.append("| 指标 | 数值 |")
            lines.append("|------|------|")
            for kpi_name, kpi_data in content.items():
                val = kpi_data.get("value", "") if isinstance(kpi_data, dict) else str(kpi_data)
                lines.append(f"| {kpi_name} | {val} |")
        else:
            lines.append(str(content))

        lines.append("")
        if insight:
            lines.append(f"> **洞察**: {insight}")
            lines.append("")

    return "\n".join(lines)


def render_html(config):
    md = render_markdown(config)
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>{config.get('title','Report')}</title></head>
<body>
<pre>{md}</pre>
</body>
</html>"""
    return html


def main():
    parser = argparse.ArgumentParser(description="Report Generator")
    parser.add_argument("config", help="Path to report config JSON")
    parser.add_argument("-o", required=True, help="Output file path")
    parser.add_argument("--format", choices=["markdown", "html"], default="markdown")
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)

    if args.format == "markdown":
        output = render_markdown(config)
    else:
        output = render_html(config)

    Path(args.o).parent.mkdir(parents=True, exist_ok=True)
    with open(args.o, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"Report generated: {args.o} (format={args.format})")


if __name__ == "__main__":
    main()
'''

(WORKSPACE / "scripts/report_generator.py").write_text(report_gen_script)

# references/financial-metrics.md
(WORKSPACE / "references/financial-metrics.md").write_text("""# Financial Metrics Reference

## Core KPIs
- **总收入 (Total Revenue)**: sum of all revenue values
- **平均毛利率 (Avg Gross Margin %)**: mean of gross_margin_pct
- **总成本 (Total Cost)**: sum of cost
- **订单数 (Order Count)**: count of order_id

## Formulas
- Gross Margin % = (Revenue - Cost) / Revenue * 100
- YoY Growth = (Current Period - Prior Period) / Prior Period * 100
""")

# references/business-analysis-patterns.md
(WORKSPACE / "references/business-analysis-patterns.md").write_text("""# Business Analysis Patterns

## Sales Analysis
- Group by store and date to identify top performers
- Use variance analysis for period-over-period changes
- Trend analysis reveals seasonality

## KPI Hierarchy
1. Revenue metrics
2. Profitability metrics
3. Volume metrics (units sold, order count)
""")

# references/report-templates.md
(WORKSPACE / "references/report-templates.md").write_text("""# Report Templates

## Standard Report Structure
1. Executive Summary (执行摘要)
2. Core KPIs (核心KPI) - use dict content with value keys
3. Trend Analysis (趋势分析)
4. Store Performance (门店绩效)
5. Recommendations (行动建议)

## Formatting Rules
- Each section must have a title and content field
- KPI sections use dict content: {"KPI名称": {"value": "数值"}}
- Include insight field for key findings
- Use markdown format for final output
""")

print("Workspace generation complete.")
print(f"Files created in: {WORKSPACE}")