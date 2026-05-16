import os
import random
import textwrap

random.seed(42)

workspace = "/workspace"

# ── directory skeleton ────────────────────────────────────────────────────────
dirs = [
    ".github/workflows",
    "skills/github-actions-workflow-hardening-audit/scripts",
    "skills/github-actions-workflow-hardening-audit/fixtures",
    "src/payments/core",
    "src/payments/gateway",
    "src/fraud/detector",
    "src/compliance/reporting",
    "infra/terraform/modules",
    "infra/k8s/overlays",
    "docs/runbooks",
    "tests/integration",
    "tests/unit",
    "scripts/deploy",
    "scripts/db-migrations",
    ".github/ISSUE_TEMPLATE",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── distractor files ──────────────────────────────────────────────────────────
distractors = {
    "src/payments/core/processor.py": "# Payment processor core\nclass Processor: pass\n",
    "src/payments/gateway/stripe.py": "# Stripe gateway adapter\n",
    "src/fraud/detector/rules.py": "RULES = []\n",
    "src/compliance/reporting/sox.py": "# SOX reporting module\n",
    "infra/terraform/modules/vpc.tf": 'resource "aws_vpc" "main" { cidr_block = "10.0.0.0/16" }\n',
    "infra/k8s/overlays/production.yaml": "apiVersion: kustomize.config.k8s.io/v1beta1\nkind: Kustomization\n",
    "docs/runbooks/incident-response.md": "# Incident Response\nSee playbook v2.\n",
    "tests/integration/test_payments.py": "def test_payment(): assert True\n",
    "tests/unit/test_fraud.py": "def test_fraud_rule(): assert True\n",
    "scripts/deploy/rollout.sh": "#!/bin/bash\necho 'deploy'\n",
    "scripts/db-migrations/migrate.py": "# DB migration runner\n",
    ".github/ISSUE_TEMPLATE/bug_report.md": "## Bug Report\n",
}
for path, content in distractors.items():
    with open(os.path.join(workspace, path), "w") as f:
        f.write(content)

# ── workflow YAML files ───────────────────────────────────────────────────────
# These are crafted so the scoring changes meaningfully with non-default params.

workflows = {}

# 1. ci-pr.yml  — triggered on pull_request
#    Issues: no timeout on one job, no permissions, floating ref @main, no concurrency
#    Score with defaults (REQUIRE_CONCURRENCY=0): timeout(1) + permissions(1) + floating-ref(2) = 4  → warn
#    Score with REQUIRE_CONCURRENCY=1: +1 = 5  → critical (if CRITICAL_SCORE=5)
workflows["ci-pr.yml"] = textwrap.dedent("""\
    name: CI Pull Request
    on:
      pull_request:
        branches: [main]
    jobs:
      lint:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: actions/setup-python@main
            with:
              python-version: "3.11"
          - run: pip install flake8 && flake8 src/
      test:
        runs-on: ubuntu-latest
        timeout-minutes: 20
        steps:
          - uses: actions/checkout@v4
          - run: pytest tests/unit
""")

# 2. deploy-staging.yml — triggered on push to develop
#    Issues: no timeout anywhere, no permissions, floating @master, no concurrency
#    Score default: 1+1+2 = 4 → warn; +concurrency = 5 → critical (CRITICAL_SCORE=5)
workflows["deploy-staging.yml"] = textwrap.dedent("""\
    name: Deploy Staging
    on:
      push:
        branches: [develop]
    jobs:
      deploy:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: hashicorp/setup-terraform@master
          - run: terraform apply -auto-approve
          - uses: nick-fields/retry@latest
            with:
              command: ./scripts/deploy/rollout.sh
""")

# 3. security-scan.yml — triggered on pull_request_target (HIGH risk event!)
#    Issues: no timeout, no permissions, floating @v3 (major-only), no concurrency
#    Score: 1+1+1+1 = 4 default; +concurrency = 5 → critical
workflows["security-scan.yml"] = textwrap.dedent("""\
    name: Security Scan
    on:
      pull_request_target:
        branches: [main]
    jobs:
      snyk:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: snyk/actions/python@v3
            env:
              SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
          - uses: github/codeql-action/analyze@v3
""")

# 4. release.yml — triggered on release published
#    Issues: no concurrency only; has timeout, has permissions, pinned ref sha → score 0
#    Should be EXCLUDED by EVENT_EXCLUDE=release
workflows["release.yml"] = textwrap.dedent("""\
    name: Release
    on:
      release:
        types: [published]
    permissions:
      contents: write
      packages: write
    jobs:
      publish:
        runs-on: ubuntu-latest
        timeout-minutes: 30
        steps:
          - uses: actions/checkout@abc1234def5678901234567890abcdef12345678
          - run: python3 -m build
          - run: twine upload dist/*
""")

# 5. scheduled-compliance.yml — triggered on schedule (cron)
#    Issues: no timeout on compliance-report job, permissions only at job level for audit job,
#            floating @v4 (major-only), no concurrency
#    Score: timeout(1) + workflow-perms-missing(but job has perms, still flagged at workflow level?) 
#    Actually no workflow-level permissions, no concurrency, floating ref → 1+1+1+1=4 default; +concurrency=5→critical
workflows["scheduled-compliance.yml"] = textwrap.dedent("""\
    name: Scheduled Compliance Check
    on:
      schedule:
        - cron: '0 2 * * 1'
    jobs:
      audit:
        runs-on: ubuntu-latest
        timeout-minutes: 45
        permissions:
          security-events: write
        steps:
          - uses: actions/checkout@v4
          - uses: ossf/scorecard-action@v4
            with:
              results_format: json
      compliance-report:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - run: python3 src/compliance/reporting/sox.py
""")

# 6. dependabot-auto-merge.yml — triggered on pull_request
#    Issues: no timeout, no permissions, floating @latest, no concurrency
#    Score: 1+1+1+1=4 default; +concurrency=5→critical
workflows["dependabot-auto-merge.yml"] = textwrap.dedent("""\
    name: Dependabot Auto Merge
    on:
      pull_request:
    jobs:
      auto-merge:
        runs-on: ubuntu-latest
        steps:
          - uses: dependabot/fetch-metadata@latest
          - uses: pascalgn/automerge-action@latest
            env:
              GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
""")

# 7. docs-deploy.yml — triggered on push to main
#    Has workflow-level permissions and timeout, one floating ref @v4 (major), no concurrency
#    Score default: floating(1) = 1 → ok; +concurrency = 2 → warn (WARN_SCORE=2)
workflows["docs-deploy.yml"] = textwrap.dedent("""\
    name: Deploy Docs
    on:
      push:
        branches: [main]
    permissions:
      contents: read
      pages: write
      id-token: write
    concurrency:
      group: pages
      cancel-in-progress: true
    jobs:
      deploy:
        runs-on: ubuntu-latest
        timeout-minutes: 15
        steps:
          - uses: actions/checkout@v4
          - uses: actions/configure-pages@v4
          - uses: actions/deploy-pages@abc9876def1234567890abcdef1234567890abcd
""")

# 8. fraud-model-train.yml — triggered on push to ml-branch + schedule
#    Has everything: permissions, timeout, concurrency, pinned SHA refs
#    Score: 0 → ok regardless of flags
workflows["fraud-model-train.yml"] = textwrap.dedent("""\
    name: Fraud Model Training
    on:
      push:
        branches: [ml-experiments]
      schedule:
        - cron: '0 6 * * *'
    permissions:
      contents: read
    concurrency:
      group: ml-train-${{ github.ref }}
      cancel-in-progress: false
    jobs:
      train:
        runs-on: ubuntu-latest
        timeout-minutes: 120
        steps:
          - uses: actions/checkout@abc1111def2222ghi3333jkl4444mno5555pqr66
          - run: python3 src/fraud/detector/rules.py
""")

for fname, content in workflows.items():
    with open(os.path.join(workspace, ".github/workflows", fname), "w") as f:
        f.write(content)

# ── write a stub audit-report placeholder so agent knows the target filename ──
# (we do NOT write the actual report; agent must produce it)
# Nothing here — agent must discover the output filename from the prompt.

print("Workspace generated successfully.")
print(f"Workflows created: {list(workflows.keys())}")