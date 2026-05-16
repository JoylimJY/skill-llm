#!/usr/bin/env python3
"""
Generate the sandbox workspace for the buyma-order-automation task.
All random operations use fixed seeds for determinism.
"""
import os
import random
import json
from pathlib import Path
from datetime import datetime, timedelta
import openpyxl
from openpyxl import Workbook
import pandas as pd

random.seed(42)

# ─── Root workspace ────────────────────────────────────────────────────────────
WS = Path(os.environ.get("WORKSPACE", "/workspace"))

def mkdirs(*paths):
    for p in paths:
        Path(p).mkdir(parents=True, exist_ok=True)

# ─── Directory structure ───────────────────────────────────────────────────────
dirs = [
    WS / ".openclaw/workspace/buyma_order/orders/incoming",
    WS / ".openclaw/workspace/buyma_order/orders/current",
    WS / ".openclaw/workspace/buyma_order/orders/archive",
    WS / ".openclaw/workspace/buyma_order/templates",
    WS / ".openclaw/workspace/buyma_order/state",
    WS / ".openclaw/workspace/buyma_order/logs",
    WS / ".openclaw/workspace/buyma_order/csv_inbox",
    WS / ".openclaw/workspace/buyma_order/csv_processed",
    WS / "scripts",
    WS / "references",
    WS / "config",
    WS / "tmp",
    WS / ".openclaw/workspace/buyma_order/orders/delivered",
]
for d in dirs:
    mkdirs(d)

# ─── Distractor files ──────────────────────────────────────────────────────────
distractor_data = [
    (WS / "config/settings.json",           '{"mode": "daily", "tz": "Asia/Seoul", "mail_deadline": "08:30"}'),
    (WS / "config/telegram.conf",           '[telegram]\nbot_token=DUMMY\nchat_id=0000000'),
    (WS / "references/workflow.md",         '# Workflow\nSee SKILL.md for authoritative steps.'),
    (WS / "references/failure-rules.md",    '# Failure Rules\nStop on buyma/csv/mail failure. Notify via Telegram.'),
    (WS / "references/run-modes.md",        '# Run Modes\nregular: daily 08:30 deadline\nadhoc: operator range'),
    (WS / "references/memo-rules.md",       '# Memo Rules\n6-digit prepend if memo has text or short number.\nNo rewrite if already valid 6-digit.'),
    (WS / ".openclaw/workspace/buyma_order/logs/run_20260306.log",
     "2026-03-06 07:45:01 INFO run completed ok\n2026-03-06 07:45:02 INFO mail sent"),
    (WS / ".openclaw/workspace/buyma_order/logs/run_20260305.log",
     "2026-03-05 07:50:00 INFO run completed ok"),
    (WS / ".openclaw/workspace/buyma_order/state/last_run.json",
     '{"last_order": 124099, "run_date": "2026-03-06", "mode": "daily"}'),
    (WS / "tmp/scratch.txt",                "scratch pad – do not use"),
    (WS / ".openclaw/workspace/buyma_order/csv_processed/old_buyma_20260305.csv",
     "order_id,product,qty\n124000,Jacket A,1\n124001,Skirt B,2"),
]
for fpath, content in distractor_data:
    fpath.write_text(content, encoding="utf-8")

# ─── Helper: make a workbook with order rows ───────────────────────────────────
HEADERS = ["A_order_id", "B_buyer", "C_product_jp", "D_qty", "E_price_jpy",
           "F_product_kr", "G_shipping", "H_tracking", "I_category",
           "J_supplier", "K_memo", "L_status", "M_note"]

def make_workbook(orders, wb_path):
    """orders: list of dicts with HEADERS keys"""
    wb = Workbook()
    ws_sheet = wb.active
    ws_sheet.title = "Orders"
    ws_sheet.append(HEADERS)
    for row in orders:
        ws_sheet.append([row.get(h, "") for h in HEADERS])
    wb.save(str(wb_path))


# ─── 1. Template ───────────────────────────────────────────────────────────────
template_path = WS / ".openclaw/workspace/buyma_order/templates/tmazonORDERLIST_template.xlsx"
make_workbook([], template_path)

