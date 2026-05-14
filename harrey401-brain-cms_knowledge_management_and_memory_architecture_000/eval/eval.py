import sys
import json
import re
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []

def check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

# ── CHECK 1: Semantic schema files created in memory/ ────────────────────────
try:
    # Look for domain-specific .md schema files (not daily logs, not INDEX/ANCHORS/MEMORY/nrem/rem)
    reserved = {"INDEX.md", "ANCHORS.md", "MEMORY.md", "nrem_report.md", "rem_report.md"}
    date_pat = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")
    
    memory_dir = workspace / "memory"
    schemas_dir = memory_dir / "schemas"
    
    # Search both memory/ and memory/schemas/
    candidate_files = []
    for f in memory_dir.glob("*.md"):
        if f.name not in reserved and not date_pat.match(f.name):
            candidate_files.append(f)
    for f in schemas_dir.glob("*.md"):
        if f.name not in reserved and not date_pat.match(f.name):
            candidate_files.append(f)
    
    if len(candidate_files) >= 1:
        schema_content_ok = any(len(f.read_text().strip()) > 50 for f in candidate_files)
        check(
            "domain_schema_files_created",
            schema_content_ok,
            f"Found {len(candidate_files)} schema file(s): {[f.name for f in candidate_files]}. Content OK: {schema_content_ok}"
        )
    else:
        check("domain_schema_files_created", False, "No domain schema .md files found in memory/ or memory/schemas/")
except Exception as e:
    check("domain_schema_files_created", False, f"Exception: {e}")

# ── CHECK 2: INDEX.md has schema entries (triggers + priority) ────────────────
try:
    index_path = workspace / "memory" / "INDEX.md"
    index_text = index_path.read_text()
    
    # Must have more content than the skeleton — look for trigger-like entries
    has_triggers = bool(re.search(r"trigger", index_text, re.IGNORECASE))
    has_priority = bool(re.search(r"priority", index_text, re.IGNORECASE))
    has_schema_ref = bool(re.search(r"\.md", index_text))  # References to schema files
    
    # Count non-comment, non-empty lines beyond header
    content_lines = [l for l in index_text.splitlines() 
                     if l.strip() and not l.startswith("#") and not l.startswith(">") and not l.startswith("<!--")]
    
    passed = has_triggers and len(content_lines) >= 3
    check(
        "index_md_has_schema_entries",
        passed,
        f"INDEX.md has_triggers={has_triggers}, has_priority={has_priority}, "
        f"has_schema_ref={has_schema_ref}, content_lines={len(content_lines)}. "
        f"Preview: {index_text[200:500]!r}"
    )
except Exception as e:
    check("index_md_has_schema_entries", False, f"Exception reading INDEX.md: {e}")

# ── CHECK 3: LanceDB vector store exists and is non-empty ─────────────────────
try:
    vectorstore_dir = workspace / "memory_brain" / "vectorstore"
    
    if vectorstore_dir.exists():
        # Check for LanceDB internal files
        all_files = list(vectorstore_dir.rglob("*"))
        lance_files = [f for f in all_files if f.is_file()]
        
        # LanceDB creates .lance directory with data files
        has_lance_data = any(
            ".lance" in str(f) or f.suffix in (".lance", ".manifest", ".bin") 
            for f in lance_files
        )
        # Also accept any files at all (LanceDB structure varies by version)
        has_any_content = len(lance_files) > 0
        
        check(
            "vectorstore_indexed",
            has_any_content,
            f"vectorstore/ exists with {len(lance_files)} file(s). "
            f"Lance-specific: {has_lance_data}. "
            f"Files: {[str(f.relative_to(vectorstore_dir)) for f in lance_files[:5]]}"
        )
    else:
        check("vectorstore_indexed", False, "memory_brain/vectorstore/ directory does not exist — index_memory.py was not run")
except Exception as e:
    check("vectorstore_indexed", False, f"Exception: {e}")

