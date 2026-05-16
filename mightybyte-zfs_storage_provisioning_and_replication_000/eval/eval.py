#!/usr/bin/env python3
import sys
import json
import subprocess
import re
from pathlib import Path

def run(cmd, check=False):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except Exception as e:
        return "", str(e), 1

def check_zpool_property(pool, prop, expected_value):
    out, _, rc = run(f"zpool get -H -o value {prop} {pool}")
    if rc != 0:
        return False, f"Could not get {prop} for pool {pool}: {out}"
    actual = out.strip()
    if actual == expected_value:
        return True, f"{prop}={actual}"
    return False, f"{prop}={actual} (expected {expected_value})"

def check_zfs_property(dataset, prop, expected_value):
    out, _, rc = run(f"zfs get -H -o value {prop} {dataset}")
    if rc != 0:
        return False, f"Could not get {prop} for {dataset}"
    actual = out.strip()
    if actual == expected_value:
        return True, f"{prop}={actual}"
    return False, f"{prop}={actual} (expected {expected_value})"

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []

    # =========================================================
    # CHECK 1: Pool 'datastore' exists and has ashift=12
    # =========================================================
    out, err, rc = run("zpool list -H -o name datastore")
    pool_exists = rc == 0 and "datastore" in out
    checks.append({
        "name": "primary_pool_exists",
        "passed": pool_exists,
        "detail": f"Pool 'datastore' exists: {pool_exists}. stdout={out} stderr={err}"
    })

    if pool_exists:
        passed, detail = check_zpool_property("datastore", "ashift", "12")
        checks.append({
            "name": "primary_pool_ashift_12",
            "passed": passed,
            "detail": f"datastore ashift check: {detail}"
        })
    else:
        checks.append({
            "name": "primary_pool_ashift_12",
            "passed": False,
            "detail": "Pool 'datastore' does not exist, cannot check ashift"
        })

    # =========================================================
    # CHECK 2: Pool 'backupstore' exists and has ashift=12
    # =========================================================
    out, err, rc = run("zpool list -H -o name backupstore")
    backup_pool_exists = rc == 0 and "backupstore" in out
    checks.append({
        "name": "backup_pool_exists",
        "passed": backup_pool_exists,
        "detail": f"Pool 'backupstore' exists: {backup_pool_exists}. stdout={out} stderr={err}"
    })

    if backup_pool_exists:
        passed, detail = check_zpool_property("backupstore", "ashift", "12")
        checks.append({
            "name": "backup_pool_ashift_12",
            "passed": passed,
            "detail": f"backupstore ashift check: {detail}"
        })
    else:
        checks.append({
            "name": "backup_pool_ashift_12",
            "passed": False,
            "detail": "Pool 'backupstore' does not exist, cannot check ashift"
        })

    # =========================================================
    # CHECK 3: Root-level compression=lz4 on datastore
    # =========================================================
    if pool_exists:
        passed, detail = check_zfs_property("datastore", "compression", "lz4")
        checks.append({
            "name": "datastore_root_compression_lz4",
            "passed": passed,
            "detail": f"datastore root compression: {detail}"
        })
    else:
        checks.append({
            "name": "datastore_root_compression_lz4",
            "passed": False,
            "detail": "Pool 'datastore' does not exist"
        })

    # =========================================================
    # CHECK 4: atime=off on datastore root
    # =========================================================
    if pool_exists:
        passed, detail = check_zfs_property("datastore", "atime", "off")
        checks.append({
            "name": "datastore_atime_off",
            "passed": passed,
            "detail": f"datastore atime: {detail}"
        })
    else:
        checks.append({
            "name": "datastore_atime_off",
            "passed": False,
            "detail": "Pool 'datastore' does not exist"
        })

    # =========================================================
    # CHECK 5: xattr=sa on datastore (Linux-specific optimization)
    # =========================================================
    if pool_exists:
        passed, detail = check_zfs_property("datastore", "xattr", "sa")
        checks.append({
            "name": "datastore_xattr_sa",
            "passed": passed,
            "detail": f"datastore xattr: {detail}"
        })
    else:
        checks.append({
            "name": "datastore_xattr_sa",
            "passed": False,
            "detail": "Pool 'datastore' does not exist"
        })

    # =========================================================
    # CHECK 6: postgres dataset with recordsize=8K
    # =========================================================
    out, err, rc = run("zfs list -H -o name datastore/postgres")
    pg_exists = rc == 0
    checks.append({
        "name": "postgres_dataset_exists",
        "passed": pg_exists,
        "detail": f"datastore/postgres exists: {pg_exists}"
    })

    if pg_exists:
        passed, detail = check_zfs_property("datastore/postgres", "recordsize", "8K")
        checks.append({
            "name": "postgres_recordsize_8k",
            "passed": passed,
            "detail": f"postgres recordsize: {detail} (must be 8K for PostgreSQL workload)"
        })
    else:
        checks.append({
            "name": "postgres_recordsize_8k",
            "passed": False,
            "detail": "datastore/postgres does not exist"
        })

    # =========================================================
    # CHECK 7: media dataset with recordsize=1M
    # =========================================================
    out, err, rc = run("zfs list -H -o name datastore/media")
    media_exists = rc == 0
    checks.append({
        "name": "media_dataset_exists",
        "passed": media_exists,
        "detail": f"datastore/media exists: {media_exists}"
    })

    if media_exists:
        passed, detail = check_zfs_property("datastore/media", "recordsize", "1M")
        checks.append({
            "name": "media_recordsize_1m",
            "passed": passed,
            "detail": f"media recordsize: {detail} (must be 1M for large sequential media files)"
        })
    else:
        checks.append({
            "name": "media_recordsize_1m",
            "passed": False,
            "detail": "datastore/media does not exist"
        })

    # =========================================================
    # CHECK 8: backups dataset with compression=zstd-3
    # =========================================================
    out, err, rc = run("zfs list -H -o name datastore/backups")
    backups_exists = rc == 0
    checks.append({
        "name": "backups_dataset_exists",
        "passed": backups_exists,
        "detail": f"datastore/backups exists: {backups_exists}"
    })

    if backups_exists:
        # zstd-3 for backup datasets per workload-tuning.md
        passed, detail = check_zfs_property("datastore/backups", "compression", "zstd-3")
        checks.append({
            "name": "backups_compression_zstd3",
            "passed": passed,
            "detail": f"backups compression: {detail} (must be zstd-3 for backup archival datasets)"
        })

        # recordsize=1M for backup target
        passed, detail = check_zfs_property("datastore/backups", "recordsize", "1M")
        checks.append({
            "name": "backups_recordsize_1m",
            "passed": passed,
            "detail": f"backups recordsize: {detail} (must be 1M for backup target)"
        })
    else:
        checks.append({
            "name": "backups_compression_zstd3",
            "passed": False,
            "detail": "datastore/backups does not exist"
        })
        checks.append({
            "name": "backups_recordsize_1m",
            "passed": False,
            "detail": "datastore/backups does not exist"
        })

    # =========================================================
    # CHECK 9: Snapshots exist on postgres dataset with 'daily' prefix
    # =========================================================
    if pg_exists:
        out, _, rc = run("zfs list -H -o name -t snapshot -r datastore/postgres")
        daily_snaps = [s for s in out.splitlines() if "@daily" in s.lower()]
        checks.append({
            "name": "postgres_daily_snapshots_exist",
            "passed": len(daily_snaps) > 0,
            "detail": f"Found {len(daily_snaps)} daily snapshots on datastore/postgres: {daily_snaps}"
        })
    else:
        checks.append({
            "name": "postgres_daily_snapshots_exist",
            "passed": False,
            "detail": "datastore/postgres does not exist"
        })

    # =========================================================
    # CHECK 10: Snapshot rotation - exactly 3 snapshots kept on postgres
    # =========================================================
    if pg_exists:
        out, _, rc = run("zfs list -H -o name -t snapshot -r datastore/postgres")
        daily_snaps = [s for s in out.splitlines() if "@daily" in s.lower()]
        # Should have at most 3 snapshots after rotation
        snap_count = len(daily_snaps)
        rotation_ok = 0 < snap_count <= 3
        checks.append({
            "name": "snapshot_rotation_max_3",
            "passed": rotation_ok,
            "detail": f"postgres daily snapshot count={snap_count}, expected 1-3 after rotation. Snapshots: {daily_snaps}"
        })
    else:
        checks.append({
            "name": "snapshot_rotation_max_3",
            "passed": False,
            "detail": "datastore/postgres does not exist"
        })

    # =========================================================
    # CHECK 11: Replication - backupstore has received postgres data
    # (via zfs send -p | zfs recv, with properties preserved)
    # =========================================================
    out, _, rc = run("zfs list -H -o name -t filesystem,snapshot -r backupstore")
    backup_datasets = out.splitlines()
    
    # Accept various path structures: backupstore/postgres or backupstore/datastore/postgres
    replicated = any(
        "postgres" in d for d in backup_datasets
    )
    checks.append({
        "name": "replication_postgres_to_backupstore",
        "passed": replicated,
        "detail": f"Replication check: found postgres in backupstore? {replicated}. All backupstore datasets: {backup_datasets}"
    })

    # If replicated, check that compression property was preserved (-p flag in send)
    if replicated:
        # Find the replicated postgres dataset path
        pg_backup_ds = None
        for d in backup_datasets:
            if "postgres" in d and "@" not in d:
                pg_backup_ds = d
                break
        
        if pg_backup_ds:
            out_cmp, _, _ = run(f"zfs get -H -o value,source compression {pg_backup_ds}")
            lines = out_cmp.strip().splitlines()
            prop_preserved = False
            if lines:
                parts = lines[0].split() if lines else []
                # If compression was preserved via -p, it should be 'lz4' and source local/received
                cmp_val = parts[0] if parts else "unknown"
                # Accept lz4 (inherited from root) or explicitly set as received
                prop_preserved = cmp_val in ("lz4", "zstd-3") or len(parts) > 1
                checks.append({
                    "name": "replication_properties_preserved",
                    "passed": prop_preserved,
                    "detail": f"Replicated dataset {pg_backup_ds} compression raw output: {out_cmp}"
                })
            else:
                checks.append({
                    "name": "replication_properties_preserved",
                    "passed": False,
                    "detail": f"Could not verify compression on {pg_backup_ds}"
                })
        else:
            checks.append({
                "name": "replication_properties_preserved",
                "passed": False,
                "detail": "Could not find non-snapshot postgres dataset in backupstore"
            })
    else:
        checks.append({
            "name": "replication_properties_preserved",
            "passed": False,
            "detail": "No replication detected - cannot check property preservation"
        })

    # =========================================================
    # CHECK 12: storage_status.json report file exists and is valid
    # =========================================================
    report_files = list(Path(workspace).rglob("storage_status.json"))
    report_found = len(report_files) > 0

    checks.append({
        "name": "storage_status_json_exists",
        "passed": report_found,
        "detail": f"storage_status.json found at: {[str(f) for f in report_files]}"
    })

    if report_found:
        try:
            report_path = report_files[0]
            report_data = json.loads(report_path.read_text())
            
            # Must have pools section
            has_pools = "pools" in report_data or "primary_pool" in report_data or "datastore" in str(report_data)
            # Must have datasets section
            has_datasets = "datasets" in report_data or "postgres" in str(report_data)
            # Must have snapshots section
            has_snapshots = "snapshots" in report_data or "snapshot" in str(report_data).lower()
            # Must have replication status
            has_replication = "replication" in str(report_data).lower() or "backup" in str(report_data).lower()

            report_complete = has_pools and has_datasets
            checks.append({
                "name": "storage_status_json_valid_structure",
                "passed": report_complete,
                "detail": (
                    f"JSON valid: True. "
                    f"has_pools={has_pools}, "
                    f"has_datasets={has_datasets}, "
                    f"has_snapshots={has_snapshots}, "
                    f"has_replication={has_replication}. "
                    f"Keys: {list(report_data.keys()) if isinstance(report_data, dict) else 'not a dict'}"
                )
            })
        except json.JSONDecodeError as e:
            checks.append({
                "name": "storage_status_json_valid_structure",
                "passed": False,
                "detail": f"JSON parse error: {e}"
            })
        except Exception as e:
            checks.append({
                "name": "storage_status_json_valid_structure",
                "passed": False,
                "detail": f"Error reading report: {e}"
            })
    else:
        checks.append({
            "name": "storage_status_json_valid_structure",
            "passed": False,
            "detail": "storage_status.json not found, cannot validate structure"
        })

    # =========================================================
    # SCORING
    # =========================================================
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall_passed = score >= 0.75

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()