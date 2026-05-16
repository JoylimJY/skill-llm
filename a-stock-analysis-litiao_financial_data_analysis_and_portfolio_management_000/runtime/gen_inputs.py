import os
import json
import random
import stat
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# === Deep directory structure with distractor files ===
dirs = [
    "projects/quant_research/backtests",
    "projects/quant_research/signals",
    "projects/quant_research/reports",
    "projects/risk_management/daily",
    "projects/risk_management/weekly",
    "data/raw/sina",
    "data/raw/eastmoney",
    "data/processed",
    "data/cache",
    "logs/2024",
    "logs/2025",
    "tools/scripts",
    "tools/configs",
    "notes",
    "temp",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# === Distractor files ===
distractors = {
    "projects/quant_research/backtests/momentum_v2.py": """# Momentum strategy backtest
import pandas as pd
def run_backtest(start='2024-01-01', end='2024-12-31'):
    # Placeholder backtest logic
    return {'sharpe': 1.42, 'max_dd': -0.18}
""",
    "projects/quant_research/signals/volume_signal.py": """# Volume anomaly signal detector
# NOTE: This is an OLD script, replaced by analyze.py
def detect_volume_spike(df, threshold=2.5):
    return df[df['volume'] > df['volume'].rolling(20).mean() * threshold]
""",
    "projects/quant_research/reports/weekly_summary_2025_01.txt": """Weekly Summary - Week 1, 2025
Top performers: 600036, 000651, 002594
Key risk events: Fed meeting, CPI release
Portfolio beta: 0.87
""",
    "projects/risk_management/daily/var_report_20250601.json": json.dumps({
        "date": "2025-06-01",
        "portfolio_var_95": 0.023,
        "portfolio_var_99": 0.041,
        "holdings": ["600036", "002594", "300750"],
        "total_exposure": 850000
    }, indent=2, ensure_ascii=False),
    "projects/risk_management/weekly/exposure_limits.yaml": """# Exposure limits config
max_single_position: 0.15
max_sector_exposure: 0.35
stop_loss_threshold: -0.08
""",
    "data/raw/sina/sample_response_600036.txt": """var hq_str_sh600036="招商银行,38.50,38.20,38.65,39.10,38.10,38.64,38.65,12345678,476543210,100,38.64,200,38.63,300,38.62,400,38.61,500,38.60,100,38.65,200,38.66,300,38.67,400,38.68,500,38.69,2025-06-10,14:30:00,00,";""",
    "data/raw/eastmoney/api_notes.txt": """EastMoney API Notes (DEPRECATED)
- Old endpoint: http://push2.eastmoney.com/api/qt/stock/get
- Replaced by sina interface for consistency
- Do NOT use eastmoney for minute data
""",
    "data/processed/portfolio_archive_2024.json": json.dumps({
        "archived_date": "2024-12-31",
        "positions": [
            {"code": "600036", "cost": 35.20, "qty": 1000, "exit_price": 37.80},
            {"code": "000651", "cost": 52.10, "qty": 500, "exit_price": 55.40}
        ]
    }, indent=2, ensure_ascii=False),
    "data/cache/minute_cache_notes.txt": """Cache policy: TTL = 60 seconds for minute data
Max 250 data points per symbol (approx 1 trading day)
""",
    "logs/2025/app_2025_06_01.log": """2025-06-01 09:30:01 INFO  Starting market data fetch
2025-06-01 09:30:02 INFO  Fetched 600036: 38.50
2025-06-01 09:30:03 INFO  Fetched 002594: 215.30
2025-06-01 15:00:00 INFO  Market closed, archiving data
""",
    "logs/2024/errors_2024.log": """2024-11-15 ERROR Failed to fetch 300750: connection timeout
2024-11-15 ERROR Retry 1/3...
2024-11-15 INFO  Retry successful
""",
    "tools/configs/stocks_watchlist.txt": """# Current watchlist
600036   # 招商银行 - core holding
002594   # 比亚迪 - growth position
300750   # 宁德时代 - thematic
601318   # 中国平安 - insurance sector
000858   # 五粮液 - consumer
""",
    "tools/scripts/fetch_historic.sh": """#!/bin/bash
# Legacy script to fetch historic data
# DEPRECATED: use analyze.py instead
echo "This script is deprecated. Use uv run scripts/analyze.py instead."
""",
    "notes/trading_journal_2025.md": """# Trading Journal 2025

## June 10
- 600036 showing unusual morning volume (>35% in first 30min)
- 002594 consolidating after recent run-up
- Need to check 300750 minute data for accumulation signals
- TODO: Set up portfolio tracker with actual cost basis
""",
    "temp/scratch.py": """# Scratch calculations
# 600036: bought 2000 shares @ 36.50 on 2025-05-15
# 002594: bought 500 shares @ 210.00 on 2025-04-20
# 300750: bought 300 shares @ 185.00 on 2025-03-10
# Need to update portfolio tracker!
""",
}

for rel_path, content in distractors.items():
    p = workspace / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

# === Create the skill base directory ===
skill_base = workspace / "skills" / "a-stock-analysis"
skill_base.mkdir(parents=True, exist_ok=True)
scripts_dir = skill_base / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

# === Create the mock analyze.py script ===
analyze_py = scripts_dir / "analyze.py"
analyze_py.write_text(r'''#!/usr/bin/env python3
"""A股实时行情与分时量能分析 - analyze.py"""
import sys
import json
import argparse
import requests
from pathlib import Path
from datetime import datetime

SINA_BASE = "http://localhost:18888"

def get_market_prefix(code):
    if code.startswith('6'):
        return 'sh'
    elif code.startswith(('0', '3')):
        return 'sz'
    elif code.startswith(('8', '4')):
        return 'bj'
    return 'sh'

def fetch_realtime(codes):
    symbols = ','.join(f"{get_market_prefix(c)}{c}" for c in codes)
    url = f"{SINA_BASE}/list={symbols}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    results = {}
    for line in resp.text.strip().split('\n'):
        if '=' not in line:
            continue
        sym_part, data_part = line.split('=', 1)
        sym = sym_part.strip().replace('var hq_str_', '').strip()
        data_part = data_part.strip().strip('"').strip(';').strip('"')
        if not data_part:
            continue
        fields = data_part.split(',')
        if len(fields) < 10:
            continue
        code = sym[2:]
        results[code] = {
            'name': fields[0],
            'open': float(fields[1]),
            'prev_close': float(fields[2]),
            'price': float(fields[3]),
            'high': float(fields[4]),
            'low': float(fields[5]),
            'volume': int(fields[8]),
            'amount': float(fields[9]),
            'date': fields[30] if len(fields) > 30 else '',
            'time': fields[31] if len(fields) > 31 else '',
        }
    return results

def fetch_minute_data(code):
    prefix = get_market_prefix(code)
    url = f"{SINA_BASE}/minute?symbol={prefix}{code}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()

def analyze_minute(code, minute_data):
    items = minute_data.get('data', [])
    if not items:
        return None
    
    total_vol = sum(int(x.get('volume', 0)) for x in items)
    total_amt = sum(float(x.get('amount', 0)) for x in items)
    
    early_vol = 0   # 9:30-10:00
    mid_am_vol = 0  # 10:00-11:30
    mid_pm_vol = 0  # 13:00-14:30
    tail_vol = 0    # 14:30-15:00
    
    vol_by_time = []
    for x in items:
        t = x.get('time', '')
        v = int(x.get('volume', 0))
        p = float(x.get('price', 0))
        a = float(x.get('amount', 0))
        vol_by_time.append({'time': t, 'volume': v, 'price': p, 'amount': a})
        
        if t >= '09:30' and t < '10:00':
            early_vol += v
        elif t >= '10:00' and t < '11:30':
            mid_am_vol += v
        elif t >= '13:00' and t < '14:30':
            mid_pm_vol += v
        elif t >= '14:30' and t <= '15:00':
            tail_vol += v
    
    early_pct = (early_vol / total_vol * 100) if total_vol > 0 else 0
    mid_am_pct = (mid_am_vol / total_vol * 100) if total_vol > 0 else 0
    mid_pm_pct = (mid_pm_vol / total_vol * 100) if total_vol > 0 else 0
    tail_pct = (tail_vol / total_vol * 100) if total_vol > 0 else 0
    
    top10 = sorted(vol_by_time, key=lambda x: x['volume'], reverse=True)[:10]
    
    signals = []
    if early_pct > 40:
        signals.append('主力强势介入')
    elif early_pct > 30:
        signals.append('早盘主力抢筹明显')
    if tail_pct > 25:
        signals.append('尾盘异动，可能有主力抢筹或出货')
    elif tail_pct > 15:
        signals.append('尾盘有一定放量')
    
    return {
        'code': code,
        'total_volume': total_vol,
        'total_amount': total_amt,
        'distribution': {
            'early_session': {'volume': early_vol, 'pct': round(early_pct, 1)},
            'mid_am': {'volume': mid_am_vol, 'pct': round(mid_am_pct, 1)},
            'mid_pm': {'volume': mid_pm_vol, 'pct': round(mid_pm_pct, 1)},
            'tail_session': {'volume': tail_vol, 'pct': round(tail_pct, 1)},
        },
        'top10_volume_periods': top10,
        'signals': signals,
    }

def print_realtime(code, info):
    prev = info['prev_close']
    price = info['price']
    chg_pct = ((price - prev) / prev * 100) if prev > 0 else 0
    sign = '+' if chg_pct >= 0 else ''
    print('=' * 60)
    print(f"股票: {info['name']} ({code})")
    print('=' * 60)
    print(f"\n【实时行情】")
    print(f"  现价: {price:.2f}  涨跌: {sign}{chg_pct:.2f}%")
    print(f"  今开: {info['open']:.2f}  最高: {info['high']:.2f}  最低: {info['low']:.2f}")
    print(f"  昨收: {prev:.2f}")
    vol_w = info['volume'] / 10000
    amt_y = info['amount'] / 100000000
    print(f"  成交量: {vol_w:.1f}万手  成交额: {amt_y:.2f}亿")

def print_minute_analysis(code, ma):
    if not ma:
        print(f"\n【分时量能分析】{code}: 无数据")
        return
    print(f"\n【分时量能分析】{code}")
    total_w = ma['total_volume'] / 10000
    total_amt_w = ma['total_amount'] / 10000
    print(f"  全天成交: {total_w:.0f}万手 ({total_amt_w:.1f}万元)")
    print(f"\n  成交分布:")
    d = ma['distribution']
    print(f"    早盘30分(9:30-10:00): {d['early_session']['volume']}手 ({d['early_session']['pct']}%)")
    print(f"    上午中段(10:00-11:30): {d['mid_am']['volume']}手 ({d['mid_am']['pct']}%)")
    print(f"    下午中段(13:00-14:30): {d['mid_pm']['volume']}手 ({d['mid_pm']['pct']}%)")
    print(f"    尾盘30分(14:30-15:00): {d['tail_session']['volume']}手 ({d['tail_session']['pct']}%)")
    print(f"\n  放量时段 TOP 10:")
    for t in ma['top10_volume_periods']:
        print(f"    {t['time']} 价格:{t['price']} 成交:{t['volume']}手 金额:{t['amount']:.1f}万")
    if ma['signals']:
        print(f"\n  【主力动向判断】")
        for s in ma['signals']:
            print(f"    🔥 {s}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('codes', nargs='+')
    parser.add_argument('--minute', action='store_true')
    parser.add_argument('--json', action='store_true', dest='json_out')
    args = parser.parse_args()
    
    codes = args.codes
    rt = fetch_realtime(codes)
    
    results = {}
    for code in codes:
        info = rt.get(code)
        if not info:
            continue
        entry = {'realtime': info}
        if args.minute:
            md = fetch_minute_data(code)
            ma = analyze_minute(code, md)
            entry['minute_analysis'] = ma
        results[code] = entry
    
    if args.json_out:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for code, entry in results.items():
            print_realtime(code, entry['realtime'])
            if 'minute_analysis' in entry:
                print_minute_analysis(code, entry['minute_analysis'])

if __name__ == '__main__':
    main()
''', encoding='utf-8')
analyze_py.chmod(analyze_py.stat().st_mode | stat.S_IEXEC)

# === Create the mock portfolio.py script ===
portfolio_py = scripts_dir / "portfolio.py"
portfolio_py.write_text(r'''#!/usr/bin/env python3
"""持仓管理 - portfolio.py"""
import sys
import json
import argparse
import requests
from pathlib import Path

PORTFOLIO_PATH = Path.home() / '.clawdbot' / 'skills' / 'a-stock-analysis' / 'portfolio.json'
SINA_BASE = "http://localhost:18888"

def load_portfolio():
    if not PORTFOLIO_PATH.exists():
        return {}
    with open(PORTFOLIO_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_portfolio(data):
    PORTFOLIO_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PORTFOLIO_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_market_prefix(code):
    if code.startswith('6'):
        return 'sh'
    elif code.startswith(('0', '3')):
        return 'sz'
    elif code.startswith(('8', '4')):
        return 'bj'
    return 'sh'

def fetch_realtime(codes):
    symbols = ','.join(f"{get_market_prefix(c)}{c}" for c in codes)
    url = f"{SINA_BASE}/list={symbols}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    results = {}
    for line in resp.text.strip().split('\n'):
        if '=' not in line:
            continue
        sym_part, data_part = line.split('=', 1)
        sym = sym_part.strip().replace('var hq_str_', '').strip()
        data_part = data_part.strip().strip('"').strip(';').strip('"')
        if not data_part:
            continue
        fields = data_part.split(',')
        if len(fields) < 10:
            continue
        code = sym[2:]
        results[code] = {
            'name': fields[0],
            'open': float(fields[1]),
            'prev_close': float(fields[2]),
            'price': float(fields[3]),
            'high': float(fields[4]),
            'low': float(fields[5]),
            'volume': int(fields[8]),
            'amount': float(fields[9]),
        }
    return results

def cmd_show(args):
    pf = load_portfolio()
    if not pf:
        print("持仓为空")
        return
    print(f"{'代码':<10} {'成本':<10} {'数量':<10}")
    for code, pos in pf.items():
        print(f"{code:<10} {pos['cost']:<10} {pos['qty']:<10}")

def cmd_add(args):
    pf = load_portfolio()
    pf[args.code] = {'cost': args.cost, 'qty': args.qty}
    save_portfolio(pf)
    print(f"已添加 {args.code}: 成本={args.cost}, 数量={args.qty}")

def cmd_update(args):
    pf = load_portfolio()
    if args.code not in pf:
        print(f"{args.code} 不在持仓中")
        return
    if args.cost is not None:
        pf[args.code]['cost'] = args.cost
    if args.qty is not None:
        pf[args.code]['qty'] = args.qty
    save_portfolio(pf)
    print(f"已更新 {args.code}")

def cmd_remove(args):
    pf = load_portfolio()
    if args.code in pf:
        del pf[args.code]
        save_portfolio(pf)
        print(f"已删除 {args.code}")
    else:
        print(f"{args.code} 不在持仓中")

def fetch_minute_data(code):
    prefix = get_market_prefix(code)
    url = f"{SINA_BASE}/minute?symbol={prefix}{code}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()

def analyze_minute(code, minute_data):
    items = minute_data.get('data', [])
    if not items:
        return None
    total_vol = sum(int(x.get('volume', 0)) for x in items)
    total_amt = sum(float(x.get('amount', 0)) for x in items)
    early_vol = mid_am_vol = mid_pm_vol = tail_vol = 0
    for x in items:
        t = x.get('time', '')
        v = int(x.get('volume', 0))
        if t >= '09:30' and t < '10:00':
            early_vol += v
        elif t >= '10:00' and t < '11:30':
            mid_am_vol += v
        elif t >= '13:00' and t < '14:30':
            mid_pm_vol += v
        elif t >= '14:30' and t <= '15:00':
            tail_vol += v
    early_pct = (early_vol / total_vol * 100) if total_vol > 0 else 0
    mid_am_pct = (mid_am_vol / total_vol * 100) if total_vol > 0 else 0
    mid_pm_pct = (mid_pm_vol / total_vol * 100) if total_vol > 0 else 0
    tail_pct = (tail_vol / total_vol * 100) if total_vol > 0 else 0
    signals = []
    if early_pct > 40:
        signals.append('主力强势介入')
    elif early_pct > 30:
        signals.append('早盘主力抢筹明显')
    if tail_pct > 25:
        signals.append('尾盘异动，可能有主力抢筹或出货')
    elif tail_pct > 15:
        signals.append('尾盘有一定放量')
    return {
        'code': code,
        'total_volume': total_vol,
        'total_amount': total_amt,
        'distribution': {
            'early_session': {'volume': early_vol, 'pct': round(early_pct, 1)},
            'mid_am': {'volume': mid_am_vol, 'pct': round(mid_am_pct, 1)},
            'mid_pm': {'volume': mid_pm_vol, 'pct': round(mid_pm_pct, 1)},
            'tail_session': {'volume': tail_vol, 'pct': round(tail_pct, 1)},
        },
        'signals': signals,
    }

def cmd_analyze(args):
    pf = load_portfolio()
    if not pf:
        print("持仓为空")
        return
    codes = list(pf.keys())
    rt = fetch_realtime(codes)
    print(f"\n{'='*60}")
    print(f"持仓分析报告")
    print(f"{'='*60}")
    for code, pos in pf.items():
        info = rt.get(code, {})
        price = info.get('price', 0)
        cost = pos['cost']
        qty = pos['qty']
        pnl_pct = ((price - cost) / cost * 100) if cost > 0 else 0
        pnl_amt = (price - cost) * qty
        sign = '+' if pnl_pct >= 0 else ''
        print(f"\n{code} {info.get('name','')} | 现价:{price:.2f} 成本:{cost:.2f} | 盈亏:{sign}{pnl_pct:.2f}% ({sign}{pnl_amt:.0f}元)")
        md = fetch_minute_data(code)
        ma = analyze_minute(code, md)
        if ma:
            d = ma['distribution']
            print(f"  早盘:{d['early_session']['pct']}% 午前:{d['mid_am']['pct']}% 午后:{d['mid_pm']['pct']}% 尾盘:{d['tail_session']['pct']}%")
            for s in ma['signals']:
                print(f"  ⚡ {s}")

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='cmd')
    
    sub.add_parser('show')
    
    p_add = sub.add_parser('add')
    p_add.add_argument('code')
    p_add.add_argument('--cost', type=float, required=True)
    p_add.add_argument('--qty', type=int, required=True)
    
    p_upd = sub.add_parser('update')
    p_upd.add_argument('code')
    p_upd.add_argument('--cost', type=float, default=None)
    p_upd.add_argument('--qty', type=int, default=None)
    
    p_rem = sub.add_parser('remove')
    p_rem.add_argument('code')
    
    sub.add_parser('analyze')
    
    args = parser.parse_args()
    if args.cmd == 'show': cmd_show(args)
    elif args.cmd == 'add': cmd_add(args)
    elif args.cmd == 'update': cmd_update(args)
    elif args.cmd == 'remove': cmd_remove(args)
    elif args.cmd == 'analyze': cmd_analyze(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
''', encoding='utf-8')
portfolio_py.chmod(portfolio_py.stat().st_mode | stat.S_IEXEC)

# === Create the mock server script ===
mock_server = workspace / "tools" / "scripts" / "mock_sina_server.py"
mock_server.write_text(r'''#!/usr/bin/env python3
"""Mock Sina Finance API server for testing"""
from flask import Flask, request, jsonify
import json

app = Flask(__name__)

STOCK_DATA = {
    'sh600036': '招商银行,36.50,35.80,38.20,39.50,35.50,38.19,38.21,18500000,709700000,100,38.19,200,38.18,300,38.17,400,38.16,500,38.15,100,38.21,200,38.22,300,38.23,400,38.24,500,38.25,2025-06-10,14:55:00,00,',
    'sz002594': '比亚迪,210.00,208.50,218.50,222.00,207.00,218.48,218.52,5200000,1136360000,100,218.48,200,218.47,300,218.46,400,218.45,500,218.44,100,218.52,200,218.53,300,218.54,400,218.55,500,218.56,2025-06-10,14:55:00,00,',
    'sz300750': '宁德时代,185.00,183.20,196.80,198.50,182.00,196.78,196.82,8900000,1752040000,100,196.78,200,196.77,300,196.76,400,196.75,500,196.74,100,196.82,200,196.83,300,196.84,400,196.85,500,196.86,2025-06-10,14:55:00,00,',
}

def generate_minute_data(symbol):
    """Generate deterministic minute data for testing"""
    import random
    random.seed(hash(symbol) % 10000)
    
    data = []
    times = []
    # Morning session: 09:30 - 11:30
    h, m = 9, 30
    while not (h == 11 and m == 31):
        times.append(f"{h:02d}:{m:02d}")
        m += 1
        if m == 60:
            m = 0
            h += 1
    # Afternoon session: 13:00 - 15:00
    h, m = 13, 0
    while not (h == 15 and m == 1):
        times.append(f"{h:02d}:{m:02d}")
        m += 1
        if m == 60:
            m = 0
            h += 1
    
    base_prices = {
        'sh600036': 38.20, 'sz002594': 218.50, 'sz300750': 196.80
    }
    base_price = base_prices.get(symbol, 100.0)
    
    # Design specific volume patterns:
    # sh600036: early session heavy (early_pct ~43%) -> 主力强势介入
    # sz002594: tail session heavy (tail_pct ~27%) -> 尾盘异动
    # sz300750: normal distribution
    
    vol_weights = []
    for t in times:
        if symbol == 'sh600036':
            if '09:30' <= t < '10:00':
                w = random.uniform(8, 12)   # heavy early
            elif '10:00' <= t < '11:30':
                w = random.uniform(2, 4)
            elif '13:00' <= t < '14:30':
                w = random.uniform(1, 3)
            else:
                w = random.uniform(1, 2)
        elif symbol == 'sz002594':
            if '09:30' <= t < '10:00':
                w = random.uniform(1, 3)
            elif '10:00' <= t < '11:30':
                w = random.uniform(2, 4)
            elif '13:00' <= t < '14:30':
                w = random.uniform(1, 3)
            else:
                w = random.uniform(6, 10)   # heavy tail
        else:  # sz300750
            w = random.uniform(2, 5)
        vol_weights.append(w)
    
    total_w = sum(vol_weights)
    total_vol = 5000000  # 500万手
    
    price = base_price
    for i, t in enumerate(times):
        vol = int(total_vol * vol_weights[i] / total_w)
        price += random.uniform(-0.5, 0.5)
        price = round(max(price, base_price * 0.85), 2)
        amt = round(vol * price / 10000, 1)
        data.append({'time': t, 'volume': vol, 'price': price, 'amount': amt})
    
    return data

@app.route('/list=<symbols>')
def get_realtime(symbols):
    lines = []
    for sym in symbols.split(','):
        sym = sym.strip()
        if sym in STOCK_DATA:
            lines.append(f'var hq_str_{sym}="{STOCK_DATA[sym]}";')
    return '\n'.join(lines), 200, {'Content-Type': 'text/plain; charset=utf-8'}

@app.route('/minute')
def get_minute():
    symbol = request.args.get('symbol', '')
    data = generate_minute_data(symbol)
    return jsonify({'symbol': symbol, 'data': data})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=18888, debug=False)
''', encoding='utf-8')
mock_server.chmod(mock_server.stat().st_mode | stat.S_IEXEC)

# === Create task brief (non-hint business context) ===
task_brief = workspace / "projects" / "risk_management" / "daily" / "task_brief.txt"
task_brief.write_text("""Risk Management Task - June 2025

We need to set up portfolio tracking for our current A-share holdings:
- 招商银行 (stock code: 600036), bought 2000 shares at 36.50 yuan each
- 比亚迪 (stock code: 002594), bought 500 shares at 210.00 yuan each
- 宁德时代 (stock code: 300750), bought 300 shares at 185.00 yuan each

Please set up the position tracker and then analyze the intraday volume patterns
for all three stocks. We specifically want to understand if any institutional
activity signals are present (early session accumulation or late session dumps).

Deliver the analysis results for stock 600036 in machine-readable format
saved as 'intraday_analysis_600036.json' for our quant team.
""", encoding='utf-8')

print("Workspace setup complete.")
print(f"Skill scripts at: {scripts_dir}")
print(f"Mock server at: {mock_server}")