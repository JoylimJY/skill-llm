#!/usr/bin/env python3
"""
Evaluation script for the OpenClaw Deep Research task.
Usage: python eval_script.py /workspace
"""

import sys
import os
import json
import re
from pathlib import Path

def find_files_by_name(workspace, name_pattern):
    """Find files matching a pattern recursively, excluding distractor dirs."""
    results = []
    exclude_prefixes = ["archive", "data/raw", "data/processed", "internal",
                        "templates_legacy", "scratch", "vendor_docs"]
    for p in Path(workspace).rglob(name_pattern):
        rel = str(p.relative_to(workspace))
        # Allow files that are NOT exclusively in distractor dirs
        in_distractor = any(rel.startswith(pfx) for pfx in exclude_prefixes)
        if not in_distractor:
            results.append(p)
    return results

def load_text(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return None

def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return None

def load_yaml(path):
    try:
        import yaml
        return yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return None

def search_text(pattern, text, flags=re.IGNORECASE):
    if text is None:
        return False
    return bool(re.search(pattern, text, flags))

checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

# ────────────────────────────────────────────────────────────────────
# PHASE 1: Canonical project directory exists
# ────────────────────────────────────────────────────────────────────
project_dirs = []
try:
    for entry in Path(workspace).iterdir():
        if entry.is_dir():
            rel = entry.name
            # Must NOT be one of the pre-existing distractor dirs
            distractor_tops = {"archive", "data", "internal", "templates_legacy",
                               "scratch", "vendor_docs"}
            if rel not in distractor_tops:
                project_dirs.append(entry)
    has_project_dir = len(project_dirs) >= 1
    add_check(
        "canonical_project_directory_exists",
        has_project_dir,
        f"Found {len(project_dirs)} non-distractor top-level directory(ies): "
        f"{[d.name for d in project_dirs]}"
    )
except Exception as e:
    add_check("canonical_project_directory_exists", False, f"Exception: {e}")
    project_dirs = []

project_root = project_dirs[0] if project_dirs else Path(workspace)

# ────────────────────────────────────────────────────────────────────
# PHASE 2: Status / state file exists with required fields
# ────────────────────────────────────────────────────────────────────
try:
    status_candidates = list(Path(workspace).rglob("status*"))
    status_candidates = [p for p in status_candidates
                         if not any(str(p.relative_to(workspace)).startswith(d)
                                    for d in ["archive", "data", "internal",
                                              "templates_legacy", "scratch", "vendor_docs"])]
    status_text = None
    status_path = None
    for sc in status_candidates:
        t = load_text(sc)
        if t and len(t) > 30:
            status_text = t
            status_path = sc
            break

    has_status = status_text is not None
    add_check("status_file_exists", has_status,
              f"Status file found: {status_path}" if has_status else "No status file found outside distractor dirs")

    if has_status:
        has_phase = search_text(r"phase|current.?phase|phase.?current", status_text)
        has_next = search_text(r"next.?action|next.?step|action.*next", status_text)
        has_open = search_text(r"open.?question|question.*open|unresolved|open.?issue", status_text)
        add_check("status_file_has_phase", has_phase,
                  "Status file contains phase/current phase field" if has_phase else "Missing phase field")
        add_check("status_file_has_next_actions", has_next,
                  "Status file contains next actions" if has_next else "Missing next actions field")
        add_check("status_file_has_open_questions", has_open,
                  "Status file contains open questions" if has_open else "Missing open questions field")
    else:
        add_check("status_file_has_phase", False, "No status file to check")
        add_check("status_file_has_next_actions", False, "No status file to check")
        add_check("status_file_has_open_questions", False, "No status file to check")
except Exception as e:
    add_check("status_file_exists", False, f"Exception: {e}")
    add_check("status_file_has_phase", False, "Exception during check")
    add_check("status_file_has_next_actions", False, "Exception during check")
    add_check("status_file_has_open_questions", False, "Exception during check")

# ────────────────────────────────────────────────────────────────────
# PHASE 3: Source ledger with source_id entries
# ────────────────────────────────────────────────────────────────────
try:
    source_candidates = list(Path(workspace).rglob("*source*ledger*")) + \
                        list(Path(workspace).rglob("*ledger*source*")) + \
                        list(Path(workspace).rglob("sources.*"))
    source_candidates = [p for p in source_candidates
                         if not any(str(p.relative_to(workspace)).startswith(d)
                                    for d in ["archive", "data", "internal",
                                              "templates_legacy", "scratch", "vendor_docs"])]
    source_text = None
    source_path = None
    for sc in source_candidates:
        t = load_text(sc)
        if t and len(t) > 50:
            source_text = t
            source_path = sc
            break

    has_source_ledger = source_text is not None
    add_check("source_ledger_exists", has_source_ledger,
              f"Source ledger at {source_path}" if has_source_ledger else "No source ledger found")

    if has_source_ledger:
        # Must have source_id pattern like S1, SRC-001, source_id, etc.
        has_source_ids = search_text(
            r"(source_id|src[-_]?\d+|s\d+\b)", source_text, re.IGNORECASE)
        add_check("source_ledger_has_source_ids", has_source_ids,
                  "Source ledger has source_id entries" if has_source_ids
                  else "Source ledger missing source_id identifiers")
        # Must have at least 2 distinct sources
        source_id_matches = re.findall(
            r"(source_id|src[-_]?\d+|s\d+\b)", source_text, re.IGNORECASE)
        add_check("source_ledger_has_multiple_sources",
                  len(source_id_matches) >= 2,
                  f"Found {len(source_id_matches)} source_id mentions")
    else:
        add_check("source_ledger_has_source_ids", False, "No source ledger")
        add_check("source_ledger_has_multiple_sources", False, "No source ledger")
except Exception as e:
    add_check("source_ledger_exists", False, f"Exception: {e}")
    add_check("source_ledger_has_source_ids", False, "Exception")
    add_check("source_ledger_has_multiple_sources", False, "Exception")

# ────────────────────────────────────────────────────────────────────
# PHASE 4: Claim ledger with claim_id and claim classes
# ────────────────────────────────────────────────────────────────────
try:
    claim_candidates = list(Path(workspace).rglob("*claim*ledger*")) + \
                       list(Path(workspace).rglob("*ledger*claim*")) + \
                       list(Path(workspace).rglob("claims.*"))
    claim_candidates = [p for p in claim_candidates
                        if not any(str(p.relative_to(workspace)).startswith(d)
                                   for d in ["archive", "data", "internal",
                                             "templates_legacy", "scratch", "vendor_docs"])]
    claim_text = None
    claim_path = None
    for cc in claim_candidates:
        t = load_text(cc)
        if t and len(t) > 50:
            claim_text = t
            claim_path = cc
            break

    has_claim_ledger = claim_text is not None
    add_check("claim_ledger_exists", has_claim_ledger,
              f"Claim ledger at {claim_path}" if has_claim_ledger else "No claim ledger found")

    if has_claim_ledger:
        # Must have claim_id pattern
        has_claim_ids = search_text(
            r"(claim_id|c\d+\b|clm[-_]?\d+)", claim_text, re.IGNORECASE)
        add_check("claim_ledger_has_claim_ids", has_claim_ids,
                  "Claim ledger has claim_id entries" if has_claim_ids
                  else "Claim ledger missing claim_id identifiers")

        # Must use proper claim classes from the skill
        required_classes = ["hard_fact", "reported_fact", "interpretation",
                            "comparison", "forecast"]
        found_classes = [cls for cls in required_classes
                         if search_text(cls, claim_text)]
        add_check("claim_ledger_uses_proper_classes",
                  len(found_classes) >= 3,
                  f"Found claim classes: {found_classes} (need ≥3 of the 5 canonical types)")

        # Must reference source_ids
        has_source_ref = search_text(
            r"(source_id|src[-_]?\d+|s\d+\b)", claim_text, re.IGNORECASE)
        add_check("claim_ledger_references_source_ids", has_source_ref,
                  "Claims reference source_ids" if has_source_ref
                  else "Claims do not reference source_ids")

        # Must have confidence or date range on at least some claims
        has_confidence = search_text(
            r"(confidence|high|medium|low|date_range|\d{4}-\d{2})", claim_text)
        add_check("claim_ledger_has_confidence_or_dates", has_confidence,
                  "Claims include confidence/date fields" if has_confidence
                  else "Claims missing confidence/date information")
    else:
        for sub in ["claim_ledger_has_claim_ids", "claim_ledger_uses_proper_classes",
                    "claim_ledger_references_source_ids", "claim_ledger_has_confidence_or_dates"]:
            add_check(sub, False, "No claim ledger found")
except Exception as e:
    add_check("claim_ledger_exists", False, f"Exception: {e}")
    for sub in ["claim_ledger_has_claim_ids", "claim_ledger_uses_proper_classes",
                "claim_ledger_references_source_ids", "claim_ledger_has_confidence_or_dates"]:
        add_check(sub, False, f"Exception: {e}")

# ────────────────────────────────────────────────────────────────────
# PHASE 5: Comparison matrix (LFP vs NMC vs sodium-ion)
# ────────────────────────────────────────────────────────────────────
try:
    matrix_candidates = list(Path(workspace).rglob("*comparison*matrix*")) + \
                        list(Path(workspace).rglob("*matrix*comparison*")) + \
                        list(Path(workspace).rglob("*matrix*"))
    matrix_candidates = [p for p in matrix_candidates
                         if not any(str(p.relative_to(workspace)).startswith(d)
                                    for d in ["archive", "data", "internal",
                                              "templates_legacy", "scratch", "vendor_docs"])
                         and p.suffix in [".md", ".json", ".yaml", ".yml", ".txt", ".csv"]]
    matrix_text = None
    matrix_path = None
    for mc in matrix_candidates:
        t = load_text(mc)
        if t and len(t) > 80:
            matrix_text = t
            matrix_path = mc
            break

    # If no dedicated matrix file, check claim ledger or report for matrix-like content
    if not matrix_text and claim_text:
        if search_text(r"(comparable|partial|not_comparable|not.comparable)", claim_text):
            matrix_text = claim_text
            matrix_path = claim_path

    has_matrix = matrix_text is not None and search_text(
        r"(LFP|NMC|sodium|Na.?[Ii]on)", matrix_text)
    add_check("comparison_matrix_exists", has_matrix,
              f"Comparison matrix/table found at {matrix_path}" if has_matrix
              else "No comparison matrix covering LFP/NMC/sodium found")

    if has_matrix:
        has_comparability = search_text(
            r"(comparable|partial|not_comparable|not.comparable)", matrix_text)
        add_check("comparison_matrix_has_comparability_annotation", has_comparability,
                  "Matrix annotates rows as comparable/partial/not_comparable"
                  if has_comparability else
                  "Matrix missing comparability annotations (comparable/partial/not_comparable)")

        covers_three = (search_text(r"LFP", matrix_text) and
                        search_text(r"NMC", matrix_text) and
                        search_text(r"(sodium|Na.?[Ii]on)", matrix_text))
        add_check("comparison_matrix_covers_all_three_chemistries", covers_three,
                  "Matrix covers LFP, NMC, and sodium-ion" if covers_three
                  else "Matrix does not cover all three chemistries")

        covers_dimensions = sum([
            search_text(r"(energy.?density|Wh.?kg)", matrix_text),
            search_text(r"(cycle.?life|cycles)", matrix_text),
            search_text(r"(cost|USD|kWh)", matrix_text),
            search_text(r"(thermal|safety)", matrix_text),
        ])
        add_check("comparison_matrix_covers_multiple_dimensions",
                  covers_dimensions >= 3,
                  f"Matrix covers {covers_dimensions}/4 required dimensions")
    else:
        for sub in ["comparison_matrix_has_comparability_annotation",
                    "comparison_matrix_covers_all_three_chemistries",
                    "comparison_matrix_covers_multiple_dimensions"]:
            add_check(sub, False, "No matrix found")
except Exception as e:
    add_check("comparison_matrix_exists", False, f"Exception: {e}")
    for sub in ["comparison_matrix_has_comparability_annotation",
                "comparison_matrix_covers_all_three_chemistries",
                "comparison_matrix_covers_multiple_dimensions"]:
        add_check(sub, False, f"Exception: {e}")

# ────────────────────────────────────────────────────────────────────
# PHASE 6: Draft report with research cutoff date near the top
# ────────────────────────────────────────────────────────────────────
try:
    report_candidates = list(Path(workspace).rglob("*report*")) + \
                        list(Path(workspace).rglob("*draft*"))
    report_candidates = [p for p in report_candidates
                         if not any(str(p.relative_to(workspace)).startswith(d)
                                    for d in ["archive", "data", "internal",
                                              "templates_legacy", "scratch", "vendor_docs"])
                         and p.suffix in [".md", ".txt", ".json", ".yaml", ".yml"]]
    report_text = None
    report_path = None
    for rc in report_candidates:
        t = load_text(rc)
        if t and len(t) > 200:
            report_text = t
            report_path = rc
            break

    has_report = report_text is not None
    add_check("draft_report_exists", has_report,
              f"Draft report at {report_path}" if has_report else "No draft report found")

    if has_report:
        # Cutoff date must appear near the top (first 600 chars)
        top_text = report_text[:600]
        has_cutoff_near_top = search_text(
            r"(cutoff|research.?date|as.?of|data.?through|2024-06-30|June.?2024|2024)", top_text)
        add_check("report_has_cutoff_date_near_top", has_cutoff_near_top,
                  "Cutoff date present in first 600 chars" if has_cutoff_near_top
                  else "Cutoff date missing from top of report")

        # Must have methods or limits section
        has_methods = search_text(
            r"(method|limitation|limits|scope|caveat|uncertain)", report_text)
        add_check("report_has_methods_or_limits_section", has_methods,
                  "Report contains methods/limits/caveats section" if has_methods
                  else "Report missing methods/limits/uncertainty section")

        # Must NOT silently promote unverified 2021 CSV data
        has_stale_price = search_text(
            r"(112|130).{0,30}(2021|kWh|USD)", report_text)
        add_check("report_does_not_silently_use_stale_2021_data",
                  not has_stale_price,
                  "Report does not silently use stale 2021 blended prices"
                  if not has_stale_price
                  else "Report appears to cite 2021 unverified prices without flagging them")

        # Must cover all three chemistries
        covers_all = (search_text(r"LFP", report_text) and
                      search_text(r"NMC", report_text) and
                      search_text(r"(sodium|Na.?[Ii]on)", report_text))
        add_check("report_covers_all_three_chemistries", covers_all,
                  "Report discusses LFP, NMC, and sodium-ion" if covers_all
                  else "Report does not cover all three chemistries")
    else:
        for sub in ["report_has_cutoff_date_near_top",
                    "report_has_methods_or_limits_section",
                    "report_does_not_silently_use_stale_2021_data",
                    "report_covers_all_three_chemistries"]:
            add_check(sub, False, "No report found")
except Exception as e:
    add_check("draft_report_exists", False, f"Exception: {e}")
    for sub in ["report_has_cutoff_date_near_top", "report_has_methods_or_limits_section",
                "report_does_not_silently_use_stale_2021_data", "report_covers_all_three_chemistries"]:
        add_check(sub, False, f"Exception: {e}")

# ────────────────────────────────────────────────────────────────────
# PHASE 7: No unsupported claims silently promoted (draft/blocked/contested)
# ────────────────────────────────────────────────────────────────────
try:
    all_text = (claim_text or "") + (report_text or "")
    has_flag_system = search_text(
        r"(draft|blocked|contested|unresolved|unverified)", all_text)
    add_check("flagging_system_for_unresolved_claims_present", has_flag_system,
              "Project uses draft/blocked/contested flags for unresolved claims"
              if has_flag_system
              else "No evidence of draft/blocked/contested claim flagging system")
except Exception as e:
    add_check("flagging_system_for_unresolved_claims_present", False, f"Exception: {e}")

# ────────────────────────────────────────────────────────────────────
# PHASE 8: Report does not use totalizing conclusions without evidence
# ────────────────────────────────────────────────────────────────────
try:
    if report_text:
        totalizing = search_text(
            r"\b(is winning overall|clearly better|definitively|unambiguously best|"
            r"is the clear winner|without question)\b", report_text)
        add_check("report_avoids_totalizing_conclusions",
                  not totalizing,
                  "Report avoids unsupported totalizing language"
                  if not totalizing
                  else "Report uses unsupported totalizing language (e.g., 'is winning overall')")
    else:
        add_check("report_avoids_totalizing_conclusions", False, "No report to check")
except Exception as e:
    add_check("report_avoids_totalizing_conclusions", False, f"Exception: {e}")

# ────────────────────────────────────────────────────────────────────
# Scoring
# ────────────────────────────────────────────────────────────────────
WEIGHTS = {
    "canonical_project_directory_exists": 2,
    "status_file_exists": 2,
    "status_file_has_phase": 1,
    "status_file_has_next_actions": 1,
    "status_file_has_open_questions": 1,
    "source_ledger_exists": 3,
    "source_ledger_has_source_ids": 3,
    "source_ledger_has_multiple_sources": 2,
    "claim_ledger_exists": 3,
    "claim_ledger_has_claim_ids": 4,
    "claim_ledger_uses_proper_classes": 5,
    "claim_ledger_references_source_ids": 4,
    "claim_ledger_has_confidence_or_dates": 2,
    "comparison_matrix_exists": 3,
    "comparison_matrix_has_comparability_annotation": 5,
    "comparison_matrix_covers_all_three_chemistries": 3,
    "comparison_matrix_covers_multiple_dimensions": 3,
    "draft_report_exists": 3,
    "report_has_cutoff_date_near_top": 4,
    "report_has_methods_or_limits_section": 2,
    "report_does_not_silently_use_stale_2021_data": 3,
    "report_covers_all_three_chemistries": 2,
    "flagging_system_for_unresolved_claims_present": 3,
    "report_avoids_totalizing_conclusions": 2,
}

total_weight = sum(WEIGHTS.values())
earned = sum(WEIGHTS.get(c["name"], 1) for c in checks if c["passed"])
score = round(earned / total_weight, 4)

# Must pass core structural checks to pass overall
critical = [
    "claim_ledger_uses_proper_classes",
    "comparison_matrix_has_comparability_annotation",
    "claim_ledger_has_claim_ids",
    "source_ledger_has_source_ids",
    "claim_ledger_references_source_ids",
    "report_has_cutoff_date_near_top",
]
critical_passed = all(
    any(c["name"] == crit and c["passed"] for c in checks)
    for crit in critical
)

passed = critical_passed and score >= 0.65

result = {
    "passed": passed,
    "score": score,
    "checks": checks,
}
print(json.dumps(result, indent=2))