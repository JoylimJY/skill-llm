#!/usr/bin/env python3
"""
Generate the sandbox workspace with realistic A-stock skill scripts,
mock data, and distractor files. The scripts simulate real analyze.py
and portfolio.py behavior but use a local mock server for data.
"""

import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ─────────────────────────────────────────────
# 1.  Directory structure + distractor files
# ─────────────────────────────────────────────
dirs = [
    "scripts",
    "data/raw",
    "data/processed",
    "data/cache",
    "logs",
    "config",
    "reports/daily",
    "reports/weekly",
    "notebooks",
    "utils",
    "tests",
    "backups/portfolio",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

distractors = {
    "data/raw/market_snapshot_20240101.csv": "date,code,open,close\n20240101,600519,1700.0,1720.5\n20240101,000001,11.2,11.5\n",
    "data/raw/index_data.json": json.dumps({"sh000001": 3100.5, "sz399001": 9800.3}),
    "data/processed/cleaned_prices.csv": "code,price\n600519,1720.5\n000001,11.5\n",
    "data/cache/sina_cache.json": json.dumps({"ts": "2024-01-01", "data": {}}),
    "logs/fetch_errors.log": "2024-01-02 09:35:12 ERROR timeout fetching 600789\n2024-01-02 10:01:55 ERROR 503 from hq.sinajs.cn\n",
    "logs/analysis.log": "2024-01-03 15:00:01 INFO analysis complete for 002446\n",
    "config/api_config.yaml": "endpoint: http://hq.sinajs.cn\ntimeout: 5\nretry: 3\n",
    "config/thresholds.yaml": "early_volume_warning: 0.30\ntail_volume_warning: 0.25\nstop_limit_buffer: 0.0\n",
    "reports/daily/report_20240102.txt": "Daily report placeholder\nNo data yet.\n",
    "reports/weekly/week01_summary.csv": "week,total_trades,pnl\n1,120,3200.0\n",
    "notebooks/eda.py": "# Exploratory data analysis\nimport pandas as pd\ndf = pd.read_csv('../data/raw/market_snapshot_20240101.csv')\nprint(df.head())\n",
    "utils/helpers.py": "def format_price(p):\n    return f'{p:.2f}'\n",
    "tests/test_helpers.py": "from utils.helpers import format_price\nassert format_price(10.5) == '10.50'\n",
    "backups/portfolio/portfolio_20231215.json": json.dumps([
        {"code": "600519", "cost": 1700.0, "qty": 100}
    ]),
    ".gitignore": "*.pyc\n__pycache__/\n.env\n",
}
for rel_path, content in distractors.items():
    p = workspace / rel_path
    p.write_text(content)

# ─────────────────────────────────────────────
# 2.  Mock HTTP server for sina finance API
# ─────────────────────────────────────────────
mock_server_script = r'''#!/usr/bin/env python3
"""
Local mock server simulating Sina Finance and Eastmoney APIs.
Listens on port 18888.
"""
from flask import Flask, request, Response
import json, random, math

app = Flask(__name__)

STOCKS = {
    "sh600789": {
        "name": "鲁抗医药",
        "price": 10.32,
        "open": 10.20,
        "high": 10.77,
        "low": 9.82,
        "prev_close": 10.23,
        "volume": 2181838,
        "amount": 2251053000,
        "turnover": 2.38,
    },
    "sz002446": {
        "name": "盛泰集团",
        "price": 8.75,
        "open": 8.60,
        "high": 8.92,
        "low": 8.55,
        "prev_close": 8.68,
        "volume": 980000,
        "amount": 855650000,
        "turnover": 1.12,
    },
    "sz002342": {
        "name": "巨力索具",
        "price": 5.44,
        "open": 5.38,
        "high": 5.60,
        "low": 5.30,
        "prev_close": 5.40,
        "volume": 542000,
        "amount": 295328000,
        "turnover": 0.87,
    },
}

def make_minute_data(stock_key):
    """Generate deterministic minute-by-minute data."""
    info = STOCKS[stock_key]
    base_price = info["price"]
    total_vol = info["volume"]
    minutes = []
    # 9:31 ~ 11:30, 13:01 ~ 15:00  (total 240 minutes of trading)
    import datetime
    slots = []
    for h in range(9, 12):
        start_m = 31 if h == 9 else 0
        end_m = 60 if h < 11 else 30
        for m in range(start_m, end_m):
            slots.append(f"{h:02d}:{m:02d}:00")
    for h in range(13, 15):
        start_m = 1 if h == 13 else 0
        end_m = 60 if h < 14 else 1
        for m in range(start_m, end_m):
            slots.append(f"{h:02d}:{m:02d}:00")
    # 14:30~15:00
    for m in range(30, 60):
        slots.append(f"14:{m:02d}:00")
    slots.append("15:00:00")

    # Weighted distribution: early heavy, tail medium
    random.seed(42)
    weights = []
    for s in slots:
        h, mn, _ = s.split(":")
        h, mn = int(h), int(mn)
        if h == 9 and mn <= 45:
            weights.append(8.0)   # early burst
        elif h == 9:
            weights.append(3.0)
        elif h == 14 and mn >= 30:
            weights.append(2.0)   # tail volume
        else:
            weights.append(1.0)

    total_w = sum(weights)
    vols = [int(total_vol * w / total_w) for w in weights]
    # Adjust last to match total
    diff = total_vol - sum(vols)
    vols[-1] += diff

    result = []
    price = base_price * 0.97
    for i, slot in enumerate(slots):
        price += random.uniform(-0.05, 0.06)
        price = max(price, info["low"])
        price = min(price, info["high"])
        result.append({
            "time": slot,
            "price": round(price, 2),
            "volume": vols[i],
            "amount": round(vols[i] * price * 100, 1)
        })
    return result

@app.route('/list', methods=['GET'])
def sina_realtime():
    """Simulate hq.sinajs.cn list endpoint."""
    codes_param = request.args.get('list', '')
    parts = codes_param.split(',')
    lines = []
    for code in parts:
        code = code.strip()
        if code in STOCKS:
            s = STOCKS[code]
            # sina format: var hq_str_sh600789="鲁抗医药,open,prev,price,high,low,...,volume,amount,..."
            line = (
                f'var hq_str_{code}="{s["name"]},'
                f'{s["open"]:.2f},'
                f'{s["prev_close"]:.2f},'
                f'{s["price"]:.2f},'
                f'{s["high"]:.2f},'
                f'{s["low"]:.2f},'
                f'0,0,'
                f'{s["volume"]},'
                f'{int(s["amount"])},'
                f'0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'
                f'2024-01-03,15:00:00,00"'
            )
            lines.append(line)
    return Response('\n'.join(lines), content_type='application/javascript; charset=GBK')

@app.route('/json/CN_MarketDataService.getKLineData', methods=['GET'])
def minute_kline():
    """Simulate Eastmoney minute kline endpoint."""
    symbol = request.args.get('symbol', '')
    # symbol format: 0.002446 or 1.600789
    code = symbol.split('.')[-1] if '.' in symbol else symbol
    # find in STOCKS
    stock_key = None
    for k in STOCKS:
        if k.endswith(code):
            stock_key = k
            break
    if not stock_key:
        return Response(json.dumps({"data": {"klines": []}}), content_type='application/json')
    
    minute_data = make_minute_data(stock_key)
    klines = []
    for d in minute_data:
        klines.append(f"{d['time']},{d['price']},{d['price']},{d['price']},{d['price']},{d['volume']},{d['amount']}")
    
    result = {
        "data": {
            "code": code,
            "name": STOCKS[stock_key]["name"],
            "klines": klines
        }
    }
    return Response(json.dumps(result, ensure_ascii=False), content_type='application/json')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=18888, debug=False)
'''

(workspace / "scripts" / "mock_server.py").write_text(mock_server_script)

# ─────────────────────────────────────────────
# 3.  analyze.py  (the real skill script)
# ─────────────────────────────────────────────
analyze_script = r'''#!/usr/bin/env python3
"""
A股实时行情与分时量能分析 - analyze.py
Uses MOCK_SERVER env var to override API endpoints for testing.
"""
import sys
import os
import json
import argparse
import requests

MOCK_BASE = os.environ.get("SINA_MOCK_URL", "http://hq.sinajs.cn")
EASTMONEY_MOCK = os.environ.get("EASTMONEY_MOCK_URL", "http://push2his.eastmoney.com")

def get_market_prefix(code):
    if code.startswith('6'):
        return 'sh'
    elif code.startswith('0') or code.startswith('3'):
        return 'sz'
    elif code.startswith('8') or code.startswith('4'):
        return 'bj'
    return 'sh'

def fetch_realtime(codes):
    """Fetch real-time data from sina."""
    symbols = [get_market_prefix(c) + c for c in codes]
    url = f"{MOCK_BASE}/list={','.join(symbols)}"
    try:
        resp = requests.get(url, timeout=5)
        resp.encoding = 'gbk'
        text = resp.text
    except Exception as e:
        return {c: None for c in codes}
    
    results = {}
    for i, code in enumerate(codes):
        sym = symbols[i]
        prefix = f'var hq_str_{sym}="'
        for line in text.split('\n'):
            if line.startswith(prefix):
                data_str = line[len(prefix):].rstrip('";')
                parts = data_str.split(',')
                if len(parts) >= 10:
                    results[code] = {
                        'name': parts[0],
                        'open': float(parts[1]) if parts[1] else 0,
                        'prev_close': float(parts[2]) if parts[2] else 0,
                        'price': float(parts[3]) if parts[3] else 0,
                        'high': float(parts[4]) if parts[4] else 0,
                        'low': float(parts[5]) if parts[5] else 0,
                        'volume': int(parts[8]) if parts[8] else 0,
                        'amount': float(parts[9]) if parts[9] else 0,
                    }
                break
        if code not in results:
            results[code] = None
    return results

def fetch_minute_data(code):
    """Fetch minute kline data."""
    prefix_num = '1' if code.startswith('6') else '0'
    symbol = f"{prefix_num}.{code}"
    url = (f"{EASTMONEY_MOCK}/json/CN_MarketDataService.getKLineData"
           f"?symbol={symbol}&type=5&end=20500101000000&count=250&fields1=f1,f2,f3,f4,f5&fields2=f51,f52,f53,f54,f55,f56,f57")
    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        klines = data.get('data', {}).get('klines', [])
    except Exception:
        return []
    
    parsed = []
    for k in klines:
        parts = k.split(',')
        if len(parts) >= 6:
            parsed.append({
                'time': parts[0],
                'price': float(parts[1]),
                'volume': int(parts[5]),
                'amount': float(parts[6]) if len(parts) > 6 else 0,
            })
    return parsed

def analyze_minute_volume(code, name, minute_data):
    """Analyze minute-level volume distribution."""
    if not minute_data:
        return None
    
    total_vol = sum(d['volume'] for d in minute_data)
    if total_vol == 0:
        return None
    
    # Segment volumes
    early_vol = 0    # 9:30-10:00
    mid_am_vol = 0   # 10:00-11:30
    mid_pm_vol = 0   # 13:00-14:30
    tail_vol = 0     # 14:30-15:00
    
    top_minutes = []
    
    for d in minute_data:
        t = d['time']
        h, m = int(t[:2]), int(t[3:5])
        vol = d['volume']
        
        top_minutes.append(d)
        
        if h == 9 and m >= 30:
            early_vol += vol
        elif h == 9 or (h == 10 and m == 0):
            early_vol += vol
        if (h == 10) or (h == 11 and m <= 30):
            mid_am_vol += vol
        if (h == 13) or (h == 14 and m < 30):
            mid_pm_vol += vol
        if h == 14 and m >= 30:
            tail_vol += vol
        if h == 15:
            tail_vol += vol
    
    # Sort top 10
    top10 = sorted(top_minutes, key=lambda x: x['volume'], reverse=True)[:10]
    
    early_pct = early_vol / total_vol * 100
    mid_am_pct = mid_am_vol / total_vol * 100
    mid_pm_pct = mid_pm_vol / total_vol * 100
    tail_pct = tail_vol / total_vol * 100
    
    signals = []
    if early_pct > 40:
        signals.append("主力强势介入")
    elif early_pct > 30:
        signals.append("早盘主力抢筹明显")
    if tail_pct > 25:
        signals.append("尾盘异动，可能主力抢筹或出货")
    elif tail_pct > 15:
        signals.append("尾盘有一定放量")
    
    return {
        'name': name,
        'total_volume': total_vol,
        'total_amount': sum(d['amount'] for d in minute_data),
        'segments': {
            'early_30min': {'volume': early_vol, 'pct': round(early_pct, 1)},
            'morning_mid': {'volume': mid_am_vol, 'pct': round(mid_am_pct, 1)},
            'afternoon_mid': {'volume': mid_pm_vol, 'pct': round(mid_pm_pct, 1)},
            'tail_30min': {'volume': tail_vol, 'pct': round(tail_pct, 1)},
        },
        'top10_minutes': top10,
        'signals': signals,
    }

def print_stock_info(code, info, minute_analysis=None):
    print("=" * 60)
    if info:
        change_pct = (info['price'] - info['prev_close']) / info['prev_close'] * 100 if info['prev_close'] else 0
        print(f"股票: {info['name']} ({code})")
        print("=" * 60)
        print("\n【实时行情】")
        print(f"  现价: {info['price']:.2f}  涨跌: {change_pct:+.2f}%")
        print(f"  今开: {info['open']:.2f}  最高: {info['high']:.2f}  最低: {info['low']:.2f}")
        print(f"  昨收: {info['prev_close']:.2f}")
        print(f"  成交量: {info['volume']/10000:.1f}万手  成交额: {info['amount']/100000000:.2f}亿")
    
    if minute_analysis:
        ma = minute_analysis
        print(f"\n【分时量能分析】{ma['name']}")
        print(f"  全天成交: {ma['total_volume']}手 ({ma['total_amount']/10000:.1f}万元)")
        print(f"\n  成交分布:")
        seg = ma['segments']
        print(f"    早盘30分(9:30-10:00): {seg['early_30min']['volume']}手 ({seg['early_30min']['pct']}%)")
        print(f"    上午中段(10:00-11:30): {seg['morning_mid']['volume']}手 ({seg['morning_mid']['pct']}%)")
        print(f"    下午中段(13:00-14:30): {seg['afternoon_mid']['volume']}手 ({seg['afternoon_mid']['pct']}%)")
        print(f"    尾盘30分(14:30-15:00): {seg['tail_30min']['volume']}手 ({seg['tail_30min']['pct']}%)")
        print(f"\n  放量时段 TOP 10:")
        for t in ma['top10_minutes']:
            print(f"    {t['time']} 价格:{t['price']} 成交:{t['volume']}手 金额:{t['amount']/10000:.1f}万")
        if ma['signals']:
            print(f"\n  【主力动向判断】")
            for sig in ma['signals']:
                print(f"    🔥 {sig}")

def format_json(codes, infos, analyses):
    result = []
    for code in codes:
        info = infos.get(code)
        analysis = analyses.get(code)
        entry = {'code': code}
        if info:
            change_pct = (info['price'] - info['prev_close']) / info['prev_close'] * 100 if info['prev_close'] else 0
            entry.update({
                'name': info['name'],
                'price': info['price'],
                'change_pct': round(change_pct, 2),
                'open': info['open'],
                'high': info['high'],
                'low': info['low'],
                'prev_close': info['prev_close'],
                'volume': info['volume'],
                'amount': info['amount'],
            })
        if analysis:
            entry['minute_analysis'] = analysis
        result.append(entry)
    return result

def main():
    parser = argparse.ArgumentParser(description='A股实时行情分析')
    parser.add_argument('codes', nargs='+', help='股票代码')
    parser.add_argument('--minute', action='store_true', help='分时量能分析')
    parser.add_argument('--json', action='store_true', dest='json_output', help='JSON输出')
    args = parser.parse_args()
    
    codes = args.codes
    infos = fetch_realtime(codes)
    
    analyses = {}
    if args.minute:
        for code in codes:
            info = infos.get(code)
            name = info['name'] if info else code
            mdata = fetch_minute_data(code)
            analyses[code] = analyze_minute_volume(code, name, mdata)
    
    if args.json_output:
        result = format_json(codes, infos, analyses)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for code in codes:
            print_stock_info(code, infos.get(code), analyses.get(code))

if __name__ == '__main__':
    main()
'''
(workspace / "scripts" / "analyze.py").write_text(analyze_script)

# ─────────────────────────────────────────────
# 4.  portfolio.py  (the real skill script)
# ─────────────────────────────────────────────
portfolio_script = r'''#!/usr/bin/env python3
"""
持仓管理 - portfolio.py
Portfolio data is stored at ~/.clawdbot/skills/a-stock-analysis/portfolio.json
"""
import sys
import os
import json
import argparse
import subprocess
from pathlib import Path

PORTFOLIO_DIR = Path.home() / ".clawdbot" / "skills" / "a-stock-analysis"
PORTFOLIO_FILE = PORTFOLIO_DIR / "portfolio.json"

def load_portfolio():
    if not PORTFOLIO_FILE.exists():
        return []
    with open(PORTFOLIO_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_portfolio(portfolio):
    PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)
    with open(PORTFOLIO_FILE, 'w', encoding='utf-8') as f:
        json.dump(portfolio, f, ensure_ascii=False, indent=2)

def find_holding(portfolio, code):
    for h in portfolio:
        if h['code'] == code:
            return h
    return None

def cmd_show(args):
    portfolio = load_portfolio()
    if not portfolio:
        print("持仓为空")
        return
    print(f"{'代码':<10} {'成本价':<10} {'数量':<10}")
    print("-" * 35)
    for h in portfolio:
        print(f"{h['code']:<10} {h['cost']:<10.3f} {h['qty']:<10}")

def cmd_add(args):
    portfolio = load_portfolio()
    existing = find_holding(portfolio, args.code)
    if existing:
        print(f"已存在持仓 {args.code}，请使用 update 命令更新")
        return
    holding = {
        'code': args.code,
        'cost': args.cost,
        'qty': args.qty,
    }
    portfolio.append(holding)
    save_portfolio(portfolio)
    print(f"已添加持仓: {args.code} 成本:{args.cost} 数量:{args.qty}")

def cmd_update(args):
    portfolio = load_portfolio()
    holding = find_holding(portfolio, args.code)
    if not holding:
        print(f"未找到持仓 {args.code}")
        return
    if args.cost is not None:
        holding['cost'] = args.cost
    if args.qty is not None:
        holding['qty'] = args.qty
    save_portfolio(portfolio)
    print(f"已更新持仓: {args.code}")

def cmd_remove(args):
    portfolio = load_portfolio()
    before = len(portfolio)
    portfolio = [h for h in portfolio if h['code'] != args.code]
    if len(portfolio) == before:
        print(f"未找到持仓 {args.code}")
    else:
        save_portfolio(portfolio)
        print(f"已删除持仓: {args.code}")

def cmd_analyze(args):
    portfolio = load_portfolio()
    if not portfolio:
        print("持仓为空，无法分析")
        return
    codes = [h['code'] for h in portfolio]
    script_dir = Path(__file__).parent
    analyze_script = script_dir / "analyze.py"
    cmd = [sys.executable, str(analyze_script)] + codes + ['--minute', '--json']
    env = os.environ.copy()
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    
    try:
        analysis_data = json.loads(result.stdout)
    except Exception:
        print(result.stdout)
        return
    
    # Merge pnl info
    price_map = {}
    for item in analysis_data:
        price_map[item['code']] = item.get('price', 0)
    
    enriched = []
    total_cost_value = 0
    total_market_value = 0
    
    for h in portfolio:
        code = h['code']
        current_price = price_map.get(code, 0)
        cost_value = h['cost'] * h['qty']
        market_value = current_price * h['qty']
        pnl = market_value - cost_value
        pnl_pct = pnl / cost_value * 100 if cost_value else 0
        total_cost_value += cost_value
        total_market_value += market_value
        
        entry = {
            'code': code,
            'cost': h['cost'],
            'qty': h['qty'],
            'current_price': current_price,
            'pnl': round(pnl, 2),
            'pnl_pct': round(pnl_pct, 2),
        }
        # Attach analysis
        for item in analysis_data:
            if item['code'] == code:
                entry['analysis'] = item
                break
        enriched.append(entry)
    
    total_pnl = total_market_value - total_cost_value
    total_pnl_pct = total_pnl / total_cost_value * 100 if total_cost_value else 0
    
    output = {
        'portfolio': enriched,
        'summary': {
            'total_cost': round(total_cost_value, 2),
            'total_market_value': round(total_market_value, 2),
            'total_pnl': round(total_pnl, 2),
            'total_pnl_pct': round(total_pnl_pct, 2),
        }
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))

def main():
    parser = argparse.ArgumentParser(description='持仓管理')
    subparsers = parser.add_subparsers(dest='command')
    
    # show
    subparsers.add_parser('show')
    
    # add
    add_p = subparsers.add_parser('add')
    add_p.add_argument('code')
    add_p.add_argument('--cost', type=float, required=True)
    add_p.add_argument('--qty', type=int, required=True)
    
    # update
    upd_p = subparsers.add_parser('update')
    upd_p.add_argument('code')
    upd_p.add_argument('--cost', type=float)
    upd_p.add_argument('--qty', type=int)
    
    # remove
    rem_p = subparsers.add_parser('remove')
    rem_p.add_argument('code')
    
    # analyze
    subparsers.add_parser('analyze')
    
    args = parser.parse_args()
    
    commands = {
        'show': cmd_show,
        'add': cmd_add,
        'update': cmd_update,
        'remove': cmd_remove,
        'analyze': cmd_analyze,
    }
    
    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
'''
(workspace / "scripts" / "portfolio.py").write_text(portfolio_script)

# ─────────────────────────────────────────────
# 5.  Additional distractor files
# ─────────────────────────────────────────────
(workspace / "config" / "portfolio_schema.json").write_text(json.dumps({
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "code": {"type": "string"},
            "cost": {"type": "number"},
            "qty": {"type": "integer"}
        }
    }
}))

(workspace / "data" / "cache" / "portfolio_cache_old.json").write_text(json.dumps([
    {"code": "600036", "cost": 42.5, "qty": 200},
    {"code": "000858", "cost": 180.0, "qty": 50}
]))

(workspace / "reports" / "daily" / "pnl_20240103.txt").write_text(
    "PNL Report 2024-01-03\n600036: +2.3%\n000858: -1.1%\n"
)

(workspace / "utils" / "sina_parser.py").write_text(
    "# Legacy parser for old sina format\ndef parse_line(line):\n    return line.split(',')\n"
)

(workspace / "utils" / "eastmoney_parser.py").write_text(
    "# Eastmoney kline parser stub\ndef parse_kline(k):\n    return k.split(',')\n"
)

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")