#!/usr/bin/env python3
"""
Generates the sandbox workspace for the model-failover-doctor task.
Creates a realistic OpenClaw workspace with broken configs and distractor files.
"""
import os
import json
import random
import shutil
from pathlib import Path

random.seed(42)

HOME = Path("/root")
OPENCLAW = HOME / ".openclaw"
WORKSPACE = OPENCLAW / "workspace"
SKILLS_DIR = WORKSPACE / "skills" / "model-failover-doctor"
LIB_DIR = WORKSPACE / ".lib"
BACKUPS_DIR = LIB_DIR / ".mfd_backups"

# Create directory structure
for d in [SKILLS_DIR, BACKUPS_DIR,
          WORKSPACE / "skills" / "code-reviewer",
          WORKSPACE / "skills" / "test-runner",
          WORKSPACE / "config",
          WORKSPACE / "logs",
          WORKSPACE / "sessions",
          WORKSPACE / "providers",
          WORKSPACE / "agents" / "primary",
          WORKSPACE / "agents" / "fallback",
          WORKSPACE / ".lib" / "cache",
          WORKSPACE / ".lib" / "metrics",
          OPENCLAW / "runtime" / "gateway",
          OPENCLAW / "runtime" / "injectors"]:
    d.mkdir(parents=True, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────

(WORKSPACE / "config" / "gateway.yaml").write_text("""\
gateway:
  port: 8742
  timeout: 30
  max_retries: 3
  log_level: info
""")

(WORKSPACE / "config" / "routing.yaml").write_text("""\
routing:
  strategy: round-robin
  health_check_interval: 60
  circuit_breaker:
    threshold: 5
    reset_timeout: 120
""")

(WORKSPACE / "logs" / "gateway.log").write_text("""\
2024-01-15 09:00:01 INFO  Gateway started on :8742
2024-01-15 09:00:02 INFO  Loaded 4 providers
2024-01-15 09:12:34 ERROR All models failed (3): kimi-coding/k2p5: No available channel for model openai/gpt-5.3-codex; zai/k2p5: No available channel for model openai/gpt-5.3-codex; minimax/k2p5: No available channel for model openai/gpt-5.3-codex
2024-01-15 09:12:35 WARN  Session sess-alpha: No fallbackChain defined, cold-start failure
2024-01-15 09:12:40 ERROR Session sess-beta: fallback provider prefix 'deprecated-kimi' not recognized
2024-01-15 09:13:01 ERROR All models failed (3): same pattern repeated
""")

(WORKSPACE / "logs" / "injector.log").write_text("""\
2024-01-15 09:12:30 DEBUG before_agent_start called for session sess-alpha
2024-01-15 09:12:30 DEBUG modelOverride=openai/gpt-5.3-codex providerOverride=kimi-coding lockModel=false
2024-01-15 09:12:30 WARN  lockModel is false but modelOverride still injected into response
""")

(WORKSPACE / "providers" / "kimi-coding.json").write_text(json.dumps({
    "id": "kimi-coding",
    "name": "Kimi Coding",
    "baseUrl": "https://api.kimi-coding.internal",
    "models": ["k2p5", "k2p3", "k2-lite"],
    "status": "active"
}, indent=2))

(WORKSPACE / "providers" / "zai.json").write_text(json.dumps({
    "id": "zai",
    "name": "Zai Provider",
    "baseUrl": "https://api.zai.internal",
    "models": ["k2p5", "zai-turbo"],
    "status": "active"
}, indent=2))

(WORKSPACE / "providers" / "minimax.json").write_text(json.dumps({
    "id": "minimax",
    "name": "MiniMax",
    "baseUrl": "https://api.minimax.internal",
    "models": ["k2p5", "mm-chat"],
    "status": "active"
}, indent=2))

(WORKSPACE / "agents" / "primary" / "agent.json").write_text(json.dumps({
    "id": "primary-agent",
    "model": "k2p5",
    "provider": "kimi-coding",
    "created": "2024-01-10T00:00:00Z"
}, indent=2))

(WORKSPACE / "agents" / "fallback" / "agent.json").write_text(json.dumps({
    "id": "fallback-agent",
    "model": "k2p5",
    "provider": "zai",
    "created": "2024-01-10T00:00:00Z"
}, indent=2))

(WORKSPACE / ".lib" / "cache" / "model_registry.json").write_text(json.dumps({
    "version": "2.1.0",
    "models": {
        "k2p5": {"capabilities": ["code", "chat"], "maxTokens": 131072},
        "k2p3": {"capabilities": ["chat"], "maxTokens": 65536},
        "zai-turbo": {"capabilities": ["code", "chat"], "maxTokens": 200000}
    }
}, indent=2))

(WORKSPACE / ".lib" / "metrics" / "latency_p99.json").write_text(json.dumps({
    "kimi-coding": 342,
    "zai": 289,
    "minimax": 401
}, indent=2))

(WORKSPACE / "skills" / "code-reviewer" / "code_reviewer.py").write_text(
    "# Code reviewer skill - not relevant to this incident\nprint('code reviewer')\n"
)

(WORKSPACE / "skills" / "test-runner" / "test_runner.py").write_text(
    "# Test runner skill\nprint('test runner')\n"
)

(OPENCLAW / "runtime" / "gateway" / "server.js").write_text("""\
// Gateway server stub
const express = require('express');
const app = express();
app.listen(8742);
""")

# ── BROKEN CONFIG 1: pools.json (P-1: references non-existent provider) ─────

POOLS_JSON = WORKSPACE / "config" / "pools.json"
POOLS_JSON.write_text(json.dumps({
    "version": "1.4.2",
    "pools": [
        {
            "id": "pool-primary",
            "name": "Primary Coding Pool",
            "providers": ["kimi-coding", "zai", "ghost-provider-xyz"],
            "modelAlias": "k2p5",
            "strategy": "priority"
        },
        {
            "id": "pool-chat",
            "name": "General Chat Pool",
            "providers": ["minimax", "zai", "phantom-llm-v2"],
            "modelAlias": "k2p5",
            "strategy": "round-robin"
        },
        {
            "id": "pool-backup",
            "name": "Backup Pool",
            "providers": ["kimi-coding", "minimax"],
            "modelAlias": "k2p5",
            "strategy": "failover"
        }
    ],
    "defaultPool": "pool-primary"
}, indent=2))

# ── BROKEN CONFIG 2: session_model_state.json ─────────────────────────────────
# S-1: sess-alpha has no fallbackChain
# S-2: sess-beta has invalid provider prefix in fallbackChain

SESSION_STATE = WORKSPACE / "sessions" / "session_model_state.json"
SESSION_STATE.write_text(json.dumps({
    "schemaVersion": "2.0",
    "sessions": {
        "sess-alpha": {
            "sessionId": "sess-alpha",
            "currentModel": "k2p5",
            "currentProvider": "kimi-coding",
            "status": "degraded",
            "createdAt": "2024-01-15T09:00:00Z",
            "lastActivityAt": "2024-01-15T09:12:34Z",
            "metadata": {"user": "alice", "project": "refactor-engine"}
        },
        "sess-beta": {
            "sessionId": "sess-beta",
            "currentModel": "k2p5",
            "currentProvider": "zai",
            "status": "degraded",
            "createdAt": "2024-01-15T09:05:00Z",
            "lastActivityAt": "2024-01-15T09:12:40Z",
            "fallbackChain": [
                "deprecated-kimi/k2p5",
                "old-zai-endpoint/k2p5",
                "minimax/k2p5"
            ],
            "metadata": {"user": "bob", "project": "api-gateway"}
        },
        "sess-gamma": {
            "sessionId": "sess-gamma",
            "currentModel": "k2p5",
            "currentProvider": "minimax",
            "status": "active",
            "createdAt": "2024-01-15T08:00:00Z",
            "lastActivityAt": "2024-01-15T09:11:00Z",
            "fallbackChain": [
                "kimi-coding/k2p5",
                "zai/k2p5"
            ],
            "metadata": {"user": "carol", "project": "data-pipeline"}
        }
    }
}, indent=2))

# ── BROKEN CONFIG 3: message-injector TypeScript (MI-1) ──────────────────────

INJECTOR_DIR = OPENCLAW / "runtime" / "injectors"
INJECTOR_TS = INJECTOR_DIR / "message-injector.ts"
INJECTOR_TS.write_text("""\
import { AgentStartContext, InjectorResult } from '../types';

interface MessageInjectorConfig {
  lockModel: boolean;
  modelOverride: string;
  providerOverride: string;
  systemPrompt?: string;
  temperature?: number;
}

export class MessageInjector {
  private config: MessageInjectorConfig;

  constructor(config: MessageInjectorConfig) {
    this.config = config;
  }

  /**
   * before_agent_start is called once per session initialization.
   * When lockModel is false, routing should be left to the gateway's
   * normal pool-based selection logic via sessions.patch.
   */
  async before_agent_start(ctx: AgentStartContext): Promise<InjectorResult> {
    const { lockModel, modelOverride, providerOverride, systemPrompt, temperature } = this.config;

    // Prepare session patch for gateway routing
    const sessionsPatch = {
      sessionId: ctx.sessionId,
      timestamp: new Date().toISOString(),
    };

    // FIXME: This unconditionally injects modelOverride and providerOverride,
    // causing all gateway fallback attempts to use the wrong model ID.
    return {
      modelOverride,
      providerOverride,
      sessionsPatch,
      ...(systemPrompt ? { systemPrompt } : {}),
      ...(temperature !== undefined ? { temperature } : {}),
    };
  }

  async after_agent_response(ctx: AgentStartContext, response: string): Promise<void> {
    // Post-processing hook - currently a no-op
  }
}
""")

# ── The actual working doctor script ─────────────────────────────────────────

DOCTOR_SCRIPT = SKILLS_DIR / "model_failover_doctor.py"
DOCTOR_SCRIPT.write_text(r'''#!/usr/bin/env python3
"""
model_failover_doctor.py — Diagnoses and fixes OpenClaw "All models failed" errors.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HOME = Path.home()
OPENCLAW = HOME / ".openclaw"
WORKSPACE = OPENCLAW / "workspace"
BACKUPS_DIR = WORKSPACE / ".lib" / ".mfd_backups"

POOLS_JSON      = WORKSPACE / "config" / "pools.json"
SESSION_STATE   = WORKSPACE / "sessions" / "session_model_state.json"
INJECTOR_TS     = OPENCLAW / "runtime" / "injectors" / "message-injector.ts"
PROVIDERS_DIR   = WORKSPACE / "providers"

KNOWN_PROVIDERS = None  # Loaded lazily

VALID_PROVIDER_IDS_CACHE = None


def load_known_providers():
    global KNOWN_PROVIDERS
    if KNOWN_PROVIDERS is not None:
        return KNOWN_PROVIDERS
    KNOWN_PROVIDERS = set()
    if PROVIDERS_DIR.exists():
        for f in PROVIDERS_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                KNOWN_PROVIDERS.add(data.get("id", f.stem))
            except Exception:
                KNOWN_PROVIDERS.add(f.stem)
    return KNOWN_PROVIDERS


def timestamp_str():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def backup_file(path: Path):
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    ts = timestamp_str()
    dest = BACKUPS_DIR / f"{path.name}.{ts}.bak"
    shutil.copy2(path, dest)
    print(f"  [backup] {path.name} → {dest.name}")
    return dest


# ── Diagnosis ────────────────────────────────────────────────────────────────

def diagnose_pools():
    """P-1: pools.json references non-existent providers."""
    issues = []
    if not POOLS_JSON.exists():
        return issues
    try:
        data = json.loads(POOLS_JSON.read_text())
    except Exception as e:
        return [{"code": "P-ERR", "msg": f"Cannot parse pools.json: {e}"}]

    known = load_known_providers()
    for pool in data.get("pools", []):
        for prov in pool.get("providers", []):
            if prov not in known:
                issues.append({
                    "code": "P-1",
                    "severity": "critical",
                    "pool": pool["id"],
                    "bad_provider": prov,
                    "msg": f"Pool '{pool['id']}' references unknown provider '{prov}'"
                })
    return issues


def diagnose_sessions():
    """S-1/S-2: sessions missing fallbackChain or with invalid provider prefixes."""
    issues = []
    if not SESSION_STATE.exists():
        return issues
    try:
        data = json.loads(SESSION_STATE.read_text())
    except Exception as e:
        return [{"code": "S-ERR", "msg": f"Cannot parse session_model_state.json: {e}"}]

    known = load_known_providers()
    for sid, sess in data.get("sessions", {}).items():
        chain = sess.get("fallbackChain")
        if chain is None:
            issues.append({
                "code": "S-1",
                "severity": "critical",
                "session": sid,
                "msg": f"Session '{sid}' has no fallbackChain; cold-start failure guaranteed"
            })
        else:
            for entry in chain:
                parts = entry.split("/", 1)
                if len(parts) == 2:
                    prov_prefix = parts[0]
                    if prov_prefix not in known:
                        issues.append({
                            "code": "S-2",
                            "severity": "critical",
                            "session": sid,
                            "bad_entry": entry,
                            "bad_provider": prov_prefix,
                            "msg": f"Session '{sid}' fallbackChain entry '{entry}' has invalid provider prefix '{prov_prefix}'"
                        })
    return issues


def diagnose_injector():
    """MI-1: message-injector unconditionally returns modelOverride."""
    issues = []
    if not INJECTOR_TS.exists():
        return issues
    src = INJECTOR_TS.read_text()
    # Detect the broken pattern: return block contains modelOverride without lockModel guard
    # We look for a return statement that includes modelOverride NOT wrapped in ternary with lockModel
    broken_pattern = re.search(
        r'return\s*\{[^}]*modelOverride[^}]*\}',
        src,
        re.DOTALL
    )
    # Also check if the correct fix is already in place
    fixed_pattern = re.search(
        r'\.\.\.\s*\(\s*lockModel\s*\?',
        src
    )
    if broken_pattern and not fixed_pattern:
        issues.append({
            "code": "MI-1",
            "severity": "critical",
            "msg": "message-injector.ts: before_agent_start unconditionally returns modelOverride/providerOverride without lockModel guard"
        })
    return issues


def run_diagnosis():
    print("=" * 60)
    print("OpenClaw Model Failover Doctor — Diagnosis Report")
    print("=" * 60)
    all_issues = []

    p_issues = diagnose_pools()
    s_issues = diagnose_sessions()
    m_issues = diagnose_injector()
    all_issues = p_issues + s_issues + m_issues

    if not all_issues:
        print("✅ No issues found.")
        return all_issues

    for issue in all_issues:
        sev = issue.get("severity", "unknown")
        icon = "🔴" if sev == "critical" else "🟡"
        print(f"\n{icon} [{issue['code']}] {issue['msg']}")

    print(f"\nTotal issues: {len(all_issues)}")
    return all_issues


# ── Fixes ────────────────────────────────────────────────────────────────────

def fix_pools(dry_run=False):
    """P-1: Remove references to non-existent providers from pools.json."""
    if not POOLS_JSON.exists():
        return False
    data = json.loads(POOLS_JSON.read_text())
    known = load_known_providers()
    changed = False
    for pool in data.get("pools", []):
        original = pool.get("providers", [])
        filtered = [p for p in original if p in known]
        if filtered != original:
            removed = set(original) - set(filtered)
            print(f"  [P-1] Pool '{pool['id']}': removing unknown providers {removed}")
            pool["providers"] = filtered
            changed = True
    if changed and not dry_run:
        backup_file(POOLS_JSON)
        POOLS_JSON.write_text(json.dumps(data, indent=2))
        print(f"  [P-1] pools.json updated.")
    elif changed and dry_run:
        print(f"  [DRY-RUN] Would update pools.json")
    return changed


def fix_sessions(dry_run=False):
    """S-1/S-2: Add missing fallbackChain and fix invalid provider prefixes."""
    if not SESSION_STATE.exists():
        return False
    data = json.loads(SESSION_STATE.read_text())
    known = load_known_providers()
    known_list = sorted(known)
    changed = False

    for sid, sess in data.get("sessions", {}).items():
        chain = sess.get("fallbackChain")

        # S-1: No fallbackChain — build one from known providers
        if chain is None:
            model = sess.get("currentModel", "k2p5")
            current_prov = sess.get("currentProvider", "")
            new_chain = [
                f"{p}/{model}" for p in known_list if p != current_prov
            ]
            print(f"  [S-1] Session '{sid}': injecting fallbackChain {new_chain}")
            sess["fallbackChain"] = new_chain
            changed = True
        else:
            # S-2: Fix entries with invalid provider prefix
            new_chain = []
            for entry in chain:
                parts = entry.split("/", 1)
                if len(parts) == 2 and parts[0] not in known:
                    model_part = parts[1]
                    # Find a valid replacement provider (not the current one)
                    current_prov = sess.get("currentProvider", "")
                    replacement = next(
                        (p for p in known_list if p != current_prov and p not in [e.split("/")[0] for e in new_chain]),
                        known_list[0] if known_list else parts[0]
                    )
                    fixed_entry = f"{replacement}/{model_part}"
                    print(f"  [S-2] Session '{sid}': replacing '{entry}' → '{fixed_entry}'")
                    new_chain.append(fixed_entry)
                    changed = True
                else:
                    new_chain.append(entry)
            sess["fallbackChain"] = new_chain

    if changed and not dry_run:
        backup_file(SESSION_STATE)
        SESSION_STATE.write_text(json.dumps(data, indent=2))
        print(f"  [S-1/S-2] session_model_state.json updated.")
    elif changed and dry_run:
        print(f"  [DRY-RUN] Would update session_model_state.json")
    return changed


def fix_injector(dry_run=False):
    """MI-1: Wrap modelOverride/providerOverride return in lockModel conditional."""
    if not INJECTOR_TS.exists():
        return False
    src = INJECTOR_TS.read_text()

    # Already fixed?
    if re.search(r'\.\.\.\s*\(\s*lockModel\s*\?', src):
        print("  [MI-1] message-injector.ts already patched.")
        return False

    # Replace the broken return block with the lockModel-guarded version
    old_return = re.compile(
        r'(// FIXME:.*?\n\s*)?return\s*\{([^}]*modelOverride[^}]*)\};',
        re.DOTALL
    )

    def replacement(m):
        inner = m.group(2)
        # Extract non-modelOverride/providerOverride fields
        lines = [l.strip().rstrip(',') for l in inner.split('\n') if l.strip()]
        other_fields = [
            l for l in lines
            if 'modelOverride' not in l and 'providerOverride' not in l
        ]
        other_str = ',\n      '.join(other_fields)
        fixed = (
            "return {\n"
            "      ...(lockModel ? { modelOverride, providerOverride } : {}),\n"
            f"      {other_str},\n"
            "      ...(systemPrompt ? { systemPrompt } : {}),\n"
            "      ...(temperature !== undefined ? { temperature } : {}),\n"
            "    };"
        )
        return fixed

    new_src, count = old_return.subn(replacement, src)

    if count == 0:
        # Fallback: manual targeted replacement
        old_snippet = (
            "    return {\n"
            "      modelOverride,\n"
            "      providerOverride,\n"
            "      sessionsPatch,\n"
            "      ...(systemPrompt ? { systemPrompt } : {}),\n"
            "      ...(temperature !== undefined ? { temperature } : {}),\n"
            "    };"
        )
        new_snippet = (
            "    return {\n"
            "      ...(lockModel ? { modelOverride, providerOverride } : {}),\n"
            "      sessionsPatch,\n"
            "      ...(systemPrompt ? { systemPrompt } : {}),\n"
            "      ...(temperature !== undefined ? { temperature } : {}),\n"
            "    };"
        )
        if old_snippet in src:
            new_src = src.replace(old_snippet, new_snippet)
            count = 1
        else:
            print("  [MI-1] ERROR: Could not locate the broken return block to patch.")
            return False

    print(f"  [MI-1] Patched {count} return block(s) in message-injector.ts")
    if not dry_run:
        backup_file(INJECTOR_TS)
        INJECTOR_TS.write_text(new_src)
        print(f"  [MI-1] message-injector.ts updated.")
    else:
        print(f"  [DRY-RUN] Would update message-injector.ts")
    return True


def restart_gateway(dry_run=False):
    """Simulate gateway restart."""
    if dry_run:
        print("  [DRY-RUN] Would restart gateway")
        return
    # Write a restart marker (in a real system this would send SIGHUP or call a service)
    restart_marker = OPENCLAW / "runtime" / "gateway" / ".last_restart"
    restart_marker.write_text(datetime.now().isoformat())
    print(f"  [GATEWAY] Restart signal sent. Marker: {restart_marker}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="OpenClaw Model Failover Doctor")
    parser.add_argument("--fix", action="store_true", help="Apply automatic fixes")
    parser.add_argument("--restart", action="store_true", help="Restart gateway after fixes")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run",
                        help="Preview changes without writing files")
    args = parser.parse_args()

    issues = run_diagnosis()

    if args.dry_run:
        print("\n── Dry-run Preview ──────────────────────────────────────")
        fix_pools(dry_run=True)
        fix_sessions(dry_run=True)
        fix_injector(dry_run=True)
        restart_gateway(dry_run=True)
        return

    if args.fix:
        if not issues:
            print("\nNothing to fix.")
            return
        print("\n── Applying Fixes ───────────────────────────────────────")
        fix_pools(dry_run=False)
        fix_sessions(dry_run=False)
        fix_injector(dry_run=False)
        if args.restart:
            restart_gateway(dry_run=False)
        print("\n✅ All automatic fixes applied.")
    else:
        if issues:
            print("\nRun with --fix --restart to apply automatic repairs.")


if __name__ == "__main__":
    main()
''')

DOCTOR_SCRIPT.chmod(0o755)

print("Sandbox workspace generated successfully.")
print(f"  pools.json         → {POOLS_JSON}")
print(f"  session_model_state.json → {SESSION_STATE}")
print(f"  message-injector.ts → {INJECTOR_TS}")
print(f"  model_failover_doctor.py → {DOCTOR_SCRIPT}")