import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str) -> dict:
    ws = Path(workspace)
    checks = []
    total_score = 0.0

    # ── Helper ────────────────────────────────────────────────────────────────
    def add_check(name: str, passed: bool, detail: str, weight: float = 1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── Check 1: trades.json exists in correct location ───────────────────────
    trades_file = ws / "skills" / "crypto-self-learning" / "data" / "trades.json"
    try:
        if not trades_file.exists():
            total_score += add_check(
                "trades.json_exists",
                False,
                f"trades.json not found at expected path: {trades_file}"
            )
            trades = []
        else:
            with open(trades_file) as f:
                trades_data = json.load(f)
            trades = trades_data.get("trades", [])
            total_score += add_check(
                "trades.json_exists",
                True,
                f"Found trades.json with {len(trades)} trades"
            )
    except Exception as e:
        trades = []
        total_score += add_check("trades.json_exists", False, f"Error reading trades.json: {e}")

    # ── Check 2: At least 8 trades logged ─────────────────────────────────────
    try:
        n_trades = len(trades)
        passed = n_trades >= 8
        total_score += add_check(
            "sufficient_trades_logged",
            passed,
            f"Found {n_trades} trades (need >= 8)"
        )
    except Exception as e:
        total_score += add_check("sufficient_trades_logged", False, f"Error: {e}")

    # ── Check 3: All trades have required fields with correct types ────────────
    try:
        required_fields = ["symbol", "direction", "entry", "exit", "pnl_percent", "result"]
        valid_count = 0
        invalid_details = []
        for i, t in enumerate(trades):
            missing = [f for f in required_fields if f not in t]
            invalid_direction = t.get("direction") not in ("LONG", "SHORT") if "direction" in t else True
            invalid_result = t.get("result") not in ("WIN", "LOSS") if "result" in t else True
            if not missing and not invalid_direction and not invalid_result:
                valid_count += 1
            else:
                msg = f"Trade {i}: missing={missing}, bad_dir={invalid_direction}, bad_result={invalid_result}"
                invalid_details.append(msg)

        passed = valid_count == len(trades) and len(trades) >= 8
        detail = f"{valid_count}/{len(trades)} trades have valid required fields"
        if invalid_details:
            detail += f"; Issues: {invalid_details[:3]}"
        total_score += add_check("all_required_fields_valid", passed, detail)
    except Exception as e:
        total_score += add_check("all_required_fields_valid", False, f"Error: {e}")

    # ── Check 4: Trades include both WIN and LOSS results ──────────────────────
    try:
        results = set(t.get("result") for t in trades)
        has_win = "WIN" in results
        has_loss = "LOSS" in results
        passed = has_win and has_loss
        total_score += add_check(
            "both_win_and_loss_present",
            passed,
            f"Results found: {results} (need both WIN and LOSS)"
        )
    except Exception as e:
        total_score += add_check("both_win_and_loss_present", False, f"Error: {e}")

    # ── Check 5: Trades include both LONG and SHORT directions ─────────────────
    try:
        directions = set(t.get("direction") for t in trades)
        has_long = "LONG" in directions
        has_short = "SHORT" in directions
        passed = has_long and has_short
        total_score += add_check(
            "both_directions_present",
            passed,
            f"Directions found: {directions} (need both LONG and SHORT)"
        )
    except Exception as e:
        total_score += add_check("both_directions_present", False, f"Error: {e}")

    # ── Check 6: Trades include multiple symbols ───────────────────────────────
    try:
        symbols = set(t.get("symbol") for t in trades if t.get("symbol"))
        passed = len(symbols) >= 2
        total_score += add_check(
            "multiple_symbols_present",
            passed,
            f"Symbols found: {symbols} (need >= 2)"
        )
    except Exception as e:
        total_score += add_check("multiple_symbols_present", False, f"Error: {e}")

    # ── Check 7: Trades have non-empty indicators dict ─────────────────────────
    try:
        trades_with_indicators = [
            t for t in trades
            if isinstance(t.get("indicators"), dict) and len(t.get("indicators", {})) > 0
        ]
        passed = len(trades_with_indicators) >= max(1, len(trades) // 2)
        total_score += add_check(
            "indicators_populated",
            passed,
            f"{len(trades_with_indicators)}/{len(trades)} trades have non-empty indicators dict"
        )
    except Exception as e:
        total_score += add_check("indicators_populated", False, f"Error: {e}")

    # ── Check 8: Trades have non-empty market_context dict ────────────────────
    try:
        trades_with_ctx = [
            t for t in trades
            if isinstance(t.get("market_context"), dict) and len(t.get("market_context", {})) > 0
        ]
        passed = len(trades_with_ctx) >= max(1, len(trades) // 2)
        total_score += add_check(
            "market_context_populated",
            passed,
            f"{len(trades_with_ctx)}/{len(trades)} trades have non-empty market_context dict"
        )
    except Exception as e:
        total_score += add_check("market_context_populated", False, f"Error: {e}")

    # ── Check 9: generated_rules.json exists ──────────────────────────────────
    rules_file = ws / "skills" / "crypto-self-learning" / "data" / "generated_rules.json"
    try:
        if not rules_file.exists():
            total_score += add_check(
                "generated_rules_exists",
                False,
                f"generated_rules.json not found at {rules_file}"
            )
            rules_data = None
        else:
            with open(rules_file) as f:
                rules_data = json.load(f)
            n_rules = len(rules_data.get("rules", []))
            total_score += add_check(
                "generated_rules_exists",
                True,
                f"generated_rules.json found with {n_rules} rules"
            )
    except Exception as e:
        rules_data = None
        total_score += add_check("generated_rules_exists", False, f"Error reading rules: {e}")

    # ── Check 10: generated_rules.json has actual rules ───────────────────────
    try:
        if rules_data is None:
            total_score += add_check("rules_have_content", False, "No rules data available")
        else:
            rules = rules_data.get("rules", [])
            n_analyzed = rules_data.get("total_trades_analyzed", 0)
            has_rules = len(rules) > 0
            has_meta = n_analyzed >= 8
            passed = has_rules and has_meta
            total_score += add_check(
                "rules_have_content",
                passed,
                f"Rules count: {len(rules)}, trades_analyzed: {n_analyzed}"
            )
    except Exception as e:
        total_score += add_check("rules_have_content", False, f"Error: {e}")

    # ── Check 11: MEMORY.md has Learned Rules section ────────────────────────
    memory_file = ws / "team" / "strategy" / "MEMORY.md"
    try:
        if not memory_file.exists():
            total_score += add_check(
                "memory_has_learned_rules_section",
                False,
                f"MEMORY.md not found at {memory_file}"
            )
            memory_content = ""
        else:
            memory_content = memory_file.read_text()
            has_section = "## 🧠 Learned Rules" in memory_content
            total_score += add_check(
                "memory_has_learned_rules_section",
                has_section,
                f"'## 🧠 Learned Rules' section {'found' if has_section else 'NOT FOUND'} in MEMORY.md"
            )
    except Exception as e:
        memory_content = ""
        total_score += add_check("memory_has_learned_rules_section", False, f"Error: {e}")

    # ── Check 12: MEMORY.md original content preserved ────────────────────────
    try:
        original_markers = [
            "# 🧠 Trading Strategy Memory",
            "## Core Philosophy",
            "## Risk Management"
        ]
        preserved = all(marker in memory_content for marker in original_markers)
        total_score += add_check(
            "memory_original_content_preserved",
            preserved,
            f"Original sections preserved: {preserved}"
        )
    except Exception as e:
        total_score += add_check("memory_original_content_preserved", False, f"Error: {e}")

    # ── Check 13: MEMORY.md Learned Rules has actual rule lines ───────────────
    try:
        rule_patterns = [r"🚫\s*AVOID", r"✅\s*PREFER", r"⚠️\s*CAUTION"]
        found_patterns = [p for p in rule_patterns if re.search(p, memory_content)]
        passed = len(found_patterns) >= 1
        total_score += add_check(
            "memory_learned_rules_have_content",
            passed,
            f"Rule patterns found in MEMORY.md: {found_patterns} (need at least 1 of AVOID/PREFER/CAUTION)"
        )
    except Exception as e:
        total_score += add_check("memory_learned_rules_have_content", False, f"Error: {e}")

    # ── Compute final score ───────────────────────────────────────────────────
    n_checks = len(checks)
    n_passed = sum(1 for c in checks if c["passed"])
    final_score = total_score / n_checks if n_checks > 0 else 0.0
    all_passed = n_passed == n_checks

    return {
        "passed": all_passed,
        "score": round(final_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))