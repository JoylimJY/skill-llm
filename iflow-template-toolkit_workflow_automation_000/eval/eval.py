#!/usr/bin/env python3
import sys
import json
import re
from pathlib import Path

workspace = Path(sys.argv[1])

checks = []

def check(name, passed, detail=""):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})
    return bool(passed)


def read_report(filename):
    candidates = list(workspace.rglob(filename))
    if not candidates:
        return None
    return candidates[0].read_text(encoding="utf-8")


# ── Load reports ─────────────────────────────────────────────────────────────
en_text = read_report("shipment_report_en.md")
zh_text = read_report("shipment_report_zh.md")

check("en_report_exists", en_text is not None,
      "shipment_report_en.md not found" if en_text is None else "found")
check("zh_report_exists", zh_text is not None,
      "shipment_report_zh.md not found" if zh_text is None else "found")

if en_text is None:
    en_text = ""
if zh_text is None:
    zh_text = ""

# ── EN: header ───────────────────────────────────────────────────────────────
check("en_header",
      "Shipment Status Report" in en_text,
      f"Expected 'Shipment Status Report' in EN report. Got snippet: {en_text[:200]!r}")

# ── ZH: header ───────────────────────────────────────────────────────────────
check("zh_header",
      "货物状态报告" in zh_text,
      f"Expected '货物状态报告' in ZH report. Got snippet: {zh_text[:200]!r}")

# ── EN: footer with operator interpolation ───────────────────────────────────
check("en_footer_interpolated",
      "Prepared by: Alex" in en_text,
      f"Expected 'Prepared by: Alex' in EN footer. Got: {en_text[-300:]!r}")

# ── ZH: footer with operator interpolation ───────────────────────────────────
check("zh_footer_interpolated",
      "由Alex编制" in zh_text,
      f"Expected '由Alex编制' in ZH footer. Got: {zh_text[-300:]!r}")

# ── Shipment numbering (1-based index1) ──────────────────────────────────────
for i in range(1, 6):
    present_en = f"[{i}]" in en_text
    present_zh = f"[{i}]" in zh_text
    check(f"en_numbering_{i}", present_en, f"Expected '[{i}]' in EN report")
    check(f"zh_numbering_{i}", present_zh, f"Expected '[{i}]' in ZH report")

# ── Verify no [0] index (would mean index not index1) ────────────────────────
check("no_zero_index_en", "[0]" not in en_text,
      "Found '[0]' in EN report — agent used `index` instead of `index1`")
check("no_zero_index_zh", "[0]" not in zh_text,
      "Found '[0]' in ZH report — agent used `index` instead of `index1`")

# ── BEGIN/END markers (first/last loop variables) ────────────────────────────
check("en_begin_marker", "--- BEGIN SHIPMENT LIST ---" in en_text,
      "Missing BEGIN marker in EN report")
check("en_end_marker",   "--- END SHIPMENT LIST ---"   in en_text,
      "Missing END marker in EN report")
check("zh_begin_marker", "--- BEGIN SHIPMENT LIST ---" in zh_text,
      "Missing BEGIN marker in ZH report")
check("zh_end_marker",   "--- END SHIPMENT LIST ---"   in zh_text,
      "Missing END marker in ZH report")

# ── BEGIN appears before END (correct ordering) ───────────────────────────────
try:
    begin_pos = en_text.index("--- BEGIN SHIPMENT LIST ---")
    end_pos   = en_text.index("--- END SHIPMENT LIST ---")
    check("en_begin_before_end", begin_pos < end_pos,
          f"BEGIN at {begin_pos}, END at {end_pos}")
except ValueError as e:
    check("en_begin_before_end", False, str(e))

# ── Status labels (elif / else branches) ─────────────────────────────────────
for report_name, text in [("en", en_text), ("zh", zh_text)]:
    check(f"{report_name}_status_active",
          "IN TRANSIT" in text,
          f"Expected 'IN TRANSIT' for active shipments in {report_name}")
    check(f"{report_name}_status_pending",
          "AWAITING DISPATCH" in text,
          f"Expected 'AWAITING DISPATCH' for pending shipments in {report_name}")
    check(f"{report_name}_status_cancelled",
          "ORDER CANCELLED" in text,
          f"Expected 'ORDER CANCELLED' for cancelled shipments in {report_name}")

# ── Tracking IDs present ──────────────────────────────────────────────────────
tracking_ids = ["SHP-1001", "SHP-1002", "SHP-1003", "SHP-1004", "SHP-1005"]
for tid in tracking_ids:
    check(f"en_tracking_{tid}", tid in en_text,
          f"Tracking ID {tid} not in EN report")
    check(f"zh_tracking_{tid}", tid in zh_text,
          f"Tracking ID {tid} not in ZH report")

# ── Operator and Region appear ────────────────────────────────────────────────
check("en_operator", "Alex" in en_text, "Operator 'Alex' missing from EN report")
check("en_region",   "APAC-EMEA-NA" in en_text, "Region missing from EN report")

# ── Scoring ───────────────────────────────────────────────────────────────────
total  = len(checks)
passed = sum(1 for c in checks if c["passed"])
score  = round(passed / total, 4) if total > 0 else 0.0
all_pass = (passed == total)

result = {
    "passed": all_pass,
    "score": score,
    "checks": checks
}
print(json.dumps(result, ensure_ascii=False, indent=2))