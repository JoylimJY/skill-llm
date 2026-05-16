import os
import json
import random

random.seed(42)

BASE = "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "references",
    "data/raw/2023",
    "data/raw/2024",
    "data/processed",
    "reports/drafts",
    "reports/final",
    "config",
    "logs",
    "archive/old_scripts",
    "archive/legacy_refs",
    "tmp",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# ── references/issuers.json (the proprietary alias map) ─────────────────────
issuers = {
    "issuers": [
        {
            "name": "Tencent Holdings Limited",
            "aliases": ["Tencent", "TCEHY", "0700.HK"],
            "ir_domain": "www.tencent.com/en-us/investors",
            "cik": None,
            "validated": False
        },
        {
            "name": "Alibaba Group Holding Limited",
            "aliases": ["Alibaba", "BABA", "9988.HK"],
            "ir_domain": "ir.alibabagroup.com",
            "cik": "0001577552",
            "validated": True
        },
        {
            "name": "JD.com Inc.",
            "aliases": ["JD", "JD.com", "9618.HK"],
            "ir_domain": "ir.jd.com",
            "cik": "0001549802",
            "validated": True
        },
        {
            "name": "Baidu Inc.",
            "aliases": ["Baidu", "BIDU"],
            "ir_domain": "ir.baidu.com",
            "cik": "0001326380",
            "validated": True
        },
        {
            "name": "NetEase Inc.",
            "aliases": ["NetEase", "NTES"],
            "ir_domain": "ir.netease.com",
            "cik": "0001108320",
            "validated": True
        }
    ]
}
with open(os.path.join(BASE, "references/issuers.json"), "w") as f:
    json.dump(issuers, f, indent=2)

# ── scripts/find_ir_pdf.py  (mock – deterministic behavior) ─────────────────
find_ir_pdf_src = r'''#!/usr/bin/env python3
"""Mock find_ir_pdf.py – deterministic for sandbox evaluation."""
import argparse, sys, json, os

ISSUER_MAP = os.path.join(os.path.dirname(__file__), "..", "references", "issuers.json")

# Deterministic URL table keyed by (resolved_domain, source_mode)
MOCK_RESULTS = {
    # company alias -> domain lookup -> PDF URL
    ("www.tencent.com/en-us/investors", "default"): (
        "https://www.tencent.com/en-us/investors/static-files/AR2023_Tencent.pdf"
    ),
    ("ir.alibabagroup.com", "default"): (
        "https://ir.alibabagroup.com/static-files/BABA_Annual_Report_FY2024.pdf"
    ),
    ("ir.jd.com", "default"): (
        "https://ir.jd.com/static-files/JD_AnnualReport_2023.pdf"
    ),
    ("ir.baidu.com", "default"): (
        "https://ir.baidu.com/static-files/Baidu_AR_2024.pdf"
    ),
    ("ir.baidu.com", "wayback"): (
        "https://web.archive.org/web/20240315120000*/https://ir.baidu.com/static-files/Baidu_AR_2024.pdf"
    ),
    ("ir.netease.com", "default"): (
        "https://ir.netease.com/static-files/NTES_Annual_2023.pdf"
    ),
    ("ir.netease.com", "wayback"): (
        "https://web.archive.org/web/20240601090000*/https://ir.netease.com/static-files/NTES_AR_2023.pdf"
    ),
}

def resolve_domain(company_alias):
    try:
        with open(ISSUER_MAP) as f:
            data = json.load(f)
        for issuer in data["issuers"]:
            if company_alias in issuer.get("aliases", []) or company_alias == issuer["name"]:
                return issuer["ir_domain"]
    except Exception as e:
        print(f"[find_ir_pdf] ERROR reading issuers.json: {e}", file=sys.stderr)
    return None

def main():
    parser = argparse.ArgumentParser(description="Find IR PDF URLs")
    parser.add_argument("--domain", default=None, help="IR domain to probe")
    parser.add_argument("--company", default=None, help="Company alias (resolved via issuers.json)")
    parser.add_argument("--year", default=None, help="Target year")
    parser.add_argument("--sources", default="default", help="Source mode: default | wayback | all")
    args = parser.parse_args()

    domain = args.domain
    if args.company and not domain:
        domain = resolve_domain(args.company)
        if not domain:
            print(f"[find_ir_pdf] ERROR: Company alias '{args.company}' not found in issuers.json", file=sys.stderr)
            sys.exit(1)
        print(f"[find_ir_pdf] Resolved '{args.company}' -> domain: {domain}")

    if not domain:
        print("[find_ir_pdf] ERROR: Provide --domain or --company", file=sys.stderr)
        sys.exit(1)

    source_mode = "wayback" if args.sources == "wayback" else "default"
    key = (domain, source_mode)
    url = MOCK_RESULTS.get(key)

    if url:
        print(f"[find_ir_pdf] Discovered PDF URL: {url}")
    else:
        print(f"[find_ir_pdf] WARNING: No PDF found for domain='{domain}' sources='{args.sources}'", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
'''
with open(os.path.join(BASE, "scripts/find_ir_pdf.py"), "w") as f:
    f.write(find_ir_pdf_src)

