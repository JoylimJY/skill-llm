import sys
import json
import os
import requests
from pathlib import Path

def run_eval(workspace: str):
    checks = []
    
    # Helper to add a check result
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # -------------------------------------------------------------------------
    # CHECK 1: Was a notebook created via POST /api/notebooks?
    # -------------------------------------------------------------------------
    try:
        resp = requests.get("http://localhost:5055/api/debug/notebooks", timeout=5)
        notebooks = resp.json()
        if isinstance(notebooks, list) and len(notebooks) >= 1:
            add_check("notebook_created", True, f"Found {len(notebooks)} notebook(s): {[n.get('name') for n in notebooks]}")
            created_notebook = notebooks[0]
            notebook_id = created_notebook.get("id")
        else:
            add_check("notebook_created", False, f"No notebooks found in server state. Response: {notebooks}")
            notebook_id = None
    except Exception as e:
        add_check("notebook_created", False, f"Exception querying debug endpoint: {e}")
        notebook_id = None

    # -------------------------------------------------------------------------
    # CHECK 2: Were all 5 research observations added as sources?
    # -------------------------------------------------------------------------
    expected_snippets = [
        "Proteomics analysis revealed elevated expression of HSP70 chaperone proteins under heat stress conditions in HeLa cells.",
        "Mass spectrometry data indicates a 3.2-fold upregulation of mitochondrial complex I subunits following hypoxia treatment.",
        "Single-cell RNA sequencing of 10,000 neurons identified 7 distinct transcriptional clusters correlated with synaptic plasticity markers.",
        "ATAC-seq chromatin accessibility profiling shows increased open chromatin at AP-1 motif regions in stimulated macrophages.",
        "Metabolomics screening detected accumulation of succinate and itaconate, confirming TCA cycle rewiring in LPS-activated monocytes.",
    ]

    try:
        resp = requests.get("http://localhost:5055/api/debug/sources", timeout=5)
        all_sources = resp.json()  # dict: {notebook_id_raw: [sources]}
        
        all_ingested_contents = []
        for nb_sources in all_sources.values():
            for src in nb_sources:
                all_ingested_contents.append(src.get("content", ""))
        
        found_count = sum(1 for snip in expected_snippets if snip in all_ingested_contents)
        
        if found_count == 5:
            add_check("all_5_snippets_ingested", True, f"All 5 research snippets found in sources.")
        else:
            add_check("all_5_snippets_ingested", False, f"Only {found_count}/5 snippets found. Ingested: {all_ingested_contents}")
    except Exception as e:
        add_check("all_5_snippets_ingested", False, f"Exception: {e}")

    # -------------------------------------------------------------------------
    # CHECK 3: Were sources added with type="text" (validated server-side)?
    # -------------------------------------------------------------------------
    try:
        resp = requests.get("http://localhost:5055/api/debug/sources", timeout=5)
        all_sources = resp.json()
        
        all_src_list = []
        for nb_sources in all_sources.values():
            all_src_list.extend(nb_sources)
        
        if len(all_src_list) >= 5:
            type_ok = all(s.get("type") == "text" for s in all_src_list)
            if type_ok:
                add_check("sources_have_type_text", True, "All sources have type='text' as required.")
            else:
                bad = [s for s in all_src_list if s.get("type") != "text"]
                add_check("sources_have_type_text", False, f"Some sources missing type='text': {bad}")
        else:
            add_check("sources_have_type_text", False, f"Not enough sources to check types. Found {len(all_src_list)} sources.")
    except Exception as e:
        add_check("sources_have_type_text", False, f"Exception: {e}")

    # -------------------------------------------------------------------------
    # CHECK 4: Was the search query issued with correct payload structure?
    # (notebook_ids as array, model: prefix for all model fields)
    # -------------------------------------------------------------------------
    try:
        resp = requests.get("http://localhost:5055/api/debug/log", timeout=5)
        log = resp.json()
        
        search_calls = [entry for entry in log if entry.get("endpoint") == "/api/search/ask"]
        
        if not search_calls:
            add_check("search_called_correctly", False, "No calls to /api/search/ask found in server log.")
        else:
            valid_search = False
            details = []
            for call in search_calls:
                body = call.get("body", {})
                nb_ids = body.get("notebook_ids")
                s_model = body.get("strategy_model", "")
                a_model = body.get("answer_model", "")
                fa_model = body.get("final_answer_model", "")
                
                is_array = isinstance(nb_ids, list)
                s_prefix = s_model.startswith("model:")
                a_prefix = a_model.startswith("model:")
                fa_prefix = fa_model.startswith("model:")
                
                if is_array and s_prefix and a_prefix and fa_prefix:
                    valid_search = True
                    details.append(f"Valid call: notebook_ids={nb_ids}, models={s_model},{a_model},{fa_model}")
                else:
                    issues = []
                    if not is_array:
                        issues.append(f"notebook_ids is not array: {type(nb_ids).__name__}={nb_ids}")
                    if not s_prefix:
                        issues.append(f"strategy_model missing 'model:' prefix: '{s_model}'")
                    if not a_prefix:
                        issues.append(f"answer_model missing 'model:' prefix: '{a_model}'")
                    if not fa_prefix:
                        issues.append(f"final_answer_model missing 'model:' prefix: '{fa_model}'")
                    details.append(f"Invalid call: {'; '.join(issues)}")
            
            add_check("search_called_correctly", valid_search, "; ".join(details))
    except Exception as e:
        add_check("search_called_correctly", False, f"Exception: {e}")

    # -------------------------------------------------------------------------
    # CHECK 5: Was the search result saved to a file named search_result.json?
    # -------------------------------------------------------------------------
    try:
        result_files = list(Path(workspace).rglob("search_result.json"))
        if not result_files:
            add_check("search_result_saved", False, "No file named 'search_result.json' found in workspace.")
        else:
            result_file = result_files[0]
            with open(result_file, "r") as f:
                content = f.read().strip()
            
            if not content:
                add_check("search_result_saved", False, f"File {result_file} is empty.")
            else:
                # Try to parse as JSON first, then fall back to checking for answer content
                try:
                    parsed = json.loads(content)
                    has_answer = (
                        "answer" in parsed or 
                        "HSP70" in str(parsed) or 
                        "succinate" in str(parsed) or
                        "stress" in str(parsed).lower()
                    )
                    if has_answer:
                        add_check("search_result_saved", True, f"search_result.json found at {result_file} with valid answer content.")
                    else:
                        add_check("search_result_saved", False, f"search_result.json exists but doesn't contain expected answer content. Keys: {list(parsed.keys()) if isinstance(parsed, dict) else 'not a dict'}")
                except json.JSONDecodeError:
                    # Accept non-JSON if it contains meaningful answer text
                    if any(kw in content for kw in ["HSP70", "succinate", "stress", "answer", "metabolic"]):
                        add_check("search_result_saved", True, f"search_result.json found with answer text at {result_file}.")
                    else:
                        add_check("search_result_saved", False, f"search_result.json exists but content is unrecognized: {content[:200]}")
    except Exception as e:
        add_check("search_result_saved", False, f"Exception: {e}")

    # -------------------------------------------------------------------------
    # CHECK 6: Was the notebook_id used in sources consistent with created notebook?
    # -------------------------------------------------------------------------
    try:
        if notebook_id:
            resp = requests.get("http://localhost:5055/api/debug/sources", timeout=5)
            all_sources = resp.json()
            
            # Sources should be stored under the created notebook's raw ID
            if notebook_id in all_sources and len(all_sources[notebook_id]) >= 5:
                add_check("sources_linked_to_created_notebook", True, 
                          f"All sources correctly linked to created notebook ID '{notebook_id}'.")
            else:
                # Also accept notebook:ID format variation
                found_nb_key = None
                for key in all_sources:
                    if key == notebook_id or key == f"notebook:{notebook_id}":
                        found_nb_key = key
                        break
                if found_nb_key:
                    add_check("sources_linked_to_created_notebook", True, 
                              f"Sources found under key '{found_nb_key}' for notebook '{notebook_id}'.")
                else:
                    add_check("sources_linked_to_created_notebook", False, 
                              f"Sources not linked to created notebook '{notebook_id}'. Found keys: {list(all_sources.keys())}")
        else:
            add_check("sources_linked_to_created_notebook", False, 
                      "Cannot verify — no notebook was created.")
    except Exception as e:
        add_check("sources_linked_to_created_notebook", False, f"Exception: {e}")

    # -------------------------------------------------------------------------
    # Final scoring
    # -------------------------------------------------------------------------
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_checks / total_checks, 3) if total_checks > 0 else 0.0
    overall_passed = passed_checks == total_checks

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace)