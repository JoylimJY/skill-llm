#!/bin/bash
set -e

# ---- Ensure scripts directory exists ----
mkdir -p /workspace/scripts

# ---- Create mock scripts in /workspace/scripts ----
# These simulate the real scripts described in SKILL.md with deterministic outputs.

# ---- fund_screener.py ----
cat > /workspace/scripts/fund_screener.py << 'PYEOF'
#!/usr/bin/env python3
"""Mock fund screener - simulates scripts/fund_screener.py from SKILL.md"""
import argparse
import json
import sys

MOCK_DATA = {
    ("近1年", "股票型", 3): [
        {"fund_code": "110011", "fund_name": "易方达中小盘混合", "fund_type": "股票型", "return_1y": "28.45%", "return_3y": "67.12%", "scale": "156.3亿", "risk": "中高风险"},
        {"fund_code": "161039", "fund_name": "富国中证红利指数增强A", "fund_type": "股票型", "return_1y": "24.78%", "return_3y": "55.30%", "scale": "42.8亿", "risk": "中高风险"},
        {"fund_code": "003095", "fund_name": "中欧医疗健康混合A", "fund_type": "股票型", "return_1y": "19.92%", "return_3y": "88.44%", "scale": "93.1亿", "risk": "高风险"},
    ],
    ("近3年", "股票型", 3): [
        {"fund_code": "003095", "fund_name": "中欧医疗健康混合A", "fund_type": "股票型", "return_1y": "19.92%", "return_3y": "88.44%", "scale": "93.1亿", "risk": "高风险"},
        {"fund_code": "110011", "fund_name": "易方达中小盘混合", "fund_type": "股票型", "return_1y": "28.45%", "return_3y": "67.12%", "scale": "156.3亿", "risk": "中高风险"},
        {"fund_code": "161039", "fund_name": "富国中证红利指数增强A", "fund_type": "股票型", "return_1y": "24.78%", "return_3y": "55.30%", "scale": "42.8亿", "risk": "中高风险"},
    ],
    ("近1年", "混合型", 3): [
        {"fund_code": "001156", "fund_name": "申万菱信沪深300价值ETF联接A", "fund_type": "混合型", "return_1y": "15.33%", "return_3y": "38.10%", "scale": "22.5亿", "risk": "中风险"},
        {"fund_code": "002001", "fund_name": "华夏新经济混合A", "fund_type": "混合型", "return_1y": "13.90%", "return_3y": "32.50%", "scale": "18.2亿", "risk": "中风险"},
        {"fund_code": "004040", "fund_name": "广发多因子混合", "fund_type": "混合型", "return_1y": "12.60%", "return_3y": "28.70%", "scale": "30.1亿", "risk": "中风险"},
    ],
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rank", required=True)
    parser.add_argument("--type", required=True)
    parser.add_argument("--top", type=int, required=True)
    args = parser.parse_args()

    key = (args.rank, args.type, args.top)
    # Find closest match
    result = None
    for k, v in MOCK_DATA.items():
        if k[0] == args.rank and k[1] == args.type:
            result = v[:args.top]
            break

    if result is None:
        print(json.dumps({"error": f"No data for rank={args.rank} type={args.type}"}))
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
PYEOF

# ---- query_fund_nav.py ----
cat > /workspace/scripts/query_fund_nav.py << 'PYEOF'
#!/usr/bin/env python3
"""Mock NAV query - simulates scripts/query_fund_nav.py from SKILL.md"""
import sys
import json

MOCK_NAV = {
    "110011": {
        "fund_code": "110011",
        "fund_name": "易方达中小盘混合",
        "latest_nav": "2.4580",
        "daily_change": "+1.23%",
        "return_1w": "2.10%",
        "return_1m": "5.40%",
        "return_3m": "8.70%",
        "return_6m": "14.20%",
        "return_1y": "28.45%",
        "return_3y": "67.12%",
        "fund_type": "股票型",
        "manager": "易方达基金管理有限公司",
        "scale": "156.3亿"
    },
    "161039": {
        "fund_code": "161039",
        "fund_name": "富国中证红利指数增强A",
        "latest_nav": "1.3450",
        "daily_change": "+0.87%",
        "return_1w": "1.30%",
        "return_1m": "3.20%",
        "return_3m": "6.10%",
        "return_6m": "11.50%",
        "return_1y": "24.78%",
        "return_3y": "55.30%",
        "fund_type": "股票型",
        "manager": "富国基金管理有限公司",
        "scale": "42.8亿"
    },
    "003095": {
        "fund_code": "003095",
        "fund_name": "中欧医疗健康混合A",
        "latest_nav": "3.1020",
        "daily_change": "-0.45%",
        "return_1w": "-0.50%",
        "return_1m": "1.80%",
        "return_3m": "4.30%",
        "return_6m": "9.00%",
        "return_1y": "19.92%",
        "return_3y": "88.44%",
        "fund_type": "股票型",
        "manager": "中欧基金管理有限公司",
        "scale": "93.1亿"
    },
}

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: query_fund_nav.py <fund_code>"}))
        sys.exit(1)
    code = sys.argv[1].strip()
    data = MOCK_NAV.get(code)
    if data is None:
        print(json.dumps({"error": f"Fund {code} not found"}))
        sys.exit(1)
    print(json.dumps(data, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
PYEOF

# ---- query_fund_history.py ----
cat > /workspace/scripts/query_fund_history.py << 'PYEOF'
#!/usr/bin/env python3
"""Mock history query - simulates scripts/query_fund_history.py from SKILL.md"""
import sys
import json
import argparse

MOCK_HISTORY = {
    ("110011", "1y"): {
        "fund_code": "110011",
        "period": "1y",
        "nav_curve": [
            {"date": "2023-06-01", "nav": "1.9820"},
            {"date": "2023-09-01", "nav": "2.1450"},
            {"date": "2023-12-01", "nav": "2.2300"},
            {"date": "2024-03-01", "nav": "2.3500"},
            {"date": "2024-06-01", "nav": "2.4580"},
        ],
        "return_1y": "28.45%",
        "peer_rank": "前15%",
        "sharpe_ratio": "1.42",
        "max_drawdown": "-12.30%"
    },
    ("161039", "1y"): {
        "fund_code": "161039",
        "period": "1y",
        "nav_curve": [
            {"date": "2023-06-01", "nav": "1.0780"},
            {"date": "2023-09-01", "nav": "1.1230"},
            {"date": "2023-12-01", "nav": "1.1900"},
            {"date": "2024-03-01", "nav": "1.2500"},
            {"date": "2024-06-01", "nav": "1.3450"},
        ],
        "return_1y": "24.78%",
        "peer_rank": "前22%",
        "sharpe_ratio": "1.18",
        "max_drawdown": "-9.80%"
    },
    ("003095", "1y"): {
        "fund_code": "003095",
        "period": "1y",
        "nav_curve": [
            {"date": "2023-06-01", "nav": "2.4800"},
            {"date": "2023-09-01", "nav": "2.6100"},
            {"date": "2023-12-01", "nav": "2.7500"},
            {"date": "2024-03-01", "nav": "2.9200"},
            {"date": "2024-06-01", "nav": "3.1020"},
        ],
        "return_1y": "19.92%",
        "peer_rank": "前30%",
        "sharpe_ratio": "0.98",
        "max_drawdown": "-18.50%"
    },
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("fund_code")
    parser.add_argument("--period", default="1y")
    args = parser.parse_args()

    key = (args.fund_code.strip(), args.period.strip())
    data = MOCK_HISTORY.get(key)
    if data is None:
        print(json.dumps({"error": f"No history for {args.fund_code} period={args.period}"}))
        sys.exit(1)
    print(json.dumps(data, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
PYEOF

# ---- query_fund_holding.py ----
cat > /workspace/scripts/query_fund_holding.py << 'PYEOF'
#!/usr/bin/env python3
"""Mock holdings query - simulates scripts/query_fund_holding.py from SKILL.md"""
import sys
import json

MOCK_HOLDINGS = {
    "110011": {
        "fund_code": "110011",
        "fund_name": "易方达中小盘混合",
        "top10_holdings": [
            {"stock": "宁德时代", "code": "300750", "weight": "8.32%", "change": "+0.50%"},
            {"stock": "贵州茅台", "code": "600519", "weight": "7.85%", "change": "-0.20%"},
            {"stock": "隆基绿能", "code": "601012", "weight": "5.40%", "change": "+1.10%"},
            {"stock": "迈瑞医疗", "code": "300760", "weight": "4.90%", "change": "+0.30%"},
            {"stock": "药明康德", "code": "603259", "weight": "4.22%", "change": "-0.50%"},
            {"stock": "比亚迪", "code": "002594", "weight": "3.80%", "change": "+0.80%"},
            {"stock": "三一重工", "code": "600031", "weight": "3.10%", "change": "+0.10%"},
            {"stock": "中国平安", "code": "601318", "weight": "2.75%", "change": "-0.30%"},
            {"stock": "招商银行", "code": "600036", "weight": "2.50%", "change": "+0.20%"},
            {"stock": "海天味业", "code": "603288", "weight": "2.30%", "change": "-0.10%"},
        ],
        "sector_distribution": {
            "新能源": "25.3%",
            "医疗健康": "18.7%",
            "消费": "16.2%",
            "科技": "14.5%",
            "金融": "12.0%",
            "其他": "13.3%"
        }
    },
    "161039": {
        "fund_code": "161039",
        "fund_name": "富国中证红利指数增强A",
        "top10_holdings": [
            {"stock": "中国神华", "code": "601088", "weight": "6.10%", "change": "+0.20%"},
            {"stock": "长江电力", "code": "600900", "weight": "5.80%", "change": "+0.10%"},
            {"stock": "中国建筑", "code": "601668", "weight": "5.20%", "change": "-0.10%"},
            {"stock": "工商银行", "code": "601398", "weight": "4.90%", "change": "0%"},
            {"stock": "农业银行", "code": "601288", "weight": "4.50%", "change": "+0.05%"},
            {"stock": "中国石化", "code": "600028", "weight": "4.10%", "change": "-0.20%"},
            {"stock": "中国移动", "code": "600941", "weight": "3.80%", "change": "+0.30%"},
            {"stock": "格力电器", "code": "000651", "weight": "3.40%", "change": "+0.50%"},
            {"stock": "潍柴动力", "code": "000338", "weight": "3.10%", "change": "-0.15%"},
            {"stock": "上汽集团", "code": "600104", "weight": "2.90%", "change": "+0.10%"},
        ],
        "sector_distribution": {
            "能源": "22.5%",
            "金融": "20.3%",
            "工业": "18.7%",
            "公用事业": "15.2%",
            "消费": "12.0%",
            "其他": "11.3%"
        }
    },
    "003095": {
        "fund_code": "003095",
        "fund_name": "中欧医疗健康混合A",
        "top10_holdings": [
            {"stock": "药明康德", "code": "603259", "weight": "9.50%", "change": "-0.80%"},
            {"stock": "迈瑞医疗", "code": "300760", "weight": "8.70%", "change": "+0.60%"},
            {"stock": "爱尔眼科", "code": "300015", "weight": "7.30%", "change": "+0.40%"},
            {"stock": "恒瑞医药", "code": "600276", "weight": "6.80%", "change": "-0.20%"},
            {"stock": "华熙生物", "code": "688363", "weight": "5.60%", "change": "+1.20%"},
            {"stock": "泰格医药", "code": "300347", "weight": "5.10%", "change": "-0.50%"},
            {"stock": "凯莱英", "code": "002821", "weight": "4.40%", "change": "+0.30%"},
            {"stock": "片仔癀", "code": "600436", "weight": "4.00%", "change": "+0.10%"},
            {"stock": "云南白药", "code": "000538", "weight": "3.50%", "change": "-0.10%"},
            {"stock": "通策医疗", "code": "600763", "weight": "3.20%", "change": "+0.70%"},
        ],
        "sector_distribution": {
            "医疗设备": "30.5%",
            "制药": "28.3%",
            "医疗服务": "22.7%",
            "生物科技": "12.5%",
            "其他": "6.0%"
        }
    },
}

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: query_fund_holding.py <fund_code>"}))
        sys.exit(1)
    code = sys.argv[1].strip()
    data = MOCK_HOLDINGS.get(code)
    if data is None:
        print(json.dumps({"error": f"Fund {code} not found"}))
        sys.exit(1)
    print(json.dumps(data, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
PYEOF

# ---- compare_funds.py ----
cat > /workspace/scripts/compare_funds.py << 'PYEOF'
#!/usr/bin/env python3
"""Mock compare funds - simulates scripts/compare_funds.py from SKILL.md"""
import sys
import json
import subprocess

def main():
    codes = sys.argv[1:]
    if not codes:
        print(json.dumps({"error": "Usage: compare_funds.py <code1> <code2> ..."}))
        sys.exit(1)
    results = []
    for code in codes:
        result = subprocess.run(
            ["python3", "/workspace/scripts/query_fund_nav.py", code],
            capture_output=True, text=True
        )
        try:
            data = json.loads(result.stdout)
            results.append(data)
        except Exception:
            results.append({"error": f"Failed for {code}"})
    print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
PYEOF

chmod +x /workspace/scripts/fund_screener.py
chmod +x /workspace/scripts/query_fund_nav.py
chmod +x /workspace/scripts/query_fund_history.py
chmod +x /workspace/scripts/query_fund_holding.py
chmod +x /workspace/scripts/compare_funds.py

echo "Mock scripts installed successfully."