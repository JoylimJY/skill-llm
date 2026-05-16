#!/usr/bin/env python3
"""
Evaluation script for the PayBridge institutional memory task.
Checks:
1. The codebase was indexed (index1 index was run on src/ and docs/)
2. At least 3 cognitive facts were recorded via `index1 learn`
3. A search_results.json file exists with valid search output
4. An index_status.json file exists with corpus and cognition stats
"""
import sys
import json
import subprocess
import os
from pathlib import Path

def run_check(name: str, fn) -> dict:
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {e}"}


def check_index_status(workspace: Path) -> tuple:
    """Run index1 status and verify corpus was indexed."""
    try:
        result = subprocess.run(
            ["index1", "status"],
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout + result.stderr
        # index1 status shows corpus chunk count and cognition count
        # We verify there are indexed chunks (corpus was indexed)
        if result.returncode != 0:
            return False, f"index1 status failed (rc={result.returncode}): {output[:500]}"
        
        # Check for any indication of indexed content
        output_lower = output.lower()
        
        # Look for chunk counts or file counts > 0
        import re
        # Find any number > 0 associated with "chunk", "file", "doc", "indexed"
        numbers = re.findall(r'(\d+)\s*(?:chunk|file|doc|indexed|item)', output_lower)
        numbers += re.findall(r'(?:chunk|file|doc|indexed|item)[s]?\s*[:\-]?\s*(\d+)', output_lower)
        
        has_indexed_content = any(int(n) > 0 for n in numbers if n.isdigit())
        
        if not has_indexed_content:
            # Try to verify via the index directory existing
            index_dirs = list(workspace.rglob(".index1")) + list(workspace.rglob("index1_data"))
            if not index_dirs:
                return False, f"No indexed content found in status output: {output[:400]}"
        
        return True, f"index1 status output indicates indexed content. Output snippet: {output[:300]}"
    except FileNotFoundError:
        return False, "index1 command not found"
    except subprocess.TimeoutExpired:
        return False, "index1 status timed out"


def check_cognition_facts(workspace: Path) -> tuple:
    """Verify at least 3 cognitive facts were recorded via index1 learn."""
    try:
        result = subprocess.run(
            ["index1", "status"],
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout + result.stderr
        output_lower = output.lower()
        
        import re
        
        # Look for cognition count patterns
        # e.g. "cognition: 4", "facts: 3", "cognitive facts: 5", "3 facts"
        cognition_patterns = [
            r'cognition[s]?\s*[:\-]\s*(\d+)',
            r'fact[s]?\s*[:\-]\s*(\d+)',
            r'(\d+)\s*cognition',
            r'(\d+)\s*fact[s]?',
            r'insight[s]?\s*[:\-]\s*(\d+)',
            r'(\d+)\s*insight[s]?',
            r'learn[ed]?\s*[:\-]\s*(\d+)',
            r'(\d+)\s*learn',
            r'episod[ic]?\s*[:\-]\s*(\d+)',
            r'record[s]?\s*[:\-]\s*(\d+)',
            r'(\d+)\s*record[s]?',
            r'memor[y|ies]\s*[:\-]\s*(\d+)',
            r'(\d+)\s*memor',
            r'entr[y|ies]\s*[:\-]\s*(\d+)',
            r'(\d+)\s*entr',
        ]
        
        cognition_count = 0
        matched_pattern = None
        for pattern in cognition_patterns:
            matches = re.findall(pattern, output_lower)
            if matches:
                max_val = max(int(m) for m in matches if m.isdigit())
                if max_val > cognition_count:
                    cognition_count = max_val
                    matched_pattern = pattern
        
        if cognition_count >= 3:
            return True, f"Found {cognition_count} cognitive facts (pattern: {matched_pattern})"
        
        # Also check if index_status.json was created with cognition info
        status_files = list(workspace.rglob("index_status.json"))
        if status_files:
            try:
                status_data = json.loads(status_files[0].read_text())
                # Look for cognition-related keys
                def find_cognition_count(d, depth=0):
                    if depth > 5:
                        return 0
                    if isinstance(d, dict):
                        for k, v in d.items():
                            if any(word in k.lower() for word in ['cognition', 'fact', 'insight', 'learn', 'episod', 'record', 'memory']):
                                if isinstance(v, int) and v >= 3:
                                    return v
                            result = find_cognition_count(v, depth+1)
                            if result >= 3:
                                return result
                    elif isinstance(d, list):
                        for item in d:
                            result = find_cognition_count(item, depth+1)
                            if result >= 3:
                                return result
                    return 0
                
                count_from_file = find_cognition_count(status_data)
                if count_from_file >= 3:
                    return True, f"Found {count_from_file} cognitive facts in index_status.json"
            except Exception:
                pass
        
        return False, (
            f"Expected >= 3 cognitive facts, found {cognition_count}. "
            f"Status output snippet: {output[:400]}"
        )
    except FileNotFoundError:
        return False, "index1 command not found"
    except subprocess.TimeoutExpired:
        return False, "index1 status timed out"


def check_search_results_file(workspace: Path) -> tuple:
    """Verify search_results.json exists and contains valid search output."""
    candidates = list(workspace.rglob("search_results.json"))
    if not candidates:
        return False, "search_results.json not found anywhere in workspace"
    
    # Use the most recently modified or first found
    target = candidates[0]
    
    try:
        content = target.read_text(encoding="utf-8")
        if not content.strip():
            return False, f"search_results.json at {target} is empty"
        
        # Try to parse as JSON
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Might be raw text output from index1 search — that's also acceptable
            # Check if it contains meaningful search result indicators
            content_lower = content.lower()
            search_indicators = ["result", "score", "chunk", "file", "match", "snippet", "source", "path"]
            found_indicators = [ind for ind in search_indicators if ind in content_lower]
            
            if len(found_indicators) >= 2:
                return True, (
                    f"search_results.json found at {target} with text content "
                    f"(non-JSON but contains search indicators: {found_indicators})"
                )
            
            # Check if it has any content related to PayBridge codebase
            paybridge_terms = ["payment", "processor", "stripe", "router", "gateway", "transaction", "merchant"]
            found_terms = [t for t in paybridge_terms if t in content_lower]
            if found_terms:
                return True, (
                    f"search_results.json at {target} contains PayBridge-relevant search results: {found_terms}"
                )
            
            return False, f"search_results.json at {target} has content but doesn't look like search results: {content[:200]}"
        
        # JSON parsing succeeded
        # Could be a list of results, a dict with results key, etc.
        if isinstance(data, list):
            if len(data) == 0:
                return False, f"search_results.json at {target} is an empty list — no search results"
            # Check that items have content
            return True, f"search_results.json at {target} contains {len(data)} search result items"
        elif isinstance(data, dict):
            # Look for results array or similar
            for key in ["results", "hits", "chunks", "items", "matches"]:
                if key in data and isinstance(data[key], list) and len(data[key]) > 0:
                    return True, f"search_results.json at {target} has '{key}' with {len(data[key])} items"
            # Any non-empty dict with content is acceptable
            if data:
                return True, f"search_results.json at {target} is a non-empty JSON object with keys: {list(data.keys())[:5]}"
            return False, f"search_results.json at {target} is an empty JSON object"
        else:
            return False, f"search_results.json at {target} has unexpected JSON type: {type(data)}"
    
    except PermissionError:
        return False, f"Permission denied reading {target}"
    except Exception as e:
        return False, f"Error reading search_results.json: {e}"


def check_index_status_file(workspace: Path) -> tuple:
    """Verify index_status.json exists and contains stats about corpus and cognition."""
    candidates = list(workspace.rglob("index_status.json"))
    if not candidates:
        return False, "index_status.json not found anywhere in workspace"
    
    target = candidates[0]
    
    try:
        content = target.read_text(encoding="utf-8")
        if not content.strip():
            return False, f"index_status.json at {target} is empty"
        
        # Try JSON parse
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Could be raw text output from `index1 status`
            content_lower = content.lower()
            stat_indicators = ["corpus", "chunk", "file", "index", "cognition", "fact", "total", "count"]
            found = [ind for ind in stat_indicators if ind in content_lower]
            if len(found) >= 2:
                return True, f"index_status.json at {target} contains status info (text format): {found}"
            return False, f"index_status.json content doesn't look like index stats: {content[:200]}"
        
        # JSON: check for corpus and/or cognition statistics
        content_lower = json.dumps(data).lower()
        corpus_present = any(word in content_lower for word in ["corpus", "chunk", "indexed", "files", "documents"])
        cognition_present = any(word in content_lower for word in ["cognition", "fact", "insight", "learn", "episod", "record"])
        
        if corpus_present or cognition_present:
            return True, (
                f"index_status.json at {target} contains stats "
                f"(corpus={corpus_present}, cognition={cognition_present})"
            )
        
        # Non-empty JSON is acceptable if it came from `index1 status`
        if data:
            return True, f"index_status.json at {target} is non-empty JSON: {str(data)[:200]}"
        
        return False, f"index_status.json at {target} appears to have no meaningful content"
    
    except Exception as e:
        return False, f"Error reading index_status.json: {e}"


def check_src_docs_indexed(workspace: Path) -> tuple:
    """Verify index covers both src/ and docs/ directories by running a search
    and checking results reference both code and documentation content."""
    try:
        # Search for something that exists in docs
        result_docs = subprocess.run(
            ["index1", "search", "payment processor fallback circuit breaker"],
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=30,
        )
        output_docs = (result_docs.stdout + result_docs.stderr).lower()
        
        # Search for something that exists in src
        result_src = subprocess.run(
            ["index1", "search", "PaymentRouter route transaction"],
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=30,
        )
        output_src = (result_src.stdout + result_src.stderr).lower()
        
        docs_covered = any(term in output_docs for term in [
            "circuit", "fallback", "processor", "stripe", "paypal",
            "architecture", "decision", "adr", "doc"
        ])
        src_covered = any(term in output_src for term in [
            "paymentrouter", "router", "route", "transaction", "processor",
            "gateway", "payment", "src"
        ])
        
        # Also accept if search returns any results at all (non-empty output > 50 chars)
        any_results = len(result_docs.stdout.strip()) > 50 or len(result_src.stdout.strip()) > 50
        
        if docs_covered and src_covered:
            return True, "Search returns results from both src/ and docs/ directories"
        elif any_results:
            return True, f"Search returns results (docs_covered={docs_covered}, src_covered={src_covered}), indicating index is populated"
        else:
            return False, (
                f"Search returned no meaningful results. "
                f"Docs search output: {output_docs[:200]}. "
                f"Src search output: {output_src[:200]}"
            )
    except FileNotFoundError:
        return False, "index1 command not found"
    except subprocess.TimeoutExpired:
        return False, "index1 search timed out"


def main():
    if len(sys.argv) < 2:
        workspace = Path("/workspace")
    else:
        workspace = Path(sys.argv[1])
    
    checks = []
    
    checks.append(run_check(
        "index1_status_shows_indexed_content",
        lambda: check_index_status(workspace)
    ))
    
    checks.append(run_check(
        "at_least_3_cognitive_facts_recorded",
        lambda: check_cognition_facts(workspace)
    ))
    
    checks.append(run_check(
        "search_results_json_exists_and_valid",
        lambda: check_search_results_file(workspace)
    ))
    
    checks.append(run_check(
        "index_status_json_exists_and_valid",
        lambda: check_index_status_file(workspace)
    ))
    
    checks.append(run_check(
        "both_src_and_docs_directories_indexed",
        lambda: check_src_docs_indexed(workspace)
    ))
    
    passed_checks = [c for c in checks if c["passed"]]
    total = len(checks)
    score = len(passed_checks) / total
    all_passed = len(passed_checks) == total
    
    result = {
        "passed": all_passed,
        "score": round(score, 2),
        "checks": checks,
    }
    
    print(json.dumps(result, indent=2))
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())