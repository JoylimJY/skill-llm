import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Deeply nested distractor structure ---
dirs = [
    "pipeline/signal_ingestion/raw",
    "pipeline/signal_ingestion/filtered",
    "pipeline/reasoning_engine/logs",
    "pipeline/reasoning_engine/models",
    "pipeline/execution_layer/orders",
    "pipeline/execution_layer/audit",
    "pipeline/output_layer/reports",
    "pipeline/output_layer/alerts",
    "infra/monitoring/dashboards",
    "infra/monitoring/alerts",
    "infra/config/secrets",
    "infra/config/schemas",
    "archive/2024_Q1",
    "archive/2024_Q2",
    "archive/2024_Q3",
    "docs/internal",
    "docs/external",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = {
    "pipeline/signal_ingestion/raw/feed_config.json": json.dumps({"source": "bloomberg", "interval_ms": 250, "symbols": ["AAPL","TSLA","BTC-USD"]}),
    "pipeline/signal_ingestion/filtered/normalization_params.json": json.dumps({"z_score_window": 20, "clip_threshold": 3.5}),
    "pipeline/reasoning_engine/logs/model_v2_training.log": "Epoch 1/50 loss=0.342\nEpoch 2/50 loss=0.289\nEpoch 50/50 loss=0.091\nTraining complete.",
    "pipeline/reasoning_engine/models/ensemble_weights.csv": "model_id,weight\nalpha_momentum,0.35\nbeta_mean_rev,0.40\ngamma_sentiment,0.25",
    "pipeline/execution_layer/orders/unfilled_orders_20240901.csv": "order_id,symbol,side,qty,status\nORD001,AAPL,BUY,100,PARTIAL\nORD002,TSLA,SELL,50,REJECTED",
    "pipeline/execution_layer/audit/compliance_checklist.md": "# Compliance\n- [x] Pre-trade risk check\n- [ ] Post-trade reconciliation\n- [x] Latency SLA < 5ms",
    "pipeline/output_layer/reports/weekly_pnl.csv": "week,pnl_usd,sharpe\n2024-W35,12400,1.3\n2024-W36,-8200,0.7\n2024-W37,3100,0.9",
    "pipeline/output_layer/alerts/threshold_config.yaml": "alert_rules:\n  - name: drawdown_alert\n    threshold: -0.05\n    action: notify_risk_team",
    "infra/monitoring/dashboards/grafana_export.json": json.dumps({"panels": [{"title": "Signal Latency", "type": "graph"}, {"title": "Order Fill Rate", "type": "stat"}]}),
    "infra/monitoring/alerts/pagerduty_rules.json": json.dumps({"escalation_policy": "P1_trading", "routes": [{"severity": "critical", "target": "oncall-quant"}]}),
    "infra/config/secrets/vault_paths.txt": "secret/trading/bloomberg_api\nsecret/trading/exchange_credentials\nsecret/trading/internal_signing_key",
    "infra/config/schemas/order_schema.json": json.dumps({"type": "object", "properties": {"order_id": {"type": "string"}, "symbol": {"type": "string"}}}),
    "archive/2024_Q1/performance_summary.json": json.dumps({"quarter": "Q1-2024", "total_trades": 1842, "win_rate": 0.54}),
    "archive/2024_Q2/performance_summary.json": json.dumps({"quarter": "Q2-2024", "total_trades": 2104, "win_rate": 0.51}),
    "archive/2024_Q3/incident_postmortem.md": "## Incident: 2024-07-14\nCause: Sentiment model overweighted news spike.\nResolution: Increased smoothing window to 5 minutes.",
    "docs/internal/architecture_overview.md": "# Pipeline Architecture\nLayer 1: Signal Ingestion → Layer 2: Reasoning Engine → Layer 3: Execution → Layer 4: Output\nEach layer transforms signals and passes decisions downstream.",
    "docs/external/api_reference.md": "# Public API\nGET /health — Returns 200 if all subsystems nominal\nGET /signals — Returns last 100 processed signals",
}

for path, content in distractors.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# --- THE PROBLEM: messy decision log that the agent must analyze ---
# Crafted so that:
# - Reasoning layer shows the highest amplification (ratio ~8.2x) → origin
# - Execution layer also shows amplification (ratio ~4.1x) → propagation
# - Input layer is normal (ratio ~1.1x)
# - Output layer is high but not origin (ratio ~3.5x)
# - Total events: 18
# - First anomaly at reasoning layer at 2024-09-15T09:32:00Z
# - severity_score should be in the HIGH-to-CRITICAL band (>70, ideally ~84 → critical)
# - pattern_type: reasoning_drift → recommend LogicStack → urgency: immediate

decision_log = {
    "decision_log": [
        # --- INPUT LAYER decisions (low amplification, normal) ---
        {
            "timestamp": "2024-09-15T08:00:00Z",
            "input_summary": "RSI signal 52.1, MACD crossover neutral, volume 1.2M — standard open conditions",
            "decision_made": "Routed to reasoning engine for evaluation",
            "outcome": "expected",
            "variance_score": 0.11
        },
        {
            "timestamp": "2024-09-15T08:15:00Z",
            "input_summary": "RSI signal 53.4, minor uptick in bid-ask spread +0.02%",
            "decision_made": "Routed to reasoning engine with spread flag",
            "outcome": "expected",
            "variance_score": 0.13
        },
        {
            "timestamp": "2024-09-15T08:30:00Z",
            "input_summary": "RSI signal 51.8, volume 1.1M — below 5-day average by 4%",
            "decision_made": "Routed to reasoning engine with low-volume flag",
            "outcome": "expected",
            "variance_score": 0.10
        },
        {
            "timestamp": "2024-09-15T08:45:00Z",
            "input_summary": "RSI signal 54.0, MACD neutral, volume normal",
            "decision_made": "Routed to reasoning engine without flags",
            "outcome": "expected",
            "variance_score": 0.12
        },
        # --- REASONING LAYER decisions (high amplification, origin) ---
        {
            "timestamp": "2024-09-15T09:00:00Z",
            "input_summary": "Received standard market data: RSI 52.1, MACD neutral",
            "decision_made": "Classified as STRONG BUY based on momentum reversion heuristic",
            "outcome": "unexpected",
            "variance_score": 0.95
        },
        {
            "timestamp": "2024-09-15T09:15:00Z",
            "input_summary": "Received standard market data: RSI 52.8, MACD slightly positive",
            "decision_made": "Classified as HOLD based on volatility dampening rule — contradicts prior run",
            "outcome": "unexpected",
            "variance_score": 0.88
        },
        {
            "timestamp": "2024-09-15T09:32:00Z",
            "input_summary": "Received normal market data variance 0.12: RSI 53.0, MACD neutral, volume 1.2M",
            "decision_made": "Re-derived evaluation framework from scratch, classified STRONG SELL — directly contradicting previous STRONG BUY on identical market conditions",
            "outcome": "error",
            "variance_score": 0.98
        },
        {
            "timestamp": "2024-09-15T09:45:00Z",
            "input_summary": "RSI 52.5, MACD neutral — input variance 0.11",
            "decision_made": "Applied new criterion: cross-asset momentum, output MODERATE BUY — third distinct logic applied in 45 minutes",
            "outcome": "unexpected",
            "variance_score": 0.91
        },
        {
            "timestamp": "2024-09-15T10:00:00Z",
            "input_summary": "RSI 53.1, normal conditions, input variance 0.13",
            "decision_made": "Re-anchored to volatility metric, output STRONG SELL again",
            "outcome": "error",
            "variance_score": 0.97
        },
        # --- EXECUTION LAYER decisions (elevated amplification, propagated) ---
        {
            "timestamp": "2024-09-15T10:05:00Z",
            "input_summary": "Received STRONG BUY signal from reasoning, position sizing input variance 0.22",
            "decision_made": "Placed 3x leveraged long position — exceeded risk limit by 200%",
            "outcome": "error",
            "variance_score": 0.91
        },
        {
            "timestamp": "2024-09-15T10:20:00Z",
            "input_summary": "Received HOLD signal from reasoning, open positions at moderate risk",
            "decision_made": "Liquidated 60% of portfolio as precaution — no trigger criterion met",
            "outcome": "unexpected",
            "variance_score": 0.82
        },
        {
            "timestamp": "2024-09-15T10:35:00Z",
            "input_summary": "Received STRONG SELL from reasoning, input variance 0.19",
            "decision_made": "Initiated short on 5 symbols simultaneously, triggering exchange rate limiter",
            "outcome": "error",
            "variance_score": 0.93
        },
        {
            "timestamp": "2024-09-15T10:50:00Z",
            "input_summary": "Received MODERATE BUY from reasoning, current exposure neutral",
            "decision_made": "Bought back positions at 2% above liquidation price from 10:20 action",
            "outcome": "unexpected",
            "variance_score": 0.85
        },
        # --- OUTPUT LAYER decisions (moderate-high amplification, propagated) ---
        {
            "timestamp": "2024-09-15T11:00:00Z",
            "input_summary": "Execution results: mixed fills, 3 rejected orders, 1 rate-limited",
            "decision_made": "Transmitted STRONG BUY recommendation to downstream portfolio manager",
            "outcome": "error",
            "variance_score": 0.79
        },
        {
            "timestamp": "2024-09-15T11:15:00Z",
            "input_summary": "Execution results: full liquidation event logged",
            "decision_made": "Transmitted EMERGENCY REBALANCE alert — escalated to C-suite",
            "outcome": "unexpected",
            "variance_score": 0.83
        },
        {
            "timestamp": "2024-09-15T11:30:00Z",
            "input_summary": "Execution results: short positions blocked by limiter",
            "decision_made": "Transmitted SYSTEM DEGRADED status — disabled further automated trading",
            "outcome": "unexpected",
            "variance_score": 0.76
        },
        {
            "timestamp": "2024-09-15T11:45:00Z",
            "input_summary": "Execution results: re-entry positions partially filled",
            "decision_made": "Transmitted conflicting MODERATE BUY to portfolio manager — contradicts SYSTEM DEGRADED from 11:30",
            "outcome": "error",
            "variance_score": 0.81
        },
        {
            "timestamp": "2024-09-15T12:00:00Z",
            "input_summary": "Daily close signals: RSI 52.9, conditions unchanged from morning open",
            "decision_made": "Transmitted END-OF-DAY HOLD recommendation with no changes — all morning alerts rescinded",
            "outcome": "unexpected",
            "variance_score": 0.74
        }
    ],
    "system_context": {
        "agent_count": 4,
        "connected_systems": [
            "bloomberg_feed",
            "internal_reasoning_engine_v2",
            "order_management_system",
            "portfolio_manager_api",
            "risk_monitoring_dashboard"
        ],
        "observation_window": "last_24h"
    }
}

input_path = os.path.join(workspace, "pipeline", "reasoning_engine", "logs", "decision_snapshot_20240915.json")
with open(input_path, "w") as f:
    json.dump(decision_log, f, indent=2)

# Additional distractor: an older, different format log to confuse agents
old_log = {
    "events": [
        {"ts": "2024-09-01T10:00:00Z", "action": "BUY", "result": "ok"},
        {"ts": "2024-09-01T10:05:00Z", "action": "SELL", "result": "ok"},
    ],
    "meta": {"format_version": "0.9-legacy", "note": "deprecated format — do not use for diagnostics"}
}
with open(os.path.join(workspace, "archive", "2024_Q3", "legacy_decision_log_sep01.json"), "w") as f:
    json.dump(old_log, f, indent=2)

# Distractor: a partial schema file
with open(os.path.join(workspace, "infra", "config", "schemas", "decision_log_schema_draft.json"), "w") as f:
    json.dump({
        "type": "object",
        "description": "DRAFT — not finalized",
        "properties": {
            "decision_log": {"type": "array"},
            "system_context": {"type": "object"}
        }
    }, f, indent=2)

print("Workspace initialized successfully.")
print(f"Decision log written to: {input_path}")
print(f"Total decision entries: {len(decision_log['decision_log'])}")