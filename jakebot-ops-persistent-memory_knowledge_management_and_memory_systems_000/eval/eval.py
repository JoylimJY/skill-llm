#!/usr/bin/env python3
"""
Evaluation script for the persistent-memory skill task.
Checks:
1. MEMORY.md exists and contains curated content from the raw notes
   (gateway migration decision, Stripe, latency figures, rollback strategy,
    KYC lesson, settlement batch window)
2. reference/people.md exists and contains team contacts (sarah.chen, marcus.webb, priya.nair)
3. The indexer was run: vector_memory/chroma_db/ exists and is non-empty
4. memory_graph.json exists and has nodes
5. memory/heartbeat-state.json exists and reports IN_SYNC
6. A search result file (search_results.txt) exists anywhere in workspace
   and contains content from the indexed memories (gateway/stripe/migration related)
"""

import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str) -> dict:
    ws = Path(workspace_dir)
    checks = []

    # ── Helper ────────────────────────────────────────────────────────────────
    def check(name: str, passed: bool, detail: str):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return passed

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 1: MEMORY.md exists
    # ─────────────────────────────────────────────────────────────────────────
    memory_md = ws / "MEMORY.md"
    try:
        if not memory_md.exists():
            check("MEMORY.md exists", False, "MEMORY.md not found in workspace root")
            memory_content = ""
        else:
            memory_content = memory_md.read_text(encoding="utf-8")
            check("MEMORY.md exists", True, f"Found MEMORY.md ({len(memory_content)} chars)")
    except Exception as e:
        check("MEMORY.md exists", False, f"Error reading MEMORY.md: {e}")
        memory_content = ""

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 2: MEMORY.md contains key migration decision content
    # ─────────────────────────────────────────────────────────────────────────
    try:
        required_patterns = [
            (r"[Ss]tripe", "Stripe migration target"),
            (r"(FIS|legacy gateway|fis)", "FIS legacy gateway reference"),
            (r"(latency|90ms|340ms|180k)", "latency/cost figures from the decision"),
            (r"(LaunchDarkly|launch.darkly|feature.flag|use_stripe_gateway)", "rollback/feature flag strategy"),
            (r"(KYC|kyc|identity.verif)", "KYC pre-flight lesson"),
            (r"(02:00|settlement.batch|settlement.*UTC|UTC.*settlement)", "settlement batch timing"),
        ]
        missed = []
        for pattern, desc in required_patterns:
            if not re.search(pattern, memory_content, re.IGNORECASE):
                missed.append(desc)
        if missed:
            check("MEMORY.md content completeness", False,
                  f"Missing key facts: {', '.join(missed)}")
        else:
            check("MEMORY.md content completeness", True,
                  "All critical migration decisions and lessons present")
    except Exception as e:
        check("MEMORY.md content completeness", False, f"Error checking content: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 3: reference/people.md exists with team contacts
    # ─────────────────────────────────────────────────────────────────────────
    people_md = ws / "reference" / "people.md"
    try:
        if not people_md.exists():
            check("reference/people.md exists", False, "reference/people.md not found")
            people_content = ""
        else:
            people_content = people_md.read_text(encoding="utf-8")
            check("reference/people.md exists", True, f"Found ({len(people_content)} chars)")
    except Exception as e:
        check("reference/people.md exists", False, f"Error: {e}")
        people_content = ""

    try:
        required_contacts = [
            (r"[Ss]arah.{0,10}[Cc]hen", "Sarah Chen"),
            (r"[Mm]arcus.{0,10}[Ww]ebb", "Marcus Webb"),
            (r"[Pp]riya.{0,10}[Nn]air", "Priya Nair"),
            (r"(sarah\.chen@|sarah@|@sarah)", "Sarah's contact info"),
            (r"(marcus\.webb@|marcus@|@marcus)", "Marcus's contact info"),
        ]
        missed_contacts = []
        for pattern, desc in required_contacts:
            if not re.search(pattern, people_content, re.IGNORECASE):
                missed_contacts.append(desc)
        if missed_contacts:
            check("reference/people.md contact completeness", False,
                  f"Missing contacts: {', '.join(missed_contacts)}")
        else:
            check("reference/people.md contact completeness", True,
                  "All required team contacts present")
    except Exception as e:
        check("reference/people.md contact completeness", False, f"Error: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 4: Indexer was run — ChromaDB populated
    # ─────────────────────────────────────────────────────────────────────────
    chroma_dir = ws / "vector_memory" / "chroma_db"
    try:
        if not chroma_dir.exists():
            check("ChromaDB index populated", False, "vector_memory/chroma_db/ not found")
        else:
            chroma_files = list(chroma_dir.rglob("*"))
            non_empty = [f for f in chroma_files if f.is_file()]
            if len(non_empty) == 0:
                check("ChromaDB index populated", False, "chroma_db/ exists but is empty")
            else:
                check("ChromaDB index populated", True,
                      f"chroma_db/ has {len(non_empty)} files")
    except Exception as e:
        check("ChromaDB index populated", False, f"Error: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 5: memory_graph.json exists and has nodes
    # ─────────────────────────────────────────────────────────────────────────
    graph_file = ws / "vector_memory" / "memory_graph.json"
    try:
        if not graph_file.exists():
            check("Knowledge graph generated", False, "vector_memory/memory_graph.json not found")
        else:
            graph_data = json.loads(graph_file.read_text())
            nodes = graph_data.get("nodes", [])
            if len(nodes) < 5:
                check("Knowledge graph generated", False,
                      f"Graph has only {len(nodes)} nodes — expected meaningful content")
            else:
                check("Knowledge graph generated", True,
                      f"Graph has {len(nodes)} nodes and {len(graph_data.get('links', []))} edges")
    except Exception as e:
        check("Knowledge graph generated", False, f"Error reading graph: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 6: heartbeat-state.json reports IN_SYNC
    # ─────────────────────────────────────────────────────────────────────────
    state_file = ws / "memory" / "heartbeat-state.json"
    try:
        if not state_file.exists():
            check("Sync state is IN_SYNC", False, "memory/heartbeat-state.json not found")
        else:
            state = json.loads(state_file.read_text())
            status = state.get("status", "UNKNOWN")
            chunks = state.get("chunk_count", 0)
            if status == "IN_SYNC" and chunks > 0:
                check("Sync state is IN_SYNC", True,
                      f"Status: {status}, chunks: {chunks}, graph nodes: {state.get('graph_nodes', 0)}")
            else:
                check("Sync state is IN_SYNC", False,
                      f"Status: {status}, chunk_count: {chunks} (expected IN_SYNC with >0 chunks)")
    except Exception as e:
        check("Sync state is IN_SYNC", False, f"Error: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 7: Search was run and results saved
    # Looks for any .txt file in workspace containing search result markers
    # ─────────────────────────────────────────────────────────────────────────
    try:
        search_result_files = list(ws.rglob("search_results.txt"))
        if not search_result_files:
            # Also accept any .txt file that looks like search output
            candidate_files = [
                f for f in ws.rglob("*.txt")
                if f.name not in ("project_notes.txt", "architecture_notes.txt")
            ]
            search_result_files = [
                f for f in candidate_files
                if "Memory Search" in f.read_text(encoding="utf-8", errors="ignore")
                or "Source:" in f.read_text(encoding="utf-8", errors="ignore")
            ]

        if not search_result_files:
            check("Search executed and results captured", False,
                  "No search_results.txt (or equivalent) found with memory search output")
        else:
            result_content = search_result_files[0].read_text(encoding="utf-8", errors="ignore")
            # Must contain content related to gateway/stripe/migration/people
            has_relevant = any(
                kw.lower() in result_content.lower()
                for kw in ["stripe", "gateway", "migration", "payment", "fis",
                           "chen", "webb", "nair", "settlement", "kyc"]
            )
            has_search_markers = (
                "Memory Search" in result_content
                or "Source:" in result_content
                or "Score:" in result_content
                or "[1]" in result_content
            )
            if has_relevant and has_search_markers:
                check("Search executed and results captured", True,
                      f"Search results saved at {search_result_files[0].relative_to(ws)}")
            elif has_search_markers:
                check("Search executed and results captured", False,
                      "Search output found but doesn't contain expected memory content")
            else:
                check("Search executed and results captured", False,
                      f"File found but doesn't look like valid search output: "
                      f"{result_content[:200]}")
    except Exception as e:
        check("Search executed and results captured", False, f"Error: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # Score
    # ─────────────────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)
    all_passed = passed_count == total

    return {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "invocation", "passed": False,
                                      "detail": "No workspace path provided"}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["passed"] else 1)