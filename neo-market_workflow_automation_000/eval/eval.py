#!/usr/bin/env python3
import sys
import json
import os

def load_json_safe(path):
    try:
        with open(path, "r") as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, f"File not found: {path}"
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {e}"

def load_jsonl_safe(path):
    try:
        entries = []
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        return entries, None
    except FileNotFoundError:
        return None, f"File not found: {path}"
    except Exception as e:
        return None, f"Error reading JSONL: {e}"

checks = []
overall_passed = True

STATE_FILE = "/tmp/neo_market_state.json"
CALL_LOG = "/tmp/neo_market_calls.jsonl"

state, state_err = load_json_safe(STATE_FILE)
calls, calls_err = load_jsonl_safe(CALL_LOG)

# -------------------------------------------------------
# CHECK 1: Register was called with a valid ipfs:// manifest
# -------------------------------------------------------
check_name = "register_with_valid_ipfs_manifest"
try:
    if state_err:
        raise ValueError(f"State file error: {state_err}")
    if calls_err:
        raise ValueError(f"Call log error: {calls_err}")

    registered = state.get("registered", False)
    manifest = state.get("manifest", "")

    register_calls = [c for c in calls if c.get("command") == "register"]

    if not registered:
        raise ValueError("Agent never successfully registered (state.registered is False)")
    if not manifest:
        raise ValueError("No manifest stored in state")
    if not manifest.startswith("ipfs://"):
        raise ValueError(f"Manifest does not start with 'ipfs://': {manifest}")
    if len(register_calls) == 0:
        raise ValueError("No 'register' command found in call log")
    # Check the manifest arg in the call
    reg_manifest = register_calls[-1].get("args", {}).get("manifest", "")
    if not reg_manifest.startswith("ipfs://"):
        raise ValueError(f"register call used non-ipfs manifest: {reg_manifest}")

    checks.append({"name": check_name, "passed": True,
                   "detail": f"Registered with manifest: {manifest}"})
except Exception as e:
    checks.append({"name": check_name, "passed": False, "detail": str(e)})
    overall_passed = False

# -------------------------------------------------------
# CHECK 2: jobs was called (agent explored the marketplace)
# -------------------------------------------------------
check_name = "jobs_command_called"
try:
    if calls_err:
        raise ValueError(f"Call log error: {calls_err}")

    job_calls = [c for c in calls if c.get("command") == "jobs"]
    if len(job_calls) == 0:
        raise ValueError("Agent never called the 'jobs' command to list available work")

    checks.append({"name": check_name, "passed": True,
                   "detail": f"jobs called {len(job_calls)} time(s)"})
except Exception as e:
    checks.append({"name": check_name, "passed": False, "detail": str(e)})
    overall_passed = False

# -------------------------------------------------------
# CHECK 3: Bid placed on the correct job (Job #2, the ONLY Open job)
# -------------------------------------------------------
check_name = "bid_on_correct_open_job"
try:
    if state_err:
        raise ValueError(f"State file error: {state_err}")
    if calls_err:
        raise ValueError(f"Call log error: {calls_err}")

    bid_calls = [c for c in calls if c.get("command") == "bid"]
    if len(bid_calls) == 0:
        raise ValueError("Agent never called the 'bid' command")

    # Find successful bid calls (result contains "success")
    successful_bids = [c for c in bid_calls if "success" in str(c.get("result", ""))]
    if len(successful_bids) == 0:
        raise ValueError("No successful bid calls found in log. Check bid parameters.")

    last_bid = successful_bids[-1]
    bid_args = last_bid.get("args", {})
    job_id = int(bid_args.get("job", -1))

    if job_id != 2:
        raise ValueError(f"Bid placed on wrong job (#{job_id}). Only Job #2 has Status: Open.")

    checks.append({"name": check_name, "passed": True,
                   "detail": f"Correctly bid on Job #2 (the only Open job)"})
except Exception as e:
    checks.append({"name": check_name, "passed": False, "detail": str(e)})
    overall_passed = False

# -------------------------------------------------------
# CHECK 4: Bid price is 380 USDC
# -------------------------------------------------------
check_name = "bid_price_correct_380_usdc"
try:
    if state_err:
        raise ValueError(f"State file error: {state_err}")

    bids = state.get("bids", [])
    job2_bids = [b for b in bids if b.get("job_id") == 2]

    if not job2_bids:
        raise ValueError("No bids for job #2 found in state")

    last_bid = job2_bids[-1]
    price = float(last_bid.get("price", -1))

    if abs(price - 380.0) > 0.01:
        raise ValueError(f"Bid price is {price} USDC, expected 380 USDC")

    checks.append({"name": check_name, "passed": True,
                   "detail": f"Bid price correctly set to {price} USDC"})
except Exception as e:
    checks.append({"name": check_name, "passed": False, "detail": str(e)})
    overall_passed = False

# -------------------------------------------------------
# CHECK 5: Bid ETA is in SECONDS (7200 for 2 hours), NOT 2 (hours)
# -------------------------------------------------------
check_name = "bid_eta_in_seconds_7200"
try:
    if state_err:
        raise ValueError(f"State file error: {state_err}")

    bids = state.get("bids", [])
    job2_bids = [b for b in bids if b.get("job_id") == 2]

    if not job2_bids:
        raise ValueError("No bids for job #2 in state")

    last_bid = job2_bids[-1]
    eta = int(last_bid.get("eta", -1))

    # Must be 7200 seconds (2 hours). Common trap: agent sets eta=2 (hours) instead of 7200 (seconds)
    if eta == 2:
        raise ValueError(f"ETA is {eta} — this looks like hours, not seconds. The CLI requires seconds. 2 hours = 7200 seconds.")
    if eta != 7200:
        raise ValueError(f"ETA is {eta} seconds, expected 7200 (2 hours * 3600 s/hr)")

    checks.append({"name": check_name, "passed": True,
                   "detail": f"ETA correctly set to {eta} seconds (= 2 hours)"})
