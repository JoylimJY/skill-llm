#!/usr/bin/env python3
"""
Sets up a realistic sandbox for the security-audit skill evaluation.
Creates a mock openclaw skill stack and the audit.py script that the
agent must invoke with correct flags and subcommands.
"""

import os
import json
import stat
import random
import hashlib
import textwrap
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")
HOME = Path("/root")
OPENCLAW_DIR = HOME / ".openclaw" / "skills"
BASE_DIR = WORKSPACE / "openclaw-security-audit"
SCRIPTS_DIR = BASE_DIR / "scripts"

# ── Create directory skeleton ────────────────────────────────────────────────
for d in [WORKSPACE, OPENCLAW_DIR, SCRIPTS_DIR,
          WORKSPACE / "logs", WORKSPACE / "tmp", WORKSPACE / "reports"]:
    d.mkdir(parents=True, exist_ok=True)

# ── Fake skills to populate the fleet ───────────────────────────────────────
SKILLS_META = [
    {
        "name": "quant-engine",
        "description": "High-frequency trading signal processor",
        "has_binary": True,
        "binary_name": "hft_engine",
        "binary_sha256": "aabbccdd" * 8,
        "trust_score": 42,
        "findings": [
            {"severity": "critical", "code": "EXEC-001",
             "message": "Unverified binary 'hft_engine' detected – no checksum record found"},
            {"severity": "high",     "code": "PROV-007",
             "message": "Provenance chain incomplete: missing upstream signature"},
        ],
        "overall_risk": "critical",
        "passes_all_checks": False,
    },
    {
        "name": "market-data-fetcher",
        "description": "Real-time price feed aggregator",
        "has_binary": False,
        "binary_name": None,
        "binary_sha256": None,
        "trust_score": 87,
        "findings": [
            {"severity": "low", "code": "NET-003",
             "message": "Outbound connection to unregistered endpoint detected"},
        ],
        "overall_risk": "low",
        "passes_all_checks": True,
    },
    {
        "name": "risk-calculator",
        "description": "Portfolio VaR and stress-test engine",
        "has_binary": False,
        "binary_name": None,
        "binary_sha256": None,
        "trust_score": 91,
        "findings": [],
        "overall_risk": "none",
        "passes_all_checks": True,
    },
    {
        "name": "compliance-reporter",
        "description": "Regulatory report generator (MiFID II)",
        "has_binary": True,
        "binary_name": "report_gen",
        "binary_sha256": "deadbeef" * 8,
        "trust_score": 55,
        "findings": [
            {"severity": "high",   "code": "EXEC-002",
             "message": "Binary 'report_gen' SHA-256 mismatch – possible tampering"},
            {"severity": "medium", "code": "CODE-011",
             "message": "Hardcoded credential pattern found in scripts/fetch.py"},
        ],
        "overall_risk": "high",
        "passes_all_checks": False,
    },
    {
        "name": "order-router",
        "description": "Smart order routing across dark pools",
        "has_binary": False,
        "binary_name": None,
        "binary_sha256": None,
        "trust_score": 78,
        "findings": [
            {"severity": "medium", "code": "PROV-003",
             "message": "Skill installed from unverified registry mirror"},
        ],
        "overall_risk": "medium",
        "passes_all_checks": False,
    },
]

# ── Populate skill directories ───────────────────────────────────────────────
for skill in SKILLS_META:
    skill_dir = OPENCLAW_DIR / skill["name"]
    scripts_subdir = skill_dir / "scripts"
    scripts_subdir.mkdir(parents=True, exist_ok=True)

    # SKILL.md
    (skill_dir / "SKILL.md").write_text(textwrap.dedent(f"""\
        ---
        name: {skill['name']}
        description: {skill['description']}
        ---
        # {skill['name']}
        {skill['description']}
    """))

    # Fake binary if applicable
    if skill["has_binary"]:
        bin_path = skill_dir / skill["binary_name"]
        bin_path.write_bytes(bytes(random.getrandbits(8) for _ in range(256)))
        bin_path.chmod(bin_path.stat().st_mode | stat.S_IEXEC)

    # Distractor files
    (skill_dir / "config.yaml").write_text(f"name: {skill['name']}\nversion: 1.0.0\n")
    (skill_dir / "requirements.txt").write_text("requests>=2.28\npydantic>=1.10\n")
    (scripts_subdir / "main.py").write_text(
        f"# {skill['name']} main entry\nprint('running {skill['name']}')\n"
    )
    if skill["name"] == "compliance-reporter":
        # Plant a fake credential pattern as a distractor
        (scripts_subdir / "fetch.py").write_text(
            "API_KEY = 'sk-hardcoded-secret-key-abc123'\n"
            "def fetch(): pass\n"
        )

