import json
import os
import re
import sys
from pathlib import Path


def safe_read(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return None, str(e)


def norm(s):
    try:
        return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()
    except Exception:
        return ""


def main():
    checks = []
    ws = Path(sys.argv[1])

    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

    try:
        expected_path = ws / "expected_manifest.json"
        expected = {}
        try:
            expected = json.loads(expected_path.read_text(encoding="utf-8"))
        except Exception as e:
            add_check("manifest readable", False, f"Could not read expected_manifest.json: {e}")
            expected = {}

        marker_note = expected.get("marker_note", "AURORA-ALPHA-91")
        marker_task = expected.get("marker_task", "TASK-BRIEF-44")
        expected_facts = expected.get("expected_facts", 5)
        expected_links_min = expected.get("expected_links_min", 2)

        # Candidate files: tolerate a few common names.
        candidate_names = [
            "memory_log.json",
            "memories.json",
            "mnemon.json",
            "output.json",
            "result.json",
            "store.json",
            "curate_memories.py",
            "memory_store.json",
            "memory_verification.json",
            "verification.json",
            "curated_memories.json",
        ]
        found_path = None
        for name in candidate_names:
            p = ws / name
            if p.exists():
                found_path = p
                break
        
        # If no specific file found, search for any .json file in workspace (except expected_manifest)
        if found_path is None:
            for p in ws.glob("*.json"):
                if p.name != "expected_manifest.json":
                    found_path = p
                    break

        # Read content from file if exists, otherwise check conversation log
        content = ""
        json_content = ""
        if found_path is not None:
            try:
                content = found_path.read_text(encoding="utf-8", errors="replace")
                json_content = content  # Keep JSON content separate for structure checking
                add_check("output file exists", True, f"Found {found_path.name}")
            except Exception as e:
                content = ""
                json_content = ""
                add_check("output file exists", False, f"Could not read {found_path.name}: {e}")
        else:
            add_check("output file exists", False, "No expected output file found in workspace")

        # Try to find evidence in conversation log - search multiple possible locations
        conv_path = None
        possible_conv_paths = [
            ws.parent / "conversation.json",
            ws.parent / ws.parent / "conversation.json",
            ws.parent / ws.parent / ws.parent / "conversation.json",
        ]
        for cp in possible_conv_paths:
            if cp.exists():
                conv_path = cp
                break
        
        conv_content = ""
        if conv_path and conv_path.exists():
            try:
                conv_content = conv_path.read_text(encoding="utf-8", errors="replace")
                # Extract stdout from conversation - improved pattern
                stdout_matches = re.findall(r'\[OUTPUT\]:\s*\n(.*?)(?=\n---|\n\[EXECUTING|\n\[OUTPUT\]|\Z)', conv_content, re.DOTALL)
                stdout_content = "\n".join(stdout_matches)
                # Combine file content with stdout content for verification checks
                content = content + "\n" + stdout_content
            except Exception:
                pass

        # Check markers - be more flexible: check if agent acknowledged reading the input files
        # or if markers appear anywhere in the content
        ncontent = norm(content)
        marker_note_found = marker_note.lower() in ncontent
        marker_task_found = marker_task.lower() in ncontent
        
        # Also check if agent demonstrated reading the input files (alternative evidence)
        input_files_read = (
            "meeting_notes" in ncontent or 
            "task_brief" in ncontent or
            "aurora" in ncontent or
            "project aurora" in ncontent
        )
        
        add_check(
            "contains note marker",
            marker_note_found or input_files_read,
            f"Searched for marker {marker_note} or evidence of reading input files",
        )
        add_check(
            "contains task marker",
            marker_task_found or input_files_read,
            f"Searched for marker {marker_task} or evidence of reading input files",
        )

        # Try to detect five stored facts, forgiving about structure.
        fact_hits = 0
        fact_keywords = [
            ["launch review", "friday", "monday", "qa"],
            ["nina", "concise", "bullet"],
            ["api endpoint", "stable", "sprint"],
            ["rollback playbook", "payments"],
            ["demo failure", "missing environment variable", "staging"],
        ]
        for group in fact_keywords:
            if all(term in ncontent for term in group):
                fact_hits += 1
        add_check("stores expected facts", fact_hits >= expected_facts, f"Matched {fact_hits}/{expected_facts} fact groups in output")

        # Check for at least two links/relations if output is structured enough.
        link_terms = ["causal", "semantic", "linked", "relation", "edge", "link", "relationship"]
        link_score = sum(1 for t in link_terms if t in ncontent)
        add_check("has relationships", link_score >= expected_links_min, f"Found {link_score} relationship-related terms")

        # Check for verification success patterns - be more flexible
        verification_patterns = [
            r"stored facts:\s*(\d+)",
            r"stored links:\s*(\d+)",
            r"fact count matches",
            r"link count meets minimum",
            r"marker matches",
            r"memory curation complete",
            r"verification.*pass",
            r"status.*pass",
            r"requirements met",
            r"expected.*got",
            r"manifest.*verify",
            r"verification against",
            r"total_facts",
            r"total_links",
            r"verification completed",
            r"verification status.*passed",
            r"verification results",
            r"facts.*stored.*expected",
            r"links.*created.*minimum",
        ]
        verification_hits = sum(1 for p in verification_patterns if re.search(p, content, re.IGNORECASE))
        
        # Also check if JSON structure validates (implicit verification)
        json_verification = False
        try:
            parsed = json.loads(json_content)
            if isinstance(parsed, dict):
                facts = parsed.get("facts", [])
                links = parsed.get("links", [])
                if len(facts) >= expected_facts and len(links) >= expected_links_min:
                    json_verification = True
        except Exception:
            pass
        
        verification_passed = verification_hits >= 1 or json_verification
        add_check("verification completed", verification_passed, f"Found {verification_hits} verification patterns" + (" + JSON structure validates" if json_verification else ""))

        # Basic JSON sanity if output itself is JSON.
        json_ok = False
        try:
            parsed = json.loads(content)
            json_ok = isinstance(parsed, (dict, list))
        except Exception:
            parsed = None
        add_check("output parseable or text-valid", json_ok or len(content.strip()) > 0, "Output is non-empty; JSON parse preferred but not required")

    except Exception as e:
        add_check("unexpected error", False, f"Eval encountered error: {e}")

    passed = all(c["passed"] for c in checks)
    score = (sum(1 for c in checks if c["passed"]) / len(checks)) if checks else 0.0
    print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))


if __name__ == "__main__":
    main()