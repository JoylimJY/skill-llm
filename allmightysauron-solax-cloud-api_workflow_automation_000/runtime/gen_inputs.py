import os
import json
import random
import string

random.seed(42)

workspace = "/home/openclaw/workspace"
os.makedirs(workspace, exist_ok=True)

# ─── Create the skill directory structure ───────────────────────────────────
skill_root = os.path.join(workspace, "skills", "solax-summary-fetch")
scripts_dir = os.path.join(skill_root, "scripts")
refs_dir = os.path.join(skill_root, "references")
os.makedirs(scripts_dir, exist_ok=True)
os.makedirs(refs_dir, exist_ok=True)

# package.json (no lockfile shipped — agent must use `npm install` not `npm ci`)
package_json = {
    "name": "solax-summary-fetch-scripts",
    "version": "1.0.0",
    "type": "module",
    "dependencies": {
        "solax-cloud-api": "^0.2.0"
    }
}
with open(os.path.join(scripts_dir, "package.json"), "w") as f:
    json.dump(package_json, f, indent=2)

# fetch_summary.mjs  — the actual skill script the agent will invoke
# Uses SOLAX_API_BASE env var to allow local mock override
fetch_summary_mjs = r"""#!/usr/bin/env node
import { SolaxCloudAPI } from 'solax-cloud-api';

// Parse CLI args: --tokenId <val> --sn <val>
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

// Confirm tokenId is set (redacted)
process.stderr.write(`tokenId set: ${'*'.repeat(8)}\n`);

// Allow base URL override for local mocking
const baseUrl = process.env.SOLAX_API_BASE ?? 'https://www.solaxcloud.com';

try {
  const api = new SolaxCloudAPI(tokenId, sn, { baseUrl });
  const raw = await api.getAPIData();
  const summary = SolaxCloudAPI.toSummary(raw);
  console.log(JSON.stringify(summary));
} catch (err) {
  console.log(JSON.stringify({ ok: false, error: err.message ?? String(err) }));
}
"""
with open(os.path.join(scripts_dir, "fetch_summary.mjs"), "w") as f:
    f.write(fetch_summary_mjs)

# TypeScript declaration file for SolaxSummary
solax_summary_dts = """export interface SolaxSummary {
  ok: boolean;
  sn: string;
  inverterType: string;
  powerdc1: number;
  powerdc2: number;
  acpower: number;
  yieldtoday: number;
  yieldtotal: number;
  feedinpower: number;
  feedinenergy: number;
  consumeenergy: number;
  soc: number;
  peps1: number;
  peps2: number;
  peps3: number;
  batPower: number;
  uploadTime: string;
}
"""
with open(os.path.join(refs_dir, "solax-summary.d.ts"), "w") as f:
    f.write(solax_summary_dts)

# ─── Distractor files ────────────────────────────────────────────────────────
distractors = [
    ("skills/weather-fetch/scripts/package.json",
     json.dumps({"name": "weather-fetch", "version": "0.1.0", "dependencies": {"axios": "^1.0.0"}}, indent=2)),
    ("skills/weather-fetch/scripts/fetch_weather.mjs",
     "import axios from 'axios';\nconsole.log('weather stub');\n"),
    ("skills/solax-summary-fetch/config/legacy_config.json",
     json.dumps({"endpoint": "https://old.solaxcloud.com/api", "version": "v1", "deprecated": True}, indent=2)),
    ("skills/solax-summary-fetch/config/staging.env.example",
     "SOLAX_TOKENID=YOUR_TOKEN_HERE\nSOLAX_SN=YOUR_SERIAL_HERE\nSOLAX_API_BASE=http://localhost:8765\n"),
    ("logs/inverter_errors_2024.log",
     "2024-01-03 08:12:00 ERROR connection timeout sn=SVXXXXXXXXX\n2024-01-03 09:00:00 INFO reconnected\n"),
    ("logs/deploy.log",
     "2024-06-01 deploy skill solax-summary-fetch v1.2\n2024-06-01 deploy skill weather-fetch v0.3\n"),
    ("dashboards/solar_dashboard_config.json",
     json.dumps({"title": "Solar Farm Alpha", "refresh_interval": 60, "inverters": ["SV12345678", "SV87654321"]}, indent=2)),
    ("dashboards/archived/old_dashboard.json",
     json.dumps({"title": "OLD Solar Dashboard (deprecated)", "inverters": []}, indent=2)),
    ("automation/pipeline_config.yaml",
     "steps:\n  - fetch_inverter_summary\n  - push_to_influxdb\n  - alert_if_low_soc\n"),
    ("automation/cron_jobs.txt",
     "*/5 * * * * /home/openclaw/workspace/run_fetch.sh >> /tmp/cron.log 2>&1\n"),
    ("skills/solax-summary-fetch/scripts/old_fetch.js",
     "// DEPRECATED: use fetch_summary.mjs instead\nconst request = require('request');\n// ...\n"),
    ("tmp/scratch_notes.txt",
     "TODO: verify tokenId rotation policy\nCheck if sn format is case-sensitive (it is)\n"),
]

for rel_path, content in distractors:
    full_path = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# ─── Credentials file the agent can discover ────────────────────────────────
# Stored in a plausible location; agent must find and use them
creds = {
    "tokenId": "tok-ALPHA-20240601-XK99",
    "sn": "SV12345678"
}
creds_path = os.path.join(workspace, "config", "inverter_creds.json")
os.makedirs(os.path.dirname(creds_path), exist_ok=True)
with open(creds_path, "w") as f:
    json.dump(creds, f, indent=2)

print("Workspace generated successfully.")
print(f"Credentials written to: {creds_path}")