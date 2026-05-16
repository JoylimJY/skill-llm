#!/bin/bash
set -e

echo "=== Setting up mock HTTP server for market.ft.tech and ftai.chat ==="

# Write the mock server script
cat > /tmp/mock_api_server.py << 'MOCKEOF'
#!/usr/bin/env python3
"""
Mock HTTP server intercepting calls to market.ft.tech and ftai.chat.
Runs on port 8899. /etc/hosts redirects the two domains here.
All sub-skill scripts use https://, but we patch requests globally
via sitecustomize.py so they hit http://localhost:8899 instead.
"""
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# ── Mock data ─────────────────────────────────────────────────────────────────
MOCK_TRADE_DATE = {"nth_trade_date": "2025-01-08"}

# Page 1 (50 records simulated, but we send 3 here for total=3 in test)
# The stock with HIGHEST margin_balance is 601398.SH (工商银行) = 15800000000
# This is intentionally NOT the one in the distractor files (600036.SH)
# to ensure the agent actually calls the API and doesn't use cached data.

MARGIN_PAGE1 = {
    "total": 3,
    "page": 1,
    "page_size": 50,
    "data": [
        {
            "symbol": "601398.SH",
            "name": "工商银行",
            "margin_balance": 15800000000,
            "margin_buy": 320000000,
            "margin_repay": 180000000,
            "net_margin_buy": 140000000,
            "short_balance": 8000000
        },
        {
            "symbol": "600036.SH",
            "name": "招商银行",
            "margin_balance": 9500000000,
            "margin_buy": 120000000,
            "margin_repay": 80000000,
            "net_margin_buy": 40000000,
            "short_balance": 5000000
        },
        {
            "symbol": "000001.SZ",
            "name": "平安银行",
            "margin_balance": 4200000000,
            "margin_buy": 85000000,
            "margin_repay": 60000000,
            "net_margin_buy": 25000000,
            "short_balance": 3000000
        }
    ]
}

SECURITY_INFO = {
    "601398.SH": {
        "symbol": "601398.SH",
        "name": "工商银行",
        "price": 6.28,
        "pe_ttm": 5.42,
        "pb": 0.61,
        "market_cap": 2230000000000,
        "change_rate": 0.0048,
        "eps": 1.16
    }
}

# ── Routes ────────────────────────────────────────────────────────────────────
@app.route('/app/trade-date/nth')
def trade_date_nth():
    n = request.args.get('n', '1')
    return jsonify(MOCK_TRADE_DATE)

@app.route('/app/margin-trading/details')
def margin_trading():
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))
    # Return page 1 data regardless (total=3, fits in one page)
    return jsonify(MARGIN_PAGE1)

@app.route('/app/stock/security-info')
def security_info():
    symbol = request.args.get('symbol', '')
    if symbol in SECURITY_INFO:
        return jsonify(SECURITY_INFO[symbol])
    return jsonify({"error": f"Symbol not found: {symbol}"}), 404

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8899, debug=False)
MOCKEOF

chmod +x /tmp/mock_api_server.py

# Start the mock server in background
python3 /tmp/mock_api_server.py &
MOCK_PID=$!
echo "Mock server started with PID $MOCK_PID on port 8899"

# Wait for mock server to be ready
sleep 2
curl -sf http://localhost:8899/health && echo "Mock server is healthy" || echo "WARNING: Mock server health check failed"

# Write sitecustomize.py to intercept requests calls
# Find site-packages directory
SITE_PACKAGES=$(python3 -c "import site; print(site.getsitepackages()[0])")
echo "Site-packages: $SITE_PACKAGES"

cat > "$SITE_PACKAGES/sitecustomize.py" << 'SITEEOF'
"""
Intercept HTTP(S) calls to market.ft.tech and ftai.chat,
redirect them to the local mock server at http://localhost:8899.
This works by monkey-patching requests.Session.request at import time.
"""
import sys

def _patch_requests():
    try:
        import requests
        from requests import Session
        _original_request = Session.request

        TARGET_HOSTS = {"market.ft.tech", "ftai.chat"}

        def _patched_request(self, method, url, **kwargs):
            from urllib.parse import urlparse, urlunparse
            parsed = urlparse(url)
            if parsed.hostname in TARGET_HOSTS:
                # Rewrite to local mock
                new_url = urlunparse((
                    "http",
                    "localhost:8899",
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment
                ))
                # Disable SSL verification (not needed for HTTP)
                kwargs.pop('verify', None)
                return _original_request(self, method, new_url, **kwargs)
            return _original_request(self, method, url, **kwargs)

        Session.request = _patched_request
    except ImportError:
        pass

_patch_requests()
SITEEOF

echo "sitecustomize.py written to $SITE_PACKAGES"
echo "=== Setup complete ==="

# Verify the interception works
python3 -c "
import requests
r = requests.get('https://market.ft.tech/health')
print('Interception test:', r.status_code, r.json())
"