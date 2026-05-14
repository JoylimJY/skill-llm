import sys
import json
import os
from pathlib import Path

def load_report(workspace):
    """Find cache_report.json anywhere in the workspace."""
    candidates = list(Path(workspace).rglob("cache_report.json"))
    if not candidates:
        return None, "cache_report.json not found anywhere in workspace"
    # prefer root-level
    candidates.sort(key=lambda p: len(p.parts))
    path = candidates[0]
    try:
        with open(path) as f:
            data = json.load(f)
        return data, str(path)
    except Exception as e:
        return None, f"Failed to parse {path}: {e}"

def run_eval(workspace):
    checks = []

    report, msg = load_report(workspace)

    # ── Check 0: File exists and is valid JSON ────────────────────────────────
    file_exists = report is not None
    checks.append({
        "name": "cache_report.json exists and is valid JSON",
        "passed": file_exists,
        "detail": msg if not file_exists else f"Found at {msg}"
    })
    if not file_exists:
        return checks

    # ══════════════════════════════════════════════════════════════════════════
    # SCENARIO 1 – LFU eviction
    # Setup: maxSize=3, strategy='lfu'
    # set A (count=0), set B (count=0), set C (count=0)
    # get(A) x2 → A.count=2
    # get(B) x1 → B.count=1
    # C never get() → C.count=0
    # set(D) triggers evict() → LFU evicts C (count=0, first in Map insertion order)
    # Expected evicted key: "C"
    # ══════════════════════════════════════════════════════════════════════════
    try:
        scenario1 = None
        raw = report.get("lfu_eviction") or report.get("scenarios", {}).get("lfu_eviction")
        if raw is None:
            # Also allow list-style
            if isinstance(report, list):
                for item in report:
                    if isinstance(item, dict) and item.get("id") == "lfu_eviction":
                        scenario1 = item
                        break
            else:
                # Try top-level keys
                scenario1 = report.get("lfu_eviction")
        else:
            scenario1 = raw

        if scenario1 is None:
            checks.append({
                "name": "LFU eviction: evicted key is 'C'",
                "passed": False,
                "detail": "lfu_eviction scenario result not found in report"
            })
        else:
            # Accept either evictedKey or evicted_key or similar
            evicted = (
                scenario1.get("evictedKey")
                or scenario1.get("evicted_key")
                or scenario1.get("evicted")
                or scenario1.get("evictedkey")
            )
            if evicted is None:
                # Check if it's nested
                evicted = scenario1.get("result", {}).get("evictedKey") if isinstance(scenario1.get("result"), dict) else None

            passed = str(evicted).upper() == "C" if evicted is not None else False
            checks.append({
                "name": "LFU eviction: evicted key is 'C'",
                "passed": passed,
                "detail": f"evicted key reported as: {evicted!r} (expected 'C')"
            })

            # Also verify D is still in cache (optional but reasonable)
            key_d_present = None
            if "dPresent" in scenario1:
                key_d_present = scenario1["dPresent"]
            elif "result" in scenario1 and isinstance(scenario1["result"], dict):
                key_d_present = scenario1["result"].get("dPresent")

            if key_d_present is not None:
                checks.append({
                    "name": "LFU eviction: key D is present after insertion",
                    "passed": bool(key_d_present),
                    "detail": f"dPresent={key_d_present!r}"
                })
    except Exception as e:
        checks.append({
            "name": "LFU eviction: evicted key is 'C'",
            "passed": False,
            "detail": f"Exception during check: {e}"
        })

    # ══════════════════════════════════════════════════════════════════════════
    # SCENARIO 2 – TTL expiry
    # Immediate get → hit: true
    # After 100ms  → hit: false, reason: 'expired'
    # ══════════════════════════════════════════════════════════════════════════
    try:
        scenario2 = None
        raw = report.get("ttl_expiry") or report.get("scenarios", {}).get("ttl_expiry")
        if raw is None and isinstance(report, list):
            for item in report:
                if isinstance(item, dict) and item.get("id") == "ttl_expiry":
                    scenario2 = item
                    break
        else:
            scenario2 = raw

        if scenario2 is None:
            checks.append({
                "name": "TTL expiry: immediate get is a hit",
                "passed": False,
                "detail": "ttl_expiry scenario result not found in report"
            })
            checks.append({
                "name": "TTL expiry: post-expiry get has hit=false and reason='expired'",
                "passed": False,
                "detail": "ttl_expiry scenario result not found in report"
            })
        else:
            # Immediate get
            immediate = (
                scenario2.get("immediateGet")
                or scenario2.get("immediate_get")
                or scenario2.get("firstGet")
                or scenario2.get("first_get")
                or (scenario2.get("result", {}).get("immediateGet") if isinstance(scenario2.get("result"), dict) else None)
            )
            if isinstance(immediate, dict):
                imm_hit = immediate.get("hit")
            else:
                imm_hit = None

            checks.append({
                "name": "TTL expiry: immediate get is a hit",
                "passed": imm_hit is True,
                "detail": f"immediateGet.hit = {imm_hit!r} (expected True)"
            })

            # Expired get
            expired = (
                scenario2.get("expiredGet")
                or scenario2.get("expired_get")
                or scenario2.get("secondGet")
                or scenario2.get("second_get")
                or (scenario2.get("result", {}).get("expiredGet") if isinstance(scenario2.get("result"), dict) else None)
            )
            if isinstance(expired, dict):
                exp_hit    = expired.get("hit")
                exp_reason = expired.get("reason")
            else:
                exp_hit, exp_reason = None, None

            exp_passed = (exp_hit is False) and (str(exp_reason).lower() == "expired")
            checks.append({
                "name": "TTL expiry: post-expiry get has hit=false and reason='expired'",
                "passed": exp_passed,
                "detail": f"expiredGet = hit={exp_hit!r}, reason={exp_reason!r} (expected hit=False, reason='expired')"
            })
    except Exception as e:
        checks.append({
            "name": "TTL expiry: immediate get is a hit",
            "passed": False,
            "detail": f"Exception: {e}"
        })
        checks.append({
            "name": "TTL expiry: post-expiry get has hit=false and reason='expired'",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ══════════════════════════════════════════════════════════════════════════
    # SCENARIO 3 – Stats check
    # maxSize=10, 7 keys inserted
    # getStats() must return:
    #   { size: 7, maxSize: 10, strategy: 'lru', hitRate: 70 }
    # hitRate = Math.round((7/10)*100) = 70  ← proprietary formula
    # ══════════════════════════════════════════════════════════════════════════
    try:
        scenario3 = None
        raw = report.get("stats_check") or report.get("scenarios", {}).get("stats_check")
        if raw is None and isinstance(report, list):
            for item in report:
                if isinstance(item, dict) and item.get("id") == "stats_check":
                    scenario3 = item
                    break
        else:
            scenario3 = raw

        if scenario3 is None:
            for sub in ["size", "maxSize", "strategy", "hitRate"]:
                checks.append({
                    "name": f"Stats: {sub} field correct",
                    "passed": False,
                    "detail": "stats_check scenario result not found in report"
                })
        else:
            stats = (
                scenario3.get("stats")
                or scenario3.get("result")
                or scenario3
            )
            if not isinstance(stats, dict):
                for sub in ["size", "maxSize", "strategy", "hitRate"]:
                    checks.append({
                        "name": f"Stats: {sub} field correct",
                        "passed": False,
                        "detail": f"stats is not a dict: {stats!r}"
                    })
            else:
                expected_stats = {"size": 7, "maxSize": 10, "strategy": "lru", "hitRate": 70}
                for field, expected_val in expected_stats.items():
                    actual = stats.get(field)
                    passed = actual == expected_val
                    checks.append({
                        "name": f"Stats: '{field}' field correct",
                        "passed": passed,
                        "detail": f"got {actual!r}, expected {expected_val!r}"
                    })
    except Exception as e:
        for sub in ["size", "maxSize", "strategy", "hitRate"]:
            checks.append({
                "name": f"Stats: {sub} field correct",
                "passed": False,
                "detail": f"Exception: {e}"
            })

    return checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = run_eval(workspace)

    passed_checks = [c for c in checks if c["passed"]]
    total   = len(checks)
    n_pass  = len(passed_checks)
    score   = round(n_pass / total, 4) if total > 0 else 0.0
    overall = score == 1.0

    result = {
        "passed": overall,
        "score":  score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()