import os
import json
import random

random.seed(42)

workspace = "/workspace"

# Create deeply nested directory structure with distractor files
dirs = [
    "docs/archive/2024",
    "docs/archive/2023",
    "docs/reports/quarterly",
    "docs/reports/weekly",
    "scripts/legacy",
    "scripts/utils",
    "data/raw/market",
    "data/processed",
    "config/prod",
    "config/dev",
    "logs/system",
    "logs/errors",
    "tmp/cache",
    "output/old_results",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files (10+) ---

# 1. Old stock selection results (distractor)
with open(os.path.join(workspace, "output/old_results/选股结果_20240101_120000.xlsx"), "w") as f:
    f.write("placeholder_old_excel")

# 2. Unrelated market report
with open(os.path.join(workspace, "docs/reports/quarterly/Q3_market_overview.txt"), "w") as f:
    f.write("Q3 市场综述：整体市场波动，蓝筹股表现稳健，科技股有所回调。宏观经济数据显示GDP增速放缓。")

# 3. Distractor config
with open(os.path.join(workspace, "config/prod/db_config.json"), "w") as f:
    json.dump({"host": "localhost", "port": 5432, "db": "stocks"}, f)

# 4. Old weekly report
with open(os.path.join(workspace, "docs/reports/weekly/week_42_summary.md"), "w") as f:
    f.write("# Week 42 Summary\n消费板块走强，食品饮料涨幅居前。医药板块分化明显。")

# 5. Distractor Python script (unrelated)
with open(os.path.join(workspace, "scripts/legacy/old_scraper.py"), "w") as f:
    f.write("# Legacy scraper - deprecated\nimport requests\n# Not in use\n")

# 6. Distractor log file
with open(os.path.join(workspace, "logs/system/system_2024.log"), "w") as f:
    f.write("2024-01-01 INFO: System started\n2024-01-02 ERROR: Connection timeout\n")

# 7. Another distractor config
with open(os.path.join(workspace, "config/dev/test_settings.yaml"), "w") as f:
    f.write("debug: true\nverbose: false\nmax_retries: 3\n")

# 8. Old data file
with open(os.path.join(workspace, "data/raw/market/stocks_20230601.csv"), "w") as f:
    f.write("code,name,price\n600519,贵州茅台,1800\n000858,五粮液,160\n")

# 9. Distractor processed data
with open(os.path.join(workspace, "data/processed/normalized_indices.json"), "w") as f:
    json.dump({"shanghai": 3200, "shenzhen": 11000, "chinext": 2100}, f)

# 10. Archive doc
with open(os.path.join(workspace, "docs/archive/2023/annual_review.txt"), "w") as f:
    f.write("2023年度回顾：新能源汽车渗透率突破30%，光伏装机量创历史新高，储能市场快速扩张。")

# 11. Distractor notes
with open(os.path.join(workspace, "docs/archive/2024/notes.txt"), "w") as f:
    f.write("待办：整理行业研究报告，更新选股模型参数。")

# 12. Legacy utils
with open(os.path.join(workspace, "scripts/utils/date_helper.py"), "w") as f:
    f.write("from datetime import datetime\ndef now_str():\n    return datetime.now().strftime('%Y%m%d_%H%M%S')\n")

# 13. Tmp cache
with open(os.path.join(workspace, "tmp/cache/query_cache.json"), "w") as f:
    json.dump({"last_query": "光伏概念股票", "timestamp": "2024-03-01"}, f)

# --- THE ACTUAL TASK INPUT ---
# A realistic policy news article about EV charging infrastructure
news_article = """
【政策快讯】国家发改委、工信部联合发布《新能源汽车充电基础设施建设提速行动方案（2025-2027）》

核心内容：
1. 到2027年，全国公共充电桩数量达到1000万个，较现有规模翻倍扩张；
2. 高速公路服务区充电设施覆盖率达到100%，城市核心商圈5公里内充电桩密度大幅提升；
3. 国家财政设立500亿元专项补贴基金，重点支持充电模块、液冷超充技术研发及产线建设；
4. 推动充电运营商接入统一国家平台，鼓励"光储充一体化"示范项目建设；
5. 鼓励电网侧配套升级，支持大功率充电场景下的配电网增容和智能调度系统部署；
6. 要求各地加快充电桩用地审批绿色通道，降低充电运营企业运营成本。

市场影响分析：
本次政策超预期，充电桩全产业链将直接受益。充电桩核心零部件（功率模块、充电枪、液冷散热）需求暴增，
充电运营商（运营平台、APP、结算系统）迎来流量红利，电力设备（变压器、配电柜）配套需求大幅拉升，
同时光伏+储能配套成为标配，储能电池、逆变器、EMS系统需求联动增长。
"""

news_file_path = os.path.join(workspace, "policy_news.txt")
with open(news_file_path, "w", encoding="utf-8") as f:
    f.write(news_article)

# --- generate_stock_excel.py (the proprietary script agents must use) ---
# This script is described in SKILL.md as already existing in workspace
generate_excel_script = '''#!/usr/bin/env python3
"""
generate_stock_excel.py - i问财选股结果Excel生成器
根据SKILL.md规范，将选股结果生成Excel文件
每个核心方向一个Sheet，文件名格式: 选股结果_YYYYMMDD_HHMMSS.xlsx
"""
import sys
import json
import os
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

def generate_stock_excel(data: dict, output_dir: str = None) -> str:
    """
    生成选股结果Excel文件
    
    Args:
        data: dict格式，key为方向名称，value为股票列表
              每个股票为dict，包含从i问财获取的字段
        output_dir: 输出目录，默认为当前目录
    
    Returns:
        生成的Excel文件路径
    """
    if output_dir is None:
        output_dir = os.getcwd()
    
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"选股结果_{timestamp}.xlsx"
    filepath = os.path.join(output_dir, filename)
    
    wb = openpyxl.Workbook()
    # Remove default sheet
    if "Sheet" in wb.sheetnames:
        del wb["Sheet"]
    
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    
    directions = list(data.items())
    # SKILL.md: 最多5个Sheet
    if len(directions) > 5:
        directions = directions[:5]
    
    for direction_name, stocks in directions:
        # Sheet名最多31字符
        sheet_name = direction_name[:31] if direction_name else "未知方向"
        ws = wb.create_sheet(title=sheet_name)
        
        if not stocks:
            ws.append(["暂无数据"])
            continue
        
        # SKILL.md: 列为i问财返回的原始字段名
        all_keys = []
        for stock in stocks:
            for k in stock.keys():
                if k not in all_keys:
                    all_keys.append(k)
        
        # Write header
        for col_idx, key in enumerate(all_keys, 1):
            cell = ws.cell(row=1, column=col_idx, value=key)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")
        
        # SKILL.md: 每个方向最多5只股票
        for row_idx, stock in enumerate(stocks[:5], 2):
            for col_idx, key in enumerate(all_keys, 1):
                ws.cell(row=row_idx, column=col_idx, value=stock.get(key, ""))
        
        # Auto-adjust column widths
        for col_idx in range(1, len(all_keys) + 1):
            ws.column_dimensions[get_column_letter(col_idx)].width = 15
    
    wb.save(filepath)
    print(f"Excel文件已生成: {filepath}")
    return filepath


if __name__ == "__main__":
    # CLI usage: python generate_stock_excel.py <json_data_file> [output_dir]
    if len(sys.argv) < 2:
        print("Usage: python generate_stock_excel.py <json_data_file> [output_dir]")
        print("")
        print("json_data_file format:")
        print(\'  {"方向名称1": [{"代码":"600000","名称":"浦发银行",...}, ...], "方向名称2": [...]}\')
        sys.exit(1)
    
    json_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()
    
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    result_path = generate_stock_excel(data, output_dir)
    print(f"成功生成: {result_path}")
'''

with open(os.path.join(workspace, "generate_stock_excel.py"), "w", encoding="utf-8") as f:
    f.write(generate_excel_script)

os.chmod(os.path.join(workspace, "generate_stock_excel.py"), 0o755)

print("Workspace generated successfully.")
print(f"Task input file: {news_file_path}")
print(f"generate_stock_excel.py created at: {os.path.join(workspace, 'generate_stock_excel.py')}")