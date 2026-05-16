import os
import json
import random

random.seed(42)

# ── create directory structure ──────────────────────────────────────────
dirs = [
    "data",
    "logs",
    "archive/2024",
    "archive/2025/q1",
    "reports/daily",
    "reports/weekly",
    "tmp/cache",
    "tmp/downloads",
    "scripts/utils",
    "scripts/analysis",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ── distractor files (≥10) ───────────────────────────────────────────────
distractors = {
    "archive/2024/market_summary.csv": "date,open,close\n20241201,3200,3210\n20241202,3210,3198\n",
    "archive/2025/q1/portfolio_snapshot.json": json.dumps({"holdings": [{"code": "600036", "shares": 500}]}),
    "reports/daily/2025_06_01.txt": "Daily PnL: +0.32%\nTop gainer: 002415\nTop loser: 601398\n",
    "reports/weekly/week22.md": "## Week 22 Summary\n- Net change: -1.2%\n- Watchlist updated\n",
    "tmp/cache/price_cache.pkl": b'\x80\x04\x95\x00\x00\x00\x00\x00\x00\x00\x00\x8c\x04test\x94.',
    "tmp/downloads/raw_ticks.csv": "ts,price\n093000,10.50\n093001,10.52\n",
    "scripts/utils/calc_macd.py": "def macd(prices): return []\n",
    "scripts/analysis/backtest.py": "# placeholder backtest script\nresult = {}\n",
    "scripts/analysis/risk_metrics.py": "def sharpe(returns): return 0.0\n",
    "logs/old_monitor_20250101_090000.log": "[monitor] started PID=9999\n[monitor] no alerts\n",
    "logs/old_monitor_20250201_090000.log": "[monitor] started PID=8888\n[monitor] alert: 000001 price moved 2.3%\n",
    "archive/2025/q1/notes.txt": "Remember to check margin ratios before open.\n",
    "tmp/stale_config_backup.json": json.dumps({"monitor_target": "user:ou_OLD_BACKUP", "interval": 10}),
}

for path, content in distractors.items():
    mode = "wb" if isinstance(content, bytes) else "w"
    with open(path, mode) as f:
        f.write(content)

# ── core skill module: config.py ────────────────────────────────────────
with open("config.py", "w") as f:
    f.write('''\
import json, os

CONFIG_PATH = os.path.join("data", "config.json")

def _load():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return {}

def _save(d):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=2)

def get(key, default=None):
    return _load().get(key, default)

def set(key, value):
    d = _load()
    d[key] = value
    _save(d)
    return d
''')

# ── core skill module: search.py ────────────────────────────────────────
STOCK_DB = [
    {"code": "000001", "name": "平安银行"},
    {"code": "600036", "name": "招商银行"},
    {"code": "000002", "name": "万科A"},
    {"code": "600519", "name": "贵州茅台"},
    {"code": "002415", "name": "海康威视"},
    {"code": "601398", "name": "工商银行"},
    {"code": "000858", "name": "五粮液"},
    {"code": "600900", "name": "长江电力"},
    {"code": "300750", "name": "宁德时代"},
    {"code": "600276", "name": "恒瑞医药"},
    {"code": "000333", "name": "美的集团"},
    {"code": "601166", "name": "兴业银行"},
]

with open("search.py", "w") as f:
    f.write(f'''\
import json

_DB = {json.dumps(STOCK_DB, ensure_ascii=False)}

def search_by_name(keyword):
    return [s for s in _DB if keyword in s["name"]]
''')

# ── core skill module: quote.py ─────────────────────────────────────────
with open("quote.py", "w") as f:
    f.write(f'''\
import json, random

_DB = {json.dumps(STOCK_DB, ensure_ascii=False)}
_MAP = {{s["code"]: s for s in _DB}}
_NMAP = {{s["name"]: s for s in _DB}}

def get_detail(code):
    if code not in _MAP:
        raise ValueError(f"股票代码不存在: {{code}}")
    s = _MAP[code]
    price = round(random.uniform(5, 200), 2)
    chg = round(random.uniform(-5, 5), 2)
    return {{
        "code": s["code"],
        "name": s["name"],
        "最新价": price,
        "涨跌幅": chg,
        "涨跌额": round(price * chg / 100, 2),
        "今开": round(price * 0.99, 2),
        "昨收": round(price * (1 - chg/100), 2),
        "最高": round(price * 1.02, 2),
        "最低": round(price * 0.98, 2),
        "成交量": random.randint(10000, 500000),
        "成交额": random.randint(10000000, 5000000000),
        "总市值": random.randint(10000000000, 3000000000000),
        "市盈率TTM": round(random.uniform(5, 80), 2),
        "52周最高": round(price * 1.3, 2),
        "52周最低": round(price * 0.7, 2),
    }}

def get_detail_by_name(name):
    matches = [s for s in _DB if s["name"] == name]
    if len(matches) == 0:
        raise ValueError(f"未找到股票: {{name}}")
    if len(matches) > 1:
        raise ValueError(f"名称匹配多只股票，请用代码查询: {{matches}}")
    return get_detail(matches[0]["code"])
''')

# ── core skill module: watchlist.py ─────────────────────────────────────
with open("watchlist.py", "w") as f:
    f.write('''\
import json, os
from quote import get_detail, get_detail_by_name
from monitor import is_running

WL_PATH = os.path.join("data", "watchlist.json")

def _load():
    if os.path.exists(WL_PATH):
        with open(WL_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return []

def _save(lst):
    os.makedirs(os.path.dirname(WL_PATH), exist_ok=True)
    with open(WL_PATH, "w", encoding="utf-8") as fh:
        json.dump(lst, fh, ensure_ascii=False, indent=2)

def _status():
    return "监控已启动" if is_running() else "监控未启动"

def list_all():
    return _load()

def add(code_or_name):
    lst = _load()
    # determine code
    if len(code_or_name) == 6 and code_or_name.isdigit():
        detail = get_detail(code_or_name)
        code = detail["code"]
        name = detail["name"]
    else:
        detail = get_detail_by_name(code_or_name)
        code = detail["code"]
        name = detail["name"]
    for item in lst:
        if item["code"] == code:
            return {"code": code, "name": name, "monitor_status": _status()}
    lst.append({"code": code, "name": name})
    _save(lst)
    return {"code": code, "name": name, "monitor_status": _status()}

def remove(code_or_name):
    lst = _load()
    if len(code_or_name) == 6 and code_or_name.isdigit():
        target = code_or_name
        match_fn = lambda item: item["code"] == target
    else:
        match_fn = lambda item: item["name"] == code_or_name
    new_lst = [item for item in lst if not match_fn(item)]
    removed = [item for item in lst if match_fn(item)]
    if not removed:
        return None
    _save(new_lst)
    r = removed[0]
    return {"code": r["code"], "name": r["name"], "monitor_status": _status()}

def clear():
    lst = _load()
    count = len(lst)
    _save([])
    return {"cleared": count, "monitor_status": _status()}
''')

# ── core skill module: monitor.py ───────────────────────────────────────
with open("monitor.py", "w") as f:
    f.write('''\
import os, json, sys, subprocess, time

PID_FILE = os.path.join("data", "monitor.pid")
PARAMS_FILE = os.path.join("data", "monitor_params.json")

def is_running():
    if not os.path.exists(PID_FILE):
        return False
    with open(PID_FILE) as f:
        pid = int(f.read().strip())
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False

def start_monitor(target=None, interval=10, threshold=2.0):
    import config as cfg
    if target is None:
        target = cfg.get("monitor_target")
    if target is None:
        raise RuntimeError("未配置 monitor_target，请先调用 config.set()")
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    params = {"target": target, "interval": interval, "threshold": threshold}
    with open(PARAMS_FILE, "w") as f:
        json.dump(params, f, indent=2)
    # write a simple background worker
    worker_code = """
import time, json, os, sys
params = json.load(open(sys.argv[1]))
pid_file = sys.argv[2]
with open(pid_file, "w") as f:
    f.write(str(os.getpid()))
# keep running
while True:
    time.sleep(3600)
"""
    worker_path = os.path.join("data", "_monitor_worker.py")
    with open(worker_path, "w") as f:
        f.write(worker_code)
    proc = subprocess.Popen(
        [sys.executable, worker_path, PARAMS_FILE, PID_FILE],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
    )
    time.sleep(0.3)
    ts = time.strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join("logs", f"monitor_{ts}.log")
    print(f"[monitor] 监控子进程已启动  PID={proc.pid}  日志→ {log_path}")

def stop_monitor():
    if not os.path.exists(PID_FILE):
        print("[monitor] 未发现运行中的监控进程")
        return
    with open(PID_FILE) as f:
        pid = int(f.read().strip())
    try:
        import signal
        os.kill(pid, signal.SIGTERM)
        print(f"[monitor] 已停止 PID={pid}")
    except Exception as e:
        print(f"[monitor] 停止失败: {e}")
    os.remove(PID_FILE)

def restart_monitor():
    stop_monitor()
    time.sleep(0.5)
    start_monitor()
''')

# ── intentionally leave data/config.json absent (agent must create it) ─
# ── intentionally leave data/watchlist.json absent ─────────────────────

print("Workspace initialized.")