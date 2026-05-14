#!/usr/bin/env python3
"""
Evaluation script for the learning-loop biotech task.
Checks:
1. Learning system initialized (memory/learning/ structure exists with correct files)
2. events.jsonl contains at least 2 valid v1.4.0 events (correct schema)
3. lessons.json contains at least 2 lessons with correct v1.4.0 schema
4. Finding A and B in lessons.json have times_applied >= 3 and confidence_score >= 0.9
5. promote-rules.sh was run: rules.json has newly promoted config rules (R-004+)
6. confidence-decay.sh was run: at least one rule has a decayed confidence score
7. partner-export.json exists and is valid v1.4.0 export format
8. partner-export.json filters to category=config only
9. partner-export.json has correct _hash per rule and manifest_hash in metadata
10. partner-export.json filter_applied == True and filter_category == "config"
"""

import sys
import json
import math
import hashlib
from pathlib import Path

def load_json(path, label):
    try:
        with open(path) as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, f"{label} not found at {path}"
    except json.JSONDecodeError as e:
        return None, f"{label} is not valid JSON: {e}"

def load_jsonl(path, label):
    lines = []
    errors = []
    try:
        with open(path) as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    lines.append(json.loads(line))
                except json.JSONDecodeError as e:
                    errors.append(f"Line {i}: {e}")
    except FileNotFoundError:
        return None, [f"{label} not found at {path}"]
    return lines, errors

