import sys
import json
import re
from pathlib import Path

workspace = Path(sys.argv[1])

checks = []
score_parts = []

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    score_parts.append((passed, weight))

# ── Find the design document ──────────────────────────────────────────────────
candidates = list(workspace.rglob("lab_results_messaging_design.md"))
if not candidates:
    # Also accept .md files with "messaging" and "design" in the name at any depth
    candidates = [
        p for p in workspace.rglob("*.md")
        if "messaging" in p.name.lower() and "design" in p.name.lower()
        and "deprecated" not in p.name.lower()
        and "draft" not in p.name.lower()
    ]

doc_found = len(candidates) > 0
add_check(
    "design_document_exists",
    doc_found,
    f"Found document at: {candidates[0]}" if doc_found else "No file named 'lab_results_messaging_design.md' (or similar) found anywhere in workspace.",
    weight=1.0,
)

if not doc_found:
    total_weight = sum(w for _, w in score_parts)
    total_score = sum(w for p, w in score_parts if p) / total_weight if total_weight else 0
    print(json.dumps({"passed": False, "score": round(total_score, 3), "checks": checks}))
    sys.exit(0)

try:
    content = candidates[0].read_text(encoding="utf-8")
    content_lower = content.lower()
except Exception as e:
    add_check("document_readable", False, f"Could not read document: {e}", weight=1.0)
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

add_check("document_readable", True, "Document read successfully.", weight=0.5)

# ── CHECK 1: Six stages present ───────────────────────────────────────────────
stage_patterns = [
    (r"stage\s*[1i]|delivery\s+semantics", "Stage 1: Delivery Semantics"),
    (r"stage\s*[2ii]|topology|partition", "Stage 2: Topology & Partitions"),
    (r"stage\s*[3iii]|message\s+contract|envelope|schema", "Stage 3: Message Contract"),
    (r"stage\s*[4iv]|consumer|retr(y|ies)|backoff", "Stage 4: Consumers & Retries"),
    (r"stage\s*[5v]|ops|scaling|lag\s+metric|offset", "Stage 5: Ops & Scaling"),
    (r"stage\s*[6vi]|failure\s+drill|kill\s+consumer|duplicate\s+publish", "Stage 6: Failure Drills"),
]
stages_found = []
for pattern, label in stage_patterns:
    found = bool(re.search(pattern, content_lower))
    stages_found.append(found)

all_stages = all(stages_found)
missing = [stage_patterns[i][1] for i, f in enumerate(stages_found) if not f]
add_check(
    "all_six_stages_present",
    all_stages,
    "All 6 stages present." if all_stages else f"Missing stages: {missing}",
    weight=2.0,
)

# ── CHECK 2: Stage 1 exit condition — one paragraph per pipeline ──────────────
# Must have explicit per-pipeline semantic statements (at least 3 pipelines mentioned)
pipeline_keywords = ["billing", "ehr", "alert", "dispatch"]
pipelines_with_semantics = []
for kw in pipeline_keywords:
    # Find paragraphs mentioning this pipeline and a semantic term
    paragraphs = re.split(r'\n\s*\n', content)
    for para in paragraphs:
        para_lower = para.lower()
        if kw in para_lower and any(
            s in para_lower for s in ["at-least-once", "at-most-once", "idempotent", "exactly-once", "delivery semantic"]
        ):
            pipelines_with_semantics.append(kw)
            break

has_per_pipeline_semantics = len(pipelines_with_semantics) >= 2
add_check(
    "stage1_one_paragraph_per_pipeline_semantics",
    has_per_pipeline_semantics,
    f"Pipelines with explicit delivery semantics paragraph: {pipelines_with_semantics}" if has_per_pipeline_semantics
    else f"Need at least 2 pipelines with per-paragraph delivery semantics. Found: {pipelines_with_semantics}",
    weight=2.5,
)

