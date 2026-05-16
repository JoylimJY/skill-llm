#!/usr/bin/env python3
"""
Evaluation script for BTC Sprint Stack sandbox task.
Checks:
  1. Entrypoint ran successfully (heartbeat_summary.json exists)
  2. heartbeat_summary.json is valid JSON with correct skill_slug and dry_run=True
  3. heartbeat_summary.json targets only BTC markets (no eth_*)
  4. data/llm_decisions.jsonl has at least one approved decision line
  5. Each approved decision contains all required FLAT fields
  6. skill_slug in decisions == "btc-sprint-stack"
  7. All approved decisions target only btc_ markets
  8. live_params.json values are reflected (signal_source == "btc_momentum_v2")
  9. btc_trade_journal.jsonl exists and has at least one entry
 10. config/defaults.json was corrected (skill_slug + max_bankroll_pct type)
     OR live_params override was applied correctly (heartbeat reflects live values)
"""

import sys
import json
from pathlib import Path

REQUIRED_FLAT_FIELDS = ["source", "skill_slug", "reasoning", "edge", "confidence", "signal_source"]

def load_jsonl(path: Path):
    records = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def run_eval(workspace: str):
    ws = Path(workspace)
    skill_base = ws / "skills" / "btc-sprint-stack"
    checks = []

    # ── Check 1: heartbeat_summary.json exists ─────────────────────────────
    heartbeat_path = skill_base / "data" / "heartbeat_summary.json"
    hb_exists = heartbeat_path.exists()
    checks.append({
        "name": "heartbeat_summary.json exists",
        "passed": hb_exists,
        "detail": str(heartbeat_path) if hb_exists else f"File not found: {heartbeat_path}"
    })

    # ── Check 2: heartbeat is valid JSON ──────────────────────────────────
    heartbeat = {}
    hb_valid = False
    if hb_exists:
        try:
            heartbeat = json.loads(heartbeat_path.read_text())
            hb_valid = True
        except Exception as e:
            pass
    checks.append({
        "name": "heartbeat_summary.json is valid JSON",
        "passed": hb_valid,
        "detail": "Parsed OK" if hb_valid else "JSON parse error"
    })

    # ── Check 3: heartbeat skill_slug == "btc-sprint-stack" ───────────────
    hb_slug_ok = heartbeat.get("skill_slug") == "btc-sprint-stack"
    checks.append({
        "name": "heartbeat skill_slug == 'btc-sprint-stack'",
        "passed": hb_slug_ok,
        "detail": f"skill_slug={heartbeat.get('skill_slug')!r}"
    })

    # ── Check 4: heartbeat dry_run == True ────────────────────────────────
    hb_dry_run_ok = heartbeat.get("dry_run") is True
    checks.append({
        "name": "heartbeat dry_run == True",
        "passed": hb_dry_run_ok,
        "detail": f"dry_run={heartbeat.get('dry_run')!r}"
    })

    # ── Check 5: heartbeat target_markets are BTC-only ────────────────────
    hb_markets = heartbeat.get("target_markets", [])
    hb_btc_only = all(m.startswith("btc_") for m in hb_markets) and len(hb_markets) >= 1
    checks.append({
        "name": "heartbeat target_markets are BTC-only (no eth_*)",
        "passed": hb_btc_only,
        "detail": f"target_markets={hb_markets}"
    })

    # ── Check 6: llm_decisions.jsonl exists and non-empty ─────────────────
    decisions_path = skill_base / "data" / "llm_decisions.jsonl"
    decisions_exists = decisions_path.exists()
    decisions_records = []
    decisions_nonempty = False
    if decisions_exists:
        try:
            decisions_records = load_jsonl(decisions_path)
            decisions_nonempty = len(decisions_records) > 0
        except Exception as e:
            pass
    checks.append({
        "name": "data/llm_decisions.jsonl exists and non-empty",
        "passed": decisions_exists and decisions_nonempty,
        "detail": f"found {len(decisions_records)} record(s)" if decisions_exists else "File not found"
    })

    # ── Check 7: at least one approved decision ───────────────────────────
    approved = [r for r in decisions_records if r.get("approved") is True]
    has_approved = len(approved) > 0
    checks.append({
        "name": "At least one approved decision in llm_decisions.jsonl",
        "passed": has_approved,
        "detail": f"{len(approved)} approved decision(s) found"
    })

    # ── Check 8: approved decisions have all required FLAT fields ─────────
    flat_fields_ok = True
    flat_fields_detail = []
    for i, rec in enumerate(approved):
        missing = [f for f in REQUIRED_FLAT_FIELDS if rec.get(f) is None]
        if missing:
            flat_fields_ok = False
            flat_fields_detail.append(f"record[{i}] missing: {missing}")
    checks.append({
        "name": "All approved decisions have required flat fields (edge, confidence, signal_source, source, skill_slug, reasoning)",
        "passed": flat_fields_ok,
        "detail": "; ".join(flat_fields_detail) if flat_fields_detail else "All flat fields present in all approved records"
    })

    # ── Check 9: approved decisions skill_slug == "btc-sprint-stack" ──────
    slug_ok_all = all(r.get("skill_slug") == "btc-sprint-stack" for r in approved) if approved else False
    checks.append({
        "name": "All approved decisions have skill_slug == 'btc-sprint-stack'",
        "passed": slug_ok_all,
        "detail": f"Checked {len(approved)} approved record(s)"
    })

    # ── Check 10: approved decisions target only btc_ markets ─────────────
    btc_only_decisions = all(
        str(r.get("market", "")).startswith("btc_") for r in approved
    ) if approved else False
    checks.append({
        "name": "All approved decisions target only btc_ markets",
        "passed": btc_only_decisions,
        "detail": str([r.get("market") for r in approved])
    })

    # ── Check 11: live_params signal_source reflected in decisions ─────────
    # live_params.json overrides signal_source to "btc_momentum_v2"
    signal_source_ok = all(
        r.get("signal_source") == "btc_momentum_v2" for r in approved
    ) if approved else False
    checks.append({
        "name": "live_params.json signal_source ('btc_momentum_v2') reflected in approved decisions",
        "passed": signal_source_ok,
        "detail": str([r.get("signal_source") for r in approved])
    })

    # ── Check 12: btc_trade_journal.jsonl exists and non-empty ────────────
    journal_path = skill_base / "data" / "btc_trade_journal.jsonl"
    journal_exists = journal_path.exists()
    journal_records = []
    journal_nonempty = False
    if journal_exists:
        try:
            journal_records = load_jsonl(journal_path)
            journal_nonempty = len(journal_records) > 0
        except Exception as e:
            pass
    checks.append({
        "name": "data/btc_trade_journal.jsonl exists and non-empty",
        "passed": journal_exists and journal_nonempty,
        "detail": f"found {len(journal_records)} journal entry/ies" if journal_exists else "File not found"
    })

    # ── Check 13: journal entries have dry_run == True ────────────────────
    journal_dry_run = all(r.get("dry_run") is True for r in journal_records) if journal_records else False
    checks.append({
        "name": "All journal entries have dry_run == True",
        "passed": journal_dry_run,
        "detail": f"Checked {len(journal_records)} journal record(s)"
    })

    # ── Check 14: heartbeat signal_source == "btc_momentum_v2" ───────────
    hb_signal_source = heartbeat.get("signal_source") == "btc_momentum_v2"
    checks.append({
        "name": "heartbeat signal_source == 'btc_momentum_v2' (live_params override applied)",
        "passed": hb_signal_source,
        "detail": f"signal_source={heartbeat.get('signal_source')!r}"
    })

    # ── Check 15: no non-BTC markets in journal ───────────────────────────
    journal_btc_only = all(
        str(r.get("market", "")).startswith("btc_") for r in journal_records
    ) if journal_records else True  # vacuously true if empty (covered by check 12)
    checks.append({
        "name": "No non-BTC market entries in trade journal",
        "passed": journal_btc_only,
        "detail": str([r.get("market") for r in journal_records])
    })

    # ── Scoring ───────────────────────────────────────────────────────────
    total   = len(checks)
    passed  = sum(1 for c in checks if c["passed"])
    score   = round(passed / total, 4)
    overall = passed == total

    result = {
        "passed": overall,
        "score":  score,
        "checks": checks,
    }
    print(json.dumps(result, indent=2))
    return 0 if overall else 1


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    sys.exit(run_eval(workspace))