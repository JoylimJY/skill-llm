import os
import random
import json
import stat

random.seed(42)

workspace = "/workspace"

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "references",
    "logs",
    "logs/archive",
    "config",
    "config/envs",
    "data/incoming",
    "data/processed",
    "agents/gotchi",
    "agents/treasury",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "config/envs/prod.env": "NETWORK=mainnet\nFEE_TIER=0.3\nSLIPPAGE=0.01\n",
    "config/envs/staging.env": "NETWORK=testnet\nFEE_TIER=0.5\nSLIPPAGE=0.05\n",
    "config/model_override.yaml": "# deprecated – do not use\noverride_model: gpt-4\n",
    "logs/router.log": "2024-01-10 INFO route=minimax msg_id=001\n2024-01-10 INFO route=sonnet msg_id=002\n",
    "logs/archive/2023-12-router.log": "archive log data\n",
    "data/incoming/raw_messages.txt": "\n".join([
        "pet all my gotchis",
        "explain the DeFi protocol to me",
        "fix the bug in the swap module",
    ]) + "\n",
    "data/processed/.gitkeep": "",
    "agents/gotchi/config.json": json.dumps({"gotchi_count": 53, "auto_pet": True}, indent=2),
    "agents/treasury/policy.json": json.dumps({"max_tx": "10000 USDC", "require_review": True}, indent=2),
    "config/legacy_router.json": json.dumps({
        "routes": {"default": "gpt-4", "code": "codex", "chat": "gpt-3.5"}
    }, indent=2),
}
for rel, content in distractors.items():
    path = os.path.join(workspace, rel)
    with open(path, "w") as f:
        f.write(content)

# ── references/routing-table.md ──────────────────────────────────────────────
routing_table = """\
# Routing Table

## Task Classification

| Task Type      | Condition                                              | Route                        |
|----------------|--------------------------------------------------------|------------------------------|
| deterministic  | Has a deterministic skill or shellable script          | zero-llm                     |
| chat           | Casual, low-risk, simple rewriting                     | bankr/minimax-m2.5           |
| general        | Reasoning, planning, product thinking                  | bankr/claude-sonnet-4.5      |
| wallet/routine | Routine wallet operations (swaps, sends, treasury)     | bankr/claude-sonnet-4.5      |
| wallet/high    | High-stakes, security-sensitive wallet actions         | bankr/claude-opus-4.6        |
| code           | Coding, patching, repo surgery, implementation         | bankr/gpt-5.2-codex          |
| long-context   | Long document synthesis, broad digestion               | bankr/gemini-3-pro           |
| vision         | Lightweight vision or multimodal triage                | bankr/gemini-3-flash         |

## Escalation Thresholds

- Escalate wallet tasks to `bankr/claude-opus-4.6` when:
  - Amount > 50,000 USD equivalent
  - Action involves private key material
  - Task is described as "critical", "emergency", or "all holdings"
  - Security review is explicitly requested

## Fallback Rules

- `zero-llm` fallback → `bankr/minimax-m2.5` (in case skill unavailable)
- `bankr/minimax-m2.5` fallback → `bankr/claude-sonnet-4.5`
- `bankr/claude-sonnet-4.5` fallback → `bankr/claude-opus-4.6`
- `bankr/gpt-5.2-codex` fallback → `bankr/claude-sonnet-4.5`
- `bankr/gemini-3-pro` fallback → `bankr/claude-sonnet-4.5`
- `bankr/gemini-3-flash` fallback → `bankr/claude-sonnet-4.5`
- `bankr/claude-opus-4.6` fallback → human-review

## Notes

- Never downgrade a high-stakes wallet task.
- Cost ordering (cheapest first): zero-llm < minimax-m2.5 < claude-sonnet-4.5 ≈ gpt-5.2-codex ≈ gemini-3-flash < gemini-3-pro < claude-opus-4.6
"""

with open(os.path.join(workspace, "references/routing-table.md"), "w") as f:
    f.write(routing_table)

