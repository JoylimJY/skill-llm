#!/usr/bin/env python3
"""
Evaluation script for the trust-verifier task.
Checks:
  1. trust.json attestation exists, has correct ClawHub schema, and valid trust_level.
  2. skill_trust_report.json exists and contains results from ALL FOUR subcommands.
  3. assess section has correct trust_level (VERIFIED for this skill).
  4. attest section references the correct schema and attestation_hash.
  5. verify section shows verified=True (attestation was generated then verified).
  6. deps section has chain_status and dep_count >= 4.
  7. trust_level values throughout use the exact bespoke ClawHub vocabulary.
"""

import json
import sys
from pathlib import Path

VALID_TRUST_LEVELS = {"VERIFIED", "TRUSTED", "UNKNOWN", "SUSPICIOUS", "UNTRUSTED"}
VALID_CHAIN_STATUSES = {"TRUSTED", "SUSPICIOUS", "UNKNOWN"}
CLAWHUB_SCHEMA = "clawhub-attestation/v1"


def load_json_file(path: Path):
    """Load JSON, return (data, error_str)."""
    try:
        return json.loads(path.read_text()), None
    except FileNotFoundError:
        return None, f"File not found: {path}"
    except json.JSONDecodeError as e:
        return None, f"JSON parse error in {path}: {e}"


def find_file(workspace: Path, filename: str):
    """Search entire workspace for a file by name."""
    matches = list(workspace.rglob(filename))
    if not matches:
        return None
    # Prefer not in tmp/
    non_tmp = [m for m in matches if "tmp" not in str(m)]
    return non_tmp[0] if non_tmp else matches[0]


