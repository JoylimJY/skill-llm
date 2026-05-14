#!/usr/bin/env python3
"""
Evaluation script for the SplitXCH nested royalty split task.
Checks:
1. Output file royalty_split.json exists
2. File contains a valid top-level XCH split address
3. Two API calls were made (leaf + parent)
4. Leaf (Studio Collective) split: 3 recipients, each with equal points summing to 9850
5. Parent split: 3 recipients (Zara, Studio Collective addr, Neon Records), points sum to 9850
6. Basis points math is correct for each level
7. The Studio Collective address from call 1 is used as a recipient in call 2
8. The top-level address in royalty_split.json matches the address returned by call 2
"""
import sys
import json
import math
from pathlib import Path

def load_calls_log():
    try:
        calls = []
        with open("/tmp/splitxch_calls.jsonl") as f:
            for line in f:
                line = line.strip()
                if line:
                    calls.append(json.loads(line))
        return calls, None
    except FileNotFoundError:
        return [], "No API calls log found at /tmp/splitxch_calls.jsonl"
    except Exception as e:
        return [], f"Error reading calls log: {e}"

def find_output_file(workspace):
    candidates = list(Path(workspace).rglob("royalty_split.json"))
    if not candidates:
        return None
    # prefer non-history files
    for c in candidates:
        if "history" not in str(c) and "draft" not in str(c).lower():
            return c
    return candidates[0]

def check_bps_collective(recipients):
    """
    3 session musicians, equal share of the collective.
    Each gets 33.333...% of 9850.
    round(1/3 * 9850) = round(3283.33) = 3283
    Two get 3283, last gets 9850 - 2*3283 = 3284
    Valid combos: (3283, 3283, 3284) or (3284, 3283, 3283) etc.
    Also accept (3283, 3284, 3283) — any permutation.
    """
    if len(recipients) != 3:
        return False, f"Expected 3 recipients, got {len(recipients)}"
    pts = sorted([r.get("points", 0) for r in recipients])
    expected = sorted([3283, 3283, 3284])
    if pts == expected:
        return True, f"Points {pts} match expected {expected}"
    # Also accept if someone rounded differently but still sums to 9850 and each > 0
    total = sum(pts)
    if total != 9850:
        return False, f"Points sum to {total}, expected 9850"
    # Check all equal-ish: each should be 3283 or 3284
    if all(p in (3283, 3284) for p in pts):
        return True, f"Points {pts} are valid equal-thirds rounding"
    return False, f"Points {pts} are not valid equal-thirds of 9850"

