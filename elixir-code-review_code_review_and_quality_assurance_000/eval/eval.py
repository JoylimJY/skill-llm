import sys
import json
import re
from pathlib import Path

workspace = sys.argv[1]

checks = []
score = 0.0

# ── Helper ────────────────────────────────────────────────────────────────────
def find_review_file(workspace):
    """Find review_findings.json anywhere under workspace."""
    matches = list(Path(workspace).rglob("review_findings.json"))
    if matches:
        return matches[0]
    return None


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def text_contains_any(text, keywords, case_sensitive=False):
    if not case_sensitive:
        text = text.lower()
        keywords = [k.lower() for k in keywords]
    return any(k in text for k in keywords)


def findings_as_text(data):
    """Return a single lowercase string of the entire JSON content for fuzzy matching."""
    return json.dumps(data).lower()


# ── Locate the report ────────────────────────────────────────────────────────
report_path = find_review_file(workspace)

if report_path is None:
    result = {
        "passed": False,
        "score": 0.0,
        "checks": [
            {
                "name": "report_exists",
                "passed": False,
                "detail": "review_findings.json not found anywhere under workspace."
            }
        ]
    }
    print(json.dumps(result))
    sys.exit(0)

checks.append({
    "name": "report_exists",
    "passed": True,
    "detail": f"Found at {report_path}"
})

try:
    data = load_json(report_path)
    raw_text = findings_as_text(data)
    checks.append({
        "name": "report_parseable",
        "passed": True,
        "detail": "JSON parsed successfully."
    })
except Exception as e:
    checks.append({
        "name": "report_parseable",
        "passed": False,
        "detail": f"JSON parse error: {e}"
    })
    result = {
        "passed": False,
        "score": 0.0,
        "checks": checks
    }
    print(json.dumps(result))
    sys.exit(0)

# ────────────────────────────────────────────────────────────────────────────
# VIOLATION CHECKS  (each worth 1 point)
# ────────────────────────────────────────────────────────────────────────────

# V1: expensive sync work in init/1 — should use handle_continue
v1_keywords = ["handle_continue", "expensive", "init", "blocking", "synchronous", "defers", "load_full_product_catalog"]
v1_passed = text_contains_any(raw_text, ["handle_continue"]) and text_contains_any(raw_text, ["init"])
checks.append({
    "name": "V1_expensive_init_should_use_handle_continue",
    "passed": v1_passed,
    "detail": "Report must flag that init/1 does expensive synchronous work and recommend handle_continue." if not v1_passed else "Correctly flagged."
})

# V2: blocking HTTP call inside handle_call — should use Task
v2_passed = (
    text_contains_any(raw_text, ["blocking", "httpclient", "http"]) and
    text_contains_any(raw_text, ["handle_call", "callback"]) and
    text_contains_any(raw_text, ["task", "async", "noreply"])
)
checks.append({
    "name": "V2_blocking_call_in_handle_call",
    "passed": v2_passed,
    "detail": "Report must flag the blocking HTTPClient.get! in handle_call and recommend Task.async or similar." if not v2_passed else "Correctly flagged."
})

# V3: fire-and-forget notification using call instead of cast
v3_passed = (
    text_contains_any(raw_text, ["cast", "fire-and-forget", "fire and forget", "async", "asynchronous"]) and
    text_contains_any(raw_text, ["cancel_order", "notify_cancellation", "call"])
)
checks.append({
    "name": "V3_should_use_cast_not_call_for_notification",
    "passed": v3_passed,
    "detail": "Report must flag that notify_cancellation is fire-and-forget and should use GenServer.cast, not call." if not v3_passed else "Correctly flagged."
})

# V4: with clause missing else handler
v4_passed = (
    text_contains_any(raw_text, ["with"]) and
    text_contains_any(raw_text, ["else", "error handling", "unhandled", "missing else"])
)
checks.append({
    "name": "V4_with_clause_missing_else",
    "passed": v4_passed,
    "detail": "Report must flag the with clause in submit_order/1 for missing else handling." if not v4_passed else "Correctly flagged."
})

# V5: destructuring in body, not function head
v5_passed = (
    text_contains_any(raw_text, ["destructur"]) and
    text_contains_any(raw_text, ["head", "function head", "process_refund", "body"])
)
checks.append({
    "name": "V5_destructuring_in_body_not_head",
    "passed": v5_passed,
    "detail": "Report must flag process_refund/1 for destructuring payment_info in body instead of function head." if not v5_passed else "Correctly flagged."
})

# V6: @moduledoc false on a genuinely public module
v6_passed = (
    text_contains_any(raw_text, ["moduledoc"]) and
    text_contains_any(raw_text, ["false"]) and
    text_contains_any(raw_text, ["public", "processor", "ecommerce.order.processor", "genuinely"])
)
checks.append({
    "name": "V6_moduledoc_false_on_public_module",
    "passed": v6_passed,
    "detail": "Report must flag @moduledoc false on Ecommerce.Order.Processor which is a genuinely public module." if not v6_passed else "Correctly flagged."
})

