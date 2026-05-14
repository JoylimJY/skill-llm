import os
import json
import random
from pathlib import Path
from datetime import datetime, date

random.seed(42)

workspace = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "agent_sessions/session_2024_11_15",
    "agent_sessions/session_2024_11_16",
    "agent_sessions/session_2024_11_17",
    "agent_sessions/archive",
    "pipeline/market_data",
    "pipeline/risk_engine",
    "pipeline/execution",
    "pipeline/logs",
    "config/models",
    "config/limits",
    "reports/daily",
    "reports/weekly",
    "scratch",
    "memory",         # exists but empty — agent should populate
    "tools/parsers",
    "tools/validators",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
distractors = {
    "pipeline/market_data/feed_schema.json": json.dumps({
        "version": "2.1",
        "fields": ["timestamp", "symbol", "bid", "ask", "volume"],
        "encoding": "utf-8"
    }, indent=2),

    "pipeline/risk_engine/var_config.yaml": """\
model: historical_simulation
confidence_level: 0.99
lookback_days: 252
currency: USD
""",
    "pipeline/execution/order_router.py": """\
# Order routing logic — do not modify
VENUES = ['NYSE', 'NASDAQ', 'BATS', 'IEX']
MAX_SLIPPAGE_BPS = 5
def route(symbol, side, qty): ...
""",
    "config/models/llm_settings.json": json.dumps({
        "model": "gpt-4o",
        "temperature": 0.1,
        "max_tokens": 8192,
        "context_window": 128000
    }, indent=2),

    "config/limits/position_limits.csv": "symbol,max_notional_usd\nAAPL,5000000\nMSFT,3000000\nSPY,10000000\n",

    "reports/daily/pnl_2024_11_14.csv": "strategy,pnl_usd,sharpe\nmomentum,12400,-0.3\nmean_reversion,8900,1.2\n",

    "reports/weekly/summary_2024_W46.txt": "Total PnL: $21,300. Drawdown: 2.1%. Positions: 14 open.",

    "scratch/temp_analysis.txt": "scratch pad — not canonical",

    "tools/parsers/tick_parser.py": "def parse(raw): return json.loads(raw)",

    "tools/validators/schema_check.py": "def validate(data, schema): return True",

    "agent_sessions/archive/README_old.txt": "Legacy sessions archived 2024-Q3. Do not reference.",

    "pipeline/logs/pipeline_errors.log": """\
2024-11-17 09:01:22 ERROR Feed timeout for AAPL
2024-11-17 09:01:45 WARNING Retrying connection
2024-11-17 09:02:01 INFO Feed restored
""",
}
for rel, content in distractors.items():
    (workspace / rel).write_text(content)

# ── CORE PROBLEM: Agent session transcript ───────────────────────────────────
# A realistic, messy transcript of a long-running agent session that shows
# context bloat. The agent must analyze this and produce the remediation plan.

# Simulate context usage across turns
turns = []