# ── scripts/download_ir_pdf.py (mock – writes deterministic fake PDF) ────────
download_ir_pdf_src = r'''#!/usr/bin/env python3
"""Mock download_ir_pdf.py – writes a deterministic fake PDF for sandbox evaluation."""
import sys, os, re, hashlib

# Minimal valid PDF header so file-type checks pass
PDF_HEADER = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"

CONTENT_MAP = {
    "AR2023_Tencent.pdf":        b"TENCENT-ANNUAL-REPORT-2023-MOCK",
    "BABA_Annual_Report_FY2024.pdf": b"ALIBABA-ANNUAL-REPORT-FY2024-MOCK",
    "JD_AnnualReport_2023.pdf":  b"JDCOM-ANNUAL-REPORT-2023-MOCK",
    "Baidu_AR_2024.pdf":         b"BAIDU-ANNUAL-REPORT-2024-MOCK",
    "NTES_Annual_2023.pdf":      b"NETEASE-ANNUAL-REPORT-2023-MOCK",
    "NTES_AR_2023.pdf":          b"NETEASE-ANNUAL-REPORT-2023-MOCK",
}

def extract_filename(url):
    # Strip Wayback wrapper if present
    clean = re.sub(r"https://web\.archive\.org/web/[^/]+\*/", "", url)
    return clean.rstrip("/").split("/")[-1]

def main():
    if len(sys.argv) < 2:
        print("Usage: download_ir_pdf.py <url> [output_path]", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    filename = extract_filename(url)
    output_path = sys.argv[2] if len(sys.argv) >= 3 else filename

    content = CONTENT_MAP.get(filename, b"UNKNOWN-PDF-MOCK-CONTENT")
    payload = PDF_HEADER + content + b"\n%%EOF\n"

    with open(output_path, "wb") as f:
        f.write(payload)

    print(f"[download_ir_pdf] Saved: {output_path} ({len(payload)} bytes)")

if __name__ == "__main__":
    main()
'''
with open(os.path.join(BASE, "scripts/download_ir_pdf.py"), "w") as f:
    f.write(download_ir_pdf_src)

# ── Distractor files ─────────────────────────────────────────────────────────

# 1. Old quarterly data CSV
with open(os.path.join(BASE, "data/raw/2023/tencent_q3_revenue.csv"), "w") as f:
    f.write("quarter,revenue_cny_bn,yoy_growth\nQ1,150.0,11%\nQ2,149.2,10%\nQ3,154.6,10%\n")

# 2. Stale issuer map in archive (wrong format, old)
stale_issuers = {"companies": [{"ticker": "BABA", "url": "http://old.alibaba.ir/ar2019.pdf"}]}
with open(os.path.join(BASE, "archive/legacy_refs/issuers_v1.json"), "w") as f:
    json.dump(stale_issuers, f, indent=2)

# 3. Config with irrelevant DB settings
with open(os.path.join(BASE, "config/db_config.yaml"), "w") as f:
    f.write("host: localhost\nport: 5432\ndbname: irdata\nuser: analyst\n")

# 4. A fake old annual report PDF (wrong content, different company)
with open(os.path.join(BASE, "data/processed/BABA_AR_2021_old.pdf"), "wb") as f:
    f.write(b"%PDF-1.3\nOLD-ALIBABA-REPORT-2021\n%%EOF\n")

# 5. A draft report in reports/drafts
with open(os.path.join(BASE, "reports/drafts/analysis_draft.txt"), "w") as f:
    f.write("Draft: Tencent 2023 performance review.\nRevenue growth strong in gaming segment.\nTODO: Attach official AR PDF.\n")

# 6. Legacy download script in archive (wrong approach)
with open(os.path.join(BASE, "archive/old_scripts/wget_pdfs.sh"), "w") as f:
    f.write("#!/bin/bash\n# DEPRECATED – use the new python scripts instead\nwget https://old-ir-site.com/pdfs/ar2019.pdf\n")

# 7. Random log from a previous run
with open(os.path.join(BASE, "logs/run_20231101.log"), "w") as f:
    f.write("[2023-11-01 09:12:33] find_ir_pdf --domain ir.jd.com\n[2023-11-01 09:12:35] Discovered: https://ir.jd.com/static-files/JD_AnnualReport_2022.pdf\n")

# 8. Metadata JSON that looks like it might help but doesn't
with open(os.path.join(BASE, "data/raw/2024/meta.json"), "w") as f:
    json.dump({"source": "manual_collection", "analyst": "jane.doe", "status": "incomplete"}, f)

# 9. Processed financial summary (distractor)
with open(os.path.join(BASE, "data/processed/netease_income_statement.csv"), "w") as f:
    f.write("year,net_income_usd_mn\n2021,3200\n2022,2900\n2023,3100\n")

# 10. requirements.txt in root (distractor)
with open(os.path.join(BASE, "requirements.txt"), "w") as f:
    f.write("requests>=2.28\npandas>=1.5\nopenpyxl>=3.0\n")

# 11. A partial HTML file pretending to be IR page (distractor)
with open(os.path.join(BASE, "tmp/tencent_ir_page_snapshot.html"), "w") as f:
    f.write("<html><body><h1>Investor Relations</h1><p>Annual Report 2023 available for download.</p></body></html>\n")

# 12. An empty placeholder in reports/final
with open(os.path.join(BASE, "reports/final/.gitkeep"), "w") as f:
    f.write("")

print("Workspace generated successfully.")