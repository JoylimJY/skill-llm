import os
import json
import random
import stat
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Distractor directory structure ──────────────────────────────────────────
dirs = [
    "scripts",
    "configs",
    "logs",
    "data/products",
    "data/users",
    "data/orders",
    "tmp/cache",
    "tmp/sessions",
    "docs/internal",
    "docs/api",
    "tests/unit",
    "tests/integration",
    ".openclaw/credentials/agent-commerce-engine",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files ─────────────────────────────────────────────────────────
distractor_files = {
    "configs/legacy_api.json": json.dumps({
        "base_url": "https://old-lafeitu.cn/api/v0",
        "version": "0.8",
        "deprecated": True
    }, indent=2),
    "configs/env_template.txt": "LAFEITU_API_KEY=\nLAFEITU_ENV=production\nDEBUG=false\n",
    "logs/api_errors_2024.log": "\n".join([
        "2024-01-15 10:23:01 ERROR 401 Unauthorized /api/v1/cart",
        "2024-01-15 10:23:05 ERROR 404 Not Found /api/v1/products/wrong-slug",
        "2024-01-15 11:00:00 ERROR 429 Rate limit exceeded",
    ]),
    "logs/access_2024.log": "2024-01-15 GET /api/v1/products 200\n2024-01-15 POST /api/v1/cart 200\n",
    "data/products/stale_catalog.csv": "slug,name,price\nold-tu,旧版兔肉,29.9\nlengchi-tu,冷吃兔,39.9\n",
    "data/users/sample_user.json": json.dumps({
        "email": "test_old@example.com",
        "name": "旧用户",
        "note": "DO NOT USE - outdated record"
    }, indent=2),
    "data/orders/order_template.json": json.dumps({
        "items": [],
        "shipping": {},
        "status": "draft",
        "note": "template only, not a real order"
    }, indent=2),
    "tmp/cache/product_cache.json": json.dumps({"ttl": 300, "entries": {}}, indent=2),
    "tmp/sessions/anon_session.json": json.dumps({
        "session_id": "anon_abc123xyz",
        "cart": [],
        "created_at": "2024-01-15T09:00:00Z"
    }, indent=2),
    "docs/internal/workflow_draft.md": "# Draft: Order Automation\n\nThis doc is a WIP. See official SKILL.md for actual commands.\n",
    "docs/api/endpoints_v0.md": "# Deprecated API Docs v0\n\nThese endpoints are no longer valid. All routes changed in v1.\n",
    "tests/unit/test_cart.py": "# placeholder\ndef test_add_to_cart():\n    pass\n",
    "tests/integration/test_order_flow.py": "# placeholder\ndef test_full_order():\n    pass\n",
}

for rel_path, content in distractor_files.items():
    fpath = workspace / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content, encoding="utf-8")

