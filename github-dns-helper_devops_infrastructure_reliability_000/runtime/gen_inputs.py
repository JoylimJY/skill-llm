import os
import stat
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── 1. Create a realistic skill directory structure ──────────────────────────
skill_path = workspace / "skills" / "github-dns-helper"
scripts_dir = skill_path / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

# ── 2. Create the actual fix_github_dns.py script ───────────────────────────
fix_script = scripts_dir / "fix_github_dns.py"
fix_script.write_text(r'''#!/usr/bin/env python3
"""GitHub DNS 修复助手 - 解决 GitHub 访问问题"""
import argparse
import platform
import re
import sys
import urllib.request
import urllib.error
import socket
from pathlib import Path
from datetime import datetime

DEFAULT_HOSTS_URL = "https://raw.hellogithub.com/hosts"
HOSTS_FILE = "/etc/hosts"
MARKER_START = "# GitHub DNS Fix - START"
MARKER_END = "# GitHub DNS Fix - END"

GITHUB_DOMAINS = [
    "github.com",
    "api.github.com",
    "assets-cdn.github.com",
    "raw.githubusercontent.com",
    "gist.github.com",
    "github.global.ssl.fastly.net",
    "github-releases.githubusercontent.com",
    "codeload.github.com",
    "objects.githubusercontent.com",
]


def check_connection():
    """Check connectivity to GitHub domains."""
    print("=== GitHub Connectivity Check ===")
    results = {}
    for domain in GITHUB_DOMAINS:
        try:
            ip = socket.gethostbyname(domain)
            results[domain] = {"status": "ok", "ip": ip}
            print(f"  [OK]  {domain} -> {ip}")
        except socket.gaierror as e:
            results[domain] = {"status": "fail", "error": str(e)}
            print(f"  [FAIL] {domain} -> {e}")
    ok_count = sum(1 for r in results.values() if r["status"] == "ok")
    print(f"\nResult: {ok_count}/{len(GITHUB_DOMAINS)} domains reachable")
    return results


def fetch_hosts_content(url):
    """Fetch hosts content from URL."""
    print(f"Fetching hosts data from: {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "github-dns-helper/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8", errors="replace")
        print(f"  Downloaded {len(content)} bytes")
        return content
    except Exception as e:
        print(f"  ERROR fetching hosts: {e}", file=sys.stderr)
        sys.exit(1)


def parse_github_entries(raw_content):
    """Parse and extract only GitHub-related host entries."""
    entries = []
    for line in raw_content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 2:
            ip, hostname = parts[0], parts[1]
            if any(gh in hostname for gh in ["github", "githubusercontent", "githubassets", "githubstatus"]):
                entries.append(f"{ip}  {hostname}")
    return entries


def read_hosts():
    try:
        return Path(HOSTS_FILE).read_text(encoding="utf-8")
    except PermissionError:
        print(f"ERROR: No permission to read {HOSTS_FILE}.", file=sys.stderr)
        print("Run the permission fix commands from SKILL.md first.", file=sys.stderr)
        sys.exit(2)


def write_hosts(content):
    try:
        Path(HOSTS_FILE).write_text(content, encoding="utf-8")
    except PermissionError:
        print(f"ERROR: No permission to write {HOSTS_FILE}.", file=sys.stderr)
        print("Run the permission fix commands from SKILL.md first.", file=sys.stderr)
        sys.exit(2)


def update_hosts_file(entries):
    """Update /etc/hosts with new GitHub entries."""
    current = read_hosts()

    # Remove existing GitHub DNS Fix block if present
    pattern = re.compile(
        rf"{re.escape(MARKER_START)}.*?{re.escape(MARKER_END)}\n?",
        re.DOTALL
    )
    cleaned = pattern.sub("", current).rstrip("\n") + "\n"

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    block_lines = [
        MARKER_START,
        f"# Updated: {timestamp}",
        f"# Entries: {len(entries)}",
    ] + entries + [MARKER_END]

    new_content = cleaned + "\n" + "\n".join(block_lines) + "\n"
    write_hosts(new_content)
    print(f"  Updated {HOSTS_FILE} with {len(entries)} GitHub entries.")
    return len(entries)


def main():
    parser = argparse.ArgumentParser(
        description="GitHub DNS 修复助手 - Fix GitHub DNS resolution issues"
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Only check GitHub connectivity, do not modify hosts"
    )
    parser.add_argument(
        "-u", "--url", default=DEFAULT_HOSTS_URL,
        help=f"Custom hosts source URL (default: {DEFAULT_HOSTS_URL})"
    )
    args = parser.parse_args()

    print(f"OS: {platform.system()}")

    if args.check:
        check_connection()
        return

    print(f"\n=== GitHub DNS Auto-Fix ===")
    raw = fetch_hosts_content(args.url)
    entries = parse_github_entries(raw)

    if not entries:
        print("WARNING: No GitHub entries found in the fetched hosts file.", file=sys.stderr)
        sys.exit(3)

    count = update_hosts_file(entries)
    print(f"\nDone. {count} GitHub host entries written to {HOSTS_FILE}.")
    print("Re-run with --check to verify connectivity.")


if __name__ == "__main__":
    main()
''')
fix_script.chmod(0o755)

