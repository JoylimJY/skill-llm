#!/usr/bin/env python3
import os
import stat
import textwrap
from pathlib import Path

WORKSPACE = Path("/workspace")

# ── 1. Initialise a fake git repository ────────────────────────────────────────
os.system("git -C /workspace init -b main")
os.system("git -C /workspace config user.email 'dev_UBER@uber.com'")
os.system("git -C /workspace config user.name 'Dev UBER'")

# Create a realistic monorepo skeleton
dirs = [
    "src/payments/gateway",
    "src/payments/logging",
    "src/auth/oauth",
    "src/users/profile",
    "infra/k8s/payments",
    "infra/terraform/networking",
    "tools/lint",
    "tools/coverage",
    "docs/runbooks",
    "tests/integration/payments",
    "tests/unit/auth",
    ".github/workflows",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

distractor_files = {
    "src/payments/gateway/handler.go":        "package gateway\n\nfunc Handle() {}\n",
    "src/payments/gateway/handler_test.go":   "package gateway\n\nfunc TestHandle(t *testing.T) {}\n",
    "src/payments/logging/logger.go":         "package logging\n\nfunc Log(msg string) {}\n",
    "src/auth/oauth/token.go":                "package oauth\n\nfunc Refresh() {}\n",
    "src/users/profile/service.go":           "package profile\n\nfunc Get() {}\n",
    "infra/k8s/payments/deployment.yaml":     "apiVersion: apps/v1\nkind: Deployment\n",
    "infra/terraform/networking/main.tf":     'terraform {}\nresource "aws_vpc" "main" {}\n',
    "tools/lint/.golangci.yml":               "linters:\n  enable:\n    - govet\n",
    "tools/coverage/threshold.txt":           "80\n",
    "docs/runbooks/payments-oncall.md":       "# Payments On-Call Runbook\n\nSee wiki.\n",
    "tests/integration/payments/suite_test.go": "package payments_test\n",
    "tests/unit/auth/token_test.go":          "package auth\n",
    ".github/workflows/ci.yml":               "name: CI\non: [push]\n",
    "go.mod":                                 'module github.com/uber-code/go-code\n\ngo 1.21\n',
    "WORKSPACE":                              '# Bazel WORKSPACE\n',
}

for relpath, content in distractor_files.items():
    p = WORKSPACE / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

os.system("git -C /workspace add -A")
os.system("git -C /workspace commit -m 'chore: initial monorepo scaffold'")

# ── 2. Pre-create some closed/merged feature stubs to simulate a messy tree ────
#    The agent should NOT need to interact with these; they are distractors.
for old_branch in ["old-refactor-auth", "stale-migration-v2"]:
    os.system(f"git -C /workspace checkout -b {old_branch}")
    (WORKSPACE / f"src/auth/{old_branch}.go").write_text(f"// {old_branch}\n")
    os.system(f"git -C /workspace add -A")
    os.system(f"git -C /workspace commit -m 'feat: {old_branch} (stale)'")
    os.system(f"git -C /workspace checkout main")

# Return to main
os.system("git -C /workspace checkout main")

# ── 3. Drop a messy notes file that hints at *what* is needed but NOT how ──────
notes = textwrap.dedent("""\
    TEAM NOTES — Payment Stack Sprint
    ===================================
    We need to land two related changes as part of the payment gateway overhaul:

      1) payment-gateway  — core gateway routing changes
      2) payment-logging  — structured logging layer (depends on #1)

    Both PRs should go up TODAY as WIPs (not ready for review yet).
    Push should be fully non-interactive (CI context).

    After pushing, sync from main and make sure the build graph is
    refreshed (important for this monorepo!).

    Then rebase the whole stack on top of the refreshed main.

    Finally, push updates for the stack again — this time skip the
    coverage gate (it is broken in CI right now).

    Once everything is merged/closed, tidy the branch tree automatically
    (no manual confirmation).
""")
(WORKSPACE / "TEAM_NOTES.txt").write_text(notes)

# ── 4. Write an arh_invocations.log stub (empty) so eval can always open it ────
(WORKSPACE / "arh_invocations.log").write_text("")
(WORKSPACE / "git_bzl_invocations.log").write_text("")

print("gen_inputs_script: workspace prepared.")