# ── CHECK 3: Exactly-once challenged; at-least-once + idempotency recommended ─
has_exactly_once_challenge = (
    bool(re.search(r"exactly.once.*(rare|not|avoid|instead|at.least.once|idempoten)", content_lower)) or
    bool(re.search(r"(rare|not.*possible|avoid).*exactly.once", content_lower)) or
    (
        "exactly-once" in content_lower and
        "at-least-once" in content_lower and
        "idempoten" in content_lower
    )
)
add_check(
    "exactly_once_challenged_with_idempotency",
    has_exactly_once_challenge,
    "Document correctly challenges exactly-once and recommends at-least-once + idempotent handlers."
    if has_exactly_once_challenge
    else "Document must explicitly challenge 'exactly-once' as rare/impractical and recommend at-least-once + idempotent handlers.",
    weight=2.5,
)

# ── CHECK 4: Message envelope has all four required fields ────────────────────
required_envelope_fields = ["id", "type", "version", "timestamp"]
envelope_section = ""
# Try to isolate envelope/contract section
contract_match = re.search(
    r"(message\s+contract|envelope|schema)(.*?)(##|\Z)", content_lower, re.DOTALL
)
search_zone = contract_match.group(2) if contract_match else content_lower

envelope_fields_found = [f for f in required_envelope_fields if re.search(r'\b' + f + r'\b', search_zone)]
all_envelope_fields = len(envelope_fields_found) == 4
add_check(
    "message_envelope_all_four_fields",
    all_envelope_fields,
    f"Envelope fields found: {envelope_fields_found}" if all_envelope_fields
    else f"Missing envelope fields. Required: {required_envelope_fields}. Found: {envelope_fields_found}",
    weight=2.0,
)

# ── CHECK 5: Retry with exponential backoff AND jitter ────────────────────────
has_backoff = bool(re.search(r"exponential\s+backoff", content_lower))
has_jitter = bool(re.search(r"jitter", content_lower))
has_retry_backoff_jitter = has_backoff and has_jitter
add_check(
    "retry_exponential_backoff_and_jitter",
    has_retry_backoff_jitter,
    "Exponential backoff with jitter documented."
    if has_retry_backoff_jitter
    else f"Retry policy incomplete. exponential_backoff={has_backoff}, jitter={has_jitter}. Both required.",
    weight=2.0,
)

# ── CHECK 6: DLQ with reason field ───────────────────────────────────────────
has_dlq = bool(re.search(r"\bdlq\b|dead.letter", content_lower))
has_dlq_reason = bool(re.search(r"(dlq|dead.letter).{0,200}reason", content_lower, re.DOTALL)) or \
                 bool(re.search(r"reason.{0,200}(dlq|dead.letter)", content_lower, re.DOTALL))
add_check(
    "dlq_with_reason_field",
    has_dlq and has_dlq_reason,
    "DLQ with reason field documented."
    if (has_dlq and has_dlq_reason)
    else f"DLQ incomplete. dlq_mentioned={has_dlq}, reason_field={has_dlq_reason}. DLQ must explicitly include a 'reason' field.",
    weight=2.0,
)

# ── CHECK 7: Replay tooling mentioned ────────────────────────────────────────
has_replay = bool(re.search(r"\breplay\b", content_lower))
add_check(
    "replay_tooling_mentioned",
    has_replay,
    "Replay tooling documented." if has_replay else "Replay tooling not mentioned. Must document owned replay tooling for DLQ.",
    weight=1.0,
)

# ── CHECK 8: Partition key = business key (patient/entity id) ─────────────────
has_partition_business_key = bool(re.search(
    r"partition\s+key.{0,100}(patient|entity|business|user|order|id)",
    content_lower, re.DOTALL
)) or bool(re.search(
    r"(patient|entity|business|user|order|id).{0,50}partition\s+key",
    content_lower, re.DOTALL
))
add_check(
    "partition_key_equals_business_key",
    has_partition_business_key,
    "Partition key aligned to business key (patient/entity id)."
    if has_partition_business_key
    else "Partition key strategy must explicitly state it equals the business key (e.g., patient_id).",
    weight=1.5,
)

# ── CHECK 9: Lag metrics / consumer offset health ─────────────────────────────
has_lag_metrics = bool(re.search(r"lag\s+metric|consumer\s+lag|consumer\s+offset", content_lower))
add_check(
    "lag_metrics_and_offset_health",
    has_lag_metrics,
    "Lag metrics and consumer offset health documented."
    if has_lag_metrics
    else "Ops section must include lag metrics and consumer offset health monitoring.",
    weight=1.5,
)