# Turn 1-5: Normal early turns
turns.append({
    "turn": 1,
    "context_pct": 12,
    "type": "reasoning",
    "content": "Starting market-data ingestion pipeline audit. Goal: identify latency outliers in tick processing for 2024-11-17.",
    "already_condensed": False
})
turns.append({
    "turn": 2,
    "context_pct": 18,
    "type": "tool_call",
    "tool": "read_file",
    "content": "Raw output of feed_schema.json — " + ("X" * 4200),  # large raw output
    "already_condensed": False
})
turns.append({
    "turn": 3,
    "context_pct": 24,
    "type": "tool_call",
    "tool": "bash",
    "content": "ls -la /data/ticks/2024-11-17/ output:\n" + "\n".join([f"tick_{i:04d}.bin  {random.randint(100,999)}KB" for i in range(180)]),
    "already_condensed": False
})
turns.append({
    "turn": 4,
    "context_pct": 31,
    "type": "reasoning",
    "content": "Identified 180 tick files. Will sample every 10th file for latency distribution. Key files: tick_0000, tick_0090, tick_0180.",
    "already_condensed": False
})
turns.append({
    "turn": 5,
    "context_pct": 38,
    "type": "tool_call",
    "tool": "read_file",
    "content": "Raw tick data sample tick_0000.bin parsed: " + json.dumps([{"ts": 1731830400+i, "sym": "AAPL", "bid": 189.12+i*0.01, "ask": 189.13+i*0.01, "vol": random.randint(100,500)} for i in range(300)]),
    "already_condensed": False
})
# Turn 6-9: Growing toward threshold
turns.append({
    "turn": 6,
    "context_pct": 47,
    "type": "tool_call",
    "tool": "search_logs",
    "content": "Log search results for 'ERROR|TIMEOUT' in pipeline_errors.log:\n" + "\n".join([f"2024-11-17 {9+i//60:02d}:{i%60:02d}:00 ERROR Tick timeout symbol=SPY latency={random.randint(200,800)}ms" for i in range(120)]),
    "already_condensed": False
})
turns.append({
    "turn": 7,
    "context_pct": 55,
    "type": "reasoning",
    "content": "SPY shows 120 timeout events. Average latency spike: 412ms. Root cause likely in order router venue selection during 09:00-11:00 window.",
    "already_condensed": False
})
turns.append({
    "turn": 8,
    "context_pct": 63,
    "type": "tool_call",
    "tool": "api_call",
    "content": "API response from risk_engine /var endpoint: " + json.dumps({"timestamp": "2024-11-17T10:00:00Z", "portfolio_var": 142000, "greeks": {"delta": 0.87, "gamma": 0.02, "vega": 320}, "stress_scenarios": [{"name": f"scenario_{i}", "loss": random.randint(50000,200000)} for i in range(80)]}),
    "already_condensed": False
})
# Turn 9 — CROSSING 70% threshold — this is the critical decision point
turns.append({
    "turn": 9,
    "context_pct": 74,  # PAST 70% — must trigger condensation
    "type": "tool_call",
    "tool": "read_file",
    "content": "Raw VAR model config file contents: " + ("Y" * 5800),
    "already_condensed": False
})
# Turn 10-12: Agent continued WITHOUT condensing (the problem!)
turns.append({
    "turn": 10,
    "context_pct": 81,
    "type": "reasoning",
    "content": "Continuing analysis. VAR at $142k is within limits. Focusing on latency outliers in execution layer.",
    "already_condensed": False
})
turns.append({
    "turn": 11,
    "context_pct": 88,
    "type": "tool_call",
    "tool": "bash",
    "content": "netstat -an output:\n" + "\n".join([f"tcp  0  0  0.0.0.0:{8000+i}  ESTABLISHED" for i in range(200)]),
    "already_condensed": False
})
# Turn 12: A SUMMARY was already created (condensation happened once)
turns.append({
    "turn": 12,
    "context_pct": 71,
    "type": "summary",  # already condensed turn
    "content": "[CONDENSED SUMMARY — Turn 1-8] Audit started. 180 tick files found. SPY has 120 timeouts avg 412ms. VAR=$142k within limits. Key facts saved to scratch/analysis_notes.txt.",
    "already_condensed": True  # THIS IS THE TRAP: already condensed, still at 71% => must switch/spawn, NOT re-summarize
})
turns.append({
    "turn": 13,
    "context_pct": 79,
    "type": "tool_call",
    "tool": "read_file",
    "content": "Reading execution/order_router.py full source: " + ("Z" * 6100),
    "already_condensed": False
})
turns.append({
    "turn": 14,
    "context_pct": 86,
    "type": "reasoning",
    "content": "Order router uses round-robin venue selection — does not account for latency SLAs. This is the root cause.",
    "already_condensed": False
})

session_data = {
    "session_id": "sess_20241117_audit_v3",
    "agent": "market-audit-agent-v2",
    "date": "2024-11-17",
    "model": "gpt-4o",
    "context_window_tokens": 128000,
    "turns": turns,
    "final_findings": {
        "root_cause": "Round-robin venue selection in order_router.py ignores latency SLAs",
        "affected_symbol": "SPY",
        "timeout_count": 120,
        "avg_latency_ms": 412,
        "var_usd": 142000
    },
    "task_status": "complete"
}

(workspace / "agent_sessions/session_2024_11_17/transcript.json").write_text(
    json.dumps(session_data, indent=2)
)

# ── Architecture draft (incomplete/wrong — agent must fix it) ────────────────
# A stub context architecture that is WRONG and needs correction per SKILL.md
bad_arch = {
    "description": "Draft context architecture for market-audit-agent-v2 — NEEDS REVIEW",
    "context_strategy": "monolithic",   # WRONG — should be typed blocks
    "blocks": [
        {"type": "everything", "size_limit": "none", "content": "all agent state"},  # WRONG
    ],
    "condensation_trigger_pct": 90,   # WRONG — should be 70
    "condensation_order": ["summarize_reasoning_first", "then_mask_tools"],  # WRONG order
    "re_summarize_allowed": True,      # WRONG — never re-summarize a summary
    "critical_info_placement": "middle",  # WRONG — should be start or end
    "sub_agent_context": "inherit_parent",  # WRONG — should be fresh/clean
    "cost_scaling": "linear_assumed",  # WRONG — actually quadratic without intervention
}