# ── CHECK 4: NREM ran — ANCHORS.md has promoted entries from daily logs ────────
try:
    anchors_path = workspace / "memory" / "ANCHORS.md"
    anchors_text = anchors_path.read_text()
    
    # Must contain the specific anchor events from the daily logs
    cpd007_anchor = bool(re.search(r"CPD007.*clinical candidate|clinical candidate.*CPD007", anchors_text, re.IGNORECASE))
    phase1_anchor = bool(re.search(r"Phase I|Phase 1|IND|steering committee|Go.No.Go", anchors_text, re.IGNORECASE))
    braf_anchor = bool(re.search(r"BRAF|V600E|resistance|kinase hinge", anchors_text, re.IGNORECASE))
    
    # Must have NREM promotion section
    has_nrem_header = bool(re.search(r"NREM|Promoted", anchors_text, re.IGNORECASE))
    
    total_anchors = anchors_text.count("[2024-") + anchors_text.count("- [")
    
    passed = (cpd007_anchor or phase1_anchor or braf_anchor) and has_nrem_header
    check(
        "anchors_promoted_by_nrem",
        passed,
        f"ANCHORS.md: cpd007={cpd007_anchor}, phase1={phase1_anchor}, "
        f"braf={braf_anchor}, nrem_header={has_nrem_header}, "
        f"approx_entries={total_anchors}. Preview: {anchors_text[:600]!r}"
    )
except Exception as e:
    check("anchors_promoted_by_nrem", False, f"Exception reading ANCHORS.md: {e}")

# ── CHECK 5: NREM report file exists ─────────────────────────────────────────
try:
    nrem_report = workspace / "memory" / "nrem_report.md"
    if nrem_report.exists():
        content = nrem_report.read_text()
        has_stats = bool(re.search(r"Daily logs scanned|lines processed|anchors promoted", content, re.IGNORECASE))
        check(
            "nrem_report_exists",
            has_stats,
            f"nrem_report.md exists. has_stats={has_stats}. Preview: {content[:400]!r}"
        )
    else:
        check("nrem_report_exists", False, "memory/nrem_report.md not found — nrem.py was not run")
except Exception as e:
    check("nrem_report_exists", False, f"Exception: {e}")

# ── CHECK 6: Query result file exists and contains source filenames ────────────
try:
    # Agent must have produced a query result file named query_results.txt
    result_files = list(workspace.rglob("query_results.txt"))
    
    if result_files:
        result_text = result_files[0].read_text()
        # Must contain .md filenames (--sources-only output format)
        has_md_sources = bool(re.search(r"\.md", result_text))
        non_empty = len(result_text.strip()) > 5
        check(
            "query_results_file",
            has_md_sources and non_empty,
            f"query_results.txt found at {result_files[0]}. "
            f"has_md_sources={has_md_sources}, non_empty={non_empty}. "
            f"Content: {result_text.strip()[:300]!r}"
        )
    else:
        check("query_results_file", False, "query_results.txt not found anywhere in workspace")
except Exception as e:
    check("query_results_file", False, f"Exception: {e}")

# ── CHECK 7: venv was used correctly (not system python) ─────────────────────
try:
    venv_dir = workspace / "memory_brain" / ".venv"
    venv_python = venv_dir / "bin" / "python3"
    venv_lancedb = list(venv_dir.rglob("lancedb")) if venv_dir.exists() else []
    
    venv_exists = venv_python.exists() if venv_python.exists() else (venv_dir / "bin" / "python").exists() if (venv_dir / "bin" / "python").exists() else False
    has_lancedb = len(venv_lancedb) > 0
    
    check(
        "venv_correctly_used",
        venv_dir.exists(),
        f".venv exists={venv_dir.exists()}, python3 exists={venv_exists}, "
        f"lancedb in venv={has_lancedb}"
    )
except Exception as e:
    check("venv_correctly_used", False, f"Exception: {e}")

# ── Scoring ──────────────────────────────────────────────────────────────────
# Weights: core workflow checks matter most
weights = {
    "domain_schema_files_created": 2.0,
    "index_md_has_schema_entries": 1.5,
    "vectorstore_indexed": 2.0,
    "anchors_promoted_by_nrem": 2.5,
    "nrem_report_exists": 1.0,
    "query_results_file": 1.5,
    "venv_correctly_used": 0.5,
}
total_weight = sum(weights.values())
earned = sum(weights.get(c["name"], 1.0) for c in checks if c["passed"])
score = round(earned / total_weight, 3)
passed_overall = score >= 0.70

result = {
    "passed": passed_overall,
    "score": score,
    "checks": checks,
}
print(json.dumps(result, indent=2))