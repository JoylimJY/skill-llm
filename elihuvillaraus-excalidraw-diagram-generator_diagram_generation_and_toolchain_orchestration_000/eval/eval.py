import sys
import json
import os
from pathlib import Path

workspace = sys.argv[1]

checks = []
score = 0.0

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

# ── 1. Find the output file ───────────────────────────────────────────────────
# Agent must produce checkout-sequence.excalidraw (or .excalidraw.edit chain resolved)
target_name = "checkout-sequence.excalidraw"
candidates = list(Path(workspace).rglob(target_name))
# Also accept .edit variant that was never finalized
edit_candidates = list(Path(workspace).rglob(target_name + ".edit"))

final_path = None
if candidates:
    final_path = candidates[0]
elif edit_candidates:
    final_path = edit_candidates[0]

file_found = final_path is not None
add_check("file_exists", file_found,
          f"Found at {final_path}" if file_found else f"No file named '{target_name}' (or .edit) found in workspace")

if not file_found:
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# ── 2. Parse JSON ─────────────────────────────────────────────────────────────
try:
    with open(final_path) as f:
        diagram = json.load(f)
    add_check("valid_json", True, "File is valid JSON")
except Exception as e:
    add_check("valid_json", False, f"JSON parse error: {e}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

elements = diagram.get("elements", [])

# ── 3. Top-level schema ───────────────────────────────────────────────────────
schema_ok = (
    diagram.get("type") == "excalidraw" and
    diagram.get("version") == 2 and
    isinstance(diagram.get("appState"), dict) and
    diagram["appState"].get("gridSize") == 20
)
add_check("schema_correct",
          schema_ok,
          f"type={diagram.get('type')}, version={diagram.get('version')}, gridSize={diagram.get('appState',{}).get('gridSize')}")

# ── 4. Minimum element count (sequence diagram needs actors + lifelines + messages) ──
min_elements = 8
elem_count = len(elements)
add_check("sufficient_elements",
          elem_count >= min_elements,
          f"Found {elem_count} elements (need >= {min_elements})")

# ── 5. fontFamily: 5 on ALL text elements (key proprietary trap) ──────────────
text_elements = [e for e in elements if e.get("type") == "text"]
wrong_font = [e for e in text_elements if e.get("fontFamily") != 5]
font_ok = len(text_elements) > 0 and len(wrong_font) == 0
add_check("all_text_fontFamily_5",
          font_ok,
          f"{len(text_elements)} text elements found; {len(wrong_font)} have wrong fontFamily. "
          + (f"Bad IDs: {[e.get('id','?') for e in wrong_font[:3]]}" if wrong_font else "All correct."))

# ── 6. Unique IDs ─────────────────────────────────────────────────────────────
ids = [e.get("id") for e in elements if e.get("id")]
unique_ids = len(ids) == len(set(ids)) and len(ids) > 0
add_check("unique_element_ids",
          unique_ids,
          f"{len(ids)} IDs total, {len(set(ids))} unique")

# ── 7. Has arrows (required for sequence diagram messages) ────────────────────
arrows = [e for e in elements if e.get("type") == "arrow"]
has_arrows = len(arrows) >= 3
add_check("has_arrows",
          has_arrows,
          f"Found {len(arrows)} arrows (need >= 3 for sequence messages)")

# ── 8. Has at least one dashed arrow (return/async messages in sequence diagram) ──
dashed_arrows = [e for e in arrows if e.get("strokeStyle") == "dashed"]
has_dashed = len(dashed_arrows) >= 1
add_check("has_dashed_arrow",
          has_dashed,
          f"Found {len(dashed_arrows)} dashed arrows (need >= 1 for return/async messages)")

# ── 9. Four key actors present as text (Client, API Gateway, Payment Processor, Database) ──
all_text = " ".join(
    (e.get("text") or e.get("label") or "") for e in elements
).lower()
actors = {
    "client": "client" in all_text,
    "api gateway": "api gateway" in all_text or "apigateway" in all_text or "api_gateway" in all_text,
    "payment processor": "payment processor" in all_text or "payment_processor" in all_text or "paymentprocessor" in all_text,
    "database": "database" in all_text or "db" in all_text,
}
actors_found = sum(actors.values())
actors_ok = actors_found >= 3
add_check("actors_present",
          actors_ok,
          f"Actors found: {actors} ({actors_found}/4 required >= 3)")

# ── 10. Icon from payment-icons library was embedded ─────────────────────────
# Agent must have used add-icon-to-diagram.py with --library-path or auto-detect
# We look for presence of icon-shaped rectangles with known colors from our icon lib
icon_colors = {"#a5d8ff", "#ffd43b", "#b2f2bb", "#ffc9c9", "#d0bfff"}
icon_rects = [
    e for e in elements
    if e.get("type") == "rectangle" and e.get("backgroundColor") in icon_colors
]
has_icon = len(icon_rects) >= 1
add_check("payment_icon_embedded",
          has_icon,
          f"Found {len(icon_rects)} icon rectangle(s) with payment-icons library colors. "
          "Expected >= 1 icon from payment-icons library.")

# ── 11. No overlapping elements (basic layout sanity) ────────────────────────
def get_bbox(e):
    x = e.get("x", 0)
    y = e.get("y", 0)
    w = e.get("width", 0)
    h = e.get("height", 0)
    return x, y, x + w, y + h

def overlaps(a, b):
    ax1, ay1, ax2, ay2 = get_bbox(a)
    bx1, by1, bx2, by2 = get_bbox(b)
    # only check sizeable elements
    if (ax2 - ax1) < 10 or (bx2 - bx1) < 10:
        return False
    return ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1

boxes = [e for e in elements if e.get("type") in ("rectangle", "ellipse", "diamond") and e.get("width", 0) > 20]
overlap_count = 0
for i in range(len(boxes)):
    for j in range(i + 1, len(boxes)):
        if overlaps(boxes[i], boxes[j]):
            overlap_count += 1

no_overlap = overlap_count == 0
add_check("no_element_overlap",
          no_overlap,
          f"{overlap_count} overlapping shape pairs detected (should be 0)")

# ── 12. Arrow with label added via add-arrow.py (dashed + label from script) ──
labeled_arrows_or_texts = [
    e for e in elements
    if (e.get("type") == "arrow" and e.get("strokeStyle") == "dashed")
    or (e.get("type") == "text" and any(
        kw in (e.get("text") or "").lower()
        for kw in ["response", "result", "ack", "return", "ok", "success", "token", "confirm"]
    ))
]
has_labeled_response = len(labeled_arrows_or_texts) >= 1
add_check("dashed_response_arrow_with_label",
          has_labeled_response,
          f"Found {len(labeled_arrows_or_texts)} dashed arrows or response-labeled texts")

# ── Scoring ───────────────────────────────────────────────────────────────────
weights = {
    "file_exists": 2,
    "valid_json": 2,
    "schema_correct": 2,
    "sufficient_elements": 1,
    "all_text_fontFamily_5": 3,   # proprietary trap — high weight
    "unique_element_ids": 1,
    "has_arrows": 1,
    "has_dashed_arrow": 2,
    "actors_present": 2,
    "payment_icon_embedded": 2,
    "no_element_overlap": 1,
    "dashed_response_arrow_with_label": 1,
}
total_weight = sum(weights.values())
earned = sum(weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights)
score = round(earned / total_weight, 3)

# Must pass these critical checks to be "passed"
critical = ["file_exists", "valid_json", "schema_correct", "all_text_fontFamily_5", "actors_present"]
passed = all(c["passed"] for c in checks if c["name"] in critical) and score >= 0.65

print(json.dumps({
    "passed": passed,
    "score": score,
    "checks": checks
}, indent=2))