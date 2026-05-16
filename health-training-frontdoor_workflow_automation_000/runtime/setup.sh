#!/usr/bin/env bash
set -e

WORKSPACE="/workspace"

# Create the mock request.js that simulates the front door
# It parses the JSON argument and returns deterministic mock responses
# based on the action field and optional parameters.

cat > "$WORKSPACE/skills/health-training-frontdoor/scripts/request.js" << 'JSEOF'
#!/usr/bin/env node
"use strict";

const arg = process.argv[2];
if (!arg) {
  process.stderr.write(JSON.stringify({"error": "No JSON argument provided"}) + "\n");
  process.exit(1);
}

let req;
try {
  req = JSON.parse(arg);
} catch(e) {
  process.stderr.write(JSON.stringify({"error": "Invalid JSON: " + e.message}) + "\n");
  process.exit(1);
}

const action = req.action;
const days = req.days !== undefined ? req.days : null;
const ensureFresh = req.ensureFresh !== undefined ? req.ensureFresh : null;
const source = req.source !== undefined ? req.source : null;

// Record what was actually called for eval verification
const callRecord = {action, days, ensureFresh, source};
const fs = require('fs');
let history = [];
const histPath = '/workspace/tmp/call_history.jsonl';
try { history = fs.existsSync(histPath) ? fs.readFileSync(histPath,'utf8').trim().split('\n').filter(Boolean).map(JSON.parse) : []; } catch(e) { history = []; }
history.push(callRecord);
fs.writeFileSync(histPath, history.map(r => JSON.stringify(r)).join('\n') + '\n');

const responses = {
  auth_status: () => ({
    "status":"authenticated",
    "token_valid":true,
    "expires_in_seconds":86342,
    "user":"joao_fitbit_primary"
  }),

  latest_recovery: () => {
    const d = days !== null ? days : 3;
    const ef = ensureFresh !== null ? ensureFresh : true;
    const records = [];
    for (let i = 0; i < d; i++) {
      records.push({
        "date": `2024-03-0${4 - i}`,
        "hrv_rmssd": 42.1 + i * 1.3,
        "resting_hr": 52 - i,
        "sleep_minutes": 430 + i * 10,
        "sleep_score": 77 + i,
        "data_quality": "good"
      });
    }
    return {"action":"latest_recovery","days":d,"ensureFresh":ef,"records":records};
  },

  quality_flags: () => {
    const d = days !== null ? days : 7;
    return {"action":"quality_flags","days":d,"flags":{"low_battery":false,"sync_gap":false,"sensor_dropout":true,"days_checked":d}};
  },

  training_status: () => {
    const d = days !== null ? days : 14;
    const ef = ensureFresh !== null ? ensureFresh : true;
    return {"action":"training_status","days":d,"ensureFresh":ef,"status":"nominal","load_trend":"stable","readiness_score":81};
  },

  training_window: () => {
    const d = days !== null ? days : 14;
    const ef = ensureFresh !== null ? ensureFresh : true;
    const sessions = [];
    for (let i = 0; i < Math.min(d, 6); i++) {
      sessions.push({"date":`2024-03-0${4-i < 10 ? '0'+(4-i) : 4-i}`,"type":"strength","load":70+i*3,"rpe":7+Math.round(i*0.5)});
    }
    return {"action":"training_window","days":d,"ensureFresh":ef,"sessions":sessions,"window_days":d};
  },

  unified_latest: () => {
    const d = days !== null ? days : 14;
    const src = source !== null ? source : "best";
    return {
      "action":"unified_latest",
      "days":d,
      "source":src,
      "hrv_rmssd":44.2,
      "resting_hr":51,
      "sleep_score":79,
      "readiness":83,
      "load_7d":68,
      "load_28d":71
    };
  }
};

if (!responses[action]) {
  process.stderr.write(JSON.stringify({"error":"Unknown action: " + action}) + "\n");
  process.exit(1);
}

// Output compact JSON (no pretty print, as per SKILL.md)
process.stdout.write(JSON.stringify(responses[action]()) + "\n");
JSEOF

chmod +x "$WORKSPACE/skills/health-training-frontdoor/scripts/request.js"
mkdir -p "$WORKSPACE/tmp"
touch "$WORKSPACE/tmp/call_history.jsonl"

echo "Mock request.js installed and ready."