# ── THE MOCK SERVER ──────────────────────────────────────────────────────────
# We write a Flask mock server that simulates the Lafeitu API
mock_server_code = r'''#!/usr/bin/env python3
"""
Mock server for https://lafeitu.cn/api/v1
Runs on http://127.0.0.1:8999
Stores state in /tmp/lafeitu_mock_state/
"""
import json, os, random, string, time
from pathlib import Path
from flask import Flask, request, jsonify

app = Flask(__name__)
STATE_DIR = Path("/tmp/lafeitu_mock_state")
STATE_DIR.mkdir(parents=True, exist_ok=True)

PRODUCTS = {
    "lengchi-tu": {
        "slug": "lengchi-tu",
        "name": "冷吃兔",
        "description": "Zigong-style cold-eat rabbit, numbing and spicy",
        "variants": [150, 200, 300],
        "prices": {"150": 35.0, "200": 45.0, "300": 62.0},
        "category": "rabbit-specialty"
    },
    "shousi-tu": {
        "slug": "shousi-tu",
        "name": "手撕兔",
        "description": "Hand-torn rabbit, classic Sichuan flavor",
        "variants": [200, 400],
        "prices": {"200": 48.0, "400": 88.0},
        "category": "rabbit-specialty"
    },
    "mala-tu-ding": {
        "slug": "mala-tu-ding",
        "name": "麻辣兔丁",
        "description": "Mala spicy rabbit cubes, intense flavor",
        "variants": [200, 500],
        "prices": {"200": 42.0, "500": 98.0},
        "category": "rabbit-specialty"
    },
    "zhangcha-ya": {
        "slug": "zhangcha-ya",
        "name": "樟茶鸭",
        "description": "Camphor tea smoked duck",
        "variants": [300, 600],
        "prices": {"300": 55.0, "600": 105.0},
        "category": "duck-specialty"
    }
}

def state_file(name):
    return STATE_DIR / f"{name}.json"

def load_state(name, default):
    f = state_file(name)
    if f.exists():
        return json.loads(f.read_text())
    return default

def save_state(name, data):
    state_file(name).write_text(json.dumps(data, ensure_ascii=False, indent=2))

def get_token_from_request():
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None

def get_logged_in_user():
    token = get_token_from_request()
    if not token:
        return None
    tokens = load_state("tokens", {})
    return tokens.get(token)

# ── Visitor/anonymous cart ───────────────────────────────────────────────────
@app.route("/api/v1/visitor", methods=["POST"])
def create_visitor():
    vid = "vis_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=12))
    visitors = load_state("visitors", {})
    visitors[vid] = {"cart": {}}
    save_state("visitors", visitors)
    return jsonify({"visitor_id": vid, "token": vid})

# ── Auth ─────────────────────────────────────────────────────────────────────
@app.route("/api/v1/auth/send-code", methods=["POST"])
def send_code():
    data = request.get_json() or {}
    email = data.get("email", "")
    if not email:
        return jsonify({"error": "email required"}), 400
    codes = load_state("codes", {})
    # Fixed code for determinism in tests
    codes[email] = "847291"
    save_state("codes", codes)
    return jsonify({"message": "verification code sent", "email": email})

@app.route("/api/v1/auth/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    email = data.get("email", "")
    password = data.get("password", "")
    code = data.get("code", "")
    name = data.get("name", "")
    reset_visitor = data.get("reset_visitor", False)

    codes = load_state("codes", {})
    if codes.get(email) != code:
        return jsonify({"error": "invalid verification code"}), 400

    users = load_state("users", {})
    if email in users:
        return jsonify({"error": "email already registered"}), 409

    users[email] = {"email": email, "password": password, "name": name}
    save_state("users", users)

    token = "tok_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=20))
    tokens = load_state("tokens", {})
    tokens[token] = email
    save_state("tokens", tokens)

    # If reset_visitor, start fresh cart
    carts = load_state("carts", {})
    if reset_visitor:
        carts[email] = {}
    save_state("carts", carts)

    reg_log = load_state("registration_log", [])
    reg_log.append({"email": email, "reset_visitor": reset_visitor, "timestamp": time.time()})
    save_state("registration_log", reg_log)

    return jsonify({"message": "registered", "token": token, "email": email})

@app.route("/api/v1/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email", "")
    password = data.get("password", "")
    users = load_state("users", {})
    if email not in users or users[email]["password"] != password:
        return jsonify({"error": "invalid credentials"}), 401
    token = "tok_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=20))
    tokens = load_state("tokens", {})
    tokens[token] = email
    save_state("tokens", tokens)
    return jsonify({"token": token, "email": email})

# ── Products ─────────────────────────────────────────────────────────────────
@app.route("/api/v1/products", methods=["GET"])
def list_products():
    q = request.args.get("q", "").lower()
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 10))
    results = list(PRODUCTS.values())
    if q:
        results = [p for p in results if q in p["name"].lower() or q in p["slug"].lower() or q in p["description"].lower()]
    start = (page-1)*limit
    return jsonify({"products": results[start:start+limit], "total": len(results), "page": page, "limit": limit})

@app.route("/api/v1/products/<slug>", methods=["GET"])
def get_product(slug):
    p = PRODUCTS.get(slug)
    if not p:
        return jsonify({"error": "product not found"}), 404
    return jsonify(p)

# ── Promotions ────────────────────────────────────────────────────────────────
@app.route("/api/v1/promotions", methods=["GET"])
def promotions():
    return jsonify({
        "promotions": [
            {"id": "promo1", "description": "满99元包邮", "threshold": 99, "type": "free_shipping"},
            {"id": "promo2", "description": "新用户首单9折", "discount": 0.9, "type": "new_user"}
        ],
        "shipping_threshold": 99
    })

# ── Cart ──────────────────────────────────────────────────────────────────────
def get_cart_key():
    user = get_logged_in_user()
    if user:
        return user
    # anonymous: use visitor token
    token = get_token_from_request()
    return token or "anon"

@app.route("/api/v1/cart", methods=["GET"])
def get_cart():
    key = get_cart_key()
    carts = load_state("carts", {})
    cart = carts.get(key, {})
    items = []
    total = 0.0
    for item_key, item in cart.items():
        slug, variant = item_key.split("__")
        p = PRODUCTS.get(slug, {})
        price = p.get("prices", {}).get(variant, 0)
        subtotal = price * item["quantity"]
        total += subtotal
        items.append({
            "slug": slug,
            "name": p.get("name", slug),
            "variant": int(variant),
            "quantity": item["quantity"],
            "price": price,
            "subtotal": subtotal
        })
    return jsonify({"items": items, "total": round(total, 2), "count": len(items)})

@app.route("/api/v1/cart/add", methods=["POST"])
def add_cart():
    data = request.get_json() or {}
    slug = data.get("slug", "")
    variant = str(data.get("variant", ""))
    qty = int(data.get("quantity", 1))
    p = PRODUCTS.get(slug)
    if not p:
        return jsonify({"error": "product not found"}), 404
    if int(variant) not in p["variants"]:
        return jsonify({"error": f"invalid variant {variant}, valid: {p['variants']}"}), 400
    key = get_cart_key()
    carts = load_state("carts", {})
    cart = carts.get(key, {})
    item_key = f"{slug}__{variant}"
    if item_key in cart:
        cart[item_key]["quantity"] += qty
    else:
        cart[item_key] = {"quantity": qty}
    carts[key] = cart
    save_state("carts", carts)
    return jsonify({"message": "added", "slug": slug, "variant": int(variant), "quantity": cart[item_key]["quantity"]})

@app.route("/api/v1/cart/update", methods=["POST"])
def update_cart():
    data = request.get_json() or {}
    slug = data.get("slug", "")
    variant = str(data.get("variant", ""))
    qty = int(data.get("quantity", 1))
    p = PRODUCTS.get(slug)
    if not p:
        return jsonify({"error": "product not found"}), 404
    if int(variant) not in p["variants"]:
        return jsonify({"error": f"invalid variant {variant}, valid: {p['variants']}"}), 400
    key = get_cart_key()
    carts = load_state("carts", {})
    cart = carts.get(key, {})
    item_key = f"{slug}__{variant}"
    if qty <= 0:
        cart.pop(item_key, None)
    else:
        cart[item_key] = {"quantity": qty}
    carts[key] = cart
    save_state("carts", carts)
    return jsonify({"message": "updated", "slug": slug, "variant": int(variant), "quantity": qty})

@app.route("/api/v1/cart/remove", methods=["POST"])
def remove_cart():
    data = request.get_json() or {}
    slug = data.get("slug", "")
    variant = str(data.get("variant", ""))
    key = get_cart_key()
    carts = load_state("carts", {})
    cart = carts.get(key, {})
    item_key = f"{slug}__{variant}"
    cart.pop(item_key, None)
    carts[key] = cart
    save_state("carts", carts)
    return jsonify({"message": "removed"})

@app.route("/api/v1/cart/clear", methods=["POST"])
def clear_cart():
    key = get_cart_key()
    carts = load_state("carts", {})
    carts[key] = {}
    save_state("carts", carts)
    return jsonify({"message": "cart cleared"})

# ── Orders ────────────────────────────────────────────────────────────────────
@app.route("/api/v1/orders", methods=["GET"])
def list_orders():
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401
    orders = load_state("orders", {})
    user_orders = [o for o in orders.values() if o.get("email") == user]
    return jsonify({"orders": user_orders})

@app.route("/api/v1/orders", methods=["POST"])
def create_order():
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json() or {}
    required = ["name", "phone", "province", "city", "address"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"missing field: {field}"}), 400

    carts = load_state("carts", {})
    cart = carts.get(user, {})
    if not cart:
        return jsonify({"error": "cart is empty"}), 400

    order_id = "LFT" + "".join(random.choices(string.digits, k=10))
    order = {
        "order_id": order_id,
        "email": user,
        "shipping": {k: data[k] for k in required},
        "items": list(cart.items()),
        "status": "pending_payment",
        "payment_url": f"https://lafeitu.cn/pay/{order_id}",
        "created_at": time.time()
    }
    orders = load_state("orders", {})
    orders[order_id] = order
    save_state("orders", orders)
    # Clear cart after order
    carts[user] = {}
    save_state("carts", carts)
    return jsonify({"order_id": order_id, "payment_url": order["payment_url"], "status": "pending_payment"})

# ── Brand ─────────────────────────────────────────────────────────────────────
@app.route("/api/v1/brand/story", methods=["GET"])
def brand_story():
    return jsonify({"story": "Lafeitu (辣匪兔) was founded in Zigong, Sichuan, home of the most authentic spicy rabbit dishes in China."})

@app.route("/api/v1/brand/company", methods=["GET"])
def company_info():
    return jsonify({"company": "四川辣匪兔食品有限公司", "founded": 2015, "location": "Zigong, Sichuan"})

@app.route("/api/v1/brand/contact", methods=["GET"])
def contact_info():
    return jsonify({"email": "contact@lafeitu.cn", "phone": "400-888-0辣", "wechat": "lafeitu_official"})

# ── Profile ───────────────────────────────────────────────────────────────────
@app.route("/api/v1/profile", methods=["GET"])
def get_profile():
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401
    users = load_state("users", {})
    u = users.get(user, {})
    return jsonify({"email": u.get("email"), "name": u.get("name", ""), "shipping": u.get("shipping", {})})

@app.route("/api/v1/profile", methods=["PUT"])
def update_profile():
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json() or {}
    users = load_state("users", {})
    u = users.get(user, {})
    for k, v in data.items():
        u[k] = v
    users[user] = u
    save_state("users", users)
    return jsonify({"message": "profile updated"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8999, debug=False)
'''
(workspace / "scripts" / "mock_server.py").write_text(mock_server_code)

# ── THE ACTUAL CLIENT SCRIPT ──────────────────────────────────────────────────
# This is the lafeitu_client.py referenced in SKILL.md
client_code = r'''#!/usr/bin/env python3
"""
Lafeitu Commerce Client
Official CLI for https://lafeitu.cn/api/v1
"""
import argparse
import json
import os
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: requests not installed. Run: pip install requests")
    sys.exit(1)

# Allow override via env for local testing
BASE_URL = os.environ.get("LAFEITU_API_URL", "https://lafeitu.cn/api/v1")
CREDS_DIR = Path(os.environ.get(
    "LAFEITU_CREDS_DIR",
    str(Path.home() / ".openclaw" / "credentials" / "agent-commerce-engine" / "lafeitu.cn")
))
CREDS_DIR.mkdir(parents=True, exist_ok=True)
TOKEN_FILE = CREDS_DIR / "token.json"

def load_token():
    if TOKEN_FILE.exists():
        try:
            return json.loads(TOKEN_FILE.read_text()).get("token")
        except Exception:
            return None
    return None

def save_token(token, email=""):
    TOKEN_FILE.write_text(json.dumps({"token": token, "email": email}))

def clear_token():
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()

def get_headers(token=None):
    headers = {"Content-Type": "application/json"}
    t = token or load_token()
    if t:
        headers["Authorization"] = f"Bearer {t}"
    return headers

def api_get(path, params=None):
    url = f"{BASE_URL}{path}"
    r = requests.get(url, headers=get_headers(), params=params, timeout=10)
    return r

def api_post(path, data=None):
    url = f"{BASE_URL}{path}"
    r = requests.post(url, headers=get_headers(), json=data or {}, timeout=10)
    return r

def api_put(path, data=None):
    url = f"{BASE_URL}{path}"
    r = requests.put(url, headers=get_headers(), json=data or {}, timeout=10)
    return r

def print_json(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))

def cmd_search(args):
    r = api_get("/products", params={"q": args.query, "page": args.page, "limit": args.limit})
    print_json(r.json())

def cmd_list(args):
    r = api_get("/products", params={"page": args.page, "limit": args.limit})
    print_json(r.json())

def cmd_get(args):
    r = api_get(f"/products/{args.slug}")
    if r.status_code == 404:
        print(json.dumps({"error": "product not found"}, ensure_ascii=False))
        sys.exit(1)
    print_json(r.json())

def cmd_promotions(args):
    r = api_get("/promotions")
    print_json(r.json())

def cmd_cart(args):
    r = api_get("/cart")
    print_json(r.json())

def cmd_add_cart(args):
    r = api_post("/cart/add", {"slug": args.slug, "variant": args.variant, "quantity": args.quantity})
    if r.status_code != 200:
        print(json.dumps(r.json(), ensure_ascii=False))
        sys.exit(1)
    print_json(r.json())

def cmd_update_cart(args):
    r = api_post("/cart/update", {"slug": args.slug, "variant": args.variant, "quantity": args.quantity})
    if r.status_code != 200:
        print(json.dumps(r.json(), ensure_ascii=False))
        sys.exit(1)
    print_json(r.json())

def cmd_remove_cart(args):
    r = api_post("/cart/remove", {"slug": args.slug, "variant": args.variant})
    print_json(r.json())

def cmd_clear_cart(args):
    r = api_post("/cart/clear")
    print_json(r.json())

def cmd_login(args):
    email = args.email or input("Email: ")
    password = args.password or input("Password: ")
    r = api_post("/auth/login", {"email": email, "password": password})
    if r.status_code != 200:
        print(json.dumps(r.json(), ensure_ascii=False))
        sys.exit(1)
    data = r.json()
    save_token(data["token"], data.get("email", email))
    print(json.dumps({"message": "logged in", "email": data.get("email", email)}, ensure_ascii=False, indent=2))

def cmd_logout(args):
    clear_token()
    print(json.dumps({"message": "logged out"}, ensure_ascii=False, indent=2))

def cmd_send_code(args):
    r = api_post("/auth/send-code", {"email": args.email})
    print_json(r.json())

def cmd_register(args):
    payload = {
        "email": args.email,
        "password": args.password,
        "code": args.code,
        "reset_visitor": args.reset_visitor,
    }
    if args.name:
        payload["name"] = args.name
    if args.invite:
        payload["invite"] = args.invite
    r = api_post("/auth/register", payload)
    if r.status_code not in (200, 201):
        print(json.dumps(r.json(), ensure_ascii=False))
        sys.exit(1)
    data = r.json()
    save_token(data["token"], data.get("email", args.email))
    print_json(data)

def cmd_get_profile(args):
    r = api_get("/profile")
    if r.status_code == 401:
        print(json.dumps({"error": "unauthorized - please login first"}, ensure_ascii=False))
        sys.exit(1)
    print_json(r.json())

def cmd_update_profile(args):
    data = {}
    if args.name:
        data["name"] = args.name
    if args.province:
        data.setdefault("shipping", {})["province"] = args.province
    if args.city:
        data.setdefault("shipping", {})["city"] = args.city
    if args.address:
        data.setdefault("shipping", {})["address"] = args.address
    r = api_put("/profile", data)
    print_json(r.json())

def cmd_orders(args):
    r = api_get("/orders")
    if r.status_code == 401:
        print(json.dumps({"error": "unauthorized - please login first"}, ensure_ascii=False))
        sys.exit(1)
    print_json(r.json())

def cmd_create_order(args):
    r = api_post("/orders", {
        "name": args.name,
        "phone": args.phone,
        "province": args.province,
        "city": args.city,
        "address": args.address,
    })
    if r.status_code != 200:
        print(json.dumps(r.json(), ensure_ascii=False))
        sys.exit(1)
    print_json(r.json())

def cmd_brand_story(args):
    r = api_get("/brand/story")
    print_json(r.json())

def cmd_company_info(args):
    r = api_get("/brand/company")
    print_json(r.json())

def cmd_contact_info(args):
    r = api_get("/brand/contact")
    print_json(r.json())

def main():
    parser = argparse.ArgumentParser(description="Lafeitu Commerce Client")
    sub = parser.add_subparsers(dest="command")

    # search
    p_search = sub.add_parser("search")
    p_search.add_argument("query")
    p_search.add_argument("--page", type=int, default=1)
    p_search.add_argument("--limit", type=int, default=10)

    # list
    p_list = sub.add_parser("list")
    p_list.add_argument("--page", type=int, default=1)
    p_list.add_argument("--limit", type=int, default=10)

    # get
    p_get = sub.add_parser("get")
    p_get.add_argument("slug")

    # promotions
    sub.add_parser("promotions")

    # cart
    sub.add_parser("cart")

    # add-cart
    p_ac = sub.add_parser("add-cart")
    p_ac.add_argument("slug")
    p_ac.add_argument("--variant", type=int, required=True)
    p_ac.add_argument("--quantity", type=int, default=1)

    # update-cart
    p_uc = sub.add_parser("update-cart")
    p_uc.add_argument("slug")
    p_uc.add_argument("--variant", type=int, required=True)
    p_uc.add_argument("--quantity", type=int, required=True)

    # remove-cart
    p_rc = sub.add_parser("remove-cart")
    p_rc.add_argument("slug")
    p_rc.add_argument("--variant", type=int, required=True)

    # clear-cart
    sub.add_parser("clear-cart")

    # login
    p_login = sub.add_parser("login")
    p_login.add_argument("--email", default="")
    p_login.add_argument("--password", default="")

    # logout
    sub.add_parser("logout")

    # send-code
    p_sc = sub.add_parser("send-code")
    p_sc.add_argument("--email", required=True)

    # register
    p_reg = sub.add_parser("register")
    p_reg.add_argument("--email", required=True)
    p_reg.add_argument("--password", required=True)
    p_reg.add_argument("--code", required=True)
    p_reg.add_argument("--name", default="")
    p_reg.add_argument("--invite", default="")
    p_reg.add_argument("--reset-visitor", action="store_true")

    # get-profile
    sub.add_parser("get-profile")

    # update-profile
    p_up = sub.add_parser("update-profile")
    p_up.add_argument("--name", default="")
    p_up.add_argument("--province", default="")
    p_up.add_argument("--city", default="")
    p_up.add_argument("--address", default="")

    # orders
    sub.add_parser("orders")

    # create-order
    p_co = sub.add_parser("create-order")
    p_co.add_argument("--name", required=True)
    p_co.add_argument("--phone", required=True)
    p_co.add_argument("--province", required=True)
    p_co.add_argument("--city", required=True)
    p_co.add_argument("--address", required=True)

    # brand
    sub.add_parser("brand-story")
    sub.add_parser("company-info")
    sub.add_parser("contact-info")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    dispatch = {
        "search": cmd_search,
        "list": cmd_list,
        "get": cmd_get,
        "promotions": cmd_promotions,
        "cart": cmd_cart,
        "add-cart": cmd_add_cart,
        "update-cart": cmd_update_cart,
        "remove-cart": cmd_remove_cart,
        "clear-cart": cmd_clear_cart,
        "login": cmd_login,
        "logout": cmd_logout,
        "send-code": cmd_send_code,
        "register": cmd_register,
        "get-profile": cmd_get_profile,
        "update-profile": cmd_update_profile,
        "orders": cmd_orders,
        "create-order": cmd_create_order,
        "brand-story": cmd_brand_story,
        "company-info": cmd_company_info,
        "contact-info": cmd_contact_info,
    }
    dispatch[args.command](args)

if __name__ == "__main__":
    main()
'''
(workspace / "scripts" / "lafeitu_client.py").write_text(client_code)
os.chmod(workspace / "scripts" / "lafeitu_client.py", 0o755)
os.chmod(workspace / "scripts" / "mock_server.py", 0o755)

# ── Task brief written to a non-standard location as "business context" ────
# This simulates a messy real-world handoff note, not a clean spec
task_brief = """\
Customer Journey Brief — Lafeitu Onboarding Automation
=======================================================
New customer: 王晓梅 (Wang Xiaomei)
Contact: 13912345678
Delivery region: 四川省 成都市 武侯区人民南路四段XX号

She is brand new — NO existing account on the platform.
Registration email to use: wxm_test_2024@lafeitu-user.com
Temporary password to set: Spicy@2024!
(Verification code will be sent to her email upon request)

Items she wants:
- 冷吃兔 (cold-eat rabbit) — the 200g size, she wants EXACTLY 3 packs
  (she first tried adding 2, but wants to correct it to 3)
- 手撕兔 (hand-torn rabbit) — the 400g size, 1 pack

After confirming the cart is correct, place the order on her behalf.
The order confirmation / payment link should be captured and saved
to a file named: order_result.json (placed anywhere accessible)

Note: she is a new user — make sure her account starts clean without
carrying over any anonymous browsing session data.
"""
(workspace / "docs" / "internal" / "customer_brief_wxm.txt").write_text(task_brief)

# Additional distractor: a stale order result to mislead
stale_result = {
    "order_id": "LFT0000000000",
    "payment_url": "https://lafeitu.cn/pay/LFT0000000000",
    "status": "STALE_DO_NOT_USE",
    "note": "This is a placeholder from a previous failed run"
}
(workspace / "data" / "orders" / "stale_order_result.json").write_text(
    json.dumps(stale_result, indent=2)
)

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")