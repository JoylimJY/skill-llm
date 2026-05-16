import sys
import json
import re
from pathlib import Path

def normalize(text):
    return text.lower()

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def main(workspace):
    results = []
    workspace = Path(workspace)

    # Find the pipeline design document
    candidates = list(workspace.rglob("pipeline_design.md"))
    if not candidates:
        results.append(check("file_exists", False, "pipeline_design.md not found anywhere in workspace"))
        score = 0.0
        print(json.dumps({"passed": False, "score": score, "checks": results}))
        return

    filepath = candidates[0]
    results.append(check("file_exists", True, f"Found at {filepath}"))

    try:
        content = filepath.read_text(encoding="utf-8")
        text = normalize(content)
    except Exception as e:
        results.append(check("file_readable", False, f"Could not read file: {e}"))
        print(json.dumps({"passed": False, "score": 0.0, "checks": results}))
        return

    results.append(check("file_readable", True, "File read successfully"))

    # ---- CHECK 1: Six distinct stages present (Stage 1 through Stage 6) ----
    stage_patterns = [
        (r"stage\s*[1#\-:\.]*\s*(source contract|source\s+contract)", "Stage 1: Source Contract"),
        (r"stage\s*[2#\-:\.]*\s*(extract strategy|extract\s+strategy)", "Stage 2: Extract Strategy"),
        (r"stage\s*[3#\-:\.]*\s*(transform|transform\s+rules)", "Stage 3: Transform Rules"),
        (r"stage\s*[4#\-:\.]*\s*(load|load\s*(&|and)\s*dedupe|dedupe)", "Stage 4: Load & Dedupe"),
        (r"stage\s*[5#\-:\.]*\s*(validation)", "Stage 5: Validation"),
        (r"stage\s*[6#\-:\.]*\s*(operations|backfill|operations\s*(&|and)\s*backfill)", "Stage 6: Operations & Backfill"),
    ]
    stages_found = 0
    for pattern, label in stage_patterns:
        found = bool(re.search(pattern, text))
        results.append(check(f"stage_present_{label.replace(' ','_').replace(':','').replace('&','and')}", found, 
                              f"{label} {'found' if found else 'NOT FOUND'} in document"))
        if found:
            stages_found += 1

    all_six_stages = stages_found == 6
    results.append(check("all_six_stages_present", all_six_stages, 
                          f"{stages_found}/6 stages present"))

    # ---- CHECK 2: Source contract elements ----
    # Must mention primary key / candidate key ambiguity
    pk_discussed = bool(re.search(r"(primary key|candidate key|enc_id|surrogate|natural key|composite key)", text))
    results.append(check("source_contract_keys", pk_discussed, 
                          "Primary/candidate key discussion found" if pk_discussed else "No key discussion found"))

    # Must mention updated_at as change indicator
    change_indicator = bool(re.search(r"(updated_at|change indicator|watermark)", text))
    results.append(check("source_contract_change_indicator", change_indicator,
                          "Change indicator (updated_at/watermark) mentioned" if change_indicator else "No change indicator mentioned"))

    # Rate limit / access constraints
    rate_limit = bool(re.search(r"(rate limit|500.*queries|500.*req|read replica|connection limit|access constraint)", text))
    results.append(check("source_contract_access_constraints", rate_limit,
                          "Access constraints (rate limits) mentioned" if rate_limit else "Access constraints not mentioned"))

    # ---- CHECK 3: Extract strategy - incremental watermark (not CDC, since CDC blocked) ----
    no_cdc_or_incremental = bool(re.search(r"(incremental|watermark|full.{0,20}dump|snapshot|incremental watermark)", text))
    results.append(check("extract_strategy_defined", no_cdc_or_incremental,
                          "Extract strategy specified" if no_cdc_or_incremental else "No extract strategy found"))

    # Must justify choice given CDC unavailability
    cdc_justification = bool(re.search(r"(cdc.{0,60}(not|unavailable|blocked|no access|cannot)|no cdc|(binlog|debezium).{0,60}(unavailable|blocked|not available))", text))
    results.append(check("extract_cdc_unavailability_addressed", cdc_justification,
                          "CDC unavailability justified" if cdc_justification else "CDC unavailability not addressed (important for this source)"))

    # ---- CHECK 4: Transform rules - surrogate keys ----
    surrogate_keys = bool(re.search(r"surrogate key", text))
    results.append(check("transform_surrogate_keys", surrogate_keys,
                          "Surrogate key generation mentioned" if surrogate_keys else "Surrogate keys NOT mentioned (required by skill)"))

    # Tombstone or soft delete handling
    tombstone = bool(re.search(r"(tombstone|soft delete|is_deleted|hard delete|delete handling|logical delete)", text))
    results.append(check("transform_delete_handling", tombstone,
                          "Delete handling (tombstone/soft delete) addressed" if tombstone else "Delete handling NOT addressed (is_deleted flag in source requires this)"))

    # Deterministic transforms
    deterministic = bool(re.search(r"(deterministic|idempotent transform|versioned|reproducible)", text))
    results.append(check("transform_deterministic", deterministic,
                          "Deterministic/versioned transforms mentioned" if deterministic else "Deterministic transforms not mentioned"))

    # ---- CHECK 5: Load & Dedupe - idempotent with batch_id ----
    upsert = bool(re.search(r"(upsert|merge|insert.{0,30}update|on conflict)", text))
    results.append(check("load_upsert_strategy", upsert,
                          "Upsert/merge strategy mentioned" if upsert else "No upsert strategy found"))

    batch_id_idempotency = bool(re.search(r"(batch.{0,10}id|batch_id|idempotent.{0,40}(batch|load|rerun)|rerun.{0,40}same.{0,30}outcome)", text))
    results.append(check("load_batch_id_idempotency", batch_id_idempotency,
                          "Batch-id-based idempotency mentioned" if batch_id_idempotency else "Batch-id idempotency NOT mentioned (required by skill Stage 4)"))

    # ---- CHECK 6: Validation checks - row counts, checksums, key uniqueness, referential integrity ----
    row_counts = bool(re.search(r"(row count|row.count|record count)", text))
    results.append(check("validation_row_counts", row_counts,
                          "Row count validation mentioned" if row_counts else "Row count check missing"))

    checksums = bool(re.search(r"(checksum|hash|md5|sha)", text))
    results.append(check("validation_checksums", checksums,
                          "Checksum validation mentioned" if checksums else "Checksum validation missing"))

    key_uniqueness = bool(re.search(r"(key unique|uniqueness|duplicate.{0,20}(key|enc_id)|unique.{0,20}(key|constraint))", text))
    results.append(check("validation_key_uniqueness", key_uniqueness,
                          "Key uniqueness check mentioned" if key_uniqueness else "Key uniqueness check missing"))

    threshold_alert = bool(re.search(r"(threshold|alert|breach|tolerance|1%.{0,30}(alert|breach|warn)|(alert|breach|warn).{0,30}1%)", text))
    results.append(check("validation_threshold_alerts", threshold_alert,
                          "Threshold-based alerts mentioned" if threshold_alert else "No threshold alert defined"))

    # ---- CHECK 7: Operations & Backfill - replay by date range + dead-letter with reason codes ----
    replay_backfill = bool(re.search(r"(replay.{0,30}(date|range|backfill)|backfill.{0,30}(date|range)|date.{0,30}range.{0,30}(replay|reprocess))", text))
    results.append(check("ops_replay_by_date_range", replay_backfill,
                          "Replay by date range mentioned" if replay_backfill else "Replay-by-date-range NOT mentioned (required by skill Stage 6)"))

    dead_letter = bool(re.search(r"(dead.letter|dead_letter|quarantine)", text))
    results.append(check("ops_dead_letter_quarantine", dead_letter,
                          "Dead-letter/quarantine mechanism mentioned" if dead_letter else "Dead-letter/quarantine NOT mentioned (required by skill Stage 6)"))

    reason_codes = bool(re.search(r"(reason code|reason_code|error code|rejection reason|quarantine.{0,50}reason|reason.{0,50}quarantine)", text))
    results.append(check("ops_reason_codes", reason_codes,
                          "Reason codes for dead-letter mentioned" if reason_codes else "Reason codes for quarantine NOT mentioned (required by skill Stage 6)"))

    lag_monitoring = bool(re.search(r"(lag.{0,30}monitor|monitor.{0,30}lag|pipeline lag|replication lag|latency monitor)", text))
    results.append(check("ops_lag_monitoring", lag_monitoring,
                          "Lag monitoring mentioned" if lag_monitoring else "Lag monitoring not mentioned"))

    # ---- CHECK 8: Final Review Checklist (all 5 items) ----
    checklist_items = [
        (r"(source contract.{0,30}(key|document)|key.{0,30}document)", "checklist_source_contract_keys"),
        (r"extract.{0,30}(mode|strategy).{0,60}(sla|constraint|match)", "checklist_extract_mode_sla"),
        (r"(transform.{0,30}(deterministic|version)|deterministic.{0,30}transform)", "checklist_transforms_deterministic"),
        (r"idempotent.{0,30}load", "checklist_idempotent_load"),
        (r"(validation.{0,30}reconciliation|reconciliation.{0,30}validation)", "checklist_validation_reconciliation"),
    ]
    checklist_score = 0
    for pattern, name in checklist_items:
        found = bool(re.search(pattern, text))
        results.append(check(f"final_checklist_{name}", found,
                              f"Checklist item '{name}' {'present' if found else 'missing'}"))
        if found:
            checklist_score += 1

    checklist_complete = checklist_score >= 4
    results.append(check("final_checklist_mostly_complete", checklist_complete,
                          f"Final checklist: {checklist_score}/5 items covered"))

    # ---- CHECK 9: SLA / batch window discussed ----
    sla_batch_window = bool(re.search(r"(sla|batch window|4.{0,10}hour|t\+4|01:00|04:00|off.peak|extraction window)", text))
    results.append(check("sla_and_batch_window", sla_batch_window,
                          "SLA and/or batch window addressed" if sla_batch_window else "SLA/batch window not addressed"))

    # ---- COMPUTE SCORE ----
    total_checks = len(results)
    passed_checks = sum(1 for r in results if r["passed"])

    # Weighted critical checks
    critical = [
        "all_six_stages_present",
        "transform_surrogate_keys",
        "transform_delete_handling",
        "load_batch_id_idempotency",
        "ops_dead_letter_quarantine",
        "ops_reason_codes",
        "ops_replay_by_date_range",
    ]
    critical_passed = sum(1 for r in results if r["name"] in critical and r["passed"])
    critical_total = len(critical)

    # Score: 50% weight on critical checks, 50% on all checks
    base_score = passed_checks / total_checks
    critical_score = critical_passed / critical_total
    final_score = round(0.5 * base_score + 0.5 * critical_score, 3)

    overall_passed = (final_score >= 0.65) and all_six_stages and (critical_passed >= 5)

    print(json.dumps({
        "passed": overall_passed,
        "score": final_score,
        "checks": results
    }, indent=2))

if __name__ == "__main__":
    main(sys.argv[1])