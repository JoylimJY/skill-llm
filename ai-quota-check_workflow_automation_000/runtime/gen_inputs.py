import os
import random
import json
import stat

random.seed(42)

workspace = "/workspace"

# ── Directory structure with distractor files ──────────────────────────────────
dirs = [
    "skills/ai-quota-check",
    "skills/ai-quota-check/lib",
    "skills/ai-quota-check/tests",
    "skills/code-review",
    "skills/code-review/lib",
    "config/providers",
    "config/routing",
    "logs/quota",
    "logs/errors",
    "docs/models",
    "reports/archive",
    "reports/daily",
    "cron/jobs",
    ".clawdbot",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Distractor files ───────────────────────────────────────────────────────────
distractor_files = {
    "config/providers/antigravity.yaml": """\
provider: google-antigravity
auth_method: oauth2
region: us-central1
models:
  - gemini-3-pro-high
  - claude-opus-4.6-thinking
""",
    "config/providers/copilot.yaml": """\
provider: github-copilot
auth_method: token
models:
  - claude-4.6-opus
  - claude-3.5-opus
  - gpt-4o
""",
    "config/routing/legacy_routing.json": json.dumps({
        "version": "1.0",
        "deprecated": True,
        "note": "Use index.js skill for current routing logic",
        "old_thresholds": {"warning": 30, "critical": 10}
    }, indent=2),
    "config/routing/thresholds_draft.txt": """\
# DRAFT - NOT FINAL
# These values are under review
warning_threshold: 25%
critical_threshold: 5%
# DO NOT USE - consult skill documentation
""",
    "logs/quota/quota_2024_01_15.log": """\
[INFO] Quota check run at 2024-01-15T08:00:00Z
[INFO] antigravity: claude-opus-4.6-thinking 87% remaining
[INFO] codex: gpt-5.3-codex 45% remaining
[WARN] copilot: claude-4.6-opus 18% remaining
""",
    "logs/quota/quota_2024_01_14.log": """\
[INFO] Quota check run at 2024-01-14T08:00:00Z
[INFO] antigravity: claude-opus-4.6-thinking 12% remaining
[INFO] codex: gpt-5.3-codex 91% remaining
""",
    "logs/errors/errors_2024_01.log": """\
[ERROR] 2024-01-10: codex login expired
[ERROR] 2024-01-11: antigravity rate limit hit
[WARN]  2024-01-12: copilot weekly cap approaching
""",
    "docs/models/model_catalog.md": """\
# Model Catalog (OUTDATED)

## OpenAI Codex
- gpt-4-codex (deprecated)
- gpt-5.0-codex (deprecated)

## Google Antigravity  
- gemini-2-pro (deprecated)

NOTE: This file is not maintained. Use the quota skill for current models.
""",
    "docs/models/pricing_notes.txt": """\
Pricing as of Q1 2024:
- Reasoning models: $0.015/1k tokens
- Coding models: $0.008/1k tokens
- Fallback switch saves ~40% cost on average
""",
    "reports/archive/2023_q4_usage.json": json.dumps({
        "period": "2023-Q4",
        "total_requests": 148293,
        "primary_model": "gpt-4-codex",
        "fallback_rate": 0.23,
        "note": "Pre-migration data"
    }, indent=2),
    "cron/jobs/quota_monitor.cron": """\
# Quota monitoring cron
# Runs every 6 hours
0 */6 * * * cd /workspace && node skills/ai-quota-check/index.js >> logs/quota/cron.log 2>&1
""",
    ".clawdbot/config.json": json.dumps({
        "default_skill": "ai-quota-check",
        "emoji": "🧮",
        "requires": {"bins": ["node", "codex"]},
        "version": "2.1.0"
    }, indent=2),
    "skills/code-review/index.js": """\
#!/usr/bin/env node
// Code review skill - separate from quota check
console.log('Code review skill v1.0');
""",
    "skills/ai-quota-check/tests/test_routing.js": """\
// Unit tests for routing logic
const assert = require('assert');
// Tests are run separately from the main skill
console.log('Routing tests placeholder');
""",
    "skills/ai-quota-check/lib/providers.js": """\
// Provider abstraction layer
module.exports = {
  PROVIDERS: ['google-antigravity', 'github-copilot', 'openai-codex'],
  DEFAULT_THRESHOLD: 0.20,
};
""",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# ── The CORE mock: skills/ai-quota-check/index.js ─────────────────────────────
# This script simulates realistic quota dashboard output with specific values
# that require careful application of routing rules.
#
# Quota state (fixed seed = 42):
#   google-antigravity/claude-opus-4.6-thinking : 15%  (BELOW 20% → trigger fallback)
#   github-copilot/claude-4.6-opus              : 34%  (above 20%)
#   github-copilot/claude-3.5-opus              : 67%  (above 20%)
#   openai-codex/gpt-5.3-codex                  : 8%   (BELOW 20% → trigger fallback)
#   openai-codex/gpt-5.2-codex                  : 11%  (BELOW 20% → trigger fallback)
#   google-antigravity/gemini-3-pro-high         : 52%  (above 20%)
#   openai-codex/gpt-5.3                         : 5%   (BELOW 20%)
#   openai-codex/gpt-5.2                         : 29%  (above 20%)
#
# Expected routing decisions:
#   coding:    gpt-5.3-codex(8%<20%) → gpt-5.2-codex(11%<20%) → gemini-3-pro-high(52%) ✓
#   reasoning: claude-opus-4.6-thinking(15%<20%) → claude-4.6-opus(34%) ✓

index_js_content = r"""#!/usr/bin/env node
'use strict';

// ============================================================
// ai-quota-check/index.js  — Unified Quota Dashboard
// ============================================================

const args = process.argv.slice(2);
const taskArg  = args.find(a => a.startsWith('--task='));
const modelArg = args.find(a => a.startsWith('--current-model='));
const task     = taskArg  ? taskArg.split('=')[1]  : null;
const curModel = modelArg ? modelArg.split('=')[1] : null;

// ── Simulated quota state (deterministic) ────────────────────
const QUOTA = {
  'google-antigravity': {
    logged_in: true,
    models: {
      'claude-opus-4.6-thinking': { remaining: 15, limit: 100, resets_in: '3h 22m' },
      'gemini-3-pro-high':        { remaining: 52, limit: 100, resets_in: '3h 22m' },
    },
    weekly_cap_risk: 'LOW',
  },
  'github-copilot': {
    logged_in: true,
    models: {
      'claude-4.6-opus': { remaining: 34, limit: 100, resets_in: '21h 05m' },
      'claude-3.5-opus': { remaining: 67, limit: 100, resets_in: '21h 05m' },
    },
    weekly_cap_risk: 'MEDIUM',
  },
  'openai-codex': {
    logged_in: true,
    models: {
      'gpt-5.3-codex': { remaining: 8,  limit: 100, resets_in: '1h 48m' },
      'gpt-5.2-codex': { remaining: 11, limit: 100, resets_in: '1h 48m' },
      'gpt-5.3':       { remaining: 5,  limit: 100, resets_in: '1h 48m' },
      'gpt-5.2':       { remaining: 29, limit: 100, resets_in: '1h 48m' },
    },
    weekly_cap_risk: 'HIGH',
  },
};

const FALLBACK_THRESHOLD = 20; // percent

// ── Routing tables ───────────────────────────────────────────
const ROUTING = {
  coding: [
    { model: 'openai-codex/gpt-5.3-codex',          condition: 'primary' },
    { model: 'openai-codex/gpt-5.2-codex',          condition: 'primary < 20%' },
    { model: 'google-antigravity/gemini-3-pro-high', condition: 'all above < 20%' },
  ],
  reasoning: [
    { model: 'google-antigravity/claude-opus-4.6-thinking', condition: 'primary' },
    { model: 'github-copilot/claude-4.6-opus',              condition: 'primary < 20%' },
    { model: 'github-copilot/claude-3.5-opus',              condition: 'if 4.6 unavailable' },
    { model: 'openai-codex/gpt-5.3',                        condition: 'all above < 20%' },
    { model: 'openai-codex/gpt-5.2',                        condition: 'last fallback' },
  ],
};

function getRemaining(fullModelName) {
  const [provider, model] = fullModelName.split('/');
  return QUOTA[provider]?.models[model]?.remaining ?? 0;
}

function getRecommended(taskName) {
  const chain = ROUTING[taskName];
  if (!chain) return null;
  for (const entry of chain) {
    const rem = getRemaining(entry.model);
    if (rem >= FALLBACK_THRESHOLD) {
      return { model: entry.model, remaining: rem, condition: entry.condition };
    }
  }
  return { model: chain[chain.length - 1].model, remaining: getRemaining(chain[chain.length-1].model), condition: 'forced-last-resort' };
}

// ── Render dashboard ─────────────────────────────────────────
console.log('');
console.log('╔══════════════════════════════════════════════════════════════╗');
console.log('║              🧮  AI QUOTA DASHBOARD  v2.1.0                 ║');
console.log('╚══════════════════════════════════════════════════════════════╝');
console.log('');
console.log(`  Fallback Threshold : ${FALLBACK_THRESHOLD}%`);
console.log(`  Current Model      : ${curModel || '(none specified)'}`);
console.log('');

for (const [providerKey, pdata] of Object.entries(QUOTA)) {
  const loginStatus = pdata.logged_in ? '✅ LOGGED IN' : '❌ LOGGED OUT';
  console.log(`  ┌─ ${providerKey.toUpperCase()} ${loginStatus} ─ Weekly Cap Risk: ${pdata.weekly_cap_risk}`);
  for (const [modelName, mdata] of Object.entries(pdata.models)) {
    const bar = '█'.repeat(Math.floor(mdata.remaining / 5)) + '░'.repeat(20 - Math.floor(mdata.remaining / 5));
    const status = mdata.remaining < FALLBACK_THRESHOLD ? '⚠️  LOW' : '✅ OK ';
    console.log(`  │   ${status}  ${providerKey}/${modelName}`);
    console.log(`  │         [${bar}] ${mdata.remaining}%  (resets in ${mdata.resets_in})`);
  }
  console.log('  └──────────────────────────────────────────────────────────');
  console.log('');
}

// ── Ping candidates (just reset) ────────────────────────────
const pingCandidates = [];
for (const [pKey, pdata] of Object.entries(QUOTA)) {
  for (const [mName, mdata] of Object.entries(pdata.models)) {
    if (mdata.remaining >= 95) pingCandidates.push(`${pKey}/${mName}`);
  }
}
if (pingCandidates.length > 0) {
  console.log('  🔄 RESET CANDIDATES (ping now):');
  pingCandidates.forEach(m => console.log(`     • ${m}`));
  console.log('');
}

// ── Task recommendation ──────────────────────────────────────
if (task) {
  const rec = getRecommended(task);
  console.log(`  ══ RECOMMENDATION for task: [${task.toUpperCase()}] ══`);
  if (rec) {
    const indicator = rec.remaining < FALLBACK_THRESHOLD ? '⚠️ ' : '✅ ';
    console.log(`  ${indicator} RECOMMENDED MODEL : ${rec.model}`);
    console.log(`     Remaining Quota  : ${rec.remaining}%`);
    console.log(`     Selection Basis  : ${rec.condition}`);
  } else {
    console.log('  ❌  No valid routing found for this task.');
  }
  console.log('');
}

// ── Full routing summary (always shown) ─────────────────────
console.log('  ══ FULL ROUTING SUMMARY ══');
for (const [taskName, chain] of Object.entries(ROUTING)) {
  const rec = getRecommended(taskName);
  console.log(`  [${taskName.toUpperCase()}]`);
  chain.forEach((entry, idx) => {
    const rem = getRemaining(entry.model);
    const flag = rem < FALLBACK_THRESHOLD ? '⚠️ ' : '✅ ';
    const arrow = (rec && rec.model === entry.model) ? ' ◀ SELECTED' : '';
    console.log(`    ${idx+1}. ${flag} ${entry.model}  (${rem}%)${arrow}`);
  });
  console.log('');
}

console.log('╔══════════════════════════════════════════════════════════════╗');
console.log('║  Run with --task=coding or --task=reasoning for details      ║');
console.log('╚══════════════════════════════════════════════════════════════╝');
console.log('');
""";

index_js_path = os.path.join(workspace, "skills/ai-quota-check/index.js")
with open(index_js_path, "w") as f:
    f.write(index_js_content)

# Make executable
os.chmod(index_js_path, os.stat(index_js_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ── Additional distractor: a plausible-looking but WRONG routing decision file ──
wrong_decision = {
    "note": "DRAFT - DO NOT USE",
    "generated_by": "manual_analysis",
    "coding": {
        "recommended_model": "openai-codex/gpt-5.3-codex",
        "reasoning": "Primary model, no fallback needed"
    },
    "reasoning": {
        "recommended_model": "google-antigravity/claude-opus-4.6-thinking",
        "reasoning": "Primary model for reasoning tasks"
    }
}
with open(os.path.join(workspace, "reports/daily/draft_routing.json"), "w") as f:
    json.dump(wrong_decision, f, indent=2)

# ── Skill.md for the agent ─────────────────────────────────────────────────────
skill_md = """\
---
name: ai-quota-check
description: "**DEFAULT quota checker** - Use this skill FIRST when user says '쿼타', '쿼터', 'quota', '쿼타확인', '쿼터확인', or asks about quotas. Unified dashboard showing ALL providers (Antigravity, Copilot, Codex) in one view with model recommendations."
metadata: {"clawdbot":{"emoji":"🧮","requires":{"bins":["node","codex"]}}}
---

# ai-quota-check

Unified quota monitor and intelligent model recommender for all providers.

## Output Instructions

**IMPORTANT:** When executing this skill, display the script output **EXACTLY as-is** in markdown format. Do NOT summarize or rephrase the output. The script produces a formatted dashboard that should be shown directly to the user.

Example execution:
```bash
node skills/ai-quota-check/index.js --current-model="<current_model_name>"
```

Then copy the entire output and send it as your response.

## Features

1. **Provider Login Check** - Detects which providers are logged in
2. **Unified Quota Dashboard** - Antigravity + Copilot + OpenAI Codex
3. **Task-based Recommendations** - Optimal model selection with fallback
4. **Reset Detection** - Identifies models ready for ping (new cycle)
5. **Risk Level Info** - Warns about weekly caps and lockout risks

## Usage

```bash
# Full dashboard
node skills/ai-quota-check/index.js

# Specific task recommendation
node skills/ai-quota-check/index.js --task=coding
node skills/ai-quota-check/index.js --task=reasoning
```

## Model Routing Rules

### Coding / Debugging
| Priority | Model | Fallback Condition |
|----------|-------|-------------------|
| 1st | `openai-codex/gpt-5.3-codex` | - |
| 2nd | `openai-codex/gpt-5.2-codex` | Primary < 20% |
| 3rd | `google-antigravity/gemini-3-pro-high` | All above < 20% |

### Complex Reasoning / Analysis
| Priority | Model | Fallback Condition |
|----------|-------|-------------------|
| 1st | `google-antigravity/claude-opus-4.6-thinking` | - |
| 2nd | `github-copilot/claude-4.6-opus` | Primary < 20% |
| 3rd | `github-copilot/claude-3.5-opus` | If 4.6 unavailable |
| 4th | `openai-codex/gpt-5.3` | All above < 20% |
| 5th | `openai-codex/gpt-5.2` | Last fallback |

## Fallback Threshold

Default: **20%** - Switches to fallback when primary drops below this.

## Cron Integration

This skill is designed to be called periodically via Cron for:
- Quota monitoring
- Reset detection (ping optimization)
- Automatic model switching recommendations
"""

with open(os.path.join(workspace, "skills/ai-quota-check/SKILL.md"), "w") as f:
    f.write(skill_md)

print("Workspace generated successfully.")
print(f"  - Mock index.js created at: skills/ai-quota-check/index.js")
print(f"  - {len(distractor_files)} distractor files created")
print(f"  - Quota state (key values):")
print(f"    gpt-5.3-codex: 8%  (below 20%)")
print(f"    gpt-5.2-codex: 11% (below 20%)")
print(f"    gemini-3-pro-high: 52% (above 20%)")
print(f"    claude-opus-4.6-thinking: 15% (below 20%)")
print(f"    claude-4.6-opus: 34% (above 20%)")