#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="/home/openclaw/workspace"
SKILL_DIR="$WORKSPACE/skills/solax-summary-fetch/scripts"

# ─── Patch fetch_summary.mjs to work with solax-cloud-api's actual API shape ─
# The real solax-cloud-api@0.2.0 may differ; we replace the script with one
# that uses a hand-rolled HTTP call against our mock, conforming to SolaxSummary.
cat > "$SKILL_DIR/fetch_summary.mjs" << 'ENDOFSCRIPT'
#!/usr/bin/env node
// fetch_summary.mjs — solax-summary-fetch skill

const args = process.argv.slice(2);
function getArg(name) {
  const idx = args.indexOf(name);
  return idx !== -1 ? args[idx + 1] : undefined;
}

const tokenId = getArg('--tokenId') ?? process.env.SOLAX_TOKENID;
const sn      = getArg('--sn')      ?? process.env.SOLAX_SN;

if (!tokenId || !sn) {
  console.log(JSON.stringify({ ok: false, error: 'Missing tokenId or sn' }));
  process.exit(0);
}

// Redact tokenId from logs
process.stderr.write('tokenId set: ********\n');

const baseUrl = process.env.SOLAX_API_BASE ?? 'https://www.solaxcloud.com';
const url = `${baseUrl}/proxyApp/proxy/api/getRealtimeInfo.do?tokenId=${encodeURIComponent(tokenId)}&sn=${encodeURIComponent(sn)}`;

try {
  const res = await fetch(url);
  if (!res.ok) {
    console.log(JSON.stringify({ ok: false, error: `HTTP ${res.status}` }));
    process.exit(0);
  }
  const data = await res.json();
  if (!data.success) {
    console.log(JSON.stringify({ ok: false, error: data.exception ?? 'API returned success=false' }));
    process.exit(0);
  }
  const r = data.result;
  // toSummary() mapping
  const summary = {
    ok: true,
    sn: r.sn,
    inverterType: r.inverterType,
    powerdc1: r.powerdc1,
    powerdc2: r.powerdc2,
    acpower: r.acpower,
    yieldtoday: r.yieldtoday,
    yieldtotal: r.yieldtotal,
    feedinpower: r.feedinpower,
    feedinenergy: r.feedinenergy,
    consumeenergy: r.consumeenergy,
    soc: r.soc,
    peps1: r.peps1,
    peps2: r.peps2,
    peps3: r.peps3,
    batPower: r.batPower,
    uploadTime: r.uploadTime
  };
  console.log(JSON.stringify(summary));
} catch (err) {
  console.log(JSON.stringify({ ok: false, error: err.message ?? String(err) }));
}
ENDOFSCRIPT

chmod +x "$SKILL_DIR/fetch_summary.mjs"

# ─── Start local mock HTTP server for Solax Cloud API ────────────────────────
MOCK_PORT=8765
MOCK_RESPONSE='{
  "success": true,
  "exception": "Query success!",
  "result": {
    "sn": "SV12345678",
    "inverterType": "X1-Hybrid-G4",
    "powerdc1": 1820.5,
    "powerdc2": 940.2,
    "acpower": 2650.0,
    "yieldtoday": 18.4,
    "yieldtotal": 4321.7,
    "feedinpower": 120.3,
    "feedinenergy": 88.6,
    "consumeenergy": 210.5,
    "soc": 73,
    "peps1": 0.0,
    "peps2": 0.0,
    "peps3": 0.0,
    "batPower": -350.0,
    "uploadTime": "2024-06-01 10:30:00"
  }
}'

python3 - << PYEOF &
import http.server, json, urllib.parse, os

RESPONSE = json.loads(r'''$MOCK_RESPONSE''')

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(RESPONSE).encode())
    def log_message(self, fmt, *args):
        pass  # silence

srv = http.server.HTTPServer(('127.0.0.1', $MOCK_PORT), Handler)
srv.serve_forever()
PYEOF

MOCK_PID=$!
echo "$MOCK_PID" > /tmp/mock_server.pid
echo "Mock Solax API server started on port $MOCK_PORT (PID $MOCK_PID)"

# Write the mock base URL to a discoverable env hint file
echo "http://127.0.0.1:${MOCK_PORT}" > /home/openclaw/workspace/config/mock_api_base.txt

# Give the server a moment to start
sleep 1
echo "Setup complete."