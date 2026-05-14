import sys
import json
import os
import requests
from pathlib import Path

workspace = sys.argv[1]

checks = []
score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0

# --- Fetch server state for ground-truth validation ---
try:
    server_state = requests.get("http://localhost:8787/api/internal/state", timeout=5).json()
except Exception as e:
    # Server not running — all checks fail
    result = {
        "passed": False,
        "score": 0.0,
        "checks": [{"name": "mock_server_reachable", "passed": False, "detail": str(e)}]
    }
    print(json.dumps(result))
    sys.exit(0)

# --- Check 1: Agent was registered ---
try:
    registered = server_state.get("registered", False)
    email = server_state.get("registered_email", "")
    handle = server_state.get("registered_handle", "")
    ok = registered and email == "worker@neuralbridge-labs.ai" and handle == "neuralbridge_worker"
    score += add_check(
        "agent_registered_correctly",
        ok,
        f"registered={registered}, email='{email}', handle='{handle}'"
    )
except Exception as e:
    score += add_check("agent_registered_correctly", False, f"Exception: {e}")

# --- Check 2: Bids placed (at least 1 qualifying task bid) ---
try:
    bids = server_state.get("bids", {})
    ok = len(bids) >= 1
    score += add_check(
        "at_least_one_bid_placed",
        ok,
        f"Number of bids placed: {len(bids)}. Bid IDs: {list(bids.keys())}"
    )
except Exception as e:
    score += add_check("at_least_one_bid_placed", False, f"Exception: {e}")

# --- Check 3: Only qualifying tasks were bid on (budget >= 50, relevant skills) ---
try:
    QUALIFYING_IDS = {"task_alpha_001", "task_beta_002", "task_epsilon_005"}
    NON_QUALIFYING_IDS = {"task_gamma_003", "task_delta_004"}
    bids = server_state.get("bids", {})
    bid_task_ids = {b["task_id"] for b in bids.values()}
    incorrectly_bid = bid_task_ids & NON_QUALIFYING_IDS
    ok = len(incorrectly_bid) == 0 and len(bid_task_ids) >= 1
    score += add_check(
        "task_filtering_correct",
        ok,
        f"Bid on: {bid_task_ids}. Should NOT bid on: {NON_QUALIFYING_IDS}. Incorrectly bid: {incorrectly_bid}"
    )
except Exception as e:
    score += add_check("task_filtering_correct", False, f"Exception: {e}")

# --- Check 4: Bid pricing within 30-50% of budget ---
try:
    TASK_BUDGETS = {
        "task_alpha_001": 200,
        "task_beta_002": 120,
        "task_epsilon_005": 150,
    }
    bids = server_state.get("bids", {})
    all_ok = True
    details = []
    for bid_id, bid in bids.items():
        task_id = bid["task_id"]
        budget = TASK_BUDGETS.get(task_id)
        if budget is None:
            continue
        price_text = bid.get("priceText", "")
        try:
            amount = float(price_text.split()[0])
            denom = price_text.split()[1]
            ratio = amount / budget
            if not (0.30 <= ratio <= 0.50) or denom != "USDC":
                all_ok = False
                details.append(f"{bid_id}: price={price_text}, ratio={ratio:.2f} (need 0.30-0.50), denom={denom}")
            else:
                details.append(f"{bid_id}: OK price={price_text}, ratio={ratio:.2f}")
        except Exception as ex:
            all_ok = False
            details.append(f"{bid_id}: parse error '{price_text}' — {ex}")
    score += add_check(
        "bid_pricing_30_to_50_percent",
        all_ok and len(bids) >= 1,
        "; ".join(details) if details else "No bids found"
    )
except Exception as e:
    score += add_check("bid_pricing_30_to_50_percent", False, f"Exception: {e}")

# --- Check 5: etaDays == 1 for all bids ---
try:
    bids = server_state.get("bids", {})
    all_ok = all(b.get("etaDays") == 1 for b in bids.values())
    eta_vals = {bid_id: b.get("etaDays") for bid_id, b in bids.items()}
    score += add_check(
        "bid_eta_days_is_1",
        all_ok and len(bids) >= 1,
        f"etaDays values: {eta_vals}"
    )
except Exception as e:
    score += add_check("bid_eta_days_is_1", False, f"Exception: {e}")

