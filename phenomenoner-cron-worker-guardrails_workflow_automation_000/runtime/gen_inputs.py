import os
import random
import textwrap

random.seed(42)

WORKSPACE = "/workspace"

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "tools",
    "references",
    "config",
    "logs",
    "data/raw",
    "data/processed",
    "reports/daily",
    "reports/weekly",
    "scripts/legacy",
    "scripts/archive",
    "tests",
    ".git/refs",  # minimal fake git skeleton
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── fake git initialisation ─────────────────────────────────────────────────
os.system(f"cd {WORKSPACE} && git init -q && git config user.email 'ci@openclaw.io' && git config user.name 'CI Bot'")

# ── distractor files ────────────────────────────────────────────────────────
distractors = {
    "config/db.conf": "[database]\nhost=localhost\nport=5432\nname=analytics\n",
    "config/alerts.yaml": "slack_webhook: null\nemail: ops@example.com\nthreshold: 0.05\n",
    "data/raw/prices_2024_01.csv": "date,symbol,close\n2024-01-02,AAPL,185.20\n2024-01-03,AAPL,184.10\n",
    "data/raw/prices_2024_02.csv": "date,symbol,close\n2024-02-01,AAPL,186.30\n2024-02-02,AAPL,187.00\n",
    "data/processed/summary_jan.json": '{"month":"2024-01","avg_close":184.65,"records":2}\n',
    "reports/daily/2024_01_03.txt": "Daily report: AAPL avg 184.65\n",
    "reports/weekly/week01.txt": "Weekly digest: stable\n",
    "logs/cron_2024_01.log": "2024-01-02 02:00:01 INFO job started\n2024-01-02 02:00:03 ERROR SIGPIPE\n",
    "logs/cron_2024_02.log": "2024-02-01 02:00:01 INFO job started\n2024-02-01 02:00:02 OK\n",
    "tests/test_placeholder.py": "def test_noop():\n    pass\n",
    "scripts/archive/old_nightly.sh": "#!/bin/bash\n# deprecated\nexit 0\n",
    "scripts/legacy/push_wrapper_v1.sh": "#!/bin/bash\ngit push origin main\n",
}
for path, content in distractors.items():
    full = os.path.join(WORKSPACE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)

# ── THE PROBLEM FILE 1: broken cron wrapper (brittle quoting, no silent-on-success) ──
# This file represents what is currently "in production" — it is deliberately broken.
broken_cron_wrapper = textwrap.dedent("""\
    #!/bin/bash
    # Nightly market-data summary job
    # BROKEN: runs inline python logic with nested quoting
    bash -lc 'cd /home/deploy/analytics && python3 -c "
    import csv, json, os
    rows = list(csv.DictReader(open(\\"data/raw/prices_2024_01.csv\\")))
    avg = sum(float(r[\\"close\\"]) for r in rows) / len(rows)
    print(json.dumps({\\"avg_close\\": round(avg,2), \\"records\\": len(rows)}))
    " > data/processed/summary.json'
    echo "Job finished"
""")
with open(os.path.join(WORKSPACE, "scripts/nightly_summary.sh"), "w") as f:
    f.write(broken_cron_wrapper)
os.chmod(os.path.join(WORKSPACE, "scripts/nightly_summary.sh"), 0o755)

# ── THE PROBLEM FILE 2: pipefail + head SIGPIPE false-failure script ────────
broken_pipeline_script = textwrap.dedent("""\
    #!/bin/bash
    # Extracts the top price record for alerting
    set -euo pipefail

    TOP=$(cat data/raw/prices_2024_01.csv | sort -t',' -k3 -rn | head -1)
    echo "Top record: $TOP"
    echo "Alert sent"
""")
with open(os.path.join(WORKSPACE, "scripts/top_price_alert.sh"), "w") as f:
    f.write(broken_pipeline_script)
os.chmod(os.path.join(WORKSPACE, "scripts/top_price_alert.sh"), 0o755)

# ── THE PROBLEM FILE 3: git push automation with no rejection handling ───────
broken_git_push = textwrap.dedent("""\
    #!/bin/bash
    # Pushes the generated summary report to the feature branch
    # BROKEN: no handling for non-fast-forward rejection
    git add data/processed/summary.json
    git commit -m "nightly: update summary report"
    git push origin feature/nightly-reports
    echo "Push complete"
""")
with open(os.path.join(WORKSPACE, "scripts/push_report.sh"), "w") as f:
    f.write(broken_git_push)
os.chmod(os.path.join(WORKSPACE, "scripts/push_report.sh"), 0o755)

# ── references directory: minimal contract stub (agent must read skill) ──────
contract_stub = textwrap.dedent("""\
    # cron-agent-contract (stub)
    # Full rules are defined in the cron-worker-guardrails skill.
    # Key: scripts-first, deterministic cwd, silent-on-success.
""")
with open(os.path.join(WORKSPACE, "references/cron-agent-contract.md"), "w") as f:
    f.write(contract_stub)

pitfalls_stub = textwrap.dedent("""\
    # pitfalls (stub)
    # See cron-worker-guardrails skill for full list.
""")
with open(os.path.join(WORKSPACE, "references/pitfalls.md"), "w") as f:
    f.write(pitfalls_stub)

print("Workspace generated successfully.")