# ── references/bankr-models.md ───────────────────────────────────────────────
bankr_models = """\
# Bankr Model Inventory

## Models

### bankr/minimax-m2.5
- Type: Chat / lightweight classification
- Context: 32k tokens
- Cost tier: cheapest LLM
- aaigotchi default: YES (fallback)

### bankr/claude-sonnet-4.5
- Type: General reasoning, planning
- Context: 200k tokens
- Cost tier: mid
- aaigotchi default: general workhorse

### bankr/gpt-5.2-codex
- Type: Code generation, patching
- Context: 128k tokens
- Cost tier: mid
- aaigotchi default: coding tasks

### bankr/gemini-3-pro
- Type: Long-context synthesis
- Context: 1M tokens
- Cost tier: mid-high
- aaigotchi default: document digestion

### bankr/gemini-3-flash
- Type: Vision, multimodal triage
- Context: 32k tokens + images
- Cost tier: mid (vision add-on)
- aaigotchi default: vision

### bankr/claude-opus-4.6
- Type: High-stakes reasoning, security
- Context: 200k tokens
- Cost tier: most expensive
- aaigotchi default: final escalation only

### zero-llm
- Type: Deterministic skill execution
- Cost tier: free (no LLM call)
- aaigotchi default: preferred when possible
"""

with open(os.path.join(workspace, "references/bankr-models.md"), "w") as f:
    f.write(bankr_models)

# ── scripts/route_message.py ─────────────────────────────────────────────────
route_message_py = '''\
#!/usr/bin/env python3
"""
route_message.py  –  Bankr / OpenClaw model-brain router
Usage:
  python3 route_message.py --text "<message>" [--json] [--mode summary|json|env]
"""

import argparse
import json
import re
import sys

ROUTING_TABLE = {
    "deterministic": {
        "primary": "zero-llm",
        "fallback": "bankr/minimax-m2.5",
    },
    "chat": {
        "primary": "bankr/minimax-m2.5",
        "fallback": "bankr/claude-sonnet-4.5",
    },
    "general": {
        "primary": "bankr/claude-sonnet-4.5",
        "fallback": "bankr/claude-opus-4.6",
    },
    "wallet/routine": {
        "primary": "bankr/claude-sonnet-4.5",
        "fallback": "bankr/claude-opus-4.6",
    },
    "wallet/high": {
        "primary": "bankr/claude-opus-4.6",
        "fallback": "human-review",
    },
    "code": {
        "primary": "bankr/gpt-5.2-codex",
        "fallback": "bankr/claude-sonnet-4.5",
    },
    "long-context": {
        "primary": "bankr/gemini-3-pro",
        "fallback": "bankr/claude-sonnet-4.5",
    },
    "vision": {
        "primary": "bankr/gemini-3-flash",
        "fallback": "bankr/claude-sonnet-4.5",
    },
}

DETERMINISTIC_PATTERNS = [
    r"\\bpet\\b", r"pet all", r"\\bauto-pet\\b", r"pet.*gotchi",
    r"run script", r"execute script", r"shellable",
]

HIGH_STAKES_PATTERNS = [
    r"all.*holding", r"private key", r"emergency", r"critical",
    r"\\b[0-9]{6,}\\b.*(?:usd|usdc|eth|btc)",
    r"(?:usd|usdc|eth|btc).*\\b[0-9]{6,}\\b",
    r"security review", r"audit.*wallet",
]

WALLET_PATTERNS = [
    r"swap", r"send.*(?:usdc|eth|btc|treasury)", r"transfer", r"treasury",
    r"wallet", r"transaction", r"\\bpay\\b",
]

CODE_PATTERNS = [
    r"fix.*bug", r"patch", r"implement", r"build.*feature", r"\\bcode\\b",
    r"repo", r"refactor", r"\\bpr\\b", r"pull request", r"\\bmodule\\b.*(?:bug|fix|build)",
]

LONG_CTX_PATTERNS = [
    r"summarize.*document", r"digest.*report", r"read.*all.*file",
    r"entire codebase", r"all.*logs", r"long.*document",
]

VISION_PATTERNS = [
    r"\\bimage\\b", r"\\bscreenshot\\b", r"\\bphoto\\b", r"\\bvision\\b",
    r"\\bpicture\\b", r"\\bmultimodal\\b",
]

CHAT_PATTERNS = [
    r"rewrite", r"shorter", r"summarize(?!.*document)", r"explain",
    r"what is", r"casual", r"chat", r"\\bhi\\b", r"\\bhello\\b",
    r"classify",
]


def classify(text: str):
    t = text.lower()

    for p in DETERMINISTIC_PATTERNS:
        if re.search(p, t):
            return "deterministic", False

    high_stakes = any(re.search(p, t) for p in HIGH_STAKES_PATTERNS)

    for p in WALLET_PATTERNS:
        if re.search(p, t):
            if high_stakes:
                return "wallet/high", True
            return "wallet/routine", False

    for p in CODE_PATTERNS:
        if re.search(p, t):
            return "code", False

    for p in LONG_CTX_PATTERNS:
        if re.search(p, t):
            return "long-context", False

    for p in VISION_PATTERNS:
        if re.search(p, t):
            return "vision", False

    for p in CHAT_PATTERNS:
        if re.search(p, t):
            return "chat", False

    return "general", False


REASON_MAP = {
    "deterministic": "Deterministic skill can handle this without an LLM call.",
    "chat": "Low-risk, casual or lightweight task; cheapest LLM suffices.",
    "general": "General reasoning or planning task; standard workhorse model.",
    "wallet/routine": "Routine wallet operation; mid-tier model balances safety and cost.",
    "wallet/high": "High-stakes or security-sensitive wallet action; requires top-tier model.",
    "code": "Coding or patching task; code-specialist model preferred.",
    "long-context": "Long-context synthesis required; high-context model needed.",
    "vision": "Vision or multimodal content; vision-capable model required.",
}


def route(text: str):
    task_type, high_stakes = classify(text)
    entry = ROUTING_TABLE[task_type]
    return {
        "task_type": task_type,
        "high_stakes": high_stakes,
        "primary": entry["primary"],
        "fallback": entry["fallback"],
        "reason": REASON_MAP[task_type],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    parser.add_argument("--json", action="store_true", dest="json_out")
    parser.add_argument("--mode", choices=["summary", "json", "env"], default="json")
    args = parser.parse_args()

    result = route(args.text)

    if args.json_out or args.mode == "json":
        print(json.dumps(result, indent=2))
    elif args.mode == "summary":
        print(f"Route: {result[\'primary\']} (fallback: {result[\'fallback\']})")
        print(f"Reason: {result[\'reason\']}")
    elif args.mode == "env":
        print(f"MODEL_PRIMARY={result[\'primary\']}")
        print(f"MODEL_FALLBACK={result[\'fallback\']}")
        print(f"TASK_TYPE={result[\'task_type\']}")
        print(f"HIGH_STAKES={str(result[\'high_stakes\']).lower()}")


if __name__ == "__main__":
    main()
'''

