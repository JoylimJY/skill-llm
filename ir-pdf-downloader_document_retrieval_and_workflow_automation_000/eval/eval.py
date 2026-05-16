import sys
import json
import os
from pathlib import Path

def run_eval(workspace: str):
    checks = []

    # ── Helper ───────────────────────────────────────────────────────────────
    def add(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ═══════════════════════════════════════════════════════════════════════
    # CHECK 1: Tencent annual report PDF exists somewhere in workspace
    # Agent must have used find_ir_pdf.py --company Tencent, then download_ir_pdf.py
    # Expected filename: tencent_annual_report_2023.pdf (task-specified)
    # ═══════════════════════════════════════════════════════════════════════
    TENCENT_FILENAME = "tencent_annual_report_2023.pdf"
    tencent_matches = list(Path(workspace).rglob(TENCENT_FILENAME))

    if not tencent_matches:
        add("tencent_pdf_exists", False, f"File '{TENCENT_FILENAME}' not found anywhere in workspace.")
    else:
        add("tencent_pdf_exists", True, f"Found at: {tencent_matches[0]}")

    # ── CHECK 2: Tencent PDF has correct mock content ─────────────────────
    EXPECTED_TENCENT_CONTENT = b"TENCENT-ANNUAL-REPORT-2023-MOCK"
    if tencent_matches:
        try:
            raw = tencent_matches[0].read_bytes()
            if EXPECTED_TENCENT_CONTENT in raw:
                add("tencent_pdf_content_correct", True,
                    "PDF contains expected Tencent 2023 mock content.")
            else:
                add("tencent_pdf_content_correct", False,
                    f"PDF content mismatch. Got first 120 bytes: {raw[:120]}")
        except Exception as e:
            add("tencent_pdf_content_correct", False, f"Could not read file: {e}")
    else:
        add("tencent_pdf_content_correct", False, "Skipped – file not found.")

    # ── CHECK 3: PDF has valid PDF header ─────────────────────────────────
    if tencent_matches:
        try:
            raw = tencent_matches[0].read_bytes()
            if raw.startswith(b"%PDF-"):
                add("tencent_pdf_valid_header", True, "File starts with %PDF- header.")
            else:
                add("tencent_pdf_valid_header", False, f"Missing PDF header. Starts with: {raw[:8]}")
        except Exception as e:
            add("tencent_pdf_valid_header", False, f"Read error: {e}")
    else:
        add("tencent_pdf_valid_header", False, "Skipped – file not found.")

    # ═══════════════════════════════════════════════════════════════════════
    # CHECK 4: NetEase Wayback-archived PDF URL was discovered
    # Agent must have used find_ir_pdf.py --domain ir.netease.com --sources wayback
    # We check for a file containing the wayback URL, written as netease_wayback_url.txt
    # ═══════════════════════════════════════════════════════════════════════
    NETEASE_URL_FILENAME = "netease_wayback_url.txt"
    EXPECTED_NETEASE_WAYBACK_URL = (
        "https://web.archive.org/web/20240601090000*/"
        "https://ir.netease.com/static-files/NTES_AR_2023.pdf"
    )
    netease_url_matches = list(Path(workspace).rglob(NETEASE_URL_FILENAME))

    if not netease_url_matches:
        add("netease_wayback_url_file_exists", False,
            f"File '{NETEASE_URL_FILENAME}' not found anywhere in workspace.")
    else:
        add("netease_wayback_url_file_exists", True, f"Found at: {netease_url_matches[0]}")

    # ── CHECK 5: File contains the exact Wayback URL ─────────────────────
    if netease_url_matches:
        try:
            content = netease_url_matches[0].read_text(encoding="utf-8", errors="replace")
            if EXPECTED_NETEASE_WAYBACK_URL in content:
                add("netease_wayback_url_correct", True,
                    "File contains the correct Wayback-archived NetEase PDF URL.")
            else:
                add("netease_wayback_url_correct", False,
                    f"Expected URL not found. File content (first 400 chars): {content[:400]}")
        except Exception as e:
            add("netease_wayback_url_correct", False, f"Could not read file: {e}")
    else:
        add("netease_wayback_url_correct", False, "Skipped – file not found.")

    # ═══════════════════════════════════════════════════════════════════════
    # CHECK 6: Agent did NOT accidentally use the stale legacy archive issuer map
    # (It should have used references/issuers.json, not archive/legacy_refs/issuers_v1.json)
    # We detect misuse by checking: if agent wrote Alibaba 2019 URL anywhere
    # ═══════════════════════════════════════════════════════════════════════
    STALE_URL = "http://old.alibaba.ir/ar2019.pdf"
    stale_found_in = []
    for fpath in Path(workspace).rglob("*"):
        if fpath.is_file() and fpath.suffix in (".txt", ".json", ".log", ".pdf", ".csv"):
            try:
                content = fpath.read_text(encoding="utf-8", errors="replace")
                if STALE_URL in content:
                    stale_found_in.append(str(fpath))
            except Exception:
                pass
    if stale_found_in:
        add("no_stale_legacy_url_used", False,
            f"Stale legacy URL found in output files: {stale_found_in}")
    else:
        add("no_stale_legacy_url_used", True,
            "No stale legacy issuer URL detected in agent outputs.")

    # ── Final scoring ─────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    all_passed = passed_count == total

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace)