#!/usr/bin/env python3
"""
Evaluation script for the dr-context-pipeline compliance task.
Checks that the agent:
  1. Ran install_pipeline.py (context_pipeline/ directory with required files exists).
  2. Produced retrieval_bundle_query1.json and retrieval_bundle_query2.json valid per schema.
  3. Produced context_pack_query1.json and context_pack_query2.json valid per schema.
  4. Snippet IDs in all bundles follow S1, S2, ... pattern (deterministic ordering).
  5. Context Pack `sources` contain ONLY snippet IDs (Sn pattern) — the key proprietary trap.
  6. Router routing is correct (task_type matches expected for each query).
  7. Caps are correct per router.yml.
  8. Patched AGENTS.md with a "Context Pipeline" section.
"""

import sys
import json
import re
from pathlib import Path

try:
    import jsonschema
except ImportError:
    jsonschema = None

def find_file(workspace: Path, pattern: str):
    """Search for a file by name pattern anywhere under workspace."""
    results = list(workspace.rglob(pattern))
    return results[0] if results else None

def load_json(path):
    if path is None or not path.exists():
        return None, f"File not found: {path}"
    try:
        return json.loads(path.read_text()), None
    except Exception as e:
        return None, f"JSON parse error in {path}: {e}"

def validate_schema(instance, schema):
    if jsonschema is None:
        return True, "jsonschema not installed, skipping validation"
    try:
        jsonschema.validate(instance=instance, schema=schema)
        return True, "OK"
    except jsonschema.ValidationError as e:
        return False, str(e.message)
    except Exception as e:
        return False, str(e)

def check_snippet_ids(snippets: list) -> tuple:
    """Return (passed, detail) — all snippet ids must match S[n] sequentially starting at S1."""
    if not snippets:
        return False, "No snippets found"
    ids = [s.get("id", "") for s in snippets]
    pattern = re.compile(r"^S[0-9]+$")
    bad = [i for i in ids if not pattern.match(i)]
    if bad:
        return False, f"Non-conforming IDs: {bad}"
    # Check sequential from S1
    expected = [f"S{i+1}" for i in range(len(ids))]
    if ids != expected:
        return False, f"IDs not sequential from S1: got {ids}, expected {expected}"
    return True, f"IDs {ids} are sequential and correctly formatted"

def check_context_pack_sources(sources: list, bundle_ids: list) -> tuple:
    """Sources must be snippet ID strings matching S[n], and must exist in bundle."""
    if not sources:
        return False, "Empty sources list"
    pattern = re.compile(r"^S[0-9]+$")
    bad_format = [s for s in sources if not pattern.match(str(s))]
    if bad_format:
        return False, f"Sources contain non-snippet-ID values (must be Sn only): {bad_format}"
    # All sources must reference valid bundle IDs
    unknown = [s for s in sources if s not in bundle_ids]
    if unknown:
        return False, f"Sources reference IDs not in bundle: {unknown}"
    return True, f"Sources {sources} are all valid snippet IDs"