def check_bps_parent(recipients):
    """
    Zara: 55% -> round(0.55 * 9850) = round(5417.5) = 5418 (Python rounds to even: 5418)
    Studio Collective: 30% -> round(0.30 * 9850) = round(2955.0) = 2955
    Neon Records: 15% -> 9850 - 5418 - 2955 = 477
    Check: round(0.15*9850) = round(1477.5) = 1478 (round half to even)
    Adjusted last = 9850 - 5418 - 2955 = 477
    
    BUT order matters for "last recipient" adjustment - the last one listed absorbs rounding.
    Multiple valid arrangements exist. We check: sum=9850, Zara~5418, Collective~2955, Label~477
    """
    if len(recipients) != 3:
        return False, f"Expected 3 recipients, got {len(recipients)}"
    total = sum(r.get("points", 0) for r in recipients)
    if total != 9850:
        return False, f"Parent points sum to {total}, expected 9850"
    
    pts_by_name = {}
    for r in recipients:
        pts_by_name[r.get("name", "").lower()] = r.get("points", 0)
    
    details = []
    ok = True
    
    # Find Zara (55%)
    zara_pts = None
    for k, v in pts_by_name.items():
        if "zara" in k or "artist" in k or "lead" in k:
            zara_pts = v
            break
    if zara_pts is None:
        # Try to identify by points near 5418
        candidates = [v for v in pts_by_name.values() if abs(v - 5418) <= 2]
        if candidates:
            zara_pts = candidates[0]
    
    # Find collective (30%)
    coll_pts = None
    for k, v in pts_by_name.items():
        if "collective" in k or "studio" in k or "team" in k or "group" in k:
            coll_pts = v
            break
    if coll_pts is None:
        candidates = [v for v in pts_by_name.values() if abs(v - 2955) <= 2]
        if candidates:
            coll_pts = candidates[0]
    
    # Find label (15%)
    label_pts = None
    for k, v in pts_by_name.items():
        if "neon" in k or "label" in k or "reserve" in k or "record" in k:
            label_pts = v
            break
    if label_pts is None:
        # It's whatever is left
        known = set()
        if zara_pts: known.add(zara_pts)
        if coll_pts: known.add(coll_pts)
        for v in pts_by_name.values():
            if v not in known:
                label_pts = v
    
    # Validate: the three values should sum to 9850 and be close to (5418, 2955, 477)
    # Allow ±1 for rounding variations, but collectively must sum to 9850
    expected_set = sorted([5418, 2955, 477])
    actual_set = sorted([v for v in pts_by_name.values()])
    
    # Check each is within 1 of expected
    all_match = all(abs(a - e) <= 1 for a, e in zip(actual_set, expected_set))
    if all_match:
        details.append(f"Points {actual_set} match expected {expected_set} (within ±1)")
    else:
        ok = False
        details.append(f"Points {actual_set} do not match expected {expected_set}")
    
    return ok, "; ".join(details)

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    
    # --- Check 1: Output file exists ---
    output_file = find_output_file(workspace)
    file_exists = output_file is not None
    checks.append({
        "name": "royalty_split.json exists",
        "passed": file_exists,
        "detail": str(output_file) if file_exists else "File not found in workspace"
    })
    
    output_data = None
    if file_exists:
        try:
            with open(output_file) as f:
                output_data = json.load(f)
        except Exception as e:
            checks.append({
                "name": "royalty_split.json is valid JSON",
                "passed": False,
                "detail": str(e)
            })
    
    # --- Check 2: Output file has a valid XCH split address ---
    top_address = None
    if output_data is not None:
        # Look for an address field (could be nested)
        def find_addresses(obj, depth=0):
            addrs = []
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, str) and v.startswith("xch1") and len(v) > 20:
                        addrs.append(v)
                    else:
                        addrs.extend(find_addresses(v, depth+1))
            elif isinstance(obj, list):
                for item in obj:
                    addrs.extend(find_addresses(item, depth+1))
            return addrs
        
        addresses_in_file = find_addresses(output_data)
        # The "main" address is likely under "split_address", "address", or similar
        for key in ["split_address", "address", "royalty_address", "payment_address", "top_level_address"]:
            if key in output_data and isinstance(output_data[key], str) and output_data[key].startswith("xch1"):
                top_address = output_data[key]
                break
        if top_address is None and addresses_in_file:
            top_address = addresses_in_file[-1]  # last address is likely the parent
        
        has_valid_address = top_address is not None and top_address.startswith("xch1")
        checks.append({
            "name": "Output file contains valid XCH split address",
            "passed": has_valid_address,
            "detail": f"Found address: {top_address}" if has_valid_address else f"No valid xch1 address found. Addresses: {addresses_in_file}"
        })
    
    # --- Check 3: API calls were made ---
    calls, calls_err = load_calls_log()
    num_calls = len(calls)
    
    checks.append({
        "name": "At least 2 API calls made (nested split)",
        "passed": num_calls >= 2,
        "detail": f"Found {num_calls} API call(s). {calls_err or ''}"
    })
    
    if num_calls < 2:
        # Can't do deeper checks
        final_passed = all(c["passed"] for c in checks)
        score = sum(1 for c in checks if c["passed"]) / len(checks)
        print(json.dumps({"passed": final_passed, "score": score, "checks": checks}))
        return
    
    # --- Check 4: Find the leaf (Studio Collective) call ---
    # The leaf call will have 3 recipients all with xch1 addresses from the deal_memo
    collective_addresses = {
        "xch1mw4p7n3kqx9r2fl8vc5te6dy0hs1ujg2bz4an8xk7mp3q5l9efr0tgdvs",  # Marcus
        "xch1pk8l2q5wr7nx3yd4fs9cv0bh6mt1ej5au3rn2xg8lp4k7q9d0cfr1shmz",  # Priya
        "xch1ds6m3p8kq2xr4nl9fw5vc7tb0hy1ej3au5rn4xg2lp8k0q7d6cfr9smvz",  # Dmitri
    }
    lead_artist_addr = "xch1zv8r9k2pmn4x5qjfl3wd6uthcn7ae2sg0yp8mvx3dlk5q9h6frt2scewj"
    label_addr = "xch1nr5k8q2pm7x4rfl9wd3vc6th0ys1uj8gb2az4xn7lp5q3m9d0efr6twsc"
    
    leaf_call = None
    parent_call = None
    
    for call in calls:
        req = call.get("request", {})
        recips = req.get("recipients", [])
        addrs = set(r.get("address", "") for r in recips)
        # Is this the leaf (collective) call?
        if collective_addresses.issubset(addrs) or addrs == collective_addresses:
            leaf_call = call
        # Is this the parent call?
        elif lead_artist_addr in addrs and label_addr in addrs:
            parent_call = call
    
    # Fallback: first call is leaf, second is parent (most likely ordering)
    if leaf_call is None and num_calls >= 1:
        leaf_call = calls[0]
    if parent_call is None and num_calls >= 2:
        parent_call = calls[-1]
    
    # --- Check 5: Leaf call has correct recipients and basis points ---
    if leaf_call is not None:
        leaf_recips = leaf_call.get("request", {}).get("recipients", [])
        bps_ok, bps_detail = check_bps_collective(leaf_recips)
        
        # Check all three session musicians are present
        leaf_addrs = set(r.get("address", "") for r in leaf_recips)
        all_musicians_present = collective_addresses.issubset(leaf_addrs)
        
        checks.append({
            "name": "Leaf (Studio Collective) split: all 3 session musicians present",
            "passed": all_musicians_present,
            "detail": f"Found addresses: {leaf_addrs}. Expected all of: {collective_addresses}"
        })
        checks.append({
            "name": "Leaf (Studio Collective) split: equal basis points (each ~3283-3284, sum=9850)",
            "passed": bps_ok,
            "detail": bps_detail
        })
    else:
        checks.append({
            "name": "Leaf (Studio Collective) split: all 3 session musicians present",
            "passed": False,
            "detail": "Could not identify leaf call"
        })
        checks.append({
            "name": "Leaf (Studio Collective) split: equal basis points",
            "passed": False,
            "detail": "Could not identify leaf call"
        })
    
    # --- Check 6: Parent call uses the leaf split's returned address ---
    leaf_address_returned = None
    if leaf_call is not None:
        leaf_address_returned = leaf_call.get("response", {}).get("address")
    
    if parent_call is not None and leaf_address_returned is not None:
        parent_recips = parent_call.get("request", {}).get("recipients", [])
        parent_addrs = [r.get("address", "") for r in parent_recips]
        uses_leaf_addr = leaf_address_returned in parent_addrs
        checks.append({
            "name": "Parent split uses Studio Collective's split address as recipient",
            "passed": uses_leaf_addr,
            "detail": f"Leaf address: {leaf_address_returned}. Parent recipients: {parent_addrs}"
        })
    else:
        checks.append({
            "name": "Parent split uses Studio Collective's split address as recipient",
            "passed": False,
            "detail": f"Could not verify. leaf_call={leaf_call is not None}, parent_call={parent_call is not None}, leaf_addr={leaf_address_returned}"
        })
    
    # --- Check 7: Parent call has correct basis points ---
    if parent_call is not None:
        parent_recips = parent_call.get("request", {}).get("recipients", [])
        bps_ok, bps_detail = check_bps_parent(parent_recips)
        
        # Check lead artist and label are present
        parent_addrs_set = set(r.get("address", "") for r in parent_recips)
        lead_present = lead_artist_addr in parent_addrs_set
        label_present = label_addr in parent_addrs_set
        
        checks.append({
            "name": "Parent split: lead artist and label addresses present",
            "passed": lead_present and label_present,
            "detail": f"Lead artist present: {lead_present}, Label present: {label_present}"
        })
        checks.append({
            "name": "Parent split: correct basis points (55%~5418, 30%~2955, 15%~477, sum=9850)",
            "passed": bps_ok,
            "detail": bps_detail
        })
    else:
        checks.append({
            "name": "Parent split: lead artist and label addresses present",
            "passed": False,
            "detail": "Could not identify parent call"
        })
        checks.append({
            "name": "Parent split: correct basis points",
            "passed": False,
            "detail": "Could not identify parent call"
        })
    
    # --- Check 8: Final address in output matches parent call response ---
    parent_response_address = None
    if parent_call is not None:
        parent_response_address = parent_call.get("response", {}).get("address")
    
    if top_address is not None and parent_response_address is not None:
        address_matches = top_address == parent_response_address
        checks.append({
            "name": "Output royalty_split.json contains the correct final split address",
            "passed": address_matches,
            "detail": f"File has: {top_address}. API returned: {parent_response_address}"
        })
    else:
        checks.append({
            "name": "Output royalty_split.json contains the correct final split address",
            "passed": False,
            "detail": f"top_address={top_address}, parent_response_address={parent_response_address}"
        })
    
    # --- Final scoring ---
    passed_count = sum(1 for c in checks if c["passed"])
    total_count = len(checks)
    score = passed_count / total_count
    
    # Must pass critical checks to be considered overall passing
    critical_checks = [
        "At least 2 API calls made (nested split)",
        "Leaf (Studio Collective) split: equal basis points (each ~3283-3284, sum=9850)",
        "Parent split: correct basis points (55%~5418, 30%~2955, 15%~477, sum=9850)",
        "Parent split uses Studio Collective's split address as recipient",
        "Output royalty_split.json contains the correct final split address",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )
    
    overall_passed = critical_passed and score >= 0.75
    
    print(json.dumps({
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }))

if __name__ == "__main__":
    main()