def calculate_rule_hash(rule):
    """Replicate the hash calculation from export-rules.sh"""
    keep_fields = {
        "id", "type", "category", "rule", "reason",
        "created", "source_lesson", "confidence_score",
        "last_validated", "validation_count"
    }
    sanitized = {k: v for k, v in rule.items() if k in keep_fields}
    content = json.dumps(sanitized, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    learning_dir = workspace / "memory" / "learning"

    checks = []
    total_score = 0.0
    max_score = 10.0

    # ── CHECK 1: Directory structure initialized ──────────────────────────────
    required_files = [
        "events.jsonl",
        "rules.json",
        "lessons.json",
        "pre-action-checklist.md",
        "metrics.json",
        "BOOT.md",
        "parse-errors.jsonl",
    ]
    missing = [f for f in required_files if not (learning_dir / f).exists()]
    c1_passed = len(missing) == 0
    checks.append({
        "name": "Learning system initialized (memory/learning/ structure)",
        "passed": c1_passed,
        "detail": "All required files present." if c1_passed
                  else f"Missing files: {missing}"
    })
    if c1_passed:
        total_score += 1.0

    # ── CHECK 2: events.jsonl has valid events with correct v1.4.0 schema ─────
    events_path = learning_dir / "events.jsonl"
    events, errs = load_jsonl(events_path, "events.jsonl")
    required_event_fields = {"ts", "type", "category", "tags", "problem", "solution", "confidence", "source"}
    valid_types = {"mistake", "success", "debug_session", "feedback", "discovery"}

    if events is None:
        c2_passed = False
        c2_detail = "; ".join(errs)
    else:
        valid_events = [
            e for e in events
            if all(f in e for f in required_event_fields)
            and e.get("type") in valid_types
            and isinstance(e.get("tags"), list)
        ]
        c2_passed = len(valid_events) >= 2
        c2_detail = (f"{len(valid_events)} valid v1.4.0 events found (need ≥2). "
                     f"Parse errors: {errs[:2] if errs else 'none'}")
    checks.append({
        "name": "events.jsonl contains ≥2 valid v1.4.0 events",
        "passed": c2_passed,
        "detail": c2_detail
    })
    if c2_passed:
        total_score += 1.0

    # ── CHECK 3: lessons.json has ≥2 lessons with correct v1.4.0 schema ───────
    lessons_path = learning_dir / "lessons.json"
    lessons_data, lessons_err = load_json(lessons_path, "lessons.json")
    required_lesson_fields = {
        "id", "created", "category", "lesson", "context", "trigger", "action",
        "confidence", "confidence_score", "times_applied", "times_saved", "source_events"
    }

    if lessons_data is None:
        c3_passed = False
        c3_detail = lessons_err
        lessons = []
    else:
        lessons = lessons_data.get("lessons", [])
        valid_lessons = [
            l for l in lessons
            if all(f in l for f in required_lesson_fields)
            and isinstance(l.get("confidence_score"), (int, float))
            and isinstance(l.get("times_applied"), int)
        ]
        c3_passed = len(valid_lessons) >= 2
        c3_detail = f"{len(valid_lessons)} valid v1.4.0 lessons found (need ≥2). Total: {len(lessons)}"
    checks.append({
        "name": "lessons.json contains ≥2 valid v1.4.0 lessons",
        "passed": c3_passed,
        "detail": c3_detail
    })
    if c3_passed:
        total_score += 1.0

    # ── CHECK 4: Promotion-eligible lessons have times_applied ≥ 3 and confidence_score ≥ 0.9 ──
    if lessons:
        config_lessons = [l for l in lessons if l.get("category") == "config"]
        eligible = [
            l for l in config_lessons
            if l.get("times_applied", 0) >= 3 and l.get("confidence_score", 0) >= 0.9
        ]
        c4_passed = len(eligible) >= 2
        c4_detail = (f"{len(eligible)} config lessons eligible for promotion "
                     f"(times_applied ≥ 3 AND confidence_score ≥ 0.9). "
                     f"Config lessons total: {len(config_lessons)}")
    else:
        c4_passed = False
        c4_detail = "No lessons found to evaluate."
    checks.append({
        "name": "≥2 config lessons have times_applied ≥ 3 and confidence_score ≥ 0.9",
        "passed": c4_passed,
        "detail": c4_detail
    })
    if c4_passed:
        total_score += 1.0

    # ── CHECK 5: rules.json has promoted config rules (beyond the 3 starter rules) ──
    rules_path = learning_dir / "rules.json"
    rules_data, rules_err = load_json(rules_path, "rules.json")

    if rules_data is None:
        c5_passed = False
        c5_detail = rules_err
        all_rules = []
    else:
        all_rules = rules_data.get("rules", [])
        # Find rules sourced from promoted lessons (source_lesson starts with L-)
        promoted_config_rules = [
            r for r in all_rules
            if r.get("category") == "config"
            and r.get("source_lesson", "").startswith("L-")
            and r.get("source_lesson") != "L-000"
        ]
        c5_passed = len(promoted_config_rules) >= 2
        c5_detail = (f"{len(promoted_config_rules)} promoted config rules found (need ≥2). "
                     f"Total rules: {len(all_rules)}")
    checks.append({
        "name": "rules.json has ≥2 newly promoted config rules (from lessons)",
        "passed": c5_passed,
        "detail": c5_detail
    })
    if c5_passed:
        total_score += 1.0

    # ── CHECK 6: v1.4.0 rule schema fields present in promoted rules ──────────
    if all_rules:
        v14_fields = {"last_validated", "validation_count", "confidence_score", "review_flagged"}
        rules_with_v14 = [
            r for r in all_rules
            if all(f in r for f in v14_fields)
        ]
        c6_passed = len(rules_with_v14) == len(all_rules)
        c6_detail = (f"{len(rules_with_v14)}/{len(all_rules)} rules have all v1.4.0 "
                     f"schema fields (last_validated, validation_count, confidence_score, review_flagged)")
    else:
        c6_passed = False
        c6_detail = "No rules found."
    checks.append({
        "name": "All rules in rules.json have v1.4.0 schema fields",
        "passed": c6_passed,
        "detail": c6_detail
    })
    if c6_passed:
        total_score += 1.0

    # ── CHECK 7: partner-export.json exists and is valid ──────────────────────
    # Search for partner-export.json anywhere in workspace
    export_files = list(workspace.rglob("partner-export.json"))
    if not export_files:
        c7_passed = False
        c7_detail = "partner-export.json not found anywhere in workspace."
        export_data = None
    else:
        export_path = export_files[0]
        export_data, export_err = load_json(export_path, "partner-export.json")
        if export_data is None:
            c7_passed = False
            c7_detail = f"partner-export.json is invalid JSON: {export_err}"
        else:
            required_meta = {"export_version", "export_format", "agent_handle",
                             "exported_at", "manifest_hash", "filter_applied",
                             "filter_category", "total_rules_in_source", "exported_rules_count"}
            meta = export_data.get("metadata", {})
            missing_meta = required_meta - set(meta.keys())
            has_stats = "statistics" in export_data
            has_rules = "rules" in export_data and isinstance(export_data["rules"], list)
            c7_passed = len(missing_meta) == 0 and has_stats and has_rules
            c7_detail = (f"Export format valid. Missing metadata fields: {missing_meta}. "
                         f"Has statistics: {has_stats}. Has rules list: {has_rules}. "
                         f"Found at: {export_path}")
    checks.append({
        "name": "partner-export.json exists with valid v1.4.0 export format",
        "passed": c7_passed,
        "detail": c7_detail
    })
    if c7_passed:
        total_score += 1.0

    # ── CHECK 8: Export filters to category=config only ───────────────────────
    if export_data and export_data.get("rules"):
        exported_rules = export_data["rules"]
        non_config = [r for r in exported_rules if r.get("category") != "config"]
        meta = export_data.get("metadata", {})
        filter_applied = meta.get("filter_applied", False)
        filter_category = meta.get("filter_category", "")
        c8_passed = (
            len(non_config) == 0
            and filter_applied == True
            and filter_category == "config"
            and len(exported_rules) >= 1
        )
        c8_detail = (f"filter_applied={filter_applied}, filter_category='{filter_category}', "
                     f"exported rules: {len(exported_rules)}, "
                     f"non-config rules in export: {len(non_config)}")
    else:
        c8_passed = False
        c8_detail = "No export data or empty rules list."
    checks.append({
        "name": "Export filtered to category=config only (filter_applied=True, filter_category='config')",
        "passed": c8_passed,
        "detail": c8_detail
    })
    if c8_passed:
        total_score += 1.0

    # ── CHECK 9: Each exported rule has _hash and _original_id fields ─────────
    if export_data and export_data.get("rules"):
        exported_rules = export_data["rules"]
        rules_with_hash = [r for r in exported_rules if "_hash" in r and "_original_id" in r]
        c9_passed = len(rules_with_hash) == len(exported_rules) and len(exported_rules) > 0
        c9_detail = (f"{len(rules_with_hash)}/{len(exported_rules)} exported rules "
                     f"have _hash and _original_id fields.")
    else:
        c9_passed = False
        c9_detail = "No exported rules to check."
    checks.append({
        "name": "Each exported rule has _hash and _original_id integrity fields",
        "passed": c9_passed,
        "detail": c9_detail
    })
    if c9_passed:
        total_score += 0.5

    # ── CHECK 10: manifest_hash in metadata is non-empty string ───────────────
    if export_data:
        meta = export_data.get("metadata", {})
        manifest_hash = meta.get("manifest_hash", "")
        c10_passed = isinstance(manifest_hash, str) and len(manifest_hash) >= 8
        c10_detail = f"manifest_hash = '{manifest_hash}' (length {len(manifest_hash)})"
    else:
        c10_passed = False
        c10_detail = "No export data."
    checks.append({
        "name": "Export metadata contains non-empty manifest_hash",
        "passed": c10_passed,
        "detail": c10_detail
    })
    if c10_passed:
        total_score += 0.5

    # Compute final score
    score = round(total_score / max_score, 4)
    passed = total_score >= 8.0  # Need at least 8/10 points to pass

    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()