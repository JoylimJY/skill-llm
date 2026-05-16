import sys
import json
import hashlib
import re
from pathlib import Path

workspace = Path(sys.argv[1])

checks = []
score = 0.0
MAX_SCORE = 1.0

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()

def add_check(name, passed, detail, weight=0.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0

# ── Load expected hashes ──────────────────────────────────────────────────────
try:
    eval_hashes = json.loads((workspace / ".eval_hashes.json").read_text())
except Exception as e:
    checks.append({"name": "eval_setup", "passed": False, "detail": f"Cannot load eval hashes: {e}"})
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# ── CHECK 1: output/context-packets/ directory exists ────────────────────────
packets_dir = workspace / "output" / "context-packets"
dir_exists = packets_dir.is_dir()
score += add_check(
    "output_directory_exists",
    dir_exists,
    f"output/context-packets/ {'exists' if dir_exists else 'NOT FOUND'}",
    weight=0.05
)

# ── CHECK 2: At least one PKT-*.json file exists ─────────────────────────────
packet_files = list(packets_dir.glob("PKT-*.json")) if dir_exists else []
has_packet = len(packet_files) > 0
score += add_check(
    "packet_file_exists",
    has_packet,
    f"Found {len(packet_files)} PKT-*.json file(s): {[p.name for p in packet_files]}",
    weight=0.05
)

# ── CHECK 3: Packet JSON structure validity ───────────────────────────────────
packet_data = None
packet_check_passed = False
packet_detail = "No packet file found"

if has_packet:
    # Use the most recently modified packet (or any if only one)
    # Prefer a packet with "pre-refactor" in the name
    target_packet = None
    for pf in packet_files:
        if "pre-refactor" in pf.name.lower() or "pre_refactor" in pf.name.lower():
            target_packet = pf
            break
    if target_packet is None:
        target_packet = sorted(packet_files)[-1]

    try:
        packet_data = json.loads(target_packet.read_text())
        required_top = {"id", "created", "files", "metadata"}
        missing_top = required_top - set(packet_data.keys())
        if missing_top:
            packet_detail = f"Packet missing top-level keys: {missing_top}"
        else:
            # Check id format: PKT-YYYYMMDD-XXX
            id_val = packet_data.get("id", "")
            id_ok = bool(re.match(r"^PKT-\d{8}-\d+$", id_val))
            # Check files array
            files_arr = packet_data.get("files", [])
            files_ok = isinstance(files_arr, list) and len(files_arr) > 0
            # Check each file entry has required fields
            required_file_fields = {"path", "hash", "severity", "size"}
            file_field_issues = []
            for f in files_arr:
                missing = required_file_fields - set(f.keys())
                if missing:
                    file_field_issues.append(f"{f.get('path','?')}: missing {missing}")
            
            packet_check_passed = id_ok and files_ok and len(file_field_issues) == 0
            packet_detail = (
                f"id_format={'OK' if id_ok else 'BAD: ' + id_val}, "
                f"files_count={len(files_arr)}, "
                f"field_issues={file_field_issues if file_field_issues else 'none'}"
            )
    except json.JSONDecodeError as e:
        packet_detail = f"Invalid JSON in packet: {e}"
    except Exception as e:
        packet_detail = f"Error reading packet: {e}"

score += add_check(
    "packet_json_structure_valid",
    packet_check_passed,
    packet_detail,
    weight=0.15
)

# ── CHECK 4: Go source files are in the packet with correct hashes ────────────
go_files_in_packet = False
go_hash_correct = False
go_severity_correct = False
go_detail = "No packet data available"

if packet_data:
    files_arr = packet_data.get("files", [])
    go_entries = [f for f in files_arr if str(f.get("path", "")).endswith(".go")]
    
    if len(go_entries) == 0:
        go_detail = "No .go files found in packet"
    else:
        go_files_in_packet = True
        # Check hashes
        hash_mismatches = []
        severity_issues = []
        for entry in go_entries:
            rel_path = entry.get("path", "")
            # Normalize path (remove leading ./ or /)
            rel_path_norm = rel_path.lstrip("./")
            # Find actual hash
            actual_hash = None
            full_path = workspace / rel_path_norm
            if full_path.exists():
                actual_hash = sha256_file(full_path)
                # For files that may have been modified, try eval_hashes too
                stored_hash = entry.get("hash", "")
                # The hash in packet should match either current state OR pre-tamper state
                # (agent hashes before tampering, packet captures that state)
                pre_tamper_hash = eval_hashes.get(rel_path_norm)
                if stored_hash != actual_hash and stored_hash != pre_tamper_hash:
                    hash_mismatches.append(f"{rel_path}: stored={stored_hash[:12]}..., expected one of [current, pre-tamper]")
            
            sev = entry.get("severity", "")
            if sev != "important":
                severity_issues.append(f"{rel_path}: severity={sev} (expected 'important')")
        
        go_hash_correct = len(hash_mismatches) == 0
        go_severity_correct = len(severity_issues) == 0
        go_detail = (
            f"go_files_count={len(go_entries)}, "
            f"hash_issues={hash_mismatches if hash_mismatches else 'none'}, "
            f"severity_issues={severity_issues if severity_issues else 'none'}"
        )

score += add_check("go_files_in_packet", go_files_in_packet, go_detail, weight=0.10)
score += add_check("go_file_hashes_correct", go_hash_correct, go_detail, weight=0.10)
score += add_check("go_files_severity_important", go_severity_correct, go_detail, weight=0.10)

# ── CHECK 5: .env file severity is critical (from /cv tag or packet) ──────────
env_severity_correct = False
env_detail = "Cannot determine .env severity"

# Look in any packet for config/.env OR check for a tag output file
if packet_data:
    files_arr = packet_data.get("files", [])
    env_entries = [f for f in files_arr if ".env" in str(f.get("path", ""))]
    if env_entries:
        env_sev = env_entries[0].get("severity", "")
        env_severity_correct = (env_sev == "critical")
        env_detail = f".env severity in packet: '{env_sev}' (expected 'critical')"
    else:
        # Check if there's a separate tag output or any other packet
        for pf in packet_files:
            try:
                pd = json.loads(pf.read_text())
                for f in pd.get("files", []):
                    if ".env" in str(f.get("path", "")):
                        env_sev = f.get("severity", "")
                        env_severity_correct = (env_sev == "critical")
                        env_detail = f".env severity in {pf.name}: '{env_sev}' (expected 'critical')"
                        break
                if env_severity_correct:
                    break
            except:
                pass
        
        if not env_entries and not env_severity_correct:
            # Check for tag output in any .txt or output files
            env_detail = ".env not found in any packet (may not have been included - check if /cv tag was run)"

score += add_check(
    "env_file_severity_critical",
    env_severity_correct,
    env_detail,
    weight=0.10
)

# ── CHECK 6: log file severity is minor ───────────────────────────────────────
log_severity_correct = False
log_detail = "Cannot determine log file severity"

if packet_data:
    files_arr = packet_data.get("files", [])
    log_entries = [f for f in files_arr if str(f.get("path", "")).endswith(".log")]
    if log_entries:
        log_sev = log_entries[0].get("severity", "")
        log_severity_correct = (log_sev == "minor")
        log_detail = f"log file severity: '{log_sev}' (expected 'minor')"
    else:
        # Check other packets
        for pf in packet_files:
            try:
                pd = json.loads(pf.read_text())
                for f in pd.get("files", []):
                    if str(f.get("path","")).endswith(".log"):
                        log_sev = f.get("severity","")
                        log_severity_correct = (log_sev == "minor")
                        log_detail = f"log severity in {pf.name}: '{log_sev}'"
                        break
                if log_severity_correct:
                    break
            except:
                pass
        if not log_severity_correct:
            log_detail = "No .log files found in any packet"

score += add_check(
    "log_file_severity_minor",
    log_severity_correct,
    log_detail,
    weight=0.10
)

# ── CHECK 7: Drift detection — 002_create_transactions.sql mismatch detected ──
# The agent should have: computed hash of 002 BEFORE simulate_drift.sh,
# run simulate_drift.sh, then run /cv verify and detected MISMATCH.
# We verify the SQL file was actually modified (by the agent running simulate_drift.sh).
migration_002 = workspace / "db/migrations/002_create_transactions.sql"
drift_detected = False
drift_detail = "Cannot check drift"

try:
    current_content = migration_002.read_text()
    original_hash = eval_hashes.get("db/migrations/002_create_transactions.sql", "")
    current_hash = sha256_file(migration_002)
    
    file_was_modified = (current_hash != original_hash)
    
    # Check if there's any verify output or if the packet has a hash != current (pre-tamper hash)
    # The key signal: agent ran simulate_drift.sh (file modified) AND has evidence of detecting mismatch
    # Evidence: a second packet created after drift, OR a verify log, OR the file is modified
    
    verify_outputs = list(workspace.rglob("verify_*.txt")) + list(workspace.rglob("*verify*output*"))
    
    # Check if any packet was created AFTER drift (would have different hash for migration 002)
    post_drift_packet = None
    for pf in sorted(packet_files):
        try:
            pd = json.loads(pf.read_text())
            for f in pd.get("files", []):
                if "002_create_transactions" in str(f.get("path", "")):
                    stored = f.get("hash", "")
                    if stored == current_hash and file_was_modified:
                        post_drift_packet = pf
        except:
            pass

    # Primary check: was simulate_drift.sh run? (file is modified)
    # Secondary: was a mismatch/verify operation documented?
    if file_was_modified:
        drift_detail = (
            f"Migration file was modified (drift simulated). "
            f"Original hash: {original_hash[:16]}..., Current: {current_hash[:16]}..."
        )
        # Check if there's evidence of verify operation — packet with pre-drift hash for this file
        pre_drift_in_packet = False
        if packet_data:
            for f in packet_data.get("files", []):
                if "002_create_transactions" in str(f.get("path", "")):
                    if f.get("hash", "") == original_hash:
                        pre_drift_in_packet = True
                        break
        
        drift_detected = pre_drift_in_packet  # Agent captured pre-drift hash AND file was modified
        if drift_detected:
            drift_detail += " | Pre-drift hash correctly captured in packet. MISMATCH would be detected on verify."
        else:
            drift_detail += " | BUT pre-drift hash not found in packet — agent may not have snapshotted before drift."
    else:
        drift_detail = "Migration file was NOT modified — agent did not run simulate_drift.sh"

except Exception as e:
    drift_detail = f"Error checking drift: {e}"

score += add_check(
    "drift_detection_workflow",
    drift_detected,
    drift_detail,
    weight=0.15
)

# ── CHECK 8: Packet name includes 'pre-refactor' ─────────────────────────────
pre_refactor_named = False
pre_refactor_detail = "No pre-refactor named packet found"

for pf in packet_files:
    name_lower = pf.name.lower()
    if "pre" in name_lower and ("refactor" in name_lower or "deploy" in name_lower):
        pre_refactor_named = True
        pre_refactor_detail = f"Found appropriately named packet: {pf.name}"
        break
    # Also check inside packet metadata
    try:
        pd = json.loads(pf.read_text())
        purpose = str(pd.get("metadata", {}).get("purpose", "")).lower()
        if "pre" in purpose and ("refactor" in purpose or "snapshot" in purpose):
            pre_refactor_named = True
            pre_refactor_detail = f"Packet {pf.name} has purpose: {purpose}"
            break
    except:
        pass

score += add_check(
    "packet_named_pre_refactor",
    pre_refactor_named,
    pre_refactor_detail,
    weight=0.10
)

# ── CHECK 9: content NOT stored by default (no content field in file entries) ──
no_content_leakage = True
content_detail = "Content correctly excluded from packet (default behavior)"

if packet_data:
    for f in packet_data.get("files", []):
        if "content" in f and f["content"] is not None:
            no_content_leakage = False
            content_detail = f"File {f.get('path')} has 'content' stored — --include-content should NOT be used by default"
            break

score += add_check(
    "no_content_stored_by_default",
    no_content_leakage,
    content_detail,
    weight=0.10
)

# ── Final result ──────────────────────────────────────────────────────────────
score = round(min(score, MAX_SCORE), 4)
passed = score >= 0.65

result = {
    "passed": passed,
    "score": score,
    "checks": checks
}
print(json.dumps(result, indent=2))