# ─── 2. Archive (old) workbook in current/ ─────────────────────────────────────
# This is an older automation-created file (last order 124070)
archive_orders = [
    {"A_order_id": str(i), "B_buyer": f"Buyer{i}", "C_product_jp": f"商品{i}",
     "D_qty": "1", "E_price_jpy": "12000", "F_product_kr": f"상품{i}",
     "G_shipping": "EMS", "H_tracking": f"JA00{i}JP",
     "I_category": "Tops", "J_supplier": "SupplierA",
     "K_memo": str(i),   # valid 6-digit order id already
     "L_status": "shipped", "M_note": "ok"}
    for i in range(124060, 124071)
]
current_wb_path = WS / ".openclaw/workspace/buyma_order/orders/current/tmazonORDERLIST260306_124060-124070.xlsx"
make_workbook(archive_orders, current_wb_path)

# ─── 3. Incoming (operator-delivered) workbook ─────────────────────────────────
# This is the LATEST delivered file — last order is 124099
incoming_orders = [
    {"A_order_id": str(i), "B_buyer": f"Buyer{i}", "C_product_jp": f"商品{i}",
     "D_qty": "1", "E_price_jpy": "15000", "F_product_kr": f"상품{i}",
     "G_shipping": "DHL", "H_tracking": f"JB00{i}JP",
     "I_category": "Bottoms", "J_supplier": "SupplierB",
     "K_memo": str(i),
     "L_status": "delivered", "M_note": "verified"}
    for i in range(124085, 124100)
]
incoming_wb_path = WS / ".openclaw/workspace/buyma_order/orders/incoming/tmazonORDERLIST260307_124085-124099.xlsx"
make_workbook(incoming_orders, incoming_wb_path)

# ─── 4. Buyma CSV (ad hoc range 124100–124115) ─────────────────────────────────
# Memo field has mixed states to test the prepend rule:
#   - some orders: memo is already 6-digit order id (no rewrite)
#   - some orders: memo has short number (< 6 digits) → prepend
#   - some orders: memo has text → prepend
csv_rows = []
for i in range(124100, 124116):
    if i % 3 == 0:
        memo = str(i)          # already valid 6-digit → do NOT rewrite
    elif i % 3 == 1:
        memo = str(i % 1000)   # short number (3 digits) → prepend order id
    else:
        memo = "要確認"          # text → prepend order id
    csv_rows.append({
        "order_id":     str(i),
        "buyer":        f"Buyer{i}",
        "product_jp":   f"商品{i}",
        "qty":          1,
        "price_jpy":    18000,
        "shipping":     "Yamato",
        "tracking":     f"JC00{i}JP",
        "memo":         memo,
        "status":       "pending",
    })

csv_path = WS / ".openclaw/workspace/buyma_order/csv_inbox/buyma_export_20260307.csv"
pd.DataFrame(csv_rows).to_csv(str(csv_path), index=False, encoding="utf-8-sig")

# ─── 5. History workbook (for enrich_from_history enrichment) ─────────────────
# Contains I/J/M data for some order ids in the new range
history_wb_path = WS / ".openclaw/workspace/buyma_order/orders/archive/tmazonORDERLIST260301_123990-124010.xlsx"
history_orders = [
    {"A_order_id": str(i), "B_buyer": f"OldBuyer{i}", "C_product_jp": f"旧商品{i}",
     "D_qty": "1", "E_price_jpy": "9000", "F_product_kr": f"구상품{i}",
     "G_shipping": "EMS", "H_tracking": f"JH00{i}JP",
     "I_category": "Outerwear", "J_supplier": "SupplierC",
     "K_memo": str(i),
     "L_status": "delivered", "M_note": "history_note"}
    for i in range(123990, 124011)
]
make_workbook(history_orders, history_wb_path)

# ─── 6. Scripts — bespoke CLI scripts referenced in SKILL.md ──────────────────
# These scripts must be created as functional stubs that the agent can call.

