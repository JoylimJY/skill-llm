import os
import json
import random

random.seed(42)

BASE = "/workspace"

# Create directory structure
dirs = [
    "assets/images",
    "assets/fonts",
    "old_prototypes",
    "design_specs",
    "data",
    "exports",
    "docs",
    "templates/basic",
    "templates/advanced",
    "meeting_notes",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# --- DISTRACTOR FILES ---

# 1. Old HTML prototype (raw HTML, NOT in axure format — a wrong format example)
with open(os.path.join(BASE, "old_prototypes", "dashboard_v1.html"), "w", encoding="utf-8") as f:
    f.write("""<!DOCTYPE html>
<html>
<head><title>Old Dashboard</title></head>
<body>
<h1>Sales Dashboard</h1>
<p>This is the old prototype. Not compatible with Axure inline frames.</p>
<div id="chart" style="width:600px;height:400px;"></div>
</body>
</html>
""")

# 2. Outdated JS file with wrong format
with open(os.path.join(BASE, "old_prototypes", "dashboard_v2.js"), "w", encoding="utf-8") as f:
    f.write("""// Old attempt - wrong format, do not use
data:text/html,<!DOCTYPE html><html><body><h1>Dashboard v2</h1></body></html>
""")

# 3. Design spec PDF placeholder
with open(os.path.join(BASE, "design_specs", "ui_spec_v3.txt"), "w", encoding="utf-8") as f:
    f.write("""UI Specification v3.0
Date: 2026-01-15

Color Palette:
- Primary: #1890ff
- Background: #f0f2f5
- Text: #333333

Note: This spec is outdated. New dark theme required for the sales dashboard.
Font: PingFang SC (fallback: Microsoft YaHei)
""")

# 4. Sales data JSON (the agent might use this for reference data)
sales_data = {
    "monthly_sales": {
        "labels": ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"],
        "values": [4200, 3800, 5100, 4700, 6200, 5900, 7100, 6800, 8200, 7500, 9100, 10200],
        "unit": "万元"
    },
    "user_growth": {
        "labels": ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"],
        "values": [1200, 1450, 1800, 2100, 2600, 3100, 3800, 4500, 5200, 6100, 7200, 8900],
        "unit": "人"
    },
    "summary": {
        "total_revenue": "7,285万元",
        "revenue_growth": "+23.5%",
        "total_users": "8,900",
        "user_growth": "+641.7%",
        "avg_deal_size": "¥128,500",
        "deal_growth": "+8.2%",
        "churn_rate": "3.2%",
        "churn_change": "-0.8%"
    }
}
with open(os.path.join(BASE, "data", "sales_2026.json"), "w", encoding="utf-8") as f:
    json.dump(sales_data, f, ensure_ascii=False, indent=2)

# 5. Meeting notes (distractor with requirements scattered in)
with open(os.path.join(BASE, "meeting_notes", "product_sync_2026_03_20.md"), "w", encoding="utf-8") as f:
    f.write("""# Product Sync Meeting Notes - 2026/03/20

Attendees: PM Wang, Designer Li, Dev Zhang

## Action Items

1. Need Axure prototype for client demo (URGENT - demo is in 2 days!)
2. Dashboard must show:
   - Monthly revenue bar chart (柱状图) for all 12 months of 2026
   - User growth line chart (折线图) for same period
   - Summary cards at top: total revenue, user count, avg deal size, churn rate
3. Dark theme preferred (client likes the "big screen" look)
4. Must work in Axure inline frame
5. Chinese labels throughout
6. Color convention: gains/positives should be RED (Chinese stock market convention)
   - revenue_growth +23.5% → RED
   - deal_growth +8.2% → RED  
   - churn_change -0.8% → GREEN (improvement)
   - user_growth +641.7% → RED

## Blockers
- Old HTML prototypes don't load in Axure inline frames (wrong format!)
- Need to figure out correct Axure-compatible code format

## Next Steps
- Generate new prototype file: sales_dashboard.js
- Place in /workspace/exports/ or root, doesn't matter
- Due: TOMORROW
""")

# 6. Axure version info (distractor)
with open(os.path.join(BASE, "docs", "axure_version.txt"), "w", encoding="utf-8") as f:
    f.write("""Axure RP 11.0.0.4442
License: Enterprise
User: product_team@company.com

Inline Frame Notes:
- Supports JavaScript: URLs
- Max code length: ~32000 characters
- Use "Link to URL" > JavaScript tab
""")

# 7. Template examples (basic, wrong format)
with open(os.path.join(BASE, "templates", "basic", "login.txt"), "w", encoding="utf-8") as f:
    f.write("""Basic login template - text description only
Fields: username, password, remember me checkbox, login button
Style: white background, blue button
""")

with open(os.path.join(BASE, "templates", "advanced", "echarts_notes.txt"), "w", encoding="utf-8") as f:
    f.write("""ECharts Integration Notes:
- CDN: https://cdn.jsdelivr.net/npm/echarts/dist/echarts.min.js
- Initialize: var chart = echarts.init(document.getElementById('chartId'));
- setOption({series:[{type:'bar',...}]})
- For line chart: type:'line'
- Remember to set chart container size before init
""")

# 8. Font assets placeholder
with open(os.path.join(BASE, "assets", "fonts", "README_fonts.txt"), "w", encoding="utf-8") as f:
    f.write("Font assets directory. For web use CSS font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;\n")

# 9. Color reference sheet
with open(os.path.join(BASE, "design_specs", "color_reference.json"), "w", encoding="utf-8") as f:
    json.dump({
        "dark_theme": {
            "background": "#0a1f3d",
            "card_bg": "#0d2137",
            "border": "#1e3a5f",
            "text_primary": "#e8f4fd",
            "text_secondary": "#8baac5"
        },
        "chinese_stock_colors": {
            "gain_up": "#ff4d4f",
            "loss_down": "#52c41a",
            "neutral": "#faad14"
        },
        "chart_colors": ["#00d4ff", "#52c41a", "#faad14", "#ff4d4f", "#722ed1"]
    }, f, ensure_ascii=False, indent=2)

# 10. Old exports directory with wrong format file
with open(os.path.join(BASE, "exports", "PLACEHOLDER.txt"), "w", encoding="utf-8") as f:
    f.write("Place generated Axure prototype files here.\n")

# 11. Requirements doc - the main task spec (messy, product-manager style)
with open(os.path.join(BASE, "requirements.md"), "w", encoding="utf-8") as f:
    f.write("""# Sales Dashboard Prototype Requirements

**Priority: URGENT**
**Owner: PM Wang**
**Due: Tomorrow**

## Background
Our team needs an interactive prototype for the client demo. We tried making HTML files 
but they don't load properly in Axure's inline frames. Someone told me there's a special 
JavaScript format that works — please figure it out and generate the correct file.

## What We Need
Generate a file called `sales_dashboard.js` that contains a complete, 
interactive sales analytics dashboard prototype.

### Content Requirements

**Top Summary Cards (4 cards):**
- 年度总收入 (Total Annual Revenue): 7,285万元, growth +23.5%
- 总用户数 (Total Users): 8,900人, growth +641.7%  
- 平均客单价 (Avg Deal Size): ¥128,500, growth +8.2%
- 客户流失率 (Churn Rate): 3.2%, change -0.8%

**Charts Section:**
- 月度销售额柱状图 (Monthly Sales Bar Chart) - 12 months of data
- 用户增长趋势折线图 (User Growth Line Chart) - 12 months of data
- Use ECharts library for the charts

**Style Requirements:**
- Dark theme (deep navy/dark background - big screen style)
- Chinese labels throughout
- For growth indicators: use RED for positive growth (Chinese convention), GREEN for improvements on negative metrics (like churn reduction)
- Font: Microsoft YaHei

## Technical Notes
- The old HTML files in old_prototypes/ don't work in Axure
- The output file must work when pasted into Axure's inline frame "Link to URL" field
- Data reference: see data/sales_2026.json

## Deliverable
File: `sales_dashboard.js`
""")

print("Workspace initialized successfully.")
print(f"Files created in {BASE}")