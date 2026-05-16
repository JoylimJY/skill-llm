import os
import json
import random
import pathlib

random.seed(42)

workspace = pathlib.Path("/workspace")

# ── Directory structure (distractors) ──────────────────────────────────────
dirs = [
    "firmware/flight-control/src",
    "firmware/flight-control/tests",
    "firmware/flight-control/docs",
    "firmware/telemetry/src",
    "firmware/telemetry/tests",
    "infra/ci",
    "infra/deploy",
    "governance/policies",
    "governance/audit-archive/2024",
    "governance/audit-archive/2025",
    "release/staging",
    "release/prod",
    "tools/lint",
    "tools/static-analysis",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ───────────────────────────────────────────────────────
distractors = {
    "firmware/flight-control/src/actuator_ctrl.c": "/* actuator_ctrl.c - DO NOT MODIFY WITHOUT DCO SIGN-OFF */\n#include <stdint.h>\nvoid actuator_update(uint8_t ch, float cmd) { /* ... */ }\n",
    "firmware/flight-control/src/pid_loop.c": "/* pid_loop.c */\nfloat pid_compute(float err, float kp, float ki, float kd) { return 0.0f; }\n",
    "firmware/flight-control/tests/test_actuator.c": "/* unit tests for actuator_ctrl */\nvoid test_nominal_range(void) {}\nvoid test_saturation(void) {}\n",
    "firmware/flight-control/docs/DESIGN_NOTES.md": "# Design Notes\n\nSee ICD-FC-002 for interface contract.\n",
    "firmware/telemetry/src/downlink.c": "/* downlink.c */\nvoid send_frame(const uint8_t *buf, size_t len) {}\n",
    "firmware/telemetry/tests/test_downlink.c": "/* downlink unit tests */\nvoid test_frame_boundary(void) {}\n",
    "infra/ci/pipeline.yaml": "stages:\n  - lint\n  - build\n  - test\n  - governance-gate\n",
    "infra/deploy/release_manifest.json": json.dumps({
        "version": "2.7.1",
        "target": "FC-BOARD-REV3",
        "signed": False,
        "promoted": False
    }, indent=2),
    "governance/policies/merge_policy_v2.txt": (
        "POLICY: All PRs touching security-classified modules require >=3 reviewers.\n"
        "POLICY: Test coverage must not regress below 85%.\n"
        "POLICY: Any BLOCK decision freezes the release branch.\n"
    ),
    "governance/audit-archive/2024/decision_20241112.json": json.dumps({
        "pr_id": "PR-1041",
        "decision": "MERGE",
        "timestamp": "2024-11-12T09:14:33Z",
        "votes": [{"voter": "alice", "vote": "approve"}, {"voter": "bob", "vote": "approve"}]
    }, indent=2),
    "governance/audit-archive/2025/decision_20250103.json": json.dumps({
        "pr_id": "PR-1187",
        "decision": "REVISE",
        "timestamp": "2025-01-03T14:22:10Z",
        "votes": [{"voter": "alice", "vote": "approve"}, {"voter": "carol", "vote": "reject"}]
    }, indent=2),
    "release/staging/changelog_2.8.0-rc1.md": "## 2.8.0-rc1\n- Added adaptive gain scheduling\n- Security patch CVE-2025-00123\n",
    "tools/lint/flightlint.sh": "#!/bin/bash\necho 'linting...'\n",
    "tools/static-analysis/cppcheck_wrapper.sh": "#!/bin/bash\ncppcheck --enable=all $@\n",
}

for rel_path, content in distractors.items():
    p = workspace / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

# ── The messy PR input that the agent must clean up and use ────────────────
# Intentionally incomplete/messy — agent must read SKILL.md to know the
# correct schema and required fields for external_agent mode.
# NOTE: This is NOT a valid input.json for the tool. The agent must:
#   1. Understand the tool's expected schema
#   2. Craft a proper input.json with external_votes[] for external_agent mode
#   3. Set env vars and invoke the tool correctly

raw_pr_summary = {
    "_note": "RAW PR SUMMARY — needs to be turned into a governance review input",
    "pr_reference": "PR-2041",
    "title": "Integrate adaptive gain scheduling into flight-control PID loop",
    "description": (
        "This PR introduces adaptive gain scheduling to pid_loop.c and actuator_ctrl.c. "
        "It includes a new security boundary check for command saturation (security-sensitive). "
        "All existing unit tests pass. Coverage at 88%. "
        "Three engineers have reviewed and two have approved, one requests minor revisions."
    ),
    "changed_files": [
        "firmware/flight-control/src/pid_loop.c",
        "firmware/flight-control/src/actuator_ctrl.c",
        "firmware/flight-control/tests/test_actuator.c"
    ],
    "ci_status": "passing",
    "security_flag": True,
    "test_coverage_pct": 88,
    "reviewers": [
        {"name": "alice", "role": "lead-engineer", "vote": "approve"},
        {"name": "bob",   "role": "safety-officer", "vote": "approve"},
        {"name": "carol", "role": "security-reviewer", "vote": "revise"}
    ],
    "_raw_notes": "Board needs a formal decision record and audit artifact. Use the governance toolchain."
}

(workspace / "governance" / "pr_2041_raw_summary.json").write_text(
    json.dumps(raw_pr_summary, indent=2)
)

# ── Partial / broken package.json to mislead ─────────────────────────────
broken_pkg = {
    "name": "flight-governance-runner",
    "version": "0.0.1",
    "_comment": "This is not a working setup — dependencies are missing",
    "scripts": {
        "review": "node run.js"
    }
}
(workspace / "package.json").write_text(json.dumps(broken_pkg, indent=2))

print("Workspace initialized.")
print("Files created:")
for p in sorted(workspace.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(workspace)}")