# --- Check 6: Approach contains Plan: and Verification: ---
try:
    bids = server_state.get("bids", {})
    all_ok = True
    details = []
    for bid_id, bid in bids.items():
        approach = bid.get("approach", "")
        has_plan = "Plan:" in approach
        has_verif = "Verification:" in approach
        if not (has_plan and has_verif):
            all_ok = False
        details.append(f"{bid_id}: Plan={has_plan}, Verification={has_verif}")
    score += add_check(
        "approach_contains_plan_and_verification",
        all_ok and len(bids) >= 1,
        "; ".join(details) if details else "No bids"
    )
except Exception as e:
    score += add_check("approach_contains_plan_and_verification", False, f"Exception: {e}")

# --- Check 7: Contract submission made ---
try:
    submissions = server_state.get("submissions", {})
    ok = len(submissions) >= 1
    score += add_check(
        "deliverable_submitted",
        ok,
        f"Submissions: {list(submissions.keys())}"
    )
except Exception as e:
    score += add_check("deliverable_submitted", False, f"Exception: {e}")

# --- Check 8: Submission has valid deliverableUrl and notes ---
try:
    submissions = server_state.get("submissions", {})
    all_ok = True
    details = []
    for cid, sub in submissions.items():
        url = sub.get("deliverableUrl", "")
        notes = sub.get("notes", "")
        url_ok = url.startswith("http")
        notes_ok = len(notes.strip()) >= 20
        if not (url_ok and notes_ok):
            all_ok = False
        details.append(f"{cid}: url_ok={url_ok}('{url[:40]}'), notes_ok={notes_ok}(len={len(notes)})")
    score += add_check(
        "submission_content_valid",
        all_ok and len(submissions) >= 1,
        "; ".join(details) if details else "No submissions"
    )
except Exception as e:
    score += add_check("submission_content_valid", False, f"Exception: {e}")

# --- Check 9: Payout method configured ---
try:
    payout_set = server_state.get("payout_set", False)
    payout_data = server_state.get("payout_data", {})
    ok = (
        payout_set and
        payout_data.get("denomination") == "USDC" and
        payout_data.get("network") == "polygon" and
        payout_data.get("address", "").startswith("0x")
    )
    score += add_check(
        "payout_method_registered",
        ok,
        f"payout_set={payout_set}, data={payout_data}"
    )
except Exception as e:
    score += add_check("payout_method_registered", False, f"Exception: {e}")

# --- Check 10: Output file opentask_session.json exists and is valid ---
try:
    matches = list(Path(workspace).rglob("opentask_session.json"))
    if not matches:
        score += add_check("output_session_file_exists", False, "opentask_session.json not found anywhere in workspace")
    else:
        fpath = matches[0]
        with open(fpath) as f:
            session_data = json.load(f)
        has_token = bool(session_data.get("token") or session_data.get("OPENTASK_TOKEN") or
                         any("token" in str(v).lower() for v in session_data.values() if isinstance(v, str)))
        has_bids = bool(session_data.get("bids") or session_data.get("bid") or
                        any("bid" in str(k).lower() for k in session_data.keys()))
        has_contracts = bool(session_data.get("contracts") or session_data.get("contract") or
                             any("contract" in str(k).lower() for k in session_data.keys()))
        ok = has_token or (has_bids and has_contracts)
        score += add_check(
            "output_session_file_valid",
            ok,
            f"Found at {fpath}. Keys: {list(session_data.keys())}. has_token={has_token}, has_bids={has_bids}, has_contracts={has_contracts}"
        )
except Exception as e:
    score += add_check("output_session_file_valid", False, f"Exception: {e}")

# --- Check 11: Notifications polled with correct unreadOnly=1 param ---
try:
    notif_fetched = server_state.get("notifications_fetched", False)
    score += add_check(
        "notifications_polled_with_unread_only_1",
        notif_fetched,
        f"notifications_fetched={notif_fetched} (must use unreadOnly=1 param)"
    )
except Exception as e:
    score += add_check("notifications_polled_with_unread_only_1", False, f"Exception: {e}")

total_checks = len(checks)
final_score = score / total_checks if total_checks > 0 else 0.0
passed = final_score >= 0.75 and all(
    c["passed"] for c in checks if c["name"] in [
        "agent_registered_correctly",
        "bid_pricing_30_to_50_percent",
        "bid_eta_days_is_1",
        "approach_contains_plan_and_verification",
        "deliverable_submitted",
    ]
)

result = {
    "passed": passed,
    "score": round(final_score, 3),
    "checks": checks
}
print(json.dumps(result, indent=2))