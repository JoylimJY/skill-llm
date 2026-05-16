import os
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

# ── Directory skeleton (distractor files) ───────────────────────────────────
dirs = [
    "configs/staging",
    "configs/production",
    "configs/archived",
    "release_notes",
    "scripts",
    "logs/deploy",
    "logs/audit",
    "tests/unit",
    "tests/integration",
    "docs",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# Distractor files
distractors = {
    "configs/archived/service_v1.json": '{"version": "1.0", "replicas": 1}',
    "configs/archived/service_v2.json": '{"version": "2.0", "replicas": 2}',
    "configs/staging/README.txt":        "Staging environment configs",
    "logs/deploy/deploy_2024-01-10.log": "Deployment started\nDeployment finished\n",
    "logs/deploy/deploy_2024-01-11.log": "Deployment started\nRollback triggered\n",
    "logs/audit/access.log":             "user=admin action=read ts=1700000000\n",
    "tests/unit/test_config.py":         "def test_dummy(): assert True\n",
    "tests/integration/test_deploy.py":  "def test_dummy2(): assert True\n",
    "docs/architecture.md":              "# Architecture\nSee diagrams folder.\n",
    "docs/runbook.md":                   "# Runbook\nStep 1: check logs.\n",
}
for rel, content in distractors.items():
    with open(os.path.join(WORKSPACE, rel), "w") as f:
        f.write(content)

# ── Core input 1: JSON service configs (staging vs production) ───────────────
staging_config = {
    "service": "payment-gateway",
    "version": "3.4.1",
    "replicas": 2,
    "environment": "staging",
    "resources": {
        "cpu": "500m",
        "memory": "256Mi"
    },
    "features": {
        "rate_limiting": False,
        "circuit_breaker": True,
        "detailed_logging": True
    },
    "database": {
        "host": "db-staging.internal",
        "port": 5432,
        "pool_size": 5
    },
    "timeouts": {
        "connect": 3,
        "read": 10,
        "write": 10
    }
}

# Production config: same keys but intentionally different values + extra key
# Key ordering is deliberately shuffled to test structural diff
production_config = {
    "timeouts": {
        "write": 30,
        "read": 30,
        "connect": 5
    },
    "database": {
        "pool_size": 20,
        "port": 5432,
        "host": "db-prod.internal"
    },
    "features": {
        "circuit_breaker": True,
        "rate_limiting": True,
        "detailed_logging": False
    },
    "resources": {
        "memory": "1Gi",
        "cpu": "2000m"
    },
    "replicas": 5,
    "environment": "production",
    "version": "3.4.1",
    "service": "payment-gateway",
    "monitoring": {
        "enabled": True,
        "endpoint": "/metrics"
    }
}

with open(os.path.join(WORKSPACE, "configs/staging/service.json"), "w") as f:
    json.dump(staging_config, f, indent=2)

with open(os.path.join(WORKSPACE, "configs/production/service.json"), "w") as f:
    json.dump(production_config, f, indent=2)

# ── Core input 2: Release notes (two versions of prose) ─────────────────────
release_notes_v1 = """\
Release Notes - v3.4.0

Summary
This release focuses on stability improvements and minor feature additions for the payment gateway service.

Changes
- Added support for idempotency keys in transaction requests
- Improved error handling for downstream service timeouts
- Updated internal retry logic with exponential backoff strategy
- Fixed a race condition in the session cache invalidation module
- Deprecated the legacy XML endpoint (removal planned for v4.0)

Known Issues
- Occasional latency spikes observed under high load conditions
- Memory usage increases slightly with detailed logging enabled

Upgrade Notes
No database migration required.   
Restart the service after deployment to apply configuration changes.
"""

release_notes_v2 = """\
Release Notes - v3.4.1

Summary
This release delivers critical security patches and performance tuning for the payment gateway service.

Changes
- Added support for idempotency keys in transaction requests
- Improved error handling for downstream service timeouts and connection resets
- Updated internal retry logic with exponential backoff strategy and jitter
- Fixed a race condition in the session cache invalidation module
- Removed the legacy XML endpoint
- Added Prometheus metrics endpoint at /metrics

Known Issues
- Memory usage increases slightly with detailed logging enabled

Upgrade Notes
Database migration required: run migrate.sh before deployment.
Restart the service after deployment to apply configuration changes.
"""

with open(os.path.join(WORKSPACE, "release_notes/v3.4.0.txt"), "w") as f:
    f.write(release_notes_v1)

with open(os.path.join(WORKSPACE, "release_notes/v3.4.1.txt"), "w") as f:
    f.write(release_notes_v2)

# ── Stub scripts/text_diff.py (the real tool) ─────────────────────────────
# The skill says "All scripts mentioned in the SKILL.md already exist in the workspace."
# We implement a realistic version of text_diff.py here.

text_diff_script = r'''#!/usr/bin/env python3
"""jrv-text-diff: Compare two text files or strings."""
import argparse
import json
import sys
import difflib
import re

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# ANSI colors
RED    = "\033[31m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
RESET  = "\033[0m"

def colorize(text, color, use_color):
    return f"{color}{text}{RESET}" if use_color else text

def load_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def normalize(lines, ignore_ws, ignore_case):
    result = []
    for line in lines:
        l = line
        if ignore_ws:
            l = l.strip()
        if ignore_case:
            l = l.lower()
        result.append(l)
    return result

def unified_diff(lines1, lines2, label1, label2, context, use_color):
    diff = list(difflib.unified_diff(lines1, lines2,
                                     fromfile=label1, tofile=label2,
                                     n=context))
    out = []
    for line in diff:
        if line.startswith("---") or line.startswith("+++"):
            out.append(colorize(line.rstrip("\n"), CYAN, use_color))
        elif line.startswith("+"):
            out.append(colorize(line.rstrip("\n"), GREEN, use_color))
        elif line.startswith("-"):
            out.append(colorize(line.rstrip("\n"), RED, use_color))
        elif line.startswith("@@"):
            out.append(colorize(line.rstrip("\n"), YELLOW, use_color))
        else:
            out.append(line.rstrip("\n"))
    return "\n".join(out)

def side_by_side_diff(lines1, lines2, use_color):
    width = 60
    out = []
    matcher = difflib.SequenceMatcher(None, lines1, lines2)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for a, b in zip(lines1[i1:i2], lines2[j1:j2]):
                out.append(f"{a.rstrip():<{width}} | {b.rstrip()}")
        elif tag == "replace":
            for a, b in zip(lines1[i1:i2], lines2[j1:j2]):
                out.append(colorize(f"{a.rstrip():<{width}}", RED, use_color) +
                            " | " + colorize(b.rstrip(), GREEN, use_color))
            for a in lines1[i1+len(lines2[j1:j2]):i2]:
                out.append(colorize(f"{a.rstrip():<{width}}", RED, use_color) + " | ")
            for b in lines2[j1+len(lines1[i1:i2]):j2]:
                out.append(" " * width + " | " + colorize(b.rstrip(), GREEN, use_color))
        elif tag == "delete":
            for a in lines1[i1:i2]:
                out.append(colorize(f"{a.rstrip():<{width}}", RED, use_color) + " | ")
        elif tag == "insert":
            for b in lines2[j1:j2]:
                out.append(" " * width + " | " + colorize(b.rstrip(), GREEN, use_color))
    return "\n".join(out)

def context_diff(lines1, lines2, label1, label2, context, use_color):
    diff = list(difflib.context_diff(lines1, lines2,
                                     fromfile=label1, tofile=label2,
                                     n=context))
    out = []
    for line in diff:
        l = line.rstrip("\n")
        if l.startswith("! "):
            out.append(colorize(l, YELLOW, use_color))
        elif l.startswith("+ "):
            out.append(colorize(l, GREEN, use_color))
        elif l.startswith("- "):
            out.append(colorize(l, RED, use_color))
        else:
            out.append(l)
    return "\n".join(out)

def word_diff(lines1, lines2, use_color, ignore_ws, ignore_case):
    out = []
    matcher = difflib.SequenceMatcher(None, lines1, lines2)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for line in lines1[i1:i2]:
                out.append(line.rstrip())
        else:
            for line in lines1[i1:i2]:
                words_old = line.split()
                word_str = " ".join(words_old)
                out.append(colorize(f"[-{word_str}-]", RED, use_color))
            for line in lines2[j1:j2]:
                words_new = line.split()
                word_str = " ".join(words_new)
                out.append(colorize(f"[+{word_str}+]", GREEN, use_color))
    return "\n".join(out)

def flatten_json(obj, prefix=""):
    items = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{prefix}.{k}" if prefix else k
            items.update(flatten_json(v, new_key))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            new_key = f"{prefix}[{i}]"
            items.update(flatten_json(v, new_key))
    else:
        items[prefix] = obj
    return items

def json_diff(text1, text2, use_color):
    try:
        obj1 = json.loads(text1)
        obj2 = json.loads(text2)
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}", file=sys.stderr)
        sys.exit(2)
    flat1 = flatten_json(obj1)
    flat2 = flatten_json(obj2)
    all_keys = sorted(set(flat1) | set(flat2))
    out = []
    added = deleted = changed = 0
    for k in all_keys:
        if k not in flat1:
            out.append(colorize(f"+ {k}: {flat2[k]}", GREEN, use_color))
            added += 1
        elif k not in flat2:
            out.append(colorize(f"- {k}: {flat1[k]}", RED, use_color))
            deleted += 1
        elif flat1[k] != flat2[k]:
            out.append(colorize(f"~ {k}: {flat1[k]} -> {flat2[k]}", YELLOW, use_color))
            changed += 1
    return "\n".join(out), added, deleted, changed

def yaml_diff(text1, text2, use_color):
    if not HAS_YAML:
        print("PyYAML not installed", file=sys.stderr)
        sys.exit(2)
    try:
        obj1 = yaml.safe_load(text1)
        obj2 = yaml.safe_load(text2)
    except yaml.YAMLError as e:
        print(f"YAML parse error: {e}", file=sys.stderr)
        sys.exit(2)
    flat1 = flatten_json(obj1)
    flat2 = flatten_json(obj2)
    all_keys = sorted(set(flat1) | set(flat2))
    out = []
    added = deleted = changed = 0
    for k in all_keys:
        if k not in flat1:
            out.append(colorize(f"+ {k}: {flat2[k]}", GREEN, use_color))
            added += 1
        elif k not in flat2:
            out.append(colorize(f"- {k}: {flat1[k]}", RED, use_color))
            deleted += 1
        elif flat1[k] != flat2[k]:
            out.append(colorize(f"~ {k}: {flat1[k]} -> {flat2[k]}", YELLOW, use_color))
            changed += 1
    return "\n".join(out), added, deleted, changed

def compute_stats(lines1, lines2):
    matcher = difflib.SequenceMatcher(None, lines1, lines2)
    added = deleted = changed = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "insert":
            added += j2 - j1
        elif tag == "delete":
            deleted += i2 - i1
        elif tag == "replace":
            changed += max(i2 - i1, j2 - j1)
    return added, deleted, changed

def main():
    parser = argparse.ArgumentParser(prog="text_diff.py")
    parser.add_argument("file1", nargs="?")
    parser.add_argument("file2", nargs="?")
    parser.add_argument("--text",  dest="text1")
    parser.add_argument("--text2", dest="text2")
    parser.add_argument("--format", choices=["unified","side-by-side","context","json","yaml"],
                        default="unified")
    parser.add_argument("--word-diff", action="store_true")
    parser.add_argument("--ignore-whitespace", action="store_true")
    parser.add_argument("--ignore-case", action="store_true")
    parser.add_argument("--context", type=int, default=3, dest="ctx")
    parser.add_argument("--output-json", action="store_true")
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args()

    use_color = not args.no_color

    # Load texts
    if args.text1 and args.text2:
        text1, text2 = args.text1, args.text2
        label1, label2 = "<text1>", "<text2>"
    elif args.file1 and args.file2:
        try:
            text1 = load_text(args.file1)
            text2 = load_text(args.file2)
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(2)
        label1, label2 = args.file1, args.file2
    else:
        parser.print_help()
        sys.exit(2)

    lines1 = text1.splitlines(keepends=True)
    lines2 = text2.splitlines(keepends=True)

    norm1 = normalize(lines1, args.ignore_whitespace, args.ignore_case)
    norm2 = normalize(lines2, args.ignore_whitespace, args.ignore_case)

    # Structural diffs
    if args.format == "json":
        diff_output, added, deleted, changed = json_diff(text1, text2, use_color)
        identical = (added == 0 and deleted == 0 and changed == 0)
        if args.output_json:
            report = {"identical": identical, "added": added,
                      "deleted": deleted, "changed": changed,
                      "format": "json"}
            print(json.dumps(report, indent=2))
        else:
            print(diff_output)
        sys.exit(0 if identical else 1)

    if args.format == "yaml":
        diff_output, added, deleted, changed = yaml_diff(text1, text2, use_color)
        identical = (added == 0 and deleted == 0 and changed == 0)
        if args.output_json:
            report = {"identical": identical, "added": added,
                      "deleted": deleted, "changed": changed,
                      "format": "yaml"}
            print(json.dumps(report, indent=2))
        else:
            print(diff_output)
        sys.exit(0 if identical else 1)

    # Text diffs
    if args.word_diff:
        diff_output = word_diff(norm1, norm2, use_color,
                                args.ignore_whitespace, args.ignore_case)
    elif args.format == "side-by-side":
        diff_output = side_by_side_diff(norm1, norm2, use_color)
    elif args.format == "context":
        diff_output = context_diff(norm1, norm2, label1, label2,
                                   args.ctx, use_color)
    else:
        diff_output = unified_diff(norm1, norm2, label1, label2,
                                   args.ctx, use_color)

    added, deleted, changed = compute_stats(norm1, norm2)
    identical = (added == 0 and deleted == 0 and changed == 0)

    if args.output_json:
        report = {"identical": identical, "added": added,
                  "deleted": deleted, "changed": changed,
                  "format": args.format if not args.word_diff else "word-diff"}
        print(json.dumps(report, indent=2))
    else:
        print(diff_output)

    sys.exit(0 if identical else 1)

if __name__ == "__main__":
    main()
'''

os.makedirs(os.path.join(WORKSPACE, "scripts"), exist_ok=True)
with open(os.path.join(WORKSPACE, "scripts/text_diff.py"), "w") as f:
    f.write(text_diff_script)

print("Workspace generated successfully.")