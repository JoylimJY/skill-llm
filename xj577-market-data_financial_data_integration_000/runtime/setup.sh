#!/bin/bash
set -e

# Start a local mock market data server that implements the skill's API
cat << 'PYEOF' > /tmp/mock_market_server.py
import json
import random
from flask import Flask, request, jsonify
from datetime import datetime, timedelta

random.seed(99)
app = Flask(__name__)

@app.route('/get_stock_price', methods=['POST'])
def get_stock_price():
    data = request.get_json()
    ticker = data.get('ticker', '')
    timeframe = data.get('timeframe', '1d')
    period1 = data.get('period1', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    period2 = data.get('period2', datetime.now().strftime('%Y-%m-%d'))

    # Validate timeframe - only accept exact supported values
    if timeframe not in ['1d', '1wk', '1mo']:
        return jsonify({"error": f"Unsupported timeframe: {timeframe}. Supported: '1d', '1wk', '1mo'"}), 400

    # Generate deterministic OHLCV records
    start = datetime.strptime(period1, '%Y-%m-%d')
    end = datetime.strptime(period2, '%Y-%m-%d')
    records = []
    current = start
    step = timedelta(days=7) if timeframe == '1wk' else (timedelta(days=30) if timeframe == '1mo' else timedelta(days=1))
    price = 500.0
    while current <= end:
        open_p = round(price + random.uniform(-10, 10), 2)
        high_p = round(open_p + random.uniform(0, 15), 2)
        low_p = round(open_p - random.uniform(0, 15), 2)
        close_p = round((open_p + high_p + low_p) / 3, 2)
        volume = random.randint(10000000, 50000000)
        records.append({
            "date": current.strftime('%Y-%m-%d'),
            "open": open_p,
            "high": high_p,
            "low": low_p,
            "close": close_p,
            "volume": volume
        })
        price = close_p
        current += step

    return jsonify({
        "ticker": ticker,
        "timeframe": timeframe,
        "period1": period1,
        "period2": period2,
        "data": records
    })

@app.route('/get_crypto_price', methods=['POST'])
def get_crypto_price():
    data = request.get_json()
    token = data.get('token', '')
    currency = data.get('currency', 'usd')

    # Map valid token names (must be full names, not tickers)
    valid_tokens = {
        'bitcoin': {'name': 'Bitcoin', 'base_price_usd': 65000},
        'ethereum': {'name': 'Ethereum', 'base_price_usd': 3200},
        'solana': {'name': 'Solana', 'base_price_usd': 140},
        'cardano': {'name': 'Cardano', 'base_price_usd': 0.45},
    }
    # Reject ticker-style inputs
    rejected_tickers = ['btc', 'eth', 'sol', 'ada', 'BTC', 'ETH', 'SOL', 'ADA', 'NVDA']
    if token.lower() in [r.lower() for r in rejected_tickers]:
        return jsonify({"error": f"Invalid token '{token}'. Use full token name (e.g., 'ethereum', not 'ETH')"}), 400

    if token.lower() not in valid_tokens:
        return jsonify({"error": f"Token '{token}' not found. Use full name like 'ethereum', 'bitcoin'."}), 404

    token_info = valid_tokens[token.lower()]
    fx_rates = {'usd': 1.0, 'eur': 0.92, 'gbp': 0.79, 'jpy': 149.5}
    rate = fx_rates.get(currency.lower(), 1.0)
    price = round(token_info['base_price_usd'] * rate, 2)
    change_24h = round(random.uniform(-5.0, 5.0), 2)
    volatility_24h = round(abs(change_24h) + random.uniform(0.5, 2.0), 2)

    return jsonify({
        "token": token.lower(),
        "name": token_info['name'],
        "currency": currency.lower(),
        "price": price,
        "change_24h_pct": change_24h,
        "volatility_24h_pct": volatility_24h
    })

@app.route('/fetch_economic_calendar', methods=['POST'])
def fetch_economic_calendar():
    data = request.get_json()
    importance = data.get('importance', 'High')
    currencies_raw = data.get('currencies', '')

    # Validate importance - must be exact casing
    valid_importance = ['High', 'Medium', 'Low', 'All']
    if importance not in valid_importance:
        return jsonify({"error": f"Invalid importance '{importance}'. Must be one of: {valid_importance}"}), 400

    all_events = [
        {"event": "US CPI YoY", "currency": "USD", "importance": "High", "date": "2024-04-10", "forecast": "3.4%", "previous": "3.2%"},
        {"event": "FOMC Meeting Minutes", "currency": "USD", "importance": "High", "date": "2024-04-10", "forecast": None, "previous": None},
        {"event": "ECB Interest Rate Decision", "currency": "EUR", "importance": "High", "date": "2024-04-11", "forecast": "4.50%", "previous": "4.50%"},
        {"event": "US Initial Jobless Claims", "currency": "USD", "importance": "Medium", "date": "2024-04-11", "forecast": "215K", "previous": "221K"},
        {"event": "UK GDP MoM", "currency": "GBP", "importance": "High", "date": "2024-04-12", "forecast": "0.1%", "previous": "-0.1%"},
        {"event": "Germany Industrial Production", "currency": "EUR", "importance": "Medium", "date": "2024-04-09", "forecast": "0.3%", "previous": "-1.5%"},
        {"event": "US PPI MoM", "currency": "USD", "importance": "High", "date": "2024-04-11", "forecast": "0.3%", "previous": "0.6%"},
        {"event": "Japan Tankan Survey", "currency": "JPY", "importance": "High", "date": "2024-04-01", "forecast": "11", "previous": "13"},
    ]

    filtered = all_events
    if importance != 'All':
        filtered = [e for e in filtered if e['importance'] == importance]

    if currencies_raw:
        currency_list = [c.strip().upper() for c in currencies_raw.split(',')]
        filtered = [e for e in filtered if e['currency'].upper() in currency_list]

    return jsonify({
        "importance_filter": importance,
        "currencies_filter": currencies_raw if currencies_raw else "All",
        "events": filtered
    })

@app.route('/get_news_headlines', methods=['POST'])
def get_news_headlines():
    data = request.get_json()
    query = data.get('query', '')
    headlines = [
        f"[{query}] Markets rally on strong earnings data",
        f"[{query}] Analysts upgrade outlook amid economic resilience",
        f"[{query}] Institutional investors increase exposure",
        f"[{query}] Regulatory scrutiny weighs on sentiment",
        f"[{query}] Technical breakout signals continued momentum",
    ]
    return jsonify({"query": query, "headlines": headlines})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8765, debug=False)