# ── 3. Distractor files in skill directory ───────────────────────────────────
(skill_path / "README.broken").write_text("# OUTDATED - do not use\nThis file is deprecated.")
(skill_path / "config.bak").write_text("# backup config - ignore\nversion=0.1\nurl=https://old-url.example.com/hosts")
(skill_path / "logs").mkdir(exist_ok=True)
(skill_path / "logs" / "run_20231101.log").write_text("2023-11-01 ERROR: timeout\n2023-11-01 FAIL: github.com unreachable")
(skill_path / "logs" / "run_20231102.log").write_text("2023-11-02 ERROR: DNS NXDOMAIN\n")
(skill_path / "scripts" / "old_fix.sh").write_text("#!/bin/bash\n# DEPRECATED: use fix_github_dns.py instead\necho 'This script is no longer maintained'")
(skill_path / "scripts" / "requirements.txt").write_text("requests>=2.28.0\n")

# ── 4. Create a realistic CI/CD project directory ────────────────────────────
project_dir = workspace / "cicd-pipeline"
project_dir.mkdir(exist_ok=True)
(project_dir / "Jenkinsfile").write_text("""pipeline {
  agent any
  stages {
    stage('Checkout') { steps { checkout scm } }
    stage('Build') { steps { sh 'make build' } }
  }
}
""")
(project_dir / ".github").mkdir(exist_ok=True)
(project_dir / ".github" / "workflows").mkdir(exist_ok=True)
(project_dir / ".github" / "workflows" / "ci.yml").write_text("""name: CI
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: echo "build"
""")
(project_dir / "network_diagnostics.txt").write_text("""=== Network Diagnostic Report ===
Date: 2024-01-15 09:32:11
Container: build-agent-007

DNS Resolution Failures:
  - github.com         NXDOMAIN
  - api.github.com     NXDOMAIN
  - raw.githubusercontent.com  NXDOMAIN

Last successful build: 2024-01-14 22:10:05
Failure rate: 100% (last 6 hours)

Action Required: DNS repair needed before pipeline can resume.
""")
(project_dir / "Makefile").write_text("""build:
\t@echo "Building project..."

test:
\t@echo "Running tests..."
""")

# ── 5. Create the mock-server config (pre-placed, agent must discover) ───────
mock_dir = workspace / "mock_hosts_server"
mock_dir.mkdir(exist_ok=True)
(mock_dir / "server_config.json").write_text(json.dumps({
    "port": 18080,
    "endpoint": "/hosts",
    "description": "Local mock hosts server for testing DNS fix tool"
}, indent=2))

# ── 6. Write the hosts file with intentionally broken/stale GitHub entries ───
hosts_content = """127.0.0.1   localhost
127.0.1.1   buildagent
::1         localhost ip6-localhost ip6-loopback
fe00::0     ip6-localnet
ff00::0     ip6-mcastprefix
ff02::1     ip6-allnodes
ff02::2     ip6-allrouters

# GitHub DNS Fix - START
# Updated: 2023-06-01 00:00:00 UTC
# Entries: 3
140.82.112.3  github.com
185.199.108.133  assets-cdn.github.com
# GitHub DNS Fix - END
"""
Path("/etc/hosts").write_text(hosts_content)

# ── 7. Create the expected "fresh" hosts data served by mock server ───────────
mock_hosts_data = mock_dir / "hosts_data.txt"
mock_hosts_data.write_text("""# GitHub Hosts - Updated 2024-01-15
# Generated by github-dns-helper project

140.82.114.4  github.com
140.82.114.5  api.github.com
185.199.108.154  assets-cdn.github.com
185.199.108.154  github.githubassets.com
151.101.1.194  github.global.ssl.fastly.net
185.199.108.133  raw.githubusercontent.com
185.199.108.133  gist.github.com
185.199.108.133  github-releases.githubusercontent.com
52.217.128.40   codeload.github.com
185.199.108.133  objects.githubusercontent.com
192.0.2.1       some.random.domain.com
203.0.113.5     another.non-github.example.net
""")

# ── 8. Record what we expect for evaluation ──────────────────────────────────
expected = {
    "github_entries_from_mock": [
        "140.82.114.4  github.com",
        "140.82.114.5  api.github.com",
        "185.199.108.154  assets-cdn.github.com",
        "185.199.108.154  github.githubassets.com",
        "151.101.1.194  github.global.ssl.fastly.net",
        "185.199.108.133  raw.githubusercontent.com",
        "185.199.108.133  gist.github.com",
        "185.199.108.133  github-releases.githubusercontent.com",
        "52.217.128.40   codeload.github.com",
        "185.199.108.133  objects.githubusercontent.com",
    ],
    "marker_start": "# GitHub DNS Fix - START",
    "marker_end": "# GitHub DNS Fix - END",
    "mock_server_port": 18080
}
(workspace / ".eval_expected.json").write_text(json.dumps(expected, indent=2))

print("Workspace initialized successfully.")
print(f"Skill path: {skill_path}")
print(f"Script: {fix_script}")
print(f"Mock data: {mock_hosts_data}")