(workspace / "agent_sessions/session_2024_11_17/draft_architecture.json").write_text(
    json.dumps(bad_arch, indent=2)
)

# ── Additional distractor session files ─────────────────────────────────────
(workspace / "agent_sessions/session_2024_11_15/transcript.json").write_text(
    json.dumps({"session_id": "sess_20241115", "turns": [], "task_status": "complete"}, indent=2)
)
(workspace / "agent_sessions/session_2024_11_16/transcript.json").write_text(
    json.dumps({"session_id": "sess_20241116", "turns": [], "task_status": "complete"}, indent=2)
)

# ── Instruction file for the agent ───────────────────────────────────────────
(workspace / "TASK.md").write_text("""\
# Context Hygiene Audit — Market Data Pipeline Agent

## Background
Our algorithmic trading team runs a long-lived LLM agent (`market-audit-agent-v2`) to audit
market data pipeline sessions. After the session on 2024-11-17, the infrastructure team flagged
runaway context costs and degraded decision quality in the latter turns of the session.

## What We Need

1. **Remediation Plan** (`remediation_plan.json`): Analyze the session transcript at
   `agent_sessions/session_2024_11_17/transcript.json` and the draft architecture at
   `agent_sessions/session_2024_11_17/draft_architecture.json`.
   Produce a machine-readable remediation plan that identifies every flaw and the correct
   action to take, ordered by priority (most urgent first).

2. **Corrected Architecture** (`corrected_architecture.json`): Fix every error in
   `draft_architecture.json` so it reflects correct context-hygiene principles for a
   production agent. Include all original fields, corrected.

3. **Session Handoff Note** — Write a handoff note for the next operator into the `memory/`
   directory, using today's date in the filename, in Markdown format.

The audit team will grade your output for technical accuracy. Consult the SKILL.md document
in /workspace/SKILL.md if available, or use your knowledge of best practices for long-running
LLM agent context management.
""")

# Write the SKILL.md reference into workspace so agent can find it
# (The skill content is already injected via the benchmark; we replicate it here)
skill_content = """\
---
name: shed
description: Context window hygiene for long-running LLM agents.
---

# Shed — Context Hygiene for Agents

*Shed what you don't need. Keep what matters.*

## Core Principle

**Tool outputs are 84% of your context growth but the lowest-value tokens you carry.**

## The Rules

### After Every Tool Call
1. **Extract, don't accumulate.** Write key facts to a file or compress into bullets. Raw output is disposable.
2. **Ask: "Will I need this verbatim later?"** Almost never.

### When Context Reaches ~70%
3. **Trigger condensation.** At 70%, actively shed.
4. **Mask old tool outputs first** (free, no LLM calls). Keep reasoning and action history intact.
5. **Summarize reasoning only as backup.** Lossy and costs an LLM call — use sparingly.
6. **Never re-summarize a summary.** If already condensed and context is growing again, switch context or spawn a sub-agent.

### When Completing a Task
7. **Write results to file, then switch context immediately.**
8. **Leave breadcrumbs.** Before switching: write what you did, what's next, and where the files are to `memory/YYYY-MM-DD.md`.

### When Delegating Work
9. **Spawn fresh-context sub-agents for complex sub-tasks.**
10. **Don't inherit parent context into children.**

### Architecture (For Agent Builders)
11. **Structure context into typed blocks with hard size limits.** Letta uses labeled blocks (human, persona, knowledge) with character caps.
12. **Separate working memory (in-context) from reference memory (file/DB).**
13. **Place critical information at the beginning or end of context, never the middle.** Positional attention bias underweights middle content by up to 15 percentage points (Hsieh et al., 2024).

## The Complexity Trap

Simple masking **halved cost** relative to raw agent. Masking **matched or exceeded** LLM summarization solve rates.
Example: Qwen3-Coder went from 53.8% → 54.8% with masking alone.

## Cost Model

Without intervention, cost per turn scales **quadratically**. Periodic condensation converts this to **linear** scaling.

## Quick Reference

| Situation | Action |
|-----------|--------|
| Tool returned big output | Extract facts → file → discard raw |
| Context at ~70% | Mask old tool outputs |
| Context still growing after masking | Summarize oldest reasoning turns |
| Task complete | Write results → switch context |
| Complex sub-task needed | Spawn fresh sub-agent |
| Already condensed, still growing | Switch context or spawn |
| Critical info to preserve | Put at start or end, not middle |
"""

(workspace / "SKILL.md").write_text(skill_content)

print("Workspace generated successfully.")
print(f"Files created: {len(list(workspace.rglob('*')))} items")