PYEOF

# Start mock server in background
python3 /tmp/mock_market_server.py &
MOCK_PID=$!
echo "Mock server PID: $MOCK_PID"

# Wait for server to be ready
for i in $(seq 1 15); do
    if curl -s http://localhost:8765/health > /dev/null 2>&1; then
        echo "Mock server is up."
        break
    fi
    echo "Waiting for mock server... ($i)"
    sleep 1
done

# Write skill tools as callable scripts in /workspace/scripts/
cat << 'SKILLEOF' > /workspace/scripts/get_stock_price.sh
#!/bin/bash
# Usage: ./get_stock_price.sh '{"ticker": "NVDA", "timeframe": "1wk", "period1": "2024-01-01", "period2": "2024-03-31"}'
curl -s -X POST http://localhost:8765/get_stock_price \
  -H "Content-Type: application/json" \
  -d "$1"
SKILLEOF

cat << 'SKILLEOF' > /workspace/scripts/get_crypto_price.sh
#!/bin/bash
# Usage: ./get_crypto_price.sh '{"token": "ethereum", "currency": "eur"}'
curl -s -X POST http://localhost:8765/get_crypto_price \
  -H "Content-Type: application/json" \
  -d "$1"
SKILLEOF

cat << 'SKILLEOF' > /workspace/scripts/fetch_economic_calendar.sh
#!/bin/bash
# Usage: ./fetch_economic_calendar.sh '{"importance": "High", "currencies": "USD"}'
curl -s -X POST http://localhost:8765/fetch_economic_calendar \
  -H "Content-Type: application/json" \
  -d "$1"
SKILLEOF

cat << 'SKILLEOF' > /workspace/scripts/get_news_headlines.sh
#!/bin/bash
# Usage: ./get_news_headlines.sh '{"query": "Nvidia Earnings"}'
curl -s -X POST http://localhost:8765/get_news_headlines \
  -H "Content-Type: application/json" \
  -d "$1"
SKILLEOF

chmod +x /workspace/scripts/*.sh

# Write a SKILL.md into workspace for agent reference
cat << 'MDEOF' > /workspace/SKILL.md
# Market Data Skill

This skill provides access to financial market data.

## Tools

### `get_stock_price`

Fetches OHLCV (Open, High, Low, Close, Volume) data for a specific ticker.

**Parameters:**

- `ticker` (string): The stock symbol (e.g., "AAPL", "BTC-USD").
- `timeframe` (string): The data interval. Supported: '1d', '1wk', '1mo'. Default: '1d'.
- `period1` (string, optional): Start date in YYYY-MM-DD format. Defaults to 30 days ago.
- `period2` (string, optional): End date in YYYY-MM-DD format. Defaults to today.

**Usage:**

Use this tool when the user asks for stock prices, historical data, chart data, or recent performance of a specific asset.

**Examples:**

- "Get daily data for Apple." -> `get_stock_price({ ticker: 'AAPL', timeframe: '1d' })`
- "Show me Bitcoin's weekly chart for the last year." -> `get_stock_price({ ticker: 'BTC-USD', timeframe: '1wk', period1: '2023-01-01' })`

### `get_crypto_price`

Fetches current price and 24h volatility data for a crypto token.

**Parameters:**

- `token` (string): The token name or ID (e.g., "bitcoin", "solana", "ethereum").
- `currency` (string, optional): Target currency. Default: "usd".

**Usage:**

Use this for checking crypto prices, volatility, and 24h changes.

**Examples:**

- "Price of Solana?" -> `get_crypto_price({ token: 'solana' })`
- "How is Bitcoin doing?" -> `get_crypto_price({ token: 'bitcoin' })`

### `fetch_economic_calendar`

Fetches upcoming high-impact economic events (e.g., CPI, FOMC, GDP).

**Parameters:**

- `importance` (string, optional): Impact level filter. 'High', 'Medium', 'Low', 'All'. Default: 'High'.
- `currencies` (string, optional): Comma-separated currency codes (e.g., 'USD,EUR'). Default: All.

**Usage:**

Use this to check for market-moving news or schedule risk.

**Examples:**

- "Any high impact news this week?" -> `fetch_economic_calendar({ importance: 'High' })`
- "Check USD and EUR calendar." -> `fetch_economic_calendar({ currencies: 'USD,EUR' })`

### `get_news_headlines`

Fetches the latest 50 news headlines for a specific asset or topic.

**Parameters:**

- `query` (string): The search topic (e.g., "Apple Stock", "Bitcoin Regulation", "Nvidia Earnings").

**Usage:**

Use this for sentiment analysis and staying updated on market narratives.

**Examples:**

- "Any news on Tesla?" -> `get_news_headlines({ query: 'Tesla Stock' })`
- "Latest crypto regulation updates?" -> `get_news_headlines({ query: 'Crypto Regulation' })`
MDEOF

echo "Setup complete."