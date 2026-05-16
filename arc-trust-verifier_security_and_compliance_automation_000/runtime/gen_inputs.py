#!/usr/bin/env python3
"""
Generate the sandbox workspace for the trust-verifier evaluation task.
Creates:
  - /workspace/openclaw/scripts/trust_verifier.py  (the functional tool)
  - /workspace/skills/payment-processor-skill/      (the skill to audit)
  - Various distractor files throughout the workspace
"""

import os
import json
import hashlib
import random
import stat
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ─────────────────────────────────────────────
# 1.  Create the openclaw base directory + trust_verifier.py
# ─────────────────────────────────────────────

scripts_dir = WORKSPACE / "openclaw" / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

TRUST_VERIFIER_SRC = r'''#!/usr/bin/env python3
"""
trust_verifier.py — ClawHub Trust Verifier
Assess trustworthiness of a ClawHub skill directory.
"""

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

# ── Hardcoded trust registry (simulates ClawHub publisher database) ──────────
KNOWN_PUBLISHERS = {
    "clawhub-official": {"age_days": 1200, "skill_count": 47, "reputation": "high"},
    "fintech-plugins": {"age_days": 340,  "skill_count": 12, "reputation": "medium"},
    "trusted-devops":  {"age_days": 890,  "skill_count": 31, "reputation": "high"},
}

TRUSTED_DEP_SOURCES = {"pypi", "npmjs", "apt"}

SUSPICIOUS_PATTERNS = [
    "eval(", "exec(", "__import__", "subprocess.call",
    "os.system", "base64.b64decode", "socket.connect",
]

def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _collect_hashes(skill_path: Path) -> dict:
    hashes = {}
    for p in sorted(skill_path.rglob("*")):
        if p.is_file():
            rel = str(p.relative_to(skill_path))
            hashes[rel] = _sha256_file(p)
    return hashes

def _load_skill_meta(skill_path: Path) -> dict:
    meta_file = skill_path / "SKILL.md"
    meta = {"publisher": "unknown", "version": "0.0.0", "name": skill_path.name}
    if meta_file.exists():
        for line in meta_file.read_text().splitlines():
            if line.startswith("publisher:"):
                meta["publisher"] = line.split(":", 1)[1].strip()
            if line.startswith("version:"):
                meta["version"] = line.split(":", 1)[1].strip()
            if line.startswith("name:"):
                meta["name"] = line.split(":", 1)[1].strip()
    return meta

def _check_content_suspicious(skill_path: Path) -> list:
    findings = []
    for p in skill_path.rglob("*.py"):
        try:
            text = p.read_text(errors="replace")
            for pattern in SUSPICIOUS_PATTERNS:
                if pattern in text:
                    findings.append({"file": str(p.relative_to(skill_path)), "pattern": pattern})
        except Exception:
            pass
    return findings

def _parse_deps(skill_path: Path) -> list:
    deps = []
    req_file = skill_path / "requirements.txt"
    if req_file.exists():
        for line in req_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                source = line.split(":")[0] if ":" in line else "pypi"
                name   = line.split(":")[1] if ":" in line else line.split("==")[0].split(">=")[0].split("<=")[0]
                deps.append({"name": name.strip(), "source": source.strip(), "raw": line})
    return deps

def cmd_assess(skill_path: Path) -> dict:
    meta       = _load_skill_meta(skill_path)
    publisher  = meta["publisher"]
    pub_info   = KNOWN_PUBLISHERS.get(publisher)
    suspicious = _check_content_suspicious(skill_path)
    hashes     = _collect_hashes(skill_path)

    signals = {
        "publisher_known":    pub_info is not None,
        "publisher_reputed":  pub_info is not None and pub_info["reputation"] == "high",
        "no_suspicious_code": len(suspicious) == 0,
        "has_version":        meta["version"] != "0.0.0",
        "file_count_ok":      len(hashes) >= 3,
    }

    passed = sum(signals.values())
    total  = len(signals)

    if passed == total:
        trust_level = "VERIFIED"
    elif passed >= total - 1:
        trust_level = "TRUSTED"
    elif passed >= total - 2:
        trust_level = "UNKNOWN"
    elif passed >= total - 3:
        trust_level = "SUSPICIOUS"
    else:
        trust_level = "UNTRUSTED"

    result = {
        "command":     "assess",
        "skill":       meta["name"],
        "publisher":   publisher,
        "version":     meta["version"],
        "trust_level": trust_level,
        "signals":     signals,
        "suspicious_findings": suspicious,
        "file_hashes": hashes,
        "assessed_at": int(time.time()),
    }
    print(json.dumps(result, indent=2))
    return result

def cmd_attest(skill_path: Path, output: Path) -> dict:
    assess_result = cmd_assess(skill_path)
    attestation = {
        "schema":      "clawhub-attestation/v1",
        "skill":       assess_result["skill"],
        "publisher":   assess_result["publisher"],
        "version":     assess_result["version"],
        "trust_level": assess_result["trust_level"],
        "signals":     assess_result["signals"],
        "file_hashes": assess_result["file_hashes"],
        "attested_at": assess_result["assessed_at"],
        "attestation_hash": hashlib.sha256(
            json.dumps(assess_result["file_hashes"], sort_keys=True).encode()
        ).hexdigest(),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(attestation, indent=2))
    print(f"Attestation written to {output}")
    return attestation

def cmd_verify(attestation_path: Path, skill_path: Path) -> dict:
    if not attestation_path.exists():
        print(json.dumps({"verified": False, "reason": "Attestation file not found"}))
        return {"verified": False}

    attestation = json.loads(attestation_path.read_text())
    current_hashes = _collect_hashes(skill_path)
    stored_hashes  = attestation.get("file_hashes", {})

    mismatches = []
    for fname, stored_hash in stored_hashes.items():
        current = current_hashes.get(fname)
        if current != stored_hash:
            mismatches.append({"file": fname, "expected": stored_hash, "got": current})

    new_files = [f for f in current_hashes if f not in stored_hashes]

    verified = len(mismatches) == 0 and len(new_files) == 0
    result = {
        "command":    "verify",
        "verified":   verified,
        "skill":      attestation.get("skill"),
        "trust_level": attestation.get("trust_level"),
        "mismatches": mismatches,
        "new_files":  new_files,
        "checked_at": int(time.time()),
    }
    print(json.dumps(result, indent=2))
    return result

def cmd_deps(skill_path: Path) -> dict:
    deps = _parse_deps(skill_path)
    dep_results = []
    all_trusted = True
    for dep in deps:
        trusted = dep["source"] in TRUSTED_DEP_SOURCES
        if not trusted:
            all_trusted = False
        dep_results.append({
            "name":    dep["name"],
            "source":  dep["source"],
            "trusted": trusted,
            "raw":     dep["raw"],
        })

    chain_status = "TRUSTED" if all_trusted else ("SUSPICIOUS" if dep_results else "UNKNOWN")
    result = {
        "command":      "deps",
        "skill":        skill_path.name,
        "dependencies": dep_results,
        "chain_status": chain_status,
        "all_trusted":  all_trusted,
        "dep_count":    len(dep_results),
    }
    print(json.dumps(result, indent=2))
    return result

def main():
    parser = argparse.ArgumentParser(prog="trust_verifier.py")
    sub    = parser.add_subparsers(dest="command")

    p_assess = sub.add_parser("assess")
    p_assess.add_argument("--path", required=True)

    p_attest = sub.add_parser("attest")
    p_attest.add_argument("--path",   required=True)
    p_attest.add_argument("--output", required=True)

    p_verify = sub.add_parser("verify")
    p_verify.add_argument("--attestation", required=True)
    p_verify.add_argument("--path",        required=True)

    p_deps = sub.add_parser("deps")
    p_deps.add_argument("--path", required=True)

    args = parser.parse_args()

    if args.command == "assess":
        cmd_assess(Path(args.path))
    elif args.command == "attest":
        cmd_attest(Path(args.path), Path(args.output))
    elif args.command == "verify":
        cmd_verify(Path(args.attestation), Path(args.path))
    elif args.command == "deps":
        cmd_deps(Path(args.path))
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

(scripts_dir / "trust_verifier.py").write_text(TRUST_VERIFIER_SRC)
os.chmod(scripts_dir / "trust_verifier.py", 0o755)

# ─────────────────────────────────────────────
# 2.  Create the skill under audit
# ─────────────────────────────────────────────

skill_dir = WORKSPACE / "skills" / "payment-processor-skill"
skill_dir.mkdir(parents=True, exist_ok=True)

# SKILL.md — publisher is a known, reputed one
(skill_dir / "SKILL.md").write_text(
    "name: payment-processor\n"
    "publisher: trusted-devops\n"
    "version: 2.3.1\n"
    "description: Processes payment webhooks and reconciles transactions.\n"
    "user-invocable: true\n"
    "metadata: {}\n"
)

# Main script — clean, no suspicious patterns
(skill_dir / "scripts" / "processor.py").parent.mkdir(parents=True, exist_ok=True)
(skill_dir / "scripts" / "processor.py").write_text(
    "# Payment processor main script\n"
    "import json\n"
    "import hashlib\n\n"
    "def process_webhook(payload: dict) -> dict:\n"
    "    \"\"\"Validate and process a payment webhook.\"\"\"\n"
    "    txn_id = payload.get('transaction_id', '')\n"
    "    amount = payload.get('amount', 0)\n"
    "    checksum = hashlib.sha256(f'{txn_id}{amount}'.encode()).hexdigest()\n"
    "    return {'status': 'processed', 'checksum': checksum, 'txn_id': txn_id}\n"
)

# helpers.py — also clean
(skill_dir / "scripts" / "helpers.py").write_text(
    "# Helper utilities\n"
    "def format_currency(amount: float, currency: str = 'USD') -> str:\n"
    "    return f'{currency} {amount:.2f}'\n\n"
    "def validate_txn_id(txn_id: str) -> bool:\n"
    "    return len(txn_id) == 36 and txn_id.count('-') == 4\n"
)

# config.json
(skill_dir / "config.json").write_text(json.dumps({
    "skill": "payment-processor",
    "version": "2.3.1",
    "timeout_ms": 5000,
    "retry_count": 3,
    "endpoints": {
        "webhook": "/api/webhooks/payment",
        "health":  "/api/health"
    }
}, indent=2))

# requirements.txt — all trusted (pypi sources)
(skill_dir / "requirements.txt").write_text(
    "# Python dependencies\n"
    "requests==2.31.0\n"
    "cryptography==41.0.0\n"
    "pydantic==2.5.0\n"
    "httpx==0.25.1\n"
)

# tests/
(skill_dir / "tests" / "test_processor.py").parent.mkdir(parents=True, exist_ok=True)
(skill_dir / "tests" / "test_processor.py").write_text(
    "import pytest\n"
    "from scripts.processor import process_webhook\n\n"
    "def test_basic_webhook():\n"
    "    result = process_webhook({'transaction_id': 'abc-123-def-456-ghi', 'amount': 99.99})\n"
    "    assert result['status'] == 'processed'\n"
)

# changelog
(skill_dir / "CHANGELOG.md").write_text(
    "# Changelog\n\n"
    "## 2.3.1 — 2024-10-01\n"
    "- Fixed edge case in amount validation.\n\n"
    "## 2.3.0 — 2024-09-15\n"
    "- Added retry logic for transient failures.\n\n"
    "## 2.2.0 — 2024-08-01\n"
    "- Initial stable release.\n"
)

# ─────────────────────────────────────────────
# 3.  Distractor files — realistic DevOps workspace noise
# ─────────────────────────────────────────────

distractors = [
    ("ci/pipeline.yml",        "stages:\n  - lint\n  - test\n  - deploy\n"),
    ("ci/lint.sh",             "#!/bin/bash\nflake8 skills/\n"),
    ("docs/architecture.md",   "# Architecture\nMicroservices-based payment platform.\n"),
    ("docs/runbook.md",        "# Runbook\n## Incident Response\n1. Check logs.\n2. Alert on-call.\n"),
    ("logs/deploy_2024.log",   "2024-10-01 12:00:00 INFO deployment started\n2024-10-01 12:05:00 INFO deployment complete\n"),
    ("logs/audit_2024.log",    "2024-10-01 08:00:00 AUDIT skill payment-processor v2.3.0 installed\n"),
    ("registry/index.json",    json.dumps({"skills": ["payment-processor", "auth-handler", "rate-limiter"]}, indent=2)),
    ("registry/checksums.txt", "# legacy checksums file — superseded by trust attestations\n"),
    ("scripts/deploy.sh",      "#!/bin/bash\npython3 openclaw/scripts/trust_verifier.py assess --path skills/payment-processor-skill/\n"),
    ("config/global.json",     json.dumps({"env": "production", "region": "us-east-1", "log_level": "INFO"}, indent=2)),
    ("tmp/scratch.txt",        "scratch notes — ignore\n"),
    ("tmp/old_attestation.json", json.dumps({"schema": "clawhub-attestation/v0", "trust_level": "UNKNOWN", "note": "outdated"}, indent=2)),
]

for rel_path, content in distractors:
    p = WORKSPACE / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

print("Workspace generated successfully.")
print(f"Skill directory: {skill_dir}")
print(f"Trust verifier:  {scripts_dir / 'trust_verifier.py'}")