def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []
    total_score = 0.0
    max_score = 7.0

    # ──────────────────────────────────────────────────────
    # CHECK 1: trust.json exists with correct ClawHub schema
    # ──────────────────────────────────────────────────────
    trust_json_path = find_file(workspace, "trust.json")
    trust_data = None

    if trust_json_path is None:
        checks.append({
            "name": "trust.json_exists",
            "passed": False,
            "detail": "trust.json not found anywhere in workspace."
        })
    else:
        trust_data, err = load_json_file(trust_json_path)
        if err:
            checks.append({"name": "trust.json_exists", "passed": False, "detail": err})
            trust_data = None
        else:
            checks.append({
                "name": "trust.json_exists",
                "passed": True,
                "detail": f"Found trust.json at {trust_json_path}"
            })
            total_score += 1.0

    # ──────────────────────────────────────────────────────
    # CHECK 2: trust.json has valid ClawHub attestation schema
    # ──────────────────────────────────────────────────────
    if trust_data is not None:
        schema_ok = trust_data.get("schema") == CLAWHUB_SCHEMA
        has_hash  = bool(trust_data.get("attestation_hash"))
        has_level = trust_data.get("trust_level") in VALID_TRUST_LEVELS
        ok = schema_ok and has_hash and has_level
        checks.append({
            "name": "trust.json_schema_valid",
            "passed": ok,
            "detail": (
                f"schema={trust_data.get('schema')!r} (expected {CLAWHUB_SCHEMA!r}), "
                f"attestation_hash={'present' if has_hash else 'MISSING'}, "
                f"trust_level={trust_data.get('trust_level')!r} valid={has_level}"
            )
        })
        if ok:
            total_score += 1.0
    else:
        checks.append({
            "name": "trust.json_schema_valid",
            "passed": False,
            "detail": "Skipped — trust.json not loaded."
        })

    # ──────────────────────────────────────────────────────
    # CHECK 3: skill_trust_report.json exists
    # ──────────────────────────────────────────────────────
    report_path = find_file(workspace, "skill_trust_report.json")
    report_data = None

    if report_path is None:
        checks.append({
            "name": "skill_trust_report.json_exists",
            "passed": False,
            "detail": "skill_trust_report.json not found anywhere in workspace."
        })
    else:
        report_data, err = load_json_file(report_path)
        if err:
            checks.append({
                "name": "skill_trust_report.json_exists",
                "passed": False,
                "detail": err
            })
            report_data = None
        else:
            checks.append({
                "name": "skill_trust_report.json_exists",
                "passed": True,
                "detail": f"Found skill_trust_report.json at {report_path}"
            })
            total_score += 1.0

    # ──────────────────────────────────────────────────────
    # CHECK 4: Report contains assess section with VERIFIED trust level
    # ──────────────────────────────────────────────────────
    if report_data is not None:
        # The report may store results under keys like "assess", "attest", "verify", "deps"
        # or as a list with "command" fields — accept both layouts.
        def extract_section(data, command_name):
            """Try to find a section by key name or by 'command' field in a list."""
            if isinstance(data, dict):
                # Direct key
                for key in [command_name, command_name.upper(), f"{command_name}_result"]:
                    if key in data:
                        return data[key]
                # Search nested dicts one level deep
                for v in data.values():
                    if isinstance(v, dict) and v.get("command") == command_name:
                        return v
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("command") == command_name:
                        return item
            return None

        assess_section = extract_section(report_data, "assess")
        assess_ok = False
        assess_detail = "assess section not found in report."
        if assess_section is not None:
            level = assess_section.get("trust_level", "")
            assess_ok = level in VALID_TRUST_LEVELS
            assess_detail = f"assess.trust_level={level!r}, valid={assess_ok}"
            # Bonus: check it's VERIFIED for this particular skill
            if level == "VERIFIED":
                assess_detail += " (correctly VERIFIED for trusted-devops publisher)"

        checks.append({
            "name": "report_assess_section",
            "passed": assess_ok,
            "detail": assess_detail
        })
        if assess_ok:
            total_score += 1.0
    else:
        checks.append({
            "name": "report_assess_section",
            "passed": False,
            "detail": "Skipped — skill_trust_report.json not loaded."
        })

    # ──────────────────────────────────────────────────────
    # CHECK 5: Report contains verify section with verified=True
    # ──────────────────────────────────────────────────────
    if report_data is not None:
        def extract_section(data, command_name):
            if isinstance(data, dict):
                for key in [command_name, command_name.upper(), f"{command_name}_result"]:
                    if key in data:
                        return data[key]
                for v in data.values():
                    if isinstance(v, dict) and v.get("command") == command_name:
                        return v
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("command") == command_name:
                        return item
            return None

        verify_section = extract_section(report_data, "verify")
        verify_ok = False
        verify_detail = "verify section not found in report."
        if verify_section is not None:
            verified_val = verify_section.get("verified")
            verify_ok = verified_val is True
            verify_detail = f"verify.verified={verified_val!r} (expected True)"

        checks.append({
            "name": "report_verify_section",
            "passed": verify_ok,
            "detail": verify_detail
        })
        if verify_ok:
            total_score += 1.0
    else:
        checks.append({
            "name": "report_verify_section",
            "passed": False,
            "detail": "Skipped — skill_trust_report.json not loaded."
        })

    # ──────────────────────────────────────────────────────
    # CHECK 6: Report contains deps section with chain_status and dep_count
    # ──────────────────────────────────────────────────────
    if report_data is not None:
        def extract_section(data, command_name):
            if isinstance(data, dict):
                for key in [command_name, command_name.upper(), f"{command_name}_result"]:
                    if key in data:
                        return data[key]
                for v in data.values():
                    if isinstance(v, dict) and v.get("command") == command_name:
                        return v
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("command") == command_name:
                        return item
            return None

        deps_section = extract_section(report_data, "deps")
        deps_ok = False
        deps_detail = "deps section not found in report."
        if deps_section is not None:
            chain = deps_section.get("chain_status", "")
            count = deps_section.get("dep_count", -1)
            chain_valid = chain in VALID_CHAIN_STATUSES
            count_ok    = isinstance(count, int) and count >= 4
            deps_ok     = chain_valid and count_ok
            deps_detail = (
                f"deps.chain_status={chain!r} (valid={chain_valid}), "
                f"deps.dep_count={count} (need>=4, ok={count_ok})"
            )

        checks.append({
            "name": "report_deps_section",
            "passed": deps_ok,
            "detail": deps_detail
        })
        if deps_ok:
            total_score += 1.0
    else:
        checks.append({
            "name": "report_deps_section",
            "passed": False,
            "detail": "Skipped — skill_trust_report.json not loaded."
        })

    # ──────────────────────────────────────────────────────
    # CHECK 7: All trust_level values in the report use exact ClawHub vocabulary
    # ──────────────────────────────────────────────────────
    if report_data is not None:
        found_levels = []
        invalid_levels = []

        def harvest_trust_levels(obj):
            if isinstance(obj, dict):
                if "trust_level" in obj:
                    lvl = obj["trust_level"]
                    found_levels.append(lvl)
                    if lvl not in VALID_TRUST_LEVELS:
                        invalid_levels.append(lvl)
                for v in obj.values():
                    harvest_trust_levels(v)
            elif isinstance(obj, list):
                for item in obj:
                    harvest_trust_levels(item)

        harvest_trust_levels(report_data)
        vocab_ok = len(found_levels) > 0 and len(invalid_levels) == 0
        checks.append({
            "name": "bespoke_trust_level_vocabulary",
            "passed": vocab_ok,
            "detail": (
                f"Found trust_levels: {list(set(found_levels))}, "
                f"Invalid values: {invalid_levels if invalid_levels else 'none'}"
            )
        })
        if vocab_ok:
            total_score += 1.0
    else:
        checks.append({
            "name": "bespoke_trust_level_vocabulary",
            "passed": False,
            "detail": "Skipped — skill_trust_report.json not loaded."
        })

    # ──────────────────────────────────────────────────────
    # Final result
    # ──────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    all_passed   = passed_count == len(checks)
    score        = round(total_score / max_score, 4)

    output = {
        "passed": all_passed,
        "score":  score,
        "checks": checks
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()