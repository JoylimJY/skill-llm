import sys
import json
import math
from pathlib import Path

def run_eval(workspace: str):
    checks = []
    total_score = 0.0

    # ── helper ──────────────────────────────────────────────────────────────
    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── locate the output file ───────────────────────────────────────────────
    candidates = list(Path(workspace).rglob("audit_report.json"))
    if not candidates:
        checks.append({"name": "file_exists", "passed": False,
                        "detail": "audit_report.json not found anywhere in workspace"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    report_path = candidates[0]
    total_score += add_check("file_exists", True, f"Found at {report_path}")

    try:
        with open(report_path) as fh:
            report = json.load(fh)
    except Exception as e:
        checks.append({"name": "file_parseable", "passed": False,
                        "detail": f"JSON parse error: {e}"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    total_score += add_check("file_parseable", True, "Valid JSON")

    # ── check top-level structure ────────────────────────────────────────────
    has_users_key = isinstance(report.get("users"), (list, dict))
    total_score += add_check("has_users_section", has_users_key,
                              "Report must contain a 'users' key with per-user results")

    if not has_users_key:
        print(json.dumps({"passed": False, "score": total_score / 10.0,
                          "checks": checks}))
        return

    # Normalise: accept list-of-dicts or dict keyed by userId
    users_raw = report["users"]
    if isinstance(users_raw, list):
        users = {u["userId"]: u for u in users_raw if "userId" in u}
    else:
        users = users_raw

    # ────────────────────────────────────────────────────────────────────────
    # Expected behaviour (re-simulated deterministically)
    # Tier config from audit_input.json:
    #   starter: requests=5, window=30000
    #   growth:  requests=20, window=30000
    #   scale:   requests=3, window=30000
    #
    # For each user we replay N calls to checkLimit in quick succession
    # (all within the same window, so no timestamps expire).
    # ────────────────────────────────────────────────────────────────────────
    tier_config = {
        "starter": {"requests": 5, "window": 30000},
        "growth":  {"requests": 20, "window": 30000},
        "scale":   {"requests": 3, "window": 30000},
    }

    test_cases = [
        # (userId, tier, requestCount)
        ("u_alice", "starter", 4),
        ("u_bob",   "starter", 6),
        ("u_carol", "growth",  20),
        ("u_dave",  "scale",   3),
        ("u_eve",   "scale",   5),
        ("u_frank", "growth",  1),
        ("u_ghost", "phantom", 2),
    ]
    reset_users = {"u_bob", "u_eve"}

    def simulate_user(uid, tier, count):
        """Return expected summary for a user."""
        cfg = tier_config.get(tier)
        if cfg is None:
            # invalid tier – every call returns allowed=false, reason=invalid_tier
            results = [{"allowed": False, "reason": "invalid_tier"} for _ in range(count)]
            return {
                "userId": uid,
                "tier": tier,
                "results": results,
                "blocked_calls": count,
                "allowed_calls": 0,
                "final_remaining": None,   # N/A for invalid tier
                "stats_before_reset": None,
                "reset_applied": False,
            }

        limit = cfg["requests"]
        window_s = math.ceil(cfg["window"] / 1000)   # resetIn when allowed
        valid = []  # simulated in-memory request list

        results = []
        for _ in range(count):
            if len(valid) >= limit:
                # oldest is valid[0], assume all in same window so resetIn > 0
                # We don't know exact timestamps; just check allowed=False + reason
                results.append({
                    "allowed": False,
                    "reason": "rate_limit_exceeded",
                    "limit": limit,
                    "remaining": 0,
                })
            else:
                valid.append(1)   # placeholder timestamp
                results.append({
                    "allowed": True,
                    "limit": limit,
                    "remaining": limit - len(valid),
                    "resetIn": window_s,
                })

        allowed_calls = sum(1 for r in results if r.get("allowed"))
        blocked_calls = count - allowed_calls
        stats_total = len(valid)   # = min(count, limit)

        return {
            "userId": uid,
            "tier": tier,
            "allowed_calls": allowed_calls,
            "blocked_calls": blocked_calls,
            "stats_total_before_reset": stats_total,
            "final_remaining_after_last_allowed": (limit - stats_total) if allowed_calls > 0 else None,
            "window_s": window_s,
        }

    expected = {uid: simulate_user(uid, tier, cnt) for uid, tier, cnt in test_cases}

    # ── CHECK 1: Custom tiers used (not legacy defaults) ────────────────────
    # u_alice on "starter" tier (limit=5): 4 requests all allowed, remaining=1
    alice_data = users.get("u_alice", {})
    alice_ok = False
    alice_detail = "u_alice entry missing"
    if alice_data:
        ac = alice_data.get("allowed_calls", alice_data.get("allowed", None))
        rem = alice_data.get("final_remaining",
              alice_data.get("remaining", alice_data.get("remaining_after_last", None)))
        # allowed_calls should be 4, remaining after 4th call = 5-4=1
        ac_ok = (ac == 4)
        rem_ok = (rem == 1)
        alice_ok = ac_ok and rem_ok
        alice_detail = (f"allowed_calls={ac} (expect 4), "
                        f"final_remaining={rem} (expect 1)")
    total_score += add_check(
        "u_alice_starter_tier_correct",
        alice_ok, alice_detail, weight=1.5)

    # ── CHECK 2: u_bob exceeded starter limit (5); 5 allowed, 1 blocked ─────
    bob_data = users.get("u_bob", {})
    bob_ok = False
    bob_detail = "u_bob entry missing"
    if bob_data:
        ac = bob_data.get("allowed_calls", None)
        bc = bob_data.get("blocked_calls", None)
        bob_ok = (ac == 5 and bc == 1)
        bob_detail = f"allowed_calls={ac} (expect 5), blocked_calls={bc} (expect 1)"
    total_score += add_check("u_bob_limit_exceeded", bob_ok, bob_detail, weight=1.5)

    # ── CHECK 3: u_carol hit exactly the growth limit (20 allowed, 0 blocked) ─
    carol_data = users.get("u_carol", {})
    carol_ok = False
    carol_detail = "u_carol entry missing"
    if carol_data:
        ac = carol_data.get("allowed_calls", None)
        bc = carol_data.get("blocked_calls", None)
        rem = carol_data.get("final_remaining",
              carol_data.get("remaining", carol_data.get("remaining_after_last", None)))
        carol_ok = (ac == 20 and bc == 0 and rem == 0)
        carol_detail = (f"allowed_calls={ac} (expect 20), "
                        f"blocked_calls={bc} (expect 0), "
                        f"final_remaining={rem} (expect 0)")
    total_score += add_check("u_carol_growth_exact_limit", carol_ok, carol_detail, weight=1.0)

    # ── CHECK 4: u_eve scale tier (limit=3); 3 allowed, 2 blocked ────────────
    eve_data = users.get("u_eve", {})
    eve_ok = False
    eve_detail = "u_eve entry missing"
    if eve_data:
        ac = eve_data.get("allowed_calls", None)
        bc = eve_data.get("blocked_calls", None)
        eve_ok = (ac == 3 and bc == 2)
        eve_detail = f"allowed_calls={ac} (expect 3), blocked_calls={bc} (expect 2)"
    total_score += add_check("u_eve_scale_exceeded", eve_ok, eve_detail, weight=1.0)

    # ── CHECK 5: u_ghost invalid tier → all blocked, reason=invalid_tier ─────
    ghost_data = users.get("u_ghost", {})
    ghost_ok = False
    ghost_detail = "u_ghost entry missing"
    if ghost_data:
        bc = ghost_data.get("blocked_calls", None)
        reason = ghost_data.get("reason",
                 ghost_data.get("block_reason",
                 ghost_data.get("error", "")))
        ac = ghost_data.get("allowed_calls", None)
        # All 2 requests must be blocked; reason must reference invalid_tier
        reason_ok = "invalid_tier" in str(reason)
        count_ok = (bc == 2 or ac == 0)
        ghost_ok = reason_ok and count_ok
        ghost_detail = (f"blocked_calls={bc}, allowed_calls={ac}, "
                        f"reason='{reason}' (expect 'invalid_tier' mentioned)")
    total_score += add_check("u_ghost_invalid_tier", ghost_ok, ghost_detail, weight=1.0)

    # ── CHECK 6: resetIn when allowed = ceil(window/1000) = ceil(30000/1000) = 30 ──
    # Verify at least one user's resetIn (when allowed) equals 30
    reset_in_ok = False
    reset_in_detail = "Could not verify resetIn=30 for any allowed call"
    for uid_check in ["u_alice", "u_frank", "u_dave"]:
        ud = users.get(uid_check, {})
        ri = ud.get("reset_in",
             ud.get("resetIn",
             ud.get("reset_in_seconds", None)))
        if ri is not None:
            try:
                if int(ri) == 30:
                    reset_in_ok = True
                    reset_in_detail = f"resetIn=30 confirmed for {uid_check}"
                    break
            except (TypeError, ValueError):
                pass
    total_score += add_check("reset_in_full_window_value", reset_in_ok,
                              reset_in_detail, weight=1.0)

    # ── CHECK 7: getStats called — stats_total_before_reset reported correctly ─
    # u_bob: 5 requests stored before reset (min(6,5)=5)
    bob_stats_ok = False
    bob_stats_detail = "stats_before_reset for u_bob missing or wrong"
    if bob_data:
        st = bob_data.get("stats_total_before_reset",
             bob_data.get("stats_before_reset",
             bob_data.get("stats", {}).get("totalRequests", None) if isinstance(bob_data.get("stats"), dict) else None))
        if st is not None:
            try:
                bob_stats_ok = (int(st) == 5)
                bob_stats_detail = f"stats_total_before_reset={st} (expect 5)"
            except (TypeError, ValueError):
                bob_stats_detail = f"stats value non-numeric: {st}"
    total_score += add_check("u_bob_stats_before_reset", bob_stats_ok,
                              bob_stats_detail, weight=1.0)

    # ── CHECK 8: reset applied to u_bob and u_eve ────────────────────────────
    reset_ok = False
    reset_detail = "reset_applied field missing for u_bob and u_eve"
    bob_reset = bob_data.get("reset_applied", bob_data.get("was_reset", None))
    eve_reset = eve_data.get("reset_applied", eve_data.get("was_reset", None))
    if bob_reset is not None and eve_reset is not None:
        reset_ok = bool(bob_reset) and bool(eve_reset)
        reset_detail = f"u_bob reset_applied={bob_reset}, u_eve reset_applied={eve_reset}"
    total_score += add_check("reset_applied_to_flagged_users", reset_ok,
                              reset_detail, weight=1.0)

    # ── CHECK 9: non-reset users NOT marked as reset ──────────────────────────
    alice_no_reset = not bool(alice_data.get("reset_applied",
                               alice_data.get("was_reset", False)))
    carol_no_reset = not bool(carol_data.get("reset_applied",
                               carol_data.get("was_reset", False)))
    no_reset_ok = alice_no_reset and carol_no_reset
    total_score += add_check(
        "non_flagged_users_not_reset", no_reset_ok,
        f"alice reset_applied={not alice_no_reset}, carol reset_applied={not carol_no_reset}",
        weight=0.5)

    # ── final scoring ────────────────────────────────────────────────────────
    max_score = 2 + 1.5 + 1.5 + 1.0 + 1.0 + 1.0 + 1.0 + 1.0 + 1.0 + 0.5
    # = 2 (file) + 1.5 (alice) + 1.5 (bob exceeded) + 1.0 (carol) +
    #   1.0 (eve) + 1.0 (ghost) + 1.0 (resetIn) + 1.0 (stats) +
    #   1.0 (reset applied) + 0.5 (no spurious resets)
    # Actually let me recount: file_exists=1, parseable=1, has_users=1,
    # alice=1.5, bob_limit=1.5, carol=1.0, eve=1.0, ghost=1.0,
    # resetIn=1.0, stats=1.0, reset_applied=1.0, no_reset=0.5 → max=12.5
    max_score = 12.5
    normalised = round(min(total_score / max_score, 1.0), 4)
    passed = normalised >= 0.75 and all(
        c["passed"] for c in checks
        if c["name"] in ("file_exists", "file_parseable",
                         "u_bob_limit_exceeded", "u_ghost_invalid_tier",
                         "reset_in_full_window_value")
    )

    print(json.dumps({
        "passed": passed,
        "score": normalised,
        "checks": checks
    }, indent=2))


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace)