#!/usr/bin/env python3
import json
import sys
import os
import time
import subprocess
from pathlib import Path

def run_checks(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    # Make sure env var is set for client calls
    env = os.environ.copy()
    env["LAFEITU_API_URL"] = "http://127.0.0.1:8999/api/v1"

    # ─────────────────────────────────────────────────────────────────────────
    # HELPER: Load mock state
    # ─────────────────────────────────────────────────────────────────────────
    STATE_DIR = Path("/tmp/lafeitu_mock_state")
    
    def load_state(name, default=None):
        f = STATE_DIR / f"{name}.json"
        if f.exists():
            try:
                return json.loads(f.read_text())
            except Exception:
                return default
        return default if default is not None else {}

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 1: User was registered with the correct email
    # ─────────────────────────────────────────────────────────────────────────
    check_name = "user_registered_with_correct_email"
    try:
        users = load_state("users", {})
        target_email = "wxm_test_2024@lafeitu-user.com"
        if target_email in users:
            checks.append({
                "name": check_name,
                "passed": True,
                "detail": f"User {target_email} found in registered users."
            })
        else:
            checks.append({
                "name": check_name,
                "passed": False,
                "detail": f"User {target_email} NOT found. Registered users: {list(users.keys())}"
            })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 2: Registration used --reset-visitor flag
    # ─────────────────────────────────────────────────────────────────────────
    check_name = "registration_used_reset_visitor"
    try:
        reg_log = load_state("registration_log", [])
        target_email = "wxm_test_2024@lafeitu-user.com"
        user_reg = [r for r in reg_log if r.get("email") == target_email]
        if user_reg and user_reg[-1].get("reset_visitor") is True:
            checks.append({
                "name": check_name,
                "passed": True,
                "detail": "Registration included reset_visitor=True as required."
            })
        else:
            detail = (
                f"Registration log for {target_email}: {user_reg}. "
                "Expected reset_visitor=True."
            )
            checks.append({"name": check_name, "passed": False, "detail": detail})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 3: Token saved locally (user is logged in after registration)
    # ─────────────────────────────────────────────────────────────────────────
    check_name = "token_saved_after_registration"
    try:
        token_file = Path.home() / ".openclaw" / "credentials" / "agent-commerce-engine" / "lafeitu.cn" / "token.json"
        if token_file.exists():
            token_data = json.loads(token_file.read_text())
            token_val = token_data.get("token", "")
            if token_val.startswith("tok_"):
                checks.append({
                    "name": check_name,
                    "passed": True,
                    "detail": f"Token file exists with valid token starting with 'tok_'."
                })
            else:
                checks.append({
                    "name": check_name,
                    "passed": False,
                    "detail": f"Token file exists but token value looks wrong: {token_val[:20]}"
                })
        else:
            checks.append({
                "name": check_name,
                "passed": False,
                "detail": f"Token file not found at {token_file}"
            })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 4: Cart ended up with correct items and quantities
    # We verify the final order items because cart is cleared post-order.
    # We check via the orders state.
    # ─────────────────────────────────────────────────────────────────────────
    check_name = "cart_had_correct_items_before_order"
    try:
        orders = load_state("orders", {})
        target_email = "wxm_test_2024@lafeitu-user.com"
        user_orders = [o for o in orders.values() if o.get("email") == target_email]
        if not user_orders:
            checks.append({
                "name": check_name,
                "passed": False,
                "detail": "No orders found for the user; cannot verify cart contents."
            })
        else:
            order = user_orders[-1]  # most recent
            items_dict = dict(order.get("items", []))
            # expected: lengchi-tu__200 -> qty 3, shousi-tu__400 -> qty 1
            lc_key = "lengchi-tu__200"
            st_key = "shousi-tu__400"
            lc_item = items_dict.get(lc_key, {})
            st_item = items_dict.get(st_key, {})
            lc_qty = lc_item.get("quantity", 0) if isinstance(lc_item, dict) else 0
            st_qty = st_item.get("quantity", 0) if isinstance(st_item, dict) else 0
            
            if lc_qty == 3 and st_qty == 1:
                checks.append({
                    "name": check_name,
                    "passed": True,
                    "detail": f"lengchi-tu/200g qty=3, shousi-tu/400g qty=1. Correct!"
                })
            else:
                checks.append({
                    "name": check_name,
                    "passed": False,
                    "detail": (
                        f"Expected lengchi-tu/200g qty=3 (got {lc_qty}), "
                        f"shousi-tu/400g qty=1 (got {st_qty}). "
                        f"Full items: {items_dict}"
                    )
                })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 5: update-cart was used to correct lengchi-tu quantity to 3
    # (not just add-cart twice). We detect this by verifying the final qty is
    # exactly 3. If they used add-cart twice from 0, they'd have qty=2 unless
    # they correctly used update-cart. We rely on the cart logic:
    # add-cart increments, update-cart sets absolute.
    # A naive agent would add-cart 3 times or add-cart twice (getting qty 2 or 4).
    # The correct flow per SKILL.md: add-cart (qty 2) then update-cart (qty 3).
    # We verify the final qty is exactly 3, which requires update-cart.
    # This is partially covered by check 4, so this is a more specific detail check.
    # ─────────────────────────────────────────────────────────────────────────
    check_name = "lengchi_tu_quantity_exactly_3"
    try:
        orders = load_state("orders", {})
        target_email = "wxm_test_2024@lafeitu-user.com"
        user_orders = [o for o in orders.values() if o.get("email") == target_email]
        if not user_orders:
            checks.append({
                "name": check_name,
                "passed": False,
                "detail": "No orders found to verify lengchi-tu quantity."
            })
        else:
            order = user_orders[-1]
            items_dict = dict(order.get("items", []))
            lc_item = items_dict.get("lengchi-tu__200", {})
            lc_qty = lc_item.get("quantity", 0) if isinstance(lc_item, dict) else 0
            passed = lc_qty == 3
            checks.append({
                "name": check_name,
                "passed": passed,
                "detail": f"lengchi-tu/200g quantity in order = {lc_qty} (expected 3)"
            })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 6: Correct shipping details in the order
    # ─────────────────────────────────────────────────────────────────────────
    check_name = "order_has_correct_shipping_details"
    try:
        orders = load_state("orders", {})
        target_email = "wxm_test_2024@lafeitu-user.com"
        user_orders = [o for o in orders.values() if o.get("email") == target_email]
        if not user_orders:
            checks.append({
                "name": check_name,
                "passed": False,
                "detail": "No orders found for the user."
            })
        else:
            order = user_orders[-1]
            shipping = order.get("shipping", {})
            
            name_ok = "王晓梅" in shipping.get("name", "") or "Wang Xiaomei" in shipping.get("name", "")
            phone_ok = "13912345678" in shipping.get("phone", "")
            province_ok = "四川" in shipping.get("province", "")
            city_ok = "成都" in shipping.get("city", "")
            address_ok = len(shipping.get("address", "")) > 3  # some address provided
            
            all_ok = name_ok and phone_ok and province_ok and city_ok and address_ok
            checks.append({
                "name": check_name,
                "passed": all_ok,
                "detail": (
                    f"name_ok={name_ok}, phone_ok={phone_ok}, "
                    f"province_ok={province_ok}, city_ok={city_ok}, "
                    f"address_ok={address_ok}. Shipping: {shipping}"
                )
            })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 7: order_result.json file was created with valid order data
    # ─────────────────────────────────────────────────────────────────────────
    check_name = "order_result_json_created"
    try:
        # Search entire filesystem for order_result.json (excluding stale distractor)
        found_files = [
            f for f in Path("/").rglob("order_result.json")
            if "stale" not in str(f) and str(f) != "/workspace/data/orders/stale_order_result.json"
        ]
        
        if not found_files:
            # Also check workspace specifically
            found_files = list(workspace.rglob("order_result.json"))
            found_files = [f for f in found_files if f.name == "order_result.json" and "stale" not in str(f)]
        
        if not found_files:
            checks.append({
                "name": check_name,
                "passed": False,
                "detail": "order_result.json not found anywhere in the filesystem."
            })
        else:
            # Check the most recently modified one
            result_file = sorted(found_files, key=lambda f: f.stat().st_mtime, reverse=True)[0]
            content = json.loads(result_file.read_text())
            
            has_order_id = bool(content.get("order_id", "").startswith("LFT"))
            has_payment_url = "lafeitu.cn/pay/" in content.get("payment_url", "")
            not_stale = content.get("status") != "STALE_DO_NOT_USE"
            is_pending = content.get("status") == "pending_payment"
            
            passed = has_order_id and has_payment_url and not_stale
            checks.append({
                "name": check_name,
                "passed": passed,
                "detail": (
                    f"File: {result_file}. "
                    f"has_order_id={has_order_id}, has_payment_url={has_payment_url}, "
                    f"not_stale={not_stale}, is_pending={is_pending}. "
                    f"Content keys: {list(content.keys())}"
                )
            })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 8: order_result.json has a REAL order_id matching mock state
    # (not the stale placeholder LFT0000000000)
    # ─────────────────────────────────────────────────────────────────────────
    check_name = "order_result_matches_real_order"
    try:
        found_files = [
            f for f in Path("/").rglob("order_result.json")
            if str(f) != "/workspace/data/orders/stale_order_result.json"
        ]
        if not found_files:
            found_files = [
                f for f in workspace.rglob("order_result.json")
                if "stale" not in str(f)
            ]
        
        if not found_files:
            checks.append({
                "name": check_name,
                "passed": False,
                "detail": "order_result.json not found."
            })
        else:
            result_file = sorted(found_files, key=lambda f: f.stat().st_mtime, reverse=True)[0]
            content = json.loads(result_file.read_text())
            order_id = content.get("order_id", "")
            
            # Verify this order_id exists in mock state
            orders = load_state("orders", {})
            order_exists_in_mock = order_id in orders
            not_placeholder = order_id != "LFT0000000000"
            
            passed = order_exists_in_mock and not_placeholder and order_id.startswith("LFT")
            checks.append({
                "name": check_name,
                "passed": passed,
                "detail": (
                    f"order_id='{order_id}', "
                    f"exists_in_mock={order_exists_in_mock}, "
                    f"not_placeholder={not_placeholder}"
                )
            })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 9: Variants were correctly resolved (not guessed)
    # lengchi-tu has variants [150, 200, 300] - agent must use 200 (not "200g")
    # shousi-tu has variants [200, 400] - agent must use 400
    # ─────────────────────────────────────────────────────────────────────────
    check_name = "correct_variants_used"
    try:
        orders = load_state("orders", {})
        target_email = "wxm_test_2024@lafeitu-user.com"
        user_orders = [o for o in orders.values() if o.get("email") == target_email]
        if not user_orders:
            checks.append({
                "name": check_name,
                "passed": False,
                "detail": "No orders found to verify variant usage."
            })
        else:
            order = user_orders[-1]
            items_dict = dict(order.get("items", []))
            has_lengchi_200 = "lengchi-tu__200" in items_dict
            has_shousi_400 = "shousi-tu__400" in items_dict
            passed = has_lengchi_200 and has_shousi_400
            checks.append({
                "name": check_name,
                "passed": passed,
                "detail": (
                    f"lengchi-tu__200 present={has_lengchi_200}, "
                    f"shousi-tu__400 present={has_shousi_400}. "
                    f"All item keys: {list(items_dict.keys())}"
                )
            })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ─────────────────────────────────────────────────────────────────────────
    # Aggregate score
    # ─────────────────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4) if total > 0 else 0.0
    all_passed = all(c["passed"] for c in checks)

    return {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "args", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)
    
    result = run_checks(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))