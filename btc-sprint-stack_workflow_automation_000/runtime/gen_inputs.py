#!/usr/bin/env python3
"""
Generate the BTC Sprint Stack sandbox workspace.
Creates a realistic but deliberately misconfigured workspace that the agent must fix and operate.
"""
import os
import json
import random
import time
from pathlib import Path

random.seed(42)
WORKSPACE = Path("/workspace")

# ── directory structure ────────────────────────────────────────────────────────
dirs = [
    "skills/btc-sprint-stack/modules",
    "skills/btc-sprint-stack/config",
    "skills/btc-sprint-stack/data",
    "skills/btc-sprint-stack/logs",
    "skills/btc-sprint-stack/archive",
    "skills/btc-sprint-stack/tests",
    "skills/eth-momentum/modules",         # distractor: different coin
    "skills/eth-momentum/config",
    "shared/utils",
    "shared/models",
    "infra/docker",
    "infra/monitoring",
    "docs/runbooks",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

BASE = WORKSPACE / "skills/btc-sprint-stack"

# ══════════════════════════════════════════════════════════════════════════════
# DISTRACTOR FILES
# ══════════════════════════════════════════════════════════════════════════════

# Old archived config (wrong format, should be ignored)
(BASE / "archive/defaults_v0.json").write_text(json.dumps({
    "max_bankroll_pct": 0.5,
    "skill_slug": "btc-sprint-stack-legacy",
    "dry_run": False,
    "fee_rate": 0.001,
}, indent=2))

# ETH momentum distractor skill
(WORKSPACE / "skills/eth-momentum/config/defaults.json").write_text(json.dumps({
    "max_bankroll_pct": 0.1,
    "skill_slug": "eth-momentum",
    "dry_run": True,
    "fee_rate": 0.002,
    "target_markets": ["eth_5m", "eth_15m"],
}, indent=2))
(WORKSPACE / "skills/eth-momentum/modules/__init__.py").write_text("")

# Stale log files
(BASE / "logs/run_20240101.log").write_text(
    "[2024-01-01 00:00:00] INFO  run started\n"
    "[2024-01-01 00:00:05] INFO  0 trades executed\n"
    "[2024-01-01 00:00:05] INFO  run ended\n"
)
(BASE / "logs/run_20240102.log").write_text(
    "[2024-01-02 00:00:00] INFO  run started\n"
    "[2024-01-02 00:00:03] ERROR signal timeout\n"
)

# Stale journal entries from previous bad run (wrong format — not JSONL, just a JSON array)
(BASE / "archive/old_journal.json").write_text(json.dumps([
    {"timestamp": "2024-01-01T00:00:00Z", "market": "BTC_5m", "side": "YES",
     "amount": 10.0, "dry_run": True, "source": "old-source"},
], indent=2))

# Pending rules — valid but should not be modified by agent
(BASE / "data/pending_rules.json").write_text(json.dumps({
    "pending": [
        {"rule_id": "r001", "param": "min_edge", "suggested": 0.04, "reason": "reduce noise"},
        {"rule_id": "r002", "param": "confidence_floor", "suggested": 0.62, "reason": "tighten filter"},
    ],
    "applied": []
}, indent=2))

# Shared utilities distractors
(WORKSPACE / "shared/utils/math_utils.py").write_text(
    "# Shared math utilities\n"
    "def clamp(v, lo, hi): return max(lo, min(hi, v))\n"
)
(WORKSPACE / "shared/models/market.py").write_text(
    "# Market data model\n"
    "class Market:\n"
    "    def __init__(self, symbol, interval): self.symbol=symbol; self.interval=interval\n"
)

# Infra distractors
(WORKSPACE / "infra/docker/docker-compose.yml").write_text(
    "version: '3'\nservices:\n  bot:\n    image: btc-sprint:latest\n    restart: always\n"
)
(WORKSPACE / "infra/monitoring/alerts.yaml").write_text(
    "alerts:\n  - name: high_drawdown\n    threshold: 0.15\n    channel: slack\n"
)

# Docs distractor
(WORKSPACE / "docs/runbooks/recovery.md").write_text(
    "# Recovery Runbook\n\nIf the bot crashes, check `logs/` for the latest run log.\n"
    "Restore `data/live_params.json` from the last known good backup.\n"
)

# Test stubs distractor
(BASE / "tests/test_signal.py").write_text(
    "# Unit tests for signal module\n"
    "def test_placeholder(): assert True\n"
)

# ══════════════════════════════════════════════════════════════════════════════
# DELIBERATELY MISCONFIGURED config/defaults.json
# Problems:
#   1. skill_slug is wrong ("btc-sprint" instead of "btc-sprint-stack")
#   2. target_markets includes "eth_5m" (wrong coin)
#   3. max_bankroll_pct is a string instead of float (type error)
#   4. fee_rate missing entirely
#   5. dry_run is False (must be overridden to True by --dry-run flag)
# ══════════════════════════════════════════════════════════════════════════════
(BASE / "config/defaults.json").write_text(json.dumps({
    "skill_slug": "btc-sprint",            # WRONG — should be "btc-sprint-stack"
    "dry_run": False,                       # WRONG default (flag should enforce True)
    "max_bankroll_pct": "0.02",            # WRONG type — should be float 0.02
    "min_edge": 0.03,
    "confidence_floor": 0.60,
    "target_markets": ["btc_5m", "btc_15m", "eth_5m"],  # eth_5m is an intruder
    "spread_limit": 0.05,
    "signal_source": "btc_momentum_v1",
    "bankroll_usd": 1000.0,
    "max_position_usd": 50.0,
    "version": "0.1.0",
}, indent=2))

# ══════════════════════════════════════════════════════════════════════════════
# data/live_params.json — learned tunables that MUST override defaults
# The agent must ensure these take effect BEFORE any env overrides.
# ══════════════════════════════════════════════════════════════════════════════
(BASE / "data/live_params.json").write_text(json.dumps({
    "skill_slug": "btc-sprint-stack",      # CORRECT override
    "max_bankroll_pct": 0.02,              # CORRECT type override
    "min_edge": 0.035,                     # tuned value
    "confidence_floor": 0.61,             # tuned value
    "target_markets": ["btc_5m", "btc_15m"],  # BTC-only, correct
    "fee_rate": 0.002,                     # was missing in defaults
    "signal_source": "btc_momentum_v2",   # upgraded signal
}, indent=2))

# Empty llm_decisions.jsonl — agent must populate this
(BASE / "data/llm_decisions.jsonl").write_text("")

# ══════════════════════════════════════════════════════════════════════════════
# MAIN ORCHESTRATION: main.py
# Reads configs (defaults → live_params → env), runs signal/filter/executor,
# writes journal and heartbeat. Has a subtle bug: it currently reads configs
# in the WRONG order (env first, then live_params, then defaults).
# The agent must correct this so live_params override defaults but NOT env.
# ══════════════════════════════════════════════════════════════════════════════
(BASE / "main.py").write_text('''\
#!/usr/bin/env python3
"""BTC Sprint Stack — main orchestration entry point."""
import argparse
import json
import os
import sys
import time
from pathlib import Path

SKILL_DIR = Path(__file__).parent
sys.path.insert(0, str(SKILL_DIR))

from modules.btc_sprint_signal import BTCSprintSignal
from modules.btc_regime_filter import BTCRegimeFilter
from modules.btc_sprint_executor import BTCSprintExecutor
from modules.btc_position_manager import BTCPositionManager
from modules.btc_trade_journal import BTCTradeJournal
from modules.btc_self_learn import BTCSelfLearn
from modules.btc_heartbeat import BTCHeartbeat
from modules.btc_llm_decider import BTCLLMDecider


def load_config(skill_dir: Path, dry_run_flag: bool) -> dict:
    """
    Merge configuration layers.
    ORDER (lowest → highest priority):
      1. config/defaults.json        (base)
      2. data/live_params.json       (learned tunables — override defaults)
      3. Environment variables       (highest priority)
    """
    # Layer 1: defaults
    defaults_path = skill_dir / "config" / "defaults.json"
    config = {}
    if defaults_path.exists():
        with open(defaults_path) as f:
            raw = json.load(f)
        # Coerce types
        raw["max_bankroll_pct"] = float(raw.get("max_bankroll_pct", 0.02))
        config.update(raw)

    # Layer 2: live_params (override defaults)
    live_path = skill_dir / "data" / "live_params.json"
    if live_path.exists():
        with open(live_path) as f:
            live = json.load(f)
        config.update(live)

    # Layer 3: env overrides (highest priority)
    for key in ["MIN_EDGE", "CONFIDENCE_FLOOR", "MAX_BANKROLL_PCT", "FEE_RATE"]:
        env_val = os.environ.get(key)
        if env_val is not None:
            config[key.lower()] = float(env_val)

    # --dry-run flag always wins
    if dry_run_flag:
        config["dry_run"] = True

    # Enforce BTC-only markets
    config["target_markets"] = [
        m for m in config.get("target_markets", [])
        if m.startswith("btc_")
    ]

    # Validate skill_slug
    if config.get("skill_slug") != "btc-sprint-stack":
        raise ValueError(
            f"Invalid skill_slug: {config.get(\'skill_slug\')!r}. "
            "Must be \'btc-sprint-stack\'."
        )

    return config


def validate_real_path(skill_dir: Path) -> None:
    """Validate that all required module files exist."""
    required = [
        "modules/btc_sprint_signal.py",
        "modules/btc_regime_filter.py",
        "modules/btc_sprint_executor.py",
        "modules/btc_position_manager.py",
        "modules/btc_trade_journal.py",
        "modules/btc_self_learn.py",
        "modules/btc_heartbeat.py",
        "modules/btc_llm_decider.py",
        "config/defaults.json",
        "data/live_params.json",
    ]
    missing = [r for r in required if not (skill_dir / r).exists()]
    if missing:
        raise FileNotFoundError(f"Missing required files: {missing}")


def main():
    parser = argparse.ArgumentParser(description="BTC Sprint Stack")
    parser.add_argument("--once", action="store_true", help="Run one cycle and exit")
    parser.add_argument("--dry-run", action="store_true", help="Dry-run mode (no real orders)")
    parser.add_argument("--validate-real-path", action="store_true",
                        help="Validate all module paths exist before running")
    args = parser.parse_args()

    skill_dir = Path(__file__).parent

    if args.validate_real_path:
        validate_real_path(skill_dir)

    config = load_config(skill_dir, dry_run_flag=args.dry_run)

    # Initialise modules
    signal_mod   = BTCSprintSignal(config)
    filter_mod   = BTCRegimeFilter(config)
    executor     = BTCSprintExecutor(config)
    pos_mgr      = BTCPositionManager(config)
    journal      = BTCTradeJournal(skill_dir / "data" / "btc_trade_journal.jsonl")
    self_learn   = BTCSelfLearn(config, skill_dir / "data" / "pending_rules.json")
    heartbeat    = BTCHeartbeat(config, skill_dir / "data" / "heartbeat_summary.json")
    llm_decider  = BTCLLMDecider(config, skill_dir / "data" / "llm_decisions.jsonl")

    trades_this_run = []

    for market in config["target_markets"]:
        # 1. Generate signal
        signal = signal_mod.generate(market)

        # 2. Regime filter
        if not filter_mod.passes(signal, market):
            heartbeat.record_skip(market, reason="regime filter")
            continue

        # 3. Position sizing
        stake_usd = pos_mgr.size_position(signal)
        if stake_usd <= 0:
            heartbeat.record_skip(market, reason="bankroll limit")
            continue

        # 4. LLM decision
        decision = llm_decider.decide(signal, market, stake_usd)
        if decision is None:
            heartbeat.record_skip(market, reason="llm rejected")
            continue

        # 5. Execute (dry-run or live)
        result = executor.execute(decision, dry_run=config["dry_run"])

        # 6. Journal
        journal.write(result)

        trades_this_run.append(result)

    # 7. Self-learn suggestions
    self_learn.suggest(trades_this_run)

    # 8. Heartbeat summary
    heartbeat.finalize(trades_this_run)

    print(f"[btc-sprint-stack] Run complete. Trades: {len(trades_this_run)}, "
          f"dry_run={config[\'dry_run\']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
''')

# ══════════════════════════════════════════════════════════════════════════════
# MODULE: btc_sprint_signal.py
# ══════════════════════════════════════════════════════════════════════════════
(BASE / "modules/__init__.py").write_text("")

(BASE / "modules/btc_sprint_signal.py").write_text('''\
"""BTC Sprint Signal — momentum + fallback signal generator."""
import random
import time


class BTCSprintSignal:
    def __init__(self, config: dict):
        self.config = config
        self._rng = random.Random(int(time.time()) % 1000)

    def generate(self, market: str) -> dict:
        """
        Returns a flat signal dict.
        All signal_data fields are TOP-LEVEL (flat), not nested.
        """
        edge       = round(self._rng.uniform(0.03, 0.08), 4)
        confidence = round(self._rng.uniform(0.58, 0.80), 4)
        side       = self._rng.choice(["YES", "NO"])
        signal_source = self.config.get("signal_source", "btc_momentum_v1")

        return {
            "market":        market,
            "side":          side,
            "edge":          edge,          # flat — NOT nested under signal_data
            "confidence":    confidence,    # flat
            "signal_source": signal_source, # flat
            "timestamp":     time.time(),
        }
''')

# ══════════════════════════════════════════════════════════════════════════════
# MODULE: btc_regime_filter.py
# ══════════════════════════════════════════════════════════════════════════════
(BASE / "modules/btc_regime_filter.py").write_text('''\
"""BTC Regime Filter — time, spread, edge, confidence, fee checks."""


class BTCRegimeFilter:
    def __init__(self, config: dict):
        self.min_edge         = float(config.get("min_edge", 0.03))
        self.confidence_floor = float(config.get("confidence_floor", 0.60))
        self.spread_limit     = float(config.get("spread_limit", 0.05))
        self.fee_rate         = float(config.get("fee_rate", 0.002))

    def passes(self, signal: dict, market: str) -> bool:
        """Return True if signal passes all regime filters."""
        edge       = signal.get("edge", 0)
        confidence = signal.get("confidence", 0)

        # Fee-aware edge check: net edge must exceed fee_rate
        net_edge = edge - self.fee_rate
        if net_edge < self.min_edge:
            return False
        if confidence < self.confidence_floor:
            return False
        # BTC-only guard
        if not market.startswith("btc_"):
            return False
        return True
''')

# ══════════════════════════════════════════════════════════════════════════════
# MODULE: btc_position_manager.py
# ══════════════════════════════════════════════════════════════════════════════
(BASE / "modules/btc_position_manager.py").write_text('''\
"""BTC Position Manager — bankroll and position sizing."""


class BTCPositionManager:
    def __init__(self, config: dict):
        self.bankroll_usd     = float(config.get("bankroll_usd", 1000.0))
        self.max_bankroll_pct = float(config.get("max_bankroll_pct", 0.02))
        self.max_position_usd = float(config.get("max_position_usd", 50.0))

    def size_position(self, signal: dict) -> float:
        """
        Kelly-inspired sizing capped by max_bankroll_pct and max_position_usd.
        Returns 0 if bankroll limit prevents any stake.
        """
        edge       = signal.get("edge", 0)
        confidence = signal.get("confidence", 0)
        raw_stake  = self.bankroll_usd * self.max_bankroll_pct * confidence * (1 + edge)
        capped     = min(raw_stake, self.max_position_usd)
        return round(max(0.0, capped), 2)
''')

# ══════════════════════════════════════════════════════════════════════════════
# MODULE: btc_sprint_executor.py
# ══════════════════════════════════════════════════════════════════════════════
(BASE / "modules/btc_sprint_executor.py").write_text('''\
"""BTC Sprint Executor — dry-run/live execution wrapper."""
import time


class BTCSprintExecutor:
    def __init__(self, config: dict):
        self.config = config

    def execute(self, decision: dict, dry_run: bool = True) -> dict:
        """
        Wrap a decision dict into an execution result.
        In dry-run mode, no real orders are placed.
        """
        result = dict(decision)
        result["dry_run"]   = dry_run
        result["executed"]  = True
        result["exec_time"] = time.time()
        result["status"]    = "dry_run_ok" if dry_run else "submitted"
        return result
''')

# ══════════════════════════════════════════════════════════════════════════════
# MODULE: btc_trade_journal.py
# ══════════════════════════════════════════════════════════════════════════════
(BASE / "modules/btc_trade_journal.py").write_text('''\
"""BTC Trade Journal — JSONL append-only journal."""
import json
from pathlib import Path


class BTCTradeJournal:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, record: dict) -> None:
        """Append one record as a JSON line."""
        with open(self.path, "a") as f:
            f.write(json.dumps(record) + "\\n")
''')

# ══════════════════════════════════════════════════════════════════════════════
# MODULE: btc_self_learn.py
# ══════════════════════════════════════════════════════════════════════════════
(BASE / "modules/btc_self_learn.py").write_text('''\
"""BTC Self-Learn — bounded parameter suggestions."""
import json
from pathlib import Path


# Allowed parameter bounds (conservative)
PARAM_BOUNDS = {
    "min_edge":         (0.02, 0.10),
    "confidence_floor": (0.55, 0.80),
    "max_bankroll_pct": (0.01, 0.05),
    "fee_rate":         (0.001, 0.005),
}


class BTCSelfLearn:
    def __init__(self, config: dict, rules_path):
        self.config     = config
        self.rules_path = Path(rules_path)

    def suggest(self, trades: list) -> None:
        """Analyse trades and append bounded suggestions to pending_rules."""
        if not trades:
            return
        # Load existing rules
        rules = {"pending": [], "applied": []}
        if self.rules_path.exists():
            with open(self.rules_path) as f:
                rules = json.load(f)
        # Simple heuristic: if avg edge is very high, suggest raising min_edge
        edges = [t.get("edge", 0) for t in trades]
        avg_edge = sum(edges) / len(edges) if edges else 0
        if avg_edge > 0.06:
            new_rule = {
                "rule_id": f"r{len(rules[\'pending\']) + len(rules[\'applied\']):03d}",
                "param":   "min_edge",
                "suggested": round(min(avg_edge * 0.8, PARAM_BOUNDS["min_edge"][1]), 4),
                "reason":  "high avg edge observed",
            }
            rules["pending"].append(new_rule)
            with open(self.rules_path, "w") as f:
                json.dump(rules, f, indent=2)
''')

# ══════════════════════════════════════════════════════════════════════════════
# MODULE: btc_heartbeat.py
# ══════════════════════════════════════════════════════════════════════════════
(BASE / "modules/btc_heartbeat.py").write_text('''\
"""BTC Heartbeat — run summary and briefing."""
import json
import time
from pathlib import Path


class BTCHeartbeat:
    def __init__(self, config: dict, summary_path):
        self.config       = config
        self.summary_path = Path(summary_path)
        self._skips       = []

    def record_skip(self, market: str, reason: str) -> None:
        self._skips.append({"market": market, "reason": reason})

    def finalize(self, trades: list) -> None:
        """Write a heartbeat summary JSON file."""
        summary = {
            "skill_slug":    self.config.get("skill_slug", "unknown"),
            "dry_run":       self.config.get("dry_run", True),
            "run_timestamp": time.time(),
            "trades_count":  len(trades),
            "skips_count":   len(self._skips),
            "skips":         self._skips,
            "target_markets": self.config.get("target_markets", []),
            "bankroll_usd":  self.config.get("bankroll_usd", 0),
            "signal_source": self.config.get("signal_source", "unknown"),
            "trades":        trades,
        }
        self.summary_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.summary_path, "w") as f:
            json.dump(summary, f, indent=2)
''')

# ══════════════════════════════════════════════════════════════════════════════
# MODULE: btc_llm_decider.py
# DELIBERATELY BROKEN: missing required flat fields in decision output,
# and the BTC-only validation is commented out.
# The agent must fix this so decisions include all required flat fields
# and only BTC markets pass through.
# ══════════════════════════════════════════════════════════════════════════════
(BASE / "modules/btc_llm_decider.py").write_text('''\
"""
BTC LLM Decider — strict JSON decision layer, provider abstraction,
and learning store helpers.

IMPORTANT: All decisions must:
  1. Be strict, valid JSON (no trailing commas, no comments).
  2. Only approve BTC markets (symbol must start with "btc_").
  3. Include all required flat fields:
       source, skill_slug, reasoning,
       edge, confidence, signal_source   ← flat (NOT nested under signal_data)
"""
import json
import time
from pathlib import Path


REQUIRED_FLAT_FIELDS = [
    "source",
    "skill_slug",
    "reasoning",
    "edge",          # flat signal_data field
    "confidence",    # flat signal_data field
    "signal_source", # flat signal_data field
]


class BTCLLMDecider:
    def __init__(self, config: dict, decisions_log_path):
        self.config    = config
        self.log_path  = Path(decisions_log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def decide(self, signal: dict, market: str, stake_usd: float) -> dict | None:
        """
        Produce a strict-JSON decision record.
        Returns None if the market is not BTC or validation fails.
        """
        # BTC-only validation
        if not market.startswith("btc_"):
            self._log({"market": market, "approved": False, "reason": "non-BTC market rejected"})
            return None

        # Build the decision with ALL required flat fields
        decision = {
            # Identity
            "source":        "btc-sprint-stack",
            "skill_slug":    self.config.get("skill_slug", "btc-sprint-stack"),
            "market":        market,
            "side":          signal.get("side", "YES"),
            "stake_usd":     stake_usd,
            # Required flat signal_data fields (flat, not nested)
            "edge":          signal.get("edge"),
            "confidence":    signal.get("confidence"),
            "signal_source": signal.get("signal_source"),
            # Reasoning
            "reasoning": (
                f"BTC momentum signal on {market}: "
                f"edge={signal.get(\'edge\'):.4f}, "
                f"confidence={signal.get(\'confidence\'):.4f}, "
                f"source={signal.get(\'signal_source\')}"
            ),
            "approved":      True,
            "timestamp":     time.time(),
        }

        # Strict JSON validation (round-trip)
        try:
            validated = json.loads(json.dumps(decision))
        except (TypeError, ValueError) as exc:
            self._log({"market": market, "approved": False, "reason": f"JSON validation failed: {exc}"})
            return None

        # Validate all required flat fields are present and non-null
        missing = [f for f in REQUIRED_FLAT_FIELDS if validated.get(f) is None]
        if missing:
            self._log({"market": market, "approved": False,
                       "reason": f"missing required fields: {missing}"})
            return None

        self._log(validated)
        return validated

    def _log(self, record: dict) -> None:
        """Append decision record as a JSON line."""
        with open(self.log_path, "a") as f:
            f.write(json.dumps(record) + "\\n")
''')

print("✅ BTC Sprint Stack sandbox workspace generated successfully.")
print(f"   Workspace root: {WORKSPACE}")
print(f"   Skill base:     {BASE}")
print(f"   Deliberate issues in workspace:")
print(f"     • config/defaults.json: wrong skill_slug, eth_5m intruder, max_bankroll_pct as string")
print(f"     • data/llm_decisions.jsonl: empty (agent must populate)")
print(f"     • data/heartbeat_summary.json: missing (agent must generate)")
print(f"     • Entrypoint not yet executable (no +x bit)")