with open(os.path.join(workspace, "scripts/route_message.py"), "w") as f:
    f.write(route_message_py)
os.chmod(os.path.join(workspace, "scripts/route_message.py"),
         stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

# ── scripts/select_model.sh ──────────────────────────────────────────────────
select_model_sh = '''\
#!/usr/bin/env bash
# select_model.sh  –  aaigotchi-friendly wrapper around route_message.py
# Usage:
#   bash select_model.sh --text "<message>" --mode summary|json|env
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEXT=""
MODE="json"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --text)  TEXT="$2"; shift 2 ;;
    --mode)  MODE="$2"; shift 2 ;;
    *)       echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$TEXT" ]]; then
  echo "Error: --text is required" >&2
  exit 1
fi

python3 "$SCRIPT_DIR/route_message.py" --text "$TEXT" --mode "$MODE"
'''

with open(os.path.join(workspace, "scripts/select_model.sh"), "w") as f:
    f.write(select_model_sh)
os.chmod(os.path.join(workspace, "scripts/select_model.sh"),
         stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

# ── data/incoming/audit_batch.json  (the RAW messy input the agent must process)
# These are 8 messages with deliberately varied, real-world phrasing
audit_batch = {
    "batch_id": "audit-2024-q1",
    "messages": [
        {
            "id": "msg-001",
            "text": "pet all my 53 gotchis right now"
        },
        {
            "id": "msg-002",
            "text": "rewrite this x thread shorter and make it punchier"
        },
        {
            "id": "msg-003",
            "text": "swap 500 ETH to USDC and send to treasury wallet"
        },
        {
            "id": "msg-004",
            "text": "emergency: transfer all holdings to cold wallet – private key rotation needed"
        },
        {
            "id": "msg-005",
            "text": "build this new staking module feature in the repo and fix the existing bug"
        },
        {
            "id": "msg-006",
            "text": "summarize this 800-page governance document and all related logs"
        },
        {
            "id": "msg-007",
            "text": "what is the current APY for our liquidity pool"
        },
        {
            "id": "msg-008",
            "text": "audit the treasury smart contract security review before mainnet deploy"
        }
    ]
}

with open(os.path.join(workspace, "data/incoming/audit_batch.json"), "w") as f:
    json.dump(audit_batch, f, indent=2)

print("Workspace initialised at", workspace)
print("Files created:")
for root, dirs_, files in os.walk(workspace):
    for fname in files:
        print(" ", os.path.join(root, fname).replace(workspace, ""))