# ── Distractor files in workspace ────────────────────────────────────────────
(WORKSPACE / "logs" / "install.log").write_text(
    "2024-01-15 10:22:01 INFO  installed quant-engine v2.3.1\n"
    "2024-01-15 10:22:45 INFO  installed market-data-fetcher v1.0.0\n"
    "2024-01-15 10:23:10 WARN  checksum mismatch for compliance-reporter\n"
)
(WORKSPACE / "tmp" / "scratch.txt").write_text("temp workspace – do not modify\n")
(WORKSPACE / "reports" / ".gitkeep").write_text("")
(WORKSPACE / "openclaw-security-audit" / "README_INTERNAL.md").write_text(
    "Internal tooling – see scripts/audit.py for usage.\n"
)

# ── Build the deterministic audit.py mock ────────────────────────────────────
# This is the script the agent must invoke. It implements the exact CLI
# documented in SKILL.md: full / single subcommands, --json, --output, --attest, --path.

SKILLS_META_JSON = json.dumps(SKILLS_META)

AUDIT_PY = r'''#!/usr/bin/env python3
"""
Deterministic mock implementation of the security-audit skill.
Implements the CLI surface documented in SKILL.md.
"""

import argparse
import json
import sys
import os
import hashlib
from pathlib import Path
from datetime import datetime, timezone

HOME = Path(os.path.expanduser("~"))
OPENCLAW_DIR = HOME / ".openclaw" / "skills"

SKILLS_META = ''' + SKILLS_META_JSON + r'''

def _skills_by_name():
    return {s["name"]: s for s in SKILLS_META}

def _build_skill_report(skill_dir: Path, meta: dict, include_attest: bool) -> dict:
    trust_score = meta["trust_score"]
    findings    = meta["findings"]
    overall_risk = meta["overall_risk"]

    critical_actions = []
    if any(f["severity"] == "critical" for f in findings):
        critical_actions.append(f"IMMEDIATE: Remove or quarantine {meta['name']} – critical finding detected")
    if any(f["severity"] == "high" for f in findings):
        critical_actions.append(f"URGENT: Investigate high-severity issues in {meta['name']} within 24h")

    report = {
        "skill": meta["name"],
        "path": str(skill_dir),
        "description": meta["description"],
        "trust_score": trust_score,
        "overall_risk": overall_risk,
        "findings": findings,
        "findings_count": {
            "critical": sum(1 for f in findings if f["severity"] == "critical"),
            "high":     sum(1 for f in findings if f["severity"] == "high"),
            "medium":   sum(1 for f in findings if f["severity"] == "medium"),
            "low":      sum(1 for f in findings if f["severity"] == "low"),
        },
        "critical_actions": critical_actions,
        "recommendations": [
            f"Review finding {f['code']}: {f['message']}" for f in findings
        ],
    }

    if include_attest:
        if meta["passes_all_checks"]:
            payload = json.dumps({"skill": meta["name"], "trust_score": trust_score}, sort_keys=True)
            attestation_hash = hashlib.sha256(payload.encode()).hexdigest()
            report["trust_attestation"] = {
                "status": "ATTESTED",
                "issued_at": "2024-06-01T00:00:00Z",
                "attestation_hash": attestation_hash,
                "note": "Skill passed all security checks",
            }
        else:
            report["trust_attestation"] = {
                "status": "FAILED",
                "issued_at": "2024-06-01T00:00:00Z",
                "attestation_hash": None,
                "note": "Skill did not pass all security checks – attestation denied",
            }

    return report

def cmd_full(args):
    skill_dirs = sorted(OPENCLAW_DIR.iterdir()) if OPENCLAW_DIR.exists() else []
    by_name = _skills_by_name()

    skill_reports = []
    for skill_dir in skill_dirs:
        if not skill_dir.is_dir():
            continue
        name = skill_dir.name
        if name not in by_name:
            continue
        meta = by_name[name]
        report = _build_skill_report(skill_dir, meta, args.attest)
        skill_reports.append(report)

    # Sort by risk priority
    RISK_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "none": 4}
    skill_reports.sort(key=lambda r: RISK_ORDER.get(r["overall_risk"], 99))

    total_findings = sum(len(r["findings"]) for r in skill_reports)
    summary = {
        "total_skills_scanned": len(skill_reports),
        "findings_by_severity": {
            "critical": sum(r["findings_count"]["critical"] for r in skill_reports),
            "high":     sum(r["findings_count"]["high"]     for r in skill_reports),
            "medium":   sum(r["findings_count"]["medium"]   for r in skill_reports),
            "low":      sum(r["findings_count"]["low"]      for r in skill_reports),
        },
        "overall_risk_level": skill_reports[0]["overall_risk"] if skill_reports else "none",
        "total_findings": total_findings,
        "skills_attested": sum(
            1 for r in skill_reports
            if r.get("trust_attestation", {}).get("status") == "ATTESTED"
        ) if args.attest else None,
    }

    output = {
        "audit_type": "full",
        "generated_at": "2024-06-01T00:00:00Z",
        "summary": summary,
        "skill_reports": skill_reports,
    }

    if args.json:
        content = json.dumps(output, indent=2)
        if args.output:
            Path(args.output).write_text(content)
            print(f"Audit report written to {args.output}")
        else:
            print(content)
    else:
        print(f"=== FULL SECURITY AUDIT ===")
        print(f"Skills scanned: {summary['total_skills_scanned']}")
        print(f"Overall risk:   {summary['overall_risk_level'].upper()}")
        print(f"Total findings: {total_findings}")
        for r in skill_reports:
            print(f"\n[{r['overall_risk'].upper()}] {r['skill']} (trust: {r['trust_score']})")
            for f in r["findings"]:
                print(f"  [{f['severity'].upper()}] {f['code']}: {f['message']}")
            for a in r["critical_actions"]:
                print(f"  !! {a}")

def cmd_single(args):
    if not args.path:
        print("ERROR: --path is required for 'single' subcommand", file=sys.stderr)
        sys.exit(1)

    skill_dir = Path(args.path).expanduser().resolve()
    by_name = _skills_by_name()
    name = skill_dir.name

    if name not in by_name:
        print(f"ERROR: Unknown skill '{name}' – not in audit database", file=sys.stderr)
        sys.exit(2)

    meta = by_name[name]
    report = _build_skill_report(skill_dir, meta, args.attest)

    output = {
        "audit_type": "single",
        "generated_at": "2024-06-01T00:00:00Z",
        "summary": {
            "total_skills_scanned": 1,
            "findings_by_severity": report["findings_count"],
            "overall_risk_level": report["overall_risk"],
            "total_findings": len(report["findings"]),
            "skills_attested": None,
        },
        "skill_reports": [report],
    }

    if args.json:
        content = json.dumps(output, indent=2)
        if args.output:
            Path(args.output).write_text(content)
            print(f"Single-skill audit report written to {args.output}")
        else:
            print(content)
    else:
        r = report
        print(f"=== SINGLE SKILL AUDIT: {r['skill']} ===")
        print(f"Path:        {r['path']}")
        print(f"Trust score: {r['trust_score']}")
        print(f"Risk level:  {r['overall_risk'].upper()}")
        for f in r["findings"]:
            print(f"  [{f['severity'].upper()}] {f['code']}: {f['message']}")
        if args.attest:
            att = r.get("trust_attestation", {})
            print(f"Attestation: {att.get('status')} – {att.get('note')}")

def main():
    parser = argparse.ArgumentParser(description="Security audit tool for openclaw skills")
    sub = parser.add_subparsers(dest="command")

    # full subcommand
    p_full = sub.add_parser("full", help="Audit all installed skills")
    p_full.add_argument("--json",   action="store_true", help="Output as JSON")
    p_full.add_argument("--output", type=str,            help="Write output to file")
    p_full.add_argument("--attest", action="store_true", help="Include trust attestations")

    # single subcommand
    p_single = sub.add_parser("single", help="Audit a specific skill")
    p_single.add_argument("--path",   type=str,            help="Path to skill directory")
    p_single.add_argument("--json",   action="store_true", help="Output as JSON")
    p_single.add_argument("--output", type=str,            help="Write output to file")
    p_single.add_argument("--attest", action="store_true", help="Include trust attestations")

    args = parser.parse_args()

    if args.command == "full":
        cmd_full(args)
    elif args.command == "single":
        cmd_single(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
audit_py_path = SCRIPTS_DIR / "audit.py"
audit_py_path.write_text(AUDIT_PY)
audit_py_path.chmod(audit_py_path.stat().st_mode | stat.S_IEXEC)

# ── Write a .env-style config so the agent can resolve {baseDir} ─────────────
(BASE_DIR / ".skillrc").write_text(f"baseDir={BASE_DIR}\n")
(WORKSPACE / "openclaw-security-audit" / "MANIFEST.json").write_text(json.dumps({
    "tool": "security-audit",
    "baseDir": str(BASE_DIR),
    "skills_dir": str(OPENCLAW_DIR),
}, indent=2))

# ── Distractor files ─────────────────────────────────────────────────────────
(WORKSPACE / "tmp" / "old_report.json").write_text(
    '{"note": "stale report from previous run – do not use"}\n'
)
(WORKSPACE / "logs" / "audit_attempt_failed.log").write_text(
    "2024-05-31 09:00:00 ERROR failed to run audit – wrong arguments supplied\n"
)

print("Sandbox setup complete.")
print(f"  baseDir     : {BASE_DIR}")
print(f"  skills dir  : {OPENCLAW_DIR}")
print(f"  audit script: {SCRIPTS_DIR / 'audit.py'}")
print(f"  skills      : {[s['name'] for s in SKILLS_META]}")