def check_deterministic_ordering(snippets: list) -> tuple:
    """Verify snippets are ordered by source_file asc, then snippet_key asc."""
    if not snippets:
        return False, "No snippets"
    order_keys = [(s.get("source_file", ""), s.get("snippet_key", "")) for s in snippets]
    if order_keys == sorted(order_keys):
        return True, f"Deterministic ordering correct: {order_keys}"
    else:
        return False, f"Ordering incorrect. Got: {order_keys}, expected sorted: {sorted(order_keys)}"

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []
    total_score = 0.0
    max_score = 0.0

    # Load schemas
    schema_rb_path = workspace / "skills" / "dr-context-pipeline" / "references" / "schemas" / "retrieval_bundle.schema.json"
    schema_cp_path = workspace / "skills" / "dr-context-pipeline" / "references" / "schemas" / "context_pack.schema.json"
    schema_rb, err = load_json(schema_rb_path)
    schema_cp, err2 = load_json(schema_cp_path)

    # ── CHECK 1: install_pipeline ran (context_pipeline/ dir exists with references/) ──
    max_score += 1.0
    cp_dir = workspace / "context_pipeline"
    cp_refs = cp_dir / "references"
    install_ok = cp_dir.exists() and cp_refs.exists() and (cp_refs / "router.yml").exists()
    checks.append({
        "name": "install_pipeline_ran",
        "passed": install_ok,
        "detail": f"context_pipeline/references/router.yml exists: {install_ok}"
    })
    if install_ok:
        total_score += 1.0

    # ── CHECK 2: AGENTS.md patched with Context Pipeline section ──
    max_score += 1.0
    agents_md = workspace / "AGENTS.md"
    agents_ok = False
    agents_detail = "AGENTS.md not found"
    if agents_md.exists():
        content = agents_md.read_text()
        if re.search(r"context.{0,10}pipeline", content, re.IGNORECASE):
            agents_ok = True
            agents_detail = "AGENTS.md contains 'Context Pipeline' section"
        else:
            agents_detail = "AGENTS.md does not contain a Context Pipeline section"
    checks.append({
        "name": "agents_md_patched",
        "passed": agents_ok,
        "detail": agents_detail
    })
    if agents_ok:
        total_score += 1.0

    # ── CHECK 3: retrieval_bundle_query1.json exists and is schema-valid ──
    max_score += 1.5
    rb1_path = find_file(workspace, "retrieval_bundle_query1.json")
    rb1, rb1_err = load_json(rb1_path)
    if rb1_err:
        checks.append({
            "name": "retrieval_bundle_query1_exists_valid",
            "passed": False,
            "detail": rb1_err
        })
    else:
        if schema_rb and jsonschema:
            valid, vmsg = validate_schema(rb1, schema_rb)
        else:
            # Manual check for required fields
            req = ["query", "task_type", "caps", "snippets", "timestamp"]
            missing = [r for r in req if r not in rb1]
            valid = len(missing) == 0
            vmsg = "OK" if valid else f"Missing fields: {missing}"
        checks.append({
            "name": "retrieval_bundle_query1_exists_valid",
            "passed": valid,
            "detail": vmsg
        })
        if valid:
            total_score += 1.5

    # ── CHECK 4: retrieval_bundle_query1 has correct task_type and caps (transaction_review, aml+reporting) ──
    max_score += 1.0
    if rb1:
        tt = rb1.get("task_type", "")
        caps = rb1.get("caps", [])
        tt_ok = tt == "transaction_review"
        caps_ok = "aml" in caps and "reporting" in caps
        route_ok = tt_ok and caps_ok
        checks.append({
            "name": "retrieval_bundle_query1_routing",
            "passed": route_ok,
            "detail": f"task_type={tt} (expected transaction_review), caps={caps} (expected aml+reporting)"
        })
        if route_ok:
            total_score += 1.0
    else:
        checks.append({"name": "retrieval_bundle_query1_routing", "passed": False,
                       "detail": "Bundle missing — cannot check routing"})

    # ── CHECK 5: Query1 bundle has deterministic snippet IDs ──
    max_score += 1.0
    if rb1 and rb1.get("snippets"):
        id_ok, id_detail = check_snippet_ids(rb1["snippets"])
        ord_ok, ord_detail = check_deterministic_ordering(rb1["snippets"])
        combined_ok = id_ok and ord_ok
        checks.append({
            "name": "retrieval_bundle_query1_deterministic_ids",
            "passed": combined_ok,
            "detail": f"IDs: {id_detail} | Ordering: {ord_detail}"
        })
        if combined_ok:
            total_score += 1.0
    else:
        checks.append({"name": "retrieval_bundle_query1_deterministic_ids", "passed": False,
                       "detail": "No snippets in bundle"})

    # ── CHECK 6: context_pack_query1.json exists and is schema-valid ──
    max_score += 1.5
    cp1_path = find_file(workspace, "context_pack_query1.json")
    cp1, cp1_err = load_json(cp1_path)
    if cp1_err:
        checks.append({
            "name": "context_pack_query1_exists_valid",
            "passed": False,
            "detail": cp1_err
        })
    else:
        if schema_cp and jsonschema:
            valid, vmsg = validate_schema(cp1, schema_cp)
        else:
            req = ["query", "task_type", "summary", "sources", "token_estimate", "lint_passed", "timestamp"]
            missing = [r for r in req if r not in cp1]
            valid = len(missing) == 0
            vmsg = "OK" if valid else f"Missing fields: {missing}"
        checks.append({
            "name": "context_pack_query1_exists_valid",
            "passed": valid,
            "detail": vmsg
        })
        if valid:
            total_score += 1.5

    # ── CHECK 7: context_pack_query1 sources are ONLY snippet IDs (the proprietary trap) ──
    max_score += 2.0
    if cp1 and rb1:
        bundle_ids = [s.get("id", "") for s in rb1.get("snippets", [])]
        sources = cp1.get("sources", [])
        src_ok, src_detail = check_context_pack_sources(sources, bundle_ids)
        checks.append({
            "name": "context_pack_query1_sources_are_snippet_ids",
            "passed": src_ok,
            "detail": src_detail
        })
        if src_ok:
            total_score += 2.0
    else:
        checks.append({"name": "context_pack_query1_sources_are_snippet_ids", "passed": False,
                       "detail": "Cannot check — bundle or context pack missing"})

    # ── CHECK 8: retrieval_bundle_query2.json exists and is schema-valid ──
    max_score += 1.5
    rb2_path = find_file(workspace, "retrieval_bundle_query2.json")
    rb2, rb2_err = load_json(rb2_path)
    if rb2_err:
        checks.append({
            "name": "retrieval_bundle_query2_exists_valid",
            "passed": False,
            "detail": rb2_err
        })
    else:
        if schema_rb and jsonschema:
            valid, vmsg = validate_schema(rb2, schema_rb)
        else:
            req = ["query", "task_type", "caps", "snippets", "timestamp"]
            missing = [r for r in req if r not in rb2]
            valid = len(missing) == 0
            vmsg = "OK" if valid else f"Missing fields: {missing}"
        checks.append({
            "name": "retrieval_bundle_query2_exists_valid",
            "passed": valid,
            "detail": vmsg
        })
        if valid:
            total_score += 1.5

    # ── CHECK 9: retrieval_bundle_query2 routing: customer_onboarding, kyc+aml ──
    max_score += 1.0
    if rb2:
        tt = rb2.get("task_type", "")
        caps = rb2.get("caps", [])
        tt_ok = tt == "customer_onboarding"
        caps_ok = "kyc" in caps and "aml" in caps
        route_ok = tt_ok and caps_ok
        checks.append({
            "name": "retrieval_bundle_query2_routing",
            "passed": route_ok,
            "detail": f"task_type={tt} (expected customer_onboarding), caps={caps} (expected kyc+aml)"
        })
        if route_ok:
            total_score += 1.0
    else:
        checks.append({"name": "retrieval_bundle_query2_routing", "passed": False,
                       "detail": "Bundle missing — cannot check routing"})

    # ── CHECK 10: Query2 bundle has deterministic snippet IDs ──
    max_score += 1.0
    if rb2 and rb2.get("snippets"):
        id_ok, id_detail = check_snippet_ids(rb2["snippets"])
        ord_ok, ord_detail = check_deterministic_ordering(rb2["snippets"])
        combined_ok = id_ok and ord_ok
        checks.append({
            "name": "retrieval_bundle_query2_deterministic_ids",
            "passed": combined_ok,
            "detail": f"IDs: {id_detail} | Ordering: {ord_detail}"
        })
        if combined_ok:
            total_score += 1.0
    else:
        checks.append({"name": "retrieval_bundle_query2_deterministic_ids", "passed": False,
                       "detail": "No snippets in bundle"})

    # ── CHECK 11: context_pack_query2.json exists and schema-valid ──
    max_score += 1.5
    cp2_path = find_file(workspace, "context_pack_query2.json")
    cp2, cp2_err = load_json(cp2_path)
    if cp2_err:
        checks.append({
            "name": "context_pack_query2_exists_valid",
            "passed": False,
            "detail": cp2_err
        })
    else:
        if schema_cp and jsonschema:
            valid, vmsg = validate_schema(cp2, schema_cp)
        else:
            req = ["query", "task_type", "summary", "sources", "token_estimate", "lint_passed", "timestamp"]
            missing = [r for r in req if r not in cp2]
            valid = len(missing) == 0
            vmsg = "OK" if valid else f"Missing fields: {missing}"
        checks.append({
            "name": "context_pack_query2_exists_valid",
            "passed": valid,
            "detail": vmsg
        })
        if valid:
            total_score += 1.5

    # ── CHECK 12: context_pack_query2 sources are ONLY snippet IDs ──
    max_score += 2.0
    if cp2 and rb2:
        bundle_ids = [s.get("id", "") for s in rb2.get("snippets", [])]
        sources = cp2.get("sources", [])
        src_ok, src_detail = check_context_pack_sources(sources, bundle_ids)
        checks.append({
            "name": "context_pack_query2_sources_are_snippet_ids",
            "passed": src_ok,
            "detail": src_detail
        })
        if src_ok:
            total_score += 2.0
    else:
        checks.append({"name": "context_pack_query2_sources_are_snippet_ids", "passed": False,
                       "detail": "Cannot check — bundle or context pack missing"})

    # ── CHECK 13: validate_pipeline.py passes (context_pipeline must be valid) ──
    max_score += 1.0
    import subprocess
    try:
        result = subprocess.run(
            ["python3",
             str(workspace / "skills" / "dr-context-pipeline" / "scripts" / "validate_pipeline.py"),
             "--context-root", str(workspace / "context_pipeline")],
            capture_output=True, text=True, timeout=30
        )
        val_ok = result.returncode == 0 and "PASS" in result.stdout
        checks.append({
            "name": "validate_pipeline_passes",
            "passed": val_ok,
            "detail": result.stdout.strip() or result.stderr.strip()
        })
        if val_ok:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "validate_pipeline_passes", "passed": False,
                       "detail": f"Error running validate_pipeline.py: {e}"})

    # ── CHECK 14: memory_watchdog.py returns OK ──
    max_score += 1.0
    try:
        result = subprocess.run(
            ["python3",
             str(workspace / "skills" / "dr-context-pipeline" / "scripts" / "memory_watchdog.py"),
             "--freshness-minutes", "240", "--min-bytes", "200",
             "--memory-path", str(workspace / "memory")],
            capture_output=True, text=True, timeout=30
        )
        try:
            wd_json = json.loads(result.stdout)
            wd_ok = wd_json.get("status") == "OK"
            wd_detail = f"status={wd_json.get('status')}, issues={wd_json.get('issues', [])}"
        except Exception:
            wd_ok = result.returncode == 0
            wd_detail = result.stdout[:200]
        checks.append({
            "name": "memory_watchdog_ok",
            "passed": wd_ok,
            "detail": wd_detail
        })
        if wd_ok:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "memory_watchdog_ok", "passed": False,
                       "detail": f"Error running memory_watchdog.py: {e}"})

    # ── Final scoring ──
    score = round(total_score / max_score, 4) if max_score > 0 else 0.0
    passed = score >= 0.75 and all(
        c["passed"] for c in checks
        if c["name"] in [
            "context_pack_query1_sources_are_snippet_ids",
            "context_pack_query2_sources_are_snippet_ids",
            "retrieval_bundle_query1_exists_valid",
            "retrieval_bundle_query2_exists_valid",
            "context_pack_query1_exists_valid",
            "context_pack_query2_exists_valid",
        ]
    )

    result_obj = {
        "passed": passed,
        "score": score,
        "checks": checks,
    }
    print(json.dumps(result_obj, indent=2))

if __name__ == "__main__":
    main()