# V7: public submit_order/1 missing @doc and @spec
v7_passed = (
    text_contains_any(raw_text, ["submit_order"]) and
    text_contains_any(raw_text, ["@doc", "doc", "@spec", "spec", "documentation", "missing"])
)
checks.append({
    "name": "V7_submit_order_missing_doc_and_spec",
    "passed": v7_passed,
    "detail": "Report must flag that public function submit_order/1 is missing @doc and @spec." if not v7_passed else "Correctly flagged."
})

# V8: doctest on side-effectful cancel_order/1
v8_passed = (
    text_contains_any(raw_text, ["doctest", "doc test"]) and
    text_contains_any(raw_text, ["cancel_order", "side effect", "side-effect", "unpredictable", "pure"])
)
checks.append({
    "name": "V8_doctest_on_side_effectful_function",
    "passed": v8_passed,
    "detail": "Report must flag the doctest on cancel_order/1 which is a side-effectful function (not pure/deterministic)." if not v8_passed else "Correctly flagged."
})

# ────────────────────────────────────────────────────────────────────────────
# NON-VIOLATION CHECKS (must NOT be flagged — negative points if flagged)
# ────────────────────────────────────────────────────────────────────────────

# NV1: single |> pipe in normalize_sku — must NOT be flagged as a violation
# If the text says normalize_sku AND (bad OR violation OR wrong OR issue) near pipe, that's a false positive
nv1_false_positive = (
    text_contains_any(raw_text, ["normalize_sku"]) and
    text_contains_any(raw_text, ["single pipe violation", "single |> violation", "pipe violation"])
)
nv1_passed = not nv1_false_positive
checks.append({
    "name": "NV1_single_pipe_must_not_be_flagged",
    "passed": nv1_passed,
    "detail": "Single-pipe chains are a valid readability choice per the skill. Flagging normalize_sku's single pipe is a false positive." if not nv1_passed else "Correctly not flagged as violation."
})

# NV2: @doc false on callback handle_call/handle_cast — must NOT be flagged
# Look for flagging @doc false on the callbacks
nv2_false_positive = (
    text_contains_any(raw_text, ["@doc false", "doc false"]) and
    text_contains_any(raw_text, ["handle_call", "handle_cast", "callback"]) and
    text_contains_any(raw_text, ["violation", "issue", "problem", "should not", "incorrect", "flag"])
)
nv2_passed = not nv2_false_positive
checks.append({
    "name": "NV2_doc_false_on_callbacks_must_not_be_flagged",
    "passed": nv2_passed,
    "detail": "@doc false on callback implementations is explicitly valid per the skill. Should not be flagged." if not nv2_passed else "Correctly not flagged as violation."
})

# NV3: private validate_order/1 without @spec — must NOT be flagged
nv3_false_positive = (
    text_contains_any(raw_text, ["validate_order", "private_helper", "load_full_product_catalog"]) and
    text_contains_any(raw_text, ["missing @spec", "missing spec", "no @spec", "no spec"]) and
    text_contains_any(raw_text, ["private", "defp"])
)
nv3_passed = not nv3_false_positive
checks.append({
    "name": "NV3_private_function_without_spec_must_not_be_flagged",
    "passed": nv3_passed,
    "detail": "@spec is optional for private functions per the skill. Should not flag missing @spec on defp." if not nv3_passed else "Correctly not flagged as violation."
})

# ────────────────────────────────────────────────────────────────────────────
# SCORING
# ────────────────────────────────────────────────────────────────────────────
# Violations: 8 checks, each worth 1 point = 8 points
# Non-violations: 3 checks, each worth 1 point = 3 points (penalty if wrong)
# Total possible: 11 points

violation_check_names = ["V1_", "V2_", "V3_", "V4_", "V5_", "V6_", "V7_", "V8_"]
non_violation_check_names = ["NV1_", "NV2_", "NV3_"]

violation_score = sum(1 for c in checks if any(c["name"].startswith(v) for v in violation_check_names) and c["passed"])
nv_score = sum(1 for c in checks if any(c["name"].startswith(nv) for nv in non_violation_check_names) and c["passed"])

total_possible = 11
raw_score = violation_score + nv_score
final_score = round(raw_score / total_possible, 3)

# Must pass at least 6/8 violations AND all 3 non-violations to be considered passing
overall_passed = (violation_score >= 6) and (nv_score == 3)

result = {
    "passed": overall_passed,
    "score": final_score,
    "checks": checks,
    "summary": {
        "violation_checks_passed": f"{violation_score}/8",
        "non_violation_checks_passed": f"{nv_score}/3",
        "raw_score": f"{raw_score}/11"
    }
}

print(json.dumps(result, indent=2))