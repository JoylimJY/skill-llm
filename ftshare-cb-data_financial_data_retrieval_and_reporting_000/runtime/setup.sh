#!/usr/bin/env bash
set -e

WORKSPACE="${WORKSPACE:-/workspace}"

# ── Start the mock Flask server in the background ───────────────────────────
cat > /tmp/mock_server.py << 'PYEOF'
#!/usr/bin/env python3
"""
Mock server for FTShare-cb-data skill.
Serves deterministic, realistic A-share convertible bond data.
"""
import json
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)

# ---------- Static data -------------------------------------------------

CB_LIST = [
    {"bond_code": "110070", "bond_name": "海尔转债", "bond_full_name": "青岛海尔股份有限公司2019年公开发行可转换公司债券",
     "stock_code": "600690.SH", "exchange": "SH"},
    {"bond_code": "113050", "bond_name": "南航转债", "bond_full_name": "中国南方航空股份有限公司可转换公司债券",
     "stock_code": "600029.SH", "exchange": "SH"},
    {"bond_code": "127043", "bond_name": "赣锋转债", "bond_full_name": "赣州锋锂新能源科技股份有限公司可转换公司债券",
     "stock_code": "002460.SZ", "exchange": "SZ"},
    {"bond_code": "128093", "bond_name": "隆华转债", "bond_full_name": "隆华科技集团股份有限公司可转换公司债券",
     "stock_code": "300263.SZ", "exchange": "SZ"},
    {"bond_code": "110081", "bond_name": "华菱转债", "bond_full_name": "华菱钢铁集团股份有限公司可转换公司债券",
     "stock_code": "000932.SZ", "exchange": "SH"},
]

CB_BASE_DATA = {
    "110070": {
        "short_name": "海尔转债",
        "full_name": "青岛海尔股份有限公司2019年公开发行可转换公司债券",
        "stock_code": "600690.SH",
        "conversion_price": 17.59,
        "conversion_value": 103.24,
        "conversion_premium_rate": 0.0427,
        "value_date": "2019-09-05",
        "maturity_date": "2025-09-05",
        "issuance_scale": 2300000000.0,
        "currency": "CNY",
    },
    "113050": {
        "short_name": "南航转债",
        "full_name": "中国南方航空股份有限公司可转换公司债券",
        "stock_code": "600029.SH",
        "conversion_price": 8.45,
        "conversion_value": 91.20,
        "conversion_premium_rate": 0.0285,
        "value_date": "2020-03-18",
        "maturity_date": "2026-03-18",
        "issuance_scale": 1600000000.0,
        "currency": "CNY",
    },
}

# Deterministic trade dates (last 30, ending 2025-05-30)
import random
random.seed(42)

def generate_trade_dates():
    """Generate ~62 trading days ending around 2025-06-06"""
    dates = []
    d = datetime(2025, 6, 6)
    while len(dates) < 62:
        if d.weekday() < 5:  # Mon-Fri
            dates.append(d.strftime("%Y-%m-%d"))
        d -= timedelta(days=1)
    return list(reversed(dates))

TRADE_DATES = generate_trade_dates()

# The "current date" for nth-trade-date reference: use TRADE_DATES[-1] as today
# So front N gives TRADE_DATES[-(N+1)] ... depends on N
# nth_trade_date = TRADE_DATES[-(n+1)] for n >= 1

def get_nth_trade_date(n):
    # n=1 => yesterday's trade date = TRADE_DATES[-2]
    # n=20 => TRADE_DATES[-(20+1)] = TRADE_DATES[-21]
    if n <= 0 or n >= len(TRADE_DATES):
        return None
    return TRADE_DATES[-(n + 1)]

def make_candles(symbol_code, since_ms, until_ms):
    """Generate deterministic OHLCV candles for trade dates within window."""
    import hashlib
    candles = []
    tz_cst = pytz.timezone("Asia/Shanghai")
    base_price = 102.5
    for i, d in enumerate(TRADE_DATES):
        dt = datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=tz_cst)
        ts_ms = int(dt.timestamp() * 1000)
        if ts_ms < since_ms or ts_ms > until_ms:
            continue
        h = int(hashlib.md5(f"{symbol_code}_{d}".encode()).hexdigest(), 16)
        delta = (h % 1000 - 500) / 1000.0
        close = round(base_price + delta + i * 0.03, 2)
        open_ = round(close - (h % 100) / 200.0, 2)
        high = round(max(open_, close) + (h % 50) / 200.0, 2)
        low = round(min(open_, close) - (h % 50) / 200.0, 2)
        volume = 100000 + (h % 500000)
        candles.append({
            "date": d,
            "ts_millis": ts_ms,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        })
    return candles

# ---------- Routes -------------------------------------------------------

@app.route("/cb-lists")
def cb_lists():
    return jsonify({"code": 0, "data": CB_LIST})

@app.route("/cb-base-data")
def cb_base_data():
    sym = request.args.get("symbol_code", "")
    code = sym.split(".")[0]
    if code not in CB_BASE_DATA:
        return jsonify({"code": 404, "message": f"Symbol {sym} not found", "data": None})
    return jsonify({"code": 0, "data": CB_BASE_DATA[code]})

@app.route("/cb-candlesticks")
def cb_candlesticks():
    symbol = request.args.get("symbol", "")
    interval_unit = request.args.get("interval_unit", "Day")
    since_ms = int(request.args.get("since_ts_millis", 0))
    until_ms = int(request.args.get("until_ts_millis", 9999999999999))

    # Validate symbol format: must end with .XSHG or .XSHE
    if not (symbol.endswith(".XSHG") or symbol.endswith(".XSHE")):
        return jsonify({
            "code": 400,
            "message": f"Invalid symbol format '{symbol}'. Must use .XSHG or .XSHE suffix.",
            "data": []
        })

    code = symbol.split(".")[0]
    candles = make_candles(code, since_ms, until_ms)
    return jsonify({"code": 0, "data": candles})

@app.route("/get-nth-trade-date")
def nth_trade_date():
    n = int(request.args.get("n", 1))
    d = get_nth_trade_date(n)
    if d is None:
        return jsonify({"code": 400, "message": "n out of range", "data": None})
    return jsonify({"code": 0, "data": {"nth_trade_date": d, "n": n}})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=19527, debug=False)
PYEOF

python3 /tmp/mock_server.py &
MOCK_PID=$!
echo "Mock server started with PID $MOCK_PID"

# Wait for server to be ready
for i in $(seq 1 15); do
    if curl -sf http://127.0.0.1:19527/cb-lists > /dev/null 2>&1; then
        echo "Mock server is ready."
        break
    fi
    sleep 0.5
done

# Export environment variable so run.py picks up the mock
export FT_MOCK_BASE="http://127.0.0.1:19527"

chmod +x "${WORKSPACE}/skills/FTShare-cb-data/run.py"

echo "Setup complete."