# --- select_base_file.py ---
(WS / "scripts/select_base_file.py").write_text(r"""#!/usr/bin/env python3
\"\"\"
Select the base order workbook per priority rules:
  1. Latest file in ~/.openclaw/workspace/buyma_order/orders/incoming/
  2. Latest file in ~/.openclaw/workspace/buyma_order/orders/current/
  3. ~/.openclaw/workspace/buyma_order/templates/tmazonORDERLIST_template.xlsx

Prints the selected file path and the last order number found in column A.

Usage: python select_base_file.py
Output JSON: {"base_file": "<path>", "last_order_number": <int>}
\"\"\"
import json, os
from pathlib import Path
import openpyxl

HOME = Path.home()
WORKSPACE = Path(os.environ.get("WORKSPACE", str(Path(__file__).parent.parent)))
BASE = WORKSPACE / ".openclaw/workspace/buyma_order/orders"

def latest_xlsx(directory):
    files = sorted(Path(directory).glob("*.xlsx"), key=lambda f: f.stat().st_mtime, reverse=True)
    return files[0] if files else None

def last_order_in(wb_path):
    wb = openpyxl.load_workbook(str(wb_path))
    ws = wb.active
    last = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        try:
            v = int(str(row[0]).strip())
            if v > last:
                last = v
        except Exception:
            pass
    return last

candidates = [
    latest_xlsx(BASE / "incoming"),
    latest_xlsx(BASE / "current"),
    WORKSPACE / ".openclaw/workspace/buyma_order/templates/tmazonORDERLIST_template.xlsx",
]

selected = next((c for c in candidates if c and Path(c).exists()), None)
last_order = last_order_in(selected) if selected else 0
print(json.dumps({"base_file": str(selected), "last_order_number": last_order}))
""", encoding="utf-8")

# --- parse_buyma_csv.py ---
(WS / "scripts/parse_buyma_csv.py").write_text(r"""#!/usr/bin/env python3
\"\"\"
Parse a Buyma CSV and apply memo numbering rules.

Memo rules (from references/memo-rules.md):
  - If memo already contains a valid 6-digit order number → do NOT rewrite
  - If memo contains text OR a number shorter than 6 digits → PREPEND the
    6-digit order_id before the existing memo content (space-separated)

Usage: python parse_buyma_csv.py <csv_path> [--start <order_id>] [--end <order_id>]
Output: prints JSON list of parsed order dicts with corrected memo field.
\"\"\"
import sys, json, re
import pandas as pd

def is_valid_6digit(s):
    return bool(re.fullmatch(r'\d{6}', str(s).strip()))

def apply_memo_rule(order_id, memo):
    memo_str = str(memo).strip() if memo == memo else ""
    if is_valid_6digit(memo_str):
        return memo_str  # already valid — do NOT rewrite
    # text or short number → prepend
    order_str = str(order_id).strip().zfill(6)
    if memo_str:
        return f"{order_str} {memo_str}"
    return order_str

csv_path = sys.argv[1]
start_id = int(sys.argv[sys.argv.index("--start") + 1]) if "--start" in sys.argv else None
end_id   = int(sys.argv[sys.argv.index("--end")   + 1]) if "--end"   in sys.argv else None

df = pd.read_csv(csv_path)
if start_id:
    df = df[df["order_id"].astype(int) >= start_id]
if end_id:
    df = df[df["order_id"].astype(int) <= end_id]

records = []
for _, row in df.iterrows():
    r = row.to_dict()
    r["memo"] = apply_memo_rule(r["order_id"], r.get("memo", ""))
    records.append(r)

print(json.dumps(records, ensure_ascii=False))
""", encoding="utf-8")

