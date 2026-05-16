import json
import sys
import os
from pathlib import Path

def main(workspace):
    checks = []
    total_score = 0.0

    alerts_file = Path.home() / ".openclaw" / "agents" / "tradebot" / "private" / "market-alerts.json"

    # ── CHECK 1: Alerts file exists ──────────────────────────────────────────
    try:
        assert alerts_file.exists(), f"File not found: {alerts_file}"
        raw = alerts_file.read_text()
        alerts = json.loads(raw)
        assert isinstance(alerts, list), "Alerts must be a JSON array"
        checks.append({"name": "alerts_file_exists_and_valid_json", "passed": True, "detail": f"Found {len(alerts)} alert(s)"})
        total_score += 1.0
    except Exception as e:
        checks.append({"name": "alerts_file_exists_and_valid_json", "passed": False, "detail": str(e)})
        # Can't continue without the file
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # ── CHECK 2: Price alert for HYPE exists with correct fields ─────────────
    price_alerts = [a for a in alerts if a.get("type") == "price"]
    hype_alerts = [a for a in price_alerts if a.get("asset", "").upper() == "HYPE"]

    try:
        assert len(hype_alerts) >= 1, f"No price alert for HYPE found. Price alerts: {price_alerts}"
        pa = hype_alerts[0]
        checks.append({"name": "price_alert_hype_exists", "passed": True, "detail": f"Found HYPE price alert id={pa.get('id')}"})
        total_score += 1.0
    except Exception as e:
        checks.append({"name": "price_alert_hype_exists", "passed": False, "detail": str(e)})
        pa = None

    if pa:
        # CHECK 2a: condition is <=
        try:
            assert pa.get("condition") == "<=", f"Expected condition '<=' got '{pa.get('condition')}'"
            checks.append({"name": "price_alert_condition_lte", "passed": True, "detail": f"condition={pa.get('condition')}"})
            total_score += 1.0
        except Exception as e:
            checks.append({"name": "price_alert_condition_lte", "passed": False, "detail": str(e)})

        # CHECK 2b: target_price is 28.5
        try:
            tp = pa.get("target_price")
            assert tp is not None and abs(float(tp) - 28.5) < 0.001, f"Expected target_price=28.5, got {tp}"
            checks.append({"name": "price_alert_target_28_5", "passed": True, "detail": f"target_price={tp}"})
            total_score += 1.0
        except Exception as e:
            checks.append({"name": "price_alert_target_28_5", "passed": False, "detail": str(e)})

        # CHECK 2c: market is crypto
        try:
            assert pa.get("market") == "crypto", f"Expected market='crypto', got '{pa.get('market')}'"
            checks.append({"name": "price_alert_market_crypto", "passed": True, "detail": f"market={pa.get('market')}"})
            total_score += 0.5
        except Exception as e:
            checks.append({"name": "price_alert_market_crypto", "passed": False, "detail": str(e)})

        # CHECK 2d: agent_id is tradebot
        try:
            assert pa.get("agent_id") == "tradebot", f"Expected agent_id='tradebot', got '{pa.get('agent_id')}'"
            checks.append({"name": "price_alert_agent_tradebot", "passed": True, "detail": f"agent_id={pa.get('agent_id')}"})
            total_score += 0.5
        except Exception as e:
            checks.append({"name": "price_alert_agent_tradebot", "passed": False, "detail": str(e)})

        # CHECK 2e: reply_channel is feishu
        try:
            assert pa.get("reply_channel") == "feishu", f"Expected reply_channel='feishu', got '{pa.get('reply_channel')}'"
            checks.append({"name": "price_alert_reply_channel_feishu", "passed": True, "detail": f"reply_channel={pa.get('reply_channel')}"})
            total_score += 0.5
        except Exception as e:
            checks.append({"name": "price_alert_reply_channel_feishu", "passed": False, "detail": str(e)})

        # CHECK 2f: session_key is set (non-empty)
        try:
            sk = pa.get("session_key", "")
            assert sk and len(sk) > 5, f"session_key is empty or too short: '{sk}'"
            checks.append({"name": "price_alert_session_key_set", "passed": True, "detail": f"session_key={sk}"})
            total_score += 0.5
        except Exception as e:
            checks.append({"name": "price_alert_session_key_set", "passed": False, "detail": str(e)})

        # CHECK 2g: transcript_msg_id is set (non-empty) — SKILL.md says "推荐填入"
        try:
            tmid = pa.get("transcript_msg_id", "")
            assert tmid and len(tmid) > 2, f"transcript_msg_id is empty: '{tmid}'. SKILL.md says this is recommended (推荐填入)"
            checks.append({"name": "price_alert_transcript_msg_id_set", "passed": True, "detail": f"transcript_msg_id={tmid}"})
            total_score += 1.0
        except Exception as e:
            checks.append({"name": "price_alert_transcript_msg_id_set", "passed": False, "detail": str(e)})

        # CHECK 2h: status is active
        try:
            assert pa.get("status") == "active", f"Expected status='active', got '{pa.get('status')}'"
            checks.append({"name": "price_alert_status_active", "passed": True, "detail": f"status={pa.get('status')}"})
            total_score += 0.5
        except Exception as e:
            checks.append({"name": "price_alert_status_active", "passed": False, "detail": str(e)})

        # CHECK 2i: one_shot is True (price alerts default to one-shot per SKILL.md)
        try:
            assert pa.get("one_shot") == True, f"Expected one_shot=True for price alert, got '{pa.get('one_shot')}'"
            checks.append({"name": "price_alert_one_shot_true", "passed": True, "detail": "one_shot=True (default for price alerts)"})
            total_score += 0.5
        except Exception as e:
            checks.append({"name": "price_alert_one_shot_true", "passed": False, "detail": str(e)})

    # ── CHECK 3: News alert exists with correct fields ────────────────────────
    news_alerts = [a for a in alerts if a.get("type") == "news"]

    try:
        assert len(news_alerts) >= 1, f"No news alert found. All alerts: {[a.get('type') for a in alerts]}"
        na = news_alerts[0]
        checks.append({"name": "news_alert_exists", "passed": True, "detail": f"Found news alert id={na.get('id')}"})
        total_score += 1.0
    except Exception as e:
        checks.append({"name": "news_alert_exists", "passed": False, "detail": str(e)})
        na = None

    if na:
        # CHECK 3a: keywords contain HYPE, Hyperliquid, HyperEVM
        try:
            kws = [k.upper() for k in na.get("keywords", [])]
            required = {"HYPE", "HYPERLIQUID", "HYPEREVM"}
            found = {k for k in required if k in kws}
            assert found == required, f"Missing keywords: {required - found}. Got: {na.get('keywords')}"
            checks.append({"name": "news_alert_keywords_correct", "passed": True, "detail": f"keywords={na.get('keywords')}"})
            total_score += 1.5
        except Exception as e:
            checks.append({"name": "news_alert_keywords_correct", "passed": False, "detail": str(e)})

        # CHECK 3b: keyword_mode is "all" (critical proprietary trap)
        try:
            assert na.get("keyword_mode") == "all", f"Expected keyword_mode='all' (all must appear in same article), got '{na.get('keyword_mode')}'"
            checks.append({"name": "news_alert_keyword_mode_all", "passed": True, "detail": f"keyword_mode={na.get('keyword_mode')}"})
            total_score += 1.5
        except Exception as e:
            checks.append({"name": "news_alert_keyword_mode_all", "passed": False, "detail": str(e)})

        # CHECK 3c: sources are exactly coindesk, cointelegraph, theblock (only — no jin10/wallstreetcn/decrypt)
        try:
            sources = set(na.get("sources", []))
            expected_sources = {"coindesk", "cointelegraph", "theblock"}
            # Must contain all three required sources
            missing = expected_sources - sources
            assert not missing, f"Missing required sources: {missing}. Got: {sources}"
            # Must NOT contain jin10, wallstreetcn (these are Chinese informal sources, not appropriate for Hyperliquid monitoring)
            forbidden = {"jin10", "wallstreetcn"} & sources
            assert not forbidden, f"Should not include informal sources {forbidden} for this monitoring task. Got: {sources}"
            checks.append({"name": "news_alert_sources_correct", "passed": True, "detail": f"sources={sorted(sources)}"})
            total_score += 1.5
        except Exception as e:
            checks.append({"name": "news_alert_sources_correct", "passed": False, "detail": str(e)})

        # CHECK 3d: one_shot is True (agent set --one-shot flag as per task requirements)
        try:
            assert na.get("one_shot") == True, f"Expected one_shot=True for this news alert (waiting for specific event), got '{na.get('one_shot')}'. SKILL.md: news alerts default to continuous, --one-shot must be explicit."
            checks.append({"name": "news_alert_one_shot_true", "passed": True, "detail": "one_shot=True (explicitly set, not default)"})
            total_score += 1.5
        except Exception as e:
            checks.append({"name": "news_alert_one_shot_true", "passed": False, "detail": str(e)})

        # CHECK 3e: agent_id is tradebot
        try:
            assert na.get("agent_id") == "tradebot", f"Expected agent_id='tradebot', got '{na.get('agent_id')}'"
            checks.append({"name": "news_alert_agent_tradebot", "passed": True, "detail": f"agent_id={na.get('agent_id')}"})
            total_score += 0.5
        except Exception as e:
            checks.append({"name": "news_alert_agent_tradebot", "passed": False, "detail": str(e)})

        # CHECK 3f: status is active
        try:
            assert na.get("status") == "active", f"Expected status='active', got '{na.get('status')}'"
            checks.append({"name": "news_alert_status_active", "passed": True, "detail": f"status={na.get('status')}"})
            total_score += 0.5
        except Exception as e:
            checks.append({"name": "news_alert_status_active", "passed": False, "detail": str(e)})

    # ── CHECK 4: Daemon was started (PID files exist) ─────────────────────────
    price_pid = Path(f"/tmp/market-watch-tradebot-price.pid")
    news_pid = Path(f"/tmp/market-watch-tradebot-news.pid")

    try:
        assert price_pid.exists(), f"Price daemon PID file not found: {price_pid}. Did you run daemon.sh start?"
        checks.append({"name": "daemon_price_pid_exists", "passed": True, "detail": f"PID file: {price_pid}"})
        total_score += 1.0
    except Exception as e:
        checks.append({"name": "daemon_price_pid_exists", "passed": False, "detail": str(e)})

    try:
        assert news_pid.exists(), f"News daemon PID file not found: {news_pid}. Did you run daemon.sh start?"
        checks.append({"name": "daemon_news_pid_exists", "passed": True, "detail": f"PID file: {news_pid}"})
        total_score += 1.0
    except Exception as e:
        checks.append({"name": "daemon_news_pid_exists", "passed": False, "detail": str(e)})

    # ── Final scoring ─────────────────────────────────────────────────────────
    max_score = 16.5
    normalized = round(min(total_score / max_score, 1.0), 4)
    passed = normalized >= 0.75 and all(
        c["passed"] for c in checks
        if c["name"] in [
            "alerts_file_exists_and_valid_json",
            "price_alert_hype_exists",
            "price_alert_condition_lte",
            "price_alert_target_28_5",
            "price_alert_transcript_msg_id_set",
            "news_alert_exists",
            "news_alert_keyword_mode_all",
            "news_alert_one_shot_true",
            "daemon_price_pid_exists",
            "daemon_news_pid_exists",
        ]
    )

    print(json.dumps({
        "passed": passed,
        "score": normalized,
        "checks": checks
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    main(workspace)