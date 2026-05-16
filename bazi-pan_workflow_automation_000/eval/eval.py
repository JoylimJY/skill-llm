#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evaluation script for bazi_reports.json
Usage: python3 eval.py <workspace_dir>
"""
import sys
import json
import subprocess
import os
import re
from pathlib import Path

def run_bazi(workspace, year, month, day, time_str):
    script = os.path.join(workspace, "skills/bazi-pan/bazi.py")
    result = subprocess.run(
        ["python3", script, str(year), str(month), str(day), time_str],
        capture_output=True, text=True, encoding="utf-8"
    )
    return result.stdout

def parse_reference(output):
    """Parse the reference bazi.py output into structured fields."""
    ref = {}
    # 年柱/月柱/日柱/时柱
    m = re.search(r"年柱：([^\s（]+)", output)
    if m: ref["年柱"] = m.group(1)
    m = re.search(r"月柱：([^\s（]+)", output)
    if m: ref["月柱"] = m.group(1)
    m = re.search(r"日柱：([^\s（]+)", output)
    if m: ref["日柱"] = m.group(1)
    m = re.search(r"时柱：([^\s（]+)", output)
    if m: ref["时柱"] = m.group(1)
    # 五行
    wx = {}
    for elem in ["金","木","水","火","土"]:
        m = re.search(elem + r"：(\d+)", output)
        if m: wx[elem] = int(m.group(1))
    ref["五行"] = wx
    # 用神/忌神
    m = re.search(r"用神：(.+)", output)
    if m: ref["用神"] = [x.strip() for x in re.split(r"[、，,]", m.group(1).strip()) if x.strip()]
    m = re.search(r"忌神：(.+)", output)
    if m: ref["忌神"] = [x.strip() for x in re.split(r"[、，,]", m.group(1).strip()) if x.strip()]
    # 日主
    m = re.search(r"日主(偏强|偏弱)", output)
    if m: ref["日主强弱"] = m.group(1)
    # 日干
    m = re.search(r"日柱：(.).", output)
    if m: ref["日干"] = m.group(1)
    # 大运前3
    m = re.search(r"岁起运：(.+)", output)
    if m:
        dayuns_raw = m.group(1).strip().split()
        ref["大运前3"] = [d.strip() for d in dayuns_raw[:3] if d.strip()]
    return ref

CLIENTS = [
    {"name": "李明",   "year": 1985, "month": 3,  "day": 12, "time": "08:00"},
    {"name": "张晓红", "year": 1992, "month": 7,  "day": 28, "time": "23:00"},
    {"name": "王建国", "year": 2000, "month": 11, "day": 5,  "time": "15:30"},
]

def evaluate(workspace):
    checks = []
    total_score = 0.0

    # ── Find bazi_reports.json ────────────────────────────────────────────────
    candidates = list(Path(workspace).rglob("bazi_reports.json"))
    if not candidates:
        checks.append({"name": "file_exists", "passed": False,
                        "detail": "bazi_reports.json not found anywhere in workspace"})
        return {"passed": False, "score": 0.0, "checks": checks}

    report_path = candidates[0]
    checks.append({"name": "file_exists", "passed": True,
                    "detail": str(report_path)})

    # ── Load JSON ──────────────────────────────────────────────────────────────
    try:
        with open(report_path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        checks.append({"name": "json_valid", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "json_valid", "passed": True, "detail": "JSON parsed OK"})

    # ── Must be a list or dict with entries for all 3 clients ─────────────────
    if isinstance(data, dict):
        # allow {"clients": [...]} or {"reports": [...]}
        entries = None
        for key in ("clients", "reports", "data", "results"):
            if key in data and isinstance(data[key], list):
                entries = data[key]
                break
        if entries is None:
            # try values
            for v in data.values():
                if isinstance(v, list):
                    entries = v
                    break
        if entries is None:
            checks.append({"name": "has_3_entries", "passed": False,
                            "detail": "Cannot find list of client entries in JSON"})
            return {"passed": False, "score": 0.0, "checks": checks}
    elif isinstance(data, list):
        entries = data
    else:
        checks.append({"name": "has_3_entries", "passed": False,
                        "detail": f"Top-level JSON type unexpected: {type(data)}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    has_3 = len(entries) >= 3
    checks.append({"name": "has_3_entries", "passed": has_3,
                    "detail": f"Found {len(entries)} entries"})
    if not has_3:
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── Per-client checks ──────────────────────────────────────────────────────
    name_to_entry = {}
    for e in entries:
        if isinstance(e, dict):
            for nk in ("name", "姓名", "client_name", "客户"):
                if nk in e:
                    name_to_entry[e[nk]] = e
                    break

    per_client_score = 0.0
    for client in CLIENTS:
        cname = client["name"]
        ref_output = run_bazi(workspace, client["year"], client["month"],
                               client["day"], client["time"])
        ref = parse_reference(ref_output)

        entry = name_to_entry.get(cname)
        if entry is None:
            # Try partial name match
            for k, v in name_to_entry.items():
                if cname in k or k in cname:
                    entry = v
                    break

        if entry is None:
            checks.append({"name": f"{cname}_found", "passed": False,
                            "detail": f"No entry for {cname} in JSON"})
            continue

        checks.append({"name": f"{cname}_found", "passed": True, "detail": "Entry located"})

        # Helper: flatten all string values in entry for loose search
        flat_text = json.dumps(entry, ensure_ascii=False)

        # Check 1: Four pillars present ────────────────────────────────────────
        pillars_ok = True
        missing_pillars = []
        for pillar_key in ["年柱", "月柱", "日柱", "时柱"]:
            expected_val = ref.get(pillar_key, "")
            # Search in the entry dict recursively
            found = expected_val in flat_text if expected_val else False
            if not found:
                pillars_ok = False
                missing_pillars.append(f"{pillar_key}={expected_val}")

        checks.append({"name": f"{cname}_pillars",
                        "passed": pillars_ok,
                        "detail": f"Missing: {missing_pillars}" if not pillars_ok else "All 4 pillars correct"})
        if pillars_ok:
            per_client_score += 1.0

        # Check 2: 五行分布 ───────────────────────────────────────────────────
        wx_ok = True
        wx_issues = []
        ref_wx = ref.get("五行", {})
        for elem, count in ref_wx.items():
            pattern = elem + r".*?" + str(count) + r"|" + str(count) + r".*?" + elem
            if str(count) not in flat_text:
                # check if the number appears anywhere near element
                wx_ok = False
                wx_issues.append(f"{elem}:{count}")

        checks.append({"name": f"{cname}_wuxing",
                        "passed": wx_ok,
                        "detail": f"Issues: {wx_issues}" if not wx_ok else "五行分布 counts match"})
        if wx_ok:
            per_client_score += 1.0

        # Check 3: 用神/忌神 ──────────────────────────────────────────────────
        yong_ok = all(y in flat_text for y in ref.get("用神", []))
        ji_ok   = all(j in flat_text for j in ref.get("忌神", []))
        yj_ok = yong_ok and ji_ok
        checks.append({"name": f"{cname}_yongshen",
                        "passed": yj_ok,
                        "detail": (f"用神={ref.get('用神')}, in_text={yong_ok}; "
                                   f"忌神={ref.get('忌神')}, in_text={ji_ok}")})
        if yj_ok:
            per_client_score += 1.0

        # Check 4: 日主强弱 ───────────────────────────────────────────────────
        rizhu_str = ref.get("日主强弱", "")
        rizhu_ok = bool(rizhu_str) and rizhu_str in flat_text
        checks.append({"name": f"{cname}_rizhu_strength",
                        "passed": rizhu_ok,
                        "detail": f"Expected '{rizhu_str}' in entry"})
        if rizhu_ok:
            per_client_score += 0.5

        # Check 5: 大运前3 ─────────────────────────────────────────────────────
        dayun3 = ref.get("大运前3", [])
        dayun_ok = len(dayun3) >= 3 and all(d in flat_text for d in dayun3[:3])
        checks.append({"name": f"{cname}_dayun",
                        "passed": dayun_ok,
                        "detail": f"Expected first 3 dayun: {dayun3[:3]}"})
        if dayun_ok:
            per_client_score += 0.5

    # ── Final score ────────────────────────────────────────────────────────────
    max_score = 3 * (1.0 + 1.0 + 1.0 + 0.5 + 0.5)  # = 12.0
    normalized = per_client_score / max_score if max_score > 0 else 0.0

    all_passed = normalized >= 0.75 and has_3
    return {
        "passed": all_passed,
        "score": round(normalized, 4),
        "checks": checks
    }

if __name__ == "__main__":
    ws = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(ws)
    print(json.dumps(result, ensure_ascii=False, indent=2))