# --- build_order_sheet.py ---
(WS / "scripts/build_order_sheet.py").write_text(r"""#!/usr/bin/env python3
\"\"\"
Build the draft order workbook from parsed CSV records and a base workbook.

Usage: python build_order_sheet.py <parsed_json_path> <base_wb_path> <output_path>

Columns: A=order_id, B=buyer, C=product_jp, D=qty, E=price_jpy,
         F=product_kr (placeholder), G=shipping, H=tracking,
         I=category, J=supplier, K=memo, L=status, M=note
\"\"\"
import sys, json
from pathlib import Path
import openpyxl
from openpyxl import Workbook

parsed_path = sys.argv[1]
base_path   = sys.argv[2]
out_path    = sys.argv[3]

with open(parsed_path, encoding="utf-8") as f:
    records = json.load(f)

HEADERS = ["A_order_id","B_buyer","C_product_jp","D_qty","E_price_jpy",
           "F_product_kr","G_shipping","H_tracking","I_category",
           "J_supplier","K_memo","L_status","M_note"]

COL_MAP = {
    "A_order_id": "order_id", "B_buyer": "buyer", "C_product_jp": "product_jp",
    "D_qty": "qty", "E_price_jpy": "price_jpy", "F_product_kr": "product_kr",
    "G_shipping": "shipping", "H_tracking": "tracking", "I_category": "category",
    "J_supplier": "supplier", "K_memo": "memo", "L_status": "status", "M_note": "note",
}

wb = Workbook()
ws = wb.active
ws.title = "Orders"
ws.append(HEADERS)
for rec in records:
    row = []
    for h in HEADERS:
        csv_key = COL_MAP.get(h, h)
        row.append(rec.get(csv_key, rec.get(h, "")))
    ws.append(row)

wb.save(out_path)
print(f"Saved: {out_path}")
""", encoding="utf-8")

# --- enrich_from_history.py ---
(WS / "scripts/enrich_from_history.py").write_text(r"""#!/usr/bin/env python3
\"\"\"
Enrich columns I (category), J (supplier), M (note) in the draft workbook
by looking up matching order_ids from the most recent prior workbook history.

History search order:
  1. Files in orders/archive/ (by mtime, newest first)
  2. Files in orders/current/ (by mtime, newest first)

Usage: python enrich_from_history.py <draft_wb_path>
Modifies the workbook in-place.
\"\"\"
import sys, os
from pathlib import Path
import openpyxl

WORKSPACE = Path(os.environ.get("WORKSPACE", str(Path(__file__).parent.parent)))
BASE = WORKSPACE / ".openclaw/workspace/buyma_order/orders"

draft_path = sys.argv[1]

def load_history_map():
    hmap = {}
    for folder in ["archive", "current"]:
        files = sorted((BASE / folder).glob("*.xlsx"), key=lambda f: f.stat().st_mtime, reverse=True)
        for fpath in files:
            wb = openpyxl.load_workbook(str(fpath))
            ws = wb.active
            headers = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1))]
            for row in ws.iter_rows(min_row=2, values_only=True):
                rdict = dict(zip(headers, row))
                oid = str(rdict.get("A_order_id", "")).strip()
                if oid and oid not in hmap:
                    hmap[oid] = {
                        "I_category": rdict.get("I_category", ""),
                        "J_supplier": rdict.get("J_supplier", ""),
                        "M_note":     rdict.get("M_note", ""),
                    }
    return hmap

hmap = load_history_map()

wb = openpyxl.load_workbook(str(draft_path))
ws = wb.active
headers = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1))]
col_idx = {h: i+1 for i, h in enumerate(headers)}

for row in ws.iter_rows(min_row=2):
    oid_cell = row[col_idx["A_order_id"] - 1]
    oid = str(oid_cell.value).strip() if oid_cell.value else ""
    if oid in hmap:
        entry = hmap[oid]
        for col_name, val in entry.items():
            if col_name in col_idx and val:
                row[col_idx[col_name] - 1].value = val

wb.save(str(draft_path))
print(f"Enriched: {draft_path}")
""", encoding="utf-8")

