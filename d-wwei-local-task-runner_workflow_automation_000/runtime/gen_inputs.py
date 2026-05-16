import os
import random
import json
import csv

random.seed(42)

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "skills/local-task-runner",
    "skills/local-task-runner/lib",
    "data/raw/trades",
    "data/raw/metadata",
    "data/processed",
    "reports/drafts",
    "reports/archive",
    "config",
    "logs",
    "tmp",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ── the local-task-runner skill (bespoke implementation) ────────────────────
runner_index = r"""
const { program } = require('commander');
const { execSync } = require('child_process');
const crypto = require('crypto');
const fs = require('fs');
const os = require('os');
const path = require('path');

program
  .command('run')
  .option('--code <code>', 'Node.js code to execute')
  .option('--timeout <ms>', 'Timeout in milliseconds', '10000')
  .action((opts) => {
    const taskId = crypto.randomBytes(4).toString('hex').toUpperCase();
    const timeout = parseInt(opts.timeout, 10);
    const start = Date.now();

    const tmpFile = path.join(os.tmpdir(), `task_${taskId}.js`);
    fs.writeFileSync(tmpFile, opts.code);

    try {
      const result = execSync(`node ${tmpFile}`, {
        timeout,
        encoding: 'utf8',
      });
      const elapsed = Date.now() - start;
      console.log(`[TASK: ${taskId}] Completed in ${elapsed}ms`);
      console.log('--- STDOUT ---');
      process.stdout.write(result);
    } catch (err) {
      const elapsed = Date.now() - start;
      console.log(`[TASK: ${taskId}] Failed in ${elapsed}ms`);
      console.log(`Error: ${err.message}`);
      console.log('--- STDERR ---');
      if (err.stderr) process.stderr.write(err.stderr);
      process.exit(1);
    } finally {
      try { fs.unlinkSync(tmpFile); } catch(_) {}
    }
  });

program.parse(process.argv);
"""
with open("skills/local-task-runner/index.js", "w") as f:
    f.write(runner_index)

# install commander for the runner
os.system("cd skills/local-task-runner && npm init -y > /dev/null 2>&1 && npm install commander > /dev/null 2>&1")

# ── distractor files ────────────────────────────────────────────────────────
distractors = {
    "config/db_config.json": json.dumps({"host": "localhost", "port": 5432, "db": "analytics"}),
    "config/pipeline.yaml": "version: 2\nsteps:\n  - ingest\n  - normalize\n  - report\n",
    "logs/pipeline_2024-01-10.log": "INFO  pipeline started\nINFO  12340 rows ingested\nWARN  3 duplicates skipped\nINFO  pipeline finished\n",
    "logs/pipeline_2024-01-11.log": "INFO  pipeline started\nERROR connection timeout after 30s\n",
    "tmp/scratch.txt": "DELETE ME\ntemporary workspace notes\n",
    "reports/drafts/q1_summary_draft.txt": "Draft Q1 Report - NOT FINAL\nTotal trades: TBD\n",
    "reports/archive/q4_2023.json": json.dumps({"quarter": "Q4-2023", "total_return_pct": 4.21}),
    "data/raw/metadata/instruments.csv": "symbol,sector,currency\nAAPL,Technology,USD\nMSFT,Technology,USD\nJPM,Finance,USD\nXOM,Energy,USD\n",
    "data/processed/.gitkeep": "",
    "skills/local-task-runner/lib/utils.js": "// placeholder utility\nmodule.exports = {};\n",
    "data/raw/metadata/holidays_2024.txt": "2024-01-01\n2024-07-04\n2024-12-25\n",
}
for path_, content in distractors.items():
    with open(path_, "w") as f:
        f.write(content)

# ── messy trade data CSV ────────────────────────────────────────────────────
# Fields: trade_id, symbol, side (BUY/SELL/ whitespace noise), quantity, price, commission
# Intentionally messy: blank lines, extra whitespace, some rows with comment prefix '#',
# duplicate header mid-file, mixed case sides, missing commission (defaults to 0)

trades = [
    ["trade_id", "symbol", "side", "quantity", "price", "commission"],
    ["T001", "AAPL", "BUY",  "100", "150.00", "1.50"],
    ["T002", "AAPL", "SELL", "50",  "155.00", "0.75"],
    ["T003", "MSFT", "BUY",  "200", "280.00", "2.00"],
    ["T004", "MSFT", " sell","200", "295.00", "2.00"],
    ["T005", "JPM",  "buy",  "300", "130.00", "3.00"],
    ["T006", "JPM",  "SELL", "150", "128.00", "1.50"],
    ["T007", "XOM",  "BUY",  "400", "60.00",  "4.00"],
    ["T008", "XOM",  "SELL", "400", "63.50",  "4.00"],
    ["T009", "AAPL", "BUY",  "75",  "152.00", ""],      # missing commission → 0
    ["T010", "MSFT", "SELL", "100", "290.00", "1.00"],
    ["T011", "JPM",  "BUY",  "200", "135.00", "2.00"],
    ["T012", "XOM",  "SELL", "200", "65.00",  "2.00"],
]

raw_csv_lines = []
raw_csv_lines.append(",".join(trades[0]))          # header
raw_csv_lines.append("")                            # blank line noise
for i, row in enumerate(trades[1:], 1):
    raw_csv_lines.append(",".join(row))
    if i == 6:
        raw_csv_lines.append("# mid-file comment — ignore")
        raw_csv_lines.append(",".join(trades[0]))  # duplicate header mid-file (noise)
        raw_csv_lines.append("")

with open("data/raw/trades/trades_2024_Q1.csv", "w") as f:
    f.write("\n".join(raw_csv_lines) + "\n")

print("Workspace generated successfully.")
print("Trade CSV written to: data/raw/trades/trades_2024_Q1.csv")