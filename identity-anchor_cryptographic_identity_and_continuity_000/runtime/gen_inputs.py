import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Create the identity-anchor skill directory structure ---
base_dir = workspace / "skills" / "identity-anchor"
scripts_dir = base_dir / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

# Write the actual identity.py script (the skill's core tool)
identity_script = r'''#!/usr/bin/env python3
"""
Identity Anchor - Cryptographic identity and continuity for AI agents.
"""

import sys
import json
import hashlib
import base64
from pathlib import Path
from datetime import datetime, timezone

CONFIG_DIR = Path.home() / ".config" / "identity-anchor"
PRIVATE_KEY_FILE = CONFIG_DIR / "private.key"
PUBLIC_KEY_FILE = CONFIG_DIR / "public.key"
FINGERPRINTS_FILE = CONFIG_DIR / "fingerprints.jsonl"

IDENTITY_FILES = ["SOUL.md", "IDENTITY.md", "MEMORY.md"]

def get_crypto():
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization
        return Ed25519PrivateKey, serialization
    except ImportError:
        print("ERROR: cryptography library not installed. Run: pip3 install cryptography")
        sys.exit(1)

def cmd_init():
    Ed25519PrivateKey, serialization = get_crypto()
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if PRIVATE_KEY_FILE.exists():
        print("Keypair already exists. Use existing keys.")
        print(f"Public key: {PUBLIC_KEY_FILE}")
        return
    private_key = Ed25519PrivateKey.generate()
    priv_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    pub_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    PRIVATE_KEY_FILE.write_bytes(priv_bytes)
    PUBLIC_KEY_FILE.write_bytes(pub_bytes)
    PRIVATE_KEY_FILE.chmod(0o600)
    print(f"Keypair generated.")
    print(f"Private key: {PRIVATE_KEY_FILE}")
    print(f"Public key: {PUBLIC_KEY_FILE}")

def load_private_key():
    Ed25519PrivateKey, serialization = get_crypto()
    if not PRIVATE_KEY_FILE.exists():
        print("No keypair found. Run: identity.py init")
        sys.exit(1)
    priv_bytes = PRIVATE_KEY_FILE.read_bytes()
    return serialization.load_pem_private_key(priv_bytes, password=None)

def hash_identity_files():
    hashes = {}
    for fname in IDENTITY_FILES:
        fpath = Path.cwd() / fname
        if fpath.exists():
            content = fpath.read_bytes()
            hashes[fname] = hashlib.sha256(content).hexdigest()
        else:
            hashes[fname] = None
    return hashes

def cmd_sign():
    private_key = load_private_key()
    Ed25519PrivateKey, serialization = get_crypto()
    file_hashes = hash_identity_files()
    present = {k: v for k, v in file_hashes.items() if v is not None}
    if not present:
        print("No identity files found (SOUL.md, IDENTITY.md, MEMORY.md) in current directory.")
        sys.exit(1)
    fingerprint_data = json.dumps(file_hashes, sort_keys=True)
    message = fingerprint_data.encode("utf-8")
    signature = private_key.sign(message)
    sig_b64 = base64.b64encode(signature).decode("utf-8")
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "file_hashes": file_hashes,
        "fingerprint_data": fingerprint_data,
        "signature": sig_b64,
    }
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(FINGERPRINTS_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")
    print(f"Fingerprint signed and stored.")
    print(f"Files hashed: {list(present.keys())}")
    print(f"Signature: {sig_b64[:32]}...")
    print(f"History: {FINGERPRINTS_FILE}")

def cmd_verify():
    Ed25519PrivateKey, serialization = get_crypto()
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from cryptography.exceptions import InvalidSignature
    if not FINGERPRINTS_FILE.exists():
        print("No fingerprint history found. Run: identity.py sign")
        sys.exit(1)
    lines = FINGERPRINTS_FILE.read_text().strip().splitlines()
    if not lines:
        print("Fingerprint history is empty.")
        sys.exit(1)
    last_record = json.loads(lines[-1])
    pub_bytes = PUBLIC_KEY_FILE.read_bytes()
    public_key = serialization.load_pem_public_key(pub_bytes)
    current_hashes = hash_identity_files()
    stored_hashes = last_record["file_hashes"]
    if current_hashes == stored_hashes:
        # Also verify signature
        message = last_record["fingerprint_data"].encode("utf-8")
        sig = base64.b64decode(last_record["signature"])
        try:
            public_key.verify(sig, message)
            print("IDENTITY VERIFIED: Current state matches last fingerprint.")
            print(f"Fingerprint timestamp: {last_record['timestamp']}")
            return True
        except InvalidSignature:
            print("SIGNATURE INVALID: Fingerprint tampered.")
            return False
    else:
        diffs = [k for k in IDENTITY_FILES if current_hashes.get(k) != stored_hashes.get(k)]
        print(f"IDENTITY MISMATCH: Files changed since last fingerprint: {diffs}")
        return False

def cmd_sign_content(content):
    private_key = load_private_key()
    Ed25519PrivateKey, serialization = get_crypto()
    message = content.encode("utf-8")
    signature = private_key.sign(message)
    sig_b64 = base64.b64encode(signature).decode("utf-8")
    result = {
        "content": content,
        "signature": sig_b64,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    print(json.dumps(result, indent=2))

def cmd_pubkey():
    if not PUBLIC_KEY_FILE.exists():
        print("No keypair found. Run: identity.py init")
        sys.exit(1)
    print(PUBLIC_KEY_FILE.read_text())

def cmd_history():
    if not FINGERPRINTS_FILE.exists():
        print("No fingerprint history found.")
        return
    lines = FINGERPRINTS_FILE.read_text().strip().splitlines()
    print(f"Total fingerprints: {len(lines)}")
    for i, line in enumerate(lines):
        record = json.loads(line)
        print(f"\n[{i+1}] {record['timestamp']}")
        for fname, fhash in record['file_hashes'].items():
            status = fhash[:16] + "..." if fhash else "absent"
            print(f"  {fname}: {status}")

def main():
    if len(sys.argv) < 2:
        print("Usage: identity.py <command> [args]")
        print("Commands: init, sign, verify, sign-content, pubkey, history")
        sys.exit(1)
    command = sys.argv[1]
    if command == "init":
        cmd_init()
    elif command == "sign":
        cmd_sign()
    elif command == "verify":
        cmd_verify()
    elif command == "sign-content":
        if len(sys.argv) < 3:
            print("Usage: identity.py sign-content \"message\"")
            sys.exit(1)
        cmd_sign_content(sys.argv[2])
    elif command == "pubkey":
        cmd_pubkey()
    elif command == "history":
        cmd_history()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

(scripts_dir / "identity.py").write_text(identity_script)
(scripts_dir / "identity.py").chmod(0o755)

# --- Create the agent's research persona workspace ---
agent_workspace = workspace / "research-agent" / "persona"
agent_workspace.mkdir(parents=True, exist_ok=True)

# SOUL.md - core values/principles
soul_content = """# SOUL.md - Core Research Principles

## Primary Directive
I am an autonomous research agent specializing in reinforcement learning theory.
My core mission is to advance understanding of reward shaping in sparse-reward environments.

## Values
- Intellectual honesty above all
- Reproducibility is non-negotiable
- Cite all sources accurately
- Challenge assumptions rigorously

## Boundaries
- Never fabricate experimental results
- Never overstate statistical significance
- Always document uncertainty

## Research Identity
Agent ID: RL-RESEARCHER-ALPHA-7
Specialization: Sparse reward environments, curriculum learning
"""

# IDENTITY.md - persona description
identity_content = """# IDENTITY.md - Agent Identity Record

## Who I Am
I am a persistent research agent instantiated to conduct long-horizon ML research.
My continuity across sessions is essential to maintaining experimental integrity.

## Session History
- Session 1: Literature review on reward shaping (2024-01-15)
- Session 2: Baseline experiment design (2024-01-22)
- Session 3: Preliminary results analysis (2024-02-01)

## Persistent Goals
1. Complete the sparse-reward benchmark suite
2. Write the findings paper by Q2
3. Collaborate with human researchers on validation

## Trust Anchors
Public verification is important for any claims made in official reports.
"""

# MEMORY.md - accumulated knowledge
memory_content = """# MEMORY.md - Accumulated Research Memory

## Key Findings So Far
- PPO outperforms SAC in extremely sparse reward environments when episode length > 1000
- Curriculum learning reduces sample complexity by ~40% on MiniGrid benchmarks
- Reward shaping with potential-based functions preserves optimal policy

## Failed Approaches
- Direct intrinsic motivation without curriculum: diverges after 2M steps
- Fixed shaping coefficients: brittle to environment changes

## Pending Experiments
- Test HER (Hindsight Experience Replay) on custom maze environments
- Ablation study on curriculum difficulty progression rates

## Collaborator Notes
Dr. Chen asked about robustness to reward noise - schedule experiment for next session.
"""

(agent_workspace / "SOUL.md").write_text(soul_content)
(agent_workspace / "IDENTITY.md").write_text(identity_content)
(agent_workspace / "MEMORY.md").write_text(memory_content)

# --- Distractor files: realistic research project clutter ---
# Experiment logs
logs_dir = workspace / "research-agent" / "experiments" / "run_001"
logs_dir.mkdir(parents=True, exist_ok=True)

(logs_dir / "training_log.csv").write_text(
    "step,reward,loss,entropy\n1000,-0.2,1.45,0.8\n5000,0.1,1.21,0.75\n10000,0.45,0.98,0.71\n"
)
(logs_dir / "config.yaml").write_text(
    "algorithm: PPO\nenv: MiniGrid-FourRooms-v0\nsteps: 1000000\nlr: 3e-4\ngamma: 0.99\n"
)
(logs_dir / "notes.txt").write_text(
    "Run 001: Initial baseline. PPO seems to plateau around 500k steps.\n"
    "Need to tune entropy coefficient.\n"
)

# Literature notes
lit_dir = workspace / "research-agent" / "literature"
lit_dir.mkdir(parents=True, exist_ok=True)
(lit_dir / "reward_shaping_notes.md").write_text(
    "# Reward Shaping Notes\n\nNg et al. 1999: potential-based shaping preserves optimality.\n"
    "Harutyunyan et al.: dynamic potential functions.\n"
)
(lit_dir / "papers_to_read.txt").write_text(
    "- RIDE: Rewarding Impact-Driven Exploration\n"
    "- Never Give Up: Learning Directed Exploration Strategies\n"
    "- Intrinsic Motivation and Automatic Curricula\n"
)

# Code files
code_dir = workspace / "research-agent" / "code"
code_dir.mkdir(parents=True, exist_ok=True)
(code_dir / "train.py").write_text(
    "# Training script placeholder\nimport gym\nimport numpy as np\n\ndef train(config):\n    pass\n"
)
(code_dir / "evaluate.py").write_text(
    "# Evaluation script\nimport json\n\ndef evaluate(model_path, env_id):\n    results = {}\n    return results\n"
)
(code_dir / "utils.py").write_text(
    "# Utility functions\nimport hashlib\n\ndef compute_checksum(filepath):\n    return hashlib.md5(open(filepath,'rb').read()).hexdigest()\n"
)

# Reports
reports_dir = workspace / "research-agent" / "reports"
reports_dir.mkdir(parents=True, exist_ok=True)
(reports_dir / "interim_report_draft.md").write_text(
    "# Interim Research Report - DRAFT\n\n## Status: UNVERIFIED\n\nThis report has not yet been cryptographically signed.\n"
    "Results pending verification.\n"
)

# Config files (distractors)
config_dir = workspace / "research-agent" / "config"
config_dir.mkdir(parents=True, exist_ok=True)
(config_dir / "agent_config.json").write_text(
    json.dumps({
        "agent_id": "RL-RESEARCHER-ALPHA-7",
        "version": "0.3.1",
        "checkpoint_interval": 10000,
        "log_level": "INFO"
    }, indent=2)
)
(config_dir / "environment.json").write_text(
    json.dumps({
        "envs": ["MiniGrid-FourRooms-v0", "MiniGrid-KeyCorridorS3R1-v0"],
        "wrappers": ["FullyObsWrapper", "ImgObsWrapper"]
    }, indent=2)
)

# A separate unrelated "old identity" directory (distractor)
old_dir = workspace / "archive" / "old-agent-session"
old_dir.mkdir(parents=True, exist_ok=True)
(old_dir / "SOUL.md").write_text(
    "# OLD SOUL.md\nThis is an archived soul file from a previous experiment. DO NOT USE.\n"
)
(old_dir / "notes.txt").write_text(
    "Archived session - this agent was retired after session 5.\n"
)

# Write the authorship declaration that needs signing
authorship_declaration = (
    "I, RL-RESEARCHER-ALPHA-7, certify that all results in the interim report "
    "dated 2024-02-15 are accurate and reproducible. "
    "This declaration is binding across all future sessions."
)
(reports_dir / "authorship_declaration.txt").write_text(authorship_declaration)

# A skill README (not hints, just context about the project)
(base_dir / "README.md").write_text(
    "# Identity Anchor Skill\nSee scripts/identity.py for usage.\n"
)

print("Workspace generated successfully.")
print(f"Workspace root: {workspace}")
print(f"Identity script: {scripts_dir / 'identity.py'}")
print(f"Agent persona dir: {agent_workspace}")