except Exception as e:
    checks.append({"name": check_name, "passed": False, "detail": str(e)})
    overall_passed = False

# -------------------------------------------------------
# CHECK 6: Bid CID uses ipfs:// prefix and correct CID
# -------------------------------------------------------
check_name = "bid_cid_valid_ipfs_uri"
try:
    if state_err:
        raise ValueError(f"State file error: {state_err}")

    bids = state.get("bids", [])
    job2_bids = [b for b in bids if b.get("job_id") == 2]

    if not job2_bids:
        raise ValueError("No bids for job #2 in state")

    last_bid = job2_bids[-1]
    cid = last_bid.get("cid", "")

    if not cid.startswith("ipfs://"):
        raise ValueError(f"Bid CID does not use ipfs:// prefix: '{cid}'. Distractor files show bare CIDs without prefix — agent must use the correct format.")
    if "QmProposalXYZ789abc" not in cid:
        raise ValueError(f"Bid CID '{cid}' does not contain the expected proposal CID 'QmProposalXYZ789abc'")

    checks.append({"name": check_name, "passed": True,
                   "detail": f"Bid CID correctly formatted: {cid}"})
except Exception as e:
    checks.append({"name": check_name, "passed": False, "detail": str(e)})
    overall_passed = False

# -------------------------------------------------------
# CHECK 7: Deliver called with correct job, escrow, and result CID
# -------------------------------------------------------
check_name = "delivery_with_correct_escrow_and_cid"
try:
    if state_err:
        raise ValueError(f"State file error: {state_err}")
    if calls_err:
        raise ValueError(f"Call log error: {calls_err}")

    deliveries = state.get("deliveries", [])
    job2_deliveries = [d for d in deliveries if d.get("job_id") == 2]

    if not job2_deliveries:
        raise ValueError("No deliveries found for job #2. Agent must call 'deliver' after placing bid.")

    last_delivery = job2_deliveries[-1]

    # Check escrow ID (must be 7, obtained from bid confirmation output)
    escrow_id = int(last_delivery.get("escrow_id", -1))
    if escrow_id != 7:
        raise ValueError(f"Wrong escrow ID: {escrow_id}. Expected 7 (from bid confirmation output). Distractor files show escrow=3 and escrow=22 — agent must use the actual value from the bid response.")

    # Check result CID
    result_cid = last_delivery.get("cid", "")
    if not result_cid.startswith("ipfs://"):
        raise ValueError(f"Delivery CID missing ipfs:// prefix: '{result_cid}'")
    if "QmResultABC123def" not in result_cid:
        raise ValueError(f"Delivery CID '{result_cid}' does not match expected 'ipfs://QmResultABC123def'")

    checks.append({"name": check_name, "passed": True,
                   "detail": f"Delivery correct: job=2, escrow={escrow_id}, cid={result_cid}"})
except Exception as e:
    checks.append({"name": check_name, "passed": False, "detail": str(e)})
    overall_passed = False

# -------------------------------------------------------
# CHECK 8: Job #2 final state is Completed
# -------------------------------------------------------
check_name = "job2_status_is_completed"
try:
    if state_err:
        raise ValueError(f"State file error: {state_err}")

    jobs = state.get("jobs", [])
    job2 = next((j for j in jobs if j["id"] == 2), None)

    if job2 is None:
        raise ValueError("Job #2 not found in state")

    status = job2.get("status", "")
    if status != "Completed":
        raise ValueError(f"Job #2 status is '{status}', expected 'Completed'. Full workflow not completed.")

    checks.append({"name": check_name, "passed": True,
                   "detail": f"Job #2 correctly moved to Completed state"})
except Exception as e:
    checks.append({"name": check_name, "passed": False, "detail": str(e)})
    overall_passed = False

# -------------------------------------------------------
# CHECK 9: Workflow order was correct (register → jobs → bid → deliver)
# -------------------------------------------------------
check_name = "correct_workflow_ordering"
try:
    if calls_err:
        raise ValueError(f"Call log error: {calls_err}")

    successful_cmds = [c["command"] for c in calls if "success" in str(c.get("result", ""))]

    if "register" not in successful_cmds:
        raise ValueError("register not in successful commands")
    if "bid" not in successful_cmds:
        raise ValueError("bid not in successful commands")
    if "deliver" not in successful_cmds:
        raise ValueError("deliver not in successful commands")

    reg_idx = next(i for i, c in enumerate(successful_cmds) if c == "register")
    bid_idx = next(i for i, c in enumerate(successful_cmds) if c == "bid")
    deliver_idx = next(i for i, c in enumerate(successful_cmds) if c == "deliver")

    if not (reg_idx < bid_idx < deliver_idx):
        raise ValueError(f"Workflow order incorrect: register@{reg_idx}, bid@{bid_idx}, deliver@{deliver_idx}. Must be register → bid → deliver.")

    checks.append({"name": check_name, "passed": True,
                   "detail": f"Correct order: register → (jobs) → bid → deliver"})
except Exception as e:
    checks.append({"name": check_name, "passed": False, "detail": str(e)})
    overall_passed = False

# -------------------------------------------------------
# Final scoring
# -------------------------------------------------------
n_passed = sum(1 for c in checks if c["passed"])
score = round(n_passed / len(checks), 4) if checks else 0.0

output = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}
print(json.dumps(output, indent=2))