# ── CHECK 10: Failure drills — kill consumer + duplicate publish + idempotency validation ─
has_kill_consumer = bool(re.search(r"kill\s+consumer|consumer.*mid.batch|mid.batch", content_lower))
has_dup_publish = bool(re.search(r"duplicate\s+publish|intentional.*duplic|publish.*duplic", content_lower))
has_idempotency_validation = bool(re.search(r"(validate|verif).{0,50}idempoten|idempoten.{0,50}(validate|verif)", content_lower))
failure_drills_complete = has_kill_consumer and has_dup_publish and has_idempotency_validation
add_check(
    "failure_drills_complete",
    failure_drills_complete,
    "All three failure drills documented (kill consumer, duplicate publish, idempotency validation)."
    if failure_drills_complete
    else (
        f"Failure drills incomplete. "
        f"kill_consumer_mid_batch={has_kill_consumer}, "
        f"duplicate_publish={has_dup_publish}, "
        f"idempotency_validation={has_idempotency_validation}."
    ),
    weight=2.0,
)

# ── CHECK 11: Final review checklist — all 5 items ───────────────────────────
checklist_items = [
    (r"deliver(y)?\s+semantic.{0,50}idempoten|idempoten.{0,50}deliver", "Delivery semantics + idempotency"),
    (r"partition.{0,80}order|order.{0,80}partition", "Partitioning/ordering strategy"),
    (r"version.{0,50}(message|contract|event|schema)|versioned\s+message", "Versioned message contract"),
    (r"(retry|dlq|dead.letter).{0,100}replay|replay.{0,100}(retry|dlq)", "Retry, DLQ, replay"),
    (r"lag\s+metric|consumer\s+lag|alert.{0,80}lag|lag.{0,80}alert", "Lag metrics and alerts"),
]
checklist_found = []
checklist_missing = []
for pattern, label in checklist_items:
    if re.search(pattern, content_lower, re.DOTALL):
        checklist_found.append(label)
    else:
        checklist_missing.append(label)

checklist_complete = len(checklist_missing) == 0
add_check(
    "final_review_checklist_complete",
    checklist_complete,
    f"All 5 checklist items covered: {checklist_found}"
    if checklist_complete
    else f"Checklist incomplete. Missing: {checklist_missing}",
    weight=2.0,
)

# ── CHECK 12: Transactional outbox pattern for DB+queue consistency ───────────
has_outbox = bool(re.search(r"transactional\s+outbox|outbox\s+pattern", content_lower))
add_check(
    "transactional_outbox_mentioned",
    has_outbox,
    "Transactional outbox pattern documented for DB + queue consistency."
    if has_outbox
    else "Transactional outbox pattern must be mentioned for DB + queue consistency (avoiding dual writes).",
    weight=1.5,
)

# ── CHECK 13: Payload size limits + blob reference strategy ───────────────────
has_payload_limit = bool(re.search(r"payload\s+size|size\s+limit|blob|reference.*by\s+id|store.*separately", content_lower))
add_check(
    "payload_size_limits_and_blob_reference",
    has_payload_limit,
    "Payload size limits and blob reference strategy documented."
    if has_payload_limit
    else "Message contract must include payload size limits and blob-by-reference strategy.",
    weight=1.0,
)

# ── Scoring ───────────────────────────────────────────────────────────────────
total_weight = sum(w for _, w in score_parts)
total_score = sum(w for p, w in score_parts if p) / total_weight if total_weight else 0.0

# Pass threshold: ≥75% weighted score AND critical checks must pass
critical_checks = [
    "design_document_exists",
    "all_six_stages_present",
    "stage1_one_paragraph_per_pipeline_semantics",
    "exactly_once_challenged_with_idempotency",
    "message_envelope_all_four_fields",
    "retry_exponential_backoff_and_jitter",
    "dlq_with_reason_field",
    "failure_drills_complete",
]
critical_passed = all(
    c["passed"] for c in checks if c["name"] in critical_checks
)
passed = (total_score >= 0.75) and critical_passed

print(json.dumps({
    "passed": passed,
    "score": round(total_score, 3),
    "checks": checks
}, indent=2))