import os
import csv
import json
import random

random.seed(42)

workspace = "/workspace"

# --- Create realistic directory structure with distractor files ---
dirs = [
    "scripts",
    "data/raw",
    "data/processed",
    "data/archive",
    "config",
    "reports/2025",
    "reports/2024",
    "templates",
    "logs",
    "utils",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractors = {
    "config/app_config.yaml": """
timezone: Asia/Shanghai
locale: zh_CN
output_format: json
encoding: utf-8
""",
    "config/db_config.json": json.dumps({
        "host": "localhost",
        "port": 5432,
        "database": "finance_db",
        "user": "admin"
    }, indent=2, ensure_ascii=False),
    "templates/invoice_template.txt": """发票模板
日期：{date}
金额：{amount}
备注：{note}
""",
    "templates/report_header.txt": """财务报告
公司名称：某某有限公司
报告期间：{period}
制表人：{author}
""",
    "logs/app.log": """2025-01-15 09:00:01 INFO 系统启动
2025-01-15 09:05:22 INFO 数据加载完成
2025-01-15 10:30:45 WARN 发现格式异常记录
2025-01-15 11:00:00 INFO 处理完成
""",
    "logs/error.log": """2025-01-10 14:22:33 ERROR 数据库连接失败
2025-01-12 08:15:00 ERROR 文件编码错误
""",
    "data/archive/old_transactions_2024.csv": "id,date,amount,description\n1,2024-01-10,500.00,旧记录\n2,2024-03-22,1200.00,旧记录",
    "utils/helpers.py": """# Helper utilities
def format_date(d):
    return d.strftime('%Y年%m月%d日')

def validate_amount(a):
    return float(a) > 0
""",
    "utils/constants.py": """# Constants
COMPANY_NAME = "某某科技有限公司"
FISCAL_YEAR = 2025
TAX_RATE = 0.13
""",
    "reports/2024/annual_summary.txt": "2024年度财务摘要\n总收入：12,500,000元\n总支出：9,800,000元\n净利润：2,700,000元\n",
    "reports/2025/q1_notes.txt": "2025年第一季度备注：数据待审计确认\n",
    "data/processed/.gitkeep": "",
}

for path, content in distractors.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# --- Scripts that SKILL.md says exist in workspace ---
# workday_check.py: outputs "workday" or "holiday" for a given date
workday_script = '''#!/usr/bin/env python3
"""
Check if a given date is a workday in mainland China.
Usage: python3 scripts/workday_check.py "YYYY-MM-DD"
Output: prints "workday" or "holiday"
"""
import sys
from datetime import date, datetime

# 2025-2026 China public holidays (statutory + approved makeup days)
# Format: "YYYY-MM-DD" -> "holiday" or "workday" (makeup)
HOLIDAY_OVERRIDES = {
    # 2025 holidays
    "2025-01-01": "holiday",  # 元旦
    "2025-01-28": "holiday",  # 春节
    "2025-01-29": "holiday",
    "2025-01-30": "holiday",
    "2025-01-31": "holiday",
    "2025-02-01": "holiday",
    "2025-02-02": "holiday",
    "2025-02-03": "holiday",
    "2025-02-04": "holiday",
    "2025-01-26": "workday",  # 调休补班
    "2025-02-08": "workday",  # 调休补班
    "2025-04-04": "holiday",  # 清明节
    "2025-04-05": "holiday",
    "2025-04-06": "holiday",
    "2025-05-01": "holiday",  # 劳动节
    "2025-05-02": "holiday",
    "2025-05-03": "holiday",
    "2025-05-04": "holiday",
    "2025-05-05": "holiday",
    "2025-04-27": "workday",  # 调休补班
    "2025-05-31": "holiday",  # 端午节
    "2025-06-01": "holiday",
    "2025-06-02": "holiday",
    "2025-10-01": "holiday",  # 国庆节/中秋节
    "2025-10-02": "holiday",
    "2025-10-03": "holiday",
    "2025-10-04": "holiday",
    "2025-10-05": "holiday",
    "2025-10-06": "holiday",
    "2025-10-07": "holiday",
    "2025-10-08": "holiday",
    "2025-09-28": "workday",  # 调休补班
    "2025-10-11": "workday",  # 调休补班
    # 2026 holidays
    "2026-01-01": "holiday",  # 元旦
    "2026-01-01": "holiday",
    "2026-02-17": "holiday",  # 春节
    "2026-02-18": "holiday",
    "2026-02-19": "holiday",
    "2026-02-20": "holiday",
    "2026-02-21": "holiday",
    "2026-02-22": "holiday",
    "2026-02-23": "holiday",
    "2026-02-24": "holiday",
    "2026-04-05": "holiday",  # 清明节
    "2026-04-06": "holiday",
    "2026-05-01": "holiday",  # 劳动节
    "2026-05-02": "holiday",
    "2026-05-03": "holiday",
    "2026-05-04": "holiday",
    "2026-05-05": "holiday",
    "2026-06-19": "holiday",  # 端午节
    "2026-06-20": "holiday",
    "2026-06-21": "holiday",
    "2026-10-01": "holiday",  # 国庆节
    "2026-10-02": "holiday",
    "2026-10-03": "holiday",
    "2026-10-04": "holiday",
    "2026-10-05": "holiday",
    "2026-10-06": "holiday",
    "2026-10-07": "holiday",
}

def is_workday(date_str):
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    if date_str in HOLIDAY_OVERRIDES:
        return HOLIDAY_OVERRIDES[date_str] == "workday"
    # Monday=0, Sunday=6
    return d.weekday() < 5

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: workday_check.py YYYY-MM-DD")
        sys.exit(1)
    date_str = sys.argv[1]
    result = is_workday(date_str)
    print("workday" if result else "holiday")
'''

lunar_script = '''#!/usr/bin/env python3
"""
Convert a Gregorian date to Chinese lunar calendar.
Usage: python3 scripts/lunar_convert.py "YYYY-MM-DD"
Output: prints lunar date string e.g. "农历2025年正月初一"
"""
import sys
from datetime import datetime
from zhdate import ZhDate

def gregorian_to_lunar(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    zh = ZhDate.from_datetime(dt)
    return str(zh)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: lunar_convert.py YYYY-MM-DD")
        sys.exit(1)
    print(gregorian_to_lunar(sys.argv[1]))
'''

number_to_chinese_script = '''#!/usr/bin/env python3
"""
Convert a number to Chinese financial uppercase (大写).
Usage: python3 scripts/number_to_chinese.py "12345.67"
Output: prints e.g. "壹万贰仟叁佰肆拾伍元陆角柒分"
"""
import sys

UNITS = ["", "拾", "佰", "仟", "万", "拾", "佰", "仟", "亿", "拾", "佰", "仟"]
DIGITS = ["零", "壹", "贰", "叁", "肆", "伍", "陆", "柒", "捌", "玖"]

def number_to_chinese(amount_str):
    try:
        amount = round(float(amount_str), 2)
    except ValueError:
        return "无效金额"
    
    if amount < 0:
        return "负" + number_to_chinese(str(-amount))
    
    # Split integer and decimal
    str_amount = f"{amount:.2f}"
    parts = str_amount.split(".")
    int_part = int(parts[0])
    fen = int(parts[1][1]) if len(parts[1]) > 1 else 0
    jiao = int(parts[1][0]) if len(parts[1]) > 0 else 0
    
    if int_part == 0:
        yuan_str = ""
    else:
        digits = []
        num = int_part
        pos = 0
        while num > 0:
            d = num % 10
            digits.append((d, pos))
            num //= 10
            pos += 1
        digits.reverse()
        
        result = []
        prev_zero = False
        for i, (d, pos) in enumerate(digits):
            if d == 0:
                prev_zero = True
            else:
                if prev_zero and result:
                    result.append("零")
                result.append(DIGITS[d])
                result.append(UNITS[pos % len(UNITS)] if pos < len(UNITS) else "")
                prev_zero = False
            # Handle wan and yi separators
            if pos == 4 and not prev_zero:
                if result and result[-1] != "万":
                    result.append("万")
            if pos == 8 and not prev_zero:
                if result and result[-1] != "亿":
                    result.append("亿")
        
        # Simpler, more reliable implementation
        result = _int_to_chinese(int_part)
        yuan_str = result + "元"
    
    if jiao == 0 and fen == 0:
        return yuan_str + "整"
    elif fen == 0:
        return yuan_str + DIGITS[jiao] + "角整"
    elif jiao == 0:
        if int_part == 0:
            return "零" + DIGITS[fen] + "分"
        return yuan_str + "零" + DIGITS[fen] + "分"
    else:
        return yuan_str + DIGITS[jiao] + "角" + DIGITS[fen] + "分"

def _int_to_chinese(n):
    if n == 0:
        return "零"
    
    DIGITS = ["零", "壹", "贰", "叁", "肆", "伍", "陆", "柒", "捌", "玖"]
    
    def _part(num, units):
        """Convert a number < 10000 using given unit list."""
        if num == 0:
            return ""
        result = []
        u = ["", "拾", "佰", "仟"]
        digits_list = []
        tmp = num
        while tmp > 0:
            digits_list.append(tmp % 10)
            tmp //= 10
        digits_list.reverse()
        # Pad to length of units
        while len(digits_list) < len(u):
            digits_list.insert(0, 0)
        digits_list = digits_list[-(len(u)):]
        
        prev_zero = False
        started = False
        for i, d in enumerate(digits_list):
            if d == 0:
                prev_zero = True
            else:
                if prev_zero and started:
                    result.append("零")
                result.append(DIGITS[d])
                result.append(u[i])
                prev_zero = False
                started = True
        return "".join(result)
    
    yi = n // 100000000
    wan = (n % 100000000) // 10000
    ge = n % 10000
    
    result = ""
    if yi > 0:
        result += _part(yi, None) + "亿"
        if wan == 0 and ge > 0:
            result += "零"
    if wan > 0:
        if yi > 0 and wan < 1000:
            result += "零"
        result += _part(wan, None) + "万"
        if ge > 0 and ge < 1000:
            result += "零"
    if ge > 0:
        if (yi > 0 or wan > 0) and ge < 1000:
            pass  # zero already added
        result += _part(ge, None)
    elif result == "":
        result = "零"
    
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: number_to_chinese.py <amount>")
        sys.exit(1)
    print(number_to_chinese(sys.argv[1]))
'''

with open(os.path.join(workspace, "scripts/workday_check.py"), "w", encoding="utf-8") as f:
    f.write(workday_script)

with open(os.path.join(workspace, "scripts/lunar_convert.py"), "w", encoding="utf-8") as f:
    f.write(lunar_script)

with open(os.path.join(workspace, "scripts/number_to_chinese.py"), "w", encoding="utf-8") as f:
    f.write(number_to_chinese_script)

# Also create an __init__.py and a dummy script to add noise
with open(os.path.join(workspace, "scripts/__init__.py"), "w") as f:
    f.write("")

with open(os.path.join(workspace, "scripts/pinyin_convert.py"), "w", encoding="utf-8") as f:
    f.write('''#!/usr/bin/env python3
"""Convert Chinese names to pinyin."""
import sys
try:
    from pypinyin import pinyin, Style
    def name_to_pinyin(name):
        result = pinyin(name, style=Style.NORMAL)
        return " ".join([item[0] for item in result]).title()
    if __name__ == "__main__":
        if len(sys.argv) > 1:
            print(name_to_pinyin(sys.argv[1]))
except ImportError:
    print("pypinyin not installed")
''')

# --- The main problem file: messy transaction CSV ---
transactions = [
    # id, date, amount, description, department
    ("TXN-2025-001", "2025-01-15", "88000.00", "设备采购款", "技术部"),
    ("TXN-2025-002", "2025-02-03", "12345.67", "软件授权费", "信息部"),   # Spring festival holiday
    ("TXN-2025-003", "2025-03-16", "500.00", "办公用品", "行政部"),       # Sunday - should be holiday
    ("TXN-2025-004", "2025-04-05", "999999.99", "年度合同款", "财务部"),  # 清明节 holiday
    ("TXN-2025-005", "2025-05-15", "7800.50", "差旅费报销", "销售部"),    # Thursday workday
    ("TXN-2025-006", "2025-06-02", "23000.00", "广告投放费", "市场部"),   # 端午节 holiday
    ("TXN-2025-007", "2025-07-18", "456.78", "餐饮费", "行政部"),         # Friday workday
    ("TXN-2025-008", "2025-09-28", "1000000.00", "季度结算款", "财务部"), # 调休补班 workday
    ("TXN-2025-009", "2025-10-03", "33333.33", "国庆促销奖励", "销售部"),# 国庆节 holiday
    ("TXN-2025-010", "2025-12-25", "5500.00", "年终奖金补贴", "人事部"),  # Thursday workday
]

csv_path = os.path.join(workspace, "data/raw/transactions_2025.csv")
with open(csv_path, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["交易编号", "交易日期", "金额（元）", "摘要", "部门"])
    for row in transactions:
        writer.writerow(row)

# A second distractor CSV with different format to confuse
with open(os.path.join(workspace, "data/raw/contacts.csv"), "w", encoding="utf-8") as f:
    f.write("姓名,部门,电话\n张三,财务部,13800000001\n李四,技术部,13900000002\n王五,销售部,13700000003\n")

with open(os.path.join(workspace, "data/raw/products.csv"), "w", encoding="utf-8") as f:
    f.write("产品编号,产品名称,单价\nP001,笔记本电脑,8999.00\nP002,办公椅,1299.00\nP003,打印机,2599.00\n")

# A partial/wrong format JSON to confuse agents looking for pre-existing output
with open(os.path.join(workspace, "data/processed/partial_output.json"), "w", encoding="utf-8") as f:
    json.dump([
        {"id": "TXN-2025-001", "note": "数据未处理完整，请重新生成"}
    ], f, ensure_ascii=False, indent=2)

print("Workspace initialized successfully.")
print(f"Transaction file: {csv_path}")