# --- validate_output.py ---
(WS / "scripts/validate_output.py").write_text(r"""#!/usr/bin/env python3
\"\"\"
Validate the output workbook:
  - Must have header row matching expected columns
  - Column A (order_id) must be all numeric
  - Column K (memo) must follow memo rules:
      * If original csv memo was valid 6-digit → unchanged
      * Otherwise → starts with the 6-digit order_id
  - Must have at least 1 data row

Usage: python validate_output.py <wb_path>
Prints JSON: {"valid": bool, "issues": [str]}
\"\"\"
import sys, json, re
import openpyxl

EXPECTED_HEADERS = ["A_order_id","B_buyer","C_product_jp","D_qty","E_price_jpy",
                    "F_product_kr","G_shipping","H_tracking","I_category",
                    "J_supplier","K_memo","L_status","M_note"]

wb = openpyxl.load_workbook(sys.argv[1])
ws = wb.active
headers = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1))]
issues = []

if headers != EXPECTED_HEADERS:
    issues.append(f"Header mismatch: {headers}")

rows = list(ws.iter_rows(min_row=2, values_only=True))
if not rows:
    issues.append("No data rows")

for r in rows:
    oid = str(r[0]).strip() if r[0] else ""
    memo = str(r[10]).strip() if r[10] else ""
    if not re.fullmatch(r'\d+', oid):
        issues.append(f"Non-numeric order_id: {oid}")
    # memo must start with a 6-digit number (either the order_id itself or prepended)
    if not re.match(r'^\d{6}', memo):
        issues.append(f"Memo missing 6-digit prefix for order {oid}: '{memo}'")

result = {"valid": len(issues) == 0, "issues": issues}
print(json.dumps(result, ensure_ascii=False))
""", encoding="utf-8")

# --- compose_output_filename.py ---
(WS / "scripts/compose_output_filename.py").write_text(r"""#!/usr/bin/env python3
\"\"\"
Compose the output filename from the workbook contents.

Format: tmazonORDERLISTYYMMDD_start-end.xlsx
  - YYMMDD: today's date in local time (Asia/Seoul preferred, fallback UTC)
  - start:  minimum order_id in the workbook
  - end:    maximum order_id in the workbook

Usage: python compose_output_filename.py <wb_path> [--output-dir <dir>]
Prints the full output path.
Also renames/moves the workbook to the composed filename in --output-dir (default: same dir as input).
\"\"\"
import sys, os, shutil
from pathlib import Path
from datetime import datetime
import openpyxl

try:
    from zoneinfo import ZoneInfo
    now = datetime.now(ZoneInfo("Asia/Seoul"))
except Exception:
    now = datetime.utcnow()

wb_path = Path(sys.argv[1])
out_dir = Path(sys.argv[sys.argv.index("--output-dir") + 1]) if "--output-dir" in sys.argv else wb_path.parent

wb = openpyxl.load_workbook(str(wb_path))
ws = wb.active
order_ids = []
for row in ws.iter_rows(min_row=2, values_only=True):
    try:
        order_ids.append(int(str(row[0]).strip()))
    except Exception:
        pass

if not order_ids:
    print("ERROR: no order ids found", file=sys.stderr)
    sys.exit(1)

start = min(order_ids)
end   = max(order_ids)
yymmdd = now.strftime("%y%m%d")
filename = f"tmazonORDERLIST{yymmdd}_{start}-{end}.xlsx"
out_path = out_dir / filename
shutil.move(str(wb_path), str(out_path))
print(str(out_path))
""", encoding="utf-8")

# --- update_state.py ---
(WS / "scripts/update_state.py").write_text(r"""#!/usr/bin/env python3
\"\"\"
Update the automation state after a successful run.

Writes/updates: ~/.openclaw/workspace/buyma_order/state/last_run.json

Usage: python update_state.py --last-order <int> --mode <daily|adhoc> --output-file <path>
\"\"\"
import sys, json, os
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(os.environ.get("WORKSPACE", str(Path(__file__).parent.parent)))
STATE_FILE = WORKSPACE / ".openclaw/workspace/buyma_order/state/last_run.json"

def get_arg(flag):
    if flag in sys.argv:
        return sys.argv[sys.argv.index(flag) + 1]
    return None

state = {
    "last_order":   int(get_arg("--last-order") or 0),
    "run_date":     datetime.utcnow().strftime("%Y-%m-%d"),
    "mode":         get_arg("--mode") or "unknown",
    "output_file":  get_arg("--output-file") or "",
}
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
print(f"State updated: {STATE_FILE}")
""", encoding="utf-8")

print("Workspace setup complete.")
print(f"  incoming wb : {incoming_wb_path}")
print(f"  current  wb : {current_wb_path}")
print(f"  csv path    : {csv_